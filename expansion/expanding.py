import spacy
import pandas as pd
import time
from tqdm import trange, tqdm
import pickle
import numpy as np
import re
import os, datetime
from prefixspan import PrefixSpan
from synonyms import synonyms_noun, synonyms_verb, synonyms_adj_adv
import random
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from pathlib import Path
from sklearn.metrics import classification_report
from operator import itemgetter

nlp = spacy.load("en_core_web_lg")

label_dict = {'resource': 1,
              'security-tradeoff': 2,
              'reliability-tradeoff': 3,
              'limited-side-effect': 4,
              'workload-specific': 5,
              'function-tradeoff': 6,
              'others': 7}

label_dict_r = [''] + list(label_dict.keys())
target_dep = ['nsubj', 'nsubjpass', 'dobj', 'obj', 'pobj', 'ROOT', 'iobj']
reserved_pos = ['ADJ', 'ADV', 'NOUN', 'NUM', 'VERB', 'ADP', 'PROPN', 'SCONJ', 'CCONJ']  # , 'PART'


def name2tokens(name):
    """
    :param name: name of configuration parameter, string
    :return: tokenized name
    e.g.
    input: ConfigurationName
    return: Configuration Name
    """
    patterns = re.compile(r'[-._]|(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])')
    res = patterns.split(name)
    res = ' '.join(res)
    # res = ' '.join([r.lower() for r in res])
    return res


def add_token2dict(pos, lemma, token_dict, uid):
    """
    :param pos: pos (part of speech) of token, if we use svo (subject, verb and object) to mine patterns,
    this should be dep_ (dependency) of the token
    :param lemma: lemma of token
    :param token_dict: return index of (pos, lemma)
    :param uid: a global counter of identical (pos, lemma)
    :return: tid: the index of (pos, lemma) of token_dict; new_uid: updated uid
    """
    if (pos, lemma) in token_dict:
        tid = token_dict[(pos, lemma)]
        new_uid = uid
    else:
        token_dict[(pos, lemma)] = uid
        tid = token_dict[(pos, lemma)]
        new_uid = uid + 1
    return tid, new_uid


def replace_syn(token):
    if token.pos_ in ['NOUN', 'PROPN']:
        for word in synonyms_noun:
            if token.lemma_ in synonyms_noun[word]:
                return word
    if token.pos_ == 'VERB':
        for word in synonyms_verb:
            if token.lemma_ in synonyms_verb[word]:
                return word
    if token.pos_ == 'ADV' or token.pos_ == 'ADJ':
        for word in synonyms_adj_adv:
            if token.lemma_ in synonyms_adj_adv[word]:
                return word
    if token.pos_ == 'NUM':
        return 'NUM'
    return token.lemma_


def tokens2id(data, output_folder, feature='description'):
    """
    Convert tokens in descriptions into numbers
    :param data: data read from datafile, in DataFrame type
    :param output_folder: folder to store the token dict
    :param feature: column in data selected to mine patterns
    :return: seqs
    """
    if feature == 'name':
        description = data[feature].apply(name2tokens)
    else:
        description = data['description']

    labels = list(data['label'])
    uid = 1  # 0 for unknown word
    token_dict = {}
    for label in label_dict:
        print(label, uid)
        token_dict[label] = label_dict[label]
        uid += 1
    seqs = []
    description = list(description)
    pbar = trange(len(description))
    for i in pbar:
        pbar.set_description('Processed Descriptions: %d' % i)
        seq = []
        doc = nlp(description[i].strip().lower())
        for token in doc:
            if feature == 'svo':
                # print('POS ：', token.pos_)
                if token.dep_ in target_dep:
                    tid, uid = add_token2dict(token.dep_, token.lemma_, token_dict=token_dict, uid=uid)
                    # print(tid, uid)
                    seq.append(tid)
            elif feature == 'description':
                if token.pos_ in reserved_pos:
                    lemma = replace_syn(token)
                    tid, uid = add_token2dict(token.pos_, lemma, token_dict=token_dict, uid=uid)
                    seq.append(tid)
                # elif token.pos_ == 'PUNCT' and token.lemma_ in ['.', '?']:
                #     lemma = '.'
                #     tid, uid = add_token2dict(token.pos_, lemma, token_dict=token_dict, uid=uid)
                #     seq.append(tid)
            else:
                tid, uid = add_token2dict(token.lemma_, token.lemma_, token_dict, uid)
                seq.append(tid)
        seq.append(token_dict[labels[i]])
        seqs.append(seq)
    print(uid)
    # from csv to txt, sentence to numbered sequences, e.g. a b c ==> 1 2 3
    with open('%s/seqs.txt' % output_folder, 'w') as f:
        for seq in seqs:
            f.write(' '.join([str(s) for s in seq]) + '\n')
    with open('%s/id2token.pkl' % output_folder, 'wb') as f:
        pickle.dump(token_dict, f)
    with open('%s/words.txt' % output_folder, 'w') as f:
        f.write('\n'.join([str(w) for w in list(token_dict.keys())]))
    return seqs


