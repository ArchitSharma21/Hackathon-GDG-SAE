# Coordinate System Fix - Final Version

## Problem & Solution

### You Were Right! ✅

The coordinate system in **hamburg_airport.json** is correct:
- **Entrance at (0, 0)** in meters
- Should transform to **canvas (400, 540)** - bottom center
- The issue was **incorrect calibration** of SCALE_X and SCALE_Y

## Fixed Coordinate Transformation

### Constants (Recalibrated)
```javascript
const ENTRANCE_CANVAS_X = 400;  // entrance at horizontal center
const ENTRANCE_CANVAS_Y = 540;  // entrance near bottom
const SCALE_X = 3.7;   // pixels per meter, horizontal
const SCALE_Y = 4.0;   // pixels per meter, vertical
```

### Transformation Formula
```javascript
function jsonToCanvas(metersX, metersY) {
    return {
        x: ENTRANCE_CANVAS_X + metersX * SCALE_X,
        y: ENTRANCE_CANVAS_Y - metersY * SCALE_Y   // Y-axis flipped
    };
}
```

## Calibration Details

### Data from hamburg_airport.json
- **X range**: -95m (gate_a5, far west) to +80m (gate_b20, far east) = 175m total
- **Y range**: 0m (entrance) to 110m (gates in north) = 110m depth

### Target Canvas Layout (800×600)
- **Entrance**: (0, 0) meters → **(400, 540)** canvas (bottom-center) ✓
- **Gates**: y=110m → **~100px** from top (gives 540 - 110×4.0 = 100) ✓
- **Left extent**: x=-95m → **~50px** from left (gives 400 - 95×3.7 ≈ 49) ✓
- **Right extent**: x=+80m → **~696px** (gives 400 + 80×3.7 = 696) ✓

### Verification of Key Locations

| Location | Meters (X, Y) | Canvas (X, Y) | Expected Position |
|----------|--------------|---------------|-------------------|
| entrance | (0, 0) | **(400, 540)** | Bottom-center ✓ |
| info_desk | (0, 15) | (400, 480) | Just above entrance ✓ |
| security | (0, 35) | (400, 400) | Middle-center ✓ |
| food_court | (0, 60) | (400, 300) | Upper middle ✓ |
| gate_a5 | (-95, 90) | (49, 180) | Top-left ✓ |
| gate_a1 | (-85, 110) | (85, 100) | Top-left area ✓ |
| gate_b12 | (20, 110) | (474, 100) | Top-center ✓ |
| gate_b15 | (55, 110) | (604, 100) | Top-right ✓ |
| gate_b20 | (80, 110) | (696, 100) | Top-far-right ✓ |
| bathroom_1 | (-65, 85) | (160, 200) | Upper-left ✓ |
| bathroom_2 | (55, 85) | (604, 200) | Upper-right ✓ |

## Changes Made

### Frontend (`frontend/js/simulation.js`)
1. ✅ Reverted to `hamburg_airport.json` (meter-based, entrance at 0,0)
2. ✅ Recalibrated SCALE_X = 3.7 px/m and SCALE_Y = 4.0 px/m
3. ✅ Person starts at (400, 540) - entrance position
4. ✅ Reset button returns to entrance coordinates
5. ✅ Coordinate transformation uses entrance-centered system

### Backend (`backend/services/location_search.py`)
1. ✅ Reverted to use `hamburg_airport.json`

### Test Tool Created
- **test_coordinates.html** - Visual verification of coordinate mapping
  - Shows transformation table
  - Displays visual preview with all locations plotted
  - Access at: `http://localhost:8000/test_coordinates.html`

## How to Verify

### 1. Open Test Page
```
http://localhost:8000/test_coordinates.html
```

**Expected:**
- Table showing all coordinate transformations
- Visual canvas with locations plotted
- Entrance (green) at bottom-center
- Gates (blue) spread across top
- Bathrooms (purple) on left and right sides

