require("ggplot2")
require("Rmisc")
require("ggsignif")

y_sig_pos = 0.55
y_lim = c(-.58, 0.62)

vjust = -.3
annot = "NS"
file_pre = "xtask_"

# read in data
sim1_df = read.csv(file=paste(file_pre, "sim1_all_subj.csv", sep=""),
                 head=TRUE, sep=",")
sim2_df = read.csv(file=paste(file_pre, "sim2_all_subj.csv", sep=""),
                 head=TRUE, sep=",")
len = length(sim1_df$X1029.ctx.lh.superiorparietal)
left = data.frame(subj=sim1_df$X, hemisphere=rep("Left SPL", len), direction=rep("Matching", len), sim=sim1_df$X1029.ctx.lh.superiorparietal)
left = rbind(left, data.frame(subj=sim2_df$X, hemisphere=rep("Left SPL", len), direction=rep("Mismatching", len), sim=sim2_df$X1029.ctx.lh.superiorparietal))
right = data.frame(subj=sim1_df$X, hemisphere=rep("Right SPL", len), direction=rep("Matching", len), sim=sim1_df$X2029.ctx.rh.superiorparietal)
right = rbind(right, data.frame(subj=sim2_df$X, hemisphere=rep("Right SPL", len), direction=rep("Mismatching", len), sim=sim2_df$X2029.ctx.rh.superiorparietal))
both = rbind(left, right)

# SE
left.stat = summarySEwithin(left, measurevar="sim", withinvars="direction", idvar="subj")
right.stat = summarySEwithin(right, measurevar="sim", withinvars="direction", idvar="subj")
left.stat$hemisphere = rep("Left SPL", length(left.stat$N))
right.stat$hemisphere = rep("Right SPL", length(right.stat$N))
summary = rbind(left.stat, right.stat)

# t tests
left.t = t.test(left$sim ~ left$direction, paired=TRUE, alternative="greater", conf.level=0.95)
right.t = t.test(right$sim ~ right$direction, paired=TRUE, alternative="greater", conf.level=0.95)
deltaR_df = data.frame(subj=both[both$direction == 'Matching',]$subj,
                       hemisphere=both[both$direction == 'Matching',]$hemisphere,
                       deltaR=both[both$direction == 'Matching',]$sim - both[both$direction == 'Mismatching',]$sim)
deltaR.t = t.test(deltaR_df$deltaR ~ deltaR_df$hemisphere, paired=TRUE, conf.level=0.95)
hemi_df = aggregate(both$sim, by=list(both$subj, both$hemisphere), mean)
colnames(hemi_df) = c('subj', 'hemisphere', "r")
hemi.t = t.test(hemi_df$sim ~ hemi_df$hemisphere, paired=TRUE, conf.level=0.95)

# plot
ggplot(summary, aes(x=direction, y=r, fill=direction)) +
  facet_grid(cols = vars(hemisphere))+
  geom_bar(position=position_dodge(.7), colour=NA, stat="identity", width=.7) +
  geom_signif(y_position=y_sig_pos, xmin=1.2, xmax=1.8,
              annotation=annot,
              tip_length=0, textsize=6, size=0.6, vjust=vjust) +
  geom_errorbar(position=position_dodge(.7), width=.12, size=.5, aes(ymin=r-ci, ymax=r+ci)) +
  ylab("Pattern Similarity (Normalized)") +
  coord_cartesian(ylim=y_lim) +
  scale_fill_manual(values=c("#21A247", "#A3CF62")) +
  scale_y_continuous(breaks=seq(-1, 1.4, by=.2), minor_breaks = seq(-1, 1.4, by=.05)) +
  theme_gray() +
  theme(legend.position="none",
        text=element_text(size=20),
        axis.text.x=element_text(size=14),
        axis.title.x=element_blank())+
  geom_point(data = both, position=position_dodge(.7), aes(x = direction, y = r, color=direction),
             alpha = 0.3) +
  scale_color_manual(values=c("#177533", "#87b04c"))+
  geom_line(data = both, aes(y=r, x=direction, group=subj), color="black", alpha=.15, size=0.2)

