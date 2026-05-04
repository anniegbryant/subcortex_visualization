# Necessary imports 
import pandas as pd
import numpy as np

# Files 
from importlib.resources import files

def get_atlas_regions(atlas_name):
    """
    Return the names of regions in a given subcortical or cerebellar atlas.

    Parameters
    ----------
    atlas_name : str
        Name of the subcortical/cerebellar atlas.

    Returns
    -------
    np.ndarray or tuple of np.ndarray
        For most atlases: a 1-D array of region names ordered by segmentation index.
        For 'SUIT_cerebellar_lobule': a tuple of (hemisphere_regions, vermis_regions).
        For 'Brainstem_Navigator': a tuple of (hemisphere_regions, midline_regions).
    """

    # If the atlas is the SUIT cerebellar lobules, use hemisphere of 'both'
    if atlas_name == 'SUIT_cerebellar_lobule':
        hemisphere = 'both'

        # Load ordering file
        atlas_ordering = pd.read_csv(files("subcortex_visualization").joinpath(f"data/{atlas_name}/{atlas_name}_{hemisphere}_ordering.csv"))

        # Identify regions for left/right cerebellar hemispheres versus vermis
        hemisphere_regions = atlas_ordering.query("Hemisphere == 'L'").sort_values('seg_index').region.unique()
        vermis_regions = atlas_ordering.query("Hemisphere=='V'").sort_values('seg_index').region.unique()

        # Return both lists of regions as a tuple
        return (hemisphere_regions, vermis_regions)

    # If atlas is Brainstem_Navigator, some regions are 'B' (both) and some regions are 'L' or 'R'
    if atlas_name == 'Brainstem_Navigator':
        # Load ordering file
        atlas_ordering = pd.read_csv(files("subcortex_visualization").joinpath(f"data/{atlas_name}/{atlas_name}_L_ordering.csv"))

        # Sort by segmentation index and print the array of region names
        hemisphere_regions = atlas_ordering.query("Hemisphere=='L'").sort_values('seg_index').region.unique()
        midline_regions = atlas_ordering.query("Hemisphere=='B'").sort_values('seg_index').region.unique()

        # Return both lists of regions as a tuple
        return (hemisphere_regions, midline_regions)

    # Else, use left hemisphere just to get names
    else:
        hemisphere='L'

        # Load ordering file
        atlas_ordering = pd.read_csv(files("subcortex_visualization").joinpath(f"data/{atlas_name}/{atlas_name}_{hemisphere}_ordering.csv"))

        # Sort by segmentation index and print the array of region names
        unique_regions = atlas_ordering.sort_values('seg_index').region.unique()

        return unique_regions
