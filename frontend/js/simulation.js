// Airport Digital Twin Simulation
// Locations are loaded from hamburg_airport.json with meter-based coordinates
// where origin (0,0) is the Main Entrance at bottom-center of the terminal.
// Pathfinding runs live BFS on the walkable grid for every query.

// ── Grid constants (must match generate_walkable_map.py) ──────────────────────
const SCALE  = 6;
const IMG_W  = 1376;
const IMG_H  = 768;
const CANVAS_W = 800;
const CANVAS_H = 600;
const GRID_W = Math.floor(IMG_W / SCALE);   // 229
const GRID_H = Math.floor(IMG_H / SCALE);   // 128

// Factors to go canvas-pixel → image-pixel
const CX = IMG_W / CANVAS_W;   // 1.72
const CY = IMG_H / CANVAS_H;   // 1.28

// ── Coordinate transformation ─────────────────────────────────────────────────
//
// JSON space   →  Canvas space
//  origin        Main Entrance (0, 0)           →  bottom-center (400, 540)
//  X axis        negative=west, positive=east   →  same direction
//  Y axis        positive=deeper into terminal  →  FLIPPED (canvas Y grows down)
//  units         meters (estimated)             →  pixels
//
// Calibration based on actual visual positions in airport_plan.png:
//   Measured from image:
//     Entrance (0, 0) → canvas (410, 540)
//     Restroom 1A (-65, 85) → canvas (280, 270)
//     Restroom 1B (55, 85) → canvas (520, 270)
//
//   Calculated scaling:
//     SCALE_X = (520-280)/(55-(-65)) = 240/120 = 2.0 px/m
//     SCALE_Y = (540-270)/85 = 270/85 ≈ 3.176 px/m

const ENTRANCE_CANVAS_X = 410;  // entrance position (measured from image)
const ENTRANCE_CANVAS_Y = 540;  // entrance near bottom
const SCALE_X = 2.0;   // pixels per meter, horizontal
const SCALE_Y = 270 / 85;   // pixels per meter, vertical (≈3.176, will be flipped)

function jsonToCanvas(metersX, metersY) {
    return {
        x: ENTRANCE_CANVAS_X + metersX * SCALE_X,
        y: ENTRANCE_CANVAS_Y - metersY * SCALE_Y   // flip Y axis
    };
}

function canvasToMeters(canvasX, canvasY) {
    return {
        x: (canvasX - ENTRANCE_CANVAS_X) / SCALE_X,
        y: (ENTRANCE_CANVAS_Y - canvasY) / SCALE_Y
    };
}

function canvasDistance(x1, y1, x2, y2) {
    const dx = x2 - x1;
    const dy = y2 - y1;
    return Math.sqrt(dx * dx + dy * dy);
}

function canvasDistanceInMeters(x1, y1, x2, y2) {
    const dist = canvasDistance(x1, y1, x2, y2);
    // Average the X and Y scales for distance calculation
    const avgScale = (SCALE_X + SCALE_Y) / 2;
    return dist / avgScale;
}

function getDirection(fromX, fromY, toX, toY) {
    const angle = Math.atan2(toY - fromY, toX - fromX);
    const degrees = angle * 180 / Math.PI;

    // Convert to compass directions
    // 0° = East, 90° = South, 180° = West, -90° = North
    if (degrees > -22.5 && degrees <= 22.5) return 'east';
    if (degrees > 22.5 && degrees <= 67.5) return 'southeast';
    if (degrees > 67.5 && degrees <= 112.5) return 'south';
    if (degrees > 112.5 && degrees <= 157.5) return 'southwest';
    if (degrees > 157.5 || degrees <= -157.5) return 'west';
    if (degrees > -157.5 && degrees <= -112.5) return 'northwest';
    if (degrees > -112.5 && degrees <= -67.5) return 'north';
    if (degrees > -67.5 && degrees <= -22.5) return 'northeast';
    return 'forward';
}

function getTurnInstruction(currentDir, nextDir) {
    const dirs = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest'];
    const currentIdx = dirs.indexOf(currentDir);
    const nextIdx = dirs.indexOf(nextDir);

    if (currentIdx === -1 || nextIdx === -1) return '';

    let diff = (nextIdx - currentIdx + 8) % 8;

    if (diff === 0) return '';
    if (diff === 1 || diff === 2) return 'turn slightly right';
    if (diff === 3) return 'turn right';
    if (diff === 4) return 'turn around';
    if (diff === 5) return 'turn left';
    if (diff === 6 || diff === 7) return 'turn slightly left';

    return '';
}

