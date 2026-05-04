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

import re

def _parse_svg_dimension(value, fallback=500):
    """
    Parse an SVG dimension attribute that may include units (e.g., '500mm', '500px').

    Parameters
    ----------
    value : str or None
        The SVG dimension string to parse.

    fallback : float, default=500
        Value to return if ``value`` is None or cannot be parsed.

    Returns
    -------
    float
        The numeric portion of the dimension string, or ``fallback`` if parsing fails.
    """
    if value is None:
        return fallback
    match = re.match(r'([\d.]+)', str(value))
    return float(match.group(1)) if match else fallback

def _normalise_hemi(h):
    """
    Normalize a hemisphere code by mapping 'BL' or 'BR' to 'B'.

    Ensures SVG title key lookups succeed regardless of whether the atlas CSV
    uses sided ('BL'/'BR') or shared ('B') bilateral notation.

    Parameters
    ----------
    h : str
        Hemisphere code from the atlas ordering DataFrame
        (e.g., 'L', 'R', 'B', 'BL', 'BR').

    Returns
    -------
    str
        'B' if ``h`` is 'BL' or 'BR'; otherwise ``h`` unchanged.
    """
    if h in ('BL', 'BR'):
        return 'B'
    return h

def _get_region_color(color_lookup, row, cmap, subcortex_data=None, value_column='value', norm=None,
                      NA_fill="#cccccc", fill_by_significance=False,
                      nonsig_fill_alpha=0.5, fill_alpha=1.0, is_cerebellum=False,
                      line_thickness=1.5):
    """
    Determine the fill color and optional backing color for a single atlas region.

    Parameters
    ----------
    color_lookup : dict
        Mapping of region name to color, used when ``subcortex_data`` is None and
        ``is_cerebellum`` is False.

    row : pandas.Series
        One row from the atlas ordering DataFrame. Must contain at least 'region'
        and 'Hemisphere'; also 'p_value' when ``fill_by_significance`` is True.

    cmap : matplotlib.colors.Colormap
        Colormap applied to continuous values when ``subcortex_data`` is provided.

    subcortex_data : pandas.DataFrame, optional
        If provided, region colors are derived from ``value_column`` via ``cmap``
        and ``norm`` rather than from ``color_lookup``.

    value_column : str, default='value'
        Column in the atlas ordering (after merging with ``subcortex_data``) that
        holds the numeric value to map through the colormap.

    norm : matplotlib.colors.Normalize or matplotlib.colors.TwoSlopeNorm, optional
        Normalization applied before passing values to ``cmap``.

    NA_fill : str, default="#cccccc"
        Hex color used for regions whose value is NaN.

    fill_by_significance : bool, default=False
        If True, non-significant regions (p_value >= 0.05) are drawn at
        ``nonsig_fill_alpha`` over a white backing patch.

    nonsig_fill_alpha : float, default=0.5
        Alpha applied to non-significant regions when ``fill_by_significance``
        is True.

    fill_alpha : float, default=1.0
        Alpha applied to significant (or all) regions.

    is_cerebellum : bool, default=False
        If True and ``subcortex_data`` is None, colors are drawn from the
        hard-coded SUIT cerebellar lobule lookup instead of ``color_lookup``.

    line_thickness : float or str, default=1.5
        Thickness of the outline for each region (in points), or a column name
        in ``row`` whose value gives the region-specific thickness.

    Returns
    -------
    this_region_color : tuple
        RGBA color for the region patch.

    base_color : str or None
        White backing color used when ``fill_by_significance`` is True;
        None otherwise.

    this_line_thickness : float
        Thickness of the outline for the region, reduced if non-significant and
        ``fill_by_significance`` is True; otherwise equal to the resolved
        ``line_thickness`` value.
    """

    _SUIT_COLOR_LOOKUP = {
        ('IV',      'LR'):     '#beff00',
        ('V',       'LR'):     '#00ea43',
        ('VI',      'LR'):     '#0068ff',
        ('VI',      'vermis'): '#0054d4',
        ('Crus_I',  'LR'):     '#df00ff',
        ('Crus_II', 'LR'):     '#ff0000',
        ('Crus_II', 'vermis'): '#df0000',
        ('VIIb',    'LR'):     '#ff9300',
        ('VIIb',    'vermis'): '#c86b00',
        ('VIIIa',   'LR'):     '#00ff00',
        ('VIIIa',   'vermis'): '#00d000',
        ('VIIIb',   'LR'):     '#00ffff',
        ('VIIIb',   'vermis'): '#00d0ce',
        ('IX',      'LR'):     '#3900ff',
        ('IX',      'vermis'): '#2e00d5',
        ('X',       'LR'):     '#ff009d',
        ('X',       'vermis'): '#df007c',
    }
        
    # Determine colour
    if subcortex_data is None:
        if is_cerebellum:
            hemi_type = 'vermis' if row['Hemisphere'] == 'V' else 'LR'
            this_region_color = _SUIT_COLOR_LOOKUP.get((row['region'], hemi_type), NA_fill)
        else:
            this_region_color = color_lookup[row['region']]

    else:
        val = row[value_column]
        this_region_color = cmap(norm(val)) if not pd.isnull(val) else NA_fill

    # If fill_by_significance is True, adjust alpha based on p-value
    if fill_by_significance:
        this_region_pval = row['p_value'] if 'p_value' in row.index else np.nan
        this_fill_alpha = nonsig_fill_alpha if pd.notnull(this_region_pval) and this_region_pval >= 0.05 else fill_alpha
        base_color = 'white'
    else:
        this_fill_alpha = fill_alpha
        base_color = None

    # If line_thickness is a column name, get the value from the row; otherwise use the provided constant.
    if isinstance(line_thickness, str):
        this_line_thickness = row[line_thickness] if line_thickness in row.index else 1.5
    else:
        # If fill_by_significance is True, reduce line thickness for non-significant regions to visually de-emphasize them; otherwise use the provided constant.
        if fill_by_significance:
            this_line_thickness = 0.25*line_thickness if pd.notnull(this_region_pval) and this_region_pval >= 0.05 else line_thickness
        else:
            this_line_thickness = line_thickness

    # Adjust this_region_color to have the specified fill_alpha
    this_region_color = mcolors.to_rgba(this_region_color, alpha=this_fill_alpha)

    return this_region_color, base_color, this_line_thickness

