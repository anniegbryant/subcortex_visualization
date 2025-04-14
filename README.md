# Subcortical data visualization in 2D

## Motivation

This Python package was created to generate two-dimensional subcortex images in the style of the popular [`ggseg` package](https://github.com/ggseg/ggseg) in R.
We based our vector graphic outlines on the three-dimensional subcortical meshes provided as part of the [ENIGMA toolbox](https://github.com/MICA-MNI/ENIGMA); more information on this powerful resource can be found in [Larivière, S., et al. *Nat Methods* (2021)](https://doi.org/10.1038/s41592-021-01186-4). 

The below graphic summarizes the transformation from 3D volumetric meshes in the ENIGMA toolbox (left) to 2D vector graphics in this python package (right).

<img src="Example_3D_to_2D_schematic.png" width="70%">


While `ggseg` offers subcortical plotting with the `aseg` atlas, it is [not currently possible](https://github.com/ggseg/ggseg/issues/104) to show data from all seven subcortical regions (accumbens, amygdala, caudate, hippocampus, pallidum, putamen, thalamus) in the same figure, hence development here.


## Installation

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

## Usage

Running the below code will produce an image of the left subcortex, each region colored by its index, with the plasma color scheme:

```python
plot_subcortical_data(hemisphere='L', cmap='plasma', 
                      fill_title = "Subcortical region index")
```

<img src="example_subcortex_plot.png" width="80%">

We compiled a simple walkthrough tutorial in [tutorial.ipynb](https://github.com/anniegbryant/subcortex_visualization/blob/main/tutorial.ipynb) to demonstrate how to plot real data in one or both hemispheres.
Real data should be structured as follows in a `pandas.DataFrame` for plotting (here we've just assigned an integer index to each region):

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

plot_subcortical_data(subcortex_data=example_continuous_data,  
                      line_thickness=1.25, line_color='black',
                          hemisphere='both', fill_title = "Normal distribution sample", cmap=white_blue_red_cmap, 
                          vmin=None, vmax=None, midpoint=0)
```


<img src="example_subcortex_normdist.png" width="80%">