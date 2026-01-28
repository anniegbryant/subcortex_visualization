# Necessary imports 
import os
import numpy as np
import pandas as pd

# neuromaps imports
from neuromaps.parcellate import Parcellater

# Files 
from importlib.resources import files

def apply_atlas_to_data(functional_map, atlas, func_name='Functional map'):
    """Apply subcortical atlas(es) to a given functional map and extract mean signal per region.
    Parameters
    ----------
    functional_map : str or Nifti1Image
        Filepath to functional map NIfTI image or Nifti1Image object.
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

        # Use the Parcellator object from neuromaps to apply the atlas to the functional map
        parcellator = Parcellater(this_atlas_volume_path, 'MNI152')
        functional_map_parc = parcellator.fit_transform(functional_map, 'MNI152', True).squeeze()

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