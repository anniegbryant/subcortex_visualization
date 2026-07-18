import numpy as np
import nibabel as nb
import pandas as pd
import os
import shutil
from glob import glob

# For inter-atlas alignment
import templateflow
import templateflow.api as tflow
import ants

# Find filepath to this file
input_volume_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'original_space')
os.chdir(input_volume_path)

# Find output path for atlas volumes in the package itself
# One directory up from the current file, then into the "data" directory
output_MNI152NLin2009cAsym_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'MNI152NLin2009cAsym')
output_MNI152NLin6Asym_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'MNI152NLin6Asym')

def create_registration(output_path, input_template="MNI152NLin2009cSym",
                        output_template="MNI152NLin2009cAsym"):
    
    if not os.path.isfile(f'{output_path}/tpl-{input_template}_from-{output_template}_mode-image_xfm.mat'):
        input_ants = ants.image_read(os.fspath(tflow.get(input_template, resolution=1, suffix='T1w', desc=None)))
        output_ants = ants.image_read(os.fspath(tflow.get(output_template, resolution=1, suffix='T1w', desc=None)))

        reg = ants.registration(
            fixed=output_ants,
            moving=input_ants,
            type_of_transform='SyN',
            outprefix=f'{output_path}/tpl-{output_template}_from-{input_template}'  # ANTs will write files here
        )

        # reg['fwdtransforms'] contains 2 files: a warp field (.nii.gz) and affine (.mat)
        # Copy them to a permanent location with BIDS-style naming
        shutil.copy(reg['fwdtransforms'][0], f'{output_path}/tpl-{output_template}_from-{input_template}_mode-image_xfm.nii.gz')
        shutil.copy(reg['fwdtransforms'][1], f'{output_path}/tpl-{output_template}_from-{input_template}_mode-image_xfm.mat')

        # Save inverse too (Asym → Sym) for free
        shutil.copy(reg['invtransforms'][0], f'{output_path}/tpl-{input_template}_from-{output_template}_mode-image_xfm.nii.gz')
        shutil.copy(reg['invtransforms'][1], f'{output_path}/tpl-{input_template}_from-{output_template}_mode-image_xfm.mat')

    transform_file = f'{output_path}/tpl-{output_template}_from-{input_template}_mode-image_xfm.mat'
    return transform_file

def copy_files_for_atlas(atlas_name, input_dir, output_atlas_dir):
    os.makedirs(f"{output_atlas_dir}", exist_ok=True)
    shutil.copy(f"{input_dir}/{atlas_name}/{atlas_name}.nii.gz", f"{output_atlas_dir}/{atlas_name}.nii.gz")
    shutil.copy(f"{input_dir}/{atlas_name}/{atlas_name}_lookup.csv", f"{output_atlas_dir}/{atlas_name}_lookup.csv")

def apply_xfm_to_atlas(atlas_name, input_space, output_space, input_vol_dir, output_vol_dir,
                       transform_file=None):

    input_atlas_file = f"{input_vol_dir}/{atlas_name}/{atlas_name}.nii.gz"
    output_atlas_file = f"{output_vol_dir}/{atlas_name}.nii.gz"

    # If those files don't exist, try f"{input_vol_dir}/{atlas_name}.nii.gz" and f"{output_vol_dir}/{atlas_name}.nii.gz" instead (in case the atlas files aren't organized into subdirectories by atlas name)
    if not os.path.isfile(input_atlas_file):
        input_atlas_file = f"{input_vol_dir}/{atlas_name}.nii.gz"
        if not os.path.isfile(input_atlas_file):
            raise FileNotFoundError(f"Could not find input atlas file for {atlas_name} at either {input_vol_dir}/{atlas_name}/{atlas_name}.nii.gz or {input_vol_dir}/{atlas_name}.nii.gz")
        output_atlas_file = f"{output_vol_dir}/{atlas_name}.nii.gz"

    # Get the .xfm file for input_space to output_space
    tflow.get(
            output_space,
            suffix="xfm",
            desc=None,
            **{"from": input_space}
    )

    # Define paths for reference image and transform
    ref_img = os.fspath(tflow.get(
        output_space,
        resolution=1,
        desc=None,
        suffix="T1w"
    ))
    print(f"Reference image for {output_space}: {ref_img}")

    xfm_results = tflow.get(
        output_space,
        suffix="xfm",
        extension=".h5",
        desc=None,
        **{"from": input_space}
    )
    print(f"Transform results for {input_space} -> {output_space}: {xfm_results}")

    if xfm_results:    
        # Handle both single path and list of paths
        xfm = os.fspath(xfm_results[0] if isinstance(xfm_results, list) else xfm_results)

    else:
        if transform_file is not None:
            xfm = transform_file

        else:
            raise FileNotFoundError(
                f"No transform found in templateflow for "
                f"{output_space} -> {input_space}. "
                f"Try swapping input_space and output_space, or check "
                f"available transforms with tflow.get('{input_space}', suffix='xfm')"
            )

    print(f"Using transform: {xfm}")  # helpful to verify the right file is picked

    # Load in images using ANTs
    atlas_img = ants.image_read(input_atlas_file)
    reference = ants.image_read(ref_img)

    # Apply nearest neighbor interpolation to preserve labels
    atlas_warped = ants.apply_transforms(
        fixed=reference,
        moving=atlas_img,
        transformlist=[xfm],
        interpolator="nearestNeighbor"
    )

    # Save out the warped atlas
    ants.image_write(atlas_warped, output_atlas_file)