def _add_legend(ax, fig, atlas_ordering, ncols=4, value_column='value', cmap_colors=None,
               fill_title=None, cmap='plasma', norm=None, multi_panel=False):
    """
    Add a legend or colorbar to the plot based on the provided data.

    Parameters
    ----------
    ax : matplotlib.axes.Axes or list of matplotlib.axes.Axes
        The axes object(s) to which the legend or colorbar will be added.
        Pass a list of axes (e.g. list(axes.flat)) when using multi_panel=True.

    fig : matplotlib.figure.Figure
        The figure object containing the plot.

    atlas_ordering : pandas.DataFrame
        DataFrame containing the atlas ordering information.

    ncols : int, default=4
        Number of columns in the discrete legend. Ignored when a continuous
        colorbar is rendered (i.e. when ``norm`` is not None).

    value_column : str, default='value'
        The name of the column in `atlas_ordering` that contains the values to be visualized.

    cmap_colors : list of str, optional
        List of colors corresponding to the regions in the atlas.

    fill_title : str, optional
        Title for the legend or colorbar.

    cmap : str or matplotlib.colors.Colormap, optional
        Colormap to use for the colorbar. Default is 'plasma'.

    norm : matplotlib.colors.Normalize or matplotlib.colors.TwoSlopeNorm, optional
        Normalization object for the colorbar. If None, a discrete legend is created.

    multi_panel : bool, default=False
        If True, uses figure-level legend/colorbar centred across all panels.
        If False, anchors legend to the single provided axis.

    Returns
    -------
    None (adds to the plot directly)
    """

    if fill_title is None:
        fill_title = "values"

    if norm is None:
        # Discrete legend
        unique_regions = atlas_ordering.sort_values(by='seg_index')[['region', value_column]].drop_duplicates()
        legend_elements = [
            Patch(facecolor=cmap_colors[row[value_column]], edgecolor='black', label=row['region'])
            for _, row in unique_regions.iterrows()
        ]

        shared_kwargs = dict(
            handles=legend_elements,
            loc='lower center',
            bbox_to_anchor=(0.5, 0.0),
            ncols=ncols,
            frameon=False,
            fontsize='large',
            handleheight=1.5,
            handlelength=1.5,
            title=fill_title,
            title_fontsize='large',
            handletextpad=0.5,
        )

        if multi_panel:
            fig.legend(**shared_kwargs)
            current = fig.subplotpars
            fig.subplots_adjust(bottom=0.25, wspace=current.wspace)
        else:
            ax.legend(**shared_kwargs)
            fig.subplots_adjust(bottom=0.5)

    else:
        # Continuous colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])

        if multi_panel:
            cbar = fig.colorbar(sm, ax=list(ax) if not isinstance(ax, list) else ax,
                                orientation='horizontal', fraction=0.03, pad=0.1, shrink=0.5)
        else:
            cbar = fig.colorbar(sm, ax=ax, orientation='horizontal', fraction=0.046, pad=0.1)

        cbar.set_label(fill_title)

def _prep_data(atlas_ordering, value_column='value', subcortex_data=None, cmap=None, vmin=None, vmax=None, midpoint=None):
    """ 
    Prepare data for plotting by merging with subcortex_data and normalizing values.

    Parameters
    ----------
    atlas_ordering : pandas.DataFrame
        DataFrame containing the atlas ordering information.

    value_column : str, default='value'
        The name of the column in `atlas_ordering` that contains the values to be visualized.

    subcortex_data : pandas.DataFrame, optional
        DataFrame with columns ['region', 'value', 'Hemisphere'].
        Might also include a 'p_value' column if `fill_by_significance` is True.
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
    When ``subcortex_data`` is None (discrete colormap):

    atlas_ordering : pandas.DataFrame
        Atlas ordering sorted by plot_order with an integer ``value_column``
        column assigning each region a discrete color index.

    color_lookup : dict
        Mapping of region name to RGBA color for use in discrete legend rendering.

    cmap_colors : numpy.ndarray
        Array of RGBA colors sampled evenly from ``cmap``, one per unique region.

    When ``subcortex_data`` is provided (continuous colormap):

    atlas_ordering : pandas.DataFrame
        Atlas ordering merged with ``subcortex_data`` on ['region', 'Hemisphere'].

    norm : matplotlib.colors.Normalize or matplotlib.colors.TwoSlopeNorm
        Normalization object mapping data values to [0, 1] for the colormap.

    vmin : float
        Effective minimum value used for normalization.

    vmax : float
        Effective maximum value used for normalization.

    midpoint : float or None
        Diverging midpoint passed through unchanged (None if not diverging).

    """

    if subcortex_data is None:
        # Sort by seg_index for color assignment
        atlas_ordering = atlas_ordering.sort_values(by='seg_index').reset_index(drop=True).dropna(subset=['region', 'Hemisphere'])

        # Assign discrete indices per region
        unique_regions = atlas_ordering['region'].unique()
        region_to_index = {region: idx for idx, region in enumerate(unique_regions)}
        atlas_ordering[value_column] = atlas_ordering['region'].map(region_to_index)
        
        # Discrete colormap
        num_regions = len(unique_regions)
        cmap_colors = cmap(np.linspace(0, 1, num_regions))
        color_lookup = {region: cmap_colors[i] for region, i in region_to_index.items()}

        # Re-sort by plot_order
        atlas_ordering = atlas_ordering.sort_values(by='plot_order').reset_index(drop=True)
        
        return atlas_ordering, color_lookup, cmap_colors
    
    else:
        # Expand 'B' rows to 'BL'/'BR' only for views where the ordering uses sided bilateral convention
        bilateral_mask = subcortex_data['Hemisphere'] == 'B'
        if bilateral_mask.any():
            bl = subcortex_data[bilateral_mask].copy(); bl['Hemisphere'] = 'BL'
            br = subcortex_data[bilateral_mask].copy(); br['Hemisphere'] = 'BR'
            subcortex_data = pd.concat(
                [subcortex_data[~bilateral_mask], bl, br, subcortex_data[bilateral_mask]],
                ignore_index=True
            )

        # If the atlas uses 'B' for midline regions but subcortex_data has 'BL'/'BR' for those
        # regions (e.g. user simulated data from the 'both' ordering), add 'B' copies so the
        # merge below can match them.
        atlas_b_regions = set(atlas_ordering.loc[atlas_ordering['Hemisphere'] == 'B', 'region'])
        if atlas_b_regions:
            existing_b_regions = set(subcortex_data.loc[subcortex_data['Hemisphere'] == 'B', 'region'])
            needs_b = atlas_b_regions - existing_b_regions
            if needs_b:
                bl_br_mask = subcortex_data['Hemisphere'].isin(['BL', 'BR']) & subcortex_data['region'].isin(needs_b)
                if bl_br_mask.any():
                    b_copies = subcortex_data[bl_br_mask].drop_duplicates(subset=['region']).copy()
                    b_copies['Hemisphere'] = 'B'
                    subcortex_data = pd.concat([subcortex_data, b_copies], ignore_index=True)

        # Merge and normalize
        atlas_ordering = atlas_ordering.merge(subcortex_data, on=['region', 'Hemisphere'], how='left')

        # Define the fill value column
        fill_values = atlas_ordering[value_column].values

        # Set min/max fill values for the colormap
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

