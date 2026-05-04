import numpy as np
import matplotlib
import argparse 

parser = argparse.ArgumentParser(description='Generate plasma colormap text file.')
parser.add_argument('--num_colors', type=int, default=8, 
                                      help='Number of colors to sample from the plasma colormap.')
parser.add_argument('--cmap_name',  type=str, default='plasma', 
                                      help='Name of the colormap to use.')
parser.add_argument('--output_file', type=str, default='plasma_8colors.txt',
                                        help='Output filename for the color text file.')
args = parser.parse_args()

num_colors = args.num_colors
cmap_name = args.cmap_name
output_file = args.output_file


# Generate color text file
cmap = matplotlib.colormaps.get_cmap(cmap_name) # Use plasma colormap
colors = cmap(np.linspace(0, 1, num_colors)) # Sample num_colors colors
rgb_colors = colors[:, :3] # Extract RGB (no alpha)
rgb_256 = (rgb_colors * 255).astype(int) # 0-256 scaling
np.savetxt(output_file, rgb_256, fmt='%d') # Save colors to .txt file
