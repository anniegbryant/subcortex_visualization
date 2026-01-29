#' Helper function to prepare the brain data for plotting
#'
#' This function reads in the corresponding SVG and atlas ordering file for the
#' user-specified atlas and hemisphere combination. The SVG is read in as both a 
#' dataframe and an XML file to enable linking between paths and Inkscape metadata.
#'
#' @param atlas Name of the atlas to plot (e.g., 'aseg')
#' @param hemisphere Hemisphere to plot ('L', 'R', or 'both')
#' @param subcortex_data Empirical data to plot (optional)
#' @param value_column If empirical data is passed, which column to plot values from
#' @return A dataframe containing all of the SVG path information together with the atlas data
#' @export
prep_data <- function(atlas, hemisphere, subcortex_data=NULL, value_column='value') {
  # Define SVG + ordering files
  SVG_file <- system.file("extdata", paste0(atlas, "_", hemisphere, ".svg"), package = "subcortexVisualizationR")
  atlas_ordering <- read.csv(system.file("extdata", paste0(atlas, "_", hemisphere, "_ordering.csv"), package = "subcortexVisualizationR"))
  
  # Read SVG in as a dataframe
  atlas_SVG_df <- svgparser::read_svg(SVG_file, obj_type="data.frame")
  atlas_SVG_xml <- xml2::read_xml(SVG_file)
  
  # Define namespace
  this_ns <- xml2::xml_ns(atlas_SVG_xml)
  
  # Find the correct paths by SVG title
  paths_xml <- xml2::xml_find_all(atlas_SVG_xml, ".//svg:path", this_ns)
  path_lookup <- tibble(
    elem_idx = seq_along(paths_xml),
    region = vapply(
      paths_xml,
      function(p) {
        t <- xml2::xml_find_first(p, "./svg:title", this_ns)
        if (!inherits(t, "xml_missing")) xml2::xml_text(t) else NA_character_
      },
      character(1)
    )
  ) %>% 
    filter(!is.na(region))
  
  # Define region order for colors
  region_order <- atlas_ordering %>% 
    distinct(seg_index, region) %>%
    arrange(seg_index) %>% 
    pull(region) 
  
  # Drop duplicates of region, keeping only first instance
  region_order <- unique(region_order)
  
  # Join with the path lookup to map the names
  atlas_SVG_df_labeled <- atlas_SVG_df %>%
    left_join(path_lookup, by = "elem_idx") %>% 
    mutate(Hemisphere = ifelse(str_detect(region, '_L$'), 'L', 'R'),
           face = ifelse(str_detect(region, '_lateral'), 'lateral', 'medial'), 
           region = str_replace_all(region, "_L$|_R$", '')) %>% 
    mutate(region = str_replace(region, '_lateral|_medial', '')) %>%
    left_join(., atlas_ordering) %>%
    arrange(plot_order, elem_idx, path_idx) %>% 
    filter(!is.na(plot_order)) %>% 
    mutate(region = factor(region, levels=region_order))
  
  # Join with subcortex_data
  if (is.null(subcortex_data)) {
    atlas_SVG_df_labeled <- atlas_SVG_df_labeled %>%
      mutate(fill_var = region)
  } else {
    atlas_SVG_df_labeled <- atlas_SVG_df_labeled %>%
      left_join(subcortex_data) %>% 
      mutate(fill_var = .data[[value_column]])
  }
  
  # Return the labeled data
  return(list(atlas_SVG_df_labeled, region_order))
}

