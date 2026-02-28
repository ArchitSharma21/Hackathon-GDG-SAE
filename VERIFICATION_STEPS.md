# Coordinate System Fix - Verification Steps

## Changes Applied ✅

### Frontend Changes
1. ✅ Updated `frontend/js/simulation.js`:
   - Changed coordinate transformation from meter-based to pixel-based
   - Updated data source to `hamburg_airport_digital_twin.json`
   - Fixed person starting position to match entrance coordinates
   - Updated TYPE_MAP to include all location types
   - Added floor tracking support

2. ✅ Copied data file:
   - `backend/data/hamburg_airport_digital_twin.json` → `frontend/assets/`

### Backend Changes
1. ✅ Updated `backend/models/airport.py`:
   - Added `floor` field to `AirportNode` model
   - Added `floors` field to `AirportMap` model
   - Updated type comments to include new location types

2. ✅ Updated `backend/services/location_search.py`:
   - Changed default data source to `hamburg_airport_digital_twin.json`
   - Added new location type keywords (exit, stairs, baggage, restaurant)

## How to Verify the Fix

### 1. Access the Simulation

Open your browser and navigate to:
```
http://localhost:8000/simulation.html
```

### 2. Check Browser Console

Open Developer Tools (F12) and check the Console tab. You should see:

```
[GRID] 229×128 | walkable: XXXXX cells
[LOC] entrance_main     floor=1 img( 50, 500) → canvas( 29, 391)
[LOC] exit_south        floor=1 img(700, 500) → canvas(407, 391)
[LOC] security_1        floor=1 img(200, 450) → canvas(116, 352)
...
[LOC] gate_e12          floor=2 img( 60, 100) → canvas( 35,  78)
[LOC] gate_a24          floor=2 img(690, 100) → canvas(401,  78)
...
[LOC] 26 locations loaded from hamburg_airport_digital_twin.json
[READY] Grid + locations loaded — BFS ready
Airport Digital Twin loaded
```

### 3. Visual Verification

**Check Person Position:**
- The yellow circle (YOU marker) should appear in the **bottom-left area** of the map
- This corresponds to the main entrance position
- Coordinates should show approximately: `x: 29, y: 391`

**Check Location Alignment:**
Look at the airport plan image and verify markers align correctly:
- **Entrance** (bottom-left area) ✓
- **Gates E, D, C, B, A** (top area, spread across) ✓
- **Information desks** (center areas) ✓
- **Bathrooms** (left and right sides) ✓

### 4. Test Navigation

Try these navigation queries in the simulation input field:

#### Test 1: Navigate to Gate E12
```
Input: "gate e12"
Expected: Route drawn to top-left area of map
Console: [BFS] gate_e12 | start=(...) dest=(...)
```

#### Test 2: Find Bathroom
```
Input: "bathroom"
Expected: Route to nearest bathroom location
Console: [NLP] "bathroom" → restroom → bathroom_...
```

#### Test 3: Navigate to Exit
```
Input: "exit"
Expected: Route to south exit (bottom-right area)
Console: [NLP] "exit" → exit → exit_south
```

#### Test 4: Find Information Desk
```
Input: "information desk"
Expected: Route to info desk
Console: [NLP] "information desk" → info → info_desk_...
```

#### Test 5: Gate A24 (far right)
```
Input: "gate a24"
Expected: Route drawn to top-right area
Console: → gate "gate_a24" → found
```

### 5. Test Movement

1. **Use Arrow Keys**: Press ↑ ↓ ← → to move the person marker
   - Verify movement stays within walkable areas
   - Check coordinates update in real-time

2. **Reset Position**: Click "Reset to Entrance" button
   - Person should return to (29, 391)
   - "Near: Main Entrance" should display

### 6. Backend API Testing (Optional)

If you want to test the backend API endpoints:

```bash
# Test location search
curl http://localhost:8000/api/search?query=gate%20e12

# Test navigation
curl -X POST http://localhost:8000/api/navigate \
  -H "Content-Type: application/json" \
  -d '{"start": "entrance_main", "destination": "gate_e12"}'
```

Expected response should include locations from the digital_twin.json.

## Expected Outcomes

✅ **Person starts at correct position** (entrance, bottom-left)
✅ **All locations visually aligned** with airport plan image
✅ **Navigation routes make visual sense** (not crossing walls)
✅ **Gate names match image** (E12, D5, C3, B25, A24, etc.)
✅ **All location types searchable** (gate, bathroom, exit, info, restaurant, stairs, baggage)
✅ **No console errors** during loading or navigation
✅ **Coordinates are reasonable** (0-800 for x, 0-600 for y)

## Troubleshooting

### Issue: Locations appear in wrong positions
- Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
- Verify the JSON file was copied correctly
- Check console for loading errors

### Issue: Navigation not working
- Check console for "[READY] Grid + locations loaded" message
- Verify walkable_map.json is present in frontend/assets
- Try simpler queries like "gate e12" instead of natural language

### Issue: Console shows "Failed to load"
- Verify server is running: `curl http://localhost:8000/api/health`
- Check file paths are correct
- Restart server if needed

### Issue: Backend API errors
- Server should auto-reload with --reload flag
- If not, manually restart: `./start.sh` or run uvicorn command
- Check backend/data/hamburg_airport_digital_twin.json exists

## Coordinate Mapping Reference

| Location | Image Coords | Canvas Coords | Visual Area |
|----------|--------------|---------------|-------------|
| entrance_main | (50, 500) | (29, 391) | Bottom-left |
| exit_south | (700, 500) | (407, 391) | Bottom-right |
| info_desk_1 | (400, 500) | (233, 391) | Bottom-center |
| gate_e12 | (60, 100) | (35, 78) | Top-left |
| gate_a24 | (690, 100) | (401, 78) | Top-right |
| gate_c3 | (380, 80) | (221, 63) | Top-center |

Scaling factor:
- X: 1376px image → 800px canvas (÷ 1.72)
- Y: 768px image → 600px canvas (÷ 1.28)

## Success Criteria

The fix is verified successful if:
1. ✅ Person marker appears at entrance (bottom-left, ~29, 391)
2. ✅ All gate markers appear in top area of map
3. ✅ Navigation routes connect start to destination visually
4. ✅ Console shows no errors and confirms locations loaded
5. ✅ Arrow key movement works smoothly
6. ✅ Reset button returns to entrance position
7. ✅ Search queries find correct locations

---

**Last Updated**: 2026-02-28
**Status**: Ready for testing
