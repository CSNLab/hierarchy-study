
df = read.csv('xtask_delta-sim_all_subj.csv')

library(BayesFactor)
ttestBF(x = df['X1029.ctx.lh.superiorparietal'][,1])
ttestBF(x = df['X2029.ctx.rh.superiorparietal'][,1])

li = c('X2005.ctx.rh.cuneus', 'X1011.ctx.lh.lateraloccipital', 'X2011.ctx.rh.lateraloccipital', 'X1029.ctx.lh.superiorparietal', 'X1021.ctx.lh.pericalcarine', 'X2021.ctx.rh.pericalcarine', 'X1007.ctx.lh.fusiform', 'X2029.ctx.rh.superiorparietal', 'X2008.ctx.rh.inferiorparietal', 'X1008.ctx.lh.inferiorparietal', 'X2025.ctx.rh.precuneus', 'X1013.ctx.lh.lingual', 'X1005.ctx.lh.cuneus', 'X2013.ctx.rh.lingual', 'X2007.ctx.rh.fusiform', 'X1025.ctx.lh.precuneus', 'X1035.ctx.lh.insula', 'X1012.ctx.lh.lateralorbitofrontal', 'X1027.ctx.lh.rostralmiddlefrontal', 'X2030.ctx.rh.superiortemporal', 'X2015.ctx.rh.middletemporal', 'X1009.ctx.lh.inferiortemporal', 'X1010.ctx.lh.isthmuscingulate', 'X2012.ctx.rh.lateralorbitofrontal', 'X1019.ctx.lh.parsorbitalis', 'X1003.ctx.lh.caudalmiddlefrontal', 'X2003.ctx.rh.caudalmiddlefrontal', 'X51.Right.Putamen', 'X1017.ctx.lh.paracentral', 'X50.Right.Caudate', 'X1028.ctx.lh.superiorfrontal', 'X1024.ctx.lh.precentral', 'X1020.ctx.lh.parstriangularis', 'X1018.ctx.lh.parsopercularis', 'X1031.ctx.lh.supramarginal', 'X2016.ctx.rh.parahippocampal', 'X2009.ctx.rh.inferiortemporal')

for (area in li) {
  print(area)
  print(ttestBF(x = df[area][,1]))
}
