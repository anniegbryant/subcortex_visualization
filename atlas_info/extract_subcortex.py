import numpy as np
import nibabel as nb
import pandas as pd
import os
import shutil

# Find filepath to this file
input_volume_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'original_space')
os.chdir(input_volume_path)

################################## aseg ##################################
print("Processing aseg atlas...")
# Load the .mgz file
aseg_input_volume = f"{input_volume_path}/aseg_subcortex/aparc+aseg.mgz"
aseg_img = nb.load(aseg_input_volume)
aseg_data = aseg_img.get_fdata()

# Load the aseg LUT
aseg_LUT = pd.read_csv(f"{input_volume_path}/aseg_subcortex/aseg_subcortex_lookup.csv", header=None)
aseg_LUT.columns = ['Index', 'Region']

# Filter atlas_data to only include index values present in atlas_LUT.index
index_list = np.unique(aseg_LUT.Index)
index_list = index_list.astype(int)

# Filter to only include indices present in the LUT
aseg_data_filtered = np.isin(aseg_data, index_list) * aseg_data
aseg_data_filtered_img = nb.Nifti1Image(aseg_data_filtered, aseg_img.affine, aseg_img.header)

# Save to new file: (1) in the same directory as the input volume, and (2) in the package directory
nb.save(aseg_data_filtered_img, f"{input_volume_path}/aseg_subcortex/aseg_subcortex.nii.gz")

####################### Melbourne subcortical atlas ######################
print("Processing Melbourne subcortical atlas...")

# Atlases are already filtered to the subcortex for this one, just need to rename
# S1
shutil.copy(f"{input_volume_path}/Melbourne_S1/Tian_Subcortex_S1_3T_2009cAsym.nii.gz", f"{input_volume_path}/Melbourne_S1/Melbourne_S1.nii.gz")
# S2
shutil.copy(f"{input_volume_path}/Melbourne_S2/Tian_Subcortex_S2_3T_2009cAsym.nii.gz", f"{input_volume_path}/Melbourne_S2/Melbourne_S2.nii.gz")
# S3
shutil.copy(f"{input_volume_path}/Melbourne_S3/Tian_Subcortex_S3_3T_2009cAsym.nii.gz", f"{input_volume_path}/Melbourne_S3/Melbourne_S3.nii.gz")
# S4
shutil.copy(f"{input_volume_path}/Melbourne_S4/Tian_Subcortex_S4_3T_2009cAsym.nii.gz", f"{input_volume_path}/Melbourne_S4/Melbourne_S4.nii.gz")

####################### AICHA ######################
print("Processing AICHA atlas...")

# Load in volume
AICHA_input_volume = f"{input_volume_path}/AICHA_subcortex/AICHA1mm.nii.gz"
AICHA_img = nb.load(AICHA_input_volume)
AICHA_data = AICHA_img.get_fdata()

# Subcortex range is 345-384. Load in the atlas and extract these regions.
AICHA_subcortex_data = np.where((AICHA_data >= 345) & (AICHA_data <= 384), AICHA_data, 0)
AICHA_subcortex_img = nb.Nifti1Image(AICHA_subcortex_data, AICHA_img.affine, AICHA_img.header)
nb.save(AICHA_subcortex_img, f"{input_volume_path}/AICHA_subcortex/AICHA_subcortex.nii.gz")

####################### Brainnetome ######################
print("Processing Brainnetome atlas...")

# Load in volume
Brainnetome_input_volume = f"{input_volume_path}/Brainnetome_subcortex/BN_Atlas_246_1mm.nii.gz"
Brainnetome_img = nb.load(Brainnetome_input_volume)
Brainnetome_data = Brainnetome_img.get_fdata()

# Subcortex range is 211-246. Load in the atlas and extract these regions.
Brainnetome_subcortex_data = np.where((Brainnetome_data >= 211) & (Brainnetome_data <= 246), Brainnetome_data, 0)
Brainnetome_subcortex_img = nb.Nifti1Image(Brainnetome_subcortex_data, Brainnetome_img.affine, Brainnetome_img.header)
nb.save(Brainnetome_subcortex_img, f"{input_volume_path}/Brainnetome_subcortex/Brainnetome_subcortex.nii.gz")

####################### CIT168 subcortex ######################
print("Processing CIT168 subcortical atlas...")

# Note that we downloaded code from https://github.com/PennLINC/AtlasPack/blob/main/CIT168/prepare_atlas.sh

input_cit_file = f"{input_volume_path}/CIT168_subcortex/tpl-MNI152NLin2009cAsym_atlas-CIT168_res-01_desc-RAS_dseg.nii.gz"
output_cit_prefix = f"{input_volume_path}/CIT168_subcortex/CIT168_subcortex"

