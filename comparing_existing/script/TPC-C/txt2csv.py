import sys
import re
import numpy as np
import matplotlib.pyplot as plt


helpstring = "Two Arguements is needed:\n\t(1) log file name (e.g., LOG_fsync.txt)\n\t(2) interested metric, know supports (latency, throughput)"
if len(sys.argv) != 3:
    print(helpstring)
    exit(0)

txt_file = open(sys.argv[1], 'r')
txt_contents = txt_file.readlines()

#THROUGHPUT 0 (TPS)
#LATENCY    1 (95% latency)
TPS_OR_QPS = 6 # 8=QPS 6=TPS
if sys.argv[2] == 'latency':
    MEASUREMENT = 1
elif sys.argv[2] == 'throughput':
    MEASUREMENT = 0
else:
    print ('Arguements 2 is wrong!\n' + helpstring)
    exit()


disks = set()
configurations = set()
data = {}


disk_idx = ''
conf_idx = ''
tmp_data = []


def disk_compare(dk):
    if dk == 'nvme-optane':
        return 1
    elif dk == 'nvme-sn850':
        return 3
    elif dk == 'nvme-980pro':
        return 5
    elif dk == 'sata-s4510':
        return 6
    elif dk == 'sata-860evo':
        return 7
    elif dk == 'hdd-sas-dell':
        return 9
    elif dk == 'hdd-smr-sg':
        return 11
    else:
        return 100


def size_compare(sz):
    sz = sz.split('=')[1]
    if type(sz) == type(0) or type(sz) == type(0.1):
        return sz
    if type(sz) == type('0'):
        if sz[-2:] in {'MB', 'KB', 'GB', 'kB'}:
            cuz = -2
        else:
            cuz = -1
        if sz[cuz] == 'M' or sz[cuz] == 'm':
            try:
                return 1024*int(sz[:cuz])
            except ValueError:
                return sz
        elif sz[cuz] == 'G' or sz[cuz] == 'g':
            try:
                return 1024*1024*int(sz[:cuz])
            except ValueError:
                return sz
        elif sz[cuz] == 'K' or sz[cuz] == 'k':
            try:
                return int(sz[:cuz])
            except ValueError:
                return sz
        else:
            try:
                return float(sz)
            except ValueError:
                return sz
    else:
        return sz


for line in txt_contents:

    if line[0] == '@':
        continue


    if line.startswith('[configuration]:'):
        conf_idx = line.split(' ')[1].strip()
        configurations.add(conf_idx)
        data[conf_idx] = {}
        continue

    if line.startswith('[device]:'):
        disk_idx = line.split(' ')[1].strip()
        disks.add(disk_idx)
        data[conf_idx][disk_idx] = []
        continue

    if line.startswith('[ ') and line.find('reconn/s') != -1:
        tmp_data = [line.split(' ')[TPS_OR_QPS], line.split(' ')[13]]
        data[conf_idx][disk_idx].append(tmp_data.copy())
        tmp_data.clear()
        continue

txt_file.close()
# print(data)

'''
csv_file = open(sys.argv[1].replace('LOG', 'RES').split('.')[0]+'.csv', 'w')

disks = list(disks)
disks.sort()
configurations = list(configurations)
configurations.sort(key=size_compare)
for dsk in disks:
    csv_file.write('%s,' % dsk)
    for cnf in configurations:
        csv_file.write('Value=%s, TransactionsPerSecond, 95%% Latency,,' % cnf)
    csv_file.write('\n')

    for rowid in range(len(data[cnf][dsk])):
        csv_file.write(',')
        for cnf2 in configurations:
            try:
                csv_file.write(',%s,,' % ', '.join(data[cnf2][dsk][rowid]))
            except IndexError:
                csv_file.write(',,,')
        csv_file.write('\n')
    csv_file.write('\n')

csv_file.close()
'''

Y = []
YY = []
X = []

disks = list(disks)
disks.sort(key=disk_compare)
print('\n==== Devices ====')
print(disks)

configurations = list(configurations)
configurations.sort(key=size_compare)
print('\n==== Configurations ====')
print(configurations)

print("\n==== Raw Data ====")
print(data)
print('')