def is_subsequence(s, t):
    index = 0
    for value in s:
        try:
            index = t.index(value, index)
        except ValueError:
            return False
        index += 1
    return True


def pattern_in_seq(pattern, config):
    for p in pattern[0]:
        if p not in config:
            return False
    return True


def label_config(patterns, config, threshold=0.85):
    """
    use patterns mined to label config
    :param patterns: patterns mined from labeled data (configs),
    a list of patterns in format (seqs, label, support, confidence)
    :param config: config to be labeled, a list of numbers like [1,2,3,4]
    :param threshold: above which the pattern is thought to be valuable
    :return: predicted label (number) and the number of matched patterns
    """
    # prob = np.zeros(len(label_dict_r))
    count = 0
    matched_pattern = [[], 0, 0, 0]
    for pattern in patterns:
        # pattern = (pattern, pred, support, confidence)
        if is_subsequence(pattern[0], config) \
                and pattern[3] >= threshold:
            count += 1
            if (pattern[3] > matched_pattern[3]) or \
                    (pattern[3] == matched_pattern[3] and pattern[2] > matched_pattern[2]):
                matched_pattern = pattern
    return matched_pattern[1], count, matched_pattern


def label_config_2(patterns, config):
    """
    use patterns mined to label config
    :param patterns: patterns mined from labeled data (configs),
    a list of patterns in format (seqs, label, support, confidence)
    :param config: config to be labeled, a list of numbers like [1,2,3,4]
    :return: predicted label (number), the number of matched patterns, weight
    """
    count = 0
    weighted_votes = [[0], [0], [0], [0], [0], [0], [0]]
    weighted_voting_classifier = [0, 0, 0, 0, 0, 0, 0]
    for pattern in patterns:
        # pattern = (pattern, pred_label, support, confidence)
        if is_subsequence(pattern[0], config):
            count += 1
            weighted_votes[pattern[1]-1].append(((pattern[2]+30.0)/30.0) * pattern[3])  # black magic
            weighted_voting_classifier[pattern[1]-1] += ((pattern[2]+30.0)/30.0) * pattern[3]  # black magic
    weighted_voting_classifier = [max(weighted_votes[0]), max(weighted_votes[1]),
                                  max(weighted_votes[2]), max(weighted_votes[3]),
                                  max(weighted_votes[4]), max(weighted_votes[5]),
                                  max(weighted_votes[6])]
    if np.sort(weighted_voting_classifier)[-2] * 1.0 < max(weighted_voting_classifier):  # another black magic
        label_pred = np.argmax(weighted_voting_classifier) + 1
        return label_pred, count, weighted_voting_classifier
    else:
        return -1, 0, [0, 0, 0, 0, 0, 0, 0]


