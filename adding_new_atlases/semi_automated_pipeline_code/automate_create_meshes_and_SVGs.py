import os
import yabplot as yab
import pyvista as pv
from matplotlib.pyplot import get_cmap

# Set before ANY pyvista plotter is created - must be module-level for script execution
pv.OFF_SCREEN = True

# YABplot functions
from yabplot import get_atlas_regions
from yabplot.plotting import get_base_name, plot_subcortical
from yabplot.scene import (
    get_view_configs, get_shading_preset,
    add_context_to_view, set_camera,
)
from yabplot.mesh import load_bmesh
from yabplot.data import _find_subcortical_files
from yabplot.utils import generate_distinct_colors


# PNG tracing to SVG
import numpy as np
from PIL import Image
from potrace import Bitmap, POTRACE_TURNPOLICY_MINORITY
from lxml import etree

# Composite SVG creation
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path
import svgpath2mpl  # pip install svgpath2mpl

# Argument parsing
import argparse

argparse = argparse.ArgumentParser(description="Create meshes and SVGs for subcortical atlas visualization.")
argparse.add_argument('--atlas_name', type=str, default='Melbourne_S1', help='Name of the atlas (used for output naming)')
argparse.add_argument('--atlas_nii', type=str, default='Tian_Subcortex_S1_3T_1mm.nii.gz', help='Path to atlas NIfTI file')
argparse.add_argument('--atlas_lookup_txt', type=str, default='Melbourne_S1_lookup.txt', help='Path to atlas lookup text file')
argparse.add_argument('--atlas_output_data_path', type=str, default='Melbourne_S1', help='Directory to save intermediate data files')
argparse.add_argument('--cmap', type=str, default='tab20', help='Matplotlib colormap name for coloring regions (e.g. "tab20", "plasma")')
argparse.add_argument('--zoom', type=float, default=2.5, help='Zoom level for rendering meshes')
argparse.add_argument('--smooth_i', type=int, default=20, help='Number of iterations for mesh smoothing')
argparse.add_argument('--smooth_f', type=float, default=0.7, help='Smoothing factor for mesh smoothing (0-1)')
argparse.add_argument('--exclude_list', nargs='*', default=[], help='List of region names to exclude when creating meshes (e.g. "VPL", "VPM")')
argparse.add_argument('--overwrite_meshes', action='store_true', help='Whether to overwrite existing mesh files if they already exist')
argparse.add_argument('--shuffle_colors', action='store_true', help='Whether to shuffle colors assigned to regions (for better distinction if adjacent regions have similar colors in the colormap)')
args = argparse.parse_args()

atlas_name = args.atlas_name
atlas_nii = args.atlas_nii
atlas_lookup_txt = args.atlas_lookup_txt
atlas_output_data_path = args.atlas_output_data_path
cmap = args.cmap
smooth_i = args.smooth_i
smooth_f = args.smooth_f
zoom = args.zoom
exclude_list = args.exclude_list
overwrite_meshes = args.overwrite_meshes
shuffle_colors = args.shuffle_colors

###########################################################
# Helper functions: creating mesh
###########################################################

def create_mesh_for_atlas(atlas_nii_file, atlas_lookup_file, atlas_mesh_output_path, smooth_i=20, smooth_f=0.7, overwrite_meshes=False):

    atlas_labels = {}

    with open(atlas_lookup_file, 'r') as f_in:
        for line in f_in:
            parts = line.strip().split()
            if len(parts) >= 2:
                try:
                    rid = int(parts[0])
                    name = parts[1].replace(' ', '_').replace('/', '-')

                    # If name ends in -lh change to end with _L, if it ends in -rh change to end with _R
                    if name.endswith('-lh'):
                        name = name[:-3] + '_L'
                    elif name.endswith('-rh'):
                        name = name[:-3] + '_R'

                    atlas_labels[rid] = name
                except ValueError:
                    continue

    print(f"successfully parsed {len(atlas_labels)} total regions from text file.")
    print(atlas_labels)

    if overwrite_meshes:
        # Remove all files in atlas_mesh_output_path
        for f in os.listdir(atlas_mesh_output_path):
            fpath = os.path.join(atlas_mesh_output_path, f)
            if os.path.isfile(fpath):
                os.remove(fpath)

    print("--- building atlas 1: full subcortical (using include_list) ---")
    yab.build_subcortical_atlas(
        nii_path=atlas_nii_file,
        labels_dict=atlas_labels,
        out_dir=atlas_mesh_output_path,
        smooth_i=smooth_i, smooth_f=smooth_f,
        exclude_list=exclude_list
    )

