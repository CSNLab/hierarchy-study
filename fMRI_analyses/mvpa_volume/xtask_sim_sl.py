from mvpa2.suite import SampleAttributes, Measure, Dataset, fmri_dataset, remove_invariant_features, sphere_searchlight, map2nifti
from mvpa2.measures.rsa import PDistTargetSimilarity
from scipy.spatial.distance import pdist, squareform
from scipy.stats import zscore
import numpy as np
import sys
from itertools import product
from subjects import *

TSTATS_DIR = '/u/project/cparkins/data/hierarchy/derivatives/lv1/tstats/'
MASK_DIR = '/u/project/cparkins/data/hierarchy/derivatives/masks/ribbon_masks/'
OUTDIR = '/u/project/cparkins/data/hierarchy/derivatives/mvpa_volume/xtask_sim_sl/native_sim_dil3mm0thr/'

SEARCHLIGHT_RADIUS = 4

subject_list = sys.argv[1:] if len(sys.argv) > 1 else EVERYONE
print(subject_list)

# eye movement directions that correspond to hierachy directions
POWERFUL_DIRCT = 'eye_up'  # 'eye_left'  #
POWERLESS_DIRCT = 'eye_down'  # 'eye_right'  #
DIRCT = 'v'  # '>'


class CustomDist(Measure):
    is_trained = True  # Indicate that this measure is always trained
    
    def __init__(self, labels, **kwargs):
        super(CustomDist, self).__init__(**kwargs)
        self.labels = labels

    def _call(self, ds):
        data_dsm = 1 - pdist(ds.samples, metric='correlation')
        data_dsm = np.arctanh(data_dsm)  # Fisher z transformation
        data_dsm = data_dsm[self.labels != 0]
        labels = self.labels[self.labels != 0]
        data_dsm = zscore(data_dsm)
        # difference between distances of same types of trials across run (labeled 1)
        # and different types of trals across run (labeled 2)
        sim = np.mean(data_dsm[labels == 1]) - np.mean(data_dsm[labels == 2])
        return Dataset([sim])


def get_nav_sac_data(nav_attr, sac_attr, subj, subj_mask):
    # nav data
    nav_ds = fmri_dataset(samples=TSTATS_DIR + 'nav_bin_tstats/%s_nav_bin.nii.gz' % subj,
                          mask=subj_mask)
    nav_ds.sa['chunks'] = nav_attr.chunks    # chunks: run #s
    nav_ds.sa['targets'] = nav_attr.targets  # targets: run types (up/down)
    # saccades data
    sac_ds = fmri_dataset(samples=TSTATS_DIR + 'sac_tstats/%s_sac.nii.gz' % subj,
                          mask=subj_mask)
    sac_ds.sa['chunks'] = sac_attr.chunks
    sac_ds.sa['targets'] = sac_attr.targets
    sac_ds = sac_ds[np.isin(sac_ds.sa.targets, [POWERFUL_DIRCT, POWERLESS_DIRCT])]
    # combine datasets
    dataset = nav_ds
    dataset.append(sac_ds)
    return dataset


def main():
    sac_attr = SampleAttributes(TSTATS_DIR + 'sac_attr.txt')
    nav_attr = SampleAttributes(TSTATS_DIR + 'nav_bin_attr.txt')

    # labels
    xtask_run = [
        # down/powerless, up/powerful
        [1, 2],  # down/powerless
        [2, 1],  # up/powerful
    ]
    intask_run = [  # no comparison within a task
        [0, 0],
        [0, 0]
    ]
    labels = squareform(np.vstack(
        [np.hstack([intask_run] * 6 + [xtask_run] * 2)] * 6 +
        [np.hstack([xtask_run] * 6 + [intask_run] * 2)] * 2
    ))

    for subj in subject_list:
        subj_mask = MASK_DIR + '%s_ribbon_rsmp0_dil3mm.nii.gz' % subj
        dataset = get_nav_sac_data(nav_attr, sac_attr, subj, subj_mask)
        dataset = remove_invariant_features(dataset)
        print(dataset.targets, dataset.chunks)

        # searchlight
        similarity = CustomDist(labels)
        searchlight = sphere_searchlight(similarity, SEARCHLIGHT_RADIUS)
        searchlight_map = searchlight(dataset)

        # save files
        nifti = map2nifti(data=searchlight_map, dataset=dataset)
        nifti.to_filename(OUTDIR + '%s_%s_%dvox_sim.nii.gz' % (subj, DIRCT, SEARCHLIGHT_RADIUS))


if __name__ == '__main__':
    main()
