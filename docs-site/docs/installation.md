# Installation guide

## Python

### Requirements

`subcortex-visualization` requires **Python ≥ 3.11** and the following packages, which are installed automatically:

| Package | Version | Source |
|---------|---------|--------|
| matplotlib | 3.10.1 | [PyPI](https://pypi.org/project/matplotlib/) |
| numpy | 2.2.5 | [PyPI](https://pypi.org/project/numpy/) |
| pandas | 2.2.3 | [PyPI](https://pypi.org/project/pandas/) |
| setuptools | 75.8.0 | [PyPI](https://pypi.org/project/setuptools/) |
| svgpath2mpl | 1.0.0 | [PyPI](https://pypi.org/project/svgpath2mpl/) |

### Direct installation from PyPI

This package can be installed directly with pip from the [PyPI repository](https://pypi.org/project/subcortex-visualization/):

```bash
pip install subcortex-visualization
```

### Cloning with GitHub

Alternatively, you can clone this [repository](https://github.com/anniegbryant/subcortex_visualization) from GitHub and then install from your local version:

```bash
git clone https://github.com/anniegbryant/subcortex_visualization.git
cd subcortex_visualization
pip install .
```

This option is good if you want to make any modifications, including [adding your own atlas](https://anniegbryant.github.io/subcortex_visualization/custom_segmentation/).

## R

### Requirements

`subcortexVisualizationR` requires **R ≥ 4.1** (tested on R 4.5.2) and the following packages:

| Package | Version | Source |
|---------|---------|--------|
| tidyverse | 2.0.0 | [CRAN](https://cran.r-project.org/package=tidyverse) |
| xml2 | 1.5.2 | [CRAN](https://cran.r-project.org/package=xml2) |
| patchwork | 1.3.2 | [CRAN](https://cran.r-project.org/package=patchwork) |
| RNifti | 1.9.0 | [CRAN](https://cran.r-project.org/package=RNifti) |
| scales | 1.4.0 | [CRAN](https://cran.r-project.org/package=scales) |
| svgparser | 0.1.2 | [GitHub (coolbutuseless/svgparser)](https://github.com/coolbutuseless/svgparser) |
| ANTsR | 0.6.6 | [GitHub (ANTsX/ANTsR)](https://github.com/ANTsX/ANTsR) |
| extrantsr | 3.10.0 | [GitHub (muschellij2/extrantsr)](https://github.com/muschellij2/extrantsr) |

!!! note "GitHub-sourced packages"
    `svgparser`, `ANTsR`, and `extrantsr` are not available on CRAN and must be installed from GitHub. These are **installed automatically** when you run `remotes::install_github()` below — no additional steps required.

### Installing from GitHub

To install the R version of this package (`subcortexVisualizationR`), run the following in R (either in the terminal or in RStudio):

```R
# if not already installed
install.packages("remotes")

# then install subcortexVisualizationR
remotes::install_github("anniegbryant/subcortex_visualization", subdir = "subcortexVisualizationR")
```

## Dependencies and reproducibility

Both the Python and R packages pin the exact version of every dependency so you can recreate the same environment in the future, even if packages have been updated or removed.

### Python

A `requirements.txt` file in the repository records the exact version of every Python dependency. To recreate the environment used to produce the package:

```bash
pip install -r requirements.txt
```

### R

The `subcortexVisualizationR` project uses [`renv`](https://rstudio.github.io/renv/) to manage R package dependencies. 
The `renv.lock` file committed to the repository records the exact version of every R dependency, including the GitHub commit SHA for GitHub-sourced packages (`svgparser`, `ANTsR`, `extrantsr`).

To restore the identical R environment at any point in the future, open R in the `subcortexVisualizationR` project directory and run:

```R
renv::restore()
```

This installs exactly the versions recorded in `renv.lock`, regardless of what package versions are current at that time.