###########################################################
# Helper functions: visualizing mesh and exporting SVG
###########################################################

def rgb2hex(rgb_tuple):
    r, g, b = rgb_tuple[:3]  # safely ignore alpha if present
    if isinstance(r, float):
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
    return "#{:02x}{:02x}{:02x}".format(r, g, b)

def _is_canvas_rect(curve, w, h, tolerance=0.05):
    """Returns True if this curve is approximately the full canvas bounding box."""
    xs = [curve.start_point.x]
    ys = [curve.start_point.y]
    for seg in curve.segments:
        xs.append(seg.end_point.x)
        ys.append(seg.end_point.y)
    x_span = max(xs) - min(xs)
    y_span = max(ys) - min(ys)
    return x_span > w * (1 - tolerance) and y_span > h * (1 - tolerance)


def png_to_traced_outline(
    input_png,
    output_svg,
    turdsize=4,
    alphamax=1.0,
    opttolerance=0.2,
    fill_color='none',
    stroke_color='black',
    stroke_width=0.5,
    alpha_threshold=128,
    canvas_tolerance=0.05,
):
    # Step 1: Load PNG and extract alpha channel as binary mask
    img = Image.open(input_png).convert('RGBA')
    alpha = np.array(img)[:, :, 3]
    binary = alpha > alpha_threshold

    # Step 2: Potrace trace
    bm = Bitmap(binary)
    plist = bm.trace(
        turdsize=turdsize,
        turnpolicy=POTRACE_TURNPOLICY_MINORITY,
        alphamax=alphamax,
        opticurve=True,
        opttolerance=opttolerance,
    )

    # Step 3: Build outline SVG, skipping canvas-sized background rectangle
    w, h = img.size
    svg_root = etree.Element('svg', {
        'version': '1.1',
        'xmlns': 'http://www.w3.org/2000/svg',
        'width': str(w),
        'height': str(h),
        'viewBox': f'0 0 {w} {h}',
    })

    for curve in plist:
        if _is_canvas_rect(curve, w, h, tolerance=canvas_tolerance):
            continue  # skip Potrace's background bounding rectangle

        parts = []
        fs = curve.start_point
        parts.append(f'M {fs.x:.3f},{fs.y:.3f}')
        for seg in curve.segments:
            if seg.is_corner:
                parts.append(f'L {seg.c.x:.3f},{seg.c.y:.3f}')
                parts.append(f'L {seg.end_point.x:.3f},{seg.end_point.y:.3f}')
            else:
                parts.append(
                    f'C {seg.c1.x:.3f},{seg.c1.y:.3f} '
                    f'{seg.c2.x:.3f},{seg.c2.y:.3f} '
                    f'{seg.end_point.x:.3f},{seg.end_point.y:.3f}'
                )
        parts.append('Z')

        etree.SubElement(svg_root, 'path', {
            'd': ' '.join(parts),
            'fill': fill_color,
            'stroke': stroke_color,
            'stroke-width': str(stroke_width),
            'fill-rule': 'evenodd',
        })

    etree.ElementTree(svg_root).write(
        output_svg, pretty_print=True,
        xml_declaration=True, encoding='UTF-8'
    )
    print(f"Saved → {output_svg}")

