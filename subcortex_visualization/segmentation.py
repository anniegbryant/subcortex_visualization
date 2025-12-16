# Necessary imports 
import os
import numpy as np
import pandas as pd

# Imaging masker
from nilearn.maskers import NiftiLabelsMasker

# Files 
from importlib.resources import files

def apply_atlas_to_data(functional_map, atlas, func_name='Functional map'):
    """Apply subcortical atlas to functional map and extract mean signal per region.
    Parameters
    ----------
    functional_map : str
        Filepath to functional map NIfTI image.
    atlas : str or list of str
        Name(s) of the subcortical atlas/atlases to apply.
    func_name : str, optional
        Name of the functional map for labeling purposes. Default is 'Functional map'.
    Returns
    -------
    pd.DataFrame
        DataFrame containing mean signal per region for each atlas applied.
    """

    if isinstance(atlas, str):
        atlas = [atlas]

    atlas_results_list = []

    for this_atlas in atlas:

        if this_atlas in ["Thalamus_Nuclei_HCP", "SUIT_cerebellar_lobule"]:
            this_atlas_file = this_atlas
            
        else: 
            this_atlas_file = this_atlas + "_subcortex"
        
        # Define atlas volume
        this_atlas_volume_path = files("subcortex_visualization.atlases").joinpath(f"{this_atlas_file}.nii.gz")

        # Define atlas lookup table (LUT)
        this_atlas_LUT = pd.read_csv(files("subcortex_visualization.atlases").joinpath(f"{this_atlas_file}_lookup.csv"), header=None)
        this_atlas_LUT.columns = ['Index', 'Region']

        # Apply example_seg to example_functional_map
        masker = NiftiLabelsMasker(
            labels_img=this_atlas_volume_path,
            memory="nilearn_cache",
            standardize=False
        )

        # Apply masker to functional map
        functional_map_parc = masker.fit_transform(functional_map)

        # Make sure the results are one-column
        functional_map_parc = functional_map_parc.flatten()

        # Merge region and index 
        functional_map_parc_df = pd.DataFrame({'Functional_Map': func_name,
                                            'Atlas': this_atlas,
                                            'Region': this_atlas_LUT['Region'],
                                            'Mean_Signal': functional_map_parc})

        # Split 'Region' into 'region' and 'Hemisphere'
        functional_map_parc_df[['region', 'Hemisphere']] = functional_map_parc_df['Region'].str.rsplit('-', n=1, expand=True)

        # Set 'Hemisphere' to a case switch where 'rh' --> 'R', 'lh' --> 'L', or 'vermis' --> 'V'
        functional_map_parc_df['Hemisphere'] = functional_map_parc_df['Hemisphere'].map({'rh': 'R', 'lh': 'L', 'vermis': 'V'})
        functional_map_parc_df.drop(columns=['Region'], inplace=True)

        # Append to results list
        atlas_results_list.append(functional_map_parc_df)

    final_atlas_results = pd.concat(atlas_results_list, ignore_index=True)

    # Return the final DataFrame
    return final_atlas_results