def _plot_helper_cerebellum(atlas_ordering, paths, value_column='value', hemisphere='L', subcortex_data=None, 
                           color_lookup=None, cmap=None, NA_fill="#cccccc", fill_alpha=1.0, 
                           fill_by_significance=False, nonsig_fill_alpha=0.5,
                           line_color='black', line_thickness=1.5, norm=None, ax=None):
    """ 
    
    Helper function to plot the SVG paths with the specified colors and line properties.

    Parameters
    ----------
    atlas_ordering : pandas.DataFrame
        DataFrame containing the atlas ordering information.

    paths : list of xml.etree.ElementTree.Element
        List of SVG path elements to be plotted.

    value_column : str, default='value'
        The name of the column in `atlas_ordering` that contains the values to be visualized.

    hemisphere : {'L', 'R', 'both'}, default='L'
        Which hemisphere(s) to display. Use 'L' for left, 'R' for right, or 'both' for bilateral plots.

    subcortex_data : pandas.DataFrame, optional
        DataFrame with columns ['region', 'value', 'Hemisphere'].
        Might also include a 'p_value' column if `fill_by_significance` is True.
        If None, a default dataset is generated based on the selected hemisphere.

    color_lookup : dict, optional
        Dictionary mapping region names to colors for discrete colormap.

    cmap : str or matplotlib.colors.Colormap, optional
        Colormap to use for the colorbar. Default is 'plasma'.

    NA_fill : str, default="#cccccc"
        Color to use for regions with missing data.

    fill_alpha : float, default=1.0
        Opacity level for the filled regions, between 0 (transparent) and 1 (opaque).

    fill_by_significance : bool, default=False
        If True, adjusts fill opacity based on significance. Requires a 'p_value'
        column in the atlas ordering (merged from ``subcortex_data``).

    nonsig_fill_alpha : float, default=0.5
        Alpha applied to non-significant regions (p_value >= 0.05) when
        ``fill_by_significance`` is True.

    line_color : str, default='black'
        Color of the outline around each subcortical region.

    line_thickness : float or str, default=1.5
        Thickness of the outline for each region (in points), or a column name
        in ``atlas_ordering`` whose value gives region-specific thickness.

    norm : matplotlib.colors.Normalize or matplotlib.colors.TwoSlopeNorm, optional
        Normalization object for the colormap. If None, a discrete colormap is used.

    ax : matplotlib.axes.Axes, optional
        Axes object to plot on. If None, a new figure and axes are created.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The generated figure object.

    ax : matplotlib.axes.Axes
        The axes object containing the plot.

    """
    # Define patches
    patches = []

    # Create figure/axes only if none were provided
    if ax is None:
        if hemisphere == 'both': 
            fig, ax = plt.subplots(figsize=(17, 8))
        else:
            fig, ax = plt.subplots(figsize=(8, 8))
    else:
        fig = ax.figure

    # Ensure atlas_ordering is sorted by seg_index. There are no overlapping regions in the cerebellar lobule
    # flatmap, so we do not need to worry about plot_order.
    atlas_ordering = atlas_ordering.sort_values(by='seg_index')

    for _, row in atlas_ordering.iterrows():
        this_region = row['region']
        this_region_side = row['face']
        this_region_hemi = row['Hemisphere']

        # Determine color and alpha
        this_region_color, base_color, this_line_thickness = _get_region_color(subcortex_data=subcortex_data, color_lookup=color_lookup, 
                                                               row=row, value_column=value_column, cmap=cmap, 
                                                               norm=norm, NA_fill=NA_fill, fill_alpha=fill_alpha, 
                                                               fill_by_significance=fill_by_significance, 
                                                               nonsig_fill_alpha=nonsig_fill_alpha,
                                                               is_cerebellum=True, line_thickness=line_thickness)
            
        # Match title to region
        for path in paths:
            for child in path:
                if child.tag.endswith('title') and child.text == f"{this_region}_{this_region_side}_{this_region_hemi}":
                    d = path.attrib['d']
                    path_obj = parse_path(d)
                    patch = PathPatch(path_obj, facecolor=this_region_color,
                                      edgecolor=line_color, lw=this_line_thickness)
                    ax.add_patch(patch)
                    patches.append(patch)

    ax.autoscale_view()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.invert_yaxis()

    return fig, ax


