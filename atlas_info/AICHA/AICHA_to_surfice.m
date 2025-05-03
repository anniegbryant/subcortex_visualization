addpath('/Users/abry4213/github/surfice_atlas/');
addpath('/Users/abry4213/github/spmScripts/');
addpath('/Users/abry4213/Documents/MATLAB/spm/');

AICHA_subcortex_nifti_L = '/Users/abry4213/github/subcortex_visualization/testing/AICHA/atlas_aicha_subcortex_L.nii.gz';
lut = '/Users/abry4213/github/surfice_atlas/mylut.lut';

nii_nii2atlas(AICHA_subcortex_nifti_L, lut, 'AICHA_subcortex_left.mz3');