def filter_cars(pattern_pkl, out, threshold):
    """
    clean the mined patterns, filter out those shorter ones with lower confidence (or support)
    :param pattern_pkl: file contains the mined patterns, in .pkl format
    :param out: file to store the cleaned patterns, in .pkl format
    :param threshold: pattern whose confidence is lower than threshold is filtered out
    :return:
    """
    patterns = pickle.load(open(pattern_pkl, 'rb'))
    label_count = [0, 0, 0, 0, 0, 0, 0]
    threshold_for_minor = 0.85
    threshold_for_major = 0.85

    with open('%s-log.txt' % pattern_pkl[:-4], 'a') as f:
        f.write('filter start at: %s\n' % time.asctime(time.localtime(time.time())))
    print('Filtering...')
    # Sorted by: x[3](confidence), if equal,
    #        by: x[2](support);
    # patterns = sorted(patterns, key=lambda x: (x[3], x[2], len(x[0])), reverse=True)
    res = []
    for i, p in enumerate(patterns):
        if (p[1] in [1, 2, 3, 4, 5, 6] and p[3] > threshold_for_minor) or\
                (p[1] == 7 and p[3] > threshold_for_major):
            res.append(p)
            label_count[p[1]-1] += 1

    print('Filtered from %d to %d, distribution: %s. With confidence_threshold=(%.2f, %.2f)' % (len(patterns),
                                                                                                len(res),
                                                                                                label_count,
                                                                                                threshold_for_minor,
                                                                                                threshold_for_major))
    pickle.dump(res, open(out, 'wb'))

    with open('%s-log.txt' % pattern_pkl[:-4], 'a') as f:
        f.write('filter end at: %s\n' % time.asctime(time.localtime(time.time())))
        f.write('%d patterns got in total.\n' % len(res))

    return res


def update_patterns(patterns, seqs):
    """
    update the confidence of mined patterns with precision
    :param patterns: patterns mined, a list of patterns
    :param configs_file: configuration sequences, a list of numbers
    :param labels_file: file in .npy format that contains the labels of labeled data
    :return: updated patterns
    """
    configs = [seq[:-1] for seq in seqs]
    labels = [seq[-1] for seq in seqs]
    res = []
    # patterns = sorted(patterns, key=lambda x: x[1])
    pbar = tqdm(patterns)
    for pattern in pbar:
        pbar.set_description('Updating patterns')
        support, conf = 0, 0
        for i in range(len(configs)):
            if is_subsequence(pattern[0], configs[i]):
                support += 1  # number of configs that contain this pattern
                if pattern[1] == labels[i]:
                    conf += 1  # number of configs that have same labels with this pattern
        pattern[2] = conf
        pattern[3] = conf / support if support else 0
        if pattern[3] > 0:  # discard patterns with 0 conf or 0 support
            # print(pattern)
            res.append(pattern)
    return res


def text2configs(file, token_dict, feature='svo'):
    """
    Convert the configuration parameters into sequences
    :param file: file contains all the configuration data in .csv
    :param token_dict: dict of tokens obtained by the data to be mined, type: dict
    :param feature: typically one of ['name', 'description', 'svo']
    :return: sequenced configuration parameters
    """
    data = pd.read_csv(file)
    if feature == 'name':
        texts = data[feature]
    else:
        texts = data['description']
    configs = []
    for text in texts:
        config = []
        doc = nlp(text)
        for token in doc:
            if feature == 'svo':
                if token.dep_ in target_dep:
                    if (token.dep_, token.lemma_) in token_dict:
                        config.append(token_dict[(token.dep_, token.lemma_)])
                    else:
                        config.append(0)
            elif feature == 'description':
                if token.pos_ in reserved_pos:
                    lemma = replace_syn(token)
                    if (token.pos_, lemma) in token_dict:
                        config.append(token_dict[(token.pos_, lemma)])
                    else:
                        config.append(0)
            elif feature == 'name':
                if token.lemma_ in token_dict:
                    config.append(token_dict[token.lemma_])
                else:
                    config.append(0)
        configs.append(config)
    return configs


def patterns2file(patterns, out, token_dict):
    """
    Store patterns to file, in a way human can read
    :param patterns: mined patterns in number, type: list
    :param out: file to store patterns in text
    :param token_dict: dict of tokens, number -> text
    :return:
    """
    with open(out, 'w') as f:
        for pattern in patterns:
            f.write('{')
            for p in pattern[0]:
                f.write(str(token_dict[p]) + ',')
            f.write('}, %s, %d, %.3f\n' % (label_dict_r[pattern[1]], pattern[2], pattern[3]))


