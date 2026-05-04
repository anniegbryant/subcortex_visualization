#!/usr/bin/env python3
# Downloaded from https://github.com/rordenlab/pythonScripts/blob/main/atlas2mz3/niiAtlas2mesh.py
# Author: Chris Rorden
# Modified by: Annie G. Bryant
# Date of download: 30 August 2025

import os
import sys
import subprocess
import nibabel as nib
import argparse
import shutil

def check_niimath():
    if not shutil.which("niimath"):
        sys.exit("Error: 'niimath' not found in your PATH. Please install or add it.")

def check_file_exists(fname):
    if not os.path.isfile(fname):
        sys.exit(f"Error: File not found: {fname}")

def get_max_index(nifti_file):
    img = nib.load(nifti_file)
    data = img.get_fdata()
    return int(data.max())

def run_niimath(nifti_file, idx, outpath=None):
    outname = f"{os.path.splitext(nifti_file)[0]}_{idx}" if outpath is None else os.path.join(outpath, f"{os.path.splitext(os.path.basename(nifti_file))[0]}_{idx}")
    cmd = [
        "niimath", nifti_file,
        "-thr", str(idx),
        "-uthr", str(idx),
        "-bin",
        "-s", "1.2",
        "-mesh",
        "-i", "0.5",
        "-r", "0.5",
        "-s", "1",
        "-q", "b",
        outname
    ]
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error processing index {idx}:\n{result.stderr}")
    else:
        print(f"Saved mesh: {outname}.mz3")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Combine *_n.mz3 meshes into a single colored atlas.')
    parser.add_argument('--input_volume', type=str, help='Input volumetric segmentation to convert.')
    parser.add_argument('--output_path', type=str, default=None, help='Output path for meshes (default: same directory as input).')
    parser.add_argument('--index_min', type=int, default=None, help='Minimum region index to convert (optional).')
    parser.add_argument('--index_max', type=int, default=None, help='Maximum region index to convert (optional).')

    args = parser.parse_args()

    nifti_file = args.input_volume
    outpath = args.output_path
    index_min = args.index_min
    index_max = args.index_max

    check_niimath()
    check_file_exists(nifti_file)

    # Set index range, defaulting to full range if not specified
    min_index = 1 if index_min is None else index_min
    max_index = get_max_index(nifti_file) if index_max is None else index_max

    print(f"Max index found: {max_index}")

    for idx in range(1, max_index + 1):
        run_niimath(nifti_file, idx, outpath)