// JSON type → internal type (used by NLP matching)
const TYPE_MAP = {
    entrance : 'entrance',
    info     : 'info',
    security : 'security',
    food     : 'restaurant',
    bathroom : 'restroom',
    gate     : 'gate',
};

// ── BFS helpers ───────────────────────────────────────────────────────────────
const DIRS = [[-1,0],[1,0],[0,-1],[0,1],[-1,-1],[1,-1],[-1,1],[1,1]];

function canvasToGrid(cx, cy) {
    return {
        x: Math.min(GRID_W - 1, Math.max(0, Math.floor((cx * CX) / SCALE))),
        y: Math.min(GRID_H - 1, Math.max(0, Math.floor((cy * CY) / SCALE)))
    };
}

function gridToCanvas(gx, gy) {
    return {
        x: (gx * SCALE) / CX,
        y: (gy * SCALE) / CY
    };
}

// Snap a canvas point to the nearest walkable grid cell
function snapToWalkable(grid, cx, cy) {
    let g = canvasToGrid(cx, cy);
    if (grid[g.y]?.[g.x] === 1) return g;
    const seen = new Set();
    const q = [[g.x, g.y]];
    seen.add(g.y * GRID_W + g.x);
    for (let i = 0; i < q.length && i < 600; i++) {
        const [x, y] = q[i];
        if (grid[y]?.[x] === 1) return { x, y };
        for (const [dx, dy] of DIRS) {
            const nx = x + dx, ny = y + dy;
            if (nx < 0 || nx >= GRID_W || ny < 0 || ny >= GRID_H) continue;
            const k = ny * GRID_W + nx;
            if (!seen.has(k)) { seen.add(k); q.push([nx, ny]); }
        }
    }
    return g;
}

// BFS from startGrid → destGrid; returns array of canvas {x,y} or null
function bfsPath(grid, startG, destG) {
    const key = (x, y) => y * GRID_W + x;
    const startK = key(startG.x, startG.y);
    const destK  = key(destG.x,  destG.y);
    if (startK === destK) return [gridToCanvas(startG.x, startG.y)];

    const parent = new Int32Array(GRID_W * GRID_H).fill(-1);
    parent[startK] = startK;

    const queue = [startK];
    let head = 0, found = false;

    while (head < queue.length) {
        const cur = queue[head++];
        const cx = cur % GRID_W;
        const cy = Math.floor(cur / GRID_W);
        for (const [dx, dy] of DIRS) {
            const nx = cx + dx, ny = cy + dy;
            if (nx < 0 || nx >= GRID_W || ny < 0 || ny >= GRID_H) continue;
            const nk = key(nx, ny);
            if (parent[nk] !== -1) continue;
            if (grid[ny]?.[nx] !== 1) continue;
            parent[nk] = cur;
            if (nk === destK) { found = true; break; }
            queue.push(nk);
        }
        if (found) break;
    }

    if (!found) return null;

    // Reconstruct path dest → start, then reverse
    const raw = [];
    let cur = destK;
    for (let safety = 0; cur !== startK && safety < 20000; safety++) {
        raw.push(gridToCanvas(cur % GRID_W, Math.floor(cur / GRID_W)));
        cur = parent[cur];
    }
    raw.push(gridToCanvas(startG.x, startG.y));
    return raw.reverse();
}

// ── Simulation class ──────────────────────────────────────────────────────────

class AirportSimulation {
    constructor() {
        this.canvas = document.getElementById('airport-map');
        this.ctx    = this.canvas.getContext('2d');

        // Person marker - start at main entrance
        // entrance in hamburg_airport.json: (0, 0) meters
        // → canvas coordinates: (410, 540) based on actual image measurements
        this.person = { x: 410, y: 540, dotRadius: 3, visualRadius: 12 };

        // Walkable grid loaded from walkable_map.json then downsampled
        this.grid = null;

        // Locations loaded + transformed from hamburg_airport.json
        this.locations = [];   // [{ id, name, type, canvas_x, canvas_y }, ...]

        // Active route drawn on the map
        this.routePath = [];
        this.routeDestName = '';

        // Voice navigation
        this.navigationInstructions = [];  // Array of {text, position, distance, direction}
        this.currentInstructionIndex = 0;
        this.voiceEnabled = true;
        this.lastSpokenInstruction = -1;

        // Manual keyboard movement
        this.isMoving = false;
        this.targetX = null;
        this.targetY = null;
        this.moveSpeed = 2;

        this.airportPlanImage = null;

        // Text-to-speech
        this.speechSynth = window.speechSynthesis;

        this.init();
    }

