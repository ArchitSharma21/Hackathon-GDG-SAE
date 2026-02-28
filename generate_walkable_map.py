"""
Generate a binary walkable map from the airport routes image.
Yellow pixels = 1 (walkable), all others = 0 (non-walkable)

Fixes applied:
  - Relaxed yellow threshold to catch anti-aliased and compressed pixels
  - Morphological dilation to bridge gaps caused by text labels over routes
"""
from PIL import Image
import numpy as np
from scipy.ndimage import binary_dilation
import json

# Load the routes image
img = Image.open('frontend/assets/images/airport_plan_routes.png').convert('RGBA')
arr = np.array(img)
height, width = arr.shape[:2]
print(f"Image size: {width} x {height}")

# --- Step 1: Detect yellow pixels (relaxed threshold) ---
# Pure yellow = high R, high G, low B
# Relaxed to catch anti-aliased edges and JPEG-compressed yellows
R = arr[:, :, 0].astype(int)
G = arr[:, :, 1].astype(int)
B = arr[:, :, 2].astype(int)

yellow_mask = (R > 180) & (G > 170) & (B < 130) & ((R - B) > 100) & ((G - B) > 80)

print(f"Yellow pixels detected (relaxed): {yellow_mask.sum()}")

# --- Step 2: Morphological dilation to fill gaps ---
# Expand walkable areas by 3 pixels to bridge anti-aliasing gaps and text holes
struct = np.ones((7, 7), dtype=bool)   # 7x7 kernel = ~3px expansion in each direction
dilated_mask = binary_dilation(yellow_mask, structure=struct)

print(f"After dilation: {dilated_mask.sum()} walkable pixels")

# --- Step 3: Convert to 0/1 list ---
walkable_map = dilated_mask.astype(np.uint8).tolist()

# --- Step 4: Save ---
output = {
    "width": width,
    "height": height,
    "map": walkable_map
}

with open('frontend/assets/walkable_map.json', 'w') as f:
    json.dump(output, f, separators=(',', ':'))  # compact JSON

total = width * height
walkable = dilated_mask.sum()
print(f"Walkable: {walkable}/{total} pixels ({100*walkable/total:.2f}%)")
print(f"Saved to frontend/assets/walkable_map.json")

sz = sum(len(row) * 2 for row in walkable_map) / 1024 / 1024
print(f"Approx file size: ~{sz:.1f} MB")
