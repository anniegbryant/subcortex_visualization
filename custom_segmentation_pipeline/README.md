# How to generate your own two-dimensional segmentation for data viz

If you use a particular segmentation atlas in your research and would like to visualize data in that atlas in two dimensions, you can follow along with this guide!
These are the exact same steps we implemented to generate the segmentation visuals included in this python package for the `aseg` (FreeSurfer) and `S1`/`S2` (Melbourne Subcortex Atlas) atlases included here.

## Step 1. Creating and visualizing a custom triangulated mesh from a volumetric segmentation/parcellation

### Generating mesh files (.obj) per region

First, you'll want to convert from your three-dimensional segmentation atlas (stored as a NIFTI image) to a triangulated mesh rendering using the [`nii2mesh` tool](https://github.com/neurolabusc/nii2mesh) developed by Chris Rorden:

<img src="../images/volume_to_mesh_schematic.png" width="90%">

The repository for this tool has really helpful documentation as well as a web-based platform that converts a NIFTI volume to a triangulated mesh (.obj) file without any installation or repository cloning.
It's an awesome resource, though we'll need to clone the repository to have full (local) access to the functionality needed to generate a mesh per index (i.e., region) in the segmentation volume.
Once you clone the repository, it's very straightforward to compile in C++.
Here are the steps, as copied from the `nii2mesh` [repository README](https://github.com/neurolabusc/nii2mesh):

```
git clone https://github.com/neurolabusc/nii2mesh
cd nii2mesh/src
make
```

Check that after running `make`, there is a binary file `nii2mesh` in the `nii2mesh/src/` directory, since that's the key function.
If everything looks good there, we'll use the `nii2mesh` program to generate an individual `.obj` mesh file per region in our segmentation atlas by setting the `-a 1` flag.
For example, if you're using a hippocampal subfield segmentation volume with 10 regions (voxels labeled 1 through 10 accordingly), the below script will generate 10 individual `.obj` mesh files:

```
nii2mesh my_custom_segmentation.nii.gz -a 1 my_custom_segmentation.obj
```

### Visualizing your mesh objects

There are a variety of programs that can render the `.obj` mesh files, including [Blender](https://www.blender.org/) and [3D Slicer](https://www.slicer.org/), as well as [online tools](https://3dviewer.net/).
If you're using a Mac, the Quick Look feature can also interactively render .obj meshes!

We've included a [simple Jupyter notebook](https://github.com/anniegbryant/subcortex_visualization/blob/main/custom_segmentation_pipeline/render_mesh_interactively.ipynb) guide to combine and render the meshes into one object that is interactive and color-coded by region:

<img src="../images/mesh_rotation_interactive.gif" width="60%">

If you use this method, we recommend rotating the object until you reach the desired angle(s) for generating your two-dimensional atlas, then exporting as a snapshot PNG image(s) by clicking the 'PNG' icon as shown in the above video.

## 🎨 Tracing the outline of each region in vector graphic editing software

### Creating outlines for each region

Next, pour yourself a big mug of coffee to sit and trace the outline of each region in Inkscape (or a similar vector graphic editing program) ☕️
We'll walk you through the steps using Inkscape.

Open up a new image (.svg) in Inkscape, and import the PNG snapshot generated from the above rendered mesh by either clicking `⌘+I` (Mac) or `Ctrl+I` (Windows), or `File > Import`.
We'll use the 'Freehand lines' tool for tracing, which looks like the following along your toolbar:

<img src="../images/inkscape_freehand_lines.png" width="80%">

And then go ahead and trace your first region in your image!
We recommend setting 'Smoothing' in your top toolbar to around 20 (we use 22.0), which means that you can do a pretty quick first pass at tracing each region and the path won't stick to every bump you draw.

<img src="../images/tracing_region.gif" width="60%">

Once you finish your first trace, if you want to edit any of the points in the path, just double-click on the black line and you can click and drag the points to adjust their spacing.
Rinse and repeat: go ahead and trace the outline for all of the regions in your atlas.
Once you finish, when you take away the 3D mesh PNG underneath, you should have a set of outlines that resemble a minimalist aesthetic line-art tattoo like so:

<img src="../images/trace_outline_combined.png" width="50%">

### Labeling each region in the SVG metadata