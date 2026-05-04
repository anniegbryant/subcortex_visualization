# Map BL/BR → B so SVG title keys match the SVG file"s naming convention
.normalise_hemi <- function(h) ifelse(h %in% c("BL", "BR"), "B", h)


# Prepare atlas ordering data for plotting: loads ordering CSV and merges with user data
.prep_data <- function(atlas, hemisphere, subcortex_data = NULL, value_column = "value") {

  ordering_file <- system.file(
    "extdata", "data", atlas,
    paste0(atlas, "_", hemisphere, "_ordering.csv"),
    package = "subcortexVisualizationR"
  )
  atlas_ordering <- read.csv(ordering_file)

  region_order <- atlas_ordering |>
    dplyr::arrange(seg_index) |>
    dplyr::distinct(region) |>
    dplyr::pull(region) |>
    unique()

  if (is.null(subcortex_data)) {
    atlas_ordering <- atlas_ordering |>
      dplyr::mutate(fill_var = region)
  } else {
    # Expand "B" hemisphere rows into BL and BR so they join with sided convention
    bilateral <- subcortex_data[subcortex_data$Hemisphere == "B", ]
    if (nrow(bilateral) > 0) {
      bl <- bilateral; bl$Hemisphere <- "BL"
      br <- bilateral; br$Hemisphere <- "BR"
      subcortex_data <- dplyr::bind_rows(
        subcortex_data[subcortex_data$Hemisphere != "B", ],
        bl, br, bilateral
      )
    }

    # If the atlas uses "B" for midline regions but subcortex_data has "BL"/"BR" for those
    # regions (e.g., user-simulated data from the "both" ordering), add "B" copies so the
    # join below can match them.
    atlas_b_regions <- unique(atlas_ordering$region[atlas_ordering$Hemisphere == "B"])
    if (length(atlas_b_regions) > 0) {
      existing_b_regions <- unique(subcortex_data$region[subcortex_data$Hemisphere == "B"])
      # regions that need a "B" copy in subcortex_data
      needs_b <- setdiff(atlas_b_regions, existing_b_regions) 
      if (length(needs_b) > 0) {
        bl_br_rows <- subcortex_data[subcortex_data$Hemisphere %in% c("BL", "BR") &
                                       subcortex_data$region %in% needs_b, ]
        if (nrow(bl_br_rows) > 0) {
          b_copies <- bl_br_rows[!duplicated(bl_br_rows$region), ]
          b_copies$Hemisphere <- "B"
          subcortex_data <- dplyr::bind_rows(subcortex_data, b_copies)
        }
      }
    }

    # Join user-supplied data to atlas ordering; fill_var is the column used for coloring in the plot.
    atlas_ordering <- atlas_ordering |>
      dplyr::left_join(subcortex_data, by = c("region", "Hemisphere")) |>
      dplyr::mutate(fill_var = .data[[value_column]])
  }

  # Return both the full atlas_ordering (with user data merged in) and the region_order (for discrete color scales)
  list(atlas_ordering = atlas_ordering, region_order = region_order)
}