#' Helper function to select appropriate color palette and fill type for data
#'
#' This function reads in the corresponding SVG and atlas ordering file for the
#' user-specified atlas and hemisphere combination. The SVG is read in as both a 
#' dataframe and an XML file to enable linking between paths and Inkscape metadata.
#'
#' @param atlas_SVG_df_labeled Dataframe containing individual path nodes from SVG plus atlas information
#' @param cmap Palette name in the viridis family, a colour vector (for discrete data), or a palette function (for continuous data)
#' @param discrete Whether the data is discrete (e.g., names of regions) or not (e.g., continuous empirical data)
#' @param region_order Order in which regions should be filled and plotted
#' @param NA_fill Color to fill in missing data for regions (string/hex code accepted)
#' @param vmin Lower bound for color plotting, useful for plotting multiple versions from the same data
#' @param vmax Upper bound for color plotting, useful for plotting multiple versions from the same data
#' @param midpoint Value to center colors at between vmin and vmax
#' @return A fill function that can be applied to discrete or continuous data as appropriate
#' @export
resolve_fill_scale <- function(
    atlas_SVG_df_labeled,
    cmap='viridis',
    discrete=TRUE,
    region_order = NULL,
    NA_fill = "#cccccc",
    vmin = NULL,
    vmax = NULL,
    midpoint = NULL) {
  
  # Case 1: character palette name (viridis family only)
  if (is.character(cmap) && length(cmap) == 1) {
    
    if (discrete) {
      return(
        scale_fill_viridis_d(
          option = cmap,
          limits = region_order,
          drop   = FALSE,
          na.value = NA_fill
        )
      )
    } else {
      return(
        scale_fill_viridis_c(
          option = cmap,
          limits = c(vmin, vmax),
          na.value = NA_fill
        )
      )
    }
  }
  
  # Case 2: discrete palette (vector of colours)
  if (is.character(cmap) && length(cmap) > 1) {
    
    if (!discrete) {
      # If vmin and vmax are null, set limits to be symmetric around midpoint
      if (is.null(vmin) & is.null(vmax) & !is.null(midpoint)) {
        max_dev = max(abs(atlas_SVG_df_labeled$fill_var - midpoint))
        vmin <- midpoint - max_dev
        vmax <- midpoint + max_dev
        
      }
      return(scale_fill_gradientn(
        colours=cmap, 
        limits=c(vmin, vmax), 
        na.value = NA_fill))
    }
    
    return(
      scale_fill_manual(
        values = cmap,
        limits = region_order,
        drop   = FALSE,
        na.value = NA_fill))
  }
  
  # Case 3: continuous palette function
  if (is.function(cmap)) {
    
    if (discrete) {
      # Generate one color per region
      return(scale_fill_manual(
        values=cmap(length(region_order)), 
        na.value=NA_fill))
    }
    
    return(
      scale_fill_gradientn(
        colours = cmap(256),
        limits  = c(vmin, vmax),
        na.value = NA_fill
      )
    )
  }
  
  stop("`cmap` must be a palette name in the viridis family, a colour vector (for discrete data), or a palette function (for continuous data).")
}

#' Helper function to plot each brain region individually to ensure proper plotting order
#'
#' This function accepts a dataframe combining SVG elements and atlas information and plots each region individually
#' according to the atlas-specific plotting order.
#'
#' @param atlas_SVG_df_labeled Dataframe containing individual path nodes from SVG plus atlas information
#' @param region_order Character vector containing the order in which regions should be plotted
#' @param line_color Color for lines outlining each region (default 'black')
#' @param line_thickness Thickness of lines outlining each region (default 0.5)
#' @param cmap Colormap to fill in regions (can be character name of palette, vector of colors, or a colormap function)
#' @param discrete Whether to plot with discrete data or not (default=T)
#' @param NA_fill Color to fill in missing data for regions (string/hex code accepted)
#' @param vmin Lower bound for color plotting, useful for plotting multiple versions from the same data
#' @param vmax Upper bound for color plotting, useful for plotting multiple versions from the same data
#' @param midpoint Value to center colors at between vmin and vmax
#' @return A ggplot2 object containing all of the brain regions for the given atlas
#' @export
plot_individual_regions <- function(atlas_SVG_df_labeled, region_order, line_color='black', line_thickness=0.5, cmap='plasma',
                                    discrete=TRUE, NA_fill="#cccccc", vmin=NULL, vmax=NULL, midpoint=NULL) {
  # We need to loop over each region individually to layer according to plot_order
  iterated_plot <- ggplot()
  
  for (plot_order_i in unique(atlas_SVG_df_labeled$plot_order)) {
    
    this_object_i <- subset(atlas_SVG_df_labeled, plot_order==plot_order_i)
    
    # Create the plot
    iterated_plot <- iterated_plot +
      geom_polygon(
        data = this_object_i,
        aes(
          x, y,
          fill = fill_var,
          group = elem_idx
        ),
        colour = line_color,
        linewidth = line_thickness,
        inherit.aes = FALSE
      )
  }
  
  # Add finishing touches to the plot
  iterated_plot <- iterated_plot + 
    scale_y_reverse() +
    theme_void() 
  
  # Way to solve fill that works for both discrete and continuous data dynamically
  iterated_plot <- iterated_plot +
    resolve_fill_scale(
      atlas_SVG_df_labeled = atlas_SVG_df_labeled,
      cmap        = cmap,
      discrete    = discrete,
      region_order = region_order,
      NA_fill     = NA_fill,
      vmin        = vmin,
      vmax        = vmax,
      midpoint    = midpoint
    )
  
  # Return the final plot
  return(iterated_plot)
}


