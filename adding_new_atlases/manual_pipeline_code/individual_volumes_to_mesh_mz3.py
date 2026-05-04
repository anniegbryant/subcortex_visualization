#!/usr/bin/env python3
# Convert a directory of binary ROI NIfTI volumes into a combined colored MZ3 atlas
# Author: Modified for directory-based ROI workflow

import argparse
import glob
import gzip
import io
import nibabel as nib
import numpy as np
import os
import re
import shutil
import struct
import subprocess
import sys

############################################################
# Utility checks
############################################################

def check_niimath():
    if not shutil.which("niimath"):
        sys.exit("Error: 'niimath' not found in PATH.")

def check_input_dir(input_dir):
    if not os.path.isdir(input_dir):
        sys.exit(f"Error: Input directory not found: {input_dir}")

############################################################
# Step 1: Convert ROI NIfTI files → MZ3 meshes
############################################################

def generate_meshes_from_directory(input_dir, outpath=None, prefix="ROI", out_file=None):
    if outpath is None:
        outpath = input_dir

    nii_files = sorted(glob.glob(os.path.join(input_dir, "*.nii.gz")))

    if len(nii_files) == 0:
        raise FileNotFoundError("No .nii.gz files found in input directory.")
    
    # Keep a list for regions
    output_region_list = []

    print(f"Found {len(nii_files)} ROI volumes.")

    for idx, nifti_file in enumerate(nii_files, start=1):
        region = os.path.basename(nifti_file).split('.')[0]  # Use filename (without extension) as prefix
        output_region_list.append(region)

        outname = os.path.join(outpath, f"{prefix}_{idx}")

        # Check if f"{outname}.mz3" exists
        if not os.path.isfile(f"{outname}.mz3"):

            # If region is SC_r, don't apply smoothing
            if region == 'SC_r':
                cmd = [
                    "niimath", nifti_file,
                    "-bin",
                    "-s", "0.5",
                    "-mesh",
                    "-i", "0.5",
                    "-r", "0.5",
                    "-q", "b",
                    outname
                ]
            else:
                cmd = [
                    "niimath", nifti_file,
                    "-bin",
                    "-s", "1.2",
                    "-mesh",
                    "-i", "0.5",
                    "-r", "0.5",
                    "-q", "b",
                    outname
                ]

            print("Running:", " ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"Error processing {nifti_file}:\n{result.stderr}")
                continue

            mz3_file = f"{outname}.mz3"
            print(f"Saved mesh: {mz3_file}")

    # Save the region list to a text file
    out_file_prefix = out_file.replace('.mz3', '') if out_file else 'combined_atlas'
    region_list_file = os.path.join(outpath, f"{out_file_prefix}_region_list.txt")
    with open(region_list_file, 'w') as f:
        for region in output_region_list:
            f.write(f"{region}\n")

############################################################
# MZ3 I/O
############################################################

def read_mz3(filename):
    with open(filename, 'rb') as f:
        magic = f.read(2)

    if magic == b'\x1f\x8b':
        with gzip.open(filename, 'rb') as gz:
            raw = gz.read()
        f = io.BytesIO(raw)
    else:
        f = open(filename, 'rb')

    with f:
        hdr = f.read(16)
        magic, attr, nface, nvert, nskip = struct.unpack('<HHIII', hdr)

        if magic != 23117:
            raise ValueError(f"{filename} is not a valid MZ3 file.")

        f.read(nskip)

        faces = np.frombuffer(f.read(nface * 12), dtype=np.int32).reshape((-1, 3)) if attr & 1 else []
        verts = np.frombuffer(f.read(nvert * 12), dtype=np.float32).reshape((-1, 3)) if attr & 2 else []

        f.read(nvert * 4) if attr & 4 else None
        f.read(nvert * 4) if attr & 8 else None

        return faces, verts


def write_mz3(filename, faces, verts, rgba, scalars):
    attr = 1 | 2 | 4 | 8
    nface = len(faces)
    nvert = len(verts)

    with gzip.open(filename, 'wb') as f:
        f.write(struct.pack('<HHIII', 0x5A4D, attr, nface, nvert, 0))
        f.write(faces.astype(np.int32).tobytes())
        f.write(verts.astype(np.float32).tobytes())
        f.write(rgba.astype(np.uint8).tobytes())
        f.write(scalars.astype(np.float32).tobytes())

############################################################
# Colors
############################################################

def load_colors(color_file):
    color_map = {}

    with open(color_file, 'r') as f:
        for idx, line in enumerate(f, 1):
            parts = line.strip().split()
            if len(parts) != 3:
                continue
            r, g, b = map(int, parts)
            color_map[idx] = np.array([r, g, b, 255], dtype=np.uint8)

    return color_map

############################################################
# Step 2: Combine meshes
############################################################

def combine_mz3(input_path, color_file, out_file, delete_mz3=False, prefix="ROI"):

    mesh_files = sorted(glob.glob(os.path.join(input_path, f"{prefix}_*.mz3")), )

    if not mesh_files:
        raise FileNotFoundError("No ROI_*.mz3 files found.")

    indices = []
    for f in mesh_files:
        m = re.match(rf"{prefix}_(\d+)\.mz3$", os.path.basename(f))
        if m:
            indices.append(int(m.group(1)))
        else:
            raise ValueError(f"Invalid filename format: {f}")

    color_map = load_colors(color_file)

    if max(indices) > len(color_map):
        sys.exit("Error: Not enough colors provided.")

    all_faces = []
    all_verts = []
    all_rgba = []
    all_scalar = []

    vert_offset = 0

    for idx, f in sorted(zip(indices, mesh_files)):

        faces, verts = read_mz3(f)
        nvert = verts.shape[0]

        color = color_map[idx]

        all_faces.append(faces + vert_offset)
        all_verts.append(verts)
        all_rgba.append(np.tile(color, (nvert, 1)))
        all_scalar.append(np.full(nvert, idx, dtype=np.float32))

        vert_offset += nvert

    write_mz3(
        os.path.join(input_path, out_file),
        np.vstack(all_faces),
        np.vstack(all_verts),
        np.vstack(all_rgba),
        np.concatenate(all_scalar)
    )

    print(f"Combined mesh saved as: {out_file}")

    if delete_mz3:
        for f in mesh_files:
            os.remove(f)
        print("Deleted intermediate meshes.")

############################################################
# Main
############################################################

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Convert ROI NIfTI directory → combined colored MZ3 atlas"
    )

    parser.add_argument('--input_dir', required=True,
                        help='Directory containing ROI .nii.gz files')

    parser.add_argument('--output_path', default=None,
                        help='Output directory (default: input_dir)')

    parser.add_argument('--colors', default='colors.txt',
                        help='Color file (R G B per line)')

    parser.add_argument('--out_file', default='combined_atlas.mz3',
                        help='Output combined mz3 filename')

    parser.add_argument('--delete_mz3', action='store_true',
                        help='Delete intermediate meshes')

    args = parser.parse_args()

    ###########################################################
    # Run pipeline
    ###########################################################

    check_niimath()
    check_input_dir(args.input_dir)

    outpath = args.output_path if args.output_path else args.input_dir

    print("\n=== Step 1: Generating meshes ===")
    generate_meshes_from_directory(args.input_dir, outpath)

    print("\n=== Step 2: Combining meshes ===")
    combine_mz3(
        input_path=outpath,
        color_file=args.colors,
        out_file=args.out_file,
        delete_mz3=args.delete_mz3
    )

    print("\nDone.")