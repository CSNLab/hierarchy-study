import json
import os
import csv
import numpy as np
from scipy.stats import sem


DATA_FOLDER = '../navigation_data/'
CSV_FILE = 'navigation_data.csv'


def rt_stats(sdata, direction_rt, direction_counters):
    for indexes in [(0, 3), (1, 2), (4, 7), (5, 6)]:
        group = np.concatenate((direction_rt[indexes[0]], direction_rt[indexes[1]]))
        rt_mean = np.mean(group)
        rt_sem = sem(group)
        sdata.append('%.0f ' % rt_mean)
        sdata.append('%.0f' % rt_sem)
        sdata.append(str(len(group)))
        sdata.append(str(direction_counters[indexes[0]] + direction_counters[indexes[1]]))
    for i in range(8):
        rt_mean = np.mean(direction_rt[i])
        rt_sem = sem(direction_rt[i])
        sdata.append('%.0f ' % rt_mean)
        sdata.append('%.0f' % rt_sem)
        sdata.append(str(len(direction_rt[i])))
        sdata.append(str(direction_counters[i]))


# main
all_data = {}
subj_stats = {}
for datafile in sorted(os.listdir(DATA_FOLDER)):
    if not datafile.endswith('.txt') or not datafile[0].isdigit():
        continue
    if 'questions' in datafile:
        continue
    sid = int(datafile[:3])
    session = datafile[4:-4] if len(datafile) > 7 else 'behavioral'
    if sid not in subj_stats:
        # stats: resp_counter, correct_counter, trial_counter, direction_rt_list, direction_counters_list
        subj_stats[sid] = [0, 0, 0, [[] for _ in range(8)], [0 for _ in range(8)]]
    with open(DATA_FOLDER + datafile, 'r') as infile:
        prac_counter, real_counter, prac_correct, real_correct, prac_resp, real_resp = 0, 0, 0, 0, 0, 0
        accuracy = 0
        # 0: top + more powerful, 1: top + less powerful, 2: bottom + more powerful, 3: bottom + less powerful,
        # 4: left + more powerful, 5: left + less powerful, 6: right + more powerful, 7: right + less powerful
        # top/bottom/left/right means the location of the correct option
        direction_counters = [0 for _ in range(8)]
        direction_rt = [[] for _ in range(8)]
        for ln_num, ln in enumerate(infile):
            # load in data file
            jdict = json.loads(ln)

            # extract data output from training and testing blocks separately
            if 'response' in jdict:
                if 'practice' in jdict:
                    prac_counter += 1
                    if jdict['response'] is not None:
                        prac_resp += 1
                        if 'correct' in jdict and jdict['correct']:
                            prac_correct += 1
                else:  # a normal trial
                    real_counter += 1
                    correct_option = jdict['anchor'] + (-1 if jdict['direction'] == 'U' else 1) * jdict['distance']
                    type_index = 2 * jdict['options'].index(correct_option)
                    type_index += int(jdict['direction'] == 'D')
                    direction_counters[type_index] += 1
                    if jdict['response'] is not None:
                        real_resp += 1
                        if 'correct' in jdict and jdict['correct']:
                            real_correct += 1
                            direction_rt[type_index].append(np.float64(jdict['rt']) * 1000)  # rt in ms
            elif 'accuracy' in jdict:
                accuracy = jdict['accuracy']
            elif 'overall_accuracy' in jdict:
                accuracy = jdict['overall_accuracy']

        # response rate & accuracy
        sdata = [sid, session,
                 '%.4f' % (real_resp * 100.0 / real_counter) + '%',
                 '%.4f' % (real_correct * 100.0 / real_resp) + '%',
                 '%.4f' % (accuracy * 100) + '%']
        rt_stats(sdata, direction_rt, direction_counters)

        # add to results
        subj_stats[sid][0] += real_resp
        subj_stats[sid][1] += real_correct
        subj_stats[sid][2] += real_counter
        for i in range(8):
            subj_stats[sid][3][i] += direction_rt[i]
            subj_stats[sid][4][i] += direction_counters[i]

        if sid not in all_data:
            all_data[sid] = {}
        all_data[sid][session] = sdata

# overall stats
for sid in subj_stats:
    resp_rate = subj_stats[sid][0] * 100.0 / subj_stats[sid][2]
    resp_acc = subj_stats[sid][1] * 100.0 / subj_stats[sid][0]
    sdata = [sid, 'overall',
             '%.4f' % resp_rate + '%',
             '%.4f' % resp_acc + '%',
             '%.4f' % (resp_rate * resp_acc / 100) + '%']
    rt_stats(sdata, subj_stats[sid][3], subj_stats[sid][4])
    all_data[sid]['overall'] = sdata

with open(CSV_FILE, 'w') as outfile:
    writer = csv.writer(outfile, delimiter=',')
    writer.writerow(['id', 'session', 'response rate', 'response accuracy', 'overall accuracy',
                     'top-down', 'stderr', 'accuracy', '',
                     'bottom-up', 'stderr', 'accuracy', '',
                     'left-right', 'stderr', 'accuracy', '',
                     'right-left', 'stderr', 'accuracy', '',
                     'top, more powerful', 'stderr', 'accuracy', '',
                     'top, less powerful', 'stderr', 'accuracy', '',
                     'bottom, more powerful', 'stderr', 'accuracy', '',
                     'bottom, less powerful', 'stderr', 'accuracy', '',
                     'left, more powerful', 'stderr', 'accuracy', '',
                     'left, less powerful', 'stderr', 'accuracy', '',
                     'right, more powerful', 'stderr', 'accuracy', '',
                     'right, less powerful', 'stderr', 'accuracy', ''])
    for sid in sorted(all_data):
        for session in ('behavioral', 'pre_scan', 'scanner', 'overall'):
            if session in all_data[sid]:
                writer.writerow(all_data[sid][session])