### 2. Open Simulation
```
http://localhost:8000/simulation.html
```

**Check Browser Console:**
```
[LOC] entrance       meters(   0,    0) → canvas(400, 540)
[LOC] info_desk      meters(   0,   15) → canvas(400, 480)
[LOC] security       meters(   0,   35) → canvas(400, 400)
[LOC] food_court     meters(   0,   60) → canvas(400, 300)
[LOC] bathroom_1     meters( -65,   85) → canvas(160, 200)
[LOC] bathroom_2     meters(  55,   85) → canvas(604, 200)
[LOC] gate_a1        meters( -85,  110) → canvas( 85, 100)
[LOC] gate_a5        meters( -95,   90) → canvas( 49, 180)
[LOC] gate_b12       meters(  20,  110) → canvas(474, 100)
[LOC] gate_b15       meters(  55,  110) → canvas(604, 100)
[LOC] gate_b20       meters(  80,  110) → canvas(696, 100)
[LOC] 11 locations loaded from hamburg_airport.json
```

**Visual Check:**
- ✅ Person marker (yellow) at bottom-center (400, 540)
- ✅ Gates spread across top of canvas (~y=100)
- ✅ Entrance/info/security/food_court in vertical line down center
- ✅ Bathrooms on left and right sides

### 3. Test Navigation
```
Try: "gate a1"     → route to top-left
Try: "gate b20"    → route to top-right
Try: "bathroom"    → route to nearest bathroom
Try: "food court"  → route to center
```

## Mathematical Verification

### Why SCALE_X = 3.7?
- Horizontal range: -95m to +80m = 175m total
- Available canvas width (with margins): ~650px
- Scale: 650px / 175m ≈ 3.7 px/m
- Verification:
  - Leftmost (gate_a5 at -95m): 400 + (-95×3.7) = 49px ✓
  - Rightmost (gate_b20 at +80m): 400 + (80×3.7) = 696px ✓

### Why SCALE_Y = 4.0?
- Vertical range: 0m to 110m
- Entrance at y=0 → canvas 540 (near bottom)
- Gates at y=110 → target canvas ~100 (near top)
- Scale: (540 - 100) / 110 = 4.0 px/m
- Verification:
  - Gates at 110m: 540 - (110×4.0) = 100px ✓
  - Food court at 60m: 540 - (60×4.0) = 300px (middle) ✓

## Success Criteria

The coordinate system is correct when:
1. ✅ Entrance at meters (0,0) → canvas (400, 540)
2. ✅ All gates appear near top of canvas (~y=100)
3. ✅ Gates spread horizontally across canvas
4. ✅ Central locations (info, security, food) form vertical line
5. ✅ Bathrooms appear on left/right sides
6. ✅ Navigation routes make logical sense
7. ✅ No locations outside canvas bounds (0-800, 0-600)

## Files Modified

1. **frontend/js/simulation.js**
   - Coordinate transformation constants
   - jsonToCanvas() function
   - loadLocations() - uses hamburg_airport.json
   - Person starting position
   - Reset button logic

2. **backend/services/location_search.py**
   - Default data path back to hamburg_airport.json

3. **test_coordinates.html** (NEW)
   - Visual testing tool

## Previous Mistakes

My earlier attempt:
- ❌ Tried to use hamburg_airport_digital_twin.json (different coordinate system)
- ❌ Used pixel-based coordinates instead of meter-based
- ❌ Confused two different datasets

Your correction:
- ✅ hamburg_airport.json is the correct source (entrance at 0,0)
- ✅ Meter-based coordinates should transform to canvas pixels
- ✅ Just needed proper SCALE_X and SCALE_Y calibration

---

**Status**: ✅ Coordinate transformation fixed and calibrated correctly
**Date**: 2026-02-28
**System**: Meter-based coordinates from hamburg_airport.json
**Entrance**: (0, 0) meters → (400, 540) canvas pixels
