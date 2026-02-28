"""
Precompute navigation data from the walkable pixel map.
Downsamples the 1376x768 map to a ~229x128 grid for fast BFS in JS.
Saves grid + key location coordinates to navigation_data.json.
"""
import json
import math
from collections import deque

SCALE = 6  # downsample factor

# ── Load walkable map ──────────────────────────────────────────────────────────
print("Loading walkable map...")
with open('frontend/assets/walkable_map.json') as f:
    raw = json.load(f)

IMG_W = raw['width']   # 1376
IMG_H = raw['height']  # 768
img_map = raw['map']   # list of lists, 0/1

GRID_W = IMG_W // SCALE   # 229
GRID_H = IMG_H // SCALE   # 128

print(f"Image: {IMG_W}x{IMG_H}  →  Grid: {GRID_W}x{GRID_H}")

# ── Downsample: cell walkable if ANY pixel in its block is walkable ────────────
print("Downsampling...")
grid = []
for gy in range(GRID_H):
    row = []
    for gx in range(GRID_W):
        walkable = 0
        for dy in range(SCALE):
            for dx in range(SCALE):
                py = gy * SCALE + dy
                px = gx * SCALE + dx
                if py < IMG_H and px < IMG_W and img_map[py][px] == 1:
                    walkable = 1
                    break
            if walkable:
                break
        row.append(walkable)
    grid.append(row)

walkable_count = sum(sum(row) for row in grid)
print(f"Walkable grid cells: {walkable_count} / {GRID_W * GRID_H}")

# ── Key locations (canvas 800x600 coordinates → image → grid) ─────────────────
# Canvas → Image scale factors
CX = IMG_W / 800   # 1.72
CY = IMG_H / 600   # 1.28

def canvas_to_grid(cx, cy):
    """Convert canvas (800x600) coordinates to downsampled grid coords."""
    ix = cx * CX
    iy = cy * CY
    return int(ix / SCALE), int(iy / SCALE)

def snap_to_walkable(gx, gy, max_radius=20):
    """Snap a grid point to the nearest walkable cell using BFS."""
    if 0 <= gx < GRID_W and 0 <= gy < GRID_H and grid[gy][gx] == 1:
        return gx, gy
    visited = set()
    q = deque([(gx, gy, 0)])
    while q:
        x, y, d = q.popleft()
        if (x, y) in visited or d > max_radius:
            continue
        visited.add((x, y))
        if 0 <= x < GRID_W and 0 <= y < GRID_H and grid[y][x] == 1:
            return x, y
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
            q.append((x+dx, y+dy, d+1))
    return gx, gy  # fallback

# Define all key locations in canvas coordinates (800x600)
raw_locations = [
    # Lower level — Arrivals & Check-in
    { "id": "entrance_main",  "name": "Main Entrance",        "type": "entrance",    "canvas_x": 400, "canvas_y": 560 },
    { "id": "checkin_left",   "name": "Check-in Counters D-E","type": "checkin",     "canvas_x": 250, "canvas_y": 450 },
    { "id": "checkin_right",  "name": "Check-in Counters A-C","type": "checkin",     "canvas_x": 530, "canvas_y": 450 },
    { "id": "baggage_left",   "name": "Baggage Claim West",   "type": "baggage",     "canvas_x": 170, "canvas_y": 490 },
    { "id": "baggage_right",  "name": "Baggage Claim East",   "type": "baggage",     "canvas_x": 640, "canvas_y": 490 },
    { "id": "restroom_lower", "name": "Restroom (Arrivals)",  "type": "restroom",    "canvas_x": 350, "canvas_y": 515 },

    # Transition — Security & Central Hub
    { "id": "security",       "name": "Security Checkpoint",  "type": "security",    "canvas_x": 400, "canvas_y": 340 },
    { "id": "info_desk",      "name": "Information Desk",     "type": "info",        "canvas_x": 400, "canvas_y": 290 },

    # Upper level — Departures & Gates
    { "id": "restroom_upper_w","name": "Restroom West (Gates)","type": "restroom",   "canvas_x": 190, "canvas_y": 185 },
    { "id": "restroom_upper_e","name": "Restroom East (Gates)","type": "restroom",   "canvas_x": 600, "canvas_y": 185 },
    { "id": "food_court",     "name": "Food Court",           "type": "restaurant",  "canvas_x": 420, "canvas_y": 210 },
    { "id": "shopping",       "name": "Shopping Area",        "type": "shop",        "canvas_x": 340, "canvas_y": 210 },

    # Gates — Section E (leftmost)
    { "id": "gate_e12",  "name": "Gate E12",  "type": "gate", "canvas_x":  75, "canvas_y": 95 },
    { "id": "gate_e14",  "name": "Gate E14",  "type": "gate", "canvas_x": 130, "canvas_y": 95 },

    # Gates — Section D
    { "id": "gate_d5",   "name": "Gate D5",   "type": "gate", "canvas_x": 220, "canvas_y": 95 },
    { "id": "gate_d7",   "name": "Gate D7",   "type": "gate", "canvas_x": 275, "canvas_y": 95 },

    # Gates — Section C (center)
    { "id": "gate_c3",   "name": "Gate C3",   "type": "gate", "canvas_x": 375, "canvas_y": 80 },
    { "id": "gate_c6",   "name": "Gate C6",   "type": "gate", "canvas_x": 435, "canvas_y": 80 },

    # Gates — Section B
    { "id": "gate_b25",  "name": "Gate B25",  "type": "gate", "canvas_x": 535, "canvas_y": 95 },
    { "id": "gate_b30",  "name": "Gate B30",  "type": "gate", "canvas_x": 595, "canvas_y": 95 },

    # Gates — Section A (rightmost)
    { "id": "gate_a24",  "name": "Gate A24",  "type": "gate", "canvas_x": 700, "canvas_y": 95 },
]