    // ── Initialisation ────────────────────────────────────────────────────────

    init() {
        this.loadAirportPlan();
        // Load grid and locations in parallel; navigate button stays disabled
        // until both are ready
        this._gridReady     = false;
        this._locationsReady = false;
        this.loadGrid();
        this.loadLocations();
        this.setupEventListeners();
        this.startAnimationLoop();
    }

    loadAirportPlan() {
        this.airportPlanImage = new Image();
        this.airportPlanImage.src = '/assets/images/airport_plan.png';
        this.airportPlanImage.onload = () => this.draw();
    }

    async loadGrid() {
        this._setNavBtn(false, 'Loading map…');
        try {
            const res  = await fetch('/assets/walkable_map.json');
            const data = await res.json();
            const raw  = data.map;  // full 1376×768 binary map

            // Downsample SCALE× — cell is walkable if any pixel in the block is
            const g = [];
            for (let gy = 0; gy < GRID_H; gy++) {
                const row = [];
                outer: for (let gx = 0; gx < GRID_W; gx++) {
                    for (let dy = 0; dy < SCALE; dy++) {
                        for (let dx = 0; dx < SCALE; dx++) {
                            if (raw[gy * SCALE + dy]?.[gx * SCALE + dx] === 1) {
                                row.push(1); continue outer;
                            }
                        }
                    }
                    row.push(0);
                }
                g.push(row);
            }
            this.grid = g;
            const wc = g.reduce((s, r) => s + r.reduce((a, v) => a + v, 0), 0);
            console.log(`[GRID] ${GRID_W}×${GRID_H} | walkable: ${wc} cells`);
        } catch (e) {
            console.error('[GRID] Failed to load walkable map:', e);
            this._setNavBtn(false, 'Map unavailable');
            return;
        }
        this._gridReady = true;
        this._checkReady();
    }

    async loadLocations() {
        try {
            // Load hamburg_airport.json with meter-based coordinates
            const res  = await fetch('/assets/hamburg_airport.json');
            const data = await res.json();

            this.locations = data.nodes.map(node => {
                const { x: cx, y: cy } = jsonToCanvas(
                    node.coordinates.x,
                    node.coordinates.y
                );
                const internalType = TYPE_MAP[node.type] ?? node.type;
                console.log(
                    `[LOC] ${node.id.padEnd(12)} ` +
                    `meters(${String(node.coordinates.x).padStart(4)}, ${String(node.coordinates.y).padStart(4)}) ` +
                    `→ canvas(${Math.round(cx).toString().padStart(3)}, ${Math.round(cy).toString().padStart(3)})`
                );
                return {
                    id      : node.id,
                    name    : node.name,
                    type    : internalType,
                    canvas_x: Math.round(cx),
                    canvas_y: Math.round(cy),
                };
            });

            console.log(`[LOC] ${this.locations.length} locations loaded from hamburg_airport.json`);
        } catch (e) {
            console.error('[LOC] Failed to load hamburg_airport.json:', e);
            this._setNavBtn(false, 'Locations unavailable');
            return;
        }
        this._locationsReady = true;
        this._checkReady();
    }

    _checkReady() {
        if (this._gridReady && this._locationsReady) {
            this._setNavBtn(true, 'Navigate');
            this._setStatus('', false);
            console.log('[READY] Grid + locations loaded — BFS ready');
        }
    }

    _setNavBtn(enabled, label) {
        const btn = document.getElementById('nav-go');
        if (!btn) return;
        btn.disabled  = !enabled;
        btn.textContent = label;
    }

    // ── Walkability (for keyboard movement) ───────────────────────────────────

    isPositionWalkable(x, y) {
        if (!this.grid) return true;
        const g = canvasToGrid(x, y);
        return this.grid[g.y]?.[g.x] === 1;
    }

    // ── Navigation ────────────────────────────────────────────────────────────

