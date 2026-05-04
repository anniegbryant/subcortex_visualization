# Necessary imports 
import os
import numpy as np
import pandas as pd

# neuromaps imports
import nibabel as nib
from nilearn.image import resample_img

# Files 
from importlib.resources import files

# Regular expressions
import re

def parcel_segstats(input_vol, atlas_space='MNI152NLin6Asym', 
                    atlas='aseg_subcortex', func_name='Functional map', parc_stat=np.mean,
                    ignore_background=True, background_value=0, interpolation=None):
    """
    Extract voxel values from an input volume based on a parcellation atlas and apply a reduction function to each parcel.

    Parameters
    ----------
    input_vol : nibabel.nifti1.Nifti1Image or str
        The input 3D or 4D NIfTI image from which to extract voxel values. Can be a nibabel Nifti1Image object or a file path to a NIfTI image.

    atlas_space : str, optional
        The standard space to use for the corresponding atlas. Options include 'MNI152NLin6Asym' (the default) and 'MNI152NLin2009cAsym'.

    atlas : str or list of str, optional
        Name(s) of the subcortical atlas/atlases to apply. Default is 'aseg_subcortex', which is the FreeSurfer subcortical segmentation atlas. If multiple atlases are provided, the function will iterate over them and concatenate results.

    func_name : str, optional
        A name for the functional map being summarized, used for labeling purposes in the output DataFrame. Default is 'Functional map'.

    parc_stat : function, optional
        A function like np.mean, np.std, etc. that takes an array of values and returns a single summary statistic (scalar). Default is np.mean.
        Can also be a list of functions, in which case the output DataFrame will have one row per parcel per summary statistic.

    ignore_background : bool, default=True
        If True, the background label (as defined by ``background_value``) is skipped
        when extracting parcel values.

    background_value : int, default=0
        Integer label in the parcellation that represents background (non-parcel) voxels.

    interpolation : str or None, optional
        If the input volume and atlas have different affines or spatial dimensions, this parameter
        specifies the interpolation method for resampling the atlas to match the input volume.
        Options include 'nearest', 'linear', and 'cubic'. If None (default), no resampling is
        performed and an error will be raised if affines or dimensions do not match.

    Returns
    -------
    results_df : pandas.DataFrame
        One row per parcel per summary statistic, with columns:
        'stat', 'value', 'Atlas', 'Functional_Map', 'region', 'Hemisphere', 'Region_Index'.

    Notes
    -----
    - Users should ensure that the input volume is in the same standard space as the atlas specified by `atlas_space` to avoid issues with affine and spatial dimension mismatches. If resampling is necessary, users must specify an interpolation method.
    """

    if isinstance(atlas, str):
        atlas = [atlas]

    if not isinstance(parc_stat, list):
        parc_stat = [parc_stat]

    # Load in the input volume, if it's a file path
    if isinstance(input_vol, str):
        input_vol = nib.load(input_vol)

    # Find the affine and input data dimensions
    input_vol_affine = input_vol.affine
    input_data = input_vol.get_fdata()

    # Initialize list to hold results dataframes for each atlas
    results_df_list = []
    
    # Iterate over user-specified atlas(es)
    for this_atlas in atlas:

        if this_atlas == 'Brainstem_Navigator':
            # One NIFTI file per ROI — discover all .nii.gz files in the atlas directory
            atlas_dir = files("subcortex_visualization.atlases").joinpath(f"{atlas_space}/{this_atlas}")
            nifti_files = sorted([f for f in atlas_dir.iterdir() if f.name.endswith('.nii.gz')])

            for roi_idx, nifti_path in enumerate(nifti_files):
                roi_name = nifti_path.name.replace('.nii.gz', '')
                roi_vol = nib.load(nifti_path)
                roi_vol_affine = roi_vol.affine

                if not np.allclose(input_vol_affine, roi_vol_affine):
                    if interpolation is not None:
                        print(f"Resampling ROI '{roi_name}' to match input data affine and dimensions using {interpolation} interpolation...")
                        roi_vol = resample_img(roi_vol, target_affine=input_vol_affine, target_shape=input_data.shape[:3], interpolation=interpolation, force_resample=True, copy_header=True)
                    else:
                        raise ValueError(f"No resampling method was specified. Re-run this function with a specified 'interpolation' argument from the available options for resample_img (including 'nearest', 'cubic', or 'linear') to resample ROI '{roi_name}' to your input data.\nInput data affine:\n{input_vol_affine}\nROI affine:\n{roi_vol_affine}\n")

                roi_data = roi_vol.get_fdata()
                mask = roi_data != 0

                if input_data.shape[:3] != roi_data.shape[:3]:
                    min_shape = np.minimum(input_data.shape[:3], roi_data.shape[:3])
                    input_data_roi = input_data[:min_shape[0], :min_shape[1], :min_shape[2]]
                    mask = mask[:min_shape[0], :min_shape[1], :min_shape[2]]
                else:
                    input_data_roi = input_data

                voxels = input_data_roi[mask]

                if input_data.ndim == 4:
                    voxels = voxels.reshape(-1, input_data.shape[-1])
                    vals = [s(voxels, axis=0) for s in parc_stat]
                else:
                    vals = [s(voxels, axis=0) for s in parc_stat]

                this_lab_df = pd.DataFrame({
                    'stat': [s.__name__ for s in parc_stat],
                    'value': vals
                })

                this_hemi = 'B'
                if roi_name.endswith(('_lh', '-lh', '-L', '_L', '_l')):
                    this_hemi = 'L'
                elif roi_name.endswith(('_rh', '-rh', '-R', '_R', '_r')):
                    this_hemi = 'R'
                elif 'vermis' in roi_name:
                    this_hemi = 'V'

                this_region_clean = re.sub(r'(_lh|-lh|-L|_L|_l|_rh|-rh|-R|_R|_r|-vermis)$', '', roi_name)

                this_lab_df['Atlas'] = this_atlas
                this_lab_df['Functional_Map'] = func_name
                this_lab_df['region'] = this_region_clean
                this_lab_df['Hemisphere'] = this_hemi
                this_lab_df['Region_Index'] = roi_idx + 1

                results_df_list.append(this_lab_df)

        else:
            # Define atlas volume
            this_atlas_volume_path = files("subcortex_visualization.atlases").joinpath(f"{atlas_space}/{this_atlas}/{this_atlas}.nii.gz")
            # Try loading atlas, if that fails, append _subcortex and try again (since some atlases have that suffix in the filename)
            try:
                this_atlas_vol = nib.load(this_atlas_volume_path)
                # Define atlas lookup table (LUT)
                this_atlas_LUT = pd.read_csv(files("subcortex_visualization.atlases").joinpath(f"{atlas_space}/{this_atlas}/{this_atlas}_lookup.csv"), header=None)
            except FileNotFoundError:
                try:
                    this_atlas_volume_path = files("subcortex_visualization.atlases").joinpath(f"{atlas_space}/{this_atlas}/{this_atlas}_subcortex.nii.gz")
                    this_atlas_vol = nib.load(this_atlas_volume_path)
                    Warning(f"Atlas volume file for atlas '{this_atlas}' not found with expected filename '{this_atlas}.nii.gz'. Successfully loaded atlas volume with alternative filename '{this_atlas}_subcortex.nii.gz'. Please check that the atlas volume file in the package directory is named according to one of these two conventions to avoid this warning in the future.")

                    this_atlas_LUT = pd.read_csv(files("subcortex_visualization.atlases").joinpath(f"{atlas_space}/{this_atlas}/{this_atlas}_subcortex_lookup.csv"), header=None)

                except FileNotFoundError:
                    raise FileNotFoundError(f"Atlas volume file not found for atlas '{this_atlas}'. Looked for files named '{this_atlas}.nii.gz' and '{this_atlas}_subcortex.nii.gz' in the subcortex_visualization.atlases package directory. Please check that the atlas name is correct and that the corresponding atlas volume file is present in the package directory.")

            # If first row has 'Region_Name' in any column, then set the column names to the first row and drop the first row from the data
            if this_atlas_LUT.iloc[0].str.contains('Region_Name').any():
                this_atlas_LUT.columns = this_atlas_LUT.iloc[0]
                this_atlas_LUT = this_atlas_LUT.drop(0).reset_index(drop=True)

            # Find affines
            this_atlas_vol_affine = this_atlas_vol.affine

            # Compare affines and raise error if they don't match
            if not np.allclose(input_vol_affine, this_atlas_vol_affine):
                # Affines don't match; resample if interpolation is specified, otherwise raise an error
                Warning(f"Affines of input data and atlas do not match. Atlas affine:\n{this_atlas_vol_affine}\nInput data affine:\n{input_vol_affine}\n")

                # Resample the atlas to match the input volume
                if interpolation is not None:
                    print(f"Resampling atlas '{this_atlas}' to match input data affine and dimensions using {interpolation} interpolation...")
                    this_atlas_vol = resample_img(this_atlas_vol, target_affine=input_vol_affine, target_shape=input_data.shape[:3], interpolation=interpolation, force_resample=True, copy_header=True)
                    this_atlas_vol_affine = this_atlas_vol.affine

                else:
                    raise ValueError(f"No resampling method was specified. Re-run this function with a specified 'interpolation' argument from the available options for resample_img (including 'nearest', 'cubic', or 'linear') to resample the desired atlas volume to your input data.\nInput data affine:\n{input_vol_affine}\nAtlas affine:\n{this_atlas_vol_affine} \n")

            # Extract data
            labels = this_atlas_vol.get_fdata()

            # Round to int — resampled atlases may have fractional label values
            labels = np.round(labels).astype(int)

            # If affines match but spatial dims still differ, it's likely an FOV mismatch — crop to the smaller shape
            if input_data.shape[:3] != labels.shape[:3]:
                Warning(f"Spatial dimensions of input data and atlas do not match. Input data shape: {input_data.shape}\nAtlas labels shape: {labels.shape}\nAttempting to crop atlas labels to match input data dimensions...")
                try:
                    min_shape = np.minimum(input_data.shape[:3], labels.shape[:3])
                    input_data = input_data[:min_shape[0], :min_shape[1], :min_shape[2]]
                    labels = labels[:min_shape[0], :min_shape[1], :min_shape[2]]

                except Exception as e:
                    print(f"Error occurred while attempting to crop atlas labels to match input data dimensions: {e}\nUnable to proceed with extraction.")

            # If affines and data dimensions are compatible, proceed with extraction

            this_atlas_LUT.columns = ['Index', 'Region']
            this_atlas_regions = this_atlas_LUT['Region'].values
            unique_labels = np.unique(labels)

            # skip background if requested, which is the default
            if ignore_background:
                unique_labels = unique_labels[unique_labels != background_value]


            # Iterate over each unique label and extract voxel values
            for i, lab in enumerate(unique_labels):
                # If lab is a str/float, convert to int
                lab = int(lab)
                mask = labels == lab
                voxels = input_data[mask]

                # Handle 4D (time series) vs 3D
                if input_data.ndim == 4:
                    voxels = voxels.reshape(-1, input_data.shape[-1])
                    vals = [s(voxels, axis=0) for s in parc_stat]
                else:
                    vals = [s(voxels, axis=0) for s in parc_stat]

                # One row per summary statistic
                this_lab_df = pd.DataFrame({
                    'stat': [s.__name__ for s in parc_stat],
                    'value': vals
                })

                this_atlas_region_full = this_atlas_regions[i]

                # Infer hemisphere from region name suffix
                this_hemi = 'B'
                if this_atlas_region_full.endswith(('_lh', '-lh', '-L', '_L', '_l', '_LH')):
                    this_hemi = 'L'
                elif this_atlas_region_full.endswith(('_rh', '-rh', '-R', '_R', '_r', '_RH')):
                    this_hemi = 'R'
                elif 'vermis' in this_atlas_region_full:
                    this_hemi = 'V'

                # Strip hemisphere suffix to get the clean region name
                this_region_clean = re.sub(r'(_lh|-lh|-L|_L|_l|_LH|_rh|-rh|-R|_R|_r|_RH|-vermis)$', '', this_atlas_region_full)

                # Add region/atlas metadata to the dataframe
                this_lab_df['Atlas'] = this_atlas
                this_lab_df['Functional_Map'] = func_name
                this_lab_df['region'] = this_region_clean
                this_lab_df['Hemisphere'] = this_hemi
                this_lab_df['Region_Index'] = lab

                # Append this label's results to the list
                results_df_list.append(this_lab_df)

    # Concatenate results from all atlases into a single DataFrame
    results_df = pd.concat(results_df_list, ignore_index=True)

    # Return the dataframe
    return results_df