# Select a ggplot2 fill scale for discrete or continuous brain data
.resolve_fill_scale <- function(atlas_ordering,
                               cmap       = "viridis",
                               discrete   = TRUE,
                               region_order = NULL,
                               NA_fill    = "#cccccc",
                               vmin       = NULL,
                               vmax       = NULL,
                               midpoint   = NULL) {

  # Case 1: single viridis-family palette name
  if (is.character(cmap) && length(cmap) == 1) {
    if (discrete) {
      return(
        ggplot2::scale_fill_viridis_d(
          option   = cmap,
          limits   = region_order,
          drop     = FALSE,
          na.value = NA_fill
        )
      )
    } else {
      if (!is.null(midpoint)) {
        # scale_fill_viridis_c does not support a custom rescaler, so sample the
        # palette and use scale_fill_gradientn with an explicit values rescaling.
        viridis_colors <- scales::viridis_pal(option = cmap)(256)
        return(
          ggplot2::scale_fill_gradientn(
            colours  = viridis_colors,
            limits   = c(vmin, vmax),
            values   = scales::rescale(c(vmin, midpoint, vmax)),
            na.value = NA_fill
          )
        )
      }
      return(
        ggplot2::scale_fill_viridis_c(
          option   = cmap,
          limits   = c(vmin, vmax),
          na.value = NA_fill
        )
      )
    }
  }

  # Case 2: User supplied a vector of colors to create a manual scale
  if (is.character(cmap) && length(cmap) > 1) {
    if (discrete) {
      return(
        ggplot2::scale_fill_manual(
          values   = cmap,
          limits   = region_order,
          drop     = FALSE,
          na.value = NA_fill
        )
      )
    } else {
      # Compute symmetric limits around midpoint if not supplied
      if (!is.null(midpoint) && is.null(vmin) && is.null(vmax)) {
        max_dev <- max(abs(atlas_ordering$fill_var - midpoint), na.rm = TRUE)
        vmin <- midpoint - max_dev
        vmax <- midpoint + max_dev
      }
      # If midpoint is provided, rescale the colors so that it maps to the center of the colormap
      if (!is.null(midpoint)) {
        return(
          ggplot2::scale_fill_gradientn(
            colours = cmap,
            limits  = c(vmin, vmax),
            values  = scales::rescale(c(vmin, midpoint, vmax)),
            na.value = NA_fill
          )
        )
      }
      # If no midpoint, just use the provided colors with the specified limits
      return(
        ggplot2::scale_fill_gradientn(
          colours  = cmap,
          limits   = c(vmin, vmax),
          na.value = NA_fill
        )
      )
    }
  }

  # Case 3: User supplied a palette function (e.g., from RColorBrewer or a custom function)
  if (is.function(cmap)) {
    if (discrete) {
      return(
        ggplot2::scale_fill_manual(
          values   = cmap(length(region_order)),
          limits   = region_order,
          drop     = FALSE,
          na.value = NA_fill
        )
      )
    }
    return(
      ggplot2::scale_fill_gradientn(
        colours  = cmap(256),
        limits   = c(vmin, vmax),
        na.value = NA_fill
      )
    )
  }

  stop("`cmap` must be a viridis palette name, a colour vector, or a palette function.")
}


# ---------------------------------------------------------------------------
# Internal SVG loading helpers
# ---------------------------------------------------------------------------

# Read polygon data from individual per-region SVG files (most atlases).
# Iterates over atlas_ordering rows, loading {region}_{hemi}_{face}.svg from svg_dir.
.read_individual_atlas_data <- function(atlas_ordering, svg_dir, views) {
  all_data   <- list()
  group_base <- 0L

  # Filter data only to the requested view(s)
  df_filtered <- atlas_ordering[atlas_ordering$face %in% views, ]

  for (i in seq_len(nrow(df_filtered))) {
    row    <- df_filtered[i, ]
    region <- row$region
    hemi   <- row$Hemisphere
    face   <- row$face

    if (hemi %in% c("BL", "BR")) {
      svg_file <- file.path(svg_dir, paste0(region, "_", face, ".svg"))
    } else {
      svg_file <- file.path(svg_dir, paste0(region, "_", hemi, "_", face, ".svg"))
    }

    if (!file.exists(svg_file)) {
      warning(paste("SVG not found, skipping:", svg_file))
      next
    }

    svg_df <- suppressMessages(tryCatch(
      svgparser::read_svg(svg_file, obj_type = "data.frame"),
      error = function(e) { warning(paste("Could not parse:", svg_file)); NULL }
    ))
    if (is.null(svg_df) || nrow(svg_df) == 0) next

    # Assign globally unique group IDs across all loaded SVGs
    unique_elems         <- unique(svg_df$elem_idx)
    id_map               <- setNames(group_base + seq_along(unique_elems), unique_elems)
    svg_df$group_id      <- id_map[as.character(svg_df$elem_idx)]
    group_base           <- group_base + length(unique_elems)

    svg_df$region             <- region
    svg_df$Hemisphere         <- hemi
    svg_df$face               <- face
    svg_df$plot_order         <- row$plot_order
    svg_df$fill_var           <- row$fill_var
    svg_df$p_value            <- if ("p_value"            %in% names(row)) row$p_value            else NA_real_
    svg_df$line_thickness_val <- if ("line_thickness_val" %in% names(row)) row$line_thickness_val else 0.5

    all_data[[length(all_data) + 1]] <- svg_df
  }

  if (length(all_data) == 0) return(NULL)
  dplyr::bind_rows(all_data)
}


