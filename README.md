# Subcortical data visualization in 2D

This python package currently includes the following six subcortical atlases for data visualization in two-dimensional vector graphics:

<img src="docs-site/docs/images/all_atlas_showcase.png" width="100%">

More information about these atlases, including the process of rendering the surfaces and tracing the outlines for each, can be found in the [`atlas_info/`](https://github.com/anniegbryant/subcortex_visualization/tree/main/atlas_info) directory and at the [project website](https://anniegbryant.github.io/subcortex_visualization/).


## 🙋‍♀️ Motivation

This Python package was created to generate two-dimensional subcortex images in the style of the popular [`ggseg` package](https://github.com/ggseg/ggseg) in R.
We based our vector graphic outlines on the three-dimensional subcortical meshes either (1) provided as part of the [ENIGMA toolbox](https://github.com/MICA-MNI/ENIGMA) for the aseg atlas or (2) meshes generated in-house using rendering software from [Chris Rorden's lab](https://github.com/neurolabusc) (either [nii2mesh](https://github.com/neurolabusc/nii2mesh) or [Surf Ice](https://github.com/neurolabusc/surf-ice); check out [`custom_segmentation_pipeline/`](https://github.com/anniegbryant/subcortex_visualization/tree/main/custom_segmentation_pipeline) for more information).

The below graphic summarizes the transformation from 3D volumetric meshes to 2D surfaces, starting from the ENIGMA toolbox ('aseg' atlas, left) or a custom-rendered mesh from the [Melbourne Subcortex Atlas](https://github.com/yetianmed/subcortex/tree/master) as published in [Tian et al. (2020)]()https://www.nature.com/articles/s41593-020-00711-6 -- ('S1' granularity level, right).

<img src="docs-site/docs/images/aseg_and_Melbourne_S1_3D_to_2D_schematic.png" width="90%">


While `ggseg` offers subcortical plotting with the `aseg` atlas, it is [not currently possible](https://github.com/ggseg/ggseg/issues/104) to show data from all seven subcortical regions (accumbens, amygdala, caudate, hippocampus, pallidum, putamen, thalamus) in the same figure.
Moreover, there is currently no other software available to visualize any of the other above subcortical/thalamic atlases in 2D with real data, hence development here.


## 🖥️ Installation

The package can be installed from GitHub in two ways.
First, you can install directly with pip from the [PyPI repository](https://pypi.org/project/subcortex-visualization/):

```bash
pip install subcortex-visualization
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

<img src="docs-site/docs/images/example_aseg_subcortex_plot.png" width="80%">


### 📚 Tutorial

For a guide that goes through all the functionality and atlases available in this package, we compiled a simple walkthrough tutorial in [tutorial.ipynb](https://github.com/anniegbryant/subcortex_visualization/blob/main/tutorial.ipynb).
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
* `value_column`: The name of the column in your `subcortex_data` to plot, defaults to 'value'
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

<img src="docs-site/docs/images/example_aseg_subcortex_normdist.png" width="80%">


## 💡 Want to generate your own mesh and/or parcellation?

This package provides six subcortical atlases as a starting point.
The workflow can readily be extended to your favorite segmentation atlas, though! 
We have a dedicated folder for a custom segmentation pipeline that will walk you through the two key steps:  
1. Rendering a series of triangulated surface meshes from your parcellation atlas (starting from a .nii.gz volume), using either the [`nii2mesh`](https://github.com/neurolabusc/nii2mesh) or [`surfice_atlas`](https://github.com/neurolabusc/surfice_atlas) software, both developed by Chris Rorden; and 
2. Tracing the outline of each region in the rendered mesh in vector graphic editing software (we use Inkscape in the tutorial as a powerful and free option), to yield a two-dimensional image of your atlas in scalable vector graphic (.svg) format.

Check out the walkthrough in the [`custom_segmentation_pipeline/`](https://github.com/anniegbryant/subcortex_visualization/tree/main/custom_segmentation_pipeline) folder for more information on how to render your own volumetric segmentation with an interactive mesh and convert to a two-dimensional vector graphic that can be integrated with this package.

## 🙏 Acknowledgments

Thank you very much to [Chris Rorden](https://github.com/rordenlab), [Ye Tian](https://github.com/yetianmed), and [Sid Chopra](https://github.com/sidchop) for their suggestions and continued development of open tools for neuroimaging visualization that enabled development of this project!

## ❓📧 Questions, comments, or suggestions always welcome!

Please feel free to ask questions, report bugs, or share suggestions by creating an issue or by emailing me (Annie) at ([anniegbryant@gmail.com](mailto:anniegbryant@gmail.com)) 😊

As an [open-source tool](https://opensource.guide/how-to-contribute/), pull requests are always welcome from the community, too.
If you create your own custom vector graphic for your segmentation atlas of choice, feel free to create a pull request to incorporate and be acknowledged.
