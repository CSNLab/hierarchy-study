from mvpa2.suite import *
from subjects import *
import numpy as np
import random
import sys
import pickle as pkl
from xtask_move_classification_sl import mark_bad_trials

subject_list = sys.argv[1:] if len(sys.argv) > 1 else EVERYONE
print(subject_list)


TASK = 'nav_trialwise'  # 'sac_trialwise'
DATA_DIR = '/u/project/cparkins/data/hierarchy/derivatives/lv1/tstats/'
MASK_DIR = '/u/project/cparkins/data/hierarchy/derivatives/masks/ribbon_masks/'
OUTDIR = '/u/project/cparkins/data/hierarchy/derivatives/mvpa_volume/nav_classification_sl/native_trialwise_dil3thr0/'
N_PROC = 6

RADIUS = 4


def main(subj, info):
    # read in mask file
    subj_mask = MASK_DIR + '%s_ribbon_rsmp0_dil3mm.nii.gz' % subj
    # read in fmri runs and assign sample attributes
    subj_data = DATA_DIR + '%s_tstats/%s_%s.nii.gz' % (TASK, subj, TASK[:3]) #[:3]
    raw_ds = fmri_dataset(samples=subj_data, mask=subj_mask)
    if TASK[:3] == 'nav' and subj == 'sub-156':
        attr = SampleAttributes(DATA_DIR + 'nav_trialwise_attr_bin_156.txt')
    else:
        attr = SampleAttributes(DATA_DIR + '%s_attr_bin.txt' % TASK)
    mark_bad_trials(subj, 'nav', 4, attr, info)
    raw_ds.sa['targets'] = attr.targets  # targets: run types (up/down)
    raw_ds.sa['chunks'] = attr.chunks    # chunks: run #s

    # nav
    dataset = raw_ds[raw_ds.sa.targets == 'up']
    dataset.append(raw_ds[raw_ds.sa.targets == 'down'])

    # # sac
    # dataset = raw_ds[raw_ds.sa.targets == 'eye_up']
    # dataset.append(raw_ds[raw_ds.sa.targets == 'eye_down'])
    # dataset.append(raw_ds[raw_ds.sa.targets == 'eye_left'])
    # dataset.append(raw_ds[raw_ds.sa.targets == 'eye_right'])

    dataset = remove_invariant_features(dataset)
    zscore(dataset)

    # run
    cv = CrossValidation(LinearCSVMC(), NFoldPartitioner(), errorfx=lambda p, t: np.mean(p == t))
    sl = sphere_searchlight(cv, radius=RADIUS, postproc=mean_sample(), nproc=N_PROC)
    result = sl(dataset)

    rfilename = OUTDIR + "{}_{}vox_{}_svm_sl.nii.gz".format(subj, RADIUS, TASK[:3])
    map2nifti(dataset, result.samples.reshape((-1, dataset.nfeatures))).to_filename(rfilename)


if __name__ == '__main__':
    with open('../lv1/good_trials.pkl', 'rb') as infile:
        info = pkl.load(infile)
    for subj in subject_list:
        main(subj, info)
