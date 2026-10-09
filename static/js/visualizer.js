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
    function renderIsometricCube(twistAngle = 0, activeMove = 'U', isAnimating = false) {
        const svg = document.getElementById('isometric-cube-svg');
        if (!svg) return;
        svg.innerHTML = '';

        const s = 34; // Facelet cell size
        const gap = 2.5; // Gap between facelets

        // Group element for dynamic layer twist animation
        const gMain = document.createElementNS("http://www.w3.org/2000/svg", "g");

        // -------------------------------------------------------------
        // TOP FACE (U: Yellow) - With potential rotation angle
        // -------------------------------------------------------------
        const gTopLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
        gTopLayer.style.transformOrigin = "0px -55px";
        if (isAnimating && twistAngle !== 0) {
            gTopLayer.style.transition = "transform 0.35s cubic-bezier(0.34, 1.3, 0.64, 1)";
            gTopLayer.style.transform = `rotate(${twistAngle}deg)`;
            setTimeout(() => {
                gTopLayer.style.transform = "rotate(0deg)";
            }, 300);
        } else if (twistAngle !== 0) {
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
        const gFrontFace = document.createElementNS("http://www.w3.org/2000/svg", "g");
        if (isAnimating && activeMove && activeMove.startsWith('F')) {
            const fAngle = activeMove.includes("'") ? -10 : 10;
            gFrontFace.style.transformOrigin = "-35px 30px";
            gFrontFace.style.transition = "transform 0.35s cubic-bezier(0.34, 1.3, 0.64, 1)";
            gFrontFace.style.transform = `rotate(${fAngle}deg)`;
            setTimeout(() => {
                gFrontFace.style.transform = "rotate(0deg)";
            }, 300);
        }

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

                gFrontFace.appendChild(poly);
            }
        }
        gMain.appendChild(gFrontFace);

        // -------------------------------------------------------------
        // RIGHT FACE (R: Orange / Red)
        // -------------------------------------------------------------
        const gRightFace = document.createElementNS("http://www.w3.org/2000/svg", "g");
        if (isAnimating && activeMove && activeMove.startsWith('R')) {
            const rAngle = activeMove.includes("'") ? -10 : 10;
            gRightFace.style.transformOrigin = "35px 30px";
            gRightFace.style.transition = "transform 0.35s cubic-bezier(0.34, 1.3, 0.64, 1)";
            gRightFace.style.transform = `rotate(${rAngle}deg)`;
            setTimeout(() => {
                gRightFace.style.transform = "rotate(0deg)";
            }, 300);
        }

        for (let row = 0; row < 3; row++) {
            for (let col = 0; col < 3; col++) {
                const idx = 9 + (row * 3 + col); // 9 to 17
                const colorKey = cubeState[idx] || 'R';
                const fillColor = COLOR_PALETTE[colorKey] || COLOR_PALETTE['R'];

                const z0 = (1.5 - col) * (s + gap) - s;
                const y0 = (1.5 - row) * (s + gap) - s;
                const x0 = 1.5 * (s + gap); // Right face x position

                const p1 = isoProject(x0, y0 + s, z0);
                const p2 = isoProject(x0 + s, y0 + s, z0 + s);
                const p3 = isoProject(x0, y0, z0 + s);
                const p4 = isoProject(x0, y0, z0);

                const poly = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
                poly.setAttribute("points", createPolygonPoints(p1, p2, p3, p4));
                poly.setAttribute("fill", fillColor);
                poly.setAttribute("class", "cube-facelet");
                poly.setAttribute("data-facelet", `R${row * 3 + col}`);
                poly.setAttribute("stroke", "#111827");
                poly.setAttribute("stroke-width", "2");

                gRightFace.appendChild(poly);
            }
        }
        gMain.appendChild(gRightFace);

        svg.appendChild(gMain);
    }

    // =========================================================================
    // 3. REAL-TIME CUBE PERMUTATION ORBIT ENGINE (DYNAMIC KINEMATICS)
    // =========================================================================

    let orbitDisplayMode = 'live'; // 'live' or 'matrix'
    let selectedOrbitFace = null;  // null = auto follow active move

    // Cardinal Piece Index Definitions for Each Face on the 54-Facelet Cube
    const FACE_PIECE_MAPPINGS = {
        'U': {
            name: 'Up Layer (Top)',
            colorKey: 'U',
            centerIdx: 4,
            edges: [
                { pos: 'North', name: 'UB', p: 1, s: 46, angle: 0 },
                { pos: 'East',  name: 'UR', p: 5, s: 10, angle: 90 },
                { pos: 'South', name: 'UF', p: 7, s: 19, angle: 180 },
                { pos: 'West',  name: 'UL', p: 3, s: 37, angle: 270 }
            ],
            corners: [
                { pos: 'NW', name: 'UBL', p: 0, s1: 47, s2: 36, angle: 315 },
                { pos: 'NE', name: 'UBR', p: 2, s1: 45, s2: 11, angle: 45 },
                { pos: 'SE', name: 'UFR', p: 8, s1: 20, s2: 9,  angle: 135 },
                { pos: 'SW', name: 'UFL', p: 6, s1: 18, s2: 38, angle: 225 }
            ],
            cycleEdges: 'UB → UR → UF → UL',
            cycleCorners: 'UBL → UBR → UFR → UFL'
        },
        'D': {
            name: 'Down Foundation (Bottom)',
            colorKey: 'D',
            centerIdx: 31,
            edges: [
                { pos: 'North', name: 'DF', p: 28, s: 25, angle: 0 },
                { pos: 'East',  name: 'DR', p: 32, s: 16, angle: 90 },
                { pos: 'South', name: 'DB', p: 34, s: 52, angle: 180 },
                { pos: 'West',  name: 'DL', p: 30, s: 43, angle: 270 }
            ],
            corners: [
                { pos: 'NW', name: 'DFL', p: 27, s1: 24, s2: 44, angle: 315 },
                { pos: 'NE', name: 'DFR', p: 29, s1: 26, s2: 15, angle: 45 },
                { pos: 'SE', name: 'DBR', p: 35, s1: 53, s2: 17, angle: 135 },
                { pos: 'SW', name: 'DBL', p: 33, s1: 51, s2: 42, angle: 225 }
            ],
            cycleEdges: 'DF → DR → DB → DL',
            cycleCorners: 'DFL → DFR → DBR → DBL'
        },
        'F': {
            name: 'Front Layer (View)',
            colorKey: 'F',
            centerIdx: 22,
            edges: [
                { pos: 'North', name: 'FU', p: 19, s: 7,  angle: 0 },
                { pos: 'East',  name: 'FR', p: 23, s: 12, angle: 90 },
                { pos: 'South', name: 'FD', p: 25, s: 28, angle: 180 },
                { pos: 'West',  name: 'FL', p: 21, s: 41, angle: 270 }
            ],
            corners: [
                { pos: 'NW', name: 'FLU', p: 18, s1: 6,  s2: 38, angle: 315 },
                { pos: 'NE', name: 'FRU', p: 20, s1: 8,  s2: 9,  angle: 45 },
                { pos: 'SE', name: 'FRD', p: 26, s1: 29, s2: 15, angle: 135 },
                { pos: 'SW', name: 'FLD', p: 24, s1: 27, s2: 44, angle: 225 }
            ],
            cycleEdges: 'FU → FR → FD → FL',
            cycleCorners: 'FLU → FRU → FRD → FLD'
        },
        'B': {
            name: 'Back Layer (Rear)',
            colorKey: 'B',
            centerIdx: 49,
            edges: [
                { pos: 'North', name: 'BU', p: 46, s: 1,  angle: 0 },
                { pos: 'East',  name: 'BL', p: 50, s: 39, angle: 90 },
                { pos: 'South', name: 'BD', p: 52, s: 34, angle: 180 },
                { pos: 'West',  name: 'BR', p: 48, s: 14, angle: 270 }
            ],
            corners: [
                { pos: 'NW', name: 'BLU', p: 47, s1: 0,  s2: 36, angle: 315 },
                { pos: 'NE', name: 'BRU', p: 45, s1: 2,  s2: 11, angle: 45 },
                { pos: 'SE', name: 'BRD', p: 51, s1: 35, s2: 17, angle: 135 },
                { pos: 'SW', name: 'BLD', p: 53, s1: 33, s2: 42, angle: 225 }
            ],
            cycleEdges: 'BU → BL → BD → BR',
            cycleCorners: 'BLU → BRU → BRD → BLD'
        },
        'L': {
            name: 'Left Layer (Flank)',
            colorKey: 'L',
            centerIdx: 40,
            edges: [
                { pos: 'North', name: 'LU', p: 37, s: 3,  angle: 0 },
                { pos: 'East',  name: 'LF', p: 41, s: 21, angle: 90 },
                { pos: 'South', name: 'LD', p: 43, s: 30, angle: 180 },
                { pos: 'West',  name: 'LB', p: 39, s: 50, angle: 270 }
            ],
            corners: [
                { pos: 'NW', name: 'LUB', p: 36, s1: 0,  s2: 47, angle: 315 },
                { pos: 'NE', name: 'LUF', p: 38, s1: 6,  s2: 18, angle: 45 },
                { pos: 'SE', name: 'LDF', p: 44, s1: 27, s2: 24, angle: 135 },
                { pos: 'SW', name: 'LDB', p: 42, s1: 33, s2: 51, angle: 225 }
            ],
            cycleEdges: 'LU → LF → LD → LB',
            cycleCorners: 'LUB → LUF → LDF → LDB'
        },
        'R': {
            name: 'Right Layer (Generator)',
            colorKey: 'R',
            centerIdx: 13,
            edges: [
                { pos: 'North', name: 'RU', p: 10, s: 5,  angle: 0 },
                { pos: 'East',  name: 'RB', p: 14, s: 48, angle: 90 },
                { pos: 'South', name: 'RD', p: 16, s: 32, angle: 180 },
                { pos: 'West',  name: 'RF', p: 12, s: 23, angle: 270 }
            ],
            corners: [
                { pos: 'NW', name: 'RUF', p: 9,  s1: 8,  s2: 20, angle: 315 },
                { pos: 'NE', name: 'RUB', p: 11, s1: 2,  s2: 45, angle: 45 },
                { pos: 'SE', name: 'RDB', p: 17, s1: 35, s2: 53, angle: 135 },
                { pos: 'SW', name: 'RDF', p: 15, s1: 29, s2: 26, angle: 225 }
            ],
            cycleEdges: 'RU → RB → RD → RF',
            cycleCorners: 'RUF → RUB → RDB → RDF'
        }
    };

    /**
     * Real-Time Permutation Orbit Engine:
     * - Dynamically reads live cubeState colors.
     * - Renders concentric animated orbit rings with realistic stickers.
     * - Rotates pieces in real time according to move direction and angle.
     */
    function renderPermutationOrbit(activeMove = 'U', isAnimating = false) {
        const svg = document.getElementById('permutation-orbit-svg');
        if (!svg) return;
        svg.innerHTML = '';

        const ns = "http://www.w3.org/2000/svg";
        const rawFace = activeMove ? activeMove[0] : 'U';
        const baseFace = selectedOrbitFace || (FACE_PIECE_MAPPINGS[rawFace] ? rawFace : 'U');
        const faceData = FACE_PIECE_MAPPINGS[baseFace] || FACE_PIECE_MAPPINGS['U'];

        const isCounter = activeMove && activeMove.includes("'");
        const isDouble = activeMove && activeMove.includes("2");
        const turnDeg = isDouble ? 180 : (isCounter ? -90 : 90);
        const turnSymbol = isDouble ? '↻ 180°' : (isCounter ? '↺ -90°' : '↻ +90°');

        // SVG Defs: Filters & Glow Effects
        const defs = document.createElementNS(ns, "defs");
        defs.innerHTML = `
            <filter id="orbit-glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                </feMerge>
            </filter>
            <filter id="sticker-shadow" x="-30%" y="-30%" width="160%" height="160%">
                <feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="rgba(0,0,0,0.7)" />
            </filter>
            <marker id="orbit-arrow-cw" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#38bdf8" />
            </marker>
            <marker id="orbit-arrow-ccw" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 8 1.5 L 0 5 L 8 8.5 z" fill="#f43f5e" />
            </marker>
        `;
        svg.appendChild(defs);

        if (orbitDisplayMode === 'matrix') {
            renderCayleyMatrixGraph(svg, ns, baseFace, activeMove, turnSymbol);
            return;
        }

        // =====================================================================
        // MODE 1: LIVE REAL-TIME PIECE ORBIT (Intuitive, Animated, Real-Time)
        // =====================================================================

        // 1. Static Outer Ambient Compass Ring
        const gBackground = document.createElementNS(ns, "g");
        
        // Deep Ambient Halo
        const halo = document.createElementNS(ns, "circle");
        halo.setAttribute("cx", "0");
        halo.setAttribute("cy", "0");
        halo.setAttribute("r", "165");
        halo.setAttribute("fill", "none");
        halo.setAttribute("stroke", "rgba(99, 102, 241, 0.12)");
        halo.setAttribute("stroke-width", "2");
        halo.setAttribute("stroke-dasharray", "4, 6");
        gBackground.appendChild(halo);

        // Corner Orbit Track (Radius: 135)
        const cornerTrack = document.createElementNS(ns, "circle");
        cornerTrack.setAttribute("cx", "0");
        cornerTrack.setAttribute("cy", "0");
        cornerTrack.setAttribute("r", "135");
        cornerTrack.setAttribute("fill", "none");
        cornerTrack.setAttribute("stroke", "rgba(56, 189, 248, 0.3)");
        cornerTrack.setAttribute("stroke-width", "2");
        cornerTrack.setAttribute("stroke-dasharray", isCounter ? "6, 4" : "10, 6");
        cornerTrack.setAttribute("class", "animate-spin-slow");
        gBackground.appendChild(cornerTrack);

        // Edge Orbit Track (Radius: 75)
        const edgeTrack = document.createElementNS(ns, "circle");
        edgeTrack.setAttribute("cx", "0");
        edgeTrack.setAttribute("cy", "0");
        edgeTrack.setAttribute("r", "75");
        edgeTrack.setAttribute("fill", "none");
        edgeTrack.setAttribute("stroke", "rgba(129, 140, 248, 0.45)");
        edgeTrack.setAttribute("stroke-width", "2.5");
        edgeTrack.setAttribute("stroke-dasharray", "8, 5");
        edgeTrack.setAttribute("filter", "url(#orbit-glow)");
        gBackground.appendChild(edgeTrack);

        // Directional Flux Arrows along Orbit
        const arrowMarker = isCounter ? 'url(#orbit-arrow-ccw)' : 'url(#orbit-arrow-cw)';
        const edgeArrowArc = document.createElementNS(ns, "path");
        const arcD = isCounter 
            ? "M 75 0 A 75 75 0 0 0 0 -75"
            : "M 0 -75 A 75 75 0 0 1 75 0";
        edgeArrowArc.setAttribute("d", arcD);
        edgeArrowArc.setAttribute("fill", "none");
        edgeArrowArc.setAttribute("stroke", isCounter ? "#f43f5e" : "#38bdf8");
        edgeArrowArc.setAttribute("stroke-width", "3");
        edgeArrowArc.setAttribute("marker-end", arrowMarker);
        gBackground.appendChild(edgeArrowArc);

        svg.appendChild(gBackground);

        // 2. DYNAMIC REAL-TIME ROTATING PIECES GROUP
        const gRotating = document.createElementNS(ns, "g");
        gRotating.setAttribute("id", "dynamic-orbit-rotating-group");
        gRotating.style.transformOrigin = "0px 0px";
        if (isAnimating) {
            gRotating.style.transition = "none";
            gRotating.style.transform = `rotate(${-turnDeg}deg)`;
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    gRotating.style.transition = "transform 0.42s cubic-bezier(0.2, 0.8, 0.2, 1)";
                    gRotating.style.transform = "rotate(0deg)";
                });
            });

            // Real-Time Permutation Shockwave Pulse
            const shockwave = document.createElementNS(ns, "circle");
            shockwave.setAttribute("cx", "0");
            shockwave.setAttribute("cy", "0");
            shockwave.setAttribute("r", "28");
            shockwave.setAttribute("fill", "none");
            shockwave.setAttribute("stroke", isCounter ? "#f43f5e" : "#38bdf8");
            shockwave.setAttribute("stroke-width", "3");
            shockwave.style.transition = "all 0.45s ease-out";
            svg.appendChild(shockwave);
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    shockwave.setAttribute("r", "150");
                    shockwave.setAttribute("stroke-width", "0.5");
                    shockwave.style.opacity = "0";
                });
            });
        } else {
            gRotating.style.transition = "none";
            gRotating.style.transform = "rotate(0deg)";
        }

        // Helper: Convert Polar (angle in deg, radius) to Cartesian (x, y)
        const polarToCart = (deg, r) => {
            const rad = (deg - 90) * Math.PI / 180;
            return { x: r * Math.cos(rad), y: r * Math.sin(rad) };
        };

        // Render 4 Corner Pieces (Radius: 135)
        faceData.corners.forEach(corner => {
            const pt = polarToCart(corner.angle, 135);
            const c1 = COLOR_PALETTE[cubeState[corner.p]] || '#facc15';
            const c2 = COLOR_PALETTE[cubeState[corner.s1]] || '#22c55e';
            const c3 = COLOR_PALETTE[cubeState[corner.s2]] || '#ef4444';

            const gCorner = document.createElementNS(ns, "g");
            gCorner.setAttribute("transform", `translate(${pt.x}, ${pt.y})`);
            gCorner.setAttribute("class", "cursor-pointer transition-transform hover:scale-110");
            gCorner.setAttribute("filter", "url(#sticker-shadow)");

            // Corner Background Capsule
            const bgRect = document.createElementNS(ns, "rect");
            bgRect.setAttribute("x", "-17");
            bgRect.setAttribute("y", "-17");
            bgRect.setAttribute("width", "34");
            bgRect.setAttribute("height", "34");
            bgRect.setAttribute("rx", "9");
            bgRect.setAttribute("fill", "#0b0f19");
            bgRect.setAttribute("stroke", "#334155");
            gCorner.appendChild(bgRect);

            // 3-Facelet Tri-Color Badge
            const s1 = document.createElementNS(ns, "rect");
            s1.setAttribute("x", "-13");
            s1.setAttribute("y", "-13");
            s1.setAttribute("width", "12");
            s1.setAttribute("height", "26");
            s1.setAttribute("rx", "4");
            s1.setAttribute("fill", c1);
            gCorner.appendChild(s1);

            const s2 = document.createElementNS(ns, "rect");
            s2.setAttribute("x", "1");
            s2.setAttribute("y", "-13");
            s2.setAttribute("width", "12");
            s2.setAttribute("height", "12");
            s2.setAttribute("rx", "3");
            s2.setAttribute("fill", c2);
            gCorner.appendChild(s2);

            const s3 = document.createElementNS(ns, "rect");
            s3.setAttribute("x", "1");
            s3.setAttribute("y", "1");
            s3.setAttribute("width", "12");
            s3.setAttribute("height", "12");
            s3.setAttribute("rx", "3");
            s3.setAttribute("fill", c3);
            gCorner.appendChild(s3);

            // Piece Label
            const lbl = document.createElementNS(ns, "text");
            lbl.setAttribute("x", "0");
            lbl.setAttribute("y", "26");
            lbl.setAttribute("text-anchor", "middle");
            lbl.setAttribute("fill", "#94a3b8");
            lbl.setAttribute("font-size", "9");
            lbl.setAttribute("font-family", "monospace");
            lbl.setAttribute("font-weight", "bold");
            lbl.textContent = corner.name;
            gCorner.appendChild(lbl);

            gRotating.appendChild(gCorner);
        });

        // Render 4 Edge Pieces (Radius: 75)
        faceData.edges.forEach(edge => {
            const pt = polarToCart(edge.angle, 75);
            const cPrimary = COLOR_PALETTE[cubeState[edge.p]] || '#facc15';
            const cSide = COLOR_PALETTE[cubeState[edge.s]] || '#3b82f6';

            const gEdge = document.createElementNS(ns, "g");
            gEdge.setAttribute("transform", `translate(${pt.x}, ${pt.y})`);
            gEdge.setAttribute("class", "cursor-pointer transition-transform hover:scale-110");
            gEdge.setAttribute("filter", "url(#sticker-shadow)");

            // Edge Background Pill
            const bgEdge = document.createElementNS(ns, "rect");
            bgEdge.setAttribute("x", "-15");
            bgEdge.setAttribute("y", "-15");
            bgEdge.setAttribute("width", "30");
            bgEdge.setAttribute("height", "30");
            bgEdge.setAttribute("rx", "8");
            bgEdge.setAttribute("fill", "#0b0f19");
            bgEdge.setAttribute("stroke", "#475569");
            bgEdge.setAttribute("stroke-width", "1.5");
            gEdge.appendChild(bgEdge);

            // Primary Facelet Sticker
            const st1 = document.createElementNS(ns, "rect");
            st1.setAttribute("x", "-11");
            st1.setAttribute("y", "-11");
            st1.setAttribute("width", "10");
            st1.setAttribute("height", "22");
            st1.setAttribute("rx", "3");
            st1.setAttribute("fill", cPrimary);
            gEdge.appendChild(st1);

            // Secondary Side Sticker
            const st2 = document.createElementNS(ns, "rect");
            st2.setAttribute("x", "1");
            st2.setAttribute("y", "-11");
            st2.setAttribute("width", "10");
            st2.setAttribute("height", "22");
            st2.setAttribute("rx", "3");
            st2.setAttribute("fill", cSide);
            gEdge.appendChild(st2);

            // Edge Label
            const lbl = document.createElementNS(ns, "text");
            lbl.setAttribute("x", "0");
            lbl.setAttribute("y", "-18");
            lbl.setAttribute("text-anchor", "middle");
            lbl.setAttribute("fill", "#cbd5e1");
            lbl.setAttribute("font-size", "9");
            lbl.setAttribute("font-family", "monospace");
            lbl.setAttribute("font-weight", "bold");
            lbl.textContent = edge.name;
            gEdge.appendChild(lbl);

            gRotating.appendChild(gEdge);
        });

        svg.appendChild(gRotating);

        // 3. CENTER ACTIVE FACE HUB (Static Stable Core)
        const gCenter = document.createElementNS(ns, "g");
        const centerColor = COLOR_PALETTE[cubeState[faceData.centerIdx]] || '#facc15';

        // Outer Glow Rim
        const centerRim = document.createElementNS(ns, "circle");
        centerRim.setAttribute("cx", "0");
        centerRim.setAttribute("cy", "0");
        centerRim.setAttribute("r", "28");
        centerRim.setAttribute("fill", "#05070c");
        centerRim.setAttribute("stroke", centerColor);
        centerRim.setAttribute("stroke-width", "2.5");
        centerRim.setAttribute("filter", "url(#orbit-glow)");
        gCenter.appendChild(centerRim);

        // Center Facelet Square
        const centerSq = document.createElementNS(ns, "rect");
        centerSq.setAttribute("x", "-11");
        centerSq.setAttribute("y", "-11");
        centerSq.setAttribute("width", "22");
        centerSq.setAttribute("height", "22");
        centerSq.setAttribute("rx", "5");
        centerSq.setAttribute("fill", centerColor);
        gCenter.appendChild(centerSq);

        // Center Move Pill Banner: e.g. "(U) ↻ +90°"
        const gBadge = document.createElementNS(ns, "g");
        gBadge.setAttribute("transform", "translate(0, 36)");

        const badgeRect = document.createElementNS(ns, "rect");
        badgeRect.setAttribute("x", "-48");
        badgeRect.setAttribute("y", "-11");
        badgeRect.setAttribute("width", "96");
        badgeRect.setAttribute("height", "22");
        badgeRect.setAttribute("rx", "11");
        badgeRect.setAttribute("fill", "#090d16");
        badgeRect.setAttribute("stroke", isCounter ? "#f43f5e" : "#38bdf8");
        badgeRect.setAttribute("stroke-width", "1.6");
        gBadge.appendChild(badgeRect);

        const badgeTxt = document.createElementNS(ns, "text");
        badgeTxt.setAttribute("x", "0");
        badgeTxt.setAttribute("y", "4");
        badgeTxt.setAttribute("text-anchor", "middle");
        badgeTxt.setAttribute("fill", "#ffffff");
        badgeTxt.setAttribute("font-size", "10");
        badgeTxt.setAttribute("font-family", "monospace");
        badgeTxt.setAttribute("font-weight", "bold");
        badgeTxt.textContent = `(${activeMove}) ${turnSymbol}`;
        gBadge.appendChild(badgeTxt);

        gCenter.appendChild(gBadge);
        svg.appendChild(gCenter);

        // 4. Update Permutation Cycle Info Bar
        const formulaEl = document.getElementById('cycle-formula-label');
        const typeEl = document.getElementById('cycle-type-label');
        const invEl = document.getElementById('cycle-invariants-label');
        if (formulaEl) {
            formulaEl.textContent = `Edges: (${faceData.cycleEdges}) | Corners: (${faceData.cycleCorners})`;
            formulaEl.title = `${faceData.name} - Move ${activeMove}`;
        }
        if (typeEl) {
            typeEl.textContent = `${baseFace}-Face Orbit:`;
        }
        if (invEl) {
            invEl.textContent = `${turnSymbol} Active`;
            invEl.className = isCounter 
                ? "text-rose-400 text-[10px] font-bold" 
                : "text-emerald-400 text-[10px] font-bold";
        }

        // 5. Update Active Face Chip Selector Highlights
        document.querySelectorAll('.orbit-face-chip').forEach(chip => {
            const f = chip.dataset.face;
            if (f === baseFace) {
                chip.classList.add('bg-slate-800', 'ring-1', 'ring-indigo-500/50', 'shadow-inner');
                chip.classList.remove('opacity-60');
            } else {
                chip.classList.remove('bg-slate-800', 'ring-1', 'ring-indigo-500/50', 'shadow-inner');
                chip.classList.add('opacity-60');
            }
        });
    }

    /**
     * Mode 2: Enhanced Cayley S54 Group Theory Matrix Graph
     */
    function renderCayleyMatrixGraph(svg, ns, baseFace, activeMove, turnSymbol) {
        const rings = [
            { cx: 0, cy: -20, r: 85, stroke: 'rgba(99, 102, 241, 0.4)' },
            { cx: -50, cy: 40, r: 85, stroke: 'rgba(56, 189, 248, 0.35)' },
            { cx: 50, cy: 40, r: 85, stroke: 'rgba(244, 63, 94, 0.35)' }
        ];

        rings.forEach(r => {
            const c = document.createElementNS(ns, "circle");
            c.setAttribute("cx", r.cx);
            c.setAttribute("cy", r.cy);
            c.setAttribute("r", r.r);
            c.setAttribute("fill", "none");
            c.setAttribute("stroke", r.stroke);
            c.setAttribute("stroke-width", "2");
            c.setAttribute("stroke-dasharray", "8, 6");
            c.setAttribute("class", "animate-spin-slow");
            svg.appendChild(c);
        });

        // 6 Face Clusters with Live Colors
        const facePositions = [
            { face: 'U', x: 0, y: -110, color: COLOR_PALETTE['U'] },
            { face: 'D', x: 0, y: 110, color: COLOR_PALETTE['D'] },
            { face: 'F', x: 0, y: 0, color: COLOR_PALETTE['F'] },
            { face: 'B', x: 0, y: -55, color: COLOR_PALETTE['B'] },
            { face: 'L', x: -95, y: 25, color: COLOR_PALETTE['L'] },
            { face: 'R', x: 95, y: 25, color: COLOR_PALETTE['R'] }
        ];

        facePositions.forEach(fp => {
            const g = document.createElementNS(ns, "g");
            g.setAttribute("transform", `translate(${fp.x}, ${fp.y})`);
            g.setAttribute("class", "cursor-pointer");

            const dot = document.createElementNS(ns, "circle");
            dot.setAttribute("cx", "0");
            dot.setAttribute("cy", "0");
            dot.setAttribute("r", fp.face === baseFace ? "18" : "12");
            dot.setAttribute("fill", fp.color);
            dot.setAttribute("stroke", fp.face === baseFace ? "#38bdf8" : "#1e293b");
            dot.setAttribute("stroke-width", "3");
            if (fp.face === baseFace) {
                dot.setAttribute("filter", "url(#orbit-glow)");
            }
            g.appendChild(dot);

            const txt = document.createElementNS(ns, "text");
            txt.setAttribute("x", "0");
            txt.setAttribute("y", "4");
            txt.setAttribute("text-anchor", "middle");
            txt.setAttribute("fill", fp.face === 'D' || fp.face === 'U' ? "#0f172a" : "#ffffff");
            txt.setAttribute("font-size", "11");
            txt.setAttribute("font-weight", "bold");
            txt.setAttribute("font-family", "monospace");
            txt.textContent = fp.face;
            g.appendChild(txt);

            svg.appendChild(g);
        });

        // Center Move Pill
        const badge = document.createElementNS(ns, "text");
        badge.setAttribute("x", "0");
        badge.setAttribute("y", "155");
        badge.setAttribute("text-anchor", "middle");
        badge.setAttribute("fill", "#38bdf8");
        badge.setAttribute("font-size", "12");
        badge.setAttribute("font-family", "monospace");
        badge.setAttribute("font-weight", "bold");
        badge.textContent = `Cayley Orbit: (${activeMove}) ${turnSymbol}`;
        svg.appendChild(badge);
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

            if (data.error) {
                alert('Solver warning: ' + data.error);
            } else if (data.solution) {
                currentMoves = data.solution.split(' ');
                currentStepIndex = 0;
                reconstructCubeStateUpToStep(0);
                updateVisualizerUI();
                playSolveFanfare();
                startPlayback();
                loadRecentSolves();
            } else {
                alert('Cube is already in the solved state - nothing to apply.');
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