def label_software(configs, patterns_all, patterns_minority):
    """
    Predict labels for unlabeled configuration parameters
    :param configs: converted sequences of configuration descriptions
    :param patterns_all: all patterns mined from labeled data
    :param patterns_minority: patterns mined from labeled data in minority classes
    :return: predicted labels, a list
    """
    # print(configs)
    pred_labels = []
    matched_patterns = []
    pbar = tqdm(configs)

    ws = []

    # for every configuration description to be expanded, try to match with patterns mined
    for i, config in enumerate(pbar):

        pbar.set_description('Labeling')

        pred_label,   count,   w   = label_config_2(patterns_all,
                                                    config)
        pred_label_m, count_m, w_m = label_config_2(patterns_minority,
                                                    config)
        # prefer mined patterns especially for those minority classes to prevent from being in performance-unrelated.
        if pred_label != pred_label_m and pred_label == 7 and max(w_m) > max(w)*5.0 and count + count_m != 0:
            pred_label = pred_label_m
            count = count_m
            w = w_m

        if count > 0:
            pred_labels.append(label_dict_r[pred_label])
            #matched_patterns.append(p)
        elif count_m > 0: # count == 0
            pred_labels.append(label_dict_r[pred_label_m])
            w = w_m
            #matched_patterns.append(p_m)
        else:
            pred_labels.append('')
            #matched_patterns.append([[], 0, 0, 0])

        ws.append(w)

    # `pred_labels` are string list!!
    return pred_labels, ws#, matched_patterns


def evaluate(labels_true, labels_pred, label_names, result_filename):
    """
    the evaluation metrics for automatic data expansion
    :param result_filename: output file name
    :param labels_true:
    :param labels_pred:
    :param label_names:
    :return:
        precision = TP/(TP+FP)
        recall = TP/(TP+FN)
    """
    counts = {}
    for label in label_names:
        counts[label] = [0, 0, 0]  # TP, TP+FP, TP+FN
    counts['performance-related'] = [0, 0, 0]
    for i in range(len(labels_pred)):
        # ********* for each type ************
        p_label, t_label = labels_pred[i], labels_true[i]
        counts[t_label][2] += 1
        if p_label != '':
            counts[p_label][1] += 1
            if p_label == t_label:
                counts[p_label][0] += 1
        # ********* for each type ************

        # ********* for performance-related ************
        if t_label != 'others':
            counts['performance-related'][2] += 1
        if p_label != '':
            if p_label != 'others':
                counts['performance-related'][1] += 1
                if t_label != 'others':
                    counts['performance-related'][0] += 1
        # ********* for performance-related ************

    with open(result_filename, 'a') as f:
        f.write('%25s\t%10s\t%10s\n' % ('Type', 'Precision', 'Recall'))
        for label in label_names:
            precision = counts[label][0] / counts[label][1] if counts[label][1] > 0 else 0
            recall = counts[label][0] / counts[label][2] if counts[label][2] > 0 else 0
            f.write('%25s\t%10.4f\t%10.4f\n' % (label, precision, recall))

        # ******* p&r for performance-related **********
        label = 'performance-related'
        precision = counts[label][0] / counts[label][1] if counts[label][1] > 0 else 0
        recall = counts[label][0] / counts[label][2]
        f.write('%25s\t%10.4f\t%10.4f\n' % (label, precision, recall))
        # ******* p&r for performance-related **********

        # ******* micro p&r for side-effect **********
        tot = sum([counts[label][1] for label in label_names if label != 'others'])
        micro_precision_6_types = sum([counts[label][0] for label in label_names if label != 'others']) / tot \
            if tot > 0 else 0

        micro_recall_6_types = sum([counts[label][0] for label in label_names if label != 'others']) / \
                               sum([counts[label][2] for label in label_names if label != 'others'])
        f.write('%25s\t%10.4f\t%10.4f\n' % ('micro_6_types', micro_precision_6_types, micro_recall_6_types))
        # ******* micro p&r for side-effect **********

        # ******* micro p&r **********
        tot = sum([counts[label][1] for label in label_names])
        micro_precision = sum([counts[label][0] for label in label_names]) / tot if tot > 0 else 0
        micro_recall = sum([counts[label][0] for label in label_names]) / \
                       sum([counts[label][2] for label in label_names])
        f.write('%25s\t%10.4f\t%10.4f\n' % ('micro', micro_precision, micro_recall))
        # ******* micro p&r **********
        f.write('*' * 80 + '\n')
        return micro_precision, micro_recall


