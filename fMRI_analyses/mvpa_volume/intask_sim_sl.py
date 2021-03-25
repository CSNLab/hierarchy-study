import sys
if sys.version_info.major == 2:
    from mvpa2.suite import Dataset, Measure, SampleAttributes, fmri_dataset, remove_invariant_features, sphere_searchlight, map2nifti
    from mvpa2.measures.rsa import PDistTargetSimilarity
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr
import numpy as np

try:
    from xtask_sim_sl import CustomDist
    from subjects import *
except ImportError:
    pass

TSTATS_DIR = '/u/project/cparkins/data/hierarchy/derivatives/lv1/tstats/'
MASK_DIR = '/u/project/cparkins/data/hierarchy/derivatives/masks/ribbon_masks/'
TSTATS_NAME = 'nav_bin'
OUTDIR = '/u/project/cparkins/data/hierarchy/derivatives/mvpa_volume/navigation_rsa_sl/native_sim_dil3mm0thr_3vox/'
OUTFILE = '%s_nav_%dvox_sim.nii.gz'
# TSTATS_NAME = 'sac'
# OUTDIR = '/u/project/cparkins/data/hierarchy/derivatives/mvpa_volume/saccades_rsa_sl/native_sim_dil3mm0thr/'
# OUTFILE = '%s_sac_%dvox_sim.nii.gz'

SEARCHLIGHT_RADIUS = 4

LABELS_SAC = [  # for saccades
    # down7, left7, right7, up7, down8, left8, right8, up8
    [0, 0, 0, 0, 1, 2, 2, 2],  # down7
    [0, 0, 0, 0, 2, 1, 2, 2],  # left7
    [0, 0, 0, 0, 2, 2, 1, 2],  # right7
    [0, 0, 0, 0, 2, 2, 2, 1],  # up7
    [1, 2, 2, 2, 0, 0, 0, 0],  # down8
    [2, 1, 2, 2, 0, 0, 0, 0],  # left8
    [2, 2, 1, 2, 0, 0, 0, 0],  # right8
    [2, 2, 2, 1, 0, 0, 0, 0]]  # up8

LABELS_NAV = [  # for social navigation
    # d1, u1, d2, u2, d3, u3, d4, u4, d5, u5, d6, u6
    [0, 0, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2],  # down1
    [0, 0, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1],  # up1
    [1, 2, 0, 0, 1, 2, 1, 2, 1, 2, 1, 2],  # down2
    [2, 1, 0, 0, 2, 1, 2, 1, 2, 1, 2, 1],  # up2
    [1, 2, 1, 2, 0, 0, 1, 2, 1, 2, 1, 2],  # down3
    [2, 1, 2, 1, 0, 0, 2, 1, 2, 1, 2, 1],  # up3
    [1, 2, 1, 2, 1, 2, 0, 0, 1, 2, 1, 2],  # down4
    [2, 1, 2, 1, 2, 1, 0, 0, 2, 1, 2, 1],  # up4
    [1, 2, 1, 2, 1, 2, 1, 2, 0, 0, 1, 2],  # down5
    [2, 1, 2, 1, 2, 1, 2, 1, 0, 0, 2, 1],  # up5
    [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 0, 0],  # down6
    [2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 0, 0]]  # up6

LABELS_DIST = [  # for step sizes in social navigation
        # d2, d3, d4, u2, u3, u4
        [0, 1, 2, 0, 1, 2],  # d2
        [1, 0, 1, 1, 0, 1],  # d3
        [2, 1, 0, 2, 1, 0],  # d4
        [0, 1, 2, 0, 1, 2],  # u2
        [1, 0, 1, 1, 0, 1],  # u3
        [2, 1, 0, 2, 1, 0]]  # u4


def main():
    subject_list = sys.argv[1:] if len(sys.argv) > 1 else EVERYONE
    print(subject_list)

    attr = SampleAttributes(TSTATS_DIR + TSTATS_NAME + '_attr.txt')

    for subj in subject_list:
        tstats_file = TSTATS_DIR + TSTATS_NAME + '_tstats/%s_%s.nii.gz' % (subj, TSTATS_NAME)
        dataset = fmri_dataset(samples=tstats_file,
                               mask=MASK_DIR + '%s_ribbon_rsmp0_dil3mm.nii.gz' % subj)
        dataset.sa['chunks'] = attr.chunks
        dataset.sa['targets'] = attr.targets
        dataset = remove_invariant_features(dataset)

        similarity = CustomDist(squareform(LABELS_NAV))
        searchlight = sphere_searchlight(similarity, SEARCHLIGHT_RADIUS)
        searchlight_map = searchlight(dataset)

        # save files
        nifti = map2nifti(data=searchlight_map, dataset=dataset)
        nifti.to_filename(OUTDIR + OUTFILE % (subj, SEARCHLIGHT_RADIUS))


if __name__ == '__main__':

    class DistDist(Measure):
        is_trained = True  # Indicate that this measure is always trained

        def __init__(self, labels, **kwargs):
            super(DistDist, self).__init__(**kwargs)
            self.labels = labels

        def _call(self, ds):
            data_dsm = pdist(ds.samples, metric='correlation')  # 'euclidean'
            corr = spearmanr(data_dsm, self.labels, axis=None).correlation
            return Dataset([corr])

    main()
