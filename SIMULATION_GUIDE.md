# Digital Twin Simulation Guide

## Overview

The **Airport Digital Twin Simulation** is an interactive 2D visualization that simulates a person navigating through Hamburg Airport. It provides real-time position tracking and syncs with the navigation app interface.

## Features

### 2D Airport Visualization
- **Two floors** - Floor 1 (Arrivals) and Floor 2 (Departures)
- **20+ locations** including:
  - 4 Gates (A1, A2, B1, B2)
  - 4 Bathrooms
  - 4 Restaurants/Cafes
  - 2 Security checkpoints
  - 2 Information desks
  - Entrances, exits, baggage claim, stairs

### Interactive Controls
- **Click to move** - Click anywhere on the map to move the person
- **Keyboard controls** - Use arrow keys (↑ ↓ ← →) to move step by step
- **Floor switching** - Toggle between Floor 1 and Floor 2
- **Real-time tracking** - Coordinates and nearest location update automatically

### Phone Mockup
- Shows the actual navigation app interface
- Receives real-time position updates from the simulation
- Fully functional voice interface
- Turn-by-turn navigation synced with person's position

## How to Use

### 1. Access the Simulation

Open in your browser:
```
http://localhost:8000/simulation.html
```

### 2. Navigate the Airport

**Option A: Click to Move**
1. Click anywhere on the airport map
2. The person (yellow circle with "YOU") will move to that location
3. Watch the coordinates and position info update

**Option B: Keyboard Controls**
1. Use arrow keys to move:
   - ↑ = Move up
   - ↓ = Move down
   - ← = Move left
   - → = Move right

### 3. Switch Floors

Use the "Floor" dropdown in the top-right:
- Floor 1 = Arrivals level (baggage claim, arrivals security)
- Floor 2 = Departures level (gates, departures security)

Note: When you switch floors, you're simulating taking the stairs/escalator

### 4. Use the Navigation App

The phone mockup on the right shows the real app interface:

1. **Voice Commands:**
   - Click the microphone button in the phone
   - Say "Where is gate A1?"
   - Say "Find bathroom"
   - The app will calculate a route based on your current position

2. **Quick Actions:**
   - Click "Find Bathroom"
   - Click "My Flight"
   - Click "Info Desk"

3. **Navigation:**
   - Once navigation starts, move your person using the map
   - The app will update as you move
   - Click "Next Step" to advance through turn-by-turn directions

### 5. Test Scenarios

#### Scenario 1: Arriving Passenger Looking for Bathroom
```
1. Start at Main Entrance (default position, Floor 1)
2. In the phone, click "Find Bathroom"
3. App calculates route to nearest bathroom
4. Click on the map to move toward the bathroom
5. Watch navigation update in real-time
```

#### Scenario 2: Find Your Gate
```
1. Move to Floor 2 (use dropdown)
2. Click near the stairs
3. In the phone, say "Where is gate B1?"
4. Follow the navigation directions
5. Move the person to gate B1
```

#### Scenario 3: Emergency Help
```
1. Be anywhere in the airport
2. Click the emergency button in the phone
3. App routes you to nearest info desk
4. Follow directions on the map
```

## Map Legend

| Color | Location Type |
|-------|---------------|
| 🟢 Green | Entrance/Exit |
| 🔵 Blue | Gates |
| 🟠 Orange | Restaurants |
| 🟣 Purple | Bathrooms |
| 🔴 Red | Info Desk |
| ⚫ Gray | Security |
| 🟡 Yellow | Person (You) |
| 💠 Dashed Line | Navigation Path |

## Tips & Tricks

### For Demonstrations

1. **Start with Floor Overview**
   - Show Floor 1 first (arrivals)
   - Point out key locations
   - Switch to Floor 2 to show gates

2. **Demonstrate Voice Commands**
   - Use natural language: "Where is the bathroom?"
   - Show different query types: gates, restaurants, info desk

3. **Show Real-Time Sync**
   - Start navigation in the app
   - Move the person on the map
   - Highlight how position updates automatically

4. **Emergency Feature**
   - Demonstrate from any location
   - Show fastest route to help

### For Testing

1. **Test All Location Types**
   - Navigate to each type of location
   - Verify voice search finds them
   - Check navigation routes work

2. **Test Floor Changes**
   - Navigate from Floor 1 to Floor 2
   - Ensure stairs/escalators are part of route

3. **Test Edge Cases**
   - Navigate to same floor locations
   - Navigate across floors
   - Test from extreme positions (corners)

## Technical Details

### Coordinate System
- Canvas: 800x600 pixels
- X-axis: 0 (left) to 800 (right)
- Y-axis: 0 (top) to 600 (bottom)
- Coordinates map directly to location positions

### Position Updates
- Updates sent every movement frame
- Message format:
  ```javascript
  {
    type: 'position_update',
    location: 'location_id',
    name: 'Location Name',
    floor: 1 or 2,
    coordinates: {x: number, y: number}
  }
  ```

### Navigation Sync
- Person position → App receives location update
- App starts navigation → Map shows path (if enabled)
- Real-time bidirectional communication via postMessage API

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| ↑ | Move up |
| ↓ | Move down |
| ← | Move left |
| → | Move right |

## Buttons

- **Reset to Entrance** - Move person back to starting position
- **Toggle Navigation Path** - Show/hide the calculated route on map
- **Show Labels** - Toggle location name labels on/off

## Troubleshooting

### Person not moving when clicking
- Ensure you're clicking inside the map canvas
- Try keyboard controls instead
- Check browser console for errors

### App not syncing with position
- Refresh the page
- Check that the iframe loaded correctly
- Open browser console to see position update messages

### Voice not working
- Allow microphone permissions
- Use Chrome or Edge browser
- Try Quick Action buttons instead

### Floor switching issues
- Locations are floor-specific
- Person doesn't automatically move when switching floors
- You need to manually move to stairs to change floors realistically

## Advanced Features

### Path Visualization
1. Enable "Toggle Navigation Path"
2. Start navigation in the app
3. See the calculated route drawn on the map as a dashed line

### Nearest Location Detection
- System automatically detects which location you're closest to
- Updates in real-time as you move
- Used to determine current position for navigation

## Demo Script

**5-Minute Demo Flow:**

1. **Introduction (30 sec)**
   - "This is a digital twin of Hamburg Airport"
   - "Left side = 2D map, Right side = actual app"

2. **Show Map (1 min)**
   - Point out Floor 1 locations
   - Switch to Floor 2, show gates
   - Explain movement controls

3. **Voice Navigation (2 min)**
   - Click to move person to entrance
   - Use voice: "Where is gate A1?"
   - Show route calculation
   - Move person along route
   - Demonstrate real-time position sync

4. **Quick Features (1 min)**
   - Test "Find Bathroom" button
   - Show emergency help
   - Demonstrate floor switching

5. **Wrap-up (30 sec)**
   - Explain real-world application
   - Mention indoor positioning would replace simulation
   - Show accessibility features

## Future Enhancements

Potential additions to the simulation:
- [ ] Animated walking (smooth transitions)
- [ ] Obstacle avoidance visualization
- [ ] Multiple people/avatars
- [ ] Real-time crowd density
- [ ] 3D isometric view option
- [ ] Import real airport floor plans
- [ ] Record and playback navigation sessions
- [ ] A/B test different navigation algorithms

---

**Enjoy exploring the digital twin!** This simulation demonstrates the complete system without needing real indoor positioning hardware. Perfect for demos, testing, and development.
