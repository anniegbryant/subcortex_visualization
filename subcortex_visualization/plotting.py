# Necessary imports 
import pandas as pd
import numpy as np

# SVG parsing
import xml.etree.ElementTree as ET
from svgpath2mpl import parse_path

# matplotlib plotting
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import PathPatch, Patch

# Files 
from importlib.resources import files

def plot_subcortical_data(subcortex_data=None, atlas='aseg',
                          line_thickness=1.5, line_color='black',
                          hemisphere='L', fill_title="values", cmap='viridis',
                          vmin=None, vmax=None, midpoint=None, show_legend=True,
                          show_figure=True):
    
    """
    Visualize subcortical brain data on an SVG map using matplotlib.

    Parameters
    ----------
    subcortex_data : pandas.DataFrame, optional
        DataFrame with columns ['region', 'value', 'Hemisphere'].
        If None, a default dataset is generated based on the selected hemisphere.

    atlas : str, default='aseg'
        The atlas used for the subcortical regions. Currently, two options are supported: 'aseg' and 'Tian_S1'.

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

    show_legend : bool, default=True
        If True, displays a legend or colorbar indicating the mapping of values to colors.

    show_figure : bool, default=True
        If True, displays the figure using `plt.show()`. If False, returns the matplotlib Figure object.

    Returns
    -------
    matplotlib.figure.Figure or None
        The generated figure, if `show_figure` is False. Otherwise, displays the plot and returns None.

    Notes
    -----
    - The function loads SVG files and a lookup CSV bundled with the package, which can be found under `data/` directory.
    - The input `subcortex_data` should align with regions defined in the lookup table.
    """
    
    # Load SVG
    svg_path = files("subcortex_visualization.data").joinpath(f"subcortex_{atlas}_base_{hemisphere}.svg")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Define SVG namespace
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    ET.register_namespace('', ns['svg'])

    # Find path elements
    paths = root.findall('.//svg:path', ns)

    # Load ordering file
    atlas_ordering = pd.read_csv(files("subcortex_visualization.data").joinpath(f"{atlas}_{hemisphere}_ordering.csv"))

    # Handle colormap
    if isinstance(cmap, str):
        cmap = matplotlib.colormaps.get_cmap(cmap)

    if subcortex_data is None:
        # Assign discrete indices per region
        unique_regions = atlas_ordering['region'].unique()
        region_to_index = {region: idx for idx, region in enumerate(unique_regions)}
        atlas_ordering['value'] = atlas_ordering['region'].map(region_to_index)
        
        # Discrete colormap
        num_regions = len(unique_regions)
        cmap_colors = cmap(np.linspace(0, 1, num_regions))
        color_lookup = {region: cmap_colors[i] for region, i in region_to_index.items()}
    else:
        # Merge and normalize
        atlas_ordering = atlas_ordering.merge(subcortex_data, on=['region', 'Hemisphere'], how='left')

        fill_values = atlas_ordering['value'].values

        if midpoint is not None:
            max_dev = np.nanmax(np.abs(fill_values - midpoint))
            if vmin is None:
                vmin = midpoint - max_dev
            if vmax is None:
                vmax = midpoint + max_dev
            norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=midpoint, vmax=vmax)
        else:
            if vmin is None:
                vmin = np.nanmin(fill_values)
            if vmax is None:
                vmax = np.nanmax(fill_values)
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    # Start plotting
    if hemisphere == 'both': 
        fig, ax = plt.subplots(figsize=(12,6))
    else:
        fig, ax = plt.subplots(figsize=(7, 6))
    patches = []

    for _, row in atlas_ordering.iterrows():
        this_region = row['region']
        this_region_side = row['face']
        this_region_hemi = row['Hemisphere']

        # Determine color
        if subcortex_data is None:
            this_region_color = color_lookup[this_region]
        else:
            val = row['value']
            this_region_color = cmap(norm(val)) if not pd.isnull(val) else "#cccccc"

        # Match title to region
        for path in paths:
            for child in path:
                if child.tag.endswith('title') and child.text == f"{this_region}_{this_region_side}_{this_region_hemi}":
                    d = path.attrib['d']
                    path_obj = parse_path(d)
                    patch = PathPatch(path_obj, facecolor=this_region_color,
                                      edgecolor=line_color, lw=line_thickness)
                    ax.add_patch(patch)
                    patches.append(patch)

    ax.autoscale_view()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.invert_yaxis()

    if show_legend:
        if subcortex_data is None:
            # Discrete legend
            unique_regions = atlas_ordering[['region', 'value']].drop_duplicates()
            legend_elements = [
                Patch(facecolor=cmap_colors[row['value']], edgecolor='black', label=row['region'])
                for _, row in unique_regions.iterrows()
            ]
            # Add legend to the plot
            ax.legend(handles=legend_elements, loc='lower center',
                      bbox_to_anchor=(0.5, -0.25), ncol=4, frameon=False,
                      fontsize='medium', handleheight=1.2, handlelength=1.2,
                      title=fill_title, 
                      handletextpad=0.4)
            fig.subplots_adjust(bottom=0.5)  # Reserve space for legend

        else:
            # Continuous colorbar
            sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])  # Only needed for compatibility
            cbar = fig.colorbar(sm, ax=ax, orientation='horizontal', fraction=0.046, pad=0.04)
            cbar.set_label(fill_title)

    plt.tight_layout()

    if show_figure:
        plt.show()
    else:
        return fig