def _plot_helper(atlas_ordering, atlas_data_path, value_column='value',
                          hemisphere='L', subcortex_data=None,
                          views=['medial', 'lateral'], color_lookup=None, 
                          cmap=None, NA_fill="#cccccc", fill_alpha=1.0,
                          fill_by_significance=False, nonsig_fill_alpha=0.5,
                          norm=None, line_color='black', line_thickness=1.5):
    """
    Hybrid plot helper for atlases like the Brainstem Navigator that have some midline (bilateral) regions.

    SVG naming conventions handled here:
      - medial / lateral views --> individual files: Brainstem_Navigator_{H}_{view}.svg
      - superior / inferior views (hemisphere='both') --> combined file: Brainstem_Navigator_both_{view}.svg
      - superior / inferior views (hemisphere='L'/'R') --> individual files: Brainstem_Navigator_{H}_{view}.svg

    Parameters
    ----------
    
    atlas_ordering : pandas.DataFrame
        DataFrame containing the atlas ordering information.

    atlas_data_path : pathlib.Path
        Path to the directory containing the SVG files for the atlas.

    value_column : str, default='value'
        The name of the column in `atlas_ordering` that contains the values to be visualized.

    hemisphere : {'L', 'R', 'both'}, default='L'
        Which hemisphere(s) to display. Use 'L' for left, 'R' for right, or 'both' for bilateral plots.

    subcortex_data : pandas.DataFrame, optional
        DataFrame with columns ['region', 'value', 'Hemisphere'].
        If None, a default dataset is generated based on the selected hemisphere.

    views : list of str, default=['medial', 'lateral']
        Which faces of the subcortical regions to display. Options include 'medial', 'lateral', 'superior', and 'inferior'.

    color_lookup : dict, optional
        Dictionary mapping region names to colors for discrete colormap.

    cmap : str or matplotlib.colors.Colormap, optional
        Colormap to use for the colorbar. Default is 'viridis'.

    NA_fill : str, default="#cccccc"
        Color to use for regions with missing data (NaN values).

    fill_alpha : float, default=1.0
        Opacity level for the filled regions, between 0 (transparent) and 1 (opaque).

    fill_by_significance : bool, default=False
        If True, adjusts fill_alpha based on significance (e.g., p-values) in the data. Requires a 'p_value' column in `subcortex_data`.

    nonsig_fill_alpha : float, default=0.5
        If `fill_by_significance` is True, this alpha level is applied to non-significant regions (e.g., p >= 0.05).

    norm : matplotlib.colors.Normalize or matplotlib.colors.TwoSlopeNorm, optional
        Normalization object for the colorbar. If None, a discrete legend is created.

    line_color : str, default='black'
        Color of the outline around each subcortical region.

    line_thickness : float or str, default=1.5
        Thickness of the outline for each region (in points), or a column name
        in ``atlas_ordering`` whose value gives region-specific thickness.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The generated figure containing all panels.

    axes : numpy.ndarray of matplotlib.axes.Axes
        2-D array of axes (shape [num_rows, num_cols]). Unused panels are hidden.
    """

    # ------------------------------------------------------------------
    # 1. Build the ordered panel list
    # ------------------------------------------------------------------
    LATERAL_MEDIAL_VIEWS = ['medial', 'lateral']
    SUP_INF_VIEWS        = ['superior', 'inferior']

    if hemisphere == 'both':
        # medial/lateral → four individual panels (L_med, L_lat, R_lat, R_med)
        lm_panels = [('L', 'medial'), ('L', 'lateral'), ('R', 'lateral'), ('R', 'medial')]
        lm_panels = [(h, v) for h, v in lm_panels if v in views]

        # superior/inferior → one "both" SVG per view, rendered as a single panel
        si_panels = [('both', v) for v in SUP_INF_VIEWS if v in views]

    else:  # 'L' or 'R'
        # Enforce (medial, lateral) order for L and (lateral, medial) order for R
        # so single-hemisphere plots always follow the same outward→inward convention
        # as the bilateral layout: [L_medial, L_lateral, R_lateral, R_medial]
        ORDERED_LM = [('L', 'medial'), ('L', 'lateral'), ('R', 'lateral'), ('R', 'medial')]
        lm_panels = [(h, v) for h, v in ORDERED_LM if h == hemisphere and v in views]
        si_panels = [(hemisphere, v) for v in SUP_INF_VIEWS if v in views]

    all_panels = lm_panels + si_panels          # top-row first, then bottom-row
    n_lm = len(lm_panels)
    n_si = len(si_panels)

    # ------------------------------------------------------------------
    # 2. Figure / axes layout
    # ------------------------------------------------------------------
    has_lm = n_lm > 0
    has_si = n_si > 0

    if has_lm and has_si:
        num_rows = 2
        num_cols = max(n_lm, n_si)
    else:
        num_rows = 1
        num_cols = max(n_lm, n_si)

    fig, axes = plt.subplots(num_rows, num_cols,
                             figsize=(8 * num_cols, 8 * num_rows),
                             squeeze=False)

    # Hide all axes by default; we'll turn on the ones we use
    for ax in axes.flat:
        ax.set_visible(False)

    # ------------------------------------------------------------------
    # 3. Helper: draw one SVG file onto one axes
    # ------------------------------------------------------------------
    def _draw_svg_on_ax(ax, svg_path_str, df_panel):
        """Parse svg_path_str and paint each region in df_panel onto ax."""
        try:
            tree = ET.parse(svg_path_str)
        except Exception as e:
            print(f"  Could not load {svg_path_str}: {e}")
            return

        root = tree.getroot()
        ns_uri = 'http://www.w3.org/2000/svg'
        ns     = {'svg': ns_uri}
        ET.register_namespace('', ns_uri)

        canvas_w = _parse_svg_dimension(root.get('width'),  fallback=500)
        canvas_h = _parse_svg_dimension(root.get('height'), fallback=500)

        ax.set_visible(True)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_xlim(0, canvas_w)
        ax.set_ylim(canvas_h, 0)   # SVG y-axis is top-down

        all_x, all_y = [], []

        # Index df_panel by the title key used in the SVG
        # Title format in SVG: {region}_{face}_{Hemisphere}
        title_to_row = {}
        for _, row in df_panel.iterrows():
            hemi_key = _normalise_hemi(row['Hemisphere'])
            key = f"{row['region']}_{row['face']}_{hemi_key}"
            title_to_row[key] = row

        paths = root.findall('.//svg:path', ns)

        for path_el in paths:
            # Find the <title> child of this <path>
            title_el = path_el.find('svg:title', ns)
            if title_el is None:
                # try without namespace
                title_el = path_el.find('title')
            title_text = title_el.text if title_el is not None else None

            row = title_to_row.get(title_text)
            if row is None:
                # Region not in our ordering — skip silently
                continue

            d = path_el.get('d', '')
            if not d:
                continue

            # Determine color and alpha
            this_region_color, base_color, this_line_thickness = _get_region_color(subcortex_data=subcortex_data, color_lookup=color_lookup, 
                                                                row=row, value_column=value_column, cmap=cmap, 
                                                                norm=norm, NA_fill=NA_fill, fill_alpha=fill_alpha, 
                                                                fill_by_significance=fill_by_significance, 
                                                                nonsig_fill_alpha=nonsig_fill_alpha,
                                                                line_thickness=line_thickness)


            try:
                mpl_path = parse_path(d)
                verts = mpl_path.vertices
                all_x.extend(verts[:, 0])
                all_y.extend(verts[:, 1])

                # Draw white backing first if needed
                if base_color is not None:
                    base_patch = PathPatch(mpl_path,        # or mpl_path depending on the helper
                                        facecolor=base_color,
                                        edgecolor='none',  # no outline on the backing
                                        linewidth=0,
                                        zorder=int(row['plot_order']) - 0.5)  # just below the colour patch
                    ax.add_patch(base_patch)
                    
                patch = PathPatch(mpl_path,
                                  facecolor=this_region_color,
                                  edgecolor=line_color,
                                  linewidth=this_line_thickness,
                                  zorder=int(row['plot_order']))
                ax.add_patch(patch)
            except Exception as e:
                print(f"  Could not parse path (title={title_text}): {e}")

        # Tight autoscale based on actual vertices
        if all_x and all_y:
            pad = 5
            ax.set_xlim(min(all_x) - pad, max(all_x) + pad)
            ax.set_ylim(max(all_y) + pad, min(all_y) - pad)

    # ------------------------------------------------------------------
    # 4. Render each panel
    # ------------------------------------------------------------------
    def _svg_filename(h, view):
        """Return the full path to the SVG for a given hemisphere/view combination."""
        return str(atlas_data_path / f"Brainstem_Navigator_{h}_{view}.svg")

    for col_idx, (panel_hemi, view) in enumerate(lm_panels):
        ax = axes[0, col_idx]

        # Filter atlas_ordering to this hemisphere + view
        hemi_filter = (
            (atlas_ordering['Hemisphere'] == panel_hemi) |
            (atlas_ordering['Hemisphere'] == f'B{panel_hemi}') |
            (atlas_ordering['Hemisphere'] == 'B')  # include bilateral regions in both hemispheres
        )
        df_panel = (atlas_ordering
                    .loc[hemi_filter & (atlas_ordering['face'] == view)]
                    .sort_values('plot_order')
                    .reset_index(drop=True))

        svg_file = _svg_filename(panel_hemi, view)
        _draw_svg_on_ax(ax, svg_file, df_panel)

    row_idx = 1 if has_lm else 0
    for col_idx, (panel_hemi, view) in enumerate(si_panels):
        ax = axes[row_idx, col_idx]

        if hemisphere == 'both':
            # Use the combined "both" SVG; keep all rows (both hemispheres)
            df_panel = (atlas_ordering
                        .loc[atlas_ordering['face'] == view]
                        .sort_values('plot_order')
                        .reset_index(drop=True))
            svg_file = _svg_filename('both', view)
        else:
            hemi_filter = (
                (atlas_ordering['Hemisphere'] == panel_hemi) |
                (atlas_ordering['Hemisphere'] == f'B{panel_hemi}') |
                (atlas_ordering['Hemisphere'] == 'B')
            )
            df_panel = (atlas_ordering
                        .loc[hemi_filter & (atlas_ordering['face'] == view)]
                        .sort_values('plot_order')
                        .reset_index(drop=True))
            svg_file = _svg_filename(panel_hemi, view)

        _draw_svg_on_ax(ax, svg_file, df_panel)

    plt.tight_layout(pad=0)
    return fig, axes