# Read polygon data from a combined SVG that uses <title> elements to identify
# regions (used for SUIT_cerebellar_lobule).
# Expected title format: {region}_{face}_{Hemisphere}
.read_SUIT_data <- function(atlas_ordering, svg_file) {
  if (!file.exists(svg_file)) {
    warning(paste("SUIT SVG not found:", svg_file))
    return(NULL)
  }

  svg_df <- suppressMessages(tryCatch(
    svgparser::read_svg(svg_file, obj_type = "data.frame"),
    error = function(e) { warning(paste("Could not parse SVG:", svg_file)); NULL }
  ))
  if (is.null(svg_df) || nrow(svg_df) == 0) return(NULL)

  # Parse the SVG XML to extract <title> elements for each path to identify the region/hemisphere
  svg_xml  <- xml2::read_xml(svg_file)
  ns       <- xml2::xml_ns(svg_xml)
  paths_xml <- xml2::xml_find_all(svg_xml, ".//svg:path", ns)

  # Build a lookup table of elem_idx to svg_title
  path_lookup <- data.frame(
    elem_idx  = seq_along(paths_xml),
    svg_title = vapply(paths_xml, function(p) {
      t <- xml2::xml_find_first(p, "./svg:title", ns)
      if (inherits(t, "xml_missing")) NA_character_ else xml2::xml_text(t)
    }, character(1)),
    stringsAsFactors = FALSE
  )
  path_lookup <- path_lookup[!is.na(path_lookup$svg_title), ]

  atlas_ordering$svg_title <- paste(
    atlas_ordering$region, atlas_ordering$face, atlas_ordering$Hemisphere, sep = "_"
  )

  matched <- dplyr::left_join(atlas_ordering, path_lookup, by = "svg_title")
  matched <- matched[!is.na(matched$elem_idx), ]

  # Select only the columns we need for plotting and joining with svg_df
  keep_cols <- intersect(
    c("elem_idx", "region", "Hemisphere", "face", "plot_order", "fill_var", "p_value", "line_thickness_val"),
    names(matched)
  )
  result <- dplyr::inner_join(svg_df, matched[, keep_cols], by = "elem_idx")
  result$group_id <- result$elem_idx
  result
}


#     Hybrid plot helper for atlases like the Brainstem Navigator that have some midline (bilateral) regions.
# SVG naming conventions handled here:
#   - medial / lateral views --> individual files: Brainstem_Navigator_{H}_{view}.svg
#   - superior / inferior views (hemisphere="both") --> combined file: Brainstem_Navigator_both_{view}.svg
#   - superior / inferior views (hemisphere="L"/"R") --> individual files: Brainstem_Navigator_{H}_{view}.svg
# This method is designed for Brainstem_Navigator but could be used for any atlas that uses the same SVG structure and title convention.
.read_atlas_data <- function(atlas_ordering, atlas, data_dir, views, hemisphere) {
  LM_VIEWS     <- c("medial", "lateral")
  SI_VIEWS     <- c("superior", "inferior")

  if (hemisphere == "both") {
    # The Brainstem_Navigator atlas uses the same SVG files for both
    # hemispheres, so we load all four LM views and filter them by
    # the requested views. For SI views, it uses combined SVGs for both
    # hemispheres (both_superior.svg, both_inferior.svg), so we override
    # the per-hemisphere SI panels below to load those instead.
    ordered_lm <- list(c("L","medial"), c("L","lateral"), c("R","lateral"), c("R","medial"))
    lm_panels  <- ordered_lm[sapply(ordered_lm, `[[`, 2) %in% views]
    si_panels  <- lapply(SI_VIEWS[SI_VIEWS %in% views], function(v) c("both", v))
  } else {
    ORDERED_LM <- list(c("L","medial"), c("L","lateral"), c("R","lateral"), c("R","medial"))
    lm_panels  <- ORDERED_LM[sapply(ORDERED_LM, function(p) p[[1]] == hemisphere && p[[2]] %in% views)]
    si_panels  <- lapply(SI_VIEWS[SI_VIEWS %in% views], function(v) c(hemisphere, v))
  }

  .read_one_SVG <- function(svg_file, df_panel) {
    if (!file.exists(svg_file)) {
      warning(paste("Brainstem SVG not found:", svg_file))
      return(NULL)
    }

    svg_df <- suppressMessages(tryCatch(
      svgparser::read_svg(svg_file, obj_type = "data.frame"),
      error = function(e) { warning(paste("Could not parse:", svg_file)); NULL }
    ))
    if (is.null(svg_df) || nrow(svg_df) == 0) return(NULL)

    svg_xml  <- xml2::read_xml(svg_file)
    ns       <- xml2::xml_ns(svg_xml)
    paths_xml <- xml2::xml_find_all(svg_xml, ".//svg:path", ns)

    path_lookup <- data.frame(
      elem_idx  = seq_along(paths_xml),
      svg_title = vapply(paths_xml, function(p) {
        t <- xml2::xml_find_first(p, "./svg:title", ns)
        if (inherits(t, "xml_missing")) NA_character_ else xml2::xml_text(t)
      }, character(1)),
      stringsAsFactors = FALSE
    )
    path_lookup <- path_lookup[!is.na(path_lookup$svg_title), ]

    df_panel$svg_title <- paste(
      df_panel$region, df_panel$face, .normalise_hemi(df_panel$Hemisphere), sep = "_"
    )

    matched <- dplyr::left_join(df_panel, path_lookup, by = "svg_title")
    matched <- matched[!is.na(matched$elem_idx), ]

    keep_cols <- intersect(
      c("elem_idx", "region", "Hemisphere", "face", "plot_order", "fill_var", "p_value", "line_thickness_val"),
      names(matched)
    )
    result <- dplyr::inner_join(svg_df, matched[, keep_cols], by = "elem_idx")
    result$group_id <- result$elem_idx
    result
  }

  all_panels_data <- list()

  for (panel in c(lm_panels, si_panels)) {
    panel_hemi <- panel[[1]]
    view       <- panel[[2]]

    svg_file <- file.path(data_dir,
                          paste0(atlas, "_", panel_hemi, "_", view, ".svg"))

    if (panel_hemi == "both") {
      df_panel <- atlas_ordering[atlas_ordering$face == view, ]
    } else {
      hemi_mask <- atlas_ordering$Hemisphere == panel_hemi |
                   atlas_ordering$Hemisphere == paste0("B", panel_hemi) |
                   atlas_ordering$Hemisphere == "B"
      df_panel  <- atlas_ordering[hemi_mask & atlas_ordering$face == view, ]
    }
    df_panel <- df_panel[order(df_panel$plot_order), ]

    panel_df <- .read_one_SVG(svg_file, df_panel)
    if (!is.null(panel_df) && nrow(panel_df) > 0) {
      panel_df$panel_hemi <- panel_hemi
      panel_df$view       <- view
      all_panels_data[[length(all_panels_data) + 1]] <- panel_df
    }
  }

  if (length(all_panels_data) == 0) return(NULL)
  dplyr::bind_rows(all_panels_data)
}