#' Main function to plot data in a user-selected subcortical/cerebellar atlas
#'
#' This function accepts a dataframe combining SVG elements and atlas information and plots each region individually
#' according to the atlas-specific plotting order.
#'
#' @param subcortex_data Empirical data to plot (optional)
#' @param atlas Name of atlas to use (default='aseg')
#' @param hemisphere Name of hemisphere(s) to use (default='L')
#' @param value_column If empirical data is passed, which column to plot values from
#' @param line_color Color for lines outlining each region (default='black')
#' @param line_thickness Thickness of lines outlining each region (default=0.5)
#' @param cmap Colormap to fill in regions (can be character name of palette, vector of colors, or a colormap function)
#' @param NA_fill Color to fill in missing data for regions (string/hex code accepted; default="#cccccc")
#' @param vmin Lower bound for color plotting, useful for plotting multiple versions from the same data
#' @param vmax Upper bound for color plotting, useful for plotting multiple versions from the same data
#' @param midpoint Value to center colors at between vmin and vmax
#' @param show_legend Whether to plot legend at the bottom (default=TRUE)
#' @param fill_title Title to use for legend, if requested (default='values')
#' @param font_size Font size for legend (default=12)
#' @return A ggplot2 object containing all of the brain regions for the given atlas
#' @export
plot_subcortical_data <- function(subcortex_data=NULL, 
                                  atlas='aseg', 
                                  hemisphere='L',
                                  value_column='value',
                                  line_color='black',
                                  line_thickness=0.5, 
                                  cmap='viridis',
                                  NA_fill="#cccccc", 
                                  vmin=NULL, 
                                  vmax=NULL, 
                                  midpoint=NULL, 
                                  show_legend=TRUE,
                                  fill_title="values", 
                                  fontsize=12) {
  
  if (atlas=='SUIT_cerebellar_lobule') {
    print("Individual-hemisphere visualization is not supported with the SUIT cerebellar lobule atlas. Rendering both hemispheres together, along with the vermis.")
    hemisphere = 'both'
  }
  
  # Prepare the SVG data and user-supplied subcortex data, if applicable
  prepped_data <- prep_data(atlas=atlas, 
                            hemisphere=hemisphere, 
                            value_column=value_column, 
                            subcortex_data=subcortex_data)
  atlas_SVG_df_labeled <- prepped_data[[1]]
  region_order <- prepped_data[[2]]
  
  # Discrete plot unless subcortex_data is provided
  discrete <- is.null(subcortex_data)
  
  # Create the ggplot2 object for this atlas/hemisphere/data
  subcortical_plot <- plot_individual_regions(atlas_SVG_df_labeled=atlas_SVG_df_labeled, 
                                              region_order=region_order,
                                              line_color=line_color, 
                                              line_thickness=line_thickness, 
                                              cmap=cmap,
                                              discrete=discrete,
                                              NA_fill=NA_fill, 
                                              vmin=vmin, 
                                              vmax=vmax, 
                                              midpoint=midpoint) +
    coord_equal() # Ensures regions are drawn in correct aspect ratio
  
  
  # Add legend if requested in function
  if (show_legend) {
    subcortical_plot <- subcortical_plot +
      theme(legend.position='bottom',
            legend.text = element_text(size=fontsize)) +
      labs(fill=fill_title) 
    
    # Check whether legend is discrete or continouous
    if (is.null(subcortex_data)) {
      subcortical_plot <- subcortical_plot +
        guides(fill=guide_legend(title.position="top", title.hjust = 0.5)) 
    } else {
      subcortical_plot <- subcortical_plot +
        guides(fill=guide_colorbar(title.position="top", title.hjust = 0.5)) 
    }
    
  } else {
    subcortical_plot <- subcortical_plot +
      theme(legend.position='none')
  }
  
  # Return the final plot
  return(subcortical_plot)
  
}