# Create a dictionary for atlas/space names
atlas_space_dict = {'aseg_subcortex': 'MNI152NLin6Asym',
                    'Melbourne_S1': 'MNI152NLin6Asym',
                    'Melbourne_S2': 'MNI152NLin6Asym',
                    'Melbourne_S3': 'MNI152NLin6Asym',
                    'Melbourne_S4': 'MNI152NLin6Asym',
                    'AICHA_subcortex': 'MNI152NLin2009cAsym',
                    'Brainnetome_subcortex': 'MNI152NLin6Asym',
                    'CIT168_subcortex': 'MNI152NLin2009cAsym',
                    'Thalamus_HCP': 'MNI152NLin2009cSym',
                    'Thalamus_THOMAS': 'MNI152NLin2009bAsym',
                    'SUIT_cerebellar_lobule': 'MNI152NLin2009cSym'}

############## Atlases --> MNI152NLin2009cAsym ##############
for output_space in ["MNI152NLin2009cAsym", "MNI152NLin6Asym"]:
    output_space_dir = output_MNI152NLin2009cAsym_dir if output_space == "MNI152NLin2009cAsym" else output_MNI152NLin6Asym_dir

    # Iterate over each atlas aside from Brainstem Navigator
    for atlas, atlas_space in atlas_space_dict.items():
        print(f"Processing {atlas} atlas...")
        atlas_output_space_dir = f"{output_space_dir}/{atlas}"
        os.makedirs(atlas_output_space_dir, exist_ok=True)

        if atlas_space == output_space:
            # Just copy files over without transformation
            copy_files_for_atlas(atlas_name=atlas, input_dir=input_volume_path, 
                                output_atlas_dir=atlas_output_space_dir)
        else:
            # First, create alignment between MNI152NLin2009cSym and MNI152NLin2009cAsym if it doesn't already exist in templateflow
            print(f"Creating alignment between {atlas_space} and {output_space} if it doesn't already exist in templateflow...")
            transform_file = create_registration(input_template=atlas_space,
                        output_template=output_space,
                        output_path=os.getcwd())

            # Apply transformation to MNI152NLin2009cAsym space
            apply_xfm_to_atlas(atlas_name=atlas,
                            input_space=atlas_space,
                            output_space=output_space,
                            input_vol_dir=input_volume_path,
                            output_vol_dir=atlas_output_space_dir,
                            transform_file=transform_file)

            # Copy the lookup table to both the atlas_info directory and the package directory
            shutil.copy(f"{input_volume_path}/{atlas}/{atlas}_lookup.csv",
                        f"{atlas_output_space_dir}/{atlas}_lookup.csv")
            
        
    # Brainstem Navigator is run separately
    print(f"Processing {atlas} atlas...")
    atlas = "Brainstem_Navigator"
    atlas_space = 'MNI152NLin6Asym'
    atlas_output_space_dir = f"{output_space_dir}/{atlas}"
    os.makedirs(atlas_output_space_dir, exist_ok=True)

    if atlas_space == output_space:
        # Just copy files over without transformation
        for file in glob(f"{input_volume_path}/{atlas}/*.nii.gz"):
            print(file)
            shutil.copy(file, f"{atlas_output_space_dir}/{os.path.basename(file)}")

    else: 
        brainstem_navigator_ROI_files = glob(f"{input_volume_path}/{atlas}/*.nii.gz")
        print(f"Found {len(brainstem_navigator_ROI_files)} Brainstem Navigator ROI files. Aligning to MNI152NLin2009cAsym...")
        for ROI_file in brainstem_navigator_ROI_files:
            ROI_base = os.path.basename(ROI_file).replace(".nii.gz", "")
            if not os.path.isfile(f"{atlas_output_space_dir}/{ROI_base}.nii.gz"):
                print(f"Aligning {ROI_base} to MNI152NLin2009cAsym...")
                apply_xfm_to_atlas(atlas_name=f"{ROI_base}",
                                input_space=atlas_space, 
                                output_space=output_space, 
                                input_vol_dir=f"{input_volume_path}/{atlas}", 
                                output_vol_dir=atlas_output_space_dir)
                
    # Copy the lookup table to the atlas_info directory
    shutil.copy(f"{input_volume_path}/{atlas}/{atlas}_lookup.csv",
                f"{atlas_output_space_dir}//{atlas}_lookup.csv")