if not os.path.isfile(f"{output_cit_prefix}.nii.gz"):
    cit168_subcortical = {"node_names": [], "node_ids": []}

    with open(f"{input_volume_path}/CIT168_subcortex/labels.txt") as f:
        for line in f:
            split = line.strip().split()
            if not len(split) == 2:
                continue
            node_id, node_name = line.strip().split()
            cit168_subcortical["node_names"].append(node_name)
            # they started at 0, wtf
            cit168_subcortical["node_ids"].append(int(node_id) + 1)

    cit_168_img = nb.load(input_cit_file)
    cit168_data = cit_168_img.get_fdata().astype(np.uint32)

    # Merge the smaller regions together
    cit_lut = {
        node_id: region_label
        for node_id, region_label in zip(
            cit168_subcortical["node_ids"], cit168_subcortical["node_names"]
        )
    }
    cit168_data[cit168_data == 10] = 7
    cit168_data[cit168_data == 11] = 7
    cit_region7_label = "_".join([cit_lut[7], cit_lut[10], cit_lut[11]])
    cit_lut[7] = cit_region7_label
    del cit_lut[10], cit_lut[11]
    merged_cit_ids = sorted(cit_lut.keys())
    merged_cit_labels = [cit_lut[node_id] for node_id in merged_cit_ids]
    merged_cit_config = {"node_ids": merged_cit_ids, "node_names": merged_cit_labels}

    # Add 100 to the LH regions to separate them
    offsetmask = np.zeros_like(cit168_data)
    midvoxel = offsetmask.shape[0] // 2
    offsetmask[midvoxel:, :, :] = 100
    hemi_cit_data = (cit168_data + offsetmask) * (cit168_data > 0)

    # Split regions into hemispheres
    cit_hemi_labels = [f"{name}_LH" for name in merged_cit_labels] + [
        f"{name}_RH" for name in merged_cit_labels
    ]
    cit_hemi_ids = merged_cit_ids + [_id + 100 for _id in merged_cit_ids]
    cit_hemi_config = {"node_ids": cit_hemi_ids, "node_names": cit_hemi_labels}

    labeldf = pd.DataFrame({"Region_Index": cit_hemi_ids, "Region_Name": cit_hemi_labels})
    labeldf.to_csv(f"{input_volume_path}/CIT168_subcortex/CIT168_subcortex_lookup.csv", sep=",", index=False)

    final_nii = nb.Nifti1Image(
        hemi_cit_data,
        cit_168_img.affine,
        header=cit_168_img.header,
    )

    final_nii.to_filename(f"{output_cit_prefix}.nii.gz")

####################### Thalamic nuclei (HCP) ######################

print("Processing thalamic nuclei atlas...")
# This atlas already only includes thalamic nuclei, just need to rename
shutil.copy(f"{input_volume_path}/Thalamus_HCP/Thalamus_Nuclei-HCP-MaxProb.nii.gz", f"{input_volume_path}/Thalamus_HCP/Thalamus_HCP.nii.gz")

####################### Thalamus (THOMAS) #######################
print("Processing THOMAS thalamic atlas...")

if not os.path.isfile(f"{input_volume_path}/Thalamus_THOMAS/Thalamus_THOMAS.nii.gz"):
    # Load the right-hemisphere THOMAS thalamus segmentation with CL and VPM
    THOMAS_R = nb.load(f"{input_volume_path}/Thalamus_THOMAS/Atlas-Thalamus_space-MNI_hemi-right_label-AllNuclei_desc-MaxProb.nii.gz")
    THOMAS_L = nb.load(f"{input_volume_path}/Thalamus_THOMAS/Atlas-Thalamus_space-MNI_hemi-left_label-AllNuclei_desc-MaxProb.nii.gz")

    data_R = THOMAS_R.get_fdata()
    data_L = THOMAS_L.get_fdata()

    # Where data_R > 0, add 18 to create new labels for the right thalamus
    data_R[data_R > 0] = data_R[data_R > 0] + 14

    # Get affine
    affine_R = THOMAS_R.affine

    # Combine left and right thalamus data into one image
    combined_data = np.zeros_like(data_L, dtype=np.int16)
    combined_data[data_L>0] = data_L[data_L>0]
    combined_data[data_R>0] = data_R[data_R>0]

    # Save the combined thalamus image
    combined_img = nb.Nifti1Image(combined_data, affine_R, THOMAS_R.header)

    nb.save(combined_img, f"{input_volume_path}/Thalamus_THOMAS/Thalamus_THOMAS.nii.gz")

####################### Cerebellum (SUIT) ######################

print("Processing SUIT cerebellar lobule atlas...")
# Load the atlas LUT
SUIT_LUT = pd.read_csv(f"{input_volume_path}/SUIT_cerebellar_lobule/SUIT_cerebellar_lobule_lookup.csv", header=None)
SUIT_LUT.columns = ['Index', 'Region']

# Filter atlas_data to only include index values present in atlas_LUT.index
index_list = np.unique(SUIT_LUT.Index)

# Load in volume
SUIT_input_volume = f"{input_volume_path}/SUIT_cerebellar_lobule/atl-Anatom_space-MNI_dseg.nii.gz"
SUIT_img = nb.load(SUIT_input_volume)
SUIT_data = SUIT_img.get_fdata()

# Filter to only include indices present in the LUT
SUIT_data_filtered = np.isin(SUIT_data, index_list) * SUIT_data
SUIT_data_filtered_img = nb.Nifti1Image(SUIT_data_filtered, SUIT_img.affine, SUIT_img.header)
nb.save(SUIT_data_filtered_img, f"{input_volume_path}/SUIT_cerebellar_lobule/SUIT_cerebellar_lobule.nii.gz")