# ---------------------------------------------------------------------------
# Single-panel plot builder
# ---------------------------------------------------------------------------

# Build a ggplot for one view panel given pre-filtered polygon data.
# fill_scale is a ggplot2 scale object from resolve_fill_scale().
# Per-region line thickness is read from panel_data$line_thickness_val.
# line_thickness_per_region: when TRUE (column-supplied values), nonsig regions use
#   line_thickness_val directly; when FALSE (scalar), nonsig gets 0.25 * line_thickness_val.
.build_panel_plot <- function(panel_data, fill_scale,
                              fill_by_significance, fill_alpha,
                              nonsig_fill_alpha, line_color,
                              line_thickness_per_region = FALSE) {
  if (is.null(panel_data) || nrow(panel_data) == 0) {
    return(patchwork::plot_spacer())
  }

  if (!"line_thickness_val" %in% names(panel_data)) {
    panel_data$line_thickness_val <- 0.5
  }

  p <- ggplot2::ggplot()

  for (po in sort(unique(panel_data$plot_order))) {
    df_po <- panel_data[panel_data$plot_order == po, ]

    # If fill_by_significance is TRUE and a p_value column exists,
    # split the data into significant and non-significant subsets
    # and plot them separately with different alphas and line thickness values.
    if (fill_by_significance && "p_value" %in% names(df_po)) {
      nonsig <- df_po[!is.na(df_po$p_value) & df_po$p_value >= 0.05, ]
      sig    <- df_po[is.na(df_po$p_value)  | df_po$p_value < 0.05,  ]

      if (nrow(nonsig) > 0) {
        # White backing so the transparent color reads against white, not the canvas
        p <- p + ggplot2::geom_polygon(
          data = nonsig,
          ggplot2::aes(x = x, y = y, group = group_id),
          fill = "white", colour = NA, linewidth = 0
        )
        nonsig_lw_aes <- if (line_thickness_per_region) {
          ggplot2::aes(x = x, y = y, fill = fill_var, group = group_id,
                       linewidth = line_thickness_val)
        } else {
          ggplot2::aes(x = x, y = y, fill = fill_var, group = group_id,
                       linewidth = 0.25 * line_thickness_val)
        }
        p <- p + ggplot2::geom_polygon(
          data    = nonsig,
          mapping = nonsig_lw_aes,
          colour  = line_color,
          alpha   = nonsig_fill_alpha
        )
      }
      if (nrow(sig) > 0) {
        p <- p + ggplot2::geom_polygon(
          data = sig,
          ggplot2::aes(x = x, y = y, fill = fill_var, group = group_id,
                       linewidth = line_thickness_val),
          colour = line_color,
          alpha  = fill_alpha
        )
      }
    } else {
      p <- p + ggplot2::geom_polygon(
        data = df_po,
        ggplot2::aes(x = x, y = y, fill = fill_var, group = group_id,
                     linewidth = line_thickness_val),
        colour = line_color,
        alpha  = fill_alpha
      )
    }
  }

  p +
    fill_scale +
    ggplot2::scale_linewidth_identity() +
    ggplot2::scale_y_reverse() +
    ggplot2::coord_fixed() +
    ggplot2::theme_void()
}


