/**
 * CubePermutation AI - Frontend Visualizer Engine
 * =================================================
 * Mathematical Permutation Network & 3D Isometric Rubik's Cube Simulator.
 * 
 * Step-by-step logic and group theory permutations are documented with Bangla comments (Banglish).
 */

document.addEventListener('DOMContentLoaded', () => {

    // =========================================================================
    // 1. STATE MANAGEMENT, AUDIO SYNTHESIZER & COLOR PALETTE
    // =========================================================================

    // Web Audio API Audio Synthesizer
    let audioCtx = null;
    function getAudioCtx() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        return audioCtx;
    }

    function playTone(freq, type = 'sine', duration = 0.08, vol = 0.08) {
        try {
            const ctx = getAudioCtx();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = type;
            osc.frequency.setValueAtTime(freq, ctx.currentTime);
            gain.gain.setValueAtTime(vol, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + duration);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + duration);
        } catch (e) {
            // Audio context not allowed until interaction
        }
    }

    function playSolveFanfare() {
        const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
        notes.forEach((freq, idx) => {
            setTimeout(() => playTone(freq, 'triangle', 0.25, 0.12), idx * 90);
        });
    }

    // Rubik's Cube Facelet Standard Colors (Yellow, Green, Orange, Red, White, Blue)
    const COLOR_PALETTE = {
        'U': '#facc15', // Yellow (Up)
        'D': '#f8fafc', // White (Down)
        'F': '#22c55e', // Green (Front)
        'B': '#2563eb', // Blue (Back)
        'L': '#fb923c', // Orange (Left)
        'R': '#ef4444', // Red (Right)
        'W': '#f8fafc',
        'Y': '#facc15',
        'G': '#22c55e',
        'O': '#fb923c'
    };

    // Default Demo Move Sequence (Matches the user's reference screenshot)
    const DEFAULT_SEQUENCE = ["F", "L'", "B'", "R'", "M", "U", "M'", "L'", "U", "E", "B", "M", "U"];

    // App State Variables
    let currentMoves = [...DEFAULT_SEQUENCE];
    let currentStepIndex = currentMoves.length - 1; // Default to step 13/15 or active move
    let isPlaying = false;
    let playInterval = null;
    let animationSpeed = 650; // Milliseconds per move
    let isTwisting = false;

    // Cube Facelet State: 54 facelets (U0-U8, R9-R17, F18-F26, D27-D35, L36-L44, B45-B53)
    let cubeState = Array(54).fill('U');
    
    // Initial Cube State Reset Function
    function initSolvedState() {
        cubeState = [
            ...Array(9).fill('U'), // 0-8: Up (Yellow)
            ...Array(9).fill('R'), // 9-17: Right (Red)
            ...Array(9).fill('F'), // 18-26: Front (Green)
            ...Array(9).fill('D'), // 27-35: Down (White)
            ...Array(9).fill('L'), // 36-44: Left (Orange)
            ...Array(9).fill('B')  // 45-53: Back (Blue)
        ];
    }
    initSolvedState();

    // =========================================================================
    // 2. 3D ISOMETRIC RUBIK'S CUBE SVG RENDERER
    // =========================================================================

    /**
     * Isometric Projection Math Helper:
     * 3D space er (x, y, z) coordinate ke 2D isometric screen coordinate (sx, sy) te convert kore.
     */
    function isoProject(x, y, z) {
        const cos30 = 0.86602540378;
        const sin30 = 0.5;
        const sx = (x - z) * cos30;
        const sy = (x + z) * sin30 - y;
        return { x: sx, y: sy };
    }

    /**
     * Isometric SVG polygon point string bananor function
     */
    function createPolygonPoints(p1, p2, p3, p4) {
        return `${p1.x},${p1.y} ${p2.x},${p2.y} ${p3.x},${p3.y} ${p4.x},${p4.y}`;
    }

    /**
     * 3D Isometric Cube render function:
     * Screen e Top (U), Front (F), ebong Right (R) faces 3D isometric angle e draw kore.
     * Active move e layer twist animation provide kore.
     */
    function renderIsometricCube(twistAngle = 0) {
        const svg = document.getElementById('isometric-cube-svg');
        if (!svg) return;
        svg.innerHTML = '';

        const s = 34; // Facelet cell size
        const gap = 2.5; // Gap between facelets
        const offset = 1.5 * s;

        // Group element for dynamic layer twist animation
        const gMain = document.createElementNS("http://www.w3.org/2000/svg", "g");

        // -------------------------------------------------------------
        // TOP FACE (U: Yellow) - With potential rotation angle
        // -------------------------------------------------------------
        const gTopLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
        if (twistAngle !== 0) {
            gTopLayer.setAttribute("transform", `rotate(${twistAngle}, 0, -55)`);
        }

        for (let row = 0; row < 3; row++) {
            for (let col = 0; col < 3; col++) {
                const idx = row * 3 + col; // 0 to 8
                const colorKey = cubeState[idx] || 'U';
                const fillColor = COLOR_PALETTE[colorKey] || COLOR_PALETTE['U'];

                const x0 = (col - 1.5) * (s + gap);
                const z0 = (row - 1.5) * (s + gap);
                const y0 = 1.5 * s; // Top plane height

                const p1 = isoProject(x0, y0, z0);
                const p2 = isoProject(x0 + s, y0, z0);
                const p3 = isoProject(x0 + s, y0, z0 + s);
                const p4 = isoProject(x0, y0, z0 + s);

                const poly = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
                poly.setAttribute("points", createPolygonPoints(p1, p2, p3, p4));
                poly.setAttribute("fill", fillColor);
                poly.setAttribute("class", "cube-facelet");
                poly.setAttribute("data-facelet", `U${idx}`);
                poly.setAttribute("stroke", "#111827");
                poly.setAttribute("stroke-width", "2");

                gTopLayer.appendChild(poly);
            }
        }
        gMain.appendChild(gTopLayer);

        // -------------------------------------------------------------
        // FRONT FACE (F: Green / Red / etc.)
        // -------------------------------------------------------------
        for (let row = 0; row < 3; row++) {
            for (let col = 0; col < 3; col++) {
                const idx = 18 + (row * 3 + col); // 18 to 26
                const colorKey = cubeState[idx] || 'F';
                const fillColor = COLOR_PALETTE[colorKey] || COLOR_PALETTE['F'];

                const x0 = (col - 1.5) * (s + gap);
                const y0 = (1.5 - row) * (s + gap) - s;
                const z0 = 1.5 * (s + gap); // Front face z position

                const p1 = isoProject(x0, y0 + s, z0);
                const p2 = isoProject(x0 + s, y0 + s, z0);
                const p3 = isoProject(x0 + s, y0, z0);
                const p4 = isoProject(x0, y0, z0);

                const poly = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
                poly.setAttribute("points", createPolygonPoints(p1, p2, p3, p4));
                poly.setAttribute("fill", fillColor);
                poly.setAttribute("class", "cube-facelet");
                poly.setAttribute("data-facelet", `F${row * 3 + col}`);
                poly.setAttribute("stroke", "#111827");
                poly.setAttribute("stroke-width", "2");

                gMain.appendChild(poly);
            }
        }

        // -------------------------------------------------------------
        // RIGHT FACE (R: Orange / Red)
        // -------------------------------------------------------------
        for (let row = 0; row < 3; row++) {
            for (let col = 0; col < 3; col++) {
                const idx = 9 + (row * 3 + col); // 9 to 17
                const colorKey = cubeState[idx] || 'R';
                const fillColor = COLOR_PALETTE[colorKey] || COLOR_PALETTE['R'];

                const z0 = (1.5 - col) * (s + gap) - s;
                const y0 = (1.5 - row) * (s + gap) - s;
                const x0 = 1.5 * (s + gap); // Right face x position

                const p1 = isoProject(x0, y0 + s, z0);
                const p2 = isoProject(x0, y0 + s, z0 + s);
                const p3 = isoProject(x0, y0, z0 + s);
                const p4 = isoProject(x0, y0, z0);

                const poly = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
                poly.setAttribute("points", createPolygonPoints(p1, p2, p3, p4));
                poly.setAttribute("fill", fillColor);
                poly.setAttribute("class", "cube-facelet");
                poly.setAttribute("data-facelet", `R${row * 3 + col}`);
                poly.setAttribute("stroke", "#111827");
                poly.setAttribute("stroke-width", "2");

                gMain.appendChild(poly);
            }
        }

        svg.appendChild(gMain);
    }

    // =========================================================================
    // 3. MATHEMATICAL PERMUTATION ORBIT NETWORK (GROUP THEORY GRAPH)
    // =========================================================================

    /**
     * Circular Permutation Orbit SVG Renderer:
     * Mathematical Group Theory visualizer matching the exact reference diagram:
     * - Overlapping symmetric orbit rings (subgroup generators).
     * - Node vertex clusters organized in geometric orbits for 6 colors (Yellow, Blue, Orange, White, Green, Red).
     * - Glowing animated highlight arcs indicating current active permutation cycle ($g \in G$).
     */
    function renderPermutationOrbit(activeMove = 'U', progress = 0) {
        const svg = document.getElementById('permutation-orbit-svg');
        if (!svg) return;
        svg.innerHTML = '';

        const ns = "http://www.w3.org/2000/svg";
        const baseFace = activeMove ? activeMove[0] : 'U';
        const isCounter = activeMove && activeMove.includes("'");
        const isDouble = activeMove && activeMove.includes("2");

        // Defs for glowing gradients, filters, and markers
        const defs = document.createElementNS(ns, "defs");
        defs.innerHTML = `
            <filter id="glow-cyan" x="-40%" y="-40%" width="180%" height="180%">
                <feGaussianBlur stdDeviation="6" result="blur" />
                <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                </feMerge>
            </filter>
            <filter id="glow-gold" x="-40%" y="-40%" width="180%" height="180%">
                <feGaussianBlur stdDeviation="6" result="blur" />
                <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                </feMerge>
            </filter>
            <filter id="glow-emerald" x="-40%" y="-40%" width="180%" height="180%">
                <feGaussianBlur stdDeviation="6" result="blur" />
                <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                </feMerge>
            </filter>
            <filter id="glow-crimson" x="-40%" y="-40%" width="180%" height="180%">
                <feGaussianBlur stdDeviation="6" result="blur" />
                <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                </feMerge>
            </filter>
            <marker id="arrow-cyan" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#38bdf8" />
            </marker>
        `;
        svg.appendChild(defs);

        // 1. Defined Group Orbit Rings with Wide, Clearly Visible Strokes
        const orbitRings = [
            { id: 'U', cx: 0, cy: -30, r: 80, color: '#facc15', name: 'U-Orbit' },
            { id: 'D', cx: 0, cy: 50, r: 80, color: '#f8fafc', name: 'D-Orbit' },
            { id: 'F', cx: 0, cy: 10, r: 90, color: '#22c55e', name: 'F-Orbit' },
            { id: 'B', cx: 0, cy: -10, r: 145, color: '#3b82f6', name: 'B-Orbit' },
            { id: 'L', cx: -60, cy: 10, r: 85, color: '#fb923c', name: 'L-Orbit' },
            { id: 'R', cx: 60, cy: 10, r: 85, color: '#ef4444', name: 'R-Orbit' },
            { id: 'HORIZON', cx: 0, cy: 0, r: 185, color: '#6366f1', name: 'S54 Horizon' }
        ];

        orbitRings.forEach(r => {
            const isActive = (r.id === baseFace);
            const circle = document.createElementNS(ns, "circle");
            circle.setAttribute("cx", r.cx);
            circle.setAttribute("cy", r.cy);
            circle.setAttribute("r", r.r);
            circle.setAttribute("fill", "none");
            
            if (isActive) {
                circle.setAttribute("stroke", r.color);
                circle.setAttribute("stroke-width", "4.5");
                circle.setAttribute("class", "orbit-track active-orbit animate-pulse-glow");
                circle.setAttribute("filter", "url(#glow-cyan)");
            } else {
                circle.setAttribute("stroke", r.color);
                circle.setAttribute("stroke-width", "2.2");
                circle.setAttribute("stroke-opacity", r.id === 'HORIZON' ? "0.3" : "0.55");
                circle.setAttribute("class", "orbit-track");
                if (r.id === 'HORIZON') circle.setAttribute("stroke-dasharray", "6, 6");
            }
            svg.appendChild(circle);

            // Orbit Label
            if (r.id !== 'HORIZON') {
                const lbl = document.createElementNS(ns, "text");
                lbl.setAttribute("x", r.cx - 5);
                lbl.setAttribute("y", r.cy - r.r + 14);
                lbl.setAttribute("fill", isActive ? r.color : "rgba(255,255,255,0.45)");
                lbl.setAttribute("font-size", isActive ? "12" : "10");
                lbl.setAttribute("font-weight", "bold");
                lbl.setAttribute("font-family", "monospace");
                lbl.textContent = r.id;
                svg.appendChild(lbl);
            }
        });

        // 2. Active Dynamic Permutation Flow Arc with Flowing Dash Particles
        const activeRing = orbitRings.find(r => r.id === baseFace) || orbitRings[0];
        const gActiveFlow = document.createElementNS(ns, "g");
        
        // Dynamic Glowing Arc Overlay on Active Orbit
        const flowArc = document.createElementNS(ns, "path");
        const arcRadius = activeRing.r;
        
        function polarToCartesian(cx, cy, radius, angleInDegrees) {
            const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0;
            return {
                x: cx + (radius * Math.cos(angleInRadians)),
                y: cy + (radius * Math.sin(angleInRadians))
            };
        }

        function describeArc(x, y, radius, startAngle, endAngle) {
            const start = polarToCartesian(x, y, radius, endAngle);
            const end = polarToCartesian(x, y, radius, startAngle);
            const largeArcFlag = Math.abs(endAngle - startAngle) <= 180 ? "0" : "1";
            return [
                "M", start.x, start.y, 
                "A", radius, radius, 0, largeArcFlag, isCounter ? 1 : 0, end.x, end.y
            ].join(" ");
        }

        // Primary Glowing Arc
        flowArc.setAttribute("d", describeArc(activeRing.cx, activeRing.cy, arcRadius, 0, isDouble ? 359 : 270));
        flowArc.setAttribute("fill", "none");
        flowArc.setAttribute("stroke", activeRing.color || "#38bdf8");
        flowArc.setAttribute("stroke-width", "5.5");
        flowArc.setAttribute("stroke-linecap", "round");
        flowArc.setAttribute("class", "orbit-flow-line");
        flowArc.setAttribute("filter", "url(#glow-cyan)");
        gActiveFlow.appendChild(flowArc);

        // Direction Arrow Marker on Active Orbit
        const arrowMarker = document.createElementNS(ns, "path");
        arrowMarker.setAttribute("d", describeArc(activeRing.cx, activeRing.cy, arcRadius, 260, 275));
        arrowMarker.setAttribute("fill", "none");
        arrowMarker.setAttribute("stroke", "#ffffff");
        arrowMarker.setAttribute("stroke-width", "4");
        arrowMarker.setAttribute("marker-end", "url(#arrow-cyan)");
        gActiveFlow.appendChild(arrowMarker);

        svg.appendChild(gActiveFlow);

        // 3. Move Generator HUD Badge in Center
        const badgeG = document.createElementNS(ns, "g");
        const badgeBg = document.createElementNS(ns, "rect");
        badgeBg.setAttribute("x", "-40");
        badgeBg.setAttribute("y", "-100");
        badgeBg.setAttribute("width", "80");
        badgeBg.setAttribute("height", "26");
        badgeBg.setAttribute("rx", "13");
        badgeBg.setAttribute("fill", "rgba(15, 23, 42, 0.9)");
        badgeBg.setAttribute("stroke", activeRing.color || "#818cf8");
        badgeBg.setAttribute("stroke-width", "2");
        badgeG.appendChild(badgeBg);

        const moveText = document.createElementNS(ns, "text");
        moveText.setAttribute("x", "0");
        moveText.setAttribute("y", "-83");
        moveText.setAttribute("text-anchor", "middle");
        moveText.setAttribute("fill", activeRing.color || "#ffffff");
        moveText.setAttribute("font-family", "monospace");
        moveText.setAttribute("font-size", "13");
        moveText.setAttribute("font-weight", "bold");
        moveText.textContent = `⟨${activeMove}⟩ ${isCounter ? '↺ -90°' : isDouble ? '↻ 180°' : '↻ +90°'}`;
        badgeG.appendChild(moveText);
        svg.appendChild(badgeG);

        // 4. Enhanced High-Visibility Orbit Node Vertices with Connections
        const nodeClusters = [
            // Top Center Cluster (Yellow Nodes - U Face)
            { x: -22, y: -50, color: '#facc15', id: 'U1' },
            { x: 0, y: -50, color: '#facc15', id: 'U2' },
            { x: 22, y: -50, color: '#facc15', id: 'U3' },
            { x: -12, y: -32, color: '#facc15', id: 'U4' },
            { x: 12, y: -32, color: '#facc15', id: 'U6' },

            // Upper Arc Outer Nodes (Cyan / Blue boundary)
            { x: 28, y: -105, color: '#38bdf8', id: 'B1' },
            { x: 48, y: -95, color: '#38bdf8', id: 'B2' },
            { x: 62, y: -78, color: '#facc15', id: 'U9' },

            // Right Upper Cluster (Blue Nodes - B Face)
            { x: 88, y: -55, color: '#3b82f6', id: 'B3' },
            { x: 105, y: -38, color: '#3b82f6', id: 'B4' },
            { x: 118, y: -20, color: '#3b82f6', id: 'B6' },
            { x: 132, y: -2, color: '#3b82f6', id: 'B7' },
            { x: 115, y: 18, color: '#facc15', id: 'U8' },

            // Right Middle Arc (Orange/Red Nodes - R Face)
            { x: 68, y: -18, color: '#ef4444', id: 'R1' },
            { x: 72, y: 2, color: '#ef4444', id: 'R2' },
            { x: 74, y: 22, color: '#ef4444', id: 'R3' },
            { x: 70, y: 42, color: '#ef4444', id: 'R6' },
            { x: 64, y: 60, color: '#fb923c', id: 'L3' },
            { x: 54, y: 78, color: '#fb923c', id: 'L6' },

            // Center Ring Inner Nodes (Green/Yellow/Red Center)
            { x: -10, y: -16, color: '#facc15', id: 'U5' },
            { x: 10, y: -16, color: '#22c55e', id: 'F2' },
            { x: 0, y: 4, color: '#22c55e', id: 'F5' },

            // Left Middle Arc (Green & Red Nodes - F/L Face)
            { x: -62, y: 72, color: '#22c55e', id: 'F7' },
            { x: -44, y: 86, color: '#22c55e', id: 'F8' },
            { x: -24, y: 92, color: '#22c55e', id: 'F9' },
            { x: -68, y: 50, color: '#fb923c', id: 'L1' },
            { x: -74, y: 30, color: '#fb923c', id: 'L2' },
            { x: -74, y: 10, color: '#fb923c', id: 'L4' },
            { x: -68, y: -10, color: '#fb923c', id: 'L7' },
            { x: -60, y: -28, color: '#ef4444', id: 'R7' },

            // Left Outer Boundary Nodes (Red/Blue)
            { x: -88, y: -50, color: '#ef4444', id: 'R4' },
            { x: -105, y: -32, color: '#ef4444', id: 'R8' },
            { x: -118, y: -14, color: '#3b82f6', id: 'B8' },
            { x: -132, y: 5, color: '#3b82f6', id: 'B9' },

            // Bottom Diamond / Cluster (White & Blue Nodes - D Face)
            { x: 0, y: 118, color: '#ffffff', id: 'D1' },
            { x: -18, y: 134, color: '#ffffff', id: 'D2' },
            { x: 0, y: 134, color: '#ffffff', id: 'D5' },
            { x: 18, y: 134, color: '#ffffff', id: 'D3' },
            { x: -35, y: 150, color: '#3b82f6', id: 'D4' },
            { x: -18, y: 150, color: '#ffffff', id: 'D7' },
            { x: 0, y: 150, color: '#ffffff', id: 'D8' },
            { x: 18, y: 150, color: '#ffffff', id: 'D9' },
            { x: 35, y: 150, color: '#3b82f6', id: 'D6' }
        ];

        // Draw connecting permutation flow lines between adjacent nodes in active cluster
        const gNodeLinks = document.createElementNS(ns, "g");
        for (let i = 0; i < nodeClusters.length - 1; i += 2) {
            const p1 = nodeClusters[i];
            const p2 = nodeClusters[i + 1];
            const line = document.createElementNS(ns, "line");
            line.setAttribute("x1", p1.x);
            line.setAttribute("y1", p1.y);
            line.setAttribute("x2", p2.x);
            line.setAttribute("y2", p2.y);
            line.setAttribute("stroke", "rgba(148, 163, 184, 0.25)");
            line.setAttribute("stroke-width", "1.5");
            line.setAttribute("stroke-dasharray", "3, 3");
            gNodeLinks.appendChild(line);
        }
        svg.appendChild(gNodeLinks);

        // Draw High-Visibility Nodes with Glowing Outlines
        nodeClusters.forEach((node) => {
            const circle = document.createElementNS(ns, "circle");
            circle.setAttribute("cx", node.x);
            circle.setAttribute("cy", node.y);
            circle.setAttribute("r", "5.5");
            circle.setAttribute("fill", node.color);
            circle.setAttribute("class", "orbit-node");
            circle.setAttribute("stroke", "#020617");
            circle.setAttribute("stroke-width", "1.8");

            // Tooltip title
            const title = document.createElementNS(ns, "title");
            title.textContent = `Permutation Vertex ${node.id} (${node.color})`;
            circle.appendChild(title);

            svg.appendChild(circle);
        });
    }

    // =========================================================================
    // 4. GROUP THEORY PERMUTATION SIMULATOR
    // =========================================================================

    /**
     * Rubik's Cube Face Turn Permutation Application:
     * Applies Singmaster notation move to the 54-facelet array.
     */
    function applyFaceTurn(move) {
        const s = [...cubeState];
        const base = move[0];
        const isPrime = move.includes("'");
        const isDouble = move.includes("2");
        const count = isDouble ? 2 : (isPrime ? 3 : 1);

        function rotFace(idx) {
            const t0 = s[idx+0], t1 = s[idx+1];
            s[idx+0] = s[idx+6]; s[idx+1] = s[idx+3]; s[idx+6] = s[idx+8]; s[idx+3] = s[idx+7];
            s[idx+8] = s[idx+2]; s[idx+7] = s[idx+5]; s[idx+2] = t0; s[idx+5] = t1;
        }

        for (let t = 0; t < count; t++) {
            if (base === 'U') {
                rotFace(0);
                const [f0,f1,f2] = [s[18], s[19], s[20]];
                const [r0,r1,r2] = [s[9], s[10], s[11]];
                const [b0,b1,b2] = [s[45], s[46], s[47]];
                const [l0,l1,l2] = [s[36], s[37], s[38]];
                s[18]=r0; s[19]=r1; s[20]=r2;
                s[9]=b0;  s[10]=b1; s[11]=b2;
                s[45]=l0; s[46]=l1; s[47]=l2;
                s[36]=f0; s[37]=f1; s[38]=f2;
            } else if (base === 'D') {
                rotFace(27);
                const [f6,f7,f8] = [s[24], s[25], s[26]];
                const [r6,r7,r8] = [s[15], s[16], s[17]];
                const [b6,b7,b8] = [s[51], s[52], s[53]];
                const [l6,l7,l8] = [s[42], s[43], s[44]];
                s[24]=l6; s[25]=l7; s[26]=l8;
                s[42]=b6; s[43]=b7; s[44]=b8;
                s[51]=r6; s[52]=r7; s[53]=r8;
                s[15]=f6; s[16]=f7; s[17]=f8;
            } else if (base === 'F') {
                rotFace(18);
                const [u6,u7,u8] = [s[6], s[7], s[8]];
                const [r0,r3,r6] = [s[9], s[12], s[15]];
                const [d0,d1,d2] = [s[27], s[28], s[29]];
                const [l2,l5,l8] = [s[38], s[41], s[44]];
                s[9]=u6; s[12]=u7; s[15]=u8;
                s[27]=r6; s[28]=r3; s[29]=r0;
                s[38]=d2; s[41]=d1; s[44]=d0;
                s[6]=l2; s[7]=l5; s[8]=l8;
            } else if (base === 'B') {
                rotFace(45);
                const [u0,u1,u2] = [s[0], s[1], s[2]];
                const [l0,l3,l6] = [s[36], s[39], s[42]];
                const [d6,d7,d8] = [s[33], s[34], s[35]];
                const [r2,r5,r8] = [s[11], s[14], s[17]];
                s[36]=u2; s[39]=u1; s[42]=u0;
                s[33]=l0; s[34]=l3; s[35]=l6;
                s[11]=d8; s[14]=d7; s[17]=d6;
                s[0]=r2; s[1]=r5; s[2]=r8;
            } else if (base === 'L') {
                rotFace(36);
                const [u0,u3,u6] = [s[0], s[3], s[6]];
                const [f0,f3,f6] = [s[18], s[21], s[24]];
                const [d0,d3,d6] = [s[27], s[30], s[33]];
                const [b2,b5,b8] = [s[47], s[50], s[53]];
                s[18]=u0; s[21]=u3; s[24]=u6;
                s[27]=f0; s[30]=f3; s[33]=f6;
                s[47]=d6; s[50]=d3; s[53]=d0;
                s[0]=b8; s[3]=b5; s[6]=b2;
            } else if (base === 'R') {
                rotFace(9);
                const [u2,u5,u8] = [s[2], s[5], s[8]];
                const [b0,b3,b6] = [s[45], s[48], s[51]];
                const [d2,d5,d8] = [s[29], s[32], s[35]];
                const [f2,f5,f8] = [s[20], s[23], s[26]];
                s[45]=u8; s[48]=u5; s[51]=u2;
                s[29]=b6; s[32]=b3; s[35]=b0;
                s[20]=d2; s[23]=d5; s[26]=d8;
                s[2]=f2; s[5]=f5; s[8]=f8;
            } else if (base === 'M') {
                const [u1,u4,u7] = [s[1], s[4], s[7]];
                const [f1,f4,f7] = [s[19], s[22], s[25]];
                const [d1,d4,d7] = [s[28], s[31], s[34]];
                const [b1,b4,b7] = [s[46], s[49], s[52]];
                s[19]=u1; s[22]=u4; s[25]=u7;
                s[28]=f1; s[31]=f4; s[34]=f7;
                s[46]=d7; s[49]=d4; s[52]=d1;
                s[1]=b7; s[4]=b4; s[7]=b1;
            } else if (base === 'E') {
                const [f3,f4,f5] = [s[21], s[22], s[23]];
                const [r3,r4,r5] = [s[12], s[13], s[14]];
                const [b3,b4,b5] = [s[48], s[49], s[50]];
                const [l3,l4,l5] = [s[39], s[40], s[41]];
                s[21]=l3; s[22]=l4; s[23]=l5;
                s[39]=b3; s[40]=b4; s[41]=b5;
                s[48]=r3; s[49]=r4; s[50]=r5;
                s[12]=f3; s[13]=f4; s[14]=f5;
            } else if (base === 'S') {
                const [u3,u4,u5] = [s[3], s[4], s[5]];
                const [r1,r4,r7] = [s[10], s[13], s[16]];
                const [d3,d4,d5] = [s[30], s[31], s[32]];
                const [l1,l4,l7] = [s[37], s[40], s[43]];
                s[10]=u3; s[13]=u4; s[16]=u5;
                s[30]=r7; s[31]=r4; s[32]=r1;
                s[37]=d5; s[40]=d4; s[43]=d3;
                s[3]=l1; s[4]=l4; s[5]=l7;
            }
        }
        cubeState = s;
    }

    /**
     * Full sequence reconstruct kore specified step index porjonto cube state rebuild kore
     */
    function reconstructCubeStateUpToStep(stepIdx) {
        initSolvedState();
        for (let i = 0; i <= stepIdx; i++) {
            if (currentMoves[i]) {
                applyFaceTurn(currentMoves[i]);
            }
        }
    }

    // =========================================================================
    // 5. UI UPDATE & RIBBON SYNCHRONIZATION
    // =========================================================================

    /**
     * Move Ribbon, Step Indicators, ebong Visualizer graphics update kore
     */
    function updateVisualizerUI() {
        const activeMove = currentMoves[currentStepIndex] || 'U';
        const totalSteps = currentMoves.length;

        // 1. Update Move Letter & Step Counter
        const moveLetterEl = document.getElementById('active-move-letter');
        const stepCounterEl = document.getElementById('active-step-counter');
        if (moveLetterEl) moveLetterEl.textContent = activeMove;
        if (stepCounterEl) stepCounterEl.textContent = `${currentStepIndex + 1} / ${Math.max(totalSteps, 1)}`;

        // 2. Update Move Ribbon
        const ribbonEl = document.getElementById('move-ribbon');
        if (ribbonEl) {
            ribbonEl.innerHTML = '';
            currentMoves.forEach((m, idx) => {
                const item = document.createElement('span');
                item.className = `ribbon-item ${idx === currentStepIndex ? 'active text-indigo-400 font-bold' : ''}`;
                item.textContent = m;
                item.addEventListener('click', () => {
                    goToStep(idx);
                });
                ribbonEl.appendChild(item);
            });
        }

        // 3. Update Group Theory Math Inspector Info
        updateMathInspector(activeMove);

        // 4. Update Live Step Walkthrough "Why & How" Inspector
        updateWalkthroughCard(activeMove, currentStepIndex, totalSteps);

        // 5. Render Isometric Cube & Permutation Orbit Network
        const twistAngle = (activeMove === 'U' || activeMove === "U'" || activeMove === 'U2') ? 22 : 0;
        renderIsometricCube(twistAngle);
        renderPermutationOrbit(activeMove);
    }

    /**
     * Live Move Explanation Card Updater
     */
    function updateWalkthroughCard(move, stepIdx, totalSteps) {
        const letterEl = document.getElementById('vis-active-move-letter');
        const arrowEl = document.getElementById('vis-active-arrow');
        const phaseEl = document.getElementById('vis-active-phase');
        const whyEl = document.getElementById('vis-active-why');
        const howEl = document.getElementById('vis-active-how');
        const badgeEl = document.getElementById('vis-active-step-badge');

        if (letterEl) {
            letterEl.textContent = move;
            const f = move[0] || 'U';
            const faceColors = {
                'U': 'bg-amber-500 text-black border-amber-300',
                'D': 'bg-slate-200 text-black border-white',
                'F': 'bg-emerald-600 text-white border-emerald-400',
                'B': 'bg-blue-600 text-white border-blue-400',
                'L': 'bg-orange-500 text-white border-orange-300',
                'R': 'bg-rose-600 text-white border-rose-400'
            };
            letterEl.className = `w-12 h-12 rounded-2xl font-black text-xl flex items-center justify-center shadow-lg border ${faceColors[f] || 'bg-indigo-600 text-white border-indigo-400'}`;
        }

        if (arrowEl) {
            arrowEl.textContent = move.includes("'") ? "↺ 90° Counter-Clockwise" : move.includes("2") ? "↻ 180° Half Turn" : "↻ 90° Clockwise";
        }

        const pct = (stepIdx + 1) / Math.max(totalSteps, 1);
        let phaseName = "Phase 1: Foundation Cross & Subgroup Orientation";
        if (pct > 0.3 && pct <= 0.65) phaseName = "Phase 2: First Two Layers (F2L) Slotting & Commutators";
        else if (pct > 0.65 && pct <= 0.85) phaseName = "Phase 3: Last Layer Orientation (OLL Invariant Balance)";
        else if (pct > 0.85) phaseName = "Phase 4: Final Permutation (PLL Orbit Cycle Reduction)";

        if (phaseEl) phaseEl.textContent = phaseName;
        if (badgeEl) badgeEl.textContent = `Move ${stepIdx + 1} / ${Math.max(totalSteps, 1)}`;

        const whyDescriptions = {
            'R': "Rotates Right face 90° clockwise. Lifts front-right cubies into the top working buffer while keeping the Left & Down face stabilizers intact.",
            "R'": "Rotates Right face 90° counter-clockwise. Pulls the top working pair directly down into its middle belt slot.",
            'R2': "Double turns Right face 180°. Reverses Right column vertically to swap top and bottom slots in minimal steps.",
            'U': "Rotates Up face 90° clockwise. Cycles top-layer corners and edges into position for commutator pairing.",
            "U'": "Rotates Up face 90° counter-clockwise. Aligns target facelets over their respective home columns before elevator slotting.",
            'U2': "Double turns Up face 180°. Rapidly shifts target pieces to the opposite side of the cube.",
            'F': "Rotates Front face 90° clockwise. Opens front gate to alter edge orientation vectors or prepare Fur-Urf triggers.",
            "F'": "Rotates Front face 90° counter-clockwise. Closes front gate to restore white cross stabilizer.",
            'F2': "Double turns Front face 180°. Transfers top Daisy petal directly down to the white foundation cross.",
            'L': "Rotates Left face 90° clockwise. Lowers Left-Front edge into bottom layer for symmetrical slotting.",
            "L'": "Rotates Left face 90° counter-clockwise. Lifts Left-Front corner into upper active workspace.",
            'L2': "Double turns Left face 180°. Inverts Left column between upper and lower orbits in minimal moves.",
            'D': "Rotates Down foundation 90° clockwise. Positions a vacant bottom slot directly under an incoming piece.",
            "D'": "Rotates Down foundation 90° counter-clockwise. Restores bottom white cross alignment.",
            'D2': "Double turns Down layer 180°. Inverts foundation slots for optimal parity alignment.",
            'B': "Rotates Back face 90° clockwise. Adjusts rear-layer edge orbits without disturbing the front 2 layers.",
            "B'": "Rotates Back face 90° counter-clockwise. Lifts rear cubies into the top buffer.",
            'B2': "Double turns Back face 180°. Cycles rear-layer pieces directly between top and bottom planes."
        };

        const howDescriptions = {
            'R': "Hold cube firmly with Left hand. Push Right face clockwise away from you using right thumb and index finger.",
            "R'": "Hold cube firmly with Left hand. Pull Right face counter-clockwise toward you using right index/middle fingers.",
            'R2': "Execute a smooth double wrist-flick on the Right layer (180°).",
            'U': "Flick top layer from right to left using right index finger (clockwise).",
            "U'": "Flick top layer from left to right using left index finger (counter-clockwise).",
            'U2': "Double flick top layer using right index then right middle finger in rapid succession.",
            'F': "Turn front face clockwise 90° using right index finger pushing downward.",
            "F'": "Turn front face counter-clockwise 90° using right thumb pushing upward.",
            'F2': "Double turn front face 180° with two consecutive finger pushes.",
            'L': "Hold cube with Right hand. Pull Left face toward you with left index finger.",
            "L'": "Hold cube with Right hand. Push Left face away from you with left thumb.",
            'L2': "Execute a smooth double wrist-flick on the Left layer (180°)."
        };

        if (whyEl) whyEl.textContent = whyDescriptions[move] || `Executes ${move} to orient facelets into solved orbits with minimum entropy.`;
        if (howEl) howEl.textContent = howDescriptions[move] || `Rotate the ${move[0]} layer smoothly.`;
    }

    /**
     * Group Theory Disjoint Cycle Notation & Parity updates
     */
    function updateMathInspector(move) {
        const cycleMap = {
            'U': '(U₁ U₃ U₉ U₇)(U₂ U₆ U₈ U₄)(F₁ R₁ B₁ L₁)',
            "U'": '(U₇ U₉ U₃ U₁)(U₄ U₈ U₆ U₂)(L₁ B₁ R₁ F₁)',
            'U2': '(U₁ U₉)(U₃ U₇)(U₂ U₈)(U₄ U₆)(F₁ B₁)(R₁ L₁)',
            'R': '(R₁ R₃ R₉ R₇)(R₂ R₆ R₈ R₄)(U₃ B₇ D₃ F₃)',
            "R'": '(R₇ R₉ R₃ R₁)(R₄ R₈ R₆ R₂)(F₃ D₃ B₇ U₃)',
            'F': '(F₁ F₃ F₉ F₇)(F₂ F₆ F₈ F₄)(U₇ R₁ D₁ L₉)',
            'M': '(U₂ F₂ D₂ B₈)(U₅ F₅ D₅ B₅)(U₈ F₈ D₈ B₂)',
            'E': '(F₄ R₄ B₄ L₄)(F₅ R₅ B₅ L₅)(F₆ R₆ B₆ L₆)',
            'S': '(U₄ R₂ D₆ L₈)(U₅ R₅ D₅ L₅)(U₆ R₈ D₄ L₂)'
        };

        const cycleEl = document.getElementById('math-cycle-notation');
        const orbitInfoEl = document.getElementById('math-orbit-info');
        
        if (cycleEl) {
            cycleEl.textContent = cycleMap[move] || `(${move}₁ ${move}₃ ${move}₉ ${move}₇)(${move}₂ ${move}₆ ${move}₈ ${move}₄)`;
        }
        if (orbitInfoEl) {
            const order = move.includes('2') ? 2 : 4;
            orbitInfoEl.textContent = `Orbit Order: ${order} • Transposition Count: 8 • Generator: ⟨${move[0]}⟩`;
        }
    }

    // =========================================================================
    // 6. PLAYBACK CONTROLLERS (STEP, PLAY, PAUSE, SPEED)
    // =========================================================================

    function nextStep() {
        if (currentStepIndex < currentMoves.length - 1) {
            currentStepIndex++;
            reconstructCubeStateUpToStep(currentStepIndex);
            updateVisualizerUI();
            playTone(520, 'sine', 0.05);
            if (visualizer3DCube && currentMoves[currentStepIndex]) {
                visualizer3DCube.animateLayerTurn(currentMoves[currentStepIndex]);
            }
        } else if (isPlaying) {
            pausePlayback();
            playSolveFanfare();
        }
    }

    function prevStep() {
        if (currentStepIndex > 0) {
            currentStepIndex--;
            reconstructCubeStateUpToStep(currentStepIndex);
            updateVisualizerUI();
            playTone(440, 'sine', 0.05);
        }
    }

    function goToStep(idx) {
        if (idx >= 0 && idx < currentMoves.length) {
            currentStepIndex = idx;
            reconstructCubeStateUpToStep(currentStepIndex);
            updateVisualizerUI();
            playTone(560, 'sine', 0.05);
            if (visualizer3DCube && currentMoves[currentStepIndex]) {
                visualizer3DCube.animateLayerTurn(currentMoves[currentStepIndex]);
            }
        }
    }

    function togglePlay() {
        if (isPlaying) {
            pausePlayback();
        } else {
            startPlayback();
        }
    }

    function startPlayback() {
        if (currentStepIndex >= currentMoves.length - 1) {
            currentStepIndex = -1; // Loop back to beginning
        }
        isPlaying = true;
        playTone(600, 'triangle', 0.08);
        const playIcon = document.getElementById('play-icon');
        if (playIcon) {
            playIcon.classList.remove('fa-play');
            playIcon.classList.add('fa-pause');
        }
        playInterval = setInterval(nextStep, animationSpeed);
    }

    function pausePlayback() {
        isPlaying = false;
        if (playInterval) clearInterval(playInterval);
        const playIcon = document.getElementById('play-icon');
        if (playIcon) {
            playIcon.classList.remove('fa-pause');
            playIcon.classList.add('fa-play');
        }
    }

    // Button event listeners
    document.getElementById('ctrl-play')?.addEventListener('click', togglePlay);
    document.getElementById('ctrl-next')?.addEventListener('click', () => { pausePlayback(); nextStep(); });
    document.getElementById('ctrl-prev')?.addEventListener('click', () => { pausePlayback(); prevStep(); });
    document.getElementById('ctrl-first')?.addEventListener('click', () => { pausePlayback(); goToStep(0); });
    document.getElementById('ctrl-last')?.addEventListener('click', () => { pausePlayback(); goToStep(currentMoves.length - 1); });
    document.getElementById('ctrl-reset')?.addEventListener('click', () => {
        pausePlayback();
        playTone(350, 'sawtooth', 0.1);
        initSolvedState();
        currentStepIndex = 0;
        updateVisualizerUI();
    });

    // Speed Controls
    document.querySelectorAll('.speed-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            playTone(700, 'sine', 0.04);
            document.querySelectorAll('.speed-btn').forEach(b => {
                b.classList.remove('active', 'bg-indigo-600', 'text-white', 'font-bold');
                b.classList.add('text-slate-400');
            });
            e.target.classList.add('active', 'bg-indigo-600', 'text-white', 'font-bold');
            e.target.classList.remove('text-slate-400');
            animationSpeed = parseInt(e.target.dataset.speed) || 650;
            if (isPlaying) {
                clearInterval(playInterval);
                playInterval = setInterval(nextStep, animationSpeed);
            }
        });
    });

    // Single Face Move Execution Buttons
    document.querySelectorAll('.face-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            pausePlayback();
            const move = btn.dataset.move;
            playTone(480, 'sine', 0.05);
            applyFaceTurn(move);
            currentMoves.push(move);
            currentStepIndex = currentMoves.length - 1;
            updateVisualizerUI();
            if (visualizer3DCube) {
                visualizer3DCube.animateLayerTurn(move);
            }
        });
    });

    // Custom Permutation Sequence Loader
    document.getElementById('btn-apply-custom')?.addEventListener('click', () => {
        const input = document.getElementById('custom-sequence-input');
        if (!input || !input.value.trim()) return;
        pausePlayback();
        playTone(600, 'triangle', 0.08);
        const moves = input.value.trim().split(/\s+/);
        currentMoves = moves;
        currentStepIndex = 0;
        reconstructCubeStateUpToStep(0);
        updateVisualizerUI();
    });

    // =========================================================================
    // 7. REST API INTEGRATION (SCRAMBLE & KOCIEMBA SOLVER)
    // =========================================================================

    // Scramble Generator API
    document.getElementById('btn-scramble')?.addEventListener('click', async () => {
        pausePlayback();
        playTone(320, 'sine', 0.12);
        const btn = document.getElementById('btn-scramble');
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Scrambling...`;
        
        try {
            const res = await fetch('/api/scramble');
            const data = await res.json();
            if (data.scramble) {
                const scrambleMoves = data.scramble.split(' ');
                currentMoves = scrambleMoves;
                currentStepIndex = currentMoves.length - 1;
                reconstructCubeStateUpToStep(currentStepIndex);
                updateVisualizerUI();
                playTone(650, 'triangle', 0.1);
            }
        } catch (err) {
            console.error("Scramble API Error:", err);
        } finally {
            btn.innerHTML = `<i class="fa-solid fa-shuffle text-indigo-400"></i> <span>Scramble Cube</span>`;
        }
    });

    // Two-Phase AI Solver API
    document.getElementById('btn-solve')?.addEventListener('click', async () => {
        pausePlayback();
        playTone(400, 'triangle', 0.1);
        const btn = document.getElementById('btn-solve');
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-cyan-300"></i> Solving...`;

        try {
            const res = await fetch('/api/solve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ custom_moves: currentMoves.join(' ') })
            });
            const data = await res.json();

            if (data.solution) {
                currentMoves = data.solution.split(' ');
                currentStepIndex = 0;
                reconstructCubeStateUpToStep(0);
                updateVisualizerUI();
                playSolveFanfare();
                startPlayback();
                loadRecentSolves();
            }
        } catch (err) {
            console.error("Solve API Error:", err);
        } finally {
            btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles text-cyan-300"></i> <span>Two-Phase Solve</span>`;
        }
    });

    // Recent Solves History Loader
    async function loadRecentSolves() {
        const historyList = document.getElementById('recent-solves-list');
        if (!historyList) return;

        try {
            const res = await fetch('/api/history');
            const data = await res.json();
            if (data.history && data.history.length > 0) {
                historyList.innerHTML = '';
                data.history.forEach(item => {
                    const row = document.createElement('div');
                    row.className = 'p-2 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex items-center justify-between';
                    row.innerHTML = `
                        <div class="truncate max-w-[170px]">
                            <span class="text-indigo-400 font-bold">${item.move_count} Moves:</span>
                            <span class="text-slate-400 ml-1">${item.solution}</span>
                        </div>
                        <span class="text-[10px] text-slate-500">${new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    `;
                    historyList.appendChild(row);
                });
            }
        } catch (err) {
            console.error("History fetch error:", err);
        }
    }
    loadRecentSolves();
    document.getElementById('btn-refresh-history')?.addEventListener('click', loadRecentSolves);

    // =========================================================================
    // 8. OPENCV COMPUTER VISION MODAL & INTERACTIVE FACELET SCANNER
    // =========================================================================

    const scannerModal = document.getElementById('scanner-modal');
    const dropzone = document.getElementById('scanner-dropzone');
    const fileInput = document.getElementById('cube-image-input');
    const scannerPlaceholder = document.getElementById('scanner-preview-placeholder');
    const scannerResultBox = document.getElementById('scanner-result-box');
    const previewImg = document.getElementById('cv-annotated-image');
    const interactiveGrid = document.getElementById('cv-interactive-grid');
    const centerBadge = document.getElementById('cv-detected-center-badge');
    const btnApplyFaceText = document.getElementById('btn-apply-face-text');
    const btnApplyScannedFace = document.getElementById('btn-apply-scanned-face');

    let currentTargetFace = 'U'; // Default target face
    let lastScannedFaceGrid = [
        ['Y', 'Y', 'Y'],
        ['Y', 'Y', 'Y'],
        ['Y', 'Y', 'Y']
    ];

    const FACE_OFFSETS = {
        'U': 0,
        'R': 9,
        'F': 18,
        'D': 27,
        'L': 36,
        'B': 45
    };

    const FACE_NAMES = {
        'U': 'Up (Yellow)',
        'L': 'Left (Orange)',
        'F': 'Front (Green)',
        'R': 'Right (Red)',
        'B': 'Back (Blue)',
        'D': 'Down (White)'
    };

    const COLOR_CYCLE = ['Y', 'W', 'G', 'B', 'O', 'R'];
    
    const COLOR_CLASSES = {
        'Y': 'bg-amber-400 text-black border-amber-300 shadow-amber-400/20',
        'W': 'bg-slate-100 text-black border-white shadow-slate-100/20',
        'G': 'bg-emerald-500 text-white border-emerald-300 shadow-emerald-500/20',
        'B': 'bg-blue-600 text-white border-blue-400 shadow-blue-600/20',
        'O': 'bg-orange-500 text-white border-orange-300 shadow-orange-500/20',
        'R': 'bg-rose-600 text-white border-rose-400 shadow-rose-600/20'
    };

    const FACE_TAB_ACTIVE_CLASSES = {
        'U': 'bg-amber-500 text-black border-amber-300 shadow-md',
        'L': 'bg-orange-500 text-white border-orange-300 shadow-md',
        'F': 'bg-emerald-600 text-white border-emerald-300 shadow-md',
        'R': 'bg-rose-600 text-white border-rose-300 shadow-md',
        'B': 'bg-blue-600 text-white border-blue-300 shadow-md',
        'D': 'bg-slate-200 text-black border-white shadow-md'
    };

    const FACE_TAB_INACTIVE_CLASSES = {
        'U': 'bg-slate-800 text-amber-400 border-slate-700 hover:bg-slate-700',
        'L': 'bg-slate-800 text-orange-400 border-slate-700 hover:bg-slate-700',
        'F': 'bg-slate-800 text-emerald-400 border-slate-700 hover:bg-slate-700',
        'R': 'bg-slate-800 text-rose-400 border-slate-700 hover:bg-slate-700',
        'B': 'bg-slate-800 text-blue-400 border-slate-700 hover:bg-slate-700',
        'D': 'bg-slate-800 text-slate-200 border-slate-700 hover:bg-slate-700'
    };

    function setTargetFace(face) {
        currentTargetFace = face;
        document.querySelectorAll('.vis-face-tab').forEach(tab => {
            const f = tab.getAttribute('data-face');
            if (f === face) {
                tab.className = `vis-face-tab px-3 py-1.5 rounded-xl text-xs font-mono font-bold border transition-all ${FACE_TAB_ACTIVE_CLASSES[f] || 'bg-indigo-600 text-white'}`;
            } else {
                tab.className = `vis-face-tab px-3 py-1.5 rounded-xl text-xs font-mono font-bold border transition-all ${FACE_TAB_INACTIVE_CLASSES[f] || 'bg-slate-800 text-slate-400'}`;
            }
        });

        if (btnApplyFaceText) {
            btnApplyFaceText.textContent = `Apply to Face (${currentTargetFace} - ${FACE_NAMES[currentTargetFace] || ''})`;
        }
    }

    // Modal Open / Close
    document.getElementById('btn-open-scanner')?.addEventListener('click', () => {
        scannerModal?.classList.remove('hidden');
        playTone(520, 'sine', 0.05);
    });

    document.getElementById('btn-close-scanner')?.addEventListener('click', () => {
        scannerModal?.classList.add('hidden');
        playTone(400, 'sine', 0.05);
    });

    // Close when clicking backdrop
    scannerModal?.addEventListener('click', (e) => {
        if (e.target === scannerModal) {
            scannerModal.classList.add('hidden');
        }
    });

    // Target Face Tabs Click
    document.querySelectorAll('.vis-face-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const face = tab.getAttribute('data-face');
            if (face) {
                setTargetFace(face);
                playTone(580, 'sine', 0.04);
            }
        });
    });

    // Interactive 3x3 Grid Color Editor Renderer
    function renderInteractiveGrid(grid) {
        if (!interactiveGrid) return;
        interactiveGrid.innerHTML = '';

        for (let r = 0; r < 3; r++) {
            for (let c = 0; c < 3; c++) {
                const cellColor = grid[r][c] || 'Y';
                const cellBtn = document.createElement('button');
                cellBtn.type = 'button';
                cellBtn.className = `w-10 h-10 rounded-xl font-mono font-black text-sm border-2 flex items-center justify-center transition-all transform hover:scale-105 active:scale-95 shadow-md ${COLOR_CLASSES[cellColor] || COLOR_CLASSES['Y']}`;
                cellBtn.textContent = cellColor;
                cellBtn.title = `Row ${r + 1}, Col ${c + 1}: ${cellColor} (Click to change)`;

                cellBtn.addEventListener('click', () => {
                    const currIdx = COLOR_CYCLE.indexOf(lastScannedFaceGrid[r][c]);
                    const nextColor = COLOR_CYCLE[(currIdx + 1) % COLOR_CYCLE.length];
                    lastScannedFaceGrid[r][c] = nextColor;
                    
                    // Update button styling immediately
                    cellBtn.textContent = nextColor;
                    cellBtn.className = `w-10 h-10 rounded-xl font-mono font-black text-sm border-2 flex items-center justify-center transition-all transform hover:scale-105 active:scale-95 shadow-md ${COLOR_CLASSES[nextColor] || COLOR_CLASSES['Y']}`;
                    cellBtn.title = `Row ${r + 1}, Col ${c + 1}: ${nextColor} (Click to change)`;

                    // Audio feedback
                    const toneFreqs = { 'Y': 523, 'W': 587, 'G': 659, 'B': 698, 'O': 784, 'R': 880 };
                    playTone(toneFreqs[nextColor] || 600, 'sine', 0.05);

                    // Update center badge if center sticker changed
                    if (r === 1 && c === 1 && centerBadge) {
                        centerBadge.textContent = `Center: ${nextColor}`;
                    }
                });

                interactiveGrid.appendChild(cellBtn);
            }
        }
    }

    // Display Scan Result Helper
    function displayScanResult(faceGrid, annotatedImgSrc, centerColor) {
        lastScannedFaceGrid = faceGrid;
        
        if (scannerPlaceholder) scannerPlaceholder.classList.add('hidden');
        if (scannerResultBox) scannerResultBox.classList.remove('hidden');
        if (previewImg) previewImg.src = annotatedImgSrc;
        if (centerBadge) centerBadge.textContent = `Center: ${centerColor || faceGrid[1][1]}`;

        renderInteractiveGrid(faceGrid);
    }

    // Sample Preset Loader
    async function loadSamplePreset(sampleId, defaultFace) {
        if (scannerPlaceholder) {
            scannerPlaceholder.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-3xl mb-2 text-cyan-400 block"></i> Loading OpenCV Synthetic Preset...`;
            scannerPlaceholder.classList.remove('hidden');
        }
        if (scannerResultBox) scannerResultBox.classList.add('hidden');

        try {
            const res = await fetch('/api/scan-image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sample_id: sampleId })
            });
            const data = await res.json();
            if (data.success && data.annotated_image) {
                setTargetFace(defaultFace);
                displayScanResult(data.face_grid, data.annotated_image, data.center_color);
                playTone(660, 'triangle', 0.08);
            } else {
                alert(data.error || 'Failed to load sample preset.');
            }
        } catch (err) {
            console.error("Sample preset error:", err);
            alert("Error loading sample preset.");
        }
    }

    document.getElementById('btn-sample-u')?.addEventListener('click', () => loadSamplePreset('sample_u', 'U'));
    document.getElementById('btn-sample-f')?.addEventListener('click', () => loadSamplePreset('sample_f', 'F'));
    document.getElementById('btn-sample-r')?.addEventListener('click', () => loadSamplePreset('sample_r', 'R'));

    // Dropzone & File Input Handlers
    dropzone?.addEventListener('click', () => fileInput?.click());
    dropzone?.addEventListener('dragover', (e) => { 
        e.preventDefault(); 
        dropzone.classList.add('border-emerald-500', 'bg-emerald-950/30'); 
    });
    dropzone?.addEventListener('dragleave', () => {
        dropzone.classList.remove('border-emerald-500', 'bg-emerald-950/30');
    });
    dropzone?.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('border-emerald-500', 'bg-emerald-950/30');
        if (e.dataTransfer.files.length) {
            handleImageUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput?.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleImageUpload(e.target.files[0]);
        }
    });

    async function handleImageUpload(file) {
        const formData = new FormData();
        formData.append('image', file);

        if (scannerPlaceholder) {
            scannerPlaceholder.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-3xl mb-2 text-emerald-400 block"></i> OpenCV CLAHE Normalization & HSV Centroid Extraction...`;
            scannerPlaceholder.classList.remove('hidden');
        }
        if (scannerResultBox) scannerResultBox.classList.add('hidden');

        try {
            const res = await fetch('/api/scan-image', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (data.success && data.annotated_image) {
                // Auto-suggest face matching center color if recognized
                const centerToFace = { 'Y': 'U', 'W': 'D', 'G': 'F', 'B': 'B', 'O': 'L', 'R': 'R' };
                if (data.center_color && centerToFace[data.center_color]) {
                    setTargetFace(centerToFace[data.center_color]);
                }
                displayScanResult(data.face_grid, data.annotated_image, data.center_color);
                playTone(660, 'triangle', 0.1);
            } else {
                if (scannerPlaceholder) {
                    scannerPlaceholder.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-3xl mb-2 text-rose-400 block"></i> ${data.error || 'Failed to parse cube face. Please try another photo.'}`;
                }
            }
        } catch (err) {
            console.error("Scan upload error:", err);
            if (scannerPlaceholder) {
                scannerPlaceholder.innerHTML = `<i class="fa-solid fa-circle-xmark text-3xl mb-2 text-rose-400 block"></i> Network or server error during scanning.`;
            }
        }
    }

    // Apply Scanned Face to Cube State
    btnApplyScannedFace?.addEventListener('click', () => {
        if (!lastScannedFaceGrid) return;

        const offset = FACE_OFFSETS[currentTargetFace] ?? 0;
        const colorToStateCode = {
            'Y': 'U', 'W': 'D', 'G': 'F', 'B': 'B', 'O': 'L', 'R': 'R',
            'U': 'U', 'D': 'D', 'F': 'F', 'L': 'L'
        };

        // Write 9 facelets into cubeState array
        for (let r = 0; r < 3; r++) {
            for (let c = 0; c < 3; c++) {
                const colorCode = lastScannedFaceGrid[r][c];
                cubeState[offset + (r * 3 + c)] = colorToStateCode[colorCode] || colorCode;
            }
        }

        // Re-render 3D Isometric SVG
        renderIsometricCube();

        // Re-render Permutation Orbit
        renderPermutationOrbit(currentMoves[currentStepIndex] || 'U');

        // Play solve/chime fanfare
        playSolveFanfare();

        // Visual confirmation feedback
        if (btnApplyFaceText) {
            const originalText = btnApplyFaceText.textContent;
            btnApplyFaceText.textContent = `✓ ${currentTargetFace} Face Updated!`;
            setTimeout(() => {
                btnApplyFaceText.textContent = originalText;
                scannerModal?.classList.add('hidden');
            }, 650);
        } else {
            scannerModal?.classList.add('hidden');
        }
    });

    // Group Theory Modal Toggle
    const mathModal = document.getElementById('math-modal');
    document.getElementById('btn-toggle-math')?.addEventListener('click', () => mathModal?.classList.remove('hidden'));
    document.getElementById('btn-close-math')?.addEventListener('click', () => mathModal?.classList.add('hidden'));

    // Keyboard Shortcuts (Arrow Left/Right, Space to Play/Pause)
    window.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT') return;
        if (e.code === 'Space') {
            e.preventDefault();
            togglePlay();
        } else if (e.code === 'ArrowRight') {
            pausePlayback();
            nextStep();
        } else if (e.code === 'ArrowLeft') {
            pausePlayback();
            prevStep();
        }
    });

    // =========================================================================
    // 9. 3D WEBGL INTERACTIVE THREE.JS CUBE TOGGLE & SYNCHRONIZATION
    // =========================================================================
    let visualizer3DCube = null;
    if (document.getElementById('visualizer-3d-cube') && typeof Interactive3DCube !== 'undefined') {
        visualizer3DCube = new Interactive3DCube('visualizer-3d-cube', {
            autoRotate: false
        });
    }

    const btnModeIso = document.getElementById('view-mode-iso');
    const btnModeWebGL = document.getElementById('view-mode-webgl');
    const isoContainer = document.getElementById('isometric-cube-container');
    const webglContainer = document.getElementById('webgl-cube-container');

    btnModeIso?.addEventListener('click', () => {
        btnModeIso.className = "px-2.5 py-0.5 rounded-full bg-indigo-600 text-white font-bold transition-all";
        btnModeWebGL.className = "px-2.5 py-0.5 rounded-full text-slate-400 hover:text-white transition-all flex items-center gap-1";
        isoContainer?.classList.remove('hidden');
        webglContainer?.classList.add('hidden');
        webglContainer?.classList.remove('flex');
    });

    btnModeWebGL?.addEventListener('click', () => {
        btnModeWebGL.className = "px-2.5 py-0.5 rounded-full bg-indigo-600 text-white font-bold transition-all flex items-center gap-1";
        btnModeIso.className = "px-2.5 py-0.5 rounded-full text-slate-400 hover:text-white transition-all";
        isoContainer?.classList.add('hidden');
        webglContainer?.classList.remove('hidden');
        webglContainer?.classList.add('flex');
        if (visualizer3DCube) {
            visualizer3DCube.onResize();
        }
    });

    // Hook WebGL 3D cube turn animation on every step update
    const originalNextStep = nextStep;
    window.addEventListener('moveApplied', (e) => {
        if (visualizer3DCube && e.detail && e.detail.move) {
            visualizer3DCube.animateLayerTurn(e.detail.move);
        }
    });

    // =========================================================================
    // 10. VISUAL SPEEDCUBING LABORATORY & PROBLEM DIAGNOSTIC HUB ENGINE
    // =========================================================================

    const tabEasy = document.getElementById('tab-btn-easy');
    const tabMath = document.getElementById('tab-btn-math');
    const tabDoctor = document.getElementById('tab-btn-doctor');

    const panelEasy = document.getElementById('panel-easy');
    const panelMath = document.getElementById('panel-math');
    const panelDoctor = document.getElementById('panel-doctor');

    function switchLabTab(activeTab, activePanel) {
        [tabEasy, tabMath, tabDoctor].forEach(tab => {
            if (tab) {
                tab.className = "lab-tab-btn px-3.5 py-2 rounded-xl text-xs font-bold font-mono text-slate-400 hover:text-white transition-all flex items-center gap-2";
            }
        });
        [panelEasy, panelMath, panelDoctor].forEach(panel => {
            if (panel) panel.classList.add('hidden');
        });

        if (activeTab) {
            activeTab.className = "lab-tab-btn active px-3.5 py-2 rounded-xl text-xs font-bold font-mono transition-all flex items-center gap-2 bg-indigo-600 text-white shadow-md";
        }
        if (activePanel) {
            activePanel.classList.remove('hidden');
        }
        playTone(550, 'sine', 0.05);
    }

    tabEasy?.addEventListener('click', () => switchLabTab(tabEasy, panelEasy));
    tabMath?.addEventListener('click', () => switchLabTab(tabMath, panelMath));
    tabDoctor?.addEventListener('click', () => switchLabTab(tabDoctor, panelDoctor));

    // Universal Sequence Loader & 3D Playback Dispatcher
    window.loadAndPlaySequence = function(seqStr, autoPlay = true) {
        if (!seqStr || !seqStr.trim()) return;
        pausePlayback();
        playTone(520, 'triangle', 0.1);

        const moves = seqStr.trim().split(/\s+/);
        currentMoves = moves;
        currentStepIndex = 0;
        
        // Reset cube state and prepare 1st step
        initSolvedState();
        reconstructCubeStateUpToStep(0);
        updateVisualizerUI();

        // Smooth scroll to visualizer stage if below view
        const stage = document.getElementById('cube-visualizer-stage') || document.getElementById('isometric-cube-container');
        if (stage) {
            const rect = stage.getBoundingClientRect();
            if (rect.top < 0 || rect.bottom > window.innerHeight) {
                stage.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }

        if (autoPlay) {
            setTimeout(() => {
                startPlayback();
            }, 350);
        }
    };

    // Attach click handlers to all Laboratory Simulation Buttons
    document.querySelectorAll('.btn-play-lab-seq').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const targetBtn = e.currentTarget;
            const seq = targetBtn.getAttribute('data-seq');
            if (seq) {
                window.loadAndPlaySequence(seq, true);
            }
        });
    });

    // Initial Render
    reconstructCubeStateUpToStep(currentStepIndex);
    updateVisualizerUI();

});

