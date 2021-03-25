. /u/local/Modules/default/init/modules.sh
module use /u/project/CCN/apps/modulefiles
module load fsl/5.0.10
module load ants/ants-2.3.1

subjectList=($(ls -d ../fmriprep/sub*/ | grep -o sub-...))

workDir="/u/project/cparkins/data/hierarchy/derivatives"
preprocDir="${workDir}/fmriprep"
mniFile="${workDir}/mvpa_volume/mni_icbm152_nlin_asym_09c/2mm_T1.nii.gz"
maskDir="${workDir}/masks/ribbon_masks"


function transform2mni() {
    # transform searchlight file to mni space
    mkdir tempdir
    for sid in "${subjectList[@]}"
    do
        # transfer to mni
        transMatrix="${preprocDir}/${sid:0:7}/anat/${sid:0:7}_T1w_target-MNI152NLin2009cAsym_warp.h5"
        maskFile="${maskDir}/${sid}_ribbon.nii.gz"
        antsApplyTransforms -i $maskFile  \
                            -r $mniFile  \
                            -o tempdir/${sid}_ribbon_mni.nii.gz  \
                            -t $transMatrix
    done
}

transform2mni
fslmerge -t tempdir/all_subj_ribbon_mni.nii.gz `echo $(ls -d tempdir/sub*mni.nii.gz)`
fslmaths tempdir/all_subj_ribbon_mni.nii.gz -Tmax ${maskDir}/all_subj_ribbon_mni_max.nii.gz

# resample
flirt -in ${maskDir}/all_subj_ribbon_mni_max.nii.gz \
          -ref ribbon_masks/all_subj_ribbon_mni_max_rsmp01.nii.gz \
          -applyxfm -usesqform \
          -out tempdir/all_subj_ribbon_mni_max_rsmp.nii.gz
# convert to binary mask
fslmaths tempdir/all_subj_ribbon_mni_max_rsmp.nii.gz -thr 0 -bin ${maskDir}/all_subj_ribbon_mni_max_rsmp0thr.nii.gz
# dilate
fslmaths ${maskDir}/all_subj_ribbon_mni_max_rsmp0thr.nii.gz -kernel sphere 2 -dilM ${maskDir}/all_subj_ribbon_mni_max_rsmp0thr_dil2mm.nii.gz
