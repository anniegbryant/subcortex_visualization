import numpy as np
import nibabel as nb
import pandas as pd
import os

# For inter-atlas alignment
import templateflow
import templateflow.api as tflow
import ants

# Find filepath to this file
input_volume_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(input_volume_path)

################################## aseg ##################################
# Load the .mgz file
aseg_input_volume = "aseg/aparc+aseg.mgz"
aseg_img = nb.load(aseg_input_volume)
aseg_data = aseg_img.get_fdata()

# Load the aseg LUT
aseg_LUT = pd.read_csv("aseg/aseg_subcortex_lookup.csv", header=None)
aseg_LUT.columns = ['Index', 'Region']

# Filter atlas_data to only include index values present in atlas_LUT.index
index_list = np.unique(aseg_LUT.Index)
index_list = index_list.astype(int)

# Filter to only include indices present in the LUT
aseg_data_filtered = np.isin(aseg_data, index_list) * aseg_data
aseg_data_filtered_img = nb.Nifti1Image(aseg_data_filtered, aseg_img.affine, aseg_img.header)

# Save to new file
nb.save(aseg_data_filtered_img, "aseg/aseg_subcortex.nii.gz")

####################### Melbourne subcortical atlas ######################

# Atlases are already filtered to the subcortex, 
# so we just need to extract out the right hemisphere for each

# S1
# Load in volume
S1_input_volume = "Melbourne_S1/Tian_Subcortex_S1_3T_1mm.nii.gz"
S1_img = nb.load(S1_input_volume)
S1_data = S1_img.get_fdata()

# Right-hemisphere subcortex range is 1-8
S1_subcortex_right_data = np.where((S1_data >= 1) & (S1_data <= 8), S1_data, 0)
S1_subcortex_right_img = nb.Nifti1Image(S1_subcortex_right_data, S1_img.affine, S1_img.header)
nb.save(S1_subcortex_right_img, "Melbourne_S1/Tian_Subcortex_S1_3T_1mm_R.nii.gz")

# S2 
# Load in volume
S2_input_volume = "Melbourne_S2/Tian_Subcortex_S2_3T_1mm.nii.gz"
S2_img = nb.load(S2_input_volume)
S2_data = S2_img.get_fdata()

# Right-hemisphere subcortex range is 1-16
S2_subcortex_right_data = np.where((S2_data >= 1) & (S2_data <= 16), S2_data, 0)
S2_subcortex_right_img = nb.Nifti1Image(S2_subcortex_right_data, S2_img.affine, S2_img.header)
nb.save(S2_subcortex_right_img, "Melbourne_S2/Tian_Subcortex_S2_3T_1mm_R.nii.gz")

# S3
# Load in volume
S3_input_volume = "Melbourne_S3/Tian_Subcortex_S3_3T_1mm.nii.gz"
S3_img = nb.load(S3_input_volume)
S3_data = S3_img.get_fdata()

# Right-hemisphere subcortex range is 1-25
S3_subcortex_right_data = np.where((S3_data >= 1) & (S3_data <= 25), S3_data, 0)
S3_subcortex_right_img = nb.Nifti1Image(S3_subcortex_right_data, S3_img.affine, S3_img.header)
nb.save(S3_subcortex_right_img, "Melbourne_S3/Tian_Subcortex_S3_3T_1mm_R.nii.gz")

# S4
# Load in volume
S4_input_volume = "Melbourne_S4/Tian_Subcortex_S4_3T_1mm.nii.gz"
S4_img = nb.load(S4_input_volume)
S4_data = S4_img.get_fdata()

# Right-hemisphere subcortex range is 1-27
S4_subcortex_right_data = np.where((S4_data >= 1) & (S4_data <= 27), S4_data, 0)
S4_subcortex_right_img = nb.Nifti1Image(S4_subcortex_right_data, S4_img.affine, S4_img.header)
nb.save(S4_subcortex_right_img, "Melbourne_S4/Tian_Subcortex_S4_3T_1mm_R.nii.gz")

####################### AICHA ######################

# Load in volume
AICHA_input_volume = "AICHA/AICHA1mm.nii"
AICHA_img = nb.load(AICHA_input_volume)
AICHA_data = AICHA_img.get_fdata()