def prefix_mining(seqs, minsup, out_filename, folder, maxlen=10, confidence_threshold=0.8):

    print('PrefixSpan mining starts at %s with minsup=%d, maxlen=%d' % (time.asctime(time.localtime(time.time())), minsup, maxlen))

    ps = PrefixSpan(seqs)
    ps.maxlen = maxlen
    tmp = ps.frequent(minsup, generator=True, filter=lambda patt, match: 1 <= patt[-1] <= 7)

    # pattern in patterns:
    #   [0] pattern itself,
    #   [1] pattern's label,
    #   [2] pattern's support,
    #   [3] 0(reserved for pattern's confidence)
    patterns = []
    num_p = [0, 0, 0, 0, 0, 0, 0]
    for (fre, pattern) in tmp:
        patterns.append([pattern[:-1], pattern[-1], fre, 0])
        num_p[pattern[-1]-1] += 1


    print('PrefixSpan mining ends at %s, got patterns: %s' % (time.asctime(time.localtime(time.time())), num_p))

    # Calculate confidence for each pattern.
    updated_patterns = update_patterns(patterns, seqs)
    pickle.dump(updated_patterns, open('%s/raw-%s' % (folder, out_filename), 'wb'))

    # Filter out redundant patterns.
    patterns_reserved = filter_cars(pattern_pkl='%s/raw-%s' % (folder, out_filename),
                                    out='%s/%s' % (folder, out_filename),
                                    threshold=confidence_threshold)
    return patterns_reserved


