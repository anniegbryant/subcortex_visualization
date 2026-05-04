#' Return the names of regions in a given subcortical or cerebellar atlas.
#'
#' @param atlas_name Name of the subcortical/cerebellar atlas (e.g., \code{"aseg_subcortex"}).
#' @return For most atlases: a character vector of region names ordered by segmentation index.
#'   For \code{"SUIT_cerebellar_lobule"}: a named list with \code{hemisphere_regions} and
#'   \code{vermis_regions}. For \code{"Brainstem_Navigator"}: a named list with
#'   \code{hemisphere_regions} and \code{midline_regions}.
#' @export
get_atlas_regions <- function(atlas_name) {

  if (atlas_name == "SUIT_cerebellar_lobule") {
    hemisphere <- "both"

    atlas_ordering <- read.csv(system.file("extdata", "data", atlas_name,
                                           paste0(atlas_name, "_", hemisphere, "_ordering.csv"),
                                           package = "subcortexVisualizationR"))

    hemisphere_regions <- atlas_ordering |>
      dplyr::filter(Hemisphere == "L") |>
      dplyr::arrange(seg_index) |>
      dplyr::distinct(region) |>
      dplyr::pull(region)

    vermis_regions <- atlas_ordering |>
      dplyr::filter(Hemisphere == "V") |>
      dplyr::arrange(seg_index) |>
      dplyr::distinct(region) |>
      dplyr::pull(region)

    return(list(hemisphere_regions = hemisphere_regions, vermis_regions = vermis_regions))
  }

  if (atlas_name == "Brainstem_Navigator") {
    atlas_ordering <- read.csv(system.file("extdata", "data", atlas_name,
                                           paste0(atlas_name, "_L_ordering.csv"),
                                           package = "subcortexVisualizationR"))

    hemisphere_regions <- atlas_ordering |>
      dplyr::filter(Hemisphere == "L") |>
      dplyr::arrange(seg_index) |>
      dplyr::distinct(region) |>
      dplyr::pull(region)

    midline_regions <- atlas_ordering |>
      dplyr::filter(Hemisphere == "B") |>
      dplyr::arrange(seg_index) |>
      dplyr::distinct(region) |>
      dplyr::pull(region)

    return(list(hemisphere_regions = hemisphere_regions, midline_regions = midline_regions))
  }

  hemisphere <- "L"
  atlas_ordering <- read.csv(system.file("extdata", "data", atlas_name,
                                         paste0(atlas_name, "_", hemisphere, "_ordering.csv"),
                                         package = "subcortexVisualizationR"))

  unique_regions <- atlas_ordering |>
    dplyr::arrange(seg_index) |>
    dplyr::distinct(region) |>
    dplyr::pull(region)

  return(unique_regions)
}
