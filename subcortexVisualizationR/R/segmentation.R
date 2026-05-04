#' Extract voxel values from an input volume based on a parcellation atlas and apply a reduction function to each parcel.
#'
#' @param input_vol The input 3D or 4D NIfTI image from which to extract voxel values.
#'   Can be an RNifti object or a file path to a NIfTI image.
#' @param atlas_space The standard space to use for the corresponding atlas. Options include
#'   \code{'MNI152NLin6Asym'} (the default) and \code{'MNI152NLin2009cAsym'}.
#' @param atlas Name(s) of the subcortical atlas/atlases to apply. Default is
#'   \code{'aseg_subcortex'}. If multiple atlases are provided as a list, the function will
#'   iterate over them and concatenate results.
#' @param func_name A name for the functional map being summarized, used for labeling purposes
#'   in the output data frame. Default is \code{'Functional map'}.
#' @param parc_stat A function like \code{mean}, \code{sd}, etc. that takes an array of values
#'   and returns a single summary statistic (scalar). Default is \code{mean}. Can also be a
#'   list of functions, in which case the output data frame will have one row per parcel per
#'   summary statistic.
#' @param ignore_background If TRUE, the background label (as defined by
#'   \code{background_value}) is skipped when extracting parcel values. Default is \code{TRUE}.
#' @param background_value Integer label in the parcellation that represents background
#'   (non-parcel) voxels. Default is \code{0}.
#' @param interpolation If the input volume and atlas have different affines or spatial
#'   dimensions, this parameter specifies the interpolation method for resampling the atlas to
#'   match the input volume. Options include \code{'nearest'}, \code{'linear'}, and
#'   \code{'cubic'}. If NULL (default), no resampling is performed and an error will be raised
#'   if affines or dimensions do not match.
#' @return A data frame with one row per parcel per summary statistic, with columns:
#'   \code{stat}, \code{value}, \code{Atlas}, \code{Functional_Map}, \code{region},
#'   \code{Hemisphere}, \code{Region_Index}.
#' @note Users should ensure that the input volume is in the same standard space as the atlas
#'   specified by \code{atlas_space} to avoid issues with affine and spatial dimension
#'   mismatches. If resampling is necessary, users must specify an interpolation method.
#' @importFrom RNifti readNifti xform
#' @export
parcel_segstats <- function(input_vol, atlas_space='MNI152NLin6Asym',
                            atlas='aseg_subcortex', func_name='Functional map', parc_stat=mean,
                            ignore_background=TRUE, background_value=0, interpolation=NULL) {
  
  # Capture parc_stat function name(s) before any transformations
  parc_stat_expr <- substitute(parc_stat)
  if (is.list(parc_stat)) {
    if (!is.null(names(parc_stat))) {
      parc_stat_names <- names(parc_stat)
    } else {
      parc_stat_names <- sapply(as.list(parc_stat_expr)[-1], function(x) {
        gsub('^"|"$', '', deparse(x))
      })
    }
  } else {
    parc_stat_names <- if (is.character(parc_stat)) parc_stat else deparse(parc_stat_expr)
  }
  
  if (is.character(atlas)) {
    atlas <- as.list(atlas)
  }
  
  if (!is.list(parc_stat)) {
    parc_stat <- list(parc_stat)
  }
  parc_stat <- lapply(parc_stat, match.fun)
  
  # Load in the input volume, if it's a file path
  if (is.character(input_vol)) {
    input_vol_ANTS <- ANTsR::antsImageRead(input_vol)
    input_vol <- readNifti(input_vol)
  } else {
    input_vol_ANTS <- extrantsr::oro2ants(input_vol)
  }
  
  # Find the affine and input data dimensions
  input_affine <- xform(input_vol)
  input_data <- as.array(input_vol)
  
  # Initialize list to hold results dataframes for each atlas
  results_df_list <- list()
  
  # Iterate over user-specified atlas(es)
  for (this_atlas in atlas) {
    
    if (this_atlas == 'Brainstem_Navigator') {
      # One NIFTI file per ROI — discover all .nii.gz files in the atlas directory
      atlas_dir <- system.file("extdata", "atlases", atlas_space, this_atlas, package="subcortexVisualizationR")
      nifti_files <- sort(list.files(atlas_dir, pattern="\\.nii\\.gz$", full.names=TRUE))
      
      for (roi_idx in seq_along(nifti_files)) {
        nifti_path <- nifti_files[roi_idx]
        roi_name <- sub("\\.nii\\.gz$", "", basename(nifti_path))
        roi_vol <- readNifti(nifti_path)
        roi_vol_affine <- xform(roi_vol)
        
        if (!isTRUE(all.equal(input_affine, roi_vol_affine, tolerance=1e-5))) {
          if (!is.null(interpolation)) {
            message(sprintf("Resampling ROI '%s' to match input data affine and dimensions using %s interpolation...", roi_name, interpolation))
            
            # Apply the resampleImage function from ANTsR, imagetype=0 specifies data are scalar values
            this_ROI_vol_ANTS <- extrantsr::oro2ants(roi_vol)
            this_ROI_vol_ANTS_resampled <- ANTsR::resampleImageToTarget(image=this_ROI_vol_ANTS, target=input_vol_ANTS, 
                                                                        interpType = interpolation, imagetype=0)
            
            # Set the resampled ANTS volume as the ROI volume
            roi_vol <- extrantsr::ants2oro(this_ROI_vol_ANTS_resampled)
          } else {
            stop(sprintf(
              "No resampling method was specified. Re-run this function with a specified 'interpolation' argument to resample ROI '%s' to your input data.\nInput data affine:\n%s\nROI affine:\n%s\n",
              roi_name,
              paste(apply(round(input_affine, 4), 1, paste, collapse=" "), collapse="\n"),
              paste(apply(round(roi_vol_affine, 4), 1, paste, collapse=" "), collapse="\n")
            ))
          }
        }
        
        roi_data <- as.array(roi_vol)
        mask <- roi_data != 0
        
        if (!all(dim(input_data)[1:3] == dim(roi_data)[1:3])) {
          min_shape <- pmin(dim(input_data)[1:3], dim(roi_data)[1:3])
          input_data_roi <- input_data[1:min_shape[1], 1:min_shape[2], 1:min_shape[3], drop=FALSE]
          mask <- mask[1:min_shape[1], 1:min_shape[2], 1:min_shape[3]]
        } else {
          input_data_roi <- input_data
        }
        
        if (length(dim(input_data_roi)) == 4) {
          n_t <- dim(input_data_roi)[4]
          input_flat <- matrix(input_data_roi, nrow=prod(dim(input_data_roi)[1:3]), ncol=n_t)
          voxels <- input_flat[as.vector(mask), , drop=FALSE]
          vals <- sapply(parc_stat, function(s) apply(voxels, 2, s))
        } else {
          voxels <- input_data_roi[mask]
          vals <- sapply(parc_stat, function(s) s(voxels))
        }
        
        this_lab_df <- data.frame(
          stat = parc_stat_names,
          value = vals,
          stringsAsFactors = FALSE
        )
        
        # Determine hemisphere from ROI name suffix
        this_hemi <- 'B'
        if (grepl("(_lh|-lh|-L|_L|_l)$", roi_name)) {
          this_hemi <- 'L'
        } else if (grepl("(_rh|-rh|-R|_R|_r)$", roi_name)) {
          this_hemi <- 'R'
        } else if (grepl("vermis", roi_name)) {
          this_hemi <- 'V'
        }
        
        this_region_clean <- sub("(_lh|-lh|-L|_L|_l|_rh|-rh|-R|_R|_r|-vermis)$", "", roi_name)
        
        this_lab_df$Atlas <- this_atlas
        this_lab_df$Functional_Map <- func_name
        this_lab_df$region <- this_region_clean
        this_lab_df$Hemisphere <- this_hemi
        this_lab_df$Region_Index <- roi_idx
        
        results_df_list <- c(results_df_list, list(this_lab_df))
      }
      
    } else {
      # Define atlas volume path
      atlas_vol_path <- system.file("extdata", "atlases", atlas_space, this_atlas, paste0(this_atlas, ".nii.gz"), package="subcortexVisualizationR")
      atlas_lut_path <- system.file("extdata", "atlases", atlas_space, this_atlas, paste0(this_atlas, "_lookup.csv"), package="subcortexVisualizationR")
      
      # Try loading atlas; if that fails, append _subcortex and try again
      if (atlas_vol_path == "" || !file.exists(atlas_vol_path)) {
        atlas_vol_path <- system.file("extdata", "atlases", atlas_space, this_atlas, paste0(this_atlas, "_subcortex.nii.gz"), package="subcortexVisualizationR")
        atlas_vol_path <- system.file("extdata", "atlases", atlas_space, this_atlas, paste0(this_atlas, "_subcortex_lookup.csv"), package="subcortexVisualizationR")
        
        if (atlas_vol_path == "" || !file.exists(atlas_vol_path)) {
          stop(sprintf(
            "Atlas volume file not found for atlas '%s'. Looked for files named '%s.nii.gz' and '%s_subcortex.nii.gz' in the subcortexVisualizationR package's atlases directory. Please check that the atlas name is correct and that the corresponding atlas volume file is present in the package directory.",
            this_atlas, this_atlas, this_atlas
          ))
        }
        
        warning(sprintf(
          "Atlas volume file for atlas '%s' not found with expected filename '%s.nii.gz'. Successfully loaded atlas volume with alternative filename '%s_subcortex.nii.gz'. Please check that the atlas volume file in the package directory is named according to one of these two conventions to avoid this warning in the future.",
          this_atlas, this_atlas, this_atlas
        ))
      }
      
      # Load atlas volume and LUT
      this_atlas_vol <- readNifti(atlas_vol_path)
      this_atlas_LUT <- read.csv(atlas_lut_path, header=FALSE, stringsAsFactors=FALSE)
      
      # If first row has 'Region_Name' in any column, set column names to first row and drop it
      if (any(grepl("Region_Name", as.character(this_atlas_LUT[1, ])))) {
        colnames(this_atlas_LUT) <- as.character(this_atlas_LUT[1, ])
        this_atlas_LUT <- this_atlas_LUT[-1, , drop=FALSE]
        rownames(this_atlas_LUT) <- NULL
      }
      
      # Find affine
      this_atlas_vol_affine <- xform(this_atlas_vol)
      
      # Compare affines and raise error if they don't match
      if (!isTRUE(all.equal(input_affine, this_atlas_vol_affine, tolerance=1e-5))) {
        warning(sprintf(
          "Affines of input data and atlas do not match.\nAtlas affine:\n%s\nInput data affine:\n%s\n",
          paste(apply(round(this_atlas_vol_affine, 4), 1, paste, collapse=" "), collapse="\n"),
          paste(apply(round(input_affine, 4), 1, paste, collapse=" "), collapse="\n")
        ))
        
        if (!is.null(interpolation)) {
          message(sprintf("Resampling atlas '%s' to match input data affine and dimensions using %s interpolation...", this_atlas, interpolation))
          
          # Apply the resampleImage function from ANTsR, imagetype=0 specifies data are scalar values
          this_atlas_vol_ANTS <- extrantsr::oro2ants(this_atlas_vol)
          this_atlas_vol_ANTS_resampled <- ANTsR::resampleImageToTarget(image=this_atlas_vol_ANTS, target=input_vol_ANTS, 
                                                                        interpType = interpolation, imagetype=0)
          
          # Set the resampled ANTS volume as the atlas volume
          this_atlas_vol <- extrantsr::ants2oro(this_atlas_vol_ANTS_resampled)
          
        } else {
          stop(sprintf(
            "No resampling method was specified. Re-run this function with a specified 'interpolation' argument to resample the desired atlas volume to your input data.\nInput data affine:\n%s\nAtlas affine:\n%s\n",
            paste(apply(round(input_affine, 4), 1, paste, collapse=" "), collapse="\n"),
            paste(apply(round(this_atlas_vol_affine, 4), 1, paste, collapse=" "), collapse="\n")
          ))
        }
      }
      
      # Extract labels; round to nearest integer since resampling may produce non-integer values
      labels <- as.array(this_atlas_vol)
      labels <- round(labels)
      storage.mode(labels) <- "integer"
      
      # Check that first three dimensions match; crop to minimum shape if not
      if (!all(dim(input_data)[1:3] == dim(labels)[1:3])) {
        warning(sprintf(
          "Spatial dimensions of input data and atlas do not match. Input data shape: %s\nAtlas labels shape: %s\nAttempting to crop atlas labels to match input data dimensions...",
          paste(dim(input_data), collapse="x"),
          paste(dim(labels), collapse="x")
        ))
        tryCatch({
          min_shape <- pmin(dim(input_data)[1:3], dim(labels)[1:3])
          input_data <- input_data[1:min_shape[1], 1:min_shape[2], 1:min_shape[3], drop=FALSE]
          labels <- labels[1:min_shape[1], 1:min_shape[2], 1:min_shape[3]]
        }, error = function(e) {
          stop(sprintf(
            "Error occurred while attempting to crop atlas labels to match input data dimensions: %s\nUnable to proceed with extraction.",
            e$message
          ))
        })
      }
      
      colnames(this_atlas_LUT) <- c('Index', 'Region')
      this_atlas_regions <- this_atlas_LUT$Region
      unique_labels <- sort(unique(as.integer(labels)))
      
      # Skip background if requested, which is the default
      if (ignore_background) {
        unique_labels <- unique_labels[unique_labels != background_value]
      }
      
      # Iterate over each unique label and extract voxel values
      for (i in seq_along(unique_labels)) {
        lab <- unique_labels[i]
        mask <- labels == lab
        
        if (length(dim(input_data)) == 4) {
          n_t <- dim(input_data)[4]
          input_flat <- matrix(input_data, nrow=prod(dim(input_data)[1:3]), ncol=n_t)
          voxels <- input_flat[as.vector(mask), , drop=FALSE]
          vals <- sapply(parc_stat, function(s) apply(voxels, 2, s))
        } else {
          voxels <- input_data[mask]
          vals <- sapply(parc_stat, function(s) s(voxels))
        }
        
        # Create dataframe for vals, one row per summary statistic
        this_lab_df <- data.frame(
          stat = parc_stat_names,
          value = vals,
          stringsAsFactors = FALSE
        )
        
        this_atlas_region_full <- as.character(this_atlas_regions[i])
        
        # Determine hemisphere from region name suffix
        this_hemi <- 'B'
        if (grepl("(_lh|-lh|-L|_L|_l|_LH)$", this_atlas_region_full)) {
          this_hemi <- 'L'
        } else if (grepl("(_rh|-rh|-R|_R|_r|_RH)$", this_atlas_region_full)) {
          this_hemi <- 'R'
        } else if (grepl("vermis", this_atlas_region_full)) {
          this_hemi <- 'V'
        }
        
        # Remove hemisphere suffix from region name
        this_region_clean <- sub("(_lh|-lh|-L|_L|_l|_LH|_rh|-rh|-R|_R|_r|_RH|-vermis)$", "", this_atlas_region_full)
        
        this_lab_df$Atlas <- this_atlas
        this_lab_df$Functional_Map <- func_name
        this_lab_df$region <- this_region_clean
        this_lab_df$Hemisphere <- this_hemi
        this_lab_df$Region_Index <- lab
        
        results_df_list <- c(results_df_list, list(this_lab_df))
      }
    }
  }
  
  # Concatenate results from all atlases into a single data frame
  results_df <- do.call(rbind, results_df_list)
  rownames(results_df) <- NULL
  
  return(results_df)
}
