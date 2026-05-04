# R API Reference

---

## `plot_subcortical_data`

Visualize a given subcortical or cerebellar atlas template as a vector graphic, colored according to user-provided data values or, by default, a simple region-based color scheme.

**Usage**

```r
plot_subcortical_data(
  subcortex_data       = NULL,
  atlas                = 'aseg_subcortex',
  value_column         = 'value',
  hemisphere           = 'L',
  views                = c('medial', 'lateral'),
  line_color           = 'black',
  line_thickness       = 0.5,
  cmap                 = 'viridis',
  NA_fill              = "#cccccc",
  fill_alpha           = 1.0,
  fill_by_significance = FALSE,
  nonsig_fill_alpha    = 0.5,
  vmin                 = NULL,
  vmax                 = NULL,
  midpoint             = NULL,
  show_legend          = TRUE,
  fill_title           = "values",
  fontsize             = 12
)
```

**Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `subcortex_data` | data.frame or NULL | `NULL` | Data frame with columns `region`, `Hemisphere`, and `value_column`. If NULL, regions will be simply colored based on their assigned index in the corresponding atlas. May also include a `p_value` column if `fill_by_significance = TRUE`. |
| `atlas` | character | `'aseg_subcortex'` | The atlas used for the subcortical regions. One of `'aseg_subcortex'`, `'CIT168_subcortex'`, `'Melbourne_S1'` (or `'Tian_S1'`), `'AICHA_subcortex'`, `'Brainnetome_subcortex'`, `'Thalamus_HCP'`, `'Thalamus_THOMAS'`, `'Brainstem_Navigator'`, `'SUIT_cerebellar_lobule'`. |
| `value_column` | character | `'value'` | The name of the column in `subcortex_data` that contains the values to be visualized. |
| `hemisphere` | character | `'L'` | Which hemisphere(s) to display. Use `'L'` for left, `'R'` for right, or `'both'` for bilateral plots. |
| `views` | character vector | `c('medial', 'lateral')` | Which faces of the subcortical regions to display. Options include `'medial'`, `'lateral'`, `'superior'`, and `'inferior'`. Not applicable to the SUIT cerebellar lobule atlas. |
| `line_color` | character | `'black'` | Color of the outline around each subcortical region. |
| `line_thickness` | numeric or character | `0.5` | Thickness of the outline for each region in ggplot2 `linewidth` units, or a column name in `subcortex_data` whose value gives region-specific thickness. |
| `cmap` | character or function | `'viridis'` | Colormap used to fill in the regions. Accepts a viridis palette name (single string), a vector of hex colors, or a palette function. |
| `NA_fill` | character | `"#cccccc"` | Color to use for regions with missing data (NA values). |
| `fill_alpha` | numeric | `1.0` | Opacity level for the filled regions, between 0 (transparent) and 1 (opaque). |
| `fill_by_significance` | logical | `FALSE` | If TRUE, adjusts fill opacity based on significance. Non-significant regions (`p_value >= 0.05`) are drawn at `nonsig_fill_alpha` over a white backing, with thinner outlines. Requires a `p_value` column in `subcortex_data`. |
| `nonsig_fill_alpha` | numeric | `0.5` | If `fill_by_significance` is TRUE, this opacity level is applied to non-significant regions (p >= 0.05). |
| `vmin` | numeric or NULL | `NULL` | Minimum value for colormap normalization. If NULL, the minimum of the input values is used. |
| `vmax` | numeric or NULL | `NULL` | Maximum value for colormap normalization. If NULL, the maximum of the input values is used. |
| `midpoint` | numeric or NULL | `NULL` | If provided, uses a diverging colormap centered around this value. |
| `show_legend` | logical | `TRUE` | If TRUE, displays a legend or colorbar indicating the mapping of values to colors. |
| `fill_title` | character | `"values"` | Label for the colorbar indicating the meaning of the fill values. |
| `fontsize` | numeric | `12` | Font size for the figure text elements. |

**Returns**

A **patchwork** / ggplot2 object.

---

## `parcel_segstats`

Extract voxel values from an input volume based on a parcellation atlas and apply a reduction function to each parcel.

**Usage**

```r
parcel_segstats(
  input_vol,
  atlas_space       = 'MNI152NLin6Asym',
  atlas             = 'aseg_subcortex',
  func_name         = 'Functional map',
  parc_stat         = mean,
  ignore_background = TRUE,
  background_value  = 0,
  interpolation     = NULL
)
```

**Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_vol` | RNifti image or character | — | The input 3D or 4D NIfTI image from which to extract voxel values. Can be an RNifti object or a file path to a NIfTI image. |
| `atlas_space` | character | `'MNI152NLin6Asym'` | The standard space to use for the corresponding atlas. Options include `'MNI152NLin6Asym'` (the default) and `'MNI152NLin2009cAsym'`. |
| `atlas` | character or list | `'aseg_subcortex'` | Name(s) of the subcortical atlas/atlases to apply. If multiple atlases are provided as a list, the function will iterate over them and concatenate results. |
| `func_name` | character | `'Functional map'` | A name for the functional map being summarized, used for labeling purposes in the output data frame. |
| `parc_stat` | function or list | `mean` | A function like `mean`, `sd`, etc. that takes an array of values and returns a single summary statistic (scalar). Can also be a list of functions, in which case the output data frame will have one row per parcel per summary statistic. |
| `ignore_background` | logical | `TRUE` | If TRUE, the background label (as defined by `background_value`) is skipped when extracting parcel values. |
| `background_value` | numeric | `0` | Integer label in the parcellation that represents background (non-parcel) voxels. |
| `interpolation` | character or NULL | `NULL` | If the input volume and atlas have different affines or spatial dimensions, this parameter specifies the interpolation method for resampling the atlas to match the input volume. Options include `'nearest'`, `'linear'`, and `'cubic'`. If NULL (default), no resampling is performed and an error will be raised if affines or dimensions do not match. |

**Returns**

A data frame with one row per parcel per summary statistic, with columns: `stat`, `value`, `Atlas`, `Functional_Map`, `region`, `Hemisphere`, `Region_Index`.

**Notes**

Users should ensure that the input volume is in the same standard space as the atlas specified by `atlas_space` to avoid issues with affine and spatial dimension mismatches. If resampling is necessary, users must specify an interpolation method.

---

## `get_atlas_regions`

Return the names of regions in a given subcortical or cerebellar atlas.

**Usage**

```r
get_atlas_regions(atlas_name)
```

**Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `atlas_name` | character | — | Name of the subcortical/cerebellar atlas (e.g. `'aseg_subcortex'`). |

**Returns**

For most atlases: a character vector of region names ordered by segmentation index.
For `'SUIT_cerebellar_lobule'`: a named list with `hemisphere_regions` and `vermis_regions`.
For `'Brainstem_Navigator'`: a named list with `hemisphere_regions` and `midline_regions`.
