#' Print the names of regions in a given subcortical atlas
#'
#' This function takes in the name of a given subcortical/cerebellar atlas (e.g., 'aseg')
#' and returns the list of regions in that atlas, ordered by segmentation index
#'
#' @param atlas_name Name of the atlas to get regions frmo (e.g., 'aseg')
#' @return A list of regions in the specified atlas, ordered by segmentation index
#' @export
get_atlas_regions <- function(atlas_name) {

  # If the atlas is the SUIT cerebellar lobules, use hemisphere of 'both'
  if (atlas_name == 'SUIT_cerebellar_lobule') {
    hemisphere='both'

    # Load ordering file
    atlas_ordering <- read.csv(system.file("extdata", paste0(atlas_name, "_", hemisphere, "_ordering.csv"), package = "subcortexVisualizationR"))

    # Identify regions for left/right cerebellar hemispheres versus vermis
    hemisphere_regions <- atlas_ordering %>% filter(Hemisphere=='L') %>% arrange(seg_index) %>% distinct(region) %>% pull(region)
    vermis_regions <- atlas_ordering %>% filter(Hemisphere=='V') %>% arrange(seg_index) %>% distinct(region) %>% pull(region)

    # Return both lists of regions as a tuple
    return(list(hemisphere_regions=hemisphere_regions, vermis_regions=vermis_regions))
  }
  
  # Otherwise, use just the left hemisphere to get region names 
  else {  
    hemisphere='L'
    
    # Load ordering file
    atlas_ordering <- read.csv(system.file("extdata", paste0(atlas_name, "_", hemisphere, "_ordering.csv"), package = "subcortexVisualizationR"))
    
    # Sort by segmentation index and print the array of region names
    unique_regions <- atlas_ordering %>% arrange(seg_index) %>% distinct(region) %>% pull(region)
    
    # Return the list of regions
    return(unique_regions)
  }
}