# Snap all locations to nearest walkable grid cell
locations = []
for loc in raw_locations:
    gx, gy = canvas_to_grid(loc['canvas_x'], loc['canvas_y'])
    sgx, sgy = snap_to_walkable(gx, gy)
    cx_snapped = (sgx * SCALE / CX)
    cy_snapped = (sgy * SCALE / CY)
    locations.append({
        **loc,
        "grid_x": sgx,
        "grid_y": sgy,
        "canvas_x": round(cx_snapped, 1),
        "canvas_y": round(cy_snapped, 1),
    })
    print(f"  {loc['id']:20s}  canvas({loc['canvas_x']},{loc['canvas_y']}) → grid({sgx},{sgy})  walkable={grid[sgy][sgx]}")

# ── BFS from each location: build parent map across entire grid ────────────────
# parent[dest_id] = flat array (GRID_W*GRID_H) where each cell stores index of
# the next step toward that destination, or -1 if unreachable.
# 8-connectivity BFS from destination outward.

DIRS = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]
# Direction index: 0=W 1=E 2=N 3=S 4=NW 5=SW 6=NE 7=SE
# To trace path, from any cell follow the REVERSE of the direction stored there.

print("\nRunning BFS for each destination...")

def bfs_from(start_gx, start_gy):
    """BFS from destination outward. Returns parent dict {(x,y): (px,py)}."""
    parent = {}
    q = deque()
    q.append((start_gx, start_gy))
    parent[(start_gx, start_gy)] = None
    while q:
        x, y = q.popleft()
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < GRID_W and 0 <= ny < GRID_H and grid[ny][nx] == 1 and (nx, ny) not in parent:
                parent[(nx, ny)] = (x, y)  # (x,y) is one step closer to destination
                q.append((nx, ny))
    return parent

def grid_to_canvas(gx, gy):
    """Convert grid coords back to canvas coords."""
    return round(gx * SCALE / CX, 1), round(gy * SCALE / CY, 1)

# For each location, store its BFS parent map as a sparse dict
# Key: "gx,gy"  Value: [next_gx, next_gy]  (one step toward destination)
dest_maps = {}
for loc in locations:
    dest_id = loc['id']
    gx, gy = loc['grid_x'], loc['grid_y']
    parents = bfs_from(gx, gy)
    # Encode sparse: only walkable cells that are reachable
    sparse = {}
    for (cx, cy), parent in parents.items():
        if parent is not None:  # skip the destination itself
            sparse[f"{cx},{cy}"] = [parent[0], parent[1]]
    dest_maps[dest_id] = sparse
    print(f"  {dest_id:20s}  reachable from {len(sparse)} cells")

# ── Save navigation_data.json ──────────────────────────────────────────────────
output = {
    "grid_width":  GRID_W,
    "grid_height": GRID_H,
    "scale":       SCALE,
    "img_width":   IMG_W,
    "img_height":  IMG_H,
    "canvas_width":  800,
    "canvas_height": 600,
    "grid":        grid,
    "locations":   locations,
    "dest_maps":   dest_maps
}

out_path = 'frontend/assets/navigation_data.json'
with open(out_path, 'w') as f:
    json.dump(output, f, separators=(',', ':'))

import os
size_mb = os.path.getsize(out_path) / 1024 / 1024
print(f"\nSaved to {out_path}  ({size_mb:.2f} MB)")
print("Done!")
