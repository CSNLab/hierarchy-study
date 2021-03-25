import seaborn as sns
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42


nav_p_df = pd.read_csv('nav_delta-sim_ttest.csv', index_col=0)
fdr_nav_p = nav_p_df[['delta_sim', 'tstats', 'p_fdr_bh']]
fdr_nav_p.columns = ('nav_dsim', 'nav_tstats', 'nav_p_fdr_bh')

sac_p_df = pd.read_csv('sac_delta-sim_ttest.csv', index_col=0)
fdr_sac_p = sac_p_df[['delta_sim', 'tstats', 'p_fdr_bh']]
fdr_sac_p.columns = ('sac_dsim', 'sac_tstats', 'sac_p_fdr_bh')

df = pd.DataFrame(fdr_nav_p).join(pd.DataFrame(fdr_sac_p), how='outer')
df['order'] = np.abs(df['nav_tstats']) * np.abs(df['sac_tstats'])

# calculate the overlap level
criteria = [1e-5, 0.0001, 0.001, 0.005, 0.01, 0.05]
overlap = np.zeros(len(df))
for row_i, (p, row) in enumerate(df.iterrows()):
	if row['nav_p_fdr_bh'] > criteria[-1] or row['sac_p_fdr_bh'] > criteria[-1]:
		continue
	for i in range(len(criteria)):
		if row['nav_p_fdr_bh'] < criteria[i] and row['sac_p_fdr_bh'] < criteria[i]:
			overlap[row_i] = len(criteria) - i + 1
			break
df['overlap'] = overlap

df = df[(df['overlap'] > 0) | (df['nav_p_fdr_bh'] <= criteria[-2]) | (df['sac_p_fdr_bh'] <= criteria[-2])]

df = df.sort_values(by=['overlap', 'order'], ascending=[False, False])
num_overlap = sum(df['overlap'] > 0)
num_nav_only = sum(df[num_overlap:]['nav_p_fdr_bh'] < 0.05)
df = pd.concat([df[:num_overlap], df[num_overlap:].sort_values('nav_p_fdr_bh')])
df = pd.concat([df[:(num_overlap + num_nav_only)], df[(num_overlap + num_nav_only):].sort_values('sac_p_fdr_bh')])
df.to_csv('sim_heatmap.csv')

for task in ['nav', 'sac', 'x']:
	fig, ax = plt.subplots()
	if task == 'sac' or task == 'nav':
		visual = pd.DataFrame(df[[task + '_p_fdr_bh']])
		colors = np.log(df[task + '_p_fdr_bh'])
		colors = pd.DataFrame([colors]).T
		colors.columns = visual.columns
		ax = sns.heatmap(colors, annot=visual, vmin=-10, vmax=np.log(.1),
						yticklabels=True, linewidths=1,
						cmap='Reds_r' if task == 'nav' else 'Blues_r')
	else:
		visual = pd.DataFrame(df['overlap'])
		ax = sns.heatmap(visual, annot=visual,
						 yticklabels=True, cmap='Purples', linewidths=1)
	plt.savefig('heatmap_' + task + '.pdf')
	plt.show()
