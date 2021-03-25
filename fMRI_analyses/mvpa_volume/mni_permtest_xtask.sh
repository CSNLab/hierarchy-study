#!/bin/bash
. /u/local/Modules/default/init/modules.sh
module use /u/project/CCN/apps/modulefiles
module load fsl/5.0.10
module load ants

# everyfile=(sub-132_v sub-133_v sub-134_\< sub-134_v sub-136_\> sub-136_v sub-137_\> sub-137_v sub-138_v sub-139_v sub-142_\> sub-142_v sub-143_v sub-144_v sub-145_\< sub-145_v sub-146_\> sub-146_v sub-148_\> sub-148_v sub-149_\< sub-149_v sub-154_\> sub-154_v sub-155_\> sub-155_v sub-156_v sub-157_v sub-159_v sub-160_\> sub-160_v sub-161_v sub-163_\< sub-163_v sub-166_v sub-167_\< sub-167_v sub-169_\< sub-169_v sub-170_v sub-171_\> sub-171_v sub-172_\> sub-172_v sub-174_v sub-175_v)

# drag & drop
subjectList=(sub-132_v sub-133_v sub-134_v sub-136_\> sub-137_v sub-138_v sub-139_v sub-142_v sub-143_v sub-144_v sub-145_v sub-146_v sub-148_\> sub-149_v sub-154_\> sub-155_\> sub-156_v sub-157_v sub-159_v sub-160_v sub-161_v sub-163_v sub-166_v sub-167_\< sub-169_v sub-170_v sub-171_\> sub-172_v sub-174_v sub-175_v)

# paths and files
workDir="/u/project/cparkins/data/hierarchy/derivatives"
preprocDir="${workDir}/fmriprep"
maskFile="${workDir}/masks/ribbon_masks/all_subj_ribbon_mni_max_rsmp0thr_dil3mm.nii.gz"
mniFile="${workDir}/mvpa_volume/mni_icbm152_nlin_asym_09c/2mm_T1.nii.gz"
# searchlightDir="${workDir}/mvpa_volume/xtask_move_classification_sl/native_r_diff_dil3mm0thr"
# searchlightName="xtask-move_twise_4vox_z_svm_1"
# transformOutpath="${workDir}/mvpa_volume/xtask_move_classification_sl/mni_test_twise_good_dil3mm0thr_dil3perm_1"
searchlightDir="${workDir}/mvpa_volume/xtask_rdiff_sl/native_move_dil3mm0thr"
searchlightName="4vox_rdiff"
transformOutpath="${workDir}/mvpa_volume/xtask_rdiff_sl/mni_test_move_dil3mm0thr_dil3perm"


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
    # chanceAcc=0.5 # chance accuracy (0.25 for within-task saccades classification; 0.5 for other classifications)

    # 1 smoothing
    #   divide FWHM (in mm) by 2.3548 to get sigma
    sigma=`echo "scale=5; $kernel/2.35482" | bc`
    #   smoothing
    smoothedFile=${accMapName}_smoothed_${kernel}mm
    fslmaths $transformOutpath/$accMapName.nii.gz -s $sigma $transformOutpath/$smoothedFile.nii.gz
    #   average smoothed accuracy maps for visualization
    fslmaths $transformOutpath/$smoothedFile.nii.gz  \
             -Tmean ${transformOutpath}/avg_subj_${searchlightName}_smoothed_${kernel}mm.nii.gz
    #   subtract chance accuracy value from each voxel before analysis (since permutation test is against 0)
    # fslmaths $transformOutpath/$smoothedFile.nii.gz -sub $chanceAcc ${transformOutpath}/${smoothedFile}_sub${chanceAcc}.nii.gz

    # 2 permutation test _sub${chanceAcc}
    randomise -i ${transformOutpath}/${smoothedFile}.nii.gz \
              -o ${transformOutpath}/oneSampT_${mniVoxSize}MNI_${kernel}mm-sm_${varSmoothKernal}mm-var-sm_${numPermutations}perm_${clusterThreshold}thr \
              -n $numPermutations  \
              -C $clusterThreshold \
              -m $maskFile \
              -x -1 -T --uncorrp
    fdr -i ${transformOutpath}/oneSampT_${mniVoxSize}MNI_${kernel}mm-sm_${varSmoothKernal}mm-var-sm_${numPermutations}perm_${clusterThreshold}thr_vox_p_tstat1.nii.gz \
        --oneminusp -m $maskFile -q 0.05 \
        --othresh=${transformOutpath}/oneSampT_${mniVoxSize}MNI_${kernel}mm-sm_${varSmoothKernal}mm-var-sm_${numPermutations}perm_vox_p_tstat1_0.05fdr.nii.gz
}

transform2mni
merge
smooth_permtest
