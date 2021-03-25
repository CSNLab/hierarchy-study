#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
This script was adapted from
https://github.com/poldrack/fmri-analysis-vm/blob/master/analysis/postFMRIPREPmodelling/First%20and%20Second%20Level%20Modeling%20(FSL).ipynb
"""

import nipype.algorithms.modelgen as model   # model generation
from nipype.interfaces import fsl
from nipype.interfaces.base import Bunch
from nipype.caching import Memory
from bids.grabbids import BIDSLayout
import pandas as pd
import os
import sys


# Path
BIDS_DIR = '/u/project/cparkins/data/hierarchy/'
PREPROC_DIR = '/u/project/cparkins/data/hierarchy/fmriprep/output/fmriprep/'
MEM_DIR = '/u/project/cparkins/data/hierarchy/derivatives/lv1/work/%s/' % sys.argv[1]
# Subjects & runs
SUBJECTS = ['132', '133', '134', '136', '137', '138', '139', '142', '143', '144', '145', '146', '148']
EXCLUDING = {}  # excluding the 6th run from the 5th subject in the above list (sub-137, run-06) only for nav-multi
# Experiment info
if sys.argv[1] == 'nav-bin':
    task = 'face'
    num_runs = 6
    conditions = ['u', 'd']
    onsets = lambda event: [list(event[event.direction == 'u'].onset),
                            list(event[event.direction == 'd'].onset)]
    durations = lambda event: [list(event[event.direction == 'u'].duration - 2),
                               list(event[event.direction == 'd'].duration - 2)]
    up_cond = ['u', 'T', ['u'], [1]]
    down_cond = ['d', 'T', ['d'], [1]]
    all_nav = ['all nav', 'F', [up_cond, down_cond]]
    contrasts = [up_cond, down_cond, all_nav]

elif sys.argv[1] == 'nav-multi':
    EXCLUDING = {4: 5}  # excluding the 6th run from the 5th subject in the above list (sub-137, run-06)
    task = 'face'
    num_runs = 6
    conditions = ['u2', 'u3', 'u4', 'd2', 'd3', 'd4']
    onsets = lambda event: [list(event[(event.direction == 'u') & (event.steps == 2)].onset),
                            list(event[(event.direction == 'u') & (event.steps == 3)].onset),
                            list(event[(event.direction == 'u') & (event.steps == 4)].onset),
                            list(event[(event.direction == 'd') & (event.steps == 2)].onset),
                            list(event[(event.direction == 'd') & (event.steps == 3)].onset),
                            list(event[(event.direction == 'd') & (event.steps == 4)].onset)]
    durations = lambda event: [list(event[(event.direction == 'u') & (event.steps == 2)].duration - 2),
                               list(event[(event.direction == 'u') & (event.steps == 3)].duration - 2),
                               list(event[(event.direction == 'u') & (event.steps == 4)].duration - 2),
                               list(event[(event.direction == 'd') & (event.steps == 2)].duration - 2),
                               list(event[(event.direction == 'd') & (event.steps == 3)].duration - 2),
                               list(event[(event.direction == 'd') & (event.steps == 4)].duration - 2)]
    u2_cond = ['u2','T', ['u2'], [1]]
    d2_cond = ['d2','T', ['d2'], [1]]
    u3_cond = ['u3','T', ['u3'], [1]]
    d3_cond = ['d3','T', ['d3'], [1]]
    u4_cond = ['u4','T', ['u4'], [1]]
    d4_cond = ['d4','T', ['d4'], [1]]
    all_nav = ['all nav', 'F', [u2_cond, d2_cond, u3_cond, d3_cond, u4_cond, d4_cond]]
    contrasts = [u2_cond, d2_cond, u3_cond, d3_cond, u4_cond, d4_cond, all_nav]

elif sys.argv[1] == 'face':
    EXCLUDING = {4: 5}  # excluding the 6th run from the 5th subject in the above list (sub-137, run-06)
    task = 'face'
    num_runs = 6
    conditions = ['no2', 'no3', 'no4', 'no5', 'no6']
    onsets = lambda event: [list(event[event.anchor == 2].onset - 2),
                            list(event[event.anchor == 3].onset - 2),
                            list(event[event.anchor == 4].onset - 2),
                            list(event[event.anchor == 5].onset - 2),
                            list(event[event.anchor == 6].onset - 2)]
    durations = lambda event: [list(event[event.anchor == 2].duration - 5),
                               list(event[event.anchor == 3].duration - 5),
                               list(event[event.anchor == 4].duration - 5),
                               list(event[event.anchor == 5].duration - 5),
                               list(event[event.anchor == 6].duration - 5)]
    num2_cond = ['no2','T', ['no2'], [1]]
    num3_cond = ['no3','T', ['no3'], [1]]
    num4_cond = ['no4','T', ['no4'], [1]]
    num5_cond = ['no5','T', ['no5'], [1]]
    num6_cond = ['no6','T', ['no6'], [1]]
    all_face = ['all face', 'F', [num2_cond, num3_cond, num4_cond, num5_cond, num6_cond]]
    contrasts = [num2_cond, num3_cond, num4_cond, num5_cond, num6_cond, all_face]

elif sys.argv[1] == 'sac':
    task = 'sacc'
    num_runs = 2
    conditions = ['up', 'down', 'left', 'right']
    onsets = lambda event: [list(event[event.direction == 'up'].onset),
                            list(event[event.direction == 'down'].onset),
                            list(event[event.direction == 'left'].onset),
                            list(event[event.direction == 'right'].onset)]
    durations = lambda event: [list(event[event.direction == 'up'].duration),
                               list(event[event.direction == 'down'].duration),
                               list(event[event.direction == 'left'].duration),
                               list(event[event.direction == 'right'].duration)]
    up_cond = ['up','T', ['up'], [1]]
    down_cond = ['down','T', ['down'], [1]]
    left_cond = ['left','T', ['left'], [1]]
    right_cond = ['right','T', ['right'], [1]]
    all_sacc = ['all sacc', 'F', [up_cond, down_cond, left_cond, right_cond]]
    contrasts = [up_cond, down_cond, left_cond, right_cond, all_sacc]


def get_events(func_files):
    events = []
    for s in range(len(SUBJECTS)):
        events.append([])
        for r in range(num_runs):
            subj = func_files[s][r].subject
            if num_runs == 1:
                filename = 'sub-%s/func/sub-%s_task-%s_events.tsv' % (subj, subj, task)
            else:
                run = func_files[s][r].run
                filename = 'sub-%s/func/sub-%s_task-%s_run-%s_events.tsv' % (subj, subj, task, run.zfill(2))
            events[s].append(pd.read_csv(os.path.join(BIDS_DIR, filename), sep="\t"))
    return events


def get_confounds(func_files):
    confounds = []
    for s in range(len(SUBJECTS)):
        confounds.append([])
        for r in range(num_runs):
            func_file = func_files[s][r]
            if num_runs == 1:
                tsvname = 'sub-%s_task-%s_bold_confounds.tsv' % (func_file.subject, task)
            else:
                tsvname = 'sub-%s_task-%s_run-%s_bold_confounds.tsv' % (func_file.subject, task, func_file.run.zfill(2))
            confounds[s].append(pd.read_csv(os.path.join(PREPROC_DIR,
                                                         'sub-%s' % func_file.subject,
                                                         'func',
                                                         tsvname),
                                            sep="\t", na_values='n/a'))
    return confounds


def get_info(events, confounds):
    info = []
    for s in range(len(SUBJECTS)):
        info.append([])
        for r in range(num_runs):
            event = events[s][r]
            info[s].append([Bunch(conditions=conditions,
                                  onsets=onsets(event),
                                  durations=durations(event),
                                  regressors=[list(confounds[s][r].FramewiseDisplacement.fillna(0)),
                                              list(confounds[s][r].aCompCor00),
                                              list(confounds[s][r].aCompCor01),
                                              list(confounds[s][r].aCompCor02),
                                              list(confounds[s][r].aCompCor03),
                                              list(confounds[s][r].aCompCor04),
                                              list(confounds[s][r].aCompCor05),
                                              list(confounds[s][r].X),
                                              list(confounds[s][r].Y),
                                              list(confounds[s][r].Z),
                                              list(confounds[s][r].RotX),
                                              list(confounds[s][r].RotY),
                                              list(confounds[s][r].RotZ)],
                                  regressor_names=['FramewiseDisplacement',
                                                   'aCompCor00',
                                                   'aCompCor01',
                                                   'aCompCor02',
                                                   'aCompCor03',
                                                   'aCompCor04',
                                                   'aCompCor05',
                                                   'X',
                                                   'Y',
                                                   'Z',
                                                   'RotX',
                                                   'RotY',
                                                   'RotZ'])])
    return info


def specify_model(layout, func_files, info):
    specify_model_results = []
    for s in range(len(SUBJECTS)):
        specify_model_results.append([])
        for r in range(num_runs):
            if s in EXCLUDING and EXCLUDING[s] == r:
                continue
            func_file = func_files[s][r]
            if num_runs == 1:
                filename = 'sub-%s_task-%s_bold_space-T1w_preproc.nii.gz' % (func_file.subject, task)
            else:
                filename = 'sub-%s_task-%s_run-%s_bold_space-T1w_preproc.nii.gz' % (func_file.subject, task, func_file.run.zfill(2))
            spec = model.SpecifyModel()
            spec.inputs.input_units = 'secs'
            spec.inputs.functional_runs = [os.path.join(
                PREPROC_DIR,
                'sub-%s' % func_file.subject,
                'func',
                filename
            )]
            spec.inputs.time_repetition = layout.get_metadata(func_files[s][r].filename)['RepetitionTime']
            spec.inputs.high_pass_filter_cutoff = 128.
            spec.inputs.subject_info = info[s][r]
            specify_model_results[s].append(spec.run())
    return specify_model_results


def lv1_design(mem, layout, func_files, specify_model_results):
    level1design = mem.cache(fsl.model.Level1Design)
    level1design_results = []
    for s in range(len(SUBJECTS)):
        level1design_results.append([])
        for r in range(num_runs):
            if s in EXCLUDING and EXCLUDING[s] == r:
                continue
            tr = layout.get_metadata(func_files[s][r].filename)['RepetitionTime']
            level1design_results[s].append(level1design(
                interscan_interval=tr,
                bases={'dgamma': {'derivs': True}},
                session_info=specify_model_results[s][r].outputs.session_info,
                model_serial_correlations=True,
                contrasts=contrasts
            ))
    return level1design_results


def feat_model(mem, level1design_results):
    modelgen = mem.cache(fsl.model.FEATModel)
    modelgen_results = []
    for s in range(len(SUBJECTS)):
        modelgen_results.append([])
        for r in range(num_runs):
            if s in EXCLUDING and EXCLUDING[s] == r:
                continue
            modelgen_results[s].append(
                modelgen(fsf_file=level1design_results[s][r].outputs.fsf_files,
                         ev_files=level1design_results[s][r].outputs.ev_files))
    return modelgen_results


def masking(mem, func_files):
    mask = mem.cache(fsl.maths.ApplyMask)
    mask_results = []
    for s in range(len(SUBJECTS)):
        mask_results.append([])
        for r in range(num_runs):
            if s in EXCLUDING and EXCLUDING[s] == r:
                continue
            subj = func_files[s][r].subject
            if num_runs == 1:
                preproc_name = 'sub-%s_task-%s_bold_space-T1w_preproc.nii.gz' % (subj, task)
                mask_name = 'sub-%s_task-%s_bold_space-T1w_brainmask.nii.gz' % (subj, task)
            else:
                run = func_files[s][r].run
                preproc_name = 'sub-%s_task-%s_run-%s_bold_space-T1w_preproc.nii.gz' % (subj, task, run.zfill(2))
                mask_name = 'sub-%s_task-%s_run-%s_bold_space-T1w_brainmask.nii.gz' % (subj, task, run.zfill(2))
            mask_results[s].append(
                mask(in_file=os.path.join(PREPROC_DIR,
                                          'sub-%s' % subj,
                                          'func',
                                          preproc_name),
                     mask_file=os.path.join(PREPROC_DIR,
                                            'sub-%s' % subj,
                                            'func',
                                            mask_name)))
    return mask_results


def film_gls(mem, mask_results, modelgen_results):
    filmgls = mem.cache(fsl.FILMGLS)
    filmgls_results = []
    for s in range(len(SUBJECTS)):
        filmgls_results.append([])
        for r in range(num_runs):
            if s in EXCLUDING and EXCLUDING[s] == r:
                continue
            filmgls_results[s].append(filmgls(in_file=mask_results[s][r].outputs.out_file,
                                              design_file=modelgen_results[s][r].outputs.design_file,
                                              tcon_file=modelgen_results[s][r].outputs.con_file,
                                              fcon_file=modelgen_results[s][r].outputs.fcon_file,
                                              autocorr_noestimate=True))
    return filmgls_results


def main():
    print('Running ' + sys.argv[1])
    if not os.path.isdir(MEM_DIR):
        os.mkdir(MEM_DIR)
    mem = Memory(base_dir=MEM_DIR)
    layout = BIDSLayout(BIDS_DIR)
    if num_runs > 1:
        func_files = [[layout.get(type='bold', task=task, run=i+1, subject=subj, extensions='nii.gz')[0]
                       for i in range(num_runs)] for subj in SUBJECTS]
    else:
        func_files = [layout.get(type='bold', task=task, subject=subj, extensions='nii.gz') for subj in SUBJECTS]
    events = get_events(func_files)
    confounds = get_confounds(func_files)
    info = get_info(events, confounds)
    specify_model_results = specify_model(layout, func_files, info)
    level1design_results = lv1_design(mem, layout, func_files, specify_model_results)
    modelgen_results = feat_model(mem, level1design_results)
    mask_results = masking(mem, func_files)
    film_gls(mem, mask_results, modelgen_results)


if __name__ == '__main__':
    main()
