import sys
from nilearn.input_data import NiftiMasker
from nilearn.image import concat_imgs, load_img, index_img
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr, pearsonr, zscore
import nibabel as nib
import numpy as np
import pandas as pd
import logging
import copy
import re
import os
from subjects import *
from intask_sim_sl import LABELS_SAC as FMRI_STRUCT


# subjects
subject_list = sys.argv[1:] if len(sys.argv) > 1 else EVERYONE
print(subject_list)

TASK = 'sac'  # nav_bin sac
NUM_RUNS = 6
# directories
TSTATS_DIR = '/u/project/cparkins/data/hierarchy/derivatives/lv1/tstats/'
MASK_DIR = '/u/project/cparkins/data/hierarchy/derivatives/masks/parcel_masks/'
OUTDIR = '/u/project/cparkins/data/hierarchy/derivatives/mvpa_parcel/sim_%s_parcel/' % TASK
# file names (%s will be replace by subject ID)
DATA_FILE = TSTATS_DIR + TASK + '_tstats/%s_' + TASK + '.nii.gz'
ATTR_FILE = TSTATS_DIR + '%s_attr.txt' % TASK
# log names
INFOLOG = '%s_sim_log' % TASK
DATALOG = '%s_sim_data' % TASK


def sim(data, labels, fmri_struct):
    corr = 1 - pdist(data, metric='correlation')
    corr = np.arctanh(corr)  # Fisher's z transformation
    corr = corr[fmri_struct != 0]
    cond = fmri_struct[fmri_struct != 0]
    corr = zscore(corr)
    sim1 = np.mean(corr[cond == 1])
    sim2 = np.mean(corr[cond == 2])
    delta = sim1 - sim2
    return [sim1, sim2, delta]


def xtask_sim_fmri_struct():
    # 1: matching, 2: mismatching
    xtask_vertical = [
        # down, left, right, up (sac)
        [1, 2, 2, 2], # down (nav)
        [2, 2, 2, 1]  # up   (nav)
    ]
    xtask_vertical_t = [*zip(*xtask_vertical)]
    xtask_leftright = [
        [2, 2, 1, 2],
        [2, 1, 2, 2]
    ]
    xtask_leftright_t = [*zip(*xtask_leftright)]
    xtask_rightleft = [
        [2, 1, 2, 2],
        [2, 2, 1, 2]
    ]
    xtask_rightleft_t = [*zip(*xtask_rightleft)]
    # no comparison within a task
    intask_nav = [[0] * 2] * 2
    intask_sac = [[0] * 4] * 4

    def stack(xtask, xtask_t):
        return squareform(np.vstack(
            [np.hstack([intask_nav] * 6 + [xtask] * 2)] * 6 +
            [np.hstack([xtask_t] * 6 + [intask_sac] * 2)] * 2
        ))

    return stack(xtask_vertical, xtask_vertical_t), \
           stack(xtask_leftright, xtask_leftright_t), \
           stack(xtask_rightleft, xtask_rightleft_t)


def main():
    if TASK == 'xtask':
        nav_labels = pd.read_csv(TSTATS_DIR + 'nav_bin_attr.txt', sep=' ', header=None)[0]
        sac_labels = pd.read_csv(TSTATS_DIR + 'sac_attr.txt', sep=' ', header=None)[0]
        labels = pd.concat((nav_labels, sac_labels), ignore_index=True)
    else:
        labels = pd.read_csv(ATTR_FILE, sep=' ', header=None)[0]
    fmri_struct = squareform(FMRI_STRUCT)  # xtask_sim_fmri_struct()
    # info logger
    for logname in (INFOLOG, DATALOG):
        logger = logging.getLogger(logname)
        logger.setLevel(logging.INFO)
        logger.addHandler(logging.FileHandler(OUTDIR + logname + '.log'))

    # run classification
    score_df_list = []
    for subj in subject_list:
        print(subj)
        masks = [mask for mask in os.listdir(MASK_DIR + subj) if mask.endswith('dil3mm.nii.gz')]
        subj_scores_list = []
        # read fmri data
        if TASK == 'xtask':
            nav_data = load_img(TSTATS_DIR + 'nav_bin_tstats/%s_nav_bin.nii.gz' % subj)
            sac_data = load_img(TSTATS_DIR + 'sac_tstats/%s_sac.nii.gz' % subj)
            data = concat_imgs([nav_data, sac_data])
            if subj in TOP_BOTTOM:
                subj_fmri_struct = fmri_struct[0]
            elif subj in LEFT_RIGHT:
                subj_fmri_struct = fmri_struct[1]
            elif subj in RIGHT_LEFT:
                subj_fmri_struct = fmri_struct[2]
        else:
            data = load_img(DATA_FILE % subj)
            subj_fmri_struct = fmri_struct
        for mask in masks:
            mask_name = re.findall(r'roi\d+.*_rsmp', mask)[0][3:-5]
            id_length = len(re.findall(r'^\d+', mask_name)[0])
            if mask_name[id_length] != '-':
                mask_name = mask_name[:id_length] + '-' + mask_name[id_length:]
            print(mask_name)
            try:
                # mask
                masker = NiftiMasker(mask_img=MASK_DIR + subj + '/' + mask)
                masked_data = masker.fit_transform(data)
                # calculation
                roi_score = sim(masked_data, labels, subj_fmri_struct)
                logging.getLogger(DATALOG).info(','.join([subj, mask_name, ','.join(map(str, roi_score))]))
                # result
                scores = roi_score
                for i, score in enumerate(scores):
                    if len(subj_scores_list) <= i:
                        subj_scores_list.append({})
                    subj_scores_list[i][mask_name] = score
            except ValueError as e:
                msg = 'ValueError: ' + mask + ' - ' + str(e)
                print(msg)
                logging.getLogger(INFOLOG).warning(msg)
                for i in range(len(subj_scores_list)):
                    subj_scores_list[i][mask_name] = 'nan'
        for i, subj_scores in enumerate(subj_scores_list):
            if len(score_df_list) <= i:
                score_df_list.append([])
            score_df_list[i].append(pd.DataFrame(subj_scores, index=[0]))

    # output all subjects' scores to csv
    for score_df, param_name in zip(score_df_list, ['sim1', 'sim2', 'delta-sim']):
        combined_df = pd.concat(score_df)
        combined_df.index = subject_list
        combined_df.to_csv(OUTDIR + '%s_%s_all_subj.csv' % (TASK, param_name))


if __name__ == '__main__':
    main()
