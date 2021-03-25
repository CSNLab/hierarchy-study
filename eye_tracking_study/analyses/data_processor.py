#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import pandas as pd
import json
import os


EXCLUDING = {202, 204, 207, 210, 216, 244}  # eye tracker crashes except that 202 is non-native English speaker, 244 didn't pass learning


def is_valid(subj_accuracy, criterion, which_method):
    """
    :param which_method: 0 or 1
                         0: use the average accuracy accross two sections
                         1: use the accuracy in the 1st section
    """
    # return True
    if which_method == 0:  # 72 trials/section
        return (int(subj_accuracy[0] * 72) + int(subj_accuracy[1] * 72)) / (72 * 2) > criterion
    return subj_accuracy[0] > criterion


def get_subj_trial_info(directory, which_method):
    """
    :return: { sid: { 'up_trials': { ... }, 'down_trials': { ... } } }
    """
    subj_acc = {}
    subj_trials = {}
    for filename in os.listdir(directory):
        if (not filename.endswith('1.txt')) and (not filename.endswith('2.txt')):
            continue
        # get sid & section
        sid = filename[:3]
        section = filename[-5]
        if int(sid) in EXCLUDING:
            continue
        if sid not in subj_acc:
            subj_acc[sid] = [-1, -1]  # two sections of accuracy
            subj_trials[sid] = {'1': {'up_trials': set(), 'down_trials': set()},
                                '2': {'up_trials': set(), 'down_trials': set()}}
        with open(directory + filename, 'r') as subjfile:
            content = subjfile.readlines()
            # get accuracy
            try:
                accuracy = float(json.loads(content[-1])['overall_accuracy'])  # on the last line
            except KeyError:
                print('Incomplete file ' + filename)
                continue
            subj_acc[sid][int(section) - 1] = accuracy
            # get trial info
            trials = [json.loads(line) for line in content[4:-1]]
            if 'trial_index' not in trials[0] or trials[0]['trial_index'] != 1 or trials[-1]['trial_index'] != 72:
                raise RuntimeError('Something is wrong in ' + filename)  # error checking
            for trial in trials:
                if trial['direction'] == 'U':
                    subj_trials[sid][section]['up_trials'].add(trial['trial_index'])
                elif trial['direction'] == 'D':
                    subj_trials[sid][section]['down_trials'].add(trial['trial_index'])
                else:
                    raise RuntimeError('Something is wrong in %s, trial #%d' % (filename, trial['trial_index']))

    return {subj: subj_trials[subj] for subj in subj_acc if is_valid(subj_acc[subj], 0.7, which_method)}


def get_trial_id_from_str(trial_tag):
    return int(trial_tag.split('#')[1].split(' ')[0])


def get_tracker_data(directory, subj_trial_info, outfile):
    result_df = pd.DataFrame()
    for subj in sorted(subj_trial_info):
        print('Subject ' + subj)
        for section in ('1', '2'):
            filename = '%s_tracker_%s.tsv' % (subj, section)
            df = pd.read_csv(directory + filename, sep='\t', header=0, index_col=False)
            nav_start_indexes = df.index[df['state'].str.contains('navigation starts')]
            nav_end_indexes = df.index[df['state'].str.contains('navigation ends')]
            prev_i, prev_j = -2, -1
            for i, j in zip(nav_start_indexes, nav_end_indexes):
                # error checking
                trial_id = get_trial_id_from_str(df['state'].loc[i])
                if i >= j or i <= prev_j or trial_id != get_trial_id_from_str(df['state'].loc[j]):
                    raise RuntimeError('Something is wrong with the navigation tags at line #' + ', '.join([prev_j, i, j]))
                if trial_id not in subj_trial_info[subj][section]['up_trials'] and \
                   trial_id not in subj_trial_info[subj][section]['down_trials']:
                    raise RuntimeError('Something is wrong with the type of trial #%d' % trial_id)
                prev_i, prev_j = i, j
                # get data
                trial_df = df[i + 1:j][['rawx', 'rawy']]
                trial_df['subject'] = subj
                trial_df['section'] = int(section)
                trial_df['trial'] = trial_id
                trial_df['trial_type'] = 'up' if trial_id in subj_trial_info[subj][section]['up_trials'] else 'down'
                result_df = result_df.append(trial_df, ignore_index=True)
    result_df.to_csv(outfile, index=False)


def summarize(raw_data_file, outfile):
    df = pd.read_csv(raw_data_file)
    # excluding invalid values
    df = df.loc[(df.rawx > 0) & (df.rawx < 1920) & (df.rawy > 0) & (df.rawy < 1080)]
    # get medians of each trial
    grouped = df.groupby(['subject', 'section', 'trial', 'trial_type'])
    trial_median_x = grouped.rawx.median()
    trial_median_y = grouped.rawy.median()
    # average accross trials to get a mean for each subject
    subj_mean_x = trial_median_x.groupby(['subject', 'trial_type']).mean()
    subj_mean_y = trial_median_y.groupby(['subject', 'trial_type']).mean()
    # write to csv
    result = []
    for subj in df['subject'].unique():
        result.append([subj, subj_mean_x[subj]['up'], subj_mean_x[subj]['down'],
                       subj_mean_y[subj]['up'], subj_mean_y[subj]['down']])
    result_df = pd.DataFrame(result, columns=['subject', 'mean_x_up', 'mean_x_down', 'mean_y_up', 'mean_y_down'])
    result_df.to_csv(outfile, index=False)


def main():
    subj_trial_info = get_subj_trial_info('../navigation_behavioral_data/', 0)
    get_tracker_data('../navigation_eyetracker_log/', subj_trial_info, 'eye_data.csv')
    summarize('eye_data.csv', 'eye_data_summary.csv')


if __name__ == '__main__':
    main()
