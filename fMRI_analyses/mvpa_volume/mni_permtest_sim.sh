#!/bin/bash
. /u/local/Modules/default/init/modules.sh
module use /u/project/CCN/apps/modulefiles
module load fsl/5.0.10
module load ants

subjectList=($(ls -d ../fmriprep/sub*/ | grep -o sub-...))

# paths and files
workDir="/u/project/cparkins/data/hierarchy/derivatives"
preprocDir="${workDir}/fmriprep"
maskFile="${workDir}/masks/ribbon_masks/all_subj_ribbon_mni_max_rsmp0thr_dil3mm.nii.gz"
mniFile="${workDir}/mvpa_volume/mni_icbm152_nlin_asym_09c/2mm_T1.nii.gz"
searchlightDir="${workDir}/mvpa_volume/nav_move_classification_sl/native_r_diff_dil3thr0"
searchlightName="4vox_nav_svm_sl"
transformOutpath="${workDir}/mvpa_volume/nav_move_classification_sl/mni_test_r_diff_dil3thr0_dil3thr0perm"
# searchlightDir="${workDir}/mvpa_volume/sac_classification_sl/native_r_diff_dil3mm0thr"
# searchlightName="4vox_sac_svm_sl"
# transformOutpath="${workDir}/mvpa_volume/sac_classification_sl/mni_test_r_diff_dil3thr0_dil3thr0perm"

# inferred names
mniVoxSize=`echo $mniFile | grep -oP "\dmm"`
accMapName="all_subj_${searchlightName}_mni-${mniVoxSize}"


function transform2mni() {
    # transform searchlight file to mni space
    mkdir $transformOutpath
    for sid in "${subjectList[@]}"
    do
        transMatrix="${preprocDir}/${sid:0:7}/anat/${sid:0:7}_T1w_target-MNI152NLin2009cAsym_warp.h5"
        searchlightFile="${searchlightDir}/${sid}_${searchlightName}.nii.gz"
        antsApplyTransforms -i $searchlightFile  \
                            -r $mniFile  \
                            -o ${transformOutpath}/${sid}_${searchlightName}_mni-${mniVoxSize}.nii.gz  \
                            -t $transMatrix
    done
}

function merge() {
    # merge MNI-space accuracy maps
    searchlightMniFiles=`ls ${transformOutpath}/*_${searchlightName}_mni-${mniVoxSize}.nii.gz`
    fslmerge -t $transformOutpath/$accMapName.nii.gz $searchlightMniFiles
    echo $searchlightMniFiles
}

function smooth_permtest() {
    # 0 parameters
    kernel=3 # smoothing kernel for accuracy maps (same as searchlight radius)
    numPermutations=10000
    clusterThreshold=2.326 # for cluster mass thresholding in randomise, z=2.326 corresponds to p-value of .01
    chanceAcc=0.5

    # 1 smoothing
    #   divide FWHM (in mm) by 2.3548 to get sigma
    sigma=`echo "scale=5; $kernel/2.35482" | bc`
    #   smoothing
    smoothedFile=${accMapName}_smoothed_${kernel}mm
    fslmaths $transformOutpath/$accMapName.nii.gz -s $sigma $transformOutpath/$smoothedFile.nii.gz
    #   average smoothed accuracy maps for visualization
    smoothedFile=${accMapName}
    fslmaths $transformOutpath/$smoothedFile.nii.gz  \
             -Tmean ${transformOutpath}/avg_subj_${searchlightName}_smoothed_${kernel}mm.nii.gz
    # subtract chance accuracy value from each voxel before analysis (since permutation test is against 0)
    fslmaths $transformOutpath/${smoothedFile}.nii.gz -sub $chanceAcc ${transformOutpath}/${smoothedFile}_sub${chanceAcc}.nii.gz

    # 2 permutation test
    randomise -i ${transformOutpath}/${smoothedFile}_sub${chanceAcc}.nii.gz.nii.gz \
              -o ${transformOutpath}/oneSampT_${mniVoxSize}MNI_${kernel}mm-sm_${numPermutations}perm_${clusterThreshold}thr \
              -n $numPermutations  \
              -C $clusterThreshold \
              -m $maskFile \
              -x -1 -T --uncorrp

    fdr -i ${transformOutpath}/oneSampT_${mniVoxSize}MNI_${kernel}mm-sm_${numPermutations}perm_${clusterThreshold}thr_vox_p_tstat1.nii.gz \
    --oneminusp -m $maskFile -q 0.05 \
    --othresh=${transformOutpath}/oneSampT_${mniVoxSize}MNI_${kernel}mm-sm_${numPermutations}perm_vox_p_tstat1_0.05fdr.nii.gz
}

transform2mni
merge
smooth_permtest