def _plot_helper_individual(atlas_ordering, svg_dir, value_column='value', 
                           hemisphere='L', subcortex_data=None, 
                           views=['medial', 'lateral'], figsize=(8, 8),
                           color_lookup=None, cmap=None, NA_fill="#cccccc", fill_alpha=1.0,
                           fill_by_significance=False, nonsig_fill_alpha=0.5,
                           norm=None, line_color='black', line_thickness=1.5):
    
    """
    Plot helper for atlases where each region is saved as its own SVG file.

    SVG naming convention: {region}_{Hemisphere}_{face}.svg

    Parameters
    ----------
    atlas_ordering : pandas.DataFrame
        DataFrame containing the atlas ordering information.

    svg_dir : str or pathlib.Path
        Directory containing the SVG files for each region.

    value_column : str, default='value'
        The name of the column in `atlas_ordering` that contains the values to be visualized.

    hemisphere : {'L', 'R', 'both'}, default='L'
        Which hemisphere(s) to display. Use 'L' for left, 'R' for right, or 'both' for bilateral plots.

    subcortex_data : pandas.DataFrame, optional
        DataFrame with columns ['region', 'value', 'Hemisphere'].

    views : list of str, default=['medial', 'lateral']
        Which faces of the subcortical regions to display. Options include 'medial', 'lateral', 'superior', and 'inferior'.

    figsize : tuple of (float, float), default=(8, 8)
        Size of each individual panel in inches (width, height).

    color_lookup : dict, optional
        Dictionary mapping region names to colors for discrete colormap.

    cmap : str or matplotlib.colors.Colormap, optional
        Colormap to use for the colorbar. Default is 'viridis'.

    NA_fill : str, default="#cccccc"
        Color to use for regions with missing data (NaN values).

    fill_alpha : float, default=1.0
        Opacity level for the filled regions, between 0 (transparent) and 1 (opaque).

    fill_by_significance : bool, default=False
        If True, adjusts fill_alpha based on significance (e.g., p-values) in the data. Requires a 'p_value' column in `subcortex_data`.

    nonsig_fill_alpha : float, default=0.5
        If `fill_by_significance` is True, this alpha level is applied to non-significant regions (e.g., p >= 0.05).

    norm : matplotlib.colors.Normalize or matplotlib.colors.TwoSlopeNorm, optional
        Normalization object for the colorbar. If None, a discrete legend is created.

    line_color : str, default='black'
        Color of the outline around each subcortical region.

    line_thickness : float or str, default=1.5
        Thickness of the outline for each region (in points), or a column name
        in ``atlas_ordering`` whose value gives region-specific thickness.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The generated figure object.

    axes : numpy.ndarray of matplotlib.axes.Axes
        2-D array of axes (shape [num_rows, num_cols]). Unused panels are hidden.
    """

    # Specify outward--inward view order for single-hemisphere
    SINGLE_VIEW_ORDER = {
        'L': ['medial', 'lateral', 'superior', 'inferior'],
        'R': ['lateral', 'medial', 'superior', 'inferior'],
    }

    BOTH_VIEW_ORDER = [
        ('L', 'medial'),
        ('L', 'lateral'),
        ('R', 'lateral'),
        ('R', 'medial'),
        ('L', 'superior'),
        ('R', 'superior'),
        # The next two are switched to look more intuitive
        ('R', 'inferior'),
        ('L', 'inferior'),
    ]

    if hemisphere == 'both':
        panels = [(h, v) for h, v in BOTH_VIEW_ORDER if v in views]
    else:
        panels = [(hemisphere, v) for v in SINGLE_VIEW_ORDER[hemisphere] if v in views]

    n_panels = len(panels)

    # ---------------------------------------------------------------------------
    # Determine grid layout
    # ---------------------------------------------------------------------------
    has_lateral_medial = any(v in views for v in ['medial', 'lateral'])
    has_superior_inferior = any(v in views for v in ['superior', 'inferior'])

    if hemisphere == 'both' and has_lateral_medial and has_superior_inferior:
        # Top row: medial/lateral pairs; bottom row: superior/inferior pairs
        num_rows = 2
        num_cols = max(
            sum(1 for h, v in panels if v in ['medial', 'lateral']),
            sum(1 for h, v in panels if v in ['superior', 'inferior'])
        )
    else:
        num_rows = 1
        num_cols = n_panels

    fig_w = figsize[0] * num_cols
    fig_h = figsize[1] * num_rows
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(fig_w, fig_h),
                             squeeze=False)  # always return 2D array

    # Assign panels to grid positions
    if num_rows == 2:
        top_panels    = [(h, v) for h, v in panels if v in ['medial', 'lateral']]
        bottom_panels = [(h, v) for h, v in panels if v in ['superior', 'inferior']]
        panel_axes = (
            [(axes[0, c], p) for c, p in enumerate(top_panels)] +
            [(axes[1, c], p) for c, p in enumerate(bottom_panels)]
        )
        # Hide any unused axes in the bottom row
        for c in range(len(bottom_panels), num_cols):
            axes[1, c].set_visible(False)
    else:
        panel_axes = [(axes[0, c], panels[c]) for c in range(n_panels)]

    # ---------------------------------------------------------------------------
    # Draw each panel
    # ---------------------------------------------------------------------------
    for ax, (panel_hemi, view) in panel_axes:
        ax.set_aspect('equal')
        ax.axis('off')

        if hemisphere == 'both':
            df_view = (
                atlas_ordering
                .loc[
                    (atlas_ordering['face'] == view) &
                    (
                        (atlas_ordering['Hemisphere'] == panel_hemi) |
                        (atlas_ordering['Hemisphere'] == f'B{panel_hemi}')
                    )
                ]
                .sort_values('plot_order')
                .reset_index(drop=True)
            )
            if df_view.empty:
                print(f"No regions found for view={view}, hemisphere={panel_hemi}")
                continue
        else:
            df_view = (
                atlas_ordering
                .loc[
                    (atlas_ordering['face'] == view) &
                    (
                        (atlas_ordering['Hemisphere'] == hemisphere) |
                        (atlas_ordering['Hemisphere'] == f'B{hemisphere}')
                    )
                ]
                .sort_values('plot_order')
                .reset_index(drop=True)
            )

            if df_view.empty:
                print(f"No regions found for view={view}, hemisphere={panel_hemi}")
                continue

        ax_canvas_w, ax_canvas_h = None, None
        all_x, all_y = [], []

        for _, row in df_view.iterrows():
            this_region = row['region']
            hemi = row['Hemisphere']

            if hemi in ['BL', 'BR']:
                svg_filename = f"{svg_dir}/{this_region}_{view}.svg"
            else:
                svg_filename = f"{svg_dir}/{this_region}_{hemi}_{view}.svg"

            # Determine color and alpha
            this_region_color, base_color, this_line_thickness = _get_region_color(subcortex_data=subcortex_data, color_lookup=color_lookup, 
                                                                row=row, value_column=value_column, cmap=cmap, 
                                                                norm=norm, NA_fill=NA_fill, fill_alpha=fill_alpha, 
                                                                fill_by_significance=fill_by_significance, 
                                                                nonsig_fill_alpha=nonsig_fill_alpha,
                                                                line_thickness=line_thickness)

            try:
                tree = ET.parse(svg_filename)
            except Exception as e:
                print(f"  Skipping {svg_filename}: {e}")
                continue

            root = tree.getroot()
            ns = 'http://www.w3.org/2000/svg'

            if ax_canvas_w is None:
                ax_canvas_w = float(root.get('width', 500))
                ax_canvas_h = float(root.get('height', 500))
                ax.set_xlim(0, ax_canvas_w)
                ax.set_ylim(ax_canvas_h, 0)

            for path_el in root.findall(f'.//{{{ns}}}path'):
                d = path_el.get('d', '')
                if not d:
                    continue
                try:
                    mpl_path = parse_path(d)
                    verts = mpl_path.vertices
                    if len(verts) > 0:
                        all_x.extend(verts[:, 0])
                        all_y.extend(verts[:, 1])

                    # Draw white backing first if needed
                    if base_color is not None:
                        base_patch = PathPatch(mpl_path,        # or mpl_path depending on the helper
                                            facecolor=base_color,
                                            edgecolor='none',  # no outline on the backing
                                            linewidth=0,
                                            zorder=int(row['plot_order']) - 0.5)  # just below the colour patch
                        ax.add_patch(base_patch)

                    patch = PathPatch(
                        mpl_path,
                        facecolor=this_region_color,
                        edgecolor=line_color,
                        linewidth=this_line_thickness,
                        zorder=row['plot_order'],
                    )
                    ax.add_patch(patch)
                except Exception as e:
                    print(f"  Could not parse path in {svg_filename}: {e}")
                    continue

        if all_x and all_y:
            pad = 5
            ax.set_xlim(min(all_x) - pad, max(all_x) + pad)
            ax.set_ylim(max(all_y) + pad, min(all_y) - pad)

    plt.tight_layout(pad=0)
    fig.subplots_adjust(wspace=0.05)  # small but non-negative horizontal gap
    return fig, axes

