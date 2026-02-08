# Necessary imports 
import pandas as pd
import numpy as np

# Files 
from importlib.resources import files

def get_atlas_regions(atlas_name):
    """Print the names of regions in a given subcortical/cerebellar atlas.
    Parameters
    ----------
    atlas_name : str
        Name of the subcortical/cerebellar atlas.

    Returns
    -------
    np.ndarray
        Array of region names in the specified atlas, ordered by segmentation index.
    """

    # If the atlas is the SUIT cerebellar lobules, use hemisphere of 'both'
    if atlas_name == 'SUIT_cerebellar_lobule':
        hemisphere = 'both'

        # Load ordering file
        atlas_ordering = pd.read_csv(files("subcortex_visualization.data").joinpath(f"{atlas_name}_{hemisphere}_ordering.csv"))

        # Identify regions for left/right cerebellar hemispheres versus vermis
        hemisphere_regions = atlas_ordering.query("Hemisphere == 'L'").sort_values('seg_index').region.unique()
        vermis_regions = atlas_ordering.query("Hemisphere=='V'").sort_values('seg_index').region.unique()

        # Return both lists of regions as a tuple
        return (hemisphere_regions, vermis_regions)

    # Else, use left hemisphere just to get names
    else:
        hemisphere='L'

        # Load ordering file
        atlas_ordering = pd.read_csv(files("subcortex_visualization.data").joinpath(f"{atlas_name}_{hemisphere}_ordering.csv"))

        # Sort by segmentation index and print the array of region names
        unique_regions = atlas_ordering.sort_values('seg_index').region.unique()

        return unique_regions
