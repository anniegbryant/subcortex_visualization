# Activate subcortex_visualization environment
source ~/miniforge3/etc/profile.d/conda.sh
conda activate subcortex_visualization

# Define path to volumes
volumes_path=/Users/abry4213/github/subcortex_visualization/atlas_info
mesh_code_path=/Users/abry4213/github/subcortex_vis_writeup/custom_segmentation_pipeline
mesh_output_path=$mesh_code_path/mesh_outputs/

cd $mesh_code_path/

########################## Brainstem Navigator, right-hemisphere only ##########################

# Brainstem navigator: from directory of ROIs to one mesh
if ! test -f $mesh_output_path/Brainstem_Navigator.mz3; then

  # Generate viridis palette for 37 regions
  python generate_color_map.py --num_colors 37 --cmap_name viridis --output_file viridis_37.txt

  # Single-hemisphere
  python individual_volumes_to_mesh_mz3.py \
    --input_dir /Users/abry4213/github/subcortex_visualization/testing/Brainstem_Navigator_v1.0/2a.BrainstemNucleiAtlas_MNI/labels_thresholded_binary_0.35_RH \
      --output_path $mesh_output_path --out_file Brainstem_Navigator.mz3 \
        --colors viridis_37.txt --delete_mz3
        
  # Remove the temporary color file
  rm viridis_37.txt
fi

########################## Brainstem Navigator, bilateral ##########################

# Brainstem navigator: from directory of ROIs to one mesh
if ! test -f $mesh_output_path/Brainstem_Navigator_Bilateral.mz3; then

  # Generate viridis palette for 66 regions
  python generate_color_map.py --num_colors 66 --cmap_name viridis --output_file viridis_66.txt

  # Bilateral
  python individual_volumes_to_mesh_mz3.py \
    --input_dir /Users/abry4213/github/subcortex_visualization/testing/Brainstem_Navigator_v1.0/2a.BrainstemNucleiAtlas_MNI/labels_thresholded_binary_0.35 \
      --output_path $mesh_output_path --out_file Brainstem_Navigator_Bilateral.mz3 \
        --colors viridis_66.txt
        
  # Remove the temporary color file
  rm viridis_66.txt
fi
