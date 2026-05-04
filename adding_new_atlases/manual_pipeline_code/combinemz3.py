#!/usr/bin/env python3
# Downloaded from https://github.com/rordenlab/pythonScripts/blob/main/atlas2mz3/combinemz3.py
# Author: Chris Rorden
# Modified by: Annie G. Bryant
# Date of download: 30 August 2025

import os
import struct
import glob
import numpy as np
import gzip
import io
import argparse
import sys
import re

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

def combine_mz3(mesh_glob='*.mz3', input_path='.',
                color_file='colors.txt', 
                out_file='combined_atlas.mz3', 
                delete_inputs=False):
    # Set working directory to input_path if provided, otherwise define as current working directory
    if input_path == '.':
        input_path = os.getcwd()

    print(f"Using input path: {input_path}")

    # Only match files with numeric suffix: e.g., Tian_1.mz3, Tian_2.mz3
    mesh_files = [f for f in sorted(glob.glob(f'{input_path}/{mesh_glob}'))
                  if re.match(r'^(.+?)_(\d+)\.mz3$', os.path.basename(f))]
    if not mesh_files:
        raise FileNotFoundError("No valid *_n.mz3 files found.")

    # Extract prefix and index
    parsed = [re.match(r'^(.+?)_(\d+)\.mz3$', os.path.basename(f)) for f in mesh_files]
    prefixes = set(m.group(1) for m in parsed)
    if len(prefixes) != 1:
        raise ValueError(f"Error: Multiple filename prefixes found: {sorted(prefixes)}. "
                         f"All files must share a common prefix like 'Tian_1.mz3', 'Tian_2.mz3'...")

    prefix = prefixes.pop()
    indices = [int(m.group(2)) for m in parsed]

    color_map = load_colors(color_file)
    if max(indices) > len(color_map):
        sys.exit(f"Error: The color file '{color_file}' defines {len(color_map)} colors, "
                 f"but a mesh with index {max(indices)} was found. Please add more colors.")

    all_faces = []
    all_verts = []
    all_rgba = []
    all_scalar = []
    vert_offset = 0

    for idx, f in sorted(zip(indices, mesh_files)):
        if idx not in color_map:
            sys.exit(f"Error: No color defined for index {idx} in '{color_file}'.")
        color = color_map[idx]
        faces, verts = read_mz3(f)
        nvert = verts.shape[0]
        all_faces.append(faces + vert_offset)
        all_verts.append(verts)
        all_rgba.append(np.tile(color, (nvert, 1)))
        all_scalar.append(np.full(nvert, idx, dtype=np.float32))
        vert_offset += nvert

    write_mz3(f'{input_path}/{out_file}',
              np.vstack(all_faces),
              np.vstack(all_verts),
              np.vstack(all_rgba),
              np.concatenate(all_scalar))
    print(f"Combined mesh saved as: {out_file}")

    if delete_inputs:
        for f in mesh_files:
            os.remove(f)
        print("Deleted input mesh files.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combine *_n.mz3 meshes into a single colored atlas.')
    parser.add_argument('--input_path', type=str, default='.', help='Directory containing input mz3 files (default: current directory)')
    parser.add_argument('--out_file', type=str, default='combined_atlas.mz3', help='Name for combined output file (default: combined_atlas.mz3)')
    parser.add_argument('--colors', type=str, default='colors.txt', help='Path to color file (default: colors.txt)')
    parser.add_argument('--delete_inputs', action='store_true', help='Delete input mz3 files after combining')

    args = parser.parse_args()

    combine_mz3(color_file=args.colors, input_path=args.input_path, out_file=args.out_file, delete_inputs=args.delete_inputs)
