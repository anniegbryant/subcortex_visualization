# Necessary imports 
import pandas as pd
import numpy as np


# Files 
from importlib.resources import files

def get_atlas_regions(atlas_name):

    # Use left hemisphere just to get names
    hemisphere='L'

    # Load ordering file
    atlas_ordering = pd.read_csv(files("subcortex_visualization.data").joinpath(f"{atlas_name}_{hemisphere}_ordering.csv"))

    # Sort by segmentation index and print the array of region names
    unique_regions = atlas_ordering.sort_values('seg_index').region.unique()

    return unique_regions
