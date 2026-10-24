# Changelog

All notable changes to `subcortex_visualization` are documented here.

---

## [1.3.3] — 2026-09-18

This release adds a new feature, two bug fixes, and a substantial new test suite.

**New features**

- Categorical/discrete color maps: Users can now map discrete categorical values to subcortical regions (e.g., coloring all thalamic regions one color, hippocampal regions another). This is particularly useful for atlases that contain multiple nuclei/subregions of a given subcortical region.

**Bug fixes**

- Fixed a bug in align_to_MNI152NLin_templates.py where the input and output spaces were inverted. Affected atlases have been corrected in both Python and R.
- Column name parsing is now case-insensitive: Region/region and Hemisphere/hemisphere/Hemi/hemi are all accepted interchangeably in both Python and R.

**Other improvements**

- Plot and legend spacing were adjusted to handle different plot layouts more gracefully.
- A new test suite (tests/) has been added covering plotting, utility functions, and private helpers (~900 lines of tests across three files).
README updated with the Aperture Neuro publication link and new studies citing the package.

---

## [1.3.2] — 2026-09-09

**New features**

- Melbourne Subcortex Atlas 7T support: The 7T versions of the Melbourne atlas are now available at resolutions S1–S4 (e.g., Melbourne_S1_7T). Tutorials for both Python and R have been updated with examples.

---

## [1.3.1] — 2026-07-19

### Fixed
- Fixed bug in `align_to_MNI152NLin_templates.py` where input and output spaces were inverted. Corrected affected atlas files in Python and R, and added print statements to confirm spaces explicitly.

---

## [1.3.0] — 2026-05-04

### Added
- **New atlases** — Added Brainstem Navigator, CIT168, and THOMAS thalamus atlases.
- **Multi-space support** — All atlases now provided in both MNI152NLin6Asym and MNI152NLin2009cAsym standard spaces.
- **Parcel segmentation** — New `parcel_segstats()` function (Python and R) extracts and summarizes voxel values from an input NIfTI volume across atlas parcels.
- **Region-specific line thickness** — `line_thickness` argument now accepts a column name to specify per-region thickness values (contributed by [@llevitis](https://github.com/llevitis)).

### Changed
- Major internal plotting refactor: monolithic plotting logic decomposed into focused helper functions (`_prep_data`, `_plot_helper`, `_plot_helper_individual`, etc.) in both Python and R.
- Fixed bilateral hemisphere handling (normalization of `BL`/`BR`/`B`).
- Vermis plotting for cerebellum in R now supports `Hemisphere = 'V'`.

### Removed
- Legacy `custom_segmentation/` scripts and old docs images removed.

### Documentation
- Updated tutorials, API reference pages, and atlas info pages for all new atlases and the segmentation feature.

---

## [1.2.1] — 2026-02-08

### Added
- R package: tutorials (Rmd/md), equal aspect ratio for plots, and more flexibility for color scales.
- R function to retrieve atlas region names.
- R tutorial added to project website.

### Fixed
- Fixed `region_order` definition in R version.
- User-specified NA values now applied consistently across all region data in R plots.
- Fixed cerebellum cortex and vermis region name retrieval in R.

---

## [1.2.0] — 2026-01-16

### Added
- **R package** (`subcortexVisualizationR`) — Full R implementation of the subcortical visualization toolbox.
- Custom segmentation script folder and walkthrough documentation.

---

## [1.1.0] — 2025-11-19

### Added
- Melbourne Subcortex Atlas S3 and S4 resolutions.
- SUIT cerebellar atlas.
- `fontsize` argument for plot labels.
- `Melbourne` and `Tian` accepted as interchangeable atlas name aliases (contributed by [@cindyhfls](https://github.com/cindyhfls)).

---

## [1.0.0] — 2025-09-27

Initial stable release of `subcortex_visualization`.

### Features
- Python package with `plot_subcortical_data()` supporting the FreeSurfer `aseg`, Melbourne Subcortex (S1–S2), and Tian atlases.
- 2D vector graphic output (SVG-based) for publication-ready figures.
- Customizable colormaps, hemisphere selection, and region ordering.