# Subcortex range is 345-384. Load in the atlas and extract these regions.
AICHA_subcortex_data = np.where((AICHA_data >= 345) & (AICHA_data <= 384), AICHA_data, 0)
AICHA_subcortex_img = nb.Nifti1Image(AICHA_subcortex_data, AICHA_img.affine, AICHA_img.header)
nb.save(AICHA_subcortex_img, "AICHA/AICHA1mm_subcortex.nii.gz")

# Also filter to even numbers only to retain the right-hemisphere subcortex 
AICHA_subcortex_right_data = np.where((AICHA_subcortex_data % 2 == 0), AICHA_subcortex_data, 0)
AICHA_subcortex_right_img = nb.Nifti1Image(AICHA_subcortex_right_data, AICHA_img.affine, AICHA_img.header)
nb.save(AICHA_subcortex_right_img, "AICHA/AICHA1mm_subcortex_R.nii.gz")

####################### Brainnetome ######################

# Load in volume
Brainnetome_input_volume = "Brainnetome/BN_Atlas_246_1mm.nii.gz"
Brainnetome_img = nb.load(Brainnetome_input_volume)
Brainnetome_data = Brainnetome_img.get_fdata()

# Subcortex range is 211-246. Load in the atlas and extract these regions.
Brainnetome_subcortex_data = np.where((Brainnetome_data >= 211) & (Brainnetome_data <= 246), Brainnetome_data, 0)
Brainnetome_subcortex_img = nb.Nifti1Image(Brainnetome_subcortex_data, Brainnetome_img.affine, Brainnetome_img.header)
nb.save(Brainnetome_subcortex_img, "Brainnetome/BN_Atlas_246_1mm_subcortex.nii.gz")


# Also filter to even numbers only to retain the right-hemisphere subcortex 
Brainnetome_subcortex_right_data = np.where((Brainnetome_subcortex_data % 2 == 0), Brainnetome_subcortex_data, 0)
Brainnetome_subcortex_right_img = nb.Nifti1Image(Brainnetome_subcortex_right_data, Brainnetome_img.affine, Brainnetome_img.header)
nb.save(Brainnetome_subcortex_right_img, "Brainnetome/BN_Atlas_246_1mm_subcortex_R.nii.gz")

# http://www.Brainnetome.org/resource/201910/t20191030_522618.html
# Get the .xfm file for MNI152NLin6Asym to MNI152NLin2009cAsym
tflow.get(
        "MNI152NLin6Asym",
        suffix="xfm",
        desc=None,
        **{"from": "MNI152NLin2009cAsym"}
)

# Define paths for reference image and transform
ref_img = os.fspath(tflow.get(
    "MNI152NLin6Asym",
    resolution=1,
    desc=None,
    suffix="T1w"
))

xfm = (
    "/Users/abry4213/Library/Caches/templateflow/"
    "tpl-MNI152NLin6Asym/"
    "tpl-MNI152NLin6Asym_from-MNI152NLin2009cAsym_mode-image_xfm.h5"
)

Brainnetome_subcortex_file = f"Brainnetome/BN_Atlas_246_1mm_subcortex.nii.gz"
Brainnetome_subcortex_warped_file = f"Brainnetome/BN_Atlas_246_MNI152NLin6Asym_1mm_subcortex.nii.gz"
Brainnetome_subcortex_R_file = f"Brainnetome/BN_Atlas_246_1mm_subcortex_R.nii.gz"
Brainnetome_subcortex_R_warped_file = f"Brainnetome/BN_Atlas_246_MNI152NLin6Asym_1mm_subcortex_R.nii.gz"

# Load in images using ANTs
Brainnetome_subcortex_img = ants.image_read(Brainnetome_subcortex_file)
Brainnetome_subcortex_right_img = ants.image_read(Brainnetome_subcortex_R_file)
reference = ants.image_read(ref_img)

# Apply nearest neighbor interpolation to preserve labels
Brainnetome_subcortex_warped = ants.apply_transforms(
    fixed=reference,
    moving=Brainnetome_subcortex_img,
    transformlist=[xfm],
    interpolator="nearestNeighbor"
)
Brainnetome_subcortex_R_warped = ants.apply_transforms(
    fixed=reference,
    moving=Brainnetome_subcortex_right_img,
    transformlist=[xfm],
    interpolator="nearestNeighbor"
)

# Save out the warped atlases
ants.image_write(Brainnetome_subcortex_warped, Brainnetome_subcortex_warped_file)
ants.image_write(Brainnetome_subcortex_R_warped, Brainnetome_subcortex_R_warped_file)

