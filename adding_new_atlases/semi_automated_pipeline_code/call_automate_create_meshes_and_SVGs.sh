#!/usr/bin/env bash

# This script calls the create_meshes_and_SVGs.py script for each atlas
repository_path=/path/to/cloned/subcortex_visualization/
atlas_name=name_of_new_atlas

# Copy the atlas in its original space to its own directory in atlas_info, if it doesn't already exist there
atlas_data_path=${repository_path}/atlas_info/original_space/${atlas_name}
atlas_SVG_output_path=$repository_path/subcortex_visualization/data/${atlas_name}

smooth_i=20 # Number of iterations for smoothing the meshes; default is 20, but can be adjusted based on the atlas and desired level of smoothing
smooth_f=0.9 # Smoothing factor for the meshes; default is 0.9, but can be adjusted based on the atlas and desired level of smoothing
cmap=viridis # Colormap to use for the meshes and SVGs; default is 'viridis', but can be adjusted based on the atlas and desired colormap

# Define paths to atlas data
atlas_nii=$atlas_data_path/$atlas_name/${atlas_name}.nii.gz
atlas_lookup_txt=$atlas_data_path/$atlas_name/${atlas_name}_lookup.txt

# Call python script
python automate_create_meshes_and_SVGs.py --atlas_name ${atlas_name} \
    --atlas_nii ${atlas_nii} \
    --atlas_lookup_txt ${atlas_lookup_txt} \
    --atlas_output_data_path ${atlas_SVG_output_path} \
    --smooth_i ${smooth_i} \
    --smooth_f ${smooth_f} \
    --cmap ${cmap}
