/**
 * GoChess 3D Smart Robotic Chess Board Engine
 * Inspired by Particula GoChess (https://particula-tech.com/pages/gochess)
 * Features:
 * - 3D WebGL Three.js Realistic Board & Procedural Geometric Pieces
 * - Patented Robotic Self-Movement Simulation (XR internal dual-motor glide)
 * - Multi-Zone RGB Smart LED Coaching (Hints, Legal Moves, Best Moves, In-Check Alerts)
 * - Web Audio API Synthetic Sound Engine (Physical click, servo glide, capture, check alarm)
 * - Minimax AI Engine (800 - 2600 ELO)
 * - Historic Masterpiece Auto-Demonstrations
 * - Clan Challenges, Group vs Group & Group vs Public Battles
 */

class GoChess3D {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`[GoChess3D] Container #${containerId} not found.`);
            return;
        }

        this.options = Object.assign({
            theme: 'obsidian', // 'obsidian', 'walnut', 'cyber'
            ledMode: 'all',    // 'all', 'hints', 'minimal', 'off'
            aiLevel: 2,
            gameId: null,
            interactive: true,
            soundEnabled: true,
            onMove: null,
            onCheck: null,
            onGameOver: null
        }, options);

        this.currentFen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
        this.selectedSquare = null;
        this.legalMoves = {};
        this.bestMove = null;
        this.checkSquare = null;
        this.isAnimating = false;
        this.autoPlayTimer = null;

        // Board Square Meshes & Pieces Dictionary: 'e4' -> { mesh, pieceType, color }
        this.boardSquares = {};
        this.piecesOnBoard = {};
        this.ledIndicators = {};

        // Sound Synthesizer
        this.initAudio();

        // 3D Scene Setup
        this.initThree();
        this.createBoard();
        this.setupEventListeners();
        this.loadFen(this.currentFen);
    }

    // =========================================================================
    // AUDIO SYNTHESIZER (Web Audio API)
    // =========================================================================
    initAudio() {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.audioCtx = new AudioContext();
        } catch (e) {
            console.warn('[GoChess3D] Web Audio API not supported.');
            this.audioCtx = null;
        }
    }

    playSound(type = 'move') {
        if (!this.options.soundEnabled || !this.audioCtx) return;
        if (this.audioCtx.state === 'suspended') {
            this.audioCtx.resume();
        }

        const now = this.audioCtx.currentTime;
        const osc = this.audioCtx.createOscillator();
        const gain = this.audioCtx.createGain();
        osc.connect(gain);
        gain.connect(this.audioCtx.destination);

        if (type === 'move') {
            // Tactile wooden snap
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(320, now);
            osc.frequency.exponentialRampToValueAtTime(80, now + 0.08);
            gain.gain.setValueAtTime(0.3, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.08);
            osc.start(now);
            osc.stop(now + 0.08);
        } else if (type === 'capture') {
            // Heavy kinetic impact
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(180, now);
            osc.frequency.exponentialRampToValueAtTime(40, now + 0.15);
            gain.gain.setValueAtTime(0.5, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
            osc.start(now);
            osc.stop(now + 0.15);
        } else if (type === 'servo') {
            // High-tech robotic stepper glide
            osc.type = 'sine';
            osc.frequency.setValueAtTime(440, now);
            osc.frequency.linearRampToValueAtTime(520, now + 0.25);
            gain.gain.setValueAtTime(0.06, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.28);
            osc.start(now);
            osc.stop(now + 0.28);
        } else if (type === 'check') {
            // Warning chime
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, now);
            osc.frequency.setValueAtTime(660, now + 0.1);
            gain.gain.setValueAtTime(0.3, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);
            osc.start(now);
            osc.stop(now + 0.35);
        } else if (type === 'victory') {
            // Harmonic fanfare
            [523.25, 659.25, 783.99, 1046.50].forEach((freq, i) => {
                const subOsc = this.audioCtx.createOscillator();
                const subGain = this.audioCtx.createGain();
                subOsc.connect(subGain);
                subGain.connect(this.audioCtx.destination);
                subOsc.frequency.setValueAtTime(freq, now + i * 0.12);
                subGain.gain.setValueAtTime(0.2, now + i * 0.12);
                subGain.gain.exponentialRampToValueAtTime(0.01, now + i * 0.12 + 0.3);
                subOsc.start(now + i * 0.12);
                subOsc.stop(now + i * 0.12 + 0.3);
            });
        }
    }

    // =========================================================================
    // THREE.JS SCENE SETUP
    // =========================================================================
    initThree() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x05070c);

        const width = this.container.clientWidth || 800;
        const height = this.container.clientHeight || 600;

        this.camera = new THREE.PerspectiveCamera(52, width / height, 0.1, 1000);
        this.camera.position.set(0, 20.5, 19);

        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        // Bright, correctly-gammaized output (r128 defaults to linear = too dark)
        this.renderer.outputEncoding = THREE.sRGBEncoding;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.05;

        // Clear container
        this.container.innerHTML = '';
        this.container.appendChild(this.renderer.domElement);

        // OrbitControls
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.maxPolarAngle = Math.PI / 2.05; // Don't flip under the table
        this.controls.minDistance = 8;
        this.controls.maxDistance = 35;
        this.controls.target.set(0, 0.2, 1.1);

        // Lighting
        this.setupLighting();

        // Raycasting for interactive piece picks
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();

        // Render loop
        this.animate = this.animate.bind(this);
        requestAnimationFrame(this.animate);

        // Handle resize
        window.addEventListener('resize', () => this.onResize());
    }

    setupLighting() {
        // Universal High-Luminance Studio Ambient
        this.ambientLight = new THREE.AmbientLight(0xffffff, 0.25);
        this.scene.add(this.ambientLight);

        // Sky / Ground Hemisphere Light for rich natural 3D depth
        this.hemiLight = new THREE.HemisphereLight(0xffffff, 0x475569, 0.16);
        this.scene.add(this.hemiLight);

        // Direct Overhead Floodlight directly over the board
        this.overheadLight = new THREE.DirectionalLight(0xffffff, 0.32);
        this.overheadLight.position.set(0, 35, 0);
        this.overheadLight.castShadow = true;
        this.overheadLight.shadow.mapSize.width = 2048;
        this.overheadLight.shadow.mapSize.height = 2048;
        this.overheadLight.shadow.bias = -0.0005;
        this.scene.add(this.overheadLight);

        // Key Directional Studio Light
        this.keyLight = new THREE.DirectionalLight(0xfffaed, 0.45);
        this.keyLight.position.set(16, 26, 18);
        this.keyLight.castShadow = true;
        this.scene.add(this.keyLight);

        // Cool Fill Light to illuminate shadow sides
        this.fillLight = new THREE.DirectionalLight(0xcffafe, 0.18);
        this.fillLight.position.set(-18, 20, -16);
        this.scene.add(this.fillLight);

        // 4 Corner Stadium Accent Lights for 360-degree piece silhouette illumination
        this.cornerLights = [];
        const corners = [
            [-10, 8, -10],
            [10, 8, -10],
            [-10, 8, 10],
            [10, 8, 10]
        ];
        corners.forEach(([x, y, z]) => {
            const pLight = new THREE.PointLight(0xf8fafc, 0.14, 35);
            pLight.position.set(x, y, z);
            this.scene.add(pLight);
            this.cornerLights.push(pLight);
        });

        // Soft Base Rim Light
        this.rimLight = new THREE.PointLight(0x06b6d4, 0.5, 25);
        this.rimLight.position.set(0, -1, 0);
        this.scene.add(this.rimLight);
    }

    setLightingIntensity(mode = 'ultra') {
        let mult = 1.0;
        if (mode === 'ultra') mult = 1.0;
        else if (mode === 'high') mult = 0.75;
        else if (mode === 'cinematic') mult = 0.5;

        if (this.ambientLight) this.ambientLight.intensity = 0.25 * mult;
        if (this.hemiLight) this.hemiLight.intensity = 0.16 * mult;
        if (this.overheadLight) this.overheadLight.intensity = 0.32 * mult;
        if (this.keyLight) this.keyLight.intensity = 0.45 * mult;
        if (this.fillLight) this.fillLight.intensity = 0.18 * mult;
        if (this.cornerLights) {
            this.cornerLights.forEach(cl => cl.intensity = 0.14 * mult);
        }
    }

    // =========================================================================
    // PROCEDURAL 3D SMART BOARD & RGB LED TILES
    // =========================================================================
    createBoard() {
        this.boardGroup = new THREE.Group();
        this.scene.add(this.boardGroup);

        const tileSize = 1.8;
        this.tileSize = tileSize;
        const boardWidth = tileSize * 8;

        // Base Plinth / Chassis (Ultra slim GoChess casing)
        const baseGeo = new THREE.BoxGeometry(boardWidth + 1.2, 0.7, boardWidth + 1.2);
        let baseMat;

        if (this.options.theme === 'walnut') {
            baseMat = new THREE.MeshStandardMaterial({ color: 0x3d2314, roughness: 0.4, metalness: 0.1 });
        } else if (this.options.theme === 'cyber') {
            baseMat = new THREE.MeshStandardMaterial({ color: 0x1b2438, roughness: 0.3, metalness: 0.5 });
        } else {
            // Obsidian Acrylic (brightened chassis edge)
            baseMat = new THREE.MeshStandardMaterial({ color: 0x2a3348, roughness: 0.25, metalness: 0.55 });
        }

        const baseMesh = new THREE.Mesh(baseGeo, baseMat);
        baseMesh.position.y = -0.35;
        baseMesh.receiveShadow = true;
        this.boardGroup.add(baseMesh);

        // Outer LED Ring Strip (Underglow)
        const stripGeo = new THREE.BoxGeometry(boardWidth + 1.35, 0.1, boardWidth + 1.35);
        const stripMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4, wireframe: false });
        const stripMesh = new THREE.Mesh(stripGeo, stripMat);
        stripMesh.position.y = -0.25;
        this.boardGroup.add(stripMesh);

        // 64 Chess Squares
        const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
        const ranks = ['1', '2', '3', '4', '5', '6', '7', '8'];

        for (let r = 0; r < 8; r++) {
            for (let f = 0; f < 8; f++) {
                const sqName = `${files[f]}${ranks[r]}`;
                const isLight = (f + r) % 2 !== 0;

                const x = (f - 3.5) * tileSize;
                const z = (3.5 - r) * tileSize; // White pieces on rank 1 (positive z)

                // Surface Tile
                const tileGeo = new THREE.BoxGeometry(tileSize * 0.97, 0.1, tileSize * 0.97);
                let tileMat;

                if (this.options.theme === 'walnut') {
                    tileMat = new THREE.MeshStandardMaterial({
                        color: isLight ? 0xfef3c7 : 0x78350f,
                        roughness: 0.35,
                        metalness: 0.05
                    });
                } else if (this.options.theme === 'cyber') {
                    tileMat = new THREE.MeshStandardMaterial({
                        color: isLight ? 0x0284c7 : 0x0f172a,
                        roughness: 0.25,
                        metalness: 0.6,
                        emissive: isLight ? 0x0369a1 : 0x000000,
                        emissiveIntensity: isLight ? 0.2 : 0
                    });
                } else {
                    // Obsidian: High contrast porcelain white vs rich graphite slate
                    tileMat = new THREE.MeshStandardMaterial({
                        color: isLight ? 0xaeb8cc : 0x2b3549,
                        roughness: 0.35,
                        metalness: isLight ? 0.05 : 0.3
                    });
                }

                const tileMesh = new THREE.Mesh(tileGeo, tileMat);
                tileMesh.position.set(x, 0.05, z);
                tileMesh.receiveShadow = true;
                tileMesh.userData = { square: sqName, isLight: isLight };
                this.boardGroup.add(tileMesh);
                this.boardSquares[sqName] = tileMesh;

                // GoChess RGB Smart LED Indicator on each square (Center circular glow diode)
                const ledGeo = new THREE.RingGeometry(0.22, 0.42, 24);
                ledGeo.rotateX(-Math.PI / 2);
                const ledMat = new THREE.MeshBasicMaterial({
                    color: 0x000000,
                    transparent: true,
                    opacity: 0.0,
                    side: THREE.DoubleSide
                });
                const ledMesh = new THREE.Mesh(ledGeo, ledMat);
                ledMesh.position.set(x, 0.11, z);
                this.boardGroup.add(ledMesh);
                this.ledIndicators[sqName] = ledMesh;
            }
        }

        // Add Visible Board Coordinates (A-H and 1-8) along the border
        this.addBoardCoordinates(tileSize, boardWidth);
    }

    addBoardCoordinates(tileSize, boardWidth) {
        const files = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
        const ranks = ['1', '2', '3', '4', '5', '6', '7', '8'];

        const createLabelMesh = (text) => {
            const canvas = document.createElement('canvas');
            canvas.width = 64;
            canvas.height = 64;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = 'rgba(0,0,0,0)';
            ctx.fillRect(0, 0, 64, 64);
            ctx.fillStyle = '#cbd5e1';
            ctx.font = 'bold 40px monospace';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(text, 32, 32);

            const tex = new THREE.CanvasTexture(canvas);
            const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, opacity: 0.85 });
            const geo = new THREE.PlaneGeometry(0.7, 0.7);
            geo.rotateX(-Math.PI / 2);
            return new THREE.Mesh(geo, mat);
        };

        // Files along bottom and top borders
        for (let f = 0; f < 8; f++) {
            const x = (f - 3.5) * tileSize;
            const bottomMesh = createLabelMesh(files[f]);
            bottomMesh.position.set(x, 0.08, (3.5 * tileSize) + 0.95);
            this.boardGroup.add(bottomMesh);

            const topMesh = createLabelMesh(files[f]);
            topMesh.position.set(x, 0.08, (-3.5 * tileSize) - 0.95);
            topMesh.rotation.y = Math.PI;
            this.boardGroup.add(topMesh);
        }

        // Ranks along left and right borders
        for (let r = 0; r < 8; r++) {
            const z = (3.5 - r) * tileSize;
            const leftMesh = createLabelMesh(ranks[r]);
            leftMesh.position.set((-3.5 * tileSize) - 0.95, 0.08, z);
            leftMesh.rotation.y = Math.PI / 2;
            this.boardGroup.add(leftMesh);

            const rightMesh = createLabelMesh(ranks[r]);
            rightMesh.position.set((3.5 * tileSize) + 0.95, 0.08, z);
            rightMesh.rotation.y = -Math.PI / 2;
            this.boardGroup.add(rightMesh);
        }
    }

    // =========================================================================
    // 3D PROCEDURAL CHESS PIECES (Statuesque Tournament Design & High Visibility)
    // =========================================================================
    createPieceMesh(pieceType, color) {
        const pieceGroup = new THREE.Group();
        const isWhite = (color === 'w' || color === 'white');

        // Material Presets - High Contrast, Specular Definition & Regal Accent Inlays
        let bodyMat, accentMat, haloRingMat, darkAccentMat;

        if (this.options.theme === 'cyber') {
            bodyMat = new THREE.MeshStandardMaterial({
                color: isWhite ? 0x38bdf8 : 0xf43f5e,
                roughness: 0.15,
                metalness: 0.65,
                emissive: isWhite ? 0x0284c7 : 0xe11d48,
                emissiveIntensity: 0.42
            });
            accentMat = new THREE.MeshStandardMaterial({
                color: isWhite ? 0xfacc15 : 0x38bdf8,
                metalness: 0.9,
                roughness: 0.1,
                emissive: isWhite ? 0x854d0e : 0x0369a1,
                emissiveIntensity: 0.48
            });
            haloRingMat = new THREE.MeshBasicMaterial({
                color: isWhite ? 0x38bdf8 : 0xf43f5e,
                transparent: true,
                opacity: 0.65
            });
            darkAccentMat = new THREE.MeshStandardMaterial({
                color: 0x050810,
                roughness: 0.5,
                metalness: 0.3
            });
        } else if (this.options.theme === 'walnut') {
            bodyMat = new THREE.MeshStandardMaterial({
                color: isWhite ? 0xfff8eb : 0x3a1e12,
                roughness: 0.28,
                metalness: 0.08,
                emissive: isWhite ? 0x451a03 : 0x120602,
                emissiveIntensity: 0.05
            });
            accentMat = new THREE.MeshStandardMaterial({
                color: isWhite ? 0xd97706 : 0xb45309,
                metalness: 0.85,
                roughness: 0.2
            });
            haloRingMat = new THREE.MeshBasicMaterial({
                color: isWhite ? 0xf59e0b : 0xb45309,
                transparent: true,
                opacity: 0.35
            });
            darkAccentMat = new THREE.MeshStandardMaterial({
                color: 0x1c0d06,
                roughness: 0.6
            });
        } else {
            // Obsidian Luxury (Default: Pearl Alabaster vs Jet Metallic Onyx with Gold/Cyan Trim)
            bodyMat = new THREE.MeshStandardMaterial({
                color: isWhite ? 0xfcfbf8 : 0x181c24,
                roughness: isWhite ? 0.22 : 0.30,
                metalness: isWhite ? 0.15 : 0.38,
                emissive: isWhite ? 0x1e293b : 0x0ea5e9,
                emissiveIntensity: isWhite ? 0.03 : 0.08
            });
            accentMat = new THREE.MeshStandardMaterial({
                color: isWhite ? 0xf59e0b : 0x38bdf8,
                metalness: 0.95,
                roughness: 0.12,
                emissive: isWhite ? 0x78350f : 0x0284c7,
                emissiveIntensity: isWhite ? 0.22 : 0.32
            });
            haloRingMat = new THREE.MeshBasicMaterial({
                color: isWhite ? 0xfbbf24 : 0x38bdf8,
                transparent: true,
                opacity: isWhite ? 0.50 : 0.60
            });
            darkAccentMat = new THREE.MeshStandardMaterial({
                color: 0x090b0e,
                roughness: 0.5,
                metalness: 0.2
            });
        }

        // 1. Subtle Under-Base Luminous Halo Ring (Projects glowing footprint onto board square)
        const haloGeo = new THREE.RingGeometry(0.50, 0.62, 28);
        const haloMesh = new THREE.Mesh(haloGeo, haloRingMat);
        haloMesh.rotation.x = -Math.PI / 2;
        haloMesh.position.y = 0.015;
        pieceGroup.add(haloMesh);

        // 2. Multi-Tier Staunton Podium Base
        // Tier 1: Plinth Foot
        const footGeo = new THREE.CylinderGeometry(0.56, 0.64, 0.14, 28);
        const footMesh = new THREE.Mesh(footGeo, bodyMat);
        footMesh.position.y = 0.07;
        footMesh.castShadow = true;
        pieceGroup.add(footMesh);

        // Tier 2: Beveled Collar
        const footRingGeo = new THREE.CylinderGeometry(0.50, 0.56, 0.09, 28);
        const footRingMesh = new THREE.Mesh(footRingGeo, bodyMat);
        footRingMesh.position.y = 0.18;
        footRingMesh.castShadow = true;
        pieceGroup.add(footRingMesh);

        // Tier 3: Inlaid Metallic Filigree Accent Ring
        const goldBandGeo = new THREE.CylinderGeometry(0.52, 0.52, 0.05, 28);
        const goldBandMesh = new THREE.Mesh(goldBandGeo, accentMat);
        goldBandMesh.position.y = 0.24;
        pieceGroup.add(goldBandMesh);

        // Tier 4: Waist Transition
        const waistGeo = new THREE.CylinderGeometry(0.36, 0.48, 0.08, 24);
        const waistMesh = new THREE.Mesh(waistGeo, bodyMat);
        waistMesh.position.y = 0.30;
        waistMesh.castShadow = true;
        pieceGroup.add(waistMesh);

        const typeLower = pieceType.toLowerCase();

        if (typeLower === 'p') {
            // =========================================================
            // PAWN: Sleek tapered stem, bead collar tray, polished spherical head
            // =========================================================
            const stem = new THREE.CylinderGeometry(0.22, 0.36, 0.46, 24);
            const stemMesh = new THREE.Mesh(stem, bodyMat);
            stemMesh.position.y = 0.57;
            stemMesh.castShadow = true;
            pieceGroup.add(stemMesh);

            // Torus Bead Collar
            const bead = new THREE.CylinderGeometry(0.30, 0.22, 0.08, 24);
            const beadMesh = new THREE.Mesh(bead, accentMat);
            beadMesh.position.y = 0.83;
            pieceGroup.add(beadMesh);

            // Spherical Head (Smooth & Distinct)
            const head = new THREE.SphereGeometry(0.31, 24, 24);
            const headMesh = new THREE.Mesh(head, bodyMat);
            headMesh.position.y = 1.13;
            headMesh.castShadow = true;
            pieceGroup.add(headMesh);

            // Peak Pearl Stud
            const stud = new THREE.SphereGeometry(0.06, 12, 12);
            const studMesh = new THREE.Mesh(stud, accentMat);
            studMesh.position.y = 1.44;
            pieceGroup.add(studMesh);
        } else if (typeLower === 'r') {
            // =========================================================
            // ROOK: Fortified castle tower, capital cornice, recessed roof, 4 crenellated battlements
            // =========================================================
            const tower = new THREE.CylinderGeometry(0.40, 0.46, 0.76, 24);
            const towerMesh = new THREE.Mesh(tower, bodyMat);
            towerMesh.position.y = 0.72;
            towerMesh.castShadow = true;
            pieceGroup.add(towerMesh);

            // Mid-Tower Architectural Band
            const midRing = new THREE.CylinderGeometry(0.42, 0.42, 0.05, 24);
            const midRingMesh = new THREE.Mesh(midRing, accentMat);
            midRingMesh.position.y = 0.65;
            pieceGroup.add(midRingMesh);

            // Flared Fortress Cornice / Capital
            const cornice = new THREE.CylinderGeometry(0.56, 0.40, 0.18, 24);
            const corniceMesh = new THREE.Mesh(cornice, bodyMat);
            corniceMesh.position.y = 1.18;
            corniceMesh.castShadow = true;
            pieceGroup.add(corniceMesh);

            // Accent Rim below battlements
            const rimRing = new THREE.CylinderGeometry(0.57, 0.57, 0.04, 24);
            const rimRingMesh = new THREE.Mesh(rimRing, accentMat);
            rimRingMesh.position.y = 1.28;
            pieceGroup.add(rimRingMesh);

            // Recessed Dark Inner Well / Roof
            const innerWell = new THREE.CylinderGeometry(0.40, 0.40, 0.08, 20);
            const innerWellMesh = new THREE.Mesh(innerWell, darkAccentMat);
            innerWellMesh.position.y = 1.28;
            pieceGroup.add(innerWellMesh);

            // 4 Crenellated Turret Merlons (Castle Battlements)
            const merlonOffsets = [
                [0.36, 0],
                [-0.36, 0],
                [0, 0.36],
                [0, -0.36]
            ];
            merlonOffsets.forEach(([mx, mz]) => {
                const merlonGeo = new THREE.BoxGeometry(0.18, 0.18, 0.18);
                const merlonMesh = new THREE.Mesh(merlonGeo, bodyMat);
                merlonMesh.position.set(mx, 1.38, mz);
                merlonMesh.castShadow = true;
                pieceGroup.add(merlonMesh);

                // Top Accent Tip on each merlon
                const tipGeo = new THREE.BoxGeometry(0.14, 0.03, 0.14);
                const tipMesh = new THREE.Mesh(tipGeo, accentMat);
                tipMesh.position.set(mx, 1.48, mz);
                pieceGroup.add(tipMesh);
            });
        } else if (typeLower === 'n') {
            // =========================================================
            // KNIGHT: True Sculpted Equestrian Horse Design with arched neck, ears, snout, mane, and eyes
            // =========================================================
            const chest = new THREE.CylinderGeometry(0.36, 0.48, 0.36, 20);
            const chestMesh = new THREE.Mesh(chest, bodyMat);
            chestMesh.position.y = 0.50;
            chestMesh.castShadow = true;
            pieceGroup.add(chestMesh);

            // Knight Horse Group (will be rotated to face opponent)
            const horseGroup = new THREE.Group();

            // Lower Arched Neck
            const neckLowerGeo = new THREE.BoxGeometry(0.32, 0.48, 0.42);
            const neckLowerMesh = new THREE.Mesh(neckLowerGeo, bodyMat);
            neckLowerMesh.position.set(0, 0.76, 0.04);
            neckLowerMesh.rotation.x = -0.22;
            neckLowerMesh.castShadow = true;
            horseGroup.add(neckLowerMesh);

            // Upper Head & Jaw
            const jawGeo = new THREE.BoxGeometry(0.28, 0.40, 0.38);
            const jawMesh = new THREE.Mesh(jawGeo, bodyMat);
            jawMesh.position.set(0, 1.08, 0.12);
            jawMesh.rotation.x = -0.35;
            jawMesh.castShadow = true;
            horseGroup.add(jawMesh);

            // Muzzle / Snout (Tilted forward and down)
            const snoutGeo = new THREE.BoxGeometry(0.24, 0.26, 0.42);
            const snoutMesh = new THREE.Mesh(snoutGeo, bodyMat);
            snoutMesh.position.set(0, 1.02, 0.36);
            snoutMesh.rotation.x = 0.32;
            snoutMesh.castShadow = true;
            horseGroup.add(snoutMesh);

            // Nose Tip & Mouth cleft
            const noseTipGeo = new THREE.BoxGeometry(0.20, 0.14, 0.12);
            const noseTipMesh = new THREE.Mesh(noseTipGeo, accentMat);
            noseTipMesh.position.set(0, 0.94, 0.54);
            horseGroup.add(noseTipMesh);

            // Mane along back of neck (3 stepped ridges)
            const mane1 = new THREE.BoxGeometry(0.12, 0.22, 0.22);
            const mane1Mesh = new THREE.Mesh(mane1, accentMat);
            mane1Mesh.position.set(0, 1.15, -0.14);
            mane1Mesh.rotation.x = 0.25;
            horseGroup.add(mane1Mesh);

            const mane2 = new THREE.BoxGeometry(0.12, 0.22, 0.22);
            const mane2Mesh = new THREE.Mesh(mane2, accentMat);
            mane2Mesh.position.set(0, 0.90, -0.18);
            mane2Mesh.rotation.x = 0.15;
            horseGroup.add(mane2Mesh);

            const mane3 = new THREE.BoxGeometry(0.12, 0.20, 0.18);
            const mane3Mesh = new THREE.Mesh(mane3, accentMat);
            mane3Mesh.position.set(0, 0.68, -0.20);
            horseGroup.add(mane3Mesh);

            // Alert Pointed Ears (Left & Right)
            const earL = new THREE.ConeGeometry(0.065, 0.24, 8);
            earL.rotateX(-0.35);
            earL.rotateZ(-0.25);
            const earLMesh = new THREE.Mesh(earL, bodyMat);
            earLMesh.position.set(0.10, 1.34, -0.04);
            horseGroup.add(earLMesh);

            const earR = new THREE.ConeGeometry(0.065, 0.24, 8);
            earR.rotateX(-0.35);
            earR.rotateZ(0.25);
            const earRMesh = new THREE.Mesh(earR, bodyMat);
            earRMesh.position.set(-0.10, 1.34, -0.04);
            horseGroup.add(earRMesh);

            // Glowing Eyes (Left & Right)
            const eyeGeo = new THREE.SphereGeometry(0.045, 8, 8);
            const eyeLMesh = new THREE.Mesh(eyeGeo, accentMat);
            eyeLMesh.position.set(0.14, 1.14, 0.22);
            horseGroup.add(eyeLMesh);

            const eyeRMesh = new THREE.Mesh(eyeGeo, accentMat);
            eyeRMesh.position.set(-0.14, 1.14, 0.22);
            horseGroup.add(eyeRMesh);

            // Rotate horseGroup to face opponent:
            // White faces -Z (towards Black rank 8), Black faces +Z (towards White rank 1)
            horseGroup.rotation.y = isWhite ? Math.PI : 0;
            pieceGroup.add(horseGroup);
        } else if (typeLower === 'b') {
            // =========================================================
            // BISHOP: Slender neoclassical stem, tray gallery, iconic miter with diagonal slash, finial orb
            // =========================================================
            const stem = new THREE.CylinderGeometry(0.24, 0.38, 0.78, 24);
            const stemMesh = new THREE.Mesh(stem, bodyMat);
            stemMesh.position.y = 0.72;
            stemMesh.castShadow = true;
            pieceGroup.add(stemMesh);

            // Mid Waist Accent Torus
            const waistBead = new THREE.CylinderGeometry(0.30, 0.30, 0.05, 24);
            const waistBeadMesh = new THREE.Mesh(waistBead, accentMat);
            waistBeadMesh.position.y = 0.70;
            pieceGroup.add(waistBeadMesh);

            // Broad Mitre Tray Gallery
            const gallery = new THREE.CylinderGeometry(0.44, 0.26, 0.14, 24);
            const galleryMesh = new THREE.Mesh(gallery, bodyMat);
            galleryMesh.position.y = 1.16;
            galleryMesh.castShadow = true;
            pieceGroup.add(galleryMesh);

            const galleryTrim = new THREE.CylinderGeometry(0.45, 0.45, 0.04, 24);
            const galleryTrimMesh = new THREE.Mesh(galleryTrim, accentMat);
            galleryTrimMesh.position.y = 1.24;
            pieceGroup.add(galleryTrimMesh);

            // Ovoid Miter Head
            const miter = new THREE.SphereGeometry(0.33, 24, 24);
            miter.scale(1.0, 1.45, 0.95);
            const miterMesh = new THREE.Mesh(miter, bodyMat);
            miterMesh.position.y = 1.54;
            miterMesh.castShadow = true;
            pieceGroup.add(miterMesh);

            // Mitre Point Tip
            const miterTip = new THREE.ConeGeometry(0.24, 0.30, 20);
            const miterTipMesh = new THREE.Mesh(miterTip, bodyMat);
            miterTipMesh.position.y = 1.84;
            pieceGroup.add(miterTipMesh);

            // Iconic Bishop Cleft / Diagonal Cross Slash
            const slash = new THREE.BoxGeometry(0.10, 0.38, 0.40);
            slash.rotateZ(0.55);
            const slashMesh = new THREE.Mesh(slash, accentMat);
            slashMesh.position.set(0.12, 1.58, 0);
            pieceGroup.add(slashMesh);

            // Peak Spherical Finial Jewel
            const finial = new THREE.SphereGeometry(0.11, 16, 16);
            const finialMesh = new THREE.Mesh(finial, accentMat);
            finialMesh.position.y = 2.04;
            pieceGroup.add(finialMesh);
        } else if (typeLower === 'q') {
            // =========================================================
            // QUEEN: Hourglass statuesque pedestal, flared coronet with 8-point radial pearl jewels, sovereign orb
            // =========================================================
            const stem = new THREE.CylinderGeometry(0.28, 0.42, 0.95, 24);
            const stemMesh = new THREE.Mesh(stem, bodyMat);
            stemMesh.position.y = 0.80;
            stemMesh.castShadow = true;
            pieceGroup.add(stemMesh);

            // Waist Accent Torus Ring
            const waistBead = new THREE.CylinderGeometry(0.34, 0.34, 0.05, 24);
            const waistBeadMesh = new THREE.Mesh(waistBead, accentMat);
            waistBeadMesh.position.y = 0.78;
            pieceGroup.add(waistBeadMesh);

            // Upper Flared Collar Tray
            const tray = new THREE.CylinderGeometry(0.48, 0.30, 0.16, 24);
            const trayMesh = new THREE.Mesh(tray, bodyMat);
            trayMesh.position.y = 1.32;
            trayMesh.castShadow = true;
            pieceGroup.add(trayMesh);

            const trayRing = new THREE.CylinderGeometry(0.50, 0.50, 0.04, 24);
            const trayRingMesh = new THREE.Mesh(trayRing, accentMat);
            trayRingMesh.position.y = 1.41;
            pieceGroup.add(trayRingMesh);

            // Flared Coronet Bowl
            const crown = new THREE.CylinderGeometry(0.56, 0.38, 0.32, 24);
            const crownMesh = new THREE.Mesh(crown, bodyMat);
            crownMesh.position.y = 1.58;
            crownMesh.castShadow = true;
            pieceGroup.add(crownMesh);

            // Inner Velvet Dome
            const dome = new THREE.SphereGeometry(0.32, 20, 20);
            const domeMesh = new THREE.Mesh(dome, darkAccentMat);
            domeMesh.position.y = 1.62;
            pieceGroup.add(domeMesh);

            // 8 Radial Crown Points with Glowing Jewels / Pearls
            const pearlRadius = 0.53;
            for (let i = 0; i < 8; i++) {
                const angle = (i / 8) * Math.PI * 2;
                const px = Math.cos(angle) * pearlRadius;
                const pz = Math.sin(angle) * pearlRadius;

                // Point Cone
                const pointGeo = new THREE.ConeGeometry(0.06, 0.16, 8);
                const pointMesh = new THREE.Mesh(pointGeo, bodyMat);
                pointMesh.position.set(px, 1.76, pz);
                pieceGroup.add(pointMesh);

                // Top Jewel Pearl
                const pearlGeo = new THREE.SphereGeometry(0.065, 12, 12);
                const pearlMesh = new THREE.Mesh(pearlGeo, accentMat);
                pearlMesh.position.set(px, 1.84, pz);
                pieceGroup.add(pearlMesh);
            }

            // Central Sovereign Orb Finial
            const orb = new THREE.SphereGeometry(0.16, 18, 18);
            const orbMesh = new THREE.Mesh(orb, accentMat);
            orbMesh.position.y = 1.95;
            pieceGroup.add(orbMesh);
        } else if (typeLower === 'k') {
            // =========================================================
            // KING: Commanding stature (tallest), imperial column, regal ermine collar, vaulted dome, 3D Maltese Cross
            // =========================================================
            const stem = new THREE.CylinderGeometry(0.32, 0.46, 1.05, 24);
            const stemMesh = new THREE.Mesh(stem, bodyMat);
            stemMesh.position.y = 0.86;
            stemMesh.castShadow = true;
            pieceGroup.add(stemMesh);

            // Dual Gold Waist Bands
            const band1 = new THREE.CylinderGeometry(0.38, 0.38, 0.05, 24);
            const band1Mesh = new THREE.Mesh(band1, accentMat);
            band1Mesh.position.y = 0.72;
            pieceGroup.add(band1Mesh);

            const band2 = new THREE.CylinderGeometry(0.35, 0.35, 0.05, 24);
            const band2Mesh = new THREE.Mesh(band2, accentMat);
            band2Mesh.position.y = 0.98;
            pieceGroup.add(band2Mesh);

            // Royal Imperial Ermine Collar
            const collar = new THREE.CylinderGeometry(0.56, 0.34, 0.18, 24);
            const collarMesh = new THREE.Mesh(collar, bodyMat);
            collarMesh.position.y = 1.44;
            collarMesh.castShadow = true;
            pieceGroup.add(collarMesh);

            const collarTrim = new THREE.CylinderGeometry(0.58, 0.58, 0.04, 24);
            const collarTrimMesh = new THREE.Mesh(collarTrim, accentMat);
            collarTrimMesh.position.y = 1.54;
            pieceGroup.add(collarTrimMesh);

            // Imperial Vaulted Crown Dome
            const dome = new THREE.SphereGeometry(0.48, 24, 24);
            dome.scale(1.0, 0.65, 1.0);
            const domeMesh = new THREE.Mesh(dome, bodyMat);
            domeMesh.position.y = 1.72;
            domeMesh.castShadow = true;
            pieceGroup.add(domeMesh);

            // Diadem Filigree Rim
            const diadem = new THREE.CylinderGeometry(0.50, 0.50, 0.08, 24);
            const diademMesh = new THREE.Mesh(diadem, accentMat);
            diademMesh.position.y = 1.62;
            pieceGroup.add(diademMesh);

            // Cross Pedestal Collar
            const crossBase = new THREE.CylinderGeometry(0.16, 0.12, 0.10, 16);
            const crossBaseMesh = new THREE.Mesh(crossBase, accentMat);
            crossBaseMesh.position.y = 1.94;
            pieceGroup.add(crossBaseMesh);

            // 3D Sculpted Maltese / Latin Cross Finial
            const vBar = new THREE.BoxGeometry(0.12, 0.44, 0.12);
            const hBar = new THREE.BoxGeometry(0.36, 0.12, 0.12);
            const vMesh = new THREE.Mesh(vBar, accentMat);
            const hMesh = new THREE.Mesh(hBar, accentMat);
            vMesh.position.y = 2.20;
            hMesh.position.y = 2.25;
            vMesh.castShadow = true;
            hMesh.castShadow = true;
            pieceGroup.add(vMesh);
            pieceGroup.add(hMesh);

            // Center Imperial Diamond/Ruby Cabochon at Cross Intersection
            const gem = new THREE.SphereGeometry(0.08, 12, 12);
            const gemMesh = new THREE.Mesh(gem, bodyMat);
            gemMesh.position.set(0, 2.25, 0.06);
            pieceGroup.add(gemMesh);

            const gemBack = new THREE.SphereGeometry(0.08, 12, 12);
            const gemBackMesh = new THREE.Mesh(gemBack, bodyMat);
            gemBackMesh.position.set(0, 2.25, -0.06);
            pieceGroup.add(gemBackMesh);
        }

        pieceGroup.userData = { pieceType: typeLower, color: isWhite ? 'w' : 'b' };
        return pieceGroup;
    }

    // =========================================================================
    // FEN BOARD PARSING & SPAWNING
    // =========================================================================
    loadFen(fen) {
        this.currentFen = fen;
        this.clearBoardPieces();

        const parts = fen.split(' ');
        const rows = parts[0].split('/');
        const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];

        for (let r = 0; r < 8; r++) {
            const rankNum = 8 - r;
            let fileIdx = 0;
            const rowStr = rows[r];

            for (let char of rowStr) {
                if (!isNaN(char)) {
                    fileIdx += parseInt(char, 10);
                } else {
                    const sqName = `${files[fileIdx]}${rankNum}`;
                    const color = (char === char.toUpperCase()) ? 'w' : 'b';
                    const pieceMesh = this.createPieceMesh(char, color);

                    const targetSq = this.boardSquares[sqName];
                    if (targetSq) {
                        pieceMesh.position.set(targetSq.position.x, 0.1, targetSq.position.z);
                        pieceMesh.userData.square = sqName;
                        this.boardGroup.add(pieceMesh);
                        this.piecesOnBoard[sqName] = pieceMesh;
                    }
                    fileIdx++;
                }
            }
        }

        this.clearAllLeds();
        if (this.checkSquare) {
            this.setSquareLed(this.checkSquare, 'check');
        }
    }

    clearBoardPieces() {
        for (let sq in this.piecesOnBoard) {
            const mesh = this.piecesOnBoard[sq];
            if (mesh) {
                this.boardGroup.remove(mesh);
            }
        }
        this.piecesOnBoard = {};
    }

    // =========================================================================
    // GOCHESS ROBOTIC SELF-MOVEMENT MECHANISM (XR Glide Animation)
    // =========================================================================
    roboticMovePiece(fromSq, toSq, onComplete = null) {
        const pieceMesh = this.piecesOnBoard[fromSq];
        if (!pieceMesh) {
            if (onComplete) onComplete();
            return;
        }

        this.isAnimating = true;
        this.playSound('servo');

        const targetSq = this.boardSquares[toSq];
        const targetPos = targetSq.position;

        const capturedPiece = this.piecesOnBoard[toSq];

        const startX = pieceMesh.position.x;
        const startZ = pieceMesh.position.z;
        const endX = targetPos.x;
        const endZ = targetPos.z;

        const duration = 600; // ms
        const startTime = performance.now();

        // Illuminate trajectory in GoChess style
        this.setSquareLed(fromSq, 'selected');
        this.setSquareLed(toSq, 'best');

        const step = (now) => {
            const elapsed = now - startTime;
            const t = Math.min(1.0, elapsed / duration);

            // Smooth cubic easeInOut
            const ease = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

            pieceMesh.position.x = startX + (endX - startX) * ease;
            pieceMesh.position.z = startZ + (endZ - startZ) * ease;
            // Slight levitation off board simulating magnetic lift
            pieceMesh.position.y = 0.1 + Math.sin(t * Math.PI) * 0.15;

            if (t < 1.0) {
                requestAnimationFrame(step);
            } else {
                pieceMesh.position.x = endX;
                pieceMesh.position.z = endZ;
                pieceMesh.position.y = 0.1;
                pieceMesh.userData.square = toSq;

                if (capturedPiece && capturedPiece !== pieceMesh) {
                    this.boardGroup.remove(capturedPiece);
                    this.playSound('capture');
                } else {
                    this.playSound('move');
                }

                delete this.piecesOnBoard[fromSq];
                this.piecesOnBoard[toSq] = pieceMesh;

                this.isAnimating = false;
                this.clearAllLeds();

                if (onComplete) onComplete();
            }
        };

        requestAnimationFrame(step);
    }

    // =========================================================================
    // MULTI-ZONE RGB LED COACHING
    // =========================================================================
    setSquareLed(square, mode = 'legal') {
        const led = this.ledIndicators[square];
        if (!led || this.options.ledMode === 'off') return;

        let color = 0x00ffff; // Cyan default
        let opacity = 0.85;

        if (mode === 'selected') {
            color = 0xf59e0b; // Solar Amber
            opacity = 0.95;
        } else if (mode === 'legal') {
            color = 0x06b6d4; // Cyan Neon
            opacity = 0.75;
        } else if (mode === 'best') {
            color = 0xfacc15; // Golden Pulse (Grandmaster Best Move)
            opacity = 1.0;
        } else if (mode === 'check') {
            color = 0xef4444; // Crimson Danger Alarm
            opacity = 0.95;
        }

        led.material.color.setHex(color);
        led.material.opacity = opacity;
    }

    clearSquareLed(square) {
        const led = this.ledIndicators[square];
        if (led) {
            led.material.opacity = 0.0;
        }
    }

    clearAllLeds() {
        for (let sq in this.ledIndicators) {
            this.clearSquareLed(sq);
        }
    }

    highlightLegalMoves(fromSquare, targets = []) {
        this.clearAllLeds();
        this.setSquareLed(fromSquare, 'selected');
        for (let target of targets) {
            this.setSquareLed(target, 'legal');
        }
        if (this.bestMove && this.bestMove.from === fromSquare) {
            this.setSquareLed(this.bestMove.to, 'best');
        }
    }

    // =========================================================================
    // INTERACTIVE EVENTS (Click-to-Move & Pick)
    // =========================================================================
    setupEventListeners() {
        this.container.addEventListener('click', (e) => this.onClick(e));
    }

    onClick(event) {
        if (!this.options.interactive || this.isAnimating) return;

        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);

        // Raycast against squares
        const squareMeshes = Object.values(this.boardSquares);
        const intersects = this.raycaster.intersectObjects(squareMeshes);

        if (intersects.length > 0) {
            const hitSquare = intersects[0].object.userData.square;
            this.handleSquareClick(hitSquare);
        }
    }

    handleSquareClick(square) {
        const pieceOnSquare = this.piecesOnBoard[square];

        // 1. If clicking our own piece to select
        if (pieceOnSquare && pieceOnSquare.userData.color === 'w') {
            this.selectedSquare = square;
            const legalTargets = this.legalMoves[square] || [];
            this.highlightLegalMoves(square, legalTargets);
            return;
        }

        // 2. If a piece is already selected, try to move to clicked target
        if (this.selectedSquare) {
            const validTargets = this.legalMoves[this.selectedSquare] || [];
            if (validTargets.includes(square)) {
                const from = this.selectedSquare;
                const to = square;
                this.selectedSquare = null;
                this.clearAllLeds();

                if (this.options.onMove) {
                    this.options.onMove(from, to);
                }
            } else {
                // Clicked an invalid square -> deselect
                this.selectedSquare = null;
                this.clearAllLeds();
            }
        }
    }

    // =========================================================================
    // THEMES & CAMERA VIEWS
    // =========================================================================
    setTheme(themeName) {
        this.options.theme = themeName;
        this.scene.remove(this.boardGroup);
        this.boardSquares = {};
        this.ledIndicators = {};
        this.createBoard();
        this.loadFen(this.currentFen);
    }

    setCameraView(view = 'white') {
        if (view === 'white') {
            this.camera.position.set(0, 20.5, 19);
        } else if (view === 'black') {
            this.camera.position.set(0, 20.5, -19);
        } else if (view === 'top') {
            this.camera.position.set(0, 27, 0.1);
        }
        this.controls.target.set(0, 0.2, 1.1);
        this.controls.update();
    }

    onResize() {
        if (!this.container) return;
        const width = this.container.clientWidth || 800;
        const height = this.container.clientHeight || 600;
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    animate() {
        requestAnimationFrame(this.animate);
        if (this.controls) this.controls.update();
        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
    }

    destroy() {
        if (this.autoPlayTimer) clearInterval(this.autoPlayTimer);
        if (this.renderer && this.renderer.domElement) {
            this.container.removeChild(this.renderer.domElement);
        }
    }
}

window.GoChess3D = GoChess3D;