if __name__ == '__main__':


    confidence_threshold = 0.85
    scale = 0.2

    date = '%02d%02d' % (datetime.datetime.now().month,
                         datetime.datetime.now().day)
    data_folder = '.'
    out_folder = 'expand_out_%s' % date
    # os.rmdir(out_folder)

    # label_names = ['others',
    #                'resource',
    #                'limited-side-effect',
    #                'workload-specific',
    #                'function-tradeoff',
    #                'security-tradeoff',
    #                'reliability-tradeoff'
    #                ]
    label_names = list(label_dict.keys())
    minority_labels = label_names[1:-1]

    configs_all_path = Path('%s/configs_all.npy' % out_folder)
    labels_all_path = Path('%s/labels_all.npy' % out_folder)
    token_dict_path = Path('%s/id2token.pkl' % out_folder)  # do not change.

    rest_data = pd.read_csv('%s/data_all.csv' % data_folder)
    counts = rest_data['software'].value_counts()
    number_to_study = int(len(rest_data) * scale)

    if configs_all_path.exists() and labels_all_path.exists() and token_dict_path.exists():
        seqs_DB    = np.load(configs_all_path, allow_pickle=True)
        labels     = np.load(labels_all_path, allow_pickle=True)
    else:
        os.makedirs(out_folder, exist_ok=True)
        seqs_DB = np.array(tokens2id(rest_data, output_folder=out_folder, feature='description'))  # saved: id2token.pkl
        labels = np.array(rest_data['label'])
        np.save(configs_all_path, seqs_DB)
        np.save(labels_all_path, labels)
    token_dict = pickle.load(open(token_dict_path, 'rb'))  # dict[(pos, lemma)] = id

    index = list(range(len(labels)))
    id_dict = dict(zip(token_dict.values(), token_dict.keys()))  # dict[id] = (pos, lemma)

    # ------------------ mining and evaluation ------------------
    for seed in range(101, 110):
        sw = 'all'
        print('Software category: %s' % sw)
        outfolder = '%s/RandSeed-%d/Software-%s' % (out_folder, seed, sw)
        os.makedirs(outfolder, exist_ok=True)

        ###  May have problem
        study_index, expand_index = train_test_split(index, train_size=scale, random_state=seed)
        # study_index = list(np.load('%s/1/study_index.npy' % outfolder, allow_pickle=True))
        # expand_index = list(np.load('%s/1/expand_index.npy' % outfolder, allow_pickle=True))

        study_data, expand_data = rest_data.iloc[study_index], rest_data.iloc[expand_index]
        study_data.to_csv('%s/to_study_Initial.csv' % outfolder, index=False)
        expand_data.to_csv('%s/to_expand_Initial.csv' % outfolder, index=False)

        epochs = 0

        # store data that SUCCESSFULLY to be expanded this epoch
        index_to_add = []
        # store data that FAILED to be expanded this epoch, to be expanded in next epoch
        new_expand_index = expand_index
        # use the predicted label for those in `new_expand_index`
        labels_to_change = []

        while True:

            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print("[%s] Mining epoch: %s" % (current_time, epochs))
            patterns_folder = '%s/epoch-%s' % (outfolder, epochs)
            os.makedirs(patterns_folder, exist_ok=True)

            study_index = study_index + index_to_add
            expand_index = new_expand_index

            np.save('%s/study_index_ep%d.npy' % (patterns_folder, epochs), np.array(study_index))
            np.save('%s/expand_index_ep%d.npy' % (patterns_folder, epochs), np.array(expand_index))
            seq_study, seqs_expand = seqs_DB[study_index], seqs_DB[expand_index]

            for i in range(len(index_to_add)):
                seq_study[i-len(index_to_add)][-1] = labels_to_change[i]

            print('%s configs to study, %s configs to expand' % (len(seq_study), len(seqs_expand)))

            print('\n[===== Mining stage 1/2 =====]')
            patterns_all = prefix_mining(seq_study,
                                         minsup=3,
                                         out_filename='patterns_all.pkl',
                                         folder=patterns_folder,
                                         maxlen=5,
                                         confidence_threshold=confidence_threshold)
            patterns2file(patterns_all,
                          out='%s/patterns_in_text_all.txt' % patterns_folder,
                          token_dict=id_dict)

            print('\n[===== Mining stage 2/2 =====]')
            minority_index = [i for i in study_index if labels[i] in minority_labels]
            minority_seqs = seqs_DB[minority_index]
            patterns_minority = prefix_mining(minority_seqs,
                                              minsup=2,
                                              out_filename='patterns_minority.pkl',
                                              folder=patterns_folder,
                                              maxlen=6,
                                              confidence_threshold=confidence_threshold)
            patterns2file(patterns_minority,
                          out='%s/patterns_in_text_minority.txt' % patterns_folder,
                          token_dict=id_dict)

            print('\n[===== Labeling software =====]')
            pred_labels, ws = label_software(seqs_expand,
                                             patterns_all=patterns_all,
                                             patterns_minority=patterns_minority)

            # store data that SUCCESSFULLY to be expanded this epoch
            index_to_add = []
            # store data that FAILED to be expanded this epoch, to be expanded in next epoch
            new_expand_index = []
            # use the predicted label for those in `new_expand_index`
            labels_to_change = []

            yPred, yTrue = [], []
            label_count = [0, 0, 0, 0, 0, 0, 0]
            for i in range(len(expand_index)):
                if pred_labels[i] != '':    # match this time, expanded SUCCESSFULLY.
                    index_to_add.append(expand_index[i])
                    #labels_to_change.append(label_dict[pred_labels[i]])  # Then, mark those labels.
                    yPred.append(label_dict[pred_labels[i]])
                    label_count[label_dict[pred_labels[i]]-1] += 1
                else:                       # FAILED to match any pattern, to be expanded next epoch.
                    new_expand_index.append(expand_index[i])
            print('  [Preserved] Expand from %d to %d,\n              %d to be expanded.' % (len(seq_study),
                                                                                             len(seq_study)+len(index_to_add),
                                                                                             len(new_expand_index)))
            print('Numbers of those expanded (from label 1 to label 7): %s' % label_count)
            yTrue = [label_dict[a] for a in labels[index_to_add]]

            np.save('%s/successfully_expanded_at_ep%d(index-of-X).npy' % (patterns_folder, epochs), np.array(index_to_add))
            np.save('%s/successfully_expanded_at_ep%d(label-of-y).npy' % (patterns_folder, epochs), np.array(labels_to_change))
            np.save('%s/to_be_expanded_after_ep%d.npy' % (patterns_folder, epochs), np.array(new_expand_index))

            print('\n[===== Evaluating Results =====]')

            target_names = np.array(['resource', 'security-tradeoff', 'reliability-tradeoff',
                                     'limited-side-effect', 'workload-specific', 'function-tradeoff',
                                     'others'])

            print(classification_report(y_true=yTrue,
                                        y_pred=yPred,
                                        target_names=list(target_names)))

            if len(new_expand_index) < 2:
                break
            else:
                epochs += 1
