# Tests for the discrete/categorical fill_domain support:
# - .prep_data() assigning fill_var from a categorical value_column
# - .resolve_fill_scale() mapping a fill_domain onto a discrete ggplot2 scale
# - plot_subcortical_data() end-to-end for string, character-sorted, ordered
#   factor, default (no data), and continuous data

small_ordering_df <- function() {
  data.frame(
    region     = c("thalamus", "putamen", "caudate"),
    hemisphere = c("L", "L", "L"),
    seg_index  = c(1, 2, 3),
    plot_order = c(1, 2, 3),
    face       = "medial"
  )
}

# ---------------------------------------------------------------------------
# .prep_data
# ---------------------------------------------------------------------------

test_that(".prep_data assigns fill_var from a character value_column", {
  subcortex_data <- data.frame(
    region = c("thalamus", "putamen", "caudate"),
    hemisphere = "L",
    value = c("A", "B", "A")
  )

  prepped <- subcortexVisualizationR:::.prep_data(
    atlas = "aseg_subcortex", hemisphere = "L",
    subcortex_data = subcortex_data, value_column = "value"
  )

  expect_true(is.character(prepped$atlas_ordering$fill_var))
  expect_setequal(unique(na.omit(prepped$atlas_ordering$fill_var)), c("A", "B"))
})

test_that(".prep_data preserves factor level order in fill_var", {
  subcortex_data <- data.frame(
    region = c("thalamus", "putamen", "caudate"),
    hemisphere = "L",
    value = factor(c("A", "B", "A"), levels = c("B", "A"))
  )

  prepped <- subcortexVisualizationR:::.prep_data(
    atlas = "aseg_subcortex", hemisphere = "L",
    subcortex_data = subcortex_data, value_column = "value"
  )

  expect_true(is.factor(prepped$atlas_ordering$fill_var))
  expect_equal(levels(prepped$atlas_ordering$fill_var), c("B", "A"))
})

test_that(".prep_data uses region as fill_var when subcortex_data is NULL", {
  prepped <- subcortexVisualizationR:::.prep_data(
    atlas = "aseg_subcortex", hemisphere = "L", subcortex_data = NULL
  )

  expect_equal(prepped$atlas_ordering$fill_var, prepped$atlas_ordering$region)
})

# ---------------------------------------------------------------------------
# .resolve_fill_scale
# ---------------------------------------------------------------------------

test_that(".resolve_fill_scale returns a discrete viridis scale over fill_domain", {
  sc <- subcortexVisualizationR:::.resolve_fill_scale(
    atlas_ordering = small_ordering_df(),
    cmap = "viridis",
    discrete = TRUE,
    fill_domain = c("A", "B", "C")
  )

  expect_s3_class(sc, "ScaleDiscrete")
  expect_equal(sc$limits, c("A", "B", "C"))
})

test_that(".resolve_fill_scale respects fill_domain order for a manual color vector", {
  sc <- subcortexVisualizationR:::.resolve_fill_scale(
    atlas_ordering = small_ordering_df(),
    cmap = c("#000000", "#ffffff", "#ff0000"),
    discrete = TRUE,
    fill_domain = c("C", "B", "A")
  )

  expect_s3_class(sc, "ScaleDiscrete")
  expect_equal(sc$limits, c("C", "B", "A"))
})

test_that(".resolve_fill_scale samples a palette function once per fill_domain entry", {
  cmap_fn <- function(n) grDevices::rainbow(n)

  sc <- subcortexVisualizationR:::.resolve_fill_scale(
    atlas_ordering = small_ordering_df(),
    cmap = cmap_fn,
    discrete = TRUE,
    fill_domain = c("A", "B")
  )

  expect_s3_class(sc, "ScaleDiscrete")
  expect_equal(sc$limits, c("A", "B"))
  expect_equal(sc$palette(2), cmap_fn(2))
})

# ---------------------------------------------------------------------------
# plot_subcortical_data end-to-end
# ---------------------------------------------------------------------------

discrete_subcortex_data <- function() {
  data.frame(
    region = c("thalamus", "putamen", "caudate", "pallidum",
               "hippocampus", "amygdala", "accumbens"),
    hemisphere = "L",
    value = c("A", "B", "A", "C", "B", "C", "A")
  )
}

fill_scale_limits <- function(plot) {
  plot[[1]]$scales$get_scales("fill")$get_limits()
}

test_that("plot_subcortical_data colors regions by category for character data", {
  p <- plot_subcortical_data(
    subcortex_data = discrete_subcortex_data(),
    atlas = "aseg_subcortex", value_column = "value",
    hemisphere = "L", show_legend = TRUE, fill_title = "Group"
  )

  expect_setequal(fill_scale_limits(p), c("A", "B", "C"))
})

test_that("plot_subcortical_data preserves factor level order for ordered categories", {
  df <- discrete_subcortex_data()
  df$value <- factor(df$value, levels = c("C", "B", "A"))

  p <- plot_subcortical_data(
    subcortex_data = df, atlas = "aseg_subcortex", value_column = "value",
    hemisphere = "L", show_legend = TRUE, fill_title = "Group"
  )

  expect_equal(fill_scale_limits(p), c("C", "B", "A"))
})

test_that("plot_subcortical_data falls back to per-region fill_domain with no data", {
  p <- plot_subcortical_data(
    subcortex_data = NULL, atlas = "aseg_subcortex",
    hemisphere = "L", show_legend = TRUE
  )

  expect_setequal(
    fill_scale_limits(p),
    c("thalamus", "caudate", "putamen", "pallidum",
      "hippocampus", "amygdala", "accumbens")
  )
})

test_that("plot_subcortical_data still uses a continuous scale for numeric data", {
  df <- discrete_subcortex_data()
  df$value <- seq_len(nrow(df))

  p <- plot_subcortical_data(
    subcortex_data = df, atlas = "aseg_subcortex", value_column = "value",
    hemisphere = "L", show_legend = TRUE
  )

  sc <- p[[1]]$scales$get_scales("fill")
  expect_s3_class(sc, "ScaleContinuous")
})
