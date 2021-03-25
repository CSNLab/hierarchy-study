"""
Detect the initial unsteady volumns in confounds.tsv, and
remove those initial volumns from preproc files.
Also check for big movements and print the info.

The original preproc file will be renamed as "unsteady_" +
original name, and the processed file will be named same as
the original preproc file name.
If no unsteady state is present in confounds.tsv, the file
remains unchanged.

Load fsl/5.0.10 before running this.
"""

import os
import pandas as pd
import subprocess
import re

PATH = '../fmriprep/'
PREPROC_POSTFIX = 'space-T1w_preproc.nii.gz'  # things after "bold_"
XYZ_MOVEMENT_CRITERION = 2.5  # if larger than this, will just print the info and nothing else

all_rows = set()
unsteady_df = {}
subjects = [f[:7] for f in os.listdir(PATH) if f.endswith('.html') and f.startswith('sub')]
for subj in subjects:
    unsteady_df[subj] = {}
    filepath = PATH + subj + '/func/'
    filenames = [f for f in os.listdir(filepath)
                 if f.startswith('sub') and f.endswith('confounds.tsv')]
    for fname in sorted(filenames):
        df = pd.read_csv(filepath + fname, sep='\t')
        # look at XYZ axis movement
        for axis in ('X', 'Y', 'Z'):
            big_move = list(df[axis][df[axis] > XYZ_MOVEMENT_CRITERION])
            if len(big_move) > 0:
                print('Big movements in %s, %s axis:' % (fname, axis), big_move)
        # find unsteady rows
        cols = [c for c in df.columns if c.startswith('NonSteadyStateOutlier')]
        unsteady = df[cols].sum(axis=1)
        unsteady_rows = list(unsteady[unsteady == 1].index)
        num_unsteady = len(unsteady_rows)
        all_rows.update(unsteady_rows)
        print(fname + '\trows=' + str(unsteady_rows))
        # update df
        task = re.findall(r'_task-[^_]+_', fname)[0][6:-1]
        run = re.findall(r'_run-\d+_', fname)
        col_name = task + run[0][5:-1] if len(run) > 0 else task
        unsteady_content = num_unsteady if unsteady_rows == list(range(num_unsteady)) else str(unsteady_rows)
        unsteady_df[subj][col_name] = unsteady_content
        if num_unsteady == 0:
            continue

        # remove first columns from preproc file
        preproc_name = fname[:fname.index('confounds.tsv')] + PREPROC_POSTFIX
        unsteady_name = 'unsteady_' + preproc_name
        print('Removing first %d volumns from ' % num_unsteady + preproc_name)
        os.rename(filepath + preproc_name, filepath + unsteady_name)
        subprocess.call('cd %s; fslroi %s %s %d -1' % (filepath, unsteady_name, preproc_name, num_unsteady), shell=True)

print('all unsteady rows:', all_rows)
# df output
unsteady_df = pd.DataFrame.from_dict(unsteady_df, orient='index')
unsteady_df.to_csv('unsteady_vols.csv')
