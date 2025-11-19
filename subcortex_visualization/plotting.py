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

def add_legend(ax, fig, atlas_ordering, ncols=4, value_column='value', cmap_colors=None, fill_title=None, cmap='plasma', norm=None):
    """
    Add a legend or colorbar to the plot based on the provided data.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes object to which the legend or colorbar will be added.

    fig : matplotlib.figure.Figure
        The figure object containing the plot.

    atlas_ordering : pandas.DataFrame
        DataFrame containing the atlas ordering information.

    value_column : str
        The name of the column in `atlas_ordering` that contains the values to be visualized.

    cmap_colors : list of str, optional
        List of colors corresponding to the regions in the atlas.

    fill_title : str, optional
        Title for the legend or colorbar.

    cmap : str or matplotlib.colors.Colormap, optional
        Colormap to use for the colorbar. Default is 'plasma'.

    norm : matplotlib.colors.Normalize or matplotlib.colors.TwoSlopeNorm, optional
        Normalization object for the colorbar. If None, a discrete legend is created.

    Returns
    -------
    None (adds to the plot directly)
        
    """

    if fill_title is None:
        fill_title = "values"

    if norm is None:
        # Discrete legend
        unique_regions = atlas_ordering[['region', value_column]].drop_duplicates()
        legend_elements = [
            Patch(facecolor=cmap_colors[row[value_column]], edgecolor='black', label=row['region'])
            for _, row in unique_regions.iterrows()
        ]
        # Add legend to the plot
        ax.legend(handles=legend_elements, loc='lower center',
                    bbox_to_anchor=(0.5, -0.25), ncols=ncols, frameon=False,
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

def prep_data(atlas_ordering, value_column='value', subcortex_data=None, cmap=None, vmin=None, vmax=None, midpoint=None):
    """ 
    Prepare data for plotting by merging with subcortex_data and normalizing values.

    Parameters
    ----------
    atlas_ordering : pandas.DataFrame
        DataFrame containing the atlas ordering information.

    value_column : str
        The name of the column in `atlas_ordering` that contains the values to be visualized. Default is 'value'.

    subcortex_data : pandas.DataFrame, optional
        DataFrame with columns ['region', 'value', 'Hemisphere'].
        If None, a default dataset is generated based on the selected hemisphere.
        
    cmap : str or matplotlib.colors.Colormap, optional
        Colormap to use for the colorbar. Default is 'plasma'.

    vmin : float, optional
        Minimum value for colormap normalization. If None, the minimum of the input values is used.

    vmax : float, optional
        Maximum value for colormap normalization. If None, the maximum of the input values is used.

    midpoint : float, optional
        If provided, uses a diverging colormap centered around this value.

    Returns
    -------
    atlas_ordering : pandas.DataFrame
        DataFrame with merged and normalized values.

    color_lookup : dict
        Dictionary mapping region names to colors for discrete colormap.

    cmap_colors : list of str
        List of colors corresponding to the regions in the atlas.

    norm : matplotlib.colors.Normalize or matplotlib.colors.TwoSlopeNorm
        Normalization object for the colorbar. If None, a discrete legend is created.

    Notes
    -----
    - The function handles both discrete and continuous colormaps based on the presence of subcortex_data.
    - If subcortex_data is None, a discrete colormap is created based on the unique regions in atlas_ordering.
    - If subcortex_data is provided, the values are normalized and a continuous colormap is created.
    - The function returns the updated atlas_ordering DataFrame, color lookup dictionary, and colormap colors.

    """

    if subcortex_data is None:
        # Sort by seg_index for color assignment
        atlas_ordering = atlas_ordering.sort_values(by='seg_index').reset_index(drop=True)

        # Assign discrete indices per region
        unique_regions = atlas_ordering['region'].unique()
        region_to_index = {region: idx for idx, region in enumerate(unique_regions)}
        atlas_ordering[value_column] = atlas_ordering['region'].map(region_to_index)
        
        # Discrete colormap
        num_regions = len(unique_regions)
        cmap_colors = cmap(np.linspace(0, 1, num_regions))
        color_lookup = {region: cmap_colors[i] for region, i in region_to_index.items()}

        # Re-sort by plot_order again 
        atlas_ordering = atlas_ordering.sort_values(by='plot_order').reset_index(drop=True)
        
        return atlas_ordering, color_lookup, cmap_colors
    
    else:
        # Merge and normalize
        atlas_ordering = atlas_ordering.merge(subcortex_data, on=['region', 'Hemisphere'], how='left')

        fill_values = atlas_ordering[value_column].values

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

        return atlas_ordering, norm, vmin, vmax, midpoint

def plot_helper(atlas_ordering, paths, value_column='value', hemisphere='L', subcortex_data=None, line_color='black', line_thickness=1.5,
                color_lookup=None, cmap=None, norm=None):
    """ 
    
    Helper function to plot the SVG paths with the specified colors and line properties.

    Parameters
    ----------
    atlas_ordering : pandas.DataFrame
        DataFrame containing the atlas ordering information.

    paths : list of xml.etree.ElementTree.Element
        List of SVG path elements to be plotted.
    
    value_column : str
        The name of the column in `atlas_ordering` that contains the values to be visualized. Default is 'value'.

    hemisphere : {'L', 'R', 'both'}, default='L'
        Which hemisphere(s) to display. Use 'L' for left, 'R' for right, or 'both' for bilateral plots.

    subcortex_data : pandas.DataFrame, optional
        DataFrame with columns ['region', 'value', 'Hemisphere'].
        If None, a default dataset is generated based on the selected hemisphere.

    line_color : str, default='black'
        Color of the outline around each subcortical region.

    line_thickness : float, default=1.5
        Thickness of the outline for each region (in mm)

    color_lookup : dict, optional
        Dictionary mapping region names to colors for discrete colormap.

    cmap : str or matplotlib.colors.Colormap, optional
        Colormap to use for the colorbar. Default is 'plasma'.

    norm : matplotlib.colors.Normalize or matplotlib.colors.TwoSlopeNorm, optional
        Normalization object for the colorbar. If None, a discrete legend is created.
    
    fontsize: font size for the figure. Default to 12.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The generated figure object.

    ax : matplotlib.axes.Axes
        The axes object containing the plot.

    """

    # Start plotting
    if hemisphere == 'both': 
        fig, ax = plt.subplots(figsize=(17,6))
    else:
        fig, ax = plt.subplots(figsize=(8, 6))
    patches = []

    # Ensure atlas_ordering is sorted by plot_order
    atlas_ordering = atlas_ordering.sort_values(by='plot_order')

    for _, row in atlas_ordering.iterrows():
        this_region = row['region']
        this_region_side = row['face']
        this_region_hemi = row['Hemisphere']

        # Determine color
        if subcortex_data is None:
            this_region_color = color_lookup[this_region]
        else:
            val = row[value_column]
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

    return fig, ax

def plot_subcortical_data(subcortex_data=None, atlas='aseg', value_column='value',
                          line_thickness=1.5, line_color='black',
                          hemisphere='L', fill_title="values", cmap='viridis',
                          vmin=None, vmax=None, midpoint=None, show_legend=True,
                          show_figure=True,fontsize=12):
    
    """
    Visualize subcortical brain data on an SVG map using matplotlib.

    Parameters
    ----------
    subcortex_data : pandas.DataFrame, optional
        DataFrame with columns ['region', 'value', 'Hemisphere'].
        If None, a default dataset is generated based on the selected hemisphere.

    atlas : str, default='aseg'
        The atlas used for the subcortical regions. Currently, two options are supported: 'aseg' and 'Tian_S1'.

    value_column : str, default='value'
        The name of the column in `subcortex_data` that contains the values to be visualized.

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
        
    if "Tian" in atlas:
        atlas = atlas.replace("Tian","Melbourne")

    # Use default of 'both' for SUIT cerebellar atlas
    if atlas == "SUIT" and hemisphere in ['L', 'R']:
        print("Individual-hemisphere visualization is not supported with the SUIT cerebellar atlas. Rendering both hemispheres together, along with the vermis.")
        hemisphere = 'both'
        
    # Load SVG
    svg_path = files("subcortex_visualization.data").joinpath(f"{atlas}_{hemisphere}.svg")
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
    # If atlas is SUIT, use a specific colormap
    if atlas == 'SUIT' and cmap is None: 
        hex_colors = [
            '#beff00', '#00ea43', '#0068ff', '#0054d4', '#df00ff', '#ff0000', '#df0000',
            '#ff9300', '#c86b00', '#00ff00', '#00d000', '#00ffff', '#00d0ce',
            '#3900ff', '#2e00d5', '#ff009d', '#df007c'
        ]

        # Create a ListedColormap
        cmap = mcolors.ListedColormap(hex_colors, name='custom_discrete')

    # Otherwise, use the provided colormap
    elif isinstance(cmap, str):
        cmap = matplotlib.colormaps.get_cmap(cmap)

    # Prepare data for plotting
    if subcortex_data is None: 
        atlas_ordering, color_lookup, cmap_colors = prep_data(atlas_ordering, value_column=value_column, subcortex_data=None, cmap=cmap)

    else: 
        atlas_ordering, norm, vmin, vmax, midpoint = prep_data(atlas_ordering, value_column=value_column, 
                                                               subcortex_data=subcortex_data, 
                                                               cmap=cmap, vmin=vmin, vmax=vmax, midpoint=midpoint)

    # Let's get plottin
    if subcortex_data is None:

        fig, ax = plot_helper(atlas_ordering, paths, value_column=value_column, hemisphere=hemisphere,
                              line_color=line_color, line_thickness=line_thickness,
                              color_lookup=color_lookup)
        
    else:

        fig, ax = plot_helper(atlas_ordering, paths, value_column=value_column, hemisphere=hemisphere,
                              line_color=line_color, line_thickness=line_thickness,
                              subcortex_data=subcortex_data, cmap=cmap, norm=norm)

    # Add a legend if requested
    if show_legend:

        # 8 columns if both hemispheres, else 4; only exception is for SUIT atlas, which always uses 4 columns
        ncols = 4 if atlas == 'SUIT' else np.where(hemisphere == 'both', 8, 4)

        # Call add_legend function to add the legend (discrete when subcortex_data is None) or colorbar (continuous when subcortex_data is not None)
        if subcortex_data is None:
            add_legend(ax=ax, fig=fig, value_column=value_column, atlas_ordering=atlas_ordering, 
                       cmap_colors=cmap_colors, fill_title=fill_title, ncols=ncols)
        else:
            add_legend(ax=ax, fig=fig, value_column=value_column, atlas_ordering=atlas_ordering, 
                       cmap=cmap, norm=norm, fill_title=fill_title)
    plt.rcParams.update({'font.size': fontsize})  # Change global font size
    plt.tight_layout()

    if show_figure:
        plt.show()
    else:
        return fig
