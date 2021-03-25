from mvpa2.suite import *
import numpy as np
from subjects import *
import sys
import pickle as pkl

# subjects
subject_list = sys.argv[1:] if len(sys.argv) > 1 else EVERYONE
print(subject_list)

# eye movement directions that correspond to hierachy directions
POWERFUL_DIRCT = 'eye_up'  # 'eye_right'  #
POWERLESS_DIRCT = 'eye_down'  # 'eye_left'  #
DIRCT = 'v'

# specify searchlight sphere radius (in voxels)
RADIUS = 4

# specify directories containing t-stats and grey matter masks
DATA_DIR = '/u/project/cparkins/data/hierarchy/derivatives/lv1/tstats/'
MASK_DIR = '/u/project/cparkins/data/hierarchy/derivatives/masks/ribbon_masks/'
OUTDIR = '/u/project/cparkins/data/hierarchy/derivatives/mvpa_volume/xtask_classification_sl/native_trialwise_dil3mm0thr/'

# num processors
N_PROC = 6

# attributes files
nav_attr = SampleAttributes(DATA_DIR + 'nav_trialwise_attr_bin.txt')
sac_attr = SampleAttributes(DATA_DIR + 'sac_trialwise_attr_bin.txt')


def mark_bad_trials(subj, task, max_nonsteady, attr, info):
    subj_task_info = info[task][subj]
    # check if numbers match
    n_trials = sum(map(len, subj_task_info.values()))
    assert n_trials == len(attr.chunks)
    assert n_trials == len(attr.targets)
    n_run = len(subj_task_info)
    flat_info = [item for run in range(1, n_run + 1) for item in subj_task_info[run]]
    # replace
    for i, val in enumerate(flat_info):
        if (np.issubdtype(type(val), np.integer) and val > max_nonsteady) or not val:
            attr.chunks[i] = -1
            attr.targets[i] = -1


def main(subj, info):
    print('Running ' + subj)
    if subj == 'sub-156':
        global nav_attr
        nav_attr = SampleAttributes(DATA_DIR + 'nav_trialwise_attr_bin_156.txt')
    # read in mask file
    subj_mask = MASK_DIR + '%s_ribbon_rsmp0_dil3mm.nii.gz' % subj
    # read in navigation runs and assign sample attributes
    subj_nav_data = DATA_DIR + 'nav_trialwise_tstats/%s_nav.nii.gz' % subj
    nav_ds = fmri_dataset(samples=subj_nav_data, mask=subj_mask)
    mark_bad_trials(subj, 'nav', 2, nav_attr, info)
    nav_ds.sa['chunks'] = nav_attr.chunks    # chunks: run #s
    nav_ds.sa['targets'] = nav_attr.targets  # targets: run types (up/down)
    # read in saccades runs and assign sample attributes
    subj_sac_data = DATA_DIR + 'sac_trialwise_tstats/%s_sac_trialwise.nii.gz' % subj
    sac_ds = fmri_dataset(samples=subj_sac_data, mask=subj_mask)
    mark_bad_trials(subj, 'sacc', 4, sac_attr, info)
    sac_ds.sa['chunks'] = sac_attr.chunks
    sac_ds.sa['targets'] = sac_attr.targets

    # get data for 'up' and 'down' trials from the 6 nav runs
    # and 'up' and 'down' eye movements from the 2 saccades runs
    dataset = nav_ds[nav_ds.sa.targets == 'up']
    dataset.append(nav_ds[nav_ds.sa.targets == 'down'])
    dataset.append(sac_ds[sac_ds.sa.targets == POWERFUL_DIRCT])
    dataset.append(sac_ds[sac_ds.sa.targets == POWERLESS_DIRCT])
    print('length', len(dataset.samples))

    # remove invariant features (e.g., 0s outside brain)
    dataset = remove_invariant_features(dataset)

    # create 2 different mappings to group patterns by direction category (up vs. down)
    # or by modality (nav or sac)
    dataset.sa['category'] = AttributeMap({POWERFUL_DIRCT:1, POWERLESS_DIRCT:2, 'up':1, 'down':2}).to_numeric(dataset.targets)
    dataset.sa['modality'] = AttributeMap({POWERFUL_DIRCT:2, POWERLESS_DIRCT:2, 'up':1, 'down':1}).to_numeric(dataset.targets)

    # replace targets with 'category' label that's the same for nav and sacc runs
    dataset.sa.targets = dataset.sa.category

    # zscore voxel values across examples within each task (so separate for training and testing data)
    zscore(dataset, chunks_attr='modality')

    # create partitions for training and testing
    partitioner = HalfPartitioner(attr='modality')
    # cross-validation
    clf = LinearCSVMC()  # get_feature_selection_clf()  #
    cv = CrossValidation(clf, partitioner, errorfx=lambda p, t: np.mean(p == t))
    # initialize searchlight
    # collapse and average accuracies across all folds as specified in posproc=mean_sample()
    sl = sphere_searchlight(cv, radius=RADIUS, nproc=N_PROC)  #, postproc=mean_sample())

    # run searchlight
    result = sl(dataset)

    # write the searchlight map into the original space using the original header from dataset
    for i in range(2):
        # 0: eye predicts nav, 1: nav predicts eye
        outfilename = OUTDIR + '%s_%s_xtask-move_twise_%svox_z_svm_%s.nii.gz' % (subj, DIRCT, RADIUS, i)
        map2nifti(dataset, result.samples[i]).to_filename(outfilename)


if __name__ == '__main__':
    with open('../lv1/good_trials.pkl', 'rb') as infile:
        info = pkl.load(infile)
    for subj in subject_list:
        main(subj, info)
