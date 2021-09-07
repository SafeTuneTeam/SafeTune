import sqlite3
import re
import ast
import os.path
from sqlite3 import Error
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
#from sklearn.feature_selection import SelectKBest, chi2
from sklearn.decomposition import PCA
#from sklearn.decomposition import LatentDirichletAllocation
from imblearn.over_sampling import BorderlineSMOTE


output_prefix = './'

# Training set
software = ['clang', 'gcc', 'flink', 'hdfs', 'httpd', 'mysql', 'cassandra', 'nginx',
            'keystone', 'mapreduce', 'mariadb', 'nova', 'core']
# Testing set
test_software = ['postgresql', 'spark', 'squid']

nameConvert1 = {1: 'Performance', 0: 'NonPerformance'}

nameConvert2 = {0: 'END.PATH',
                1: 'MoreCost',
                2: 'LowSecure',
                3: 'LowReliable',
                4: 'Limit',
                5: 'WorkloadSpec',
                6: 'ReduceFunc'}

name2_name1 = {
    'END.PATH': 'NonPerformance',
    'MoreCost': 'Performance',
    'LowSecure': 'Performance',
    'LowReliable': 'Performance',
    'Limit': 'Performance',
    'WorkloadSpec': 'Performance',
    'ReduceFunc': 'Performance'
}

# New data ID offset after balancing.
offset = 100000

def fetchAllandEncodeTFIDF():

    ID, res_X, res_Y1, res_Y2 = {}, {}, {}, {}

    try:
        conn = sqlite3.connect("../dataset/safetune.db")
    except Error as e:
        print(e)

    sql = "SELECT ID, description, p, s, software FROM ConfigDocs"

    df = pd.read_sql_query(sql, conn)

    # for COL: performance_related('p') & side_effect('s')
    df['p'] = df['p'].apply(lambda x: nameConvert1[x])
    df['s'] = df['s'].apply(lambda x: nameConvert2[x])

    # for COL: description
    stemmer = PorterStemmer()
    words = stopwords.words("english")
    df['description'] = df['description'].apply(
        lambda x: " ".join([stemmer.stem(i) for i in re.sub("[^a-zA-Z]", " ", x).split() if i not in words]).lower())
        
    #=== TF-IDF, ngram_range=(1, 3)) meaning that unigram, bigram and trigram ===
    vectorizer = TfidfVectorizer(min_df=3, stop_words="english", sublinear_tf=True, norm='l2', ngram_range=(1, 3))  # norm: 'l1' or 'l2'
    embeddeds_numeric = vectorizer.fit_transform(list(df['description'])).todense()
    
    #=== PCA, n_components=0.99 meaning that keep 99% information ===
    print('Embedding dimensions by TF-IDF: %d, doing PCA...' % embeddeds_numeric.shape[1])
    pca = PCA(n_components=0.99)
    descrips = pca.fit_transform(embeddeds_numeric, df['s'].to_numpy())
    print('PCA embedding dimensions: %d' % descrips.shape[1])
    
    #=== LDA ===
    # df['description'] = pd.Series([str(desc.tolist()) for desc in descrips])
    # lda =LatentDirichletAllocation(n_components=7, n_jobs=8)
    # descrips = lda.fit_transform(embeddeds_numeric, df['s'].to_numpy())
    # print('LDA embedding dimensions: %d' % descrips.shape[1])
    df['description'] = pd.Series([str(desc.tolist()) for desc in descrips])


    # organize by software
    v = dict(tuple(df.groupby('software')))
    print('\n[=== Test samples of each software ===]')
    for s in software + test_software:
        ID[s] = v[s]['ID']
        res_X[s] = v[s]['description']
        res_Y1[s] = v[s]['p']
        res_Y2[s] = v[s]['s']
        print('  [%s]: %d' % (s, len(res_X[s])))

    return ID, res_X, res_Y1, res_Y2


def split_train_test(ID, X, y1, y2, test_soft):

    ID_train, X_train, y1_train, y2_train = [], [], [], []

    for s in X.keys():
        if s in test_soft:
            continue
        else:
            ID_train.extend(ID[s])
            X_train.extend(X[s])
            y1_train.extend(y1[s])
            y2_train.extend(y2[s])

    return ID_train, X_train, y1_train, y2_train


ID, X, y1, y2 = fetchAllandEncodeTFIDF()
ID_train, X_train, y1_train, y2_train = split_train_test(ID, X, y1, y2, test_software)

# === BorderlineSMOTE, sampling_strategy='not majority' meaning that all none majority classes are resampled to be the same with majority class
balancer = BorderlineSMOTE(sampling_strategy='not majority', random_state=123456)
X_train_balance, y2_train_balance = balancer.fit_resample([ast.literal_eval(X) for X in X_train], y2_train)
ID_train_balance = [str(i+offset) for i, piece in enumerate(y2_train_balance)]
y1_train_balance = [name2_name1[piece] for piece in y2_train_balance]


# Training set
print('\n[=== Saving to csv... ===]')
dataTrain = {'ID': ID_train_balance,
             'Desc': [str(X) for X in X_train_balance],
             'L1': y1_train_balance,
             'L2':y2_train_balance}
dfTrain = pd.DataFrame(data=dataTrain)
dfTrain.to_csv(output_prefix + 'TrainingSet.csv', header=None, index=None)

# Testing set
for i in test_software:

    print('  |___ Load/Convert/Save Data for Software [%s] ...' % i)
    ID_test = ID[i]
    X_test = X[i]
    y1_test = y1[i]
    y2_test = y2[i]
    
    #print('       Train : Test = %d : %d' % (len(X_train_balance), len(X_test)))
    dataTest = {'ID': ID_test, 'Desc': X_test, 'L1': y1_test, 'L2':y2_test}
    dfTest = pd.DataFrame(data=dataTest)
    dfTest.to_csv(output_prefix + 'Test_' + i + '.csv', header=None, index=None)