def atlas_to_SVGs(mesh_path, atlas_name='aseg', views=['left_medial', 'left_lateral', 'right_lateral', 'right_medial', 'superior', 'inferior'],
                  atlas=None, zoom=2, style='flat', bmesh='midthickness', bmesh_alpha=0, cmap='plasma', shuffle_colors=False,
                  bmesh_color=None, figsize=(1000, 600), export_path=None):

    if export_path is None:
        export_path = os.getcwd()
    elif not os.path.exists(export_path):
        os.makedirs(export_path)

    plot_subcortical(custom_atlas_path=mesh_path, 
                         views = views, 
                         cmap=cmap, figsize=figsize, bmesh_alpha=bmesh_alpha, style=style, zoom=zoom,
                         plot_regions_separately=True, export_path=export_path)
    
    # Find all mesh files and their corresponding region names, and get the list of region names for this atlas
    file_map = _find_subcortical_files(mesh_path)
    rmesh_names = get_atlas_regions(atlas, 'subcortical', mesh_path)

    # Get unique base names (preserving order)
    base_names = list(dict.fromkeys(get_base_name(n) for n in rmesh_names))

    # Generate one color per unique base region
    if cmap is None:
        base_colors = generate_distinct_colors(len(base_names), seed=42)
        base_color_map = {base: color for base, color in zip(base_names, base_colors)}
    elif isinstance(cmap, str):
        cmap_obj = get_cmap(cmap)
        base_color_map = {
            base: tuple(c[:3])
            for base, c in zip(base_names, cmap_obj(np.linspace(0, 1, len(base_names))))
        }

    # Optionally shuffle the color assignments to help distinguish adjacent regions with similar colors in the colormap
    if shuffle_colors:
        import random
        random.seed(42)
        items = list(base_color_map.items())
        random.shuffle(items)
        base_color_map = dict(items)
    
    # Map every region (including L/R variants) to its base color
    d_atlas_colors = {name: base_color_map[get_base_name(name)] for name in rmesh_names}
    
    # Loop over views and regions to convert PNGs to SVGs
    for view_name in views:
        
        view_name_face = view_name.replace('left_', '').replace('right_', '')  # e.g. 'medial', 'lateral'

        for target_name in d_atlas_colors.keys():

            export_prefix = f'{export_path}/{target_name}_{view_name_face}'
            # If d_atlas_color is a tuple 
            if isinstance(d_atlas_colors[target_name], tuple):
                hex_color = rgb2hex(d_atlas_colors[target_name])
            else:
                hex_color = d_atlas_colors[target_name]

            print(f"Tracing PNG to SVG for {target_name} in view {view_name} with color {hex_color}...")
                
            try:
                png_to_traced_outline(input_png=f'{export_prefix}.png', output_svg=f'{export_prefix}.svg', turdsize=4,
                                    alphamax=1.0, opttolerance=0.2, fill_color=hex_color, stroke_color='black',
                                    stroke_width=0.5, alpha_threshold=128)
                
                # Remove the intermediate PNG if you only want SVGs
                if os.path.exists(f'{export_prefix}.svg'):
                    os.remove(f'{export_prefix}.png')
                
            except Exception as e:
                print(f"Error occurred while tracing {target_name} in view {view_name}: {e}")


def composite_3D_mesh(mesh_path, atlas_name='aseg', views=['left_medial', 'left_lateral'],
                  zoom=1.5, style='glossy', cmap='plasma', bmesh_alpha=0,
                  figsize=(1000, 600), export_path=None):
    
    if export_path is None:
        export_path = os.getcwd()
    
    # Also render a composite view with all regions visible for this hemisphere/face, to use as a reference when layering SVGs
    yab.plot_subcortical(
        custom_atlas_path=mesh_path,
        figsize=figsize,
        bmesh_alpha=bmesh_alpha,
        zoom=zoom,
        cmap=cmap,
        style=style,
        export_path=f'{export_path}/{atlas_name}_3D_composite_left.png',
        display_type='object',
        views=views
    )

