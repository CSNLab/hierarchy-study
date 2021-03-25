#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import pandas as pd
import os
import pickle as pkl

# Path
BIDS_DIR = '/u/project/cparkins/data/hierarchy/'
ATTR_DIR = '/u/project/cparkins/data/hierarchy/derivatives/lv1/tstats/'
TASK_RUNS = {'nav': 6, 'sacc': 2}
OUTFILE = '/u/project/cparkins/data/hierarchy/derivatives/lv1/good_trials.pkl'

def main():
    nonsteady = pd.read_csv('unsteady_vols.csv', index_col=0)
    subjects = nonsteady.index.tolist()
    trials = {}
    for task in TASK_RUNS:
        trials[task] = {}
        # trial attributes
        task_fname = 'face' if task == 'nav' else task
        attr_file = ATTR_DIR + ('sac' if task == 'sacc' else task) + '_trialwise_attr_bin.txt'
        attrs = pd.read_csv(attr_file, sep=' ', header=None)[0].unique()
        if task == 'sacc':
            attrs = [attr[4:] for attr in attrs]  # 'eye_up' -> 'up'
        elif task == 'nav':
            attrs = [attr[0] for attr in attrs]   # 'up' -> 'u'
        for subj in subjects:
            trials[task][subj] = {}
            for run in range(1, TASK_RUNS[task] + 1):
                # get event file
                fname = BIDS_DIR + subj + '/func/%s_task-%s_run-0%d_events.tsv' % (subj, task_fname, run)
                events = pd.read_csv(fname, sep='\t')
                # reorder events based on attributes
                col = 'direction'
                ord_events = pd.concat([events[events[col] == attr] for attr in attrs])
                if len(ord_events) == 0:
                    print(subj, task, run, attrs, events)
                trial1_index = ord_events.index.get_loc(0)
                # correct
                if task == 'nav':
                    trial_bools = list(ord_events.correct)
                else:
                    trial_bools = [True] * len(ord_events)
                # steady
                n_trial1_nonsteady = nonsteady[task_fname + str(run).zfill(2)][subj]
                if n_trial1_nonsteady > 0:
                    trial_bools[trial1_index] = n_trial1_nonsteady
                trials[task][subj][run] = trial_bools
    print(trials)
    with open(OUTFILE, 'wb') as pkl_file:
        pkl.dump(trials, pkl_file, protocol=2)

if __name__ == '__main__':
    main()
