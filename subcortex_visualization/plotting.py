# Necessary imports 
import pandas as pd
import numpy as np
import random

# SVG parsing
from IPython.display import SVG, display
import xml.etree.ElementTree as ET
from svgpath2mpl import parse_path

# matplotlib plotting
import matplotlib
from matplotlib.colors import to_hex
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib.patches import PathPatch

# Files 
from importlib.resources import files

def plot_subcortical_data(subcortex_data=None,
                          line_thickness=1.5, line_color='black',
                          hemisphere='L', fill_title = "values", cmap='viridis', 
                          vmin=None, vmax=None, midpoint=None,
                          show_figure=True):
    """
    Visualize subcortical brain data on an SVG map using matplotlib.

    Parameters
    ----------
    subcortex_data : pandas.DataFrame, optional
        DataFrame with columns ['region', 'value', 'Hemisphere'].
        If None, a default dataset is generated based on the selected hemisphere.

    line_thickness : float, default=1.5
        Thickness of the outline for each region.

    line_color : str, default='black'
        Color of the outline around each subcortical region.

    hemisphere : {'L', 'R', 'both'}, default='L'
        Which hemisphere(s) to display. Use 'L' for left, 'R' for right, or 'both' for bilateral plots.

    fill_title : str, default="values"
        Label for the colorbar indicating the meaning of the fill values.

    cmap : str or matplotlib.colors.Colormap, default='viridis'
        Colormap used to fill in the regions. Accepts a string name or a Colormap object.

    vmin : float, optional
        Minimum value for colormap normalization. If None, the minimum of the input values is used.

    vmax : float, optional
        Maximum value for colormap normalization. If None, the maximum of the input values is used.

    midpoint : float, optional
        If provided, uses a diverging colormap centered around this value.

    show_figure : bool, default=True
        If True, displays the figure using `plt.show()`. If False, returns the matplotlib Figure object.

    Returns
    -------
    matplotlib.figure.Figure or None
        The generated figure, if `show_figure` is False. Otherwise, displays the plot and returns None.

    Notes
    -----
    - The function loads SVG files and a lookup CSV bundled with the package, which can be found under `data/` directory.
    - It assumes SVGs are named `subcortex_base_L.svg` and `subcortex_base_R.svg` in the package `data/` directory.
    - The input `subcortex_data` should align with regions defined in the lookup table.
    """
        
    # Load SVG
    svg_path = files("subcortex_visualization.data").joinpath(f"subcortex_base_{hemisphere}.svg")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Load subcorticla paths lookup
    subcortical_paths_lookup_path = files("subcortex_visualization.data").joinpath("subcortical_paths_lookup.csv")
    subcortical_paths_lookup = pd.read_csv(subcortical_paths_lookup_path)

    # Define SVG namespace
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    ET.register_namespace('', ns['svg'])  # Prevents adding ns0 in output

    # Find objects
    paths = root.findall('.//svg:path', ns)  # for example, all <path> elements

    # If the user didn't provide subcortex_data, simply generate a dataframe with indices from 1 to 7 (if left/right) or 1 to 14 (if both)
    if subcortex_data is None:
        if hemisphere == 'both':
            subcortex_data = pd.DataFrame({"region": ["accumbens", "amygdala", "caudate", "hippocampus", "pallidum", "putamen", "thalamus"]*2, 
                                           "Hemisphere": ["L"]*7 + ["R"]*7,
                                           "value": list(range(7)) + list(range(7))}).assign(Num_Hemi = 2)
        else:
            subcortex_data = pd.DataFrame({"region": ["accumbens", "amygdala", "caudate", "hippocampus", "pallidum", "putamen", "thalamus"], 
                                           "value": range(7)}).assign(Hemisphere = hemisphere, Num_Hemi = 1)

    # If hemisphere = 'both', filter subcortical_paths_lookup to Num_Hemi == 2
    if hemisphere == 'both':
        subcortical_paths_lookup = subcortical_paths_lookup.query("Num_Hemi == 2")
        # Merge example data with paths
        subcortex_data_with_paths = (subcortex_data
                                            .merge(subcortical_paths_lookup, on=['region', 'Hemisphere'], how='left')
                                            .sort_values('path_number'))
    else:
        subcortical_paths_lookup = subcortical_paths_lookup.query("Num_Hemi == 1")
        # Merge example data with paths
        subcortex_data_with_paths = (subcortex_data
                                            .merge(subcortical_paths_lookup, on=['region', 'Hemisphere'], how='left')
                                            .query("Hemisphere == @hemisphere")
                                            .sort_values('path_number'))

    # Extract fill values
    fill_values = subcortex_data_with_paths['value'].values

    if midpoint is not None:
        # Compute max absolute deviation from the midpoint
        max_dev = np.max(np.abs(fill_values - midpoint))

        # If vmin or vmax is not set, define them symmetrically around midpoint
        if vmin is None:
            vmin = midpoint - max_dev
        if vmax is None:
            vmax = midpoint + max_dev

        norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=midpoint, vmax=vmax)
    else:
        if vmin is None:
            vmin = np.min(fill_values)
        if vmax is None:
            vmax = np.max(fill_values)
            
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    
    if isinstance(cmap, str):
        cmap = matplotlib.colormaps.get_cmap(cmap)
        
    elif isinstance(cmap, mcolors.Colormap):
        pass

    # Start plotting
    fig, ax = plt.subplots(figsize=(6, 6))

    patches = []
    for path_elem, fill_value in zip(paths, fill_values):
        d = path_elem.attrib['d']
        path = parse_path(d)
        patch = PathPatch(path, facecolor=cmap(norm(fill_value)), edgecolor=line_color, lw=line_thickness)
        ax.add_patch(patch)
        patches.append(patch)

    # Set axis limits and aspect
    ax.autoscale_view()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.invert_yaxis()  # <- This fixes the upside-down SVG

    # Add colorbar
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])  # required for colorbar to render
    cbar = fig.colorbar(sm, ax=ax, orientation='horizontal', fraction=0.046, pad=0.04)
    cbar.set_label(fill_title)

    plt.tight_layout()

    if show_figure:
        plt.show()
    
    else:
        # Return the plot
        return fig