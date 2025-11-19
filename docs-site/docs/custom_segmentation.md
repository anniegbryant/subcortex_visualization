## Usage Example

This package provides six subcortical atlases as a starting point.
The workflow can readily be extended to your favorite segmentation atlas, though! 
We have a dedicated folder for a custom segmentation pipeline that will walk you through the two key steps:  

1. Rendering a series of surface meshes from your parcellation atlas (starting from a .nii.gz volume), using [`surfice_atlas`](https://github.com/neurolabusc/surfice_atlas) software developed by the lab of [Chris Rorden](https://github.com/neurolabusc); and 
2. Tracing the outline of each region in the rendered mesh in vector graphic editing software (we use Inkscape in the tutorial as a powerful and free option), to yield a two-dimensional image of your atlas in scalable vector graphic (.svg) format.

If you use a particular segmentation atlas in your research and would like to visualize data in that atlas in two dimensions, you can follow along with this guide!
These are the exact same steps we implemented to generate the segmentation visuals included in this Python package for all atlases.

## Step 1. Creating and visualizing a custom triangulated mesh from a volumetric segmentation/parcellation

First, you'll want to convert from your three-dimensional segmentation atlas (stored as a NIFTI image) to a triangulated mesh rendering.
There are many tools out there to accomplish this depending on your preference; here, we'll suggest and walk through the [`surfice_atlas'](https://github.com/neurolabusc/surfice_atlas) option, developed by the lab of [Chris Rorden](https://github.com/neurolabusc) 

This method will generate one color-coded 3D mesh file (`.mz3`) for your segmentation, which can then be rendered interactively in the [`Surf Ice`](https://github.com/neurolabusc/surf-ice) GUI software (described in more detail in [Rorden *Nature Methods* (2025)](https://www.nature.com/articles/s41592-025-02764-6).)

### Prerequisites for mesh generation and visualization
There are a few prerequisites for this step, which should be completed before you can crack on with your mesh generation:  

1. Ensure your system has a working [MATLAB](https://www.mathworks.com/products/matlab.html) installation.

2. Clone the [`surfice_atlas`](https://github.com/neurolabusc/surfice_atlas) repository to your local machine with `git clone https://github.com/neurolabusc/surfice_atlas.git` 

3. Clone the [`surfice_atlas`](https://github.com/neurolabusc/spmScripts) repository to your local machine with `git clone https://github.com/neurolabusc/spmScripts.git` 

4. Download the [latest SPM](https://www.fil.ion.ucl.ac.uk/spm/software/) (Statistical Parametric Mapping) to wherever you store Matlab plugins 

5. Download and install the `Surf Ice` (Version 6) graphical rendering software for your given operating systen from [NITRC](https://www.nitrc.org/projects/surfice/). 

Once you've completed these steps, we'll generate the `.mz3` file for an example segmentation in Matlab.

### Generating the .mz3 file in Matlab

First, we'll add the relevant paths to MATLAB in a script or directly at the console:

```matlab
addpath('/path/to/github/surfice_atlas/'); % Change to where you cloned surfice_atlas
addpath('/path/to/github/spmScripts/'); % Change to where you cloned spmScripts
addpath('/path/to/MATLAB/spm/'); % Change to where you copied the spm folder
```

Now, it's a very simple process to convert our atlas segmentation to an `.mz3` file to read into Surf Ice:

```matlab
our_example_segmentation = '/path/to/example_segmentation.nii.gz';
lut = '/path/to/github/surfice_atlas/mylut.lut'; % We use the default LUT that came with surfice_atlas, you can create your own

nii_nii2atlas(our_example_segmentation, lut);
```

This will generate a file called `merge.mz3`, which contains color-coded mesh volumes for each region in your example segmentation.

### Visualizing the 3D mesh

Boot up the Surf Ice GUI software and open the `merge.mz3` file (using File > Open to select merge.mz3), and you should have a color-coded three-dimensional mesh rendered on your screen.

![3D mesh rotation GIF](images/surfice_example.gif)

If you use this method, we recommend rotating the object until you reach the desired angle(s) for generating your two-dimensional atlas, then taking a screenshot from the medial and lateral perspectives.

## 🎨 Tracing the outline of each region in vector graphic editing software

### Creating outlines for each region

Next, pour yourself a big mug of coffee to sit and trace the outline of each region in Inkscape (or a similar vector graphic editing program) ☕️
We'll walk you through the steps using Inkscape.

Open up a new image (.svg) in Inkscape, and import the PNG snapshot generated from the above rendered mesh by either clicking `⌘+I` (Mac) or `Ctrl+I` (Windows), or `File > Import`.
We'll use the 'Freehand lines' tool for tracing, which looks like the following along your toolbar:

![Tracing outline example](images/inkscape_freehand_lines.png)

And then go ahead and trace your first region in your image!
We recommend setting 'Smoothing' in your top toolbar to around 20 (we use 22.0), which means that you can do a pretty quick first pass at tracing each region and the path won't stick to every bump you draw.

![Tracing outline example](images/tracing_region.gif)

Once you finish your first trace, if you want to edit any of the points in the path, just double-click on the black line and you can click and drag the points to adjust their spacing.
Rinse and repeat: go ahead and trace the outline for all of the regions in your atlas.
Once you finish, when you take away the 3D mesh PNG underneath, you should have a set of outlines that resemble a minimalist aesthetic line-art tattoo like so:

![Completed trace](images/trace_outline_combined.png)

### Labeling each region in the SVG metadata

After you finish tracing the outline for each region, you can store the name of that region along with the face (medial or lateral) and hemisphere (right or left) to identify that region programmatically in python.
In Inkscape, you can accomplish this by selecting a given region (here, the left putamen shown on the lateral face).
In the 'Object Properties' pane shown on the right, in the 'Title' text box, you should then put the name of the region (e.g., 'putamen'), face (e.g., 'lateral'), and abbreviation (e.g., 'L'), all as one string separated by underscores, as shown in the screenshot.
In other words, for the highlighted region, its Title should be 'putamen_lateral_L':

![Inkscape region metadata](images/inkscape_region_metadata.png)

Once you add the title to each region, congrats, you've finished creating the vector graphic for the given hemisphere for your custom atlas!

### Repeating for the other hemisphere

You may notice that the above SVG image is saved as 'Melbourne_S1_L.svg', which indicates that this file corresponds to: 
* subcortex
* Melbourne Subcortex Atlas, granularity level 1 (S1)
* left hemisphere (L)

If your atlas is left-right symmetric, you can just copy-paste the SVG objects into a new file named e.g., 'Melbourne_S1_R.svg', making sure you (1) flip the image along the $y$-axis (i.e., left-right mirror) and update each region's Title to end with '_R' rather than '_L'.

### Combining the left and right hemispheres into one image

Once you have both hemispheres traced, the last step here is to copy-paste the left and right hemisphere vector graphics into the same image for an SVG corresponding to both hemispheres, named e.g. 'Melbourne_S1_both.svg'.
Make sure all the individual regions have appropriate Title text fields corresponding to the region name, face, and hemisphere.

![Combining hemispheres Inkscape](images/Melbourne_S1_both_inkscape.png)

## 🗂️ Organizing the file structure correctly for your custom atlas

Once you have all your regions traced in the left and right hemispheres for your segmentation, in the `subcortex_visualization/data/` folder, make sure you have the following SVG files--in this case, corresponding to the Melbourne S1 subcortical atlas:

* Melbourne_S1_both.svg
* Melbourne_S1_L.svg
* Melbourne_S1_R.svg

### 🔎 Lookup tables to indicate the order for drawing regions

Home stretch, you're almost done 🏃‍♀️

One of the last steps to get plotting with your custom atlas to create a lookup table for each of the three SVG images (left, right, and both hemispheres).
Each table, in .csv format, should have the following four columns:  

1. `region`: name of the region (e.g., 'accumbens')
2. `face`: which face to plot (e.g., 'lateral')
3. `plot_order`: in which order should this region be plotted? A value of 1 means this region will be drawn first (i.e., on the bottom) and higher values mean the region will be drawn higher in the stack (i.e., closer to the top). This is only relevant if some regions are overlapping and you care about plotting order.
4. `Hemisphere`: which hemisphere the corresponding region belongs to (should be all 'L' for left hemisphere and 'R' for right hemisphere).

Take a look at the examine lookup tables provided for the Melbourne Subcortex Atlas S1 segmentation in the [left hemisphere], [right hemisphere], and both hemispheres to see exactly how these files are organized.
In the case of the Melbourne Subcortex Atlas S1 subcortical atlas, this corresponds to three lookup table files:

* Melbourne_S1_both_ordering.csv
* Melbourne_S1_L_ordering.csv
* Melbourne_S1_R_ordering.csv

And with that, you'll just need to reinstall the python package once you've added your new vector graphics and lookup tables! 
That can be accomplished by simply navigating to the base level of this repository and running:

```bash 
# Change to where you've cloned this repo
cd /path/to/github/subcortex_visualization 

# To reinstall the subcortex-visualization package
python3 -m pip install . 
```