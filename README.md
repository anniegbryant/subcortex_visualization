# Subcortical data visualization in 2D

## 🙋‍♀️ Motivation

This Python package was created to generate two-dimensional subcortex images in the style of the popular [`ggseg` package](https://github.com/ggseg/ggseg) in R.
We based our vector graphic outlines on the three-dimensional subcortical meshes provided as part of the [ENIGMA toolbox](https://github.com/MICA-MNI/ENIGMA); more information on this powerful resource can be found in [Larivière, S., et al. *Nat Methods* (2021)](https://doi.org/10.1038/s41592-021-01186-4). 

The below graphic summarizes the transformation from 3D volumetric meshes to 2D surfaces, starting from the ENIGMA toolbox ('aseg' atlas, left) or a custom-rendered mesh from the [Melbourne Subcortex Atlas](https://github.com/yetianmed/subcortex/tree/master) generated by Ye Tian ('S1' granularity level, right).

<img src="images/aseg_and_Tian_S1_3D_to_2D_schematic.png" width="90%">


While `ggseg` offers subcortical plotting with the `aseg` atlas, it is [not currently possible](https://github.com/ggseg/ggseg/issues/104) to show data from all seven subcortical regions (accumbens, amygdala, caudate, hippocampus, pallidum, putamen, thalamus) in the same figure.
There is currently no other software available to visualize the Melbourne Subcortex Atlas segmentation in 2D with real data, hence development here (currently detail levels S1 and S2 are available in this package, as described below).


## 🖥️ Installation

The package can be installed from GitHub in two ways.
First, you can install directly with pip:

```bash
pip install git+https://github.com/anniegbryant/subcortex_visualization.git#egg=subcortex_visualization
```

If you would like to make your own modifications before installing, you can also clone this repository first and then install from your local version:

```bash
git clone https://github.com/anniegbryant/subcortex_visualization.git
cd subcortex_visualization
pip install .
```

This will install the `subcortex_visualization` package so you have access to the `plot_subcortical_data` function and associated data.

## 👨‍💻 Usage

### ❗️ Quick start

Running the below code will produce an image of the left subcortex in the aseg atlas (the default), each region colored by its index, with the plasma color scheme:

```python
plot_subcortical_data(hemisphere='L', cmap='plasma', 
                      fill_title = "Subcortical region index")
```

<img src="images/example_aseg_subcortex_plot.png" width="80%">


### 📚 Tutorial

For a guide that goes through all the functionality and atlases available in this package,  we compiled a simple walkthrough tutorial in [tutorial.ipynb](https://github.com/anniegbryant/subcortex_visualization/blob/main/tutorial.ipynb).
To plot real data in the subcortex, your `subcortex_data` should be  a `pandas.DataFrame` structured as follows (here we've just assigned an integer index to each region):

| region        | value         | Hemisphere  |
| :--- | :---: | :---: |
| accumbens | 0 | L |
| amygdala | 1 | L |
| caudate | 2 | L |
| hippocampus | 3 | L |
| pallidum | 4 | L |
| putamen | 5 | L |
| thalamus | 6 | L |

Briefly, all functionality is contained within the `plot_subcortical_data` function, which takes in the following arguments: 
* `subcortex_data`: The three-column dataframe in a format as shown above; this is optional, if left out the plot will just color each region by its index
* `atlas`: The name of the subcortical segmentation atlas (default is 'aseg', which is currently the only supported atlas)
* `line_thickness`: How thick the lines around each subcortical region should be drawn, in mm (default is 1.5)
* `line_color`: What color the lines around each subcortical region should be (default is 'black')
* `hemisphere`: Which hemisphere ('L' or 'R') the `subcortex_data` is from; can also be 'both' (default is 'L')
* `fill_title`: Name to add to legend (default is 'values')
* `cmap`: name of colormap (e.g., 'plasma' or 'viridis') or a `matplotlib.colors.Colormap` (default is 'viridis')
* `vmin`: Min fill value; this is optional, and you would only want to use this to manually constrain the fill range to match another figure
* `vmax`: Max fill value; this is optional, and you would only want to use this to manually constrain the fill range to match another figure
* `midpoint`: Midpoint value to enforce for fill range; this is optional

Here's an example plotting both hemispheres, with data randomly sampled from a normal distribution, setting a color range from blue (low) to red (high) with white at the center (midpoint=0):

```python
import matplotlib.colors as mcolors
import numpy as np

np.random.seed(127)

example_continuous_data_L = pd.DataFrame({"region": ["accumbens", "amygdala", "caudate", "hippocampus", "pallidum", "putamen", "thalamus"],
                                          "value": np.random.normal(0, 1, 7)}).assign(Hemisphere = "L")
example_continuous_data_R = pd.DataFrame({"region": ["accumbens", "amygdala", "caudate", "hippocampus", "pallidum", "putamen", "thalamus"],
                                            "value": np.random.normal(0, 1, 7)}).assign(Hemisphere = "R")
example_continuous_data = pd.concat([example_continuous_data_L, example_continuous_data_R], axis=0)

white_blue_red_cmap = mcolors.LinearSegmentedColormap.from_list("BlueWhiteRed", ["blue", "white", "red"])

plot_subcortical_data(subcortex_data=example_continuous_data, atlas='aseg',
                      hemisphere='both', fill_title = "Normal distribution sample",
                      cmap=white_blue_red_cmap, midpoint=0)
```

<img src="images/example_aseg_subcortex_normdist.png" width="80%">


### 🧠 Usage with different levels of granularity in the Melbourne Subcortex Atlas

We currently offer two levels of detail from the [Melbourne Subcortex Atlas](https://github.com/yetianmed/subcortex/tree/master): S1 (total of 16 regions) and S2 (total of 32 regions).
Here's a schematic overview of the conversion from 3D to 2D for these two segmentations:

<img src="images/Tian_S1_and_S2_3D_to_2D_schematic.png" width="90%">

## 💡 Want to generate your own mesh and/or parcellation?

This package provides three popular subcortical atlases as a starting point: the `aseg` segmentation into seven regions per hemisphere from the FreeSurfer `recon-all` pipeline, and two segmentation levels (`S1` and `S2`) from Ye Tian's segmentations as part of the Melbourne Subcortical Atlas.
The workflow can readily be extended to your favorite segmentation atlas, though! 
We have a dedicated folder for a custom segmentation pipeline that will walk you through the two key steps:  
1. Rendering a series of triangulated surface meshes from your parcellation atlas (starting from a .nii.gz volume), using the [`nii2mesh`](https://github.com/neurolabusc/nii2mesh) software developed by Chris Rorden; and 
2. Tracing the outline of each region in the rendered mesh in vector graphic editing software (we use Inkscape in the tutorial as a powerful and free option), to yield a two-dimensional image of your atlas in scalable vector graphic (.svg) format.

### 🕸️ Creating and visualizing a custom triangulated mesh from a volumetric segmentation/parcellation

First, you'll want to convert from your three-dimensional segmentation atlas (stored as a NIFTI image) to a triangulated mesh rendering using the [`nii2mesh` tool](https://github.com/neurolabusc/nii2mesh) developed by Chris Rorden:

<img src="images/volume_to_mesh_schematic.png" width="90%">

In the tutorial Jupyter notebook, you can rotate the rendered mesh in 3D right in your notebook!

<img src="images/mesh_rotation_interactive.gif" width="60%">


### 🎨 Tracing the outline of each region in vector graphic editing software

Next, pour yourself a big mug of coffee to sit and trace the outline of each region in Inkscape (or a similar vector graphic editing program) ☕️

<img src="images/tracing_region.gif" width="60%">

The first pass at tracing each region can be pretty quick, since you can edit individual points in the path afterwards.
If your atlas is homotopically symmetric (i.e., symmetric between hemispheres), the silver lining here is that you only need to trace for one hemisphere (e.g., left hemisphere) and then save the flipped (mirrored) version for the other hemisphere. 

## ❓📧 Questions, comments, or suggestions always welcome!

Please feel free to ask questions, report bugs, or share suggestions by creating an issue or by emailing me (Annie) at ([anniegbryant@gmail.com](mailto:anniegbryant@gmail.com)) 😊

As an [open-source tool](https://opensource.guide/how-to-contribute/), pull requests are always welcome from the community, too.