def plot_subcortical_data(subcortex_data=None, atlas='aseg_subcortex', value_column='value', hemisphere='L',  
                          views=['medial', 'lateral'], line_thickness=1.5, line_color='black',
                          fill_title="values", cmap=None, NA_fill="#cccccc", fill_alpha=1.0,
                          fill_by_significance=False, nonsig_fill_alpha=0.5,   
                          vmin=None, vmax=None, midpoint=None, show_legend=True,
                          show_figure=True, fontsize=12, ax=None):
    
    """
    Visualize a given subcortical or cerebellar atlas template as a vector graphic, colored according to user-provided data values or, by default, a simple region-based color scheme. 

    Parameters
    ----------
    subcortex_data : pandas.DataFrame, optional
        DataFrame with columns ['region', 'value', 'Hemisphere'].
        If None, regions will be simply colored based on their assigned index in the corresponding atlas (which is arbitrary).

    atlas : str, default='aseg_subcortex'
        The atlas used for the subcortical regions. The default is 'aseg_subcortex'.

    value_column : str, default='value'
        The name of the column in `subcortex_data` that contains the values to be visualized.

    hemisphere : {'L', 'R', 'both'}, default='L'
        Which hemisphere(s) to display. Use 'L' for left, 'R' for right, or 'both' for bilateral plots.

    views : list of str, default=['medial', 'lateral']
        Which faces of the subcortical regions to display. Options include 'medial', 'lateral', 'superior', and 'inferior'. 
        Not applicable to the SUIT cerebellar lobule atlas.

    line_thickness : float or str, default=1.5
        Thickness of the outline for each region, or a column name in ``subcortex_data`` whose value gives region-specific thickness.

    line_color : str, default='black'
        Color of the outline around each subcortical region.

    fill_title : str, default="values"
        Label for the colorbar indicating the meaning of the fill values.

    cmap : str or matplotlib.colors.Colormap, default='viridis'
        Colormap used to fill in the regions. Accepts a string name or a Colormap object.

    NA_fill : str, default="#cccccc"
        Color to use for regions with missing data (NaN values).

    fill_alpha : float, default=1.0
        Opacity level for the filled regions, between 0 (transparent) and 1 (opaque).

    fill_by_significance : bool, default=False
        If True, adjusts fill_alpha based on significance (e.g., p-values) in the data. Requires a 'p_value' column in `subcortex_data`.

    nonsig_fill_alpha : float, default=0.5
        If `fill_by_significance` is True, this alpha level is applied to non-significant regions (e.g., p >= 0.05).

    vmin : float, optional
        Minimum value for colormap normalization. 
        If None, the minimum of the input values is used.

    vmax : float, optional
        Maximum value for colormap normalization. 
        If None, the maximum of the input values is used.

    midpoint : float, optional
        If provided, uses a diverging colormap centered around this value.

    show_legend : bool, default=True
        If True, displays a legend or colorbar indicating the mapping of values to colors.

    show_figure : bool, default=True
        If True, displays the figure using `plt.show()`. If False, returns the matplotlib Figure object.

    fontsize : int, default=12
        Font size for the figure text elements.

    ax : matplotlib.axes.Axes, optional
        Axes object to plot on. If None, a new figure and axes are created.

    Returns
    -------
    matplotlib.figure.Figure or None
        The generated figure, if `show_figure` is False. Otherwise, displays the plot and returns None.

    Notes
    -----
    - The function loads SVG files and a lookup CSV bundled with the package, which can be found under `data/` directory.
    - The input `subcortex_data` should align with regions defined in the lookup table.
    """
        
    # Aliases and backward compatibility
    if "Tian" in atlas:
        atlas = atlas.replace("Tian","Melbourne")

    # Use default of 'both' for SUIT cerebellar atlas
    # Handle colormap
    # If atlas is SUIT, use a specific colormap
    if atlas == 'SUIT_cerebellar_lobule':
        if hemisphere in ['L', 'R']:
            print("Individual-hemisphere visualization is not supported with the SUIT cerebellar lobule atlas. Rendering both hemispheres together, along with the vermis.")
            hemisphere = 'both'

    if cmap is None:
        cmap = 'viridis'  # default colormap

    # Otherwise, use the provided colormap
    if isinstance(cmap, str):
        cmap = matplotlib.colormaps.get_cmap(cmap)

    # If fill_by_significance is True, ensure that 'p_value' column is present in subcortex_data
    if fill_by_significance:
        if subcortex_data is None or 'p_value' not in subcortex_data.columns:
            raise ValueError("fill_by_significance=True requires a 'p_value' column in subcortex_data.")

    try:
        # Load ordering file
        atlas_ordering = pd.read_csv(files("subcortex_visualization").joinpath('data').joinpath(f"{atlas}/{atlas}_{hemisphere}_ordering.csv"))
    
    except Exception as e:
        try:
            # try appending '_subcortex' if not already present
            atlas = atlas + '_subcortex' 
            atlas_ordering = pd.read_csv(files("subcortex_visualization").joinpath('data').joinpath(f"{atlas}/{atlas}_{hemisphere}_ordering.csv"))
            print(f"Atlas name found with '_subcortex' suffix. Using atlas='{atlas}'.")

        except Exception as e:
            raise FileNotFoundError(f"Could not find atlas '{atlas}'. Please ensure the atlas name is correct and the corresponding data is included in the package.") from e
        

    # Define atlas data path
    atlas_data_path = files('subcortex_visualization').joinpath('data').joinpath(atlas)

    # Prepare data for plotting
    if subcortex_data is None: 
        atlas_ordering, color_lookup, cmap_colors = _prep_data(atlas_ordering, value_column=value_column, subcortex_data=None, cmap=cmap)
        norm=None

    else: 
        color_lookup=None
        atlas_ordering, norm, vmin, vmax, midpoint = _prep_data(atlas_ordering, value_column=value_column, 
                                                               subcortex_data=subcortex_data, 
                                                               cmap=cmap, vmin=vmin, vmax=vmax, midpoint=midpoint)
        
        
    # Generate plot

    # Case 1: Brainstem_Navigator atlas, where all regions are included in the same SVG for each hemisphere/view
    if atlas == 'Brainstem_Navigator':
        fig, axes = _plot_helper(
            atlas_ordering, 
            atlas_data_path,
            value_column=value_column,
            hemisphere=hemisphere,
            subcortex_data=subcortex_data,
            views=views,
            color_lookup=color_lookup,
            cmap=cmap,
            NA_fill=NA_fill,
            norm=norm,
            fill_alpha=fill_alpha,
            fill_by_significance=fill_by_significance,
            nonsig_fill_alpha=nonsig_fill_alpha,
            line_color=line_color,
            line_thickness=line_thickness,
        )
        flat_axes   = [ax for ax in axes.flat if ax.get_visible()]
        legend_ax   = flat_axes[0]
        is_multi_panel = True

    # Case 2: SUIT cerebellar lobule
    elif atlas=='SUIT_cerebellar_lobule':
        svg_path = files("subcortex_visualization").joinpath(
            f"data/{atlas}/{atlas}_{hemisphere}.svg")
        tree = ET.parse(svg_path)
        root = tree.getroot()
        ns   = {'svg': 'http://www.w3.org/2000/svg'}
        ET.register_namespace('', ns['svg'])
        paths = root.findall('.//svg:path', ns)

        if subcortex_data is None:
            fig, ax = _plot_helper_cerebellum(atlas_ordering, paths=paths,
                                    value_column=value_column,
                                    hemisphere=hemisphere,
                                    cmap=cmap,
                                    color_lookup=color_lookup,
                                    NA_fill=NA_fill, 
                                    fill_alpha=fill_alpha,
                                    fill_by_significance=fill_by_significance,
                                    line_color=line_color,
                                    line_thickness=line_thickness,
                                    ax=ax)
        else:
            fig, ax = _plot_helper_cerebellum(atlas_ordering, paths=paths,
                                    value_column=value_column,
                                    hemisphere=hemisphere,
                                    subcortex_data=subcortex_data,
                                    cmap=cmap, 
                                    NA_fill=NA_fill,
                                    norm=norm, 
                                    fill_alpha=fill_alpha,
                                    fill_by_significance=fill_by_significance,
                                    line_color=line_color,
                                    line_thickness=line_thickness,
                                    ax=ax)

        legend_ax      = ax
        flat_axes      = [ax]
        is_multi_panel = False
        
    # For all other atlases
    else:
        svg_dir=f'{atlas_data_path}/vectors/'
        
        fig, axes = _plot_helper_individual(atlas_ordering, svg_dir, value_column=value_column, 
            hemisphere=hemisphere, subcortex_data=subcortex_data, 
            views=views, figsize=(8, 8), line_color=line_color, line_thickness=line_thickness,
            color_lookup=color_lookup, cmap=cmap, NA_fill=NA_fill, 
            fill_alpha=fill_alpha, fill_by_significance=fill_by_significance,
            nonsig_fill_alpha=nonsig_fill_alpha,norm=norm)
        
        # Pick a legend anchor ax
        flat_axes = [ax for ax in axes.flat if ax.get_visible()]
        legend_ax = flat_axes[0]  # or flat_axes[0]
        is_multi_panel = True

    plt.rcParams.update({'font.size': fontsize})
    plt.tight_layout(h_pad=1.5)

    # Add a legend if requested — must come AFTER tight_layout so the
    # colorbar / subplots_adjust reservation is not overwritten.
    if show_legend:

        # 8 columns if both hemispheres, else 4; only exception is for SUIT atlas, which always uses 4 columns
        ncols = 4 if atlas == 'SUIT_cerebellar_lobule' else np.where(hemisphere == 'both', 8, 4)

        # Discrete legend when no data provided, colorbar otherwise
        if subcortex_data is None:
            _add_legend(ax=flat_axes if is_multi_panel else legend_ax,
                       multi_panel=is_multi_panel,
                       fig=fig, value_column=value_column, atlas_ordering=atlas_ordering,
                       cmap_colors=cmap_colors, fill_title=fill_title, ncols=ncols)
        else:
            _add_legend(ax=flat_axes if is_multi_panel else legend_ax,
                       multi_panel=is_multi_panel,
                       fig=fig, value_column=value_column, atlas_ordering=atlas_ordering,
                       cmap=cmap, norm=norm, fill_title=fill_title)

    if show_figure:
        plt.show()
    else:
        return fig
