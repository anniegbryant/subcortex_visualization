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

def plot_subcortical_data(subcortex_data,
                          line_thickness=1.5, line_color='black',
                          hemisphere='L', fill_title = "values", cmap='viridis', 
                          vmin=None, vmax=None,):
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

    if vmin is None:
        vmin = np.min(fill_values)
    if vmax is None:
        vmax = np.max(fill_values)

    # Normalize values and set up colormap
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
    plt.show()