# Every built-in atlas renders without error for default parameters,
# including the 7T Melbourne Subcortex Atlas variants (S1-S4).

ALL_ATLASES <- c(
  "aseg_subcortex",
  "Melbourne_S1", "Melbourne_S2", "Melbourne_S3", "Melbourne_S4",
  "Melbourne_S1_7T", "Melbourne_S2_7T", "Melbourne_S3_7T", "Melbourne_S4_7T",
  "AICHA_subcortex",
  "Brainnetome_subcortex",
  "CIT168_subcortex",
  "Thalamus_HCP",
  "Thalamus_THOMAS",
  "Brainstem_Navigator",
  "SUIT_cerebellar_lobule"
)

test_that("every built-in atlas renders with default parameters", {
  for (atlas in ALL_ATLASES) {
    p <- plot_subcortical_data(atlas = atlas, show_legend = FALSE)
    expect_s3_class(p, "gg")
  }
})

test_that("Tian_S* is a backward-compatible alias for Melbourne_S*", {
  p <- plot_subcortical_data(atlas = "Tian_S1", show_legend = FALSE)
  expect_s3_class(p, "gg")
})

test_that("Tian_S*_7T is a backward-compatible alias for Melbourne_S*_7T", {
  p <- plot_subcortical_data(atlas = "Tian_S1_7T", show_legend = FALSE)
  expect_s3_class(p, "gg")
})

test_that("Melbourne 7T atlases render bilaterally", {
  for (scale in 1:4) {
    p <- plot_subcortical_data(
      atlas = paste0("Melbourne_S", scale, "_7T"),
      hemisphere = "both", show_legend = TRUE
    )
    expect_s3_class(p, "gg")
  }
})

test_that("get_atlas_regions returns non-empty, non-duplicated regions for Melbourne 7T atlases", {
  for (scale in 1:4) {
    regions <- get_atlas_regions(paste0("Melbourne_S", scale, "_7T"))
    expect_true(length(regions) > 0)
    expect_equal(length(regions), length(unique(regions)))
  }
})

test_that("Melbourne 7T region counts increase with scale", {
  counts <- sapply(1:4, function(scale) length(get_atlas_regions(paste0("Melbourne_S", scale, "_7T"))))
  expect_equal(counts, sort(counts))
})

test_that("Melbourne 7T region counts differ from the 3T atlas at the same scale", {
  counts_3t <- sapply(1:4, function(scale) length(get_atlas_regions(paste0("Melbourne_S", scale))))
  counts_7t <- sapply(1:4, function(scale) length(get_atlas_regions(paste0("Melbourne_S", scale, "_7T"))))
  expect_false(identical(counts_3t, counts_7t))
})

test_that("an unrecognized atlas name raises an error", {
  expect_error(
    suppressWarnings(plot_subcortical_data(atlas = "nonexistent_atlas_xyz", show_legend = FALSE))
  )
})