####################### Thalamic nuclei (HCP) ######################

# Load in volume
Thalamus_Nuclei_HCP_input_volume = "Thalamus_Nuclei_HCP/Thalamus_Nuclei-HCP-MaxProb.nii.gz"
Thalamus_Nuclei_HCP_img = nb.load(Thalamus_Nuclei_HCP_input_volume)
Thalamus_Nuclei_HCP_data = Thalamus_Nuclei_HCP_img.get_fdata()

# Filter to indices 8-14 to retain the right-hemisphere subcortex 
Thalamus_Nuclei_HCP_right_data = np.where((Thalamus_Nuclei_HCP_data >= 8) & (Thalamus_Nuclei_HCP_data <= 14), Thalamus_Nuclei_HCP_data, 0)
Thalamus_Nuclei_HCP_data_right_img = nb.Nifti1Image(Thalamus_Nuclei_HCP_right_data, Thalamus_Nuclei_HCP_img.affine, Thalamus_Nuclei_HCP_img.header)
nb.save(Thalamus_Nuclei_HCP_data_right_img, "Thalamus_Nuclei_HCP/Thalamus_Nuclei_HCP_R.nii.gz")

# Define paths for reference image and transform
ref_img = os.fspath(tflow.get(
    "MNI152NLin6Asym",
    resolution=1,
    desc=None,
    suffix="T1w"
))

xfm = (
    "/Users/abry4213/Library/Caches/templateflow/"
    "tpl-MNI152NLin6Asym/"
    "tpl-MNI152NLin6Asym_from-MNI152NLin2009cAsym_mode-image_xfm.h5"
)

Thalamus_Nuclei_HCP_warped_file = f"Thalamus_Nuclei_HCP/Thalamus_Nuclei_HCP_MNI152NLin6Asym.nii.gz"
Thalamus_Nuclei_HCP_R_file = f"Thalamus_Nuclei_HCP/Thalamus_Nuclei_HCP_R.nii.gz"
Thalamus_Nuclei_HCP_R_warped_file = f"Thalamus_Nuclei_HCP/Thalamus_Nuclei_HCP_MNI152NLin6Asym_R.nii.gz"

# Load in images using ANTs
Thalamus_Nuclei_HCP_img = ants.image_read(Thalamus_Nuclei_HCP_input_volume)
Thalamus_Nuclei_HCP_right_img = ants.image_read(Thalamus_Nuclei_HCP_R_file)
reference = ants.image_read(ref_img)

# Apply nearest neighbor interpolation to preserve labels
Thalamus_Nuclei_HCP_warped = ants.apply_transforms(
    fixed=reference,
    moving=Thalamus_Nuclei_HCP_img,
    transformlist=[xfm],
    interpolator="nearestNeighbor"
)
Thalamus_Nuclei_HCP_R_warped = ants.apply_transforms(
    fixed=reference,
    moving=Thalamus_Nuclei_HCP_right_img,
    transformlist=[xfm],
    interpolator="nearestNeighbor"
)

# Save out the warped atlases
ants.image_write(Thalamus_Nuclei_HCP_warped, Thalamus_Nuclei_HCP_warped_file)
ants.image_write(Thalamus_Nuclei_HCP_R_warped, Thalamus_Nuclei_HCP_R_warped_file)

####################### Cerebellum (SUIT) ######################

# Load the atlas LUT
SUIT_LUT = pd.read_csv("SUIT_cerebellar_lobule/SUIT_cerebellar_lobule_lookup.csv", header=None)
SUIT_LUT.columns = ['Index', 'Region']

# Filter atlas_data to only include index values present in atlas_LUT.index
index_list = np.unique(SUIT_LUT.Index)

# Load in volume
SUIT_input_volume = "SUIT_cerebellar_lobule/atl-Anatom_space-MNI_dseg.nii.gz"
SUIT_img = nb.load(SUIT_input_volume)
SUIT_data = SUIT_img.get_fdata()

# Filter to only include indices present in the LUT
SUIT_data_filtered = np.isin(SUIT_data, index_list) * SUIT_data
SUIT_data_filtered_img = nb.Nifti1Image(SUIT_data_filtered, SUIT_img.affine, SUIT_img.header)
nb.save(SUIT_data_filtered_img, "SUIT_cerebellar_lobule/atl-Anatom_space-MNI_dseg_filtered.nii.gz")