# ---------------------------------------------------------------------------
# Multi-panel assembly helper
# ---------------------------------------------------------------------------

# Arrange multiple view panels (individual atlas or Brainstem_Navigator) into a patchwork.
.assemble_panels <- function(atlas_paths, hemisphere, views,
                             atlas_type = "individual", fill_scale,
                             fill_alpha, line_color, fill_by_significance,
                             nonsig_fill_alpha,
                             line_thickness_per_region = FALSE) {
  LM_VIEWS <- c("medial", "lateral")
  SI_VIEWS <- c("superior", "inferior")

  # Determine ordered panel list (mirrors Python"s BOTH_VIEW_ORDER / SINGLE_VIEW_ORDER)
  if (hemisphere == "both") {
    BOTH_ORDER <- list(
      c("L", "medial"), c("L", "lateral"),
      c("R", "lateral"), c("R", "medial"),
      c("L", "superior"), c("R", "superior"),
      c("R", "inferior"), c("L", "inferior")
    )
    all_panels <- BOTH_ORDER[sapply(BOTH_ORDER, function(p) p[[2]] %in% views)]
  } else {
    VIEW_ORDER <- list(
      L = c("medial", "lateral", "superior", "inferior"),
      R = c("lateral", "medial", "superior", "inferior")
    )
    ordered_v  <- VIEW_ORDER[[hemisphere]][VIEW_ORDER[[hemisphere]] %in% views]
    all_panels <- lapply(ordered_v, function(v) c(hemisphere, v))
  }

  lm_panels  <- all_panels[sapply(all_panels, function(p) p[[2]] %in% LM_VIEWS)]

  # "combined" atlas (e.g., Brainstem_Navigator): superior/inferior with hemisphere="both" uses a single combined SVG
  # (both_superior/inferior.svg) stored under panel_hemi="both", so override the
  # per-hemisphere si_panels produced by BOTH_ORDER above.
  if (atlas_type == "combined" && hemisphere == "both") {
    si_panels <- lapply(SI_VIEWS[SI_VIEWS %in% views], function(v) c("both", v))
  } else {
    si_panels <- all_panels[sapply(all_panels, function(p) p[[2]] %in% SI_VIEWS)]
  }

  has_lm     <- length(lm_panels) > 0
  has_si     <- length(si_panels) > 0
  two_rows   <- (hemisphere == "both") && has_lm && has_si

  # Filter polygon data for one panel and build its ggplot
  make_one_panel <- function(panel_hemi, view) {
    if (is.null(atlas_paths)) return(patchwork::plot_spacer())

    if (atlas_type == "combined") {
      df_panel <- atlas_paths[atlas_paths$panel_hemi == panel_hemi &
                              atlas_paths$view       == view, ]
    } else {
      if (hemisphere == "both") {
        hemi_mask <- atlas_paths$Hemisphere %in%
                     c(panel_hemi, paste0("B", panel_hemi), "B")
        df_panel  <- atlas_paths[hemi_mask & atlas_paths$face == view, ]
      } else {
        hemi_mask <- atlas_paths$Hemisphere %in%
                     c(hemisphere, paste0("B", hemisphere))
        df_panel  <- atlas_paths[hemi_mask & atlas_paths$face == view, ]
      }
    }

    .build_panel_plot(panel_data=df_panel, fill_scale=fill_scale,
                      fill_by_significance = fill_by_significance, 
                      fill_alpha = fill_alpha, nonsig_fill_alpha = nonsig_fill_alpha,
                      line_color = line_color, line_thickness_per_region = line_thickness_per_region)
  }

  if (two_rows) {
    n_cols    <- max(length(lm_panels), length(si_panels))
    top_plots <- lapply(lm_panels, function(p) make_one_panel(p[[1]], p[[2]]))
    bot_plots <- lapply(si_panels, function(p) make_one_panel(p[[1]], p[[2]]))

    # Pad the shorter row with spacers so column widths align
    while (length(top_plots) < n_cols) top_plots <- c(top_plots, list(patchwork::plot_spacer()))
    while (length(bot_plots) < n_cols) bot_plots <- c(bot_plots, list(patchwork::plot_spacer()))

    top_row <- patchwork::wrap_plots(top_plots, nrow = 1)
    bot_row <- patchwork::wrap_plots(bot_plots, nrow = 1)
    top_row / bot_row
  } else {
    patchwork::wrap_plots(
      lapply(all_panels, function(p) make_one_panel(p[[1]], p[[2]])),
      nrow = 1
    )
  }
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

#' Visualize a given subcortical or cerebellar atlas template as a vector graphic, colored according to user-provided data values or, by default, a simple region-based color scheme.
#'
#' @param subcortex_data Optional data.frame with columns \code{region}, \code{Hemisphere},
#'   and \code{value_column}. If NULL, regions will be simply colored based on their assigned
#'   index in the corresponding atlas. May also include a \code{p_value} column if
#'   \code{fill_by_significance = TRUE}.
#' @param atlas The atlas used for the subcortical regions. Default is \code{"aseg_subcortex"}.
#'   One of \code{"aseg_subcortex"}, \code{"CIT168_subcortex"}, \code{"Melbourne_S1"} (or
#'   \code{"Tian_S1"}), \code{"AICHA_subcortex"}, \code{"Brainnetome_subcortex"},
#'   \code{"Thalamus_HCP"}, \code{"Thalamus_THOMAS"}, \code{"Brainstem_Navigator"},
#'   \code{"SUIT_cerebellar_lobule"}.
#' @param value_column The name of the column in \code{subcortex_data} that contains the
#'   values to be visualized.
#' @param hemisphere Which hemisphere(s) to display. Use \code{"L"} for left, \code{"R"} for
#'   right, or \code{"both"} for bilateral plots.
#' @param views Which faces of the subcortical regions to display. Options include
#'   \code{"medial"}, \code{"lateral"}, \code{"superior"}, and \code{"inferior"}.
#'   Not applicable to the SUIT cerebellar lobule atlas.
#' @param line_color Color of the outline around each subcortical region. Default is
#'   \code{"black"}.
#' @param line_thickness Thickness of the outline for each region in ggplot2 \code{linewidth}
#'   units, or a column name in \code{subcortex_data} whose value gives region-specific
#'   thickness. Default is \code{0.5}.
#' @param cmap Colormap used to fill in the regions. Accepts a viridis palette name (single
#'   string), a vector of hex colors, or a palette function. Default is \code{"viridis"}.
#' @param NA_fill Color to use for regions with missing data (NA values). Default is
#'   \code{"#cccccc"}.
#' @param fill_alpha Opacity level for the filled regions, between 0 (transparent) and 1
#'   (opaque). Default is \code{1.0}.
#' @param fill_by_significance If TRUE, adjusts fill opacity based on significance.
#'   Non-significant regions (\code{p_value >= 0.05}) are drawn at \code{nonsig_fill_alpha}
#'   over a white backing, with thinner outlines. Requires a \code{p_value} column in
#'   \code{subcortex_data}. Default is \code{FALSE}.
#' @param nonsig_fill_alpha If \code{fill_by_significance} is TRUE, this opacity level is
#'   applied to non-significant regions (p >= 0.05). Default is \code{0.5}.
#' @param vmin Minimum value for colormap normalization. If NULL, the minimum of the input
#'   values is used.
#' @param vmax Maximum value for colormap normalization. If NULL, the maximum of the input
#'   values is used.
#' @param midpoint If provided, uses a diverging colormap centered around this value.
#' @param show_legend If TRUE, displays a legend or colorbar indicating the mapping of values
#'   to colors.
#' @param fill_title Label for the colorbar indicating the meaning of the fill values.
#'   Default is \code{"values"}.
#' @param fontsize Font size for the figure text elements. Default is \code{12}.
#' @return A \pkg{patchwork} / ggplot2 object.
#' @export
plot_subcortical_data <- function(subcortex_data      = NULL,
                                   atlas               = "aseg_subcortex",
                                   value_column        = "value",
                                   hemisphere          = "L",
                                   views               = c("medial", "lateral"),
                                   line_color          = "black",
                                   line_thickness      = 0.5,
                                   cmap                = "viridis",
                                   NA_fill             = "#cccccc",
                                   fill_alpha          = 1.0,
                                   fill_by_significance = FALSE,
                                   nonsig_fill_alpha   = 0.5,
                                   vmin                = NULL,
                                   vmax                = NULL,
                                   midpoint            = NULL,
                                   show_legend         = TRUE,
                                   fill_title          = "values",
                                   fontsize            = 12) {

  # Tian → Melbourne alias
  atlas <- gsub("Tian", "Melbourne", atlas)

  # SUIT only supports "both"
  if (atlas == "SUIT_cerebellar_lobule" && hemisphere != "both") {
    message("Individual-hemisphere visualisation is not supported for SUIT_cerebellar_lobule. Switching to hemisphere='both'.")
    hemisphere <- "both"
  }

  # If fill_by_significance is TRUE, ensure that "p_value" column is present in subcortex_data
  if (fill_by_significance) {
    if (is.null(subcortex_data) || !("p_value" %in% names(subcortex_data))) {
      stop("fill_by_significance=TRUE requires a 'p_value' column in subcortex_data.")
    }
  }

  # ── Load ordering CSV and merge with user data ─────────────────────────────
  tryCatch({
      prepped       <- .prep_data(atlas          = atlas,
                              hemisphere     = hemisphere,
                              subcortex_data = subcortex_data,
                              value_column   = value_column)
  }, error = function(e) {
    tryCatch({
      # try appending "_subcortex" if not already present
      atlas <- paste0(atlas, "_subcortex")
      prepped       <- .prep_data(atlas          = atlas,
                              hemisphere     = hemisphere,
                              subcortex_data = subcortex_data,
                              value_column   = value_column)
      print(paste("Warning: initial data preparation failed; successfully loaded with atlas name", atlas))
    }, error = function(e2) {
      stop(paste("Error preparing data with atlas", atlas, 
                 "and hemisphere", hemisphere, ":", e$message, 
                 "; also tried atlas", paste0(atlas, "_subcortex"), ":", e2$message))
    })
  })

  atlas_ordering <- prepped$atlas_ordering
  region_order   <- prepped$region_order
  discrete       <- is.null(subcortex_data)

  # Compute continuous scale limits
  if (!discrete) {
    fill_values <- atlas_ordering$fill_var
    if (!is.null(midpoint)) {
      max_dev <- max(abs(fill_values - midpoint), na.rm = TRUE)
      if (is.null(vmin)) vmin <- midpoint - max_dev
      if (is.null(vmax)) vmax <- midpoint + max_dev
    } else {
      if (is.null(vmin)) vmin <- min(fill_values, na.rm = TRUE)
      if (is.null(vmax)) vmax <- max(fill_values, na.rm = TRUE)
    }
  }

  fill_scale <- .resolve_fill_scale(
    atlas_ordering = atlas_ordering,
    cmap           = cmap,
    discrete       = discrete,
    region_order   = region_order,
    NA_fill        = NA_fill,
    vmin           = vmin,
    vmax           = vmax,
    midpoint       = midpoint
  )

  # Resolve line_thickness into per-row values and a flag used by .build_panel_plot.
  # line_thickness_per_region = TRUE  → column supplied; nonsig regions keep full thickness.
  # line_thickness_per_region = FALSE → scalar; nonsig regions get 0.25 * scalar thickness.
  line_thickness_per_region <- FALSE
  if (is.character(line_thickness) && length(line_thickness) == 1) {
    if (line_thickness %in% names(atlas_ordering)) {
      atlas_ordering$line_thickness_val <- atlas_ordering[[line_thickness]]
      line_thickness_per_region <- TRUE
    } else {
      warning(paste0("`line_thickness` column '", line_thickness, "' not found in data; defaulting to 0.5"))
      atlas_ordering$line_thickness_val <- 0.5
    }
  } else {
    atlas_ordering$line_thickness_val <- as.numeric(line_thickness)
  }

  # ── Load SVG path data and build the assembled plot ────────────────────────
  if (atlas == "SUIT_cerebellar_lobule") {
    svg_file <- system.file("extdata", "data", atlas,
                            paste0(atlas, "_", hemisphere, ".svg"),
                            package = "subcortexVisualizationR")
    df_panel <- .read_SUIT_data(atlas_ordering, svg_file)
    final_plot  <- .build_panel_plot(panel_data=df_panel, fill_scale=fill_scale,
                      fill_by_significance = fill_by_significance, 
                      fill_alpha = fill_alpha, nonsig_fill_alpha = nonsig_fill_alpha,
                      line_color = line_color, line_thickness_per_region = line_thickness_per_region)

  } else if (atlas == "Brainstem_Navigator") {
    data_dir    <- system.file("extdata", "data", atlas, package = "subcortexVisualizationR")
    atlas_paths <- .read_atlas_data(atlas_ordering, atlas, data_dir, views, hemisphere)
    final_plot  <- .assemble_panels(
      atlas_paths=atlas_paths, hemisphere=hemisphere,
      views=views, atlas_type="combined", fill_scale=fill_scale,
      fill_alpha=fill_alpha, line_color=line_color,
      fill_by_significance = fill_by_significance,
      nonsig_fill_alpha = nonsig_fill_alpha,
      line_thickness_per_region = line_thickness_per_region)

  } else {
    svg_dir     <- system.file("extdata", "data", atlas, "vectors",
                               package = "subcortexVisualizationR")
    atlas_paths <- .read_individual_atlas_data(atlas_ordering, svg_dir, views)
    final_plot  <- .assemble_panels(
      atlas_paths=atlas_paths, fill_scale=fill_scale,
      fill_by_significance=fill_by_significance, fill_alpha=fill_alpha, nonsig_fill_alpha=nonsig_fill_alpha,
      line_color=line_color,
      hemisphere=hemisphere, views=views,
      atlas_type = "individual",
      line_thickness_per_region = line_thickness_per_region
    )
  }

  # ── Legend ─────────────────────────────────────────────────────────────────
  legend_theme <- ggplot2::theme(
    legend.position = "bottom",
    legend.title    = ggplot2::element_text(size = fontsize),
    legend.text     = ggplot2::element_text(size = fontsize)
  )

  if (show_legend) {
    guide <- if (discrete) {
      ggplot2::guides(fill = ggplot2::guide_legend(
        title.position = "top", title.hjust = 0.5
      ))
    } else {
      ggplot2::guides(fill = ggplot2::guide_colorbar(
        title.position = "top", title.hjust = 0.5, barwidth=unit(5, "cm"), barheight=unit(0.5, "cm")
      ))
    }

    if (discrete) {
      # guides="collect" doesn"t reliably deduplicate identical discrete legends
      # across panels. Build a standalone legend via a helper ggplot (geom_col
      # with y=0 renders no visible bar but still fires the fill scale, giving
      # filled-rectangle keys), then append it below the main panels. Using the
      # full ggplot (not a grob) avoids device side-effects in Jupyter/IRkernel.
      legend_gg <- ggplot2::ggplot(
          data.frame(x = seq_along(region_order), y = 0, fill_var = region_order),
          ggplot2::aes(x = x, y = y, fill = fill_var)
        ) +
        ggplot2::geom_col() +
        fill_scale +
        ggplot2::labs(fill = fill_title) +
        ggplot2::theme_void() +
        ggplot2::theme(
          legend.position  = "top",
          legend.title     = ggplot2::element_text(size = fontsize),
          legend.text      = ggplot2::element_text(size = fontsize)
        ) +
        guide

      final_plot <- patchwork::wrap_plots(
        final_plot & ggplot2::labs(fill = fill_title) & ggplot2::theme(legend.position = "none"),
        legend_gg,
        ncol    = 1,
        heights = c(9, 1)
      )
    } else {
      # Same helper-ggplot approach as discrete: geom_col with y=0 fires the
      # continuous fill scale (producing a colorbar) while rendering no visible
      # bar. Appending it below guarantees the colorbar spans the full width.
      legend_gg <- ggplot2::ggplot(
          data.frame(x = c(0, 1), y = c(0, 0), fill_var = c(vmin, vmax)),
          ggplot2::aes(x = x, y = y, fill = fill_var)
        ) +
        ggplot2::geom_col() +
        fill_scale +
        ggplot2::labs(fill = fill_title) +
        ggplot2::theme_void() +
        ggplot2::theme(
          legend.position  = "top",
          legend.title     = ggplot2::element_text(size = fontsize),
          legend.text      = ggplot2::element_text(size = fontsize)
        ) +
        guide

      final_plot <- patchwork::wrap_plots(
        final_plot & ggplot2::labs(fill = fill_title) & ggplot2::theme(legend.position = "none"),
        legend_gg,
        ncol    = 1,
        heights = c(9, 1)
      )
    }
  } else {
    final_plot <- final_plot &
      ggplot2::theme(legend.position = "none")
  }

  final_plot
}