for dsk in disks:
    y = []
    yyy = []
    for cnf in configurations:
        y.append(
            np.mean(
                [(float(data[cnf][dsk][a][MEASUREMENT])) for a in range(len(data[cnf][dsk]))]
            )
        )
        yyy.append(
            [(float(data[cnf][dsk][a][MEASUREMENT])) for a in range(len(data[cnf][dsk]))]
        )
    Y.append(y.copy())
    YY.append(yyy.copy())
    y.clear()
    yyy.clear()
X = disks
Y = np.asarray(Y)
YY = np.asarray(YY)

figure, axes = plt.subplots(1, 2, figsize=(15, 7))


n = len(configurations)
m = len(disks)
width = 3.0 / ((float(n)*float(m)) + 4)
if n==2:
    width = width*0.9
xx = list(range(n))
colors = ['royalblue',  'cornflowerblue', 'darkgreen', 'darkseagreen', 'tan', 'peru']
'''
for idx, yy in enumerate(Y):
    axes[0].bar(xx, yy, width=width, label=disks[idx], tick_label=configurations, color=colors[idx])
    mean = np.mean(yy)
    axes[1].bar(xx, np.asarray([y/yy[0] for y in yy]), width=width, label=disks[idx], tick_label=configurations, color=colors[idx])
    for nn in range(n):
        xx[nn] = xx[nn] + width
'''
poses = []

for idx, yy in enumerate(YY):
    #axes[0].bar(xx, [0 for asdf in yy], width=width, label=disks[idx], color=colors[idx])
    axes[1].bar(xx, [0 for asdf in yy], width=width, label=disks[idx], color=colors[idx])

    #if idx == len(YY)//2:
    #    lab = configurations
    #else:
    #    lab = ['' for a in configurations]

    bplot1 = axes[0].boxplot(x=yy.tolist(),
                    meanline=True,
                    positions=xx,
                    #labels=lab,
                    #notch=True,
                    patch_artist=True,
                    widths=0.45/(1+n))
    mean = np.median(yy[0])
    #axes[1].violinplot([(y/mean).tolist() for y in yy], positions=xx, showmedians=True, widths=0.45/(1+n))

    bplot2 = axes[1].boxplot(x=[(y/mean).tolist() for y in yy],
                    meanline=True,
                    positions=xx,
                    #labels=lab,
                    #notch=True,
                    patch_artist=True,
                    widths=0.6/(n+1))

    axes[0].set_xticks([])
    axes[1].set_xticks([])

    poses.append(xx.copy())
    for nn in range(n):
        xx[nn] = xx[nn] + width

    for bplot in (bplot1, bplot2):
        for patch, color in zip(bplot['boxes'], [colors[idx] for asss in configurations]):
            patch.set_facecolor(color)

splits_x = ((np.asarray(poses[0][1:]) + np.asarray(poses[-1][:-1]))/2).tolist()

rotation = 0
try:
    if np.asarray([len(cc) for cc in configurations]).max() > 8:
        rotation = 20
except TypeError:
    pass

axes[0].yaxis.grid(True, linestyle='dashed')
axes[0].set_xlabel('Configuration value')
axes[0].set_ylabel(sys.argv[2])
axes[0].set_xticks((np.asarray(range(n)) + 1.0/n).tolist())
axes[0].set_xticklabels(configurations, rotation=rotation)
axes[0].vlines(
    splits_x,
    0, 1,
    transform=axes[0].get_xaxis_transform(),
    color='gray',
    #linestyles='dashed',
    linewidth=1)

axes[1].vlines(
    splits_x,
    0, 1,
    transform=axes[1].get_xaxis_transform(),
    color='gray',
    #linestyles='dashed',
    linewidth=1)

axes[1].yaxis.grid(True, linestyle='dashed')
axes[1].set_xlabel('Configuration value')
axes[1].set_ylabel(sys.argv[2] + ' (normalized)')
axes[1].legend()

#axes[1].set(ylim=(0.5, 1.3))

axes[0].set_title(configurations[0].split('=')[0])
axes[1].set_title(configurations[0].split('=')[0])

plt.xticks((np.asarray(range(n)) + 1.0/n).tolist(), configurations, rotation=rotation)

plt.savefig(sys.argv[1].replace('LOG', 'RES').split('.')[0] + '(' + sys.argv[2] +').png')
print("Saving done.")
plt.show()