def composite_svgs_by_plot_order(
    plot_order_df,
    svg_dir,
    view_name,
    hemisphere,
    output_img_path=None,
    figsize=(6, 6),
    stroke_color='black',
    stroke_width=0.5,
    dpi=150,
):
    """
    Composite individual region SVGs into a single figure, layered by plot_order.

    Parameters
    ----------
    plot_order_df : pd.DataFrame
        Must have columns: region, face, plot_order, Hemisphere
    svg_dir : str
        Directory containing per-region SVGs named like '{Region}_{view_name}.svg'
        e.g. 'Caudate_R_right_medial.svg'
    view_name : str
        e.g. 'right_medial' or 'right_lateral'
    hemisphere : str
        'L' or 'R'
    output_svg : str or None
        Path to save final composite SVG
    output_png : str or None
        Path to save final composite PNG
    figsize : tuple
        Matplotlib figure size in inches
    stroke_color : str
        Outline color for all patches
    stroke_width : float
        Outline width for all patches
    dpi : int
        Resolution for PNG export
    """

    # Determine which face(s) correspond to this view
    # view_name like 'right_lateral' -> face = 'lateral', hemisphere = 'R'
    if '_' in view_name:
        face = view_name.split('_')[-1]   # 'lateral' or 'medial'
    else:
        face = view_name  # if view_name is just 'medial' or 'lateral' without hemisphere prefix

    # Filter dataframe to this view's face and hemisphere
    df_view = (
        plot_order_df
        .loc[
            (plot_order_df['face'] == face) &
            # Hemisphere is equal to the view's hemisphere, OR the region is labeled as 'both' (e.g. 'B' for bilateral)
            (plot_order_df['Hemisphere'] == hemisphere) | (plot_order_df['Hemisphere'] == f'B{hemisphere}')

        ]
        .sort_values('plot_order')
        .reset_index(drop=True)
    )

    if df_view.empty:
        print(f"No regions found for view={view_name}, hemisphere={hemisphere}")
        return

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect('equal')
    ax.axis('off')

    canvas_w, canvas_h = None, None

    for _, row in df_view.iterrows():
        region = row['region']          # e.g. 'caudate'
        hemi = row['Hemisphere']        # 'R'

        # Build the expected SVG filename
        if hemi in ['BL', 'BR']:
            svg_filename = f"{svg_dir}/{region}_{face}.svg"  # bilateral regions don't have hemisphere in filename
        else:
            svg_filename = f"{svg_dir}/{region}_{hemi}_{face}.svg"

        try:
            tree = etree.parse(svg_filename)
        except Exception as e:
            print(f"  Skipping {svg_filename}: {e}")
            continue

        root = tree.getroot()
        ns = 'http://www.w3.org/2000/svg'

        # Get canvas size from first SVG we successfully load
        if canvas_w is None:
            canvas_w = float(root.get('width', 500))
            canvas_h = float(root.get('height', 500))
            ax.set_xlim(0, canvas_w)
            ax.set_ylim(canvas_h, 0)  # flip y so SVG coords match (origin top-left)

        # Parse all <path> elements and add as PathPatch objects
        for path_el in root.findall(f'.//{{{ns}}}path'):
            # Read fill and stroke directly from the SVG element
            fill_color = path_el.get('fill', 'none')

            d = path_el.get('d', '')
            if not d:
                continue
            try:
                mpl_path = svgpath2mpl.parse_path(d)
                patch = mpatches.PathPatch(
                    mpl_path,
                    facecolor=fill_color,
                    edgecolor=stroke_color,
                    linewidth=stroke_width,
                    zorder=row['plot_order'],   # layer by plot_order
                )
                ax.add_patch(patch)
            except Exception as e:
                print(f"  Could not parse path in {svg_filename}: {e}")
                continue

    plt.tight_layout(pad=0)

    # If no output_img_path is specified, use current working directory
    if output_img_path is None:
        output_img_path = os.getcwd()

    output_png = f'{output_img_path}/{atlas_name}_{hemisphere}_{face}.png'
    output_svg = f'{output_img_path}/{atlas_name}_{hemisphere}_{face}.svg'

    fig.savefig(output_png, dpi=dpi, bbox_inches='tight',
                transparent=True, format='png')
    print(f"Saved PNG → {output_png}")

    fig.savefig(output_svg, bbox_inches='tight',
                    transparent=True, format='svg')
    print(f"Saved SVG → {output_svg}")

    plt.close(fig)

            
###########################################################
# Run the pipeline
###########################################################

if __name__ == "__main__":

    atlas_mesh_output_path = f'{atlas_output_data_path}/meshes/'
    atlas_vector_output_path = f'{atlas_output_data_path}/vectors/'

    # Create meshes for given atlas
    create_mesh_for_atlas(atlas_nii, atlas_lookup_txt, atlas_mesh_output_path, smooth_i=smooth_i, smooth_f=smooth_f, overwrite_meshes=overwrite_meshes)

    # Plot composite 3D mesh for reference when layering SVGs
    composite_3D_mesh(mesh_path=atlas_mesh_output_path, atlas_name=atlas_name, views=['left_medial', 'left_lateral', 'right_medial', 'right_lateral', 'superior', 'inferior'],
                  zoom=zoom, style='glossy', cmap=cmap, bmesh_alpha=0,
                  figsize=(2000, 600), export_path=atlas_output_data_path)

    # Convert meshes --> PNG --> SVG for rendering data
    atlas_to_SVGs(mesh_path=atlas_mesh_output_path, atlas_name=atlas_name, export_path=atlas_vector_output_path, cmap=cmap, shuffle_colors=shuffle_colors,
                  views=['left_medial', 'left_lateral', 'right_lateral', 'right_medial', 'superior', 'inferior'])
