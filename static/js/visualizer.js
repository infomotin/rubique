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

        // Defs for glowing gradients and filters
        const defs = document.createElementNS(ns, "defs");
        defs.innerHTML = `
            <filter id="glow-cyan" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                </feMerge>
            </filter>
            <filter id="glow-white" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="5" result="blur" />
                <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                </feMerge>
            </filter>
        `;
        svg.appendChild(defs);

        // 1. Concentric and Intersecting Orbit Rings
        const rings = [
            { cx: 0, cy: -20, r: 80 },
            { cx: -50, cy: 35, r: 85 },
            { cx: 50, cy: 35, r: 85 },
            { cx: 0, cy: 0, r: 125 },
            { cx: 0, cy: -30, r: 155 },
            { cx: 0, cy: 20, r: 170 }
        ];

        rings.forEach(r => {
            const circle = document.createElementNS(ns, "circle");
            circle.setAttribute("cx", r.cx);
            circle.setAttribute("cy", r.cy);
            circle.setAttribute("r", r.r);
            circle.setAttribute("class", "orbit-track");
            svg.appendChild(circle);
        });

        // 2. Active Dynamic Highlight Arc (Corresponds to active move cycle)
        const gActiveArc = document.createElementNS(ns, "g");
        
        // Active Move Arc Path calculation (Top Active Arc in Reference Image)
        const arcRadius = 78;
        const startAngle = -170;
        const endAngle = 30;
        
        // Convert polar to Cartesian for SVG Arc path
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
            const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
            return [
                "M", start.x, start.y, 
                "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y
            ].join(" ");
        }

        // Glowing Cyan Upper Arc
        const arcPathCyan = document.createElementNS(ns, "path");
        arcPathCyan.setAttribute("d", describeArc(0, -20, arcRadius, -140, 20));
        arcPathCyan.setAttribute("fill", "none");
        arcPathCyan.setAttribute("stroke", "#38bdf8");
        arcPathCyan.setAttribute("stroke-width", "4.5");
        arcPathCyan.setAttribute("stroke-linecap", "round");
        arcPathCyan.setAttribute("filter", "url(#glow-cyan)");
        gActiveArc.appendChild(arcPathCyan);

        // Glowing White Arc Segment
        const arcPathWhite = document.createElementNS(ns, "path");
        arcPathWhite.setAttribute("d", describeArc(0, -20, arcRadius, 20, 140));
        arcPathWhite.setAttribute("fill", "none");
        arcPathWhite.setAttribute("stroke", "#ffffff");
        arcPathWhite.setAttribute("stroke-width", "4");
        arcPathWhite.setAttribute("stroke-linecap", "round");
        arcPathWhite.setAttribute("filter", "url(#glow-white)");
        gActiveArc.appendChild(arcPathWhite);

        // Glowing Red/Green Lower Arc Segment
        const arcPathLower = document.createElementNS(ns, "path");
        arcPathLower.setAttribute("d", describeArc(0, -20, arcRadius, 140, 220));
        arcPathLower.setAttribute("fill", "none");
        arcPathLower.setAttribute("stroke", "#ef4444");
        arcPathLower.setAttribute("stroke-width", "3.5");
        arcPathLower.setAttribute("stroke-linecap", "round");
        gActiveArc.appendChild(arcPathLower);

        svg.appendChild(gActiveArc);

        // 3. Move Label Near Active Orbit (e.g. 'U')
        const moveText = document.createElementNS(ns, "text");
        moveText.setAttribute("x", "-70");
        moveText.setAttribute("y", "-85");
        moveText.setAttribute("fill", "#e2e8f0");
        moveText.setAttribute("font-family", "Outfit, serif");
        moveText.setAttribute("font-size", "15");
        moveText.setAttribute("font-weight", "600");
        moveText.textContent = activeMove;
        svg.appendChild(moveText);

        // 4. Colored Orbit Node Vertices (Yellow, Blue, Orange, White, Green, Red)
        const nodeClusters = [
            // Top Center Cluster (Yellow Nodes - U Face)
            { x: -18, y: -45, color: '#facc15' },
            { x: 0, y: -45, color: '#facc15' },
            { x: 18, y: -45, color: '#facc15' },
            { x: -9, y: -30, color: '#facc15' },
            { x: 9, y: -30, color: '#facc15' },

            // Upper Arc Outer Nodes (Yellow/Blue boundary)
            { x: 25, y: -95, color: '#38bdf8' },
            { x: 42, y: -85, color: '#38bdf8' },
            { x: 55, y: -70, color: '#facc15' },

            // Right Upper Cluster (Blue Nodes - B Face)
            { x: 80, y: -50, color: '#3b82f6' },
            { x: 95, y: -35, color: '#3b82f6' },
            { x: 105, y: -20, color: '#3b82f6' },
            { x: 120, y: -5, color: '#3b82f6' },
            { x: 105, y: 15, color: '#facc15' },

            // Right Middle Arc (Orange Nodes - L/R Face)
            { x: 62, y: -15, color: '#fb923c' },
            { x: 65, y: 2, color: '#fb923c' },
            { x: 66, y: 20, color: '#fb923c' },
            { x: 63, y: 38, color: '#fb923c' },
            { x: 58, y: 55, color: '#fb923c' },
            { x: 48, y: 72, color: '#fb923c' },

            // Center Ring Inner Nodes (Green/Yellow/Red Center)
            { x: -8, y: -15, color: '#facc15' },
            { x: 8, y: -15, color: '#22c55e' },
            { x: 0, y: 2, color: '#22c55e' },

            // Left Middle Arc (Green & Red Nodes)
            { x: -55, y: 65, color: '#22c55e' },
            { x: -40, y: 78, color: '#22c55e' },
            { x: -22, y: 84, color: '#22c55e' },
            { x: -62, y: 45, color: '#ef4444' },
            { x: -66, y: 28, color: '#ef4444' },
            { x: -66, y: 10, color: '#ef4444' },
            { x: -62, y: -8, color: '#ef4444' },
            { x: -55, y: -25, color: '#ef4444' },

            // Left Outer Boundary Nodes (Red/Blue)
            { x: -80, y: -45, color: '#ef4444' },
            { x: -95, y: -30, color: '#ef4444' },
            { x: -105, y: -12, color: '#3b82f6' },
            { x: -120, y: 5, color: '#3b82f6' },

            // Bottom Diamond / Cluster (White & Blue Nodes - D Face)
            { x: 0, y: 110, color: '#ffffff' },
            { x: -16, y: 124, color: '#ffffff' },
            { x: 0, y: 124, color: '#ffffff' },
            { x: 16, y: 124, color: '#ffffff' },
            { x: -32, y: 138, color: '#3b82f6' },
            { x: -16, y: 138, color: '#ffffff' },
            { x: 0, y: 138, color: '#ffffff' },
            { x: 16, y: 138, color: '#ffffff' },
            { x: 32, y: 138, color: '#3b82f6' },
            { x: 0, y: 152, color: '#3b82f6' }
        ];

        nodeClusters.forEach((node, i) => {
            const circle = document.createElementNS(ns, "circle");
            circle.setAttribute("cx", node.x);
            circle.setAttribute("cy", node.y);
            circle.setAttribute("r", "4.2");
            circle.setAttribute("fill", node.color);
            circle.setAttribute("class", "orbit-node");
            circle.setAttribute("stroke", "#05070c");
            circle.setAttribute("stroke-width", "1.2");
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

        // 4. Render Isometric Cube & Permutation Orbit Network
        const twistAngle = (activeMove === 'U' || activeMove === "U'" || activeMove === 'U2') ? 22 : 0;
        renderIsometricCube(twistAngle);
        renderPermutationOrbit(activeMove);
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
    // 8. OPENCV COMPUTER VISION MODAL & SCANNER
    // =========================================================================

    const scannerModal = document.getElementById('scanner-modal');
    const dropzone = document.getElementById('scanner-dropzone');
    const fileInput = document.getElementById('cube-image-input');
    let lastScannedFaceGrid = null;

    document.getElementById('btn-open-scanner')?.addEventListener('click', () => {
        scannerModal?.classList.remove('hidden');
    });
    document.getElementById('btn-close-scanner')?.addEventListener('click', () => {
        scannerModal?.classList.add('hidden');
    });

    dropzone?.addEventListener('click', () => fileInput?.click());
    dropzone?.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('border-emerald-500'); });
    dropzone?.addEventListener('dragleave', () => dropzone.classList.remove('border-emerald-500'));
    dropzone?.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('border-emerald-500');
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

        const placeholder = document.getElementById('scanner-preview-placeholder');
        const resultBox = document.getElementById('scanner-result-box');
        const previewImg = document.getElementById('cv-annotated-image');

        if (placeholder) placeholder.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-2xl mb-2 text-emerald-400 block"></i> OpenCV Image Processing & HSV Clustering...`;

        try {
            const res = await fetch('/api/scan-image', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (data.success && data.annotated_image) {
                lastScannedFaceGrid = data.face_grid;
                if (placeholder) placeholder.classList.add('hidden');
                if (resultBox) resultBox.classList.remove('hidden');
                if (previewImg) previewImg.src = data.annotated_image;
            } else {
                alert(data.error || 'Failed to parse cube face.');
            }
        } catch (err) {
            console.error("Scan upload error:", err);
            alert("Network error scanning image.");
        }
    }

    document.getElementById('btn-apply-scanned-face')?.addEventListener('click', () => {
        if (lastScannedFaceGrid) {
            // Apply scanned 3x3 to Top U Face
            for (let r = 0; r < 3; r++) {
                for (let c = 0; c < 3; c++) {
                    cubeState[r * 3 + c] = lastScannedFaceGrid[r][c];
                }
            }
            renderIsometricCube();
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

    // Initial Render
    reconstructCubeStateUpToStep(currentStepIndex);
    updateVisualizerUI();

});
