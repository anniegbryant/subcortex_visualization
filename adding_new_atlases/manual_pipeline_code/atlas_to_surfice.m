function surfice_res = atlas_to_surfice(input_nifti_volume, output_mz3_volume, lut_file)

    % Check if lut_file is provided, if not set to empty
    if nargin < 3
        lut_file = [];
    end

    % Add paths for surfice
    addpath('/Users/abry4213/github/surfice_atlas/');
    addpath('/Users/abry4213/github/spmScripts/');
    addpath('/Users/abry4213/Documents/MATLAB/spm/');

    % Run nii_nii2atlas
    nii_nii2atlas(input_nifti_volume, lut_file, output_mz3_volume);