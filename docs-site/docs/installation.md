# Python

## Direct installation from PyPI

This package can be installed directly with pip from the [PyPI repository](https://pypi.org/project/subcortex-visualization/):

```bash
pip install subcortex-visualization
```

## Cloning with GitHub

Alternatively, you can clone this [repository](https://github.com/anniegbryant/subcortex_visualization) from GitHub and then install from your local version:

```bash
git clone https://github.com/anniegbryant/subcortex_visualization.git
cd subcortex_visualization
pip install .
```

This option is good if you want to make any modifications, including [adding your own atlas](https://anniegbryant.github.io/subcortex_visualization/custom_segmentation/).

# R

## Installing from GitHub

To install the R version of this package (`subcortexVisualizationR`), run the following in R (either in the terminal or in RStudio):

```R
# if not already installed
install.packages("remotes")

# then install subcortexVisualizationR
remotes::install_github("anniegbryant/subcortex_visualization", subdir = "subcortexVisualizationR")
```