    // Resolve query → location id → run BFS → draw red path
    navigateByQuery(query) {
        if (!this.grid || !this.locations.length) {
            this._setStatus('Map is still loading…', true); return;
        }
        const q = query.toLowerCase().trim();
        console.group(`[NLP] "${query}"`);

        let destId = null;

        // Type-based lookups
        if (/\b(restroom|bathroom|toilet|wc|lavatory)\b/.test(q)) {
            destId = this._nearestOfType('restroom')?.id;
            console.log(`→ restroom → ${destId}`);

        } else if (/\b(restaurant|food|eat|cafe|hungry)\b/.test(q)) {
            destId = this._nearestOfType('restaurant')?.id;
            console.log(`→ restaurant → ${destId}`);

        } else if (/security/.test(q)) {
            destId = this.locations.find(l => l.type === 'security')?.id;
            console.log(`→ security → ${destId}`);

        } else if (/\b(entrance|exit|entry)\b/.test(q)) {
            destId = this.locations.find(l => l.type === 'entrance')?.id;
            console.log(`→ entrance → ${destId}`);

        } else if (/\b(info|information)\b/.test(q)) {
            destId = this.locations.find(l => l.type === 'info')?.id;
            console.log(`→ info → ${destId}`);

        } else if (/gate/.test(q)) {
            // Match patterns like "gate a24", "gate e 12", "gate_d5"
            const m = q.match(/gate[\s_]*([a-e])\s*(\d+)/i);
            if (m) {
                const gateId = `gate_${m[1].toLowerCase()}${m[2]}`;
                const loc = this.locations.find(l => l.id === gateId);
                console.log(`→ gate "${gateId}" → ${loc ? 'found' : 'NOT FOUND'}`);
                if (!loc) {
                    console.log('Available gates:',
                        this.locations.filter(l => l.type === 'gate').map(l => l.id).join(', '));
                }
                destId = loc?.id;
            } else {
                console.log('gate pattern not matched');
            }

        } else {
            // Fallback: match by id or name substring
            const loc = this.locations.find(l =>
                l.id === q.replace(/\s+/g, '_') ||
                l.name.toLowerCase().includes(q)
            );
            console.log(`→ fallback: ${loc?.id ?? 'none'}`);
            destId = loc?.id;
        }

        console.groupEnd();

        if (destId) {
            this._showRoute(destId);
        } else {
            this._setStatus(`Could not understand: "${query}"`, true);
            console.log('All IDs:', this.locations.map(l => l.id).join(', '));
        }
    }

    _showRoute(destId) {
        const destLoc = this.locations.find(l => l.id === destId);
        if (!destLoc) { this._setStatus(`Unknown: ${destId}`, true); return; }

        // Snap both endpoints onto the walkable grid
        const startG = snapToWalkable(this.grid, this.person.x,   this.person.y);
        const destG  = snapToWalkable(this.grid, destLoc.canvas_x, destLoc.canvas_y);

        console.log(`[BFS] ${destId} | start=(${startG.x},${startG.y}) dest=(${destG.x},${destG.y})`);

        const path = bfsPath(this.grid, startG, destG);

        if (!path || path.length < 2) {
            this._setStatus(`No walkable route to "${destLoc.name}"`, true);
            console.warn('[BFS] No path found');
            return;
        }

        this.routePath     = path;
        this.routeDestName = destLoc.name;
        this._setStatus(`Route to: ${destLoc.name}  (${path.length} steps)`, false);
        console.log(`[BFS] Path found — ${path.length} waypoints`);

        // Generate turn-by-turn voice instructions
        this._generateVoiceInstructions();
    }

    _nearestOfType(type) {
        const candidates = this.locations.filter(l => l.type === type);
        if (!candidates.length) return null;
        return candidates.reduce((best, loc) => {
            const d = Math.hypot(this.person.x - loc.canvas_x, this.person.y - loc.canvas_y);
            return d < Math.hypot(this.person.x - best.canvas_x, this.person.y - best.canvas_y)
                ? loc : best;
        });
    }

    clearRoute() {
        this.routePath = [];
        this.routeDestName = '';
        this.navigationInstructions = [];
        this.currentInstructionIndex = 0;
        this.lastSpokenInstruction = -1;
        this._setStatus('', false);

        // Stop any ongoing speech
        if (this.speechSynth) {
            this.speechSynth.cancel();
        }

        // Hide voice controls
        const voiceControls = document.getElementById('voice-controls');
        if (voiceControls) {
            voiceControls.style.display = 'none';
        }
    }

    _generateVoiceInstructions() {
        this.navigationInstructions = [];
        this.currentInstructionIndex = 0;
        this.lastSpokenInstruction = -1;

        if (!this.routePath || this.routePath.length < 2) return;

        const path = this.routePath;
        const instructions = [];

        // Simplify path by removing intermediate points in same direction
        const simplified = [path[0]];
        let currentDir = null;

        for (let i = 1; i < path.length; i++) {
            const dir = getDirection(
                simplified[simplified.length - 1].x,
                simplified[simplified.length - 1].y,
                path[i].x,
                path[i].y
            );

            // Add waypoint if direction changed or it's the last point
            if (dir !== currentDir || i === path.length - 1) {
                simplified.push(path[i]);
                currentDir = dir;
            }
        }

        console.log(`[VOICE] Simplified path: ${path.length} → ${simplified.length} waypoints`);

        // Generate instructions for each segment
        let prevDirection = null;

        for (let i = 0; i < simplified.length - 1; i++) {
            const from = simplified[i];
            const to = simplified[i + 1];

            const distance = canvasDistanceInMeters(from.x, from.y, to.x, to.y);
            const direction = getDirection(from.x, from.y, to.x, to.y);

            let instructionText = '';

            if (i === 0) {
                // First instruction
                instructionText = `Starting navigation to ${this.routeDestName}. `;
                instructionText += `Move ${Math.round(distance)} meters ${direction}.`;
            } else {
                // Subsequent instructions
                const turn = getTurnInstruction(prevDirection, direction);
                if (turn) {
                    instructionText = `${turn.charAt(0).toUpperCase() + turn.slice(1)}, then move ${Math.round(distance)} meters ${direction}.`;
                } else {
                    instructionText = `Continue ${Math.round(distance)} meters ${direction}.`;
                }
            }

            instructions.push({
                text: instructionText,
                position: to,
                distance: distance,
                direction: direction,
                waypointIndex: i
            });

            prevDirection = direction;
        }

        // Add final instruction
        instructions.push({
            text: `You have arrived at ${this.routeDestName}.`,
            position: simplified[simplified.length - 1],
            distance: 0,
            direction: 'arrived',
            waypointIndex: simplified.length - 1
        });

        this.navigationInstructions = instructions;

        console.log('[VOICE] Generated instructions:', instructions.map(i => i.text));

        // Speak first instruction
        this._speakCurrentInstruction();
    }

    _speakCurrentInstruction() {
        if (!this.voiceEnabled) return;
        if (this.currentInstructionIndex >= this.navigationInstructions.length) return;
        if (this.currentInstructionIndex === this.lastSpokenInstruction) return;

        const instruction = this.navigationInstructions[this.currentInstructionIndex];

        console.log(`[VOICE] Speaking: "${instruction.text}"`);

        if (this.speechSynth) {
            this.speechSynth.cancel();

            const utterance = new SpeechSynthesisUtterance(instruction.text);
            utterance.rate = 0.9;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;

            this.speechSynth.speak(utterance);
        }

        this.lastSpokenInstruction = this.currentInstructionIndex;

        // Update status display
        this._setStatus(`🔊 ${instruction.text}`, false);

        // Update instruction counter
        const counterEl = document.getElementById('instruction-counter');
        if (counterEl) {
            counterEl.textContent = `Step ${this.currentInstructionIndex + 1}/${this.navigationInstructions.length}`;
        }

        // Show voice controls
        const voiceControls = document.getElementById('voice-controls');
        if (voiceControls) {
            voiceControls.style.display = 'block';
        }
    }

    _checkNavigationProgress() {
        if (this.navigationInstructions.length === 0) return;
        if (this.currentInstructionIndex >= this.navigationInstructions.length) return;

        const currentInstruction = this.navigationInstructions[this.currentInstructionIndex];
        const targetPos = currentInstruction.position;

        // Check if person is close to the current waypoint
        const distToWaypoint = canvasDistance(
            this.person.x, this.person.y,
            targetPos.x, targetPos.y
        );

        // Threshold: 20 pixels (about 5-7 meters)
        if (distToWaypoint < 20) {
            // Move to next instruction
            this.currentInstructionIndex++;

            if (this.currentInstructionIndex < this.navigationInstructions.length) {
                console.log(`[VOICE] Reached waypoint ${this.currentInstructionIndex}, speaking next instruction`);
                this._speakCurrentInstruction();
            } else {
                console.log('[VOICE] Navigation complete!');
            }
        }
    }

    _setStatus(text, isError) {
        const el = document.getElementById('nav-status');
        if (!el) return;
        if (!text) { el.style.display = 'none'; return; }
        el.style.display        = 'block';
        el.textContent          = text;
        el.style.borderLeftColor = isError ? '#FF3333' : '#00aa55';
        el.style.color          = isError ? '#c00'    : '#006633';
        el.style.background     = isError
            ? 'rgba(255,51,51,0.1)' : 'rgba(0,170,85,0.1)';
    }

    // ── Manual movement ───────────────────────────────────────────────────────

    updateMovement() {
        if (!this.isMoving) return;
        const dx = this.targetX - this.person.x;
        const dy = this.targetY - this.person.y;
        const dist = Math.hypot(dx, dy);
        if (dist < this.moveSpeed) {
            this.person.x = this.targetX;
            this.person.y = this.targetY;
            this.isMoving = false;
        } else {
            const nx = this.person.x + (dx / dist) * this.moveSpeed;
            const ny = this.person.y + (dy / dist) * this.moveSpeed;
            if (this.isPositionWalkable(nx, ny)) {
                this.person.x = nx;
                this.person.y = ny;
            } else {
                this.isMoving = false;
            }
        }
        this._updatePositionUI();
        this._checkNavigationProgress();
    }

    // ── Events ────────────────────────────────────────────────────────────────

    setupEventListeners() {
        document.addEventListener('keydown', (e) => {
            const step = 10;
            let nx = this.person.x, ny = this.person.y;
            switch (e.key) {
                case 'ArrowUp':    e.preventDefault(); ny -= step; break;
                case 'ArrowDown':  e.preventDefault(); ny += step; break;
                case 'ArrowLeft':  e.preventDefault(); nx -= step; break;
                case 'ArrowRight': e.preventDefault(); nx += step; break;
                default: return;
            }
            nx = Math.max(0, Math.min(CANVAS_W, nx));
            ny = Math.max(0, Math.min(CANVAS_H, ny));
            if (this.isPositionWalkable(nx, ny)) {
                this.person.x = nx;
                this.person.y = ny;
                this._updatePositionUI();
                this._checkNavigationProgress();
            }
        });

        const resetBtn = document.getElementById('reset-position');
        if (resetBtn) resetBtn.addEventListener('click', () => {
            this.clearRoute();
            // Reset to main entrance (0, 0 in meters)
            this.person.x = ENTRANCE_CANVAS_X;
            this.person.y = ENTRANCE_CANVAS_Y;
            this._updatePositionUI();
        });

        const stopBtn = document.getElementById('stop-navigation');
        if (stopBtn) stopBtn.addEventListener('click', () => this.clearRoute());

        const navInput = document.getElementById('nav-query');
        const navBtn   = document.getElementById('nav-go');
        if (navBtn && navInput) {
            navBtn.addEventListener('click',
                () => this.navigateByQuery(navInput.value));
            navInput.addEventListener('keydown',
                e => { if (e.key === 'Enter') this.navigateByQuery(navInput.value); });
        }

        // Voice control buttons
        const repeatBtn = document.getElementById('repeat-instruction');
        if (repeatBtn) repeatBtn.addEventListener('click', () => {
            this.lastSpokenInstruction = -1; // Force re-speak
            this._speakCurrentInstruction();
        });

        const toggleVoiceBtn = document.getElementById('toggle-voice');
        if (toggleVoiceBtn) toggleVoiceBtn.addEventListener('click', () => {
            this.voiceEnabled = !this.voiceEnabled;
            toggleVoiceBtn.textContent = this.voiceEnabled ? '🔇 Voice Off' : '🔊 Voice On';
            if (!this.voiceEnabled && this.speechSynth) {
                this.speechSynth.cancel();
            }
        });

        window.addEventListener('message', (e) => {
            if (e.data?.type === 'navigate_to')    this.navigateByQuery(e.data.query ?? '');
            if (e.data?.type === 'stop_navigation') this.clearRoute();
        });
    }

    // ── Animation loop ────────────────────────────────────────────────────────

    startAnimationLoop() {
        const tick = () => {
            this.updateMovement();
            this.draw();
            requestAnimationFrame(tick);
        };
        tick();
    }

    // ── Drawing ───────────────────────────────────────────────────────────────

    draw() {
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Background
        if (this.airportPlanImage?.complete) {
            ctx.drawImage(this.airportPlanImage, 0, 0, this.canvas.width, this.canvas.height);
        } else {
            ctx.fillStyle = '#1a1a2e';
            ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        }

        if (this.routePath.length > 1) this._drawRoute();
        this._drawPerson();
    }

    _drawRoute() {
        const ctx  = this.ctx;
        const path = this.routePath;

        // Soft glow
        ctx.beginPath();
        ctx.moveTo(path[0].x, path[0].y);
        for (let i = 1; i < path.length; i++) ctx.lineTo(path[i].x, path[i].y);
        ctx.strokeStyle = 'rgba(255,60,60,0.35)';
        ctx.lineWidth   = 10;
        ctx.lineJoin    = 'round';
        ctx.lineCap     = 'round';
        ctx.stroke();

        // Solid red line
        ctx.beginPath();
        ctx.moveTo(path[0].x, path[0].y);
        for (let i = 1; i < path.length; i++) ctx.lineTo(path[i].x, path[i].y);
        ctx.strokeStyle = '#FF2222';
        ctx.lineWidth   = 3;
        ctx.stroke();

        // Destination pin
        const dest = path[path.length - 1];
        ctx.beginPath();
        ctx.arc(dest.x, dest.y, 8, 0, Math.PI * 2);
        ctx.fillStyle   = '#00FFDD';
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth   = 2;
        ctx.stroke();

        // Label
        if (this.routeDestName) {
            ctx.font      = 'bold 13px sans-serif';
            ctx.textAlign = 'center';
            ctx.strokeStyle = '#000';
            ctx.lineWidth   = 3;
            ctx.strokeText(this.routeDestName, dest.x, dest.y - 14);
            ctx.fillStyle = '#fff';
            ctx.fillText(this.routeDestName, dest.x, dest.y - 14);
        }
    }

    _drawPerson() {
        const ctx      = this.ctx;
        const hasRoute = this.routePath.length > 0;
        const color    = hasRoute ? '#FF3333' : '#FFD700';

        // Outer ring
        ctx.beginPath();
        ctx.arc(this.person.x, this.person.y, this.person.visualRadius, 0, Math.PI * 2);
        ctx.fillStyle   = hasRoute ? 'rgba(255,51,51,0.25)' : 'rgba(255,215,0,0.25)';
        ctx.fill();
        ctx.strokeStyle = color;
        ctx.lineWidth   = 2;
        ctx.stroke();

        // Inner dot
        ctx.beginPath();
        ctx.arc(this.person.x, this.person.y, this.person.dotRadius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();

        // Direction arrow toward first step of route
        if (hasRoute && this.routePath.length > 1) {
            const target = this.routePath[1];
            const angle  = Math.atan2(target.y - this.person.y, target.x - this.person.x);
            const r      = this.person.visualRadius;
            ctx.beginPath();
            ctx.moveTo(this.person.x + Math.cos(angle) * r,
                       this.person.y + Math.sin(angle) * r);
            ctx.lineTo(this.person.x + Math.cos(angle) * (r + 14),
                       this.person.y + Math.sin(angle) * (r + 14));
            ctx.strokeStyle = color;
            ctx.lineWidth   = 2;
            ctx.stroke();
        }
    }

    // ── UI helpers ────────────────────────────────────────────────────────────

    _updatePositionUI() {
        const coordEl = document.getElementById('coordinates');
        if (coordEl) {
            coordEl.textContent =
                `x: ${Math.round(this.person.x)}, y: ${Math.round(this.person.y)}`;
        }

        if (this.locations.length) {
            const nearest = this.locations.reduce((best, loc) => {
                const d = Math.hypot(this.person.x - loc.canvas_x, this.person.y - loc.canvas_y);
                return d < Math.hypot(this.person.x - best.canvas_x, this.person.y - best.canvas_y)
                    ? loc : best;
            });
            const posEl = document.getElementById('current-position');
            if (posEl) posEl.textContent = `Near: ${nearest.name}`;
        }

        const frame = document.getElementById('app-frame');
        if (frame?.contentWindow) {
            frame.contentWindow.postMessage({
                type       : 'position_update',
                x          : Math.round(this.person.x),
                y          : Math.round(this.person.y),
                hasRoute   : this.routePath.length > 0,
                destination: this.routeDestName,
            }, '*');
        }
    }
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    window.simulation = new AirportSimulation();
    console.log('Airport Digital Twin loaded');
});
