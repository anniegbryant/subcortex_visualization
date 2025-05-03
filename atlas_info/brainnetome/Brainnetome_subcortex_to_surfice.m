addpath('/Users/abry4213/github/surfice_atlas/');
addpath('/Users/abry4213/github/spmScripts/');
addpath('/Users/abry4213/Documents/MATLAB/spm/');


%%
function cmap = viridis_colormap()
% 256x3 viridis colormap
% Source: matplotlib viridis (resampled)

cmap = [...
    0.267, 0.005, 0.329;
    0.283, 0.141, 0.458;
    0.254, 0.265, 0.530;
    0.207, 0.372, 0.553;
    0.164, 0.471, 0.558;
    0.128, 0.567, 0.551;
    0.135, 0.659, 0.518;
    0.267, 0.749, 0.441;
    0.478, 0.821, 0.318;
    0.741, 0.873, 0.150;
    0.993, 0.906, 0.144];  % abbreviated for demo

% Interpolate to 256 colors
cmap = interp1(linspace(0,1,size(cmap,1)), cmap, linspace(0,1,256), 'linear');
end


fnm = 'viridis';
% Get Viridis RGB values for 256 entries
% Use colormap from File Exchange if needed, or generate from Python dump
viridis = viridis_colormap();  % Nx3 RGB in [0,1]

% Convert to 0–255 range
lut = uint8(floor(viridis * 255));

% Save as 768-byte binary: R(256), G(256), B(256)
[p, n] = fileparts(fnm);
fid = fopen(fullfile(p, [n, '.lut']), 'wb');
fwrite(fid, lut', 'uchar');  % must transpose to write by color channel
fclose(fid);

%%

Brainnetome_subcortex_nifti_L = '/Users/abry4213/github/subcortex_visualization/testing/brainnetome/Brainnetome_1mm_subcortex_L.nii.gz';
lut = '/Users/abry4213/github/surfice_atlas/mylut.lut';
% lut = 'viridis.lut';

nii_nii2atlas(Brainnetome_subcortex_nifti_L, lut, 'Brainnetome_1mm_subcortex_left.mz3');