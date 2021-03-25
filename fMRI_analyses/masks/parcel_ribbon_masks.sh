#!/bin/bash

# This script shows an example for mask creation. It takes input from freesurfer recon-all
# results, and creates masks for functional runs in subject native space.

# Note: To find out what value corresponds to what ROI in the parcellation file, a lookup table
# can be found at $FREESURFER_HOME/FreeSurferColorLUT.txt. The first column of that file
# indicates the numbers shown in the parcellation files.
# If you need a mask for a particular ROI, find the ROI ID and change step a and b in the
# ribbon_masks function to extract the number you want.


. /u/local/Modules/default/init/modules.sh
module load fsl/5.0.10
module load freesurfer/6.0.0

fmriprepDir="/u/project/cparkins/data/hierarchy/derivatives/fmriprep"  # to find a functional run
freesurferDir="/u/project/cparkins/data/hierarchy/derivatives/freesurfer"
maskDir="/u/project/CCN/cparkins/data/hierarchy/derivatives/masks"
outDir="$maskDir/ribbon_masks"
subjectList=($(ls -d ${fmriprepDir}/sub*/ | grep -o sub-...)) #$1
dilate=2  # in mm


function all_parcel_masks() {
    # this function creates ROI masks for all parcels found in a subject's aparcaseg file
    cd $maskDir
	# extracts all ROI ID-name pairs from FreeSurferColorLUT.txt
	# cat $FREESURFER_HOME/FreeSurferColorLUT.txt | grep -o '^[0-9]\+\s\+[-_.a-zA-Z0-9]\+' > ROIlist.txt
	declare -A roi_map
	while IFS=' ' read id name  # ROI ID and ROI name are separated by space in ROIlist.txt
	do
		roi_map[$id]=$name  # create a hash map of ROI ID-name pairs
	done < ROIlist.txt
	# iterate through subjects
    for sid in "${subjectList[@]}"
    do
        aparcasegDir=$freesurferDir/$sid/mri  # parcellation file
        aparcaseg=${aparcasegDir}/aparc.DKTatlas+aseg.nii.gz
        mri_convert --in_type mgz --out_type nii ${aparcasegDir}/aparc.DKTatlas+aseg.mgz $aparcaseg
        mkdir $outDir/$sid
        # iterate through all ROIs
        for roi_id in "${!roi_map[@]}"
        do
			# use ROI ID +- 0.1 as thresholds
            lower_thr=`echo "$roi_id-0.1" | bc`
            upper_thr=`echo "$roi_id+0.1" | bc`
            # get the number of voxels that has the ROI label i
            roi_voxels=`fslstats $aparcaseg -l $lower_thr -u $upper_thr -V | grep -o '^[0-9]*'`
			roi_name=${roi_map[$roi_id]}
            echo -e "\t\t\t\t${sid}\t${roi_id}\t${roi_name}\t${roi_voxels} voxels"
            if [ $roi_voxels -gt 0 ]  # if ROI has more than 0 voxel
            then
            	echo -e "${sid}\t${roi_id}\t${roi_name}\t${roi_voxels} voxels"
                # make mask
                fslmaths $aparcaseg -thr $lower_thr -uthr $upper_thr -bin $outDir/$sid/${sid}_roi${roi_id}-${roi_name}.nii.gz
                # resample
                flirt -in $outDir/$sid/${sid}_roi${roi_id}-${roi_name}.nii.gz \
                      -ref $fmriprepDir/$sid/func/$sid\_task-face_run-01_bold_space-T1w_preproc.nii.gz \
                      -applyxfm -usesqform \
                      -out $outDir/$sid/${sid}_roi${roi_id}-${roi_name}_rsmp.nii.gz
                fslmaths $outDir/$sid/${sid}_roi${roi_id}-${roi_name}_rsmp.nii.gz -thr 0.5 -bin $outDir/$sid/${sid}_roi${roi_id}-${roi_name}_rsmp.nii.gz
                # dilate
                fslmaths $outDir/$sid/${sid}_roi${roi_id}-${roi_name}_rsmp.nii.gz -kernel sphere $dilate -dilM $outDir/$sid/${sid}_roi${roi_id}-${roi_name}_rsmp_dil${dilate}mm.nii.gz
                # remove intermediate files
                rm $outDir/$sid/${sid}_roi${roi_id}-${roi_name}.nii.gz
                rm $outDir/$sid/${sid}_roi${roi_id}-${roi_name}_rsmp.nii.gz
            fi
        done
        rm $aparcaseg
    done
}


function ribbon_masks() {
    # this function creates one corticol ribbon mask for each subject. If you need masks for another ROI,
    # change step a and step b in this function.
    cd $maskDir
    for sid in "${subjectList[@]}"
    do
        # a) convert freesurfer ribbon.mgz to nifti
        mri_convert $freesurferDir/$sid/mri/ribbon.mgz $outDir/$sid\_ribbon.nii.gz
        # b) make a ribbon mask by taking out 3 (Left-Cerebral-Cortex) and 42 (Right-Cerebral-Cortex)
        #  1) minus 22.5  2) take absolute value  3) mask out everything other than 19.5  4) convert to binary
        fslmaths $outDir/$sid\_ribbon.nii.gz -sub 22.5 -abs -thr 19.5 -uthr 19.5 -bin $outDir/$sid\_ribbon.nii.gz
        c) resample
        flirt -in $outDir/$sid\_ribbon.nii.gz \
              -ref $fmriprepDir/$sid/func/$sid\_task-face_run-01_bold_space-T1w_preproc.nii.gz \
              -applyxfm -usesqform \
              -out $outDir/$sid\_ribbon_rsmp.nii.gz
        fslmaths $outDir/$sid\_ribbon_rsmp.nii.gz -thr 0 -bin $outDir/$sid\_ribbon_rsmp0.nii.gz
        # d) dilate
        fslmaths $outDir/$sid\_ribbon_rsmp0.nii.gz -kernel sphere $dilate -dilM $outDir/$sid\_ribbon_rsmp0_dil${dilate}mm.nii.gz
    done
}

# all_parcel_masks
ribbon_masks
