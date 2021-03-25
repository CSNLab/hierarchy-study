import numpy as np
import pandas as pd
import csv
from scipy.stats import ttest_1samp
from statsmodels.stats.multitest import multipletests
import statsmodels.stats.api as sms
import statistics
import nibabel as nib
import copy
import re

OUTDIR = 'sim_sac_parcel/'  #  'sim_nav_parcel/'
FILE = OUTDIR + 'sac_delta-sim_all_subj.csv'
OUTNIFTI = OUTDIR + 'sac_sim_ttest_%s.nii.gz'
OUTCSV = OUTDIR + 'sac_delta-sim_ttest.csv'
ALPHA = 0.05


EXCLUDE = ['White', 'CSF', 'CC_', 'Ventricle', 'VentralDC', 'Brain-Stem', 'Cerebellum', 'Thalamus']


def main():
    df = pd.read_csv(FILE, index_col=0)

    # SD, CI, effect size
    desc = sms.DescrStatsW(df)
    dsim_values = desc.mean
    sd = desc.std_ddof(1)
    lower_ci, _ = desc.tconfint_mean(alternative='larger')
    cohens_d = dsim_values / sd

    # t test
    raw_tstats = ttest_1samp(df, popmean=0, axis=0)
    column_bools = ~np.isnan(raw_tstats.pvalue) & \
                   list(map(lambda c: not any(ex in c for ex in EXCLUDE), df.columns))
    all_tstats = [np.array(dsim_values[column_bools]),
                  sd[column_bools],
                  lower_ci[column_bools],
                  cohens_d[column_bools],
                  raw_tstats.statistic[column_bools],
                  raw_tstats.pvalue[column_bools],
                  raw_tstats.pvalue[column_bools] / 2]  # one tailed p

    # multiple comparison correction
    multi_corrections = ['fdr_bh']
    for method in multi_corrections:
        corrected = multipletests(all_tstats[-1], alpha=ALPHA, method=method)
        all_tstats.append(corrected[1])

    p_df = pd.DataFrame(all_tstats,
                        columns=df.columns[column_bools],
                        index=['delta_sim', 'sd', 'lower_ci', 'cohens_d', 'tstats', 'raw_p_2tailed', 'raw_p_1tailed'] +
                              ['p_' + m for m in multi_corrections])
    p_df = p_df.T.sort_values('raw_p_1tailed')
    p_df.to_csv(OUTCSV)
    print('Output to: ' + OUTCSV)


if __name__ == '__main__':
    main()
