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

        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        this.camera.position.set(0, 18, 18);

        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

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
        this.controls.target.set(0, 0.5, 0);

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
        const ambient = new THREE.AmbientLight(0xffffff, 0.7);
        this.scene.add(ambient);

        const keyLight = new THREE.DirectionalLight(0xfff5e6, 1.2);
        keyLight.position.set(10, 20, 15);
        keyLight.castShadow = true;
        keyLight.shadow.mapSize.width = 2048;
        keyLight.shadow.mapSize.height = 2048;
        keyLight.shadow.bias = -0.001;
        this.scene.add(keyLight);

        const fillLight = new THREE.DirectionalLight(0x88bbff, 0.6);
        fillLight.position.set(-15, 12, -10);
        this.scene.add(fillLight);

        // Rim Light from bottom
        const rimLight = new THREE.PointLight(0x6366f1, 0.8, 30);
        rimLight.position.set(0, -2, 0);
        this.scene.add(rimLight);
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
            baseMat = new THREE.MeshStandardMaterial({ color: 0x090d16, roughness: 0.2, metalness: 0.8 });
        } else {
            // Obsidian Acrylic
            baseMat = new THREE.MeshStandardMaterial({ color: 0x0a0c10, roughness: 0.1, metalness: 0.9 });
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
                        color: isLight ? 0xf0d9b5 : 0xb58863,
                        roughness: 0.5,
                        metalness: 0.05
                    });
                } else if (this.options.theme === 'cyber') {
                    tileMat = new THREE.MeshStandardMaterial({
                        color: isLight ? 0x1e293b : 0x0f172a,
                        roughness: 0.2,
                        metalness: 0.7
                    });
                } else {
                    // Obsidian
                    tileMat = new THREE.MeshStandardMaterial({
                        color: isLight ? 0x222734 : 0x0d0f15,
                        roughness: 0.2,
                        metalness: 0.6
                    });
                }

                const tileMesh = new THREE.Mesh(tileGeo, tileMat);
                tileMesh.position.set(x, 0.05, z);
                tileMesh.receiveShadow = true;
                tileMesh.userData = { square: sqName, isLight: isLight };
                this.boardGroup.add(tileMesh);
                this.boardSquares[sqName] = tileMesh;

                // GoChess RGB Smart LED Indicator on each square (Center circular glow diode)
                const ledGeo = new THREE.RingGeometry(0.18, 0.35, 24);
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
    }

    // =========================================================================
    // 3D PROCEDURAL CHESS PIECES (Statuesque Tournament Design)
    // =========================================================================
    createPieceMesh(pieceType, color) {
        const pieceGroup = new THREE.Group();
        const isWhite = (color === 'w' || color === 'white');

        // Material Presets
        let mat;
        if (this.options.theme === 'cyber') {
            mat = new THREE.MeshStandardMaterial({
                color: isWhite ? 0x38bdf8 : 0xf43f5e,
                roughness: 0.2,
                metalness: 0.8,
                emissive: isWhite ? 0x075985 : 0x881337,
                emissiveIntensity: 0.2
            });
        } else if (this.options.theme === 'walnut') {
            mat = new THREE.MeshStandardMaterial({
                color: isWhite ? 0xfff8ee : 0x2e180d,
                roughness: 0.35,
                metalness: 0.05
            });
        } else {
            // Obsidian Luxury Acrylic & Brushed Platinum
            mat = new THREE.MeshStandardMaterial({
                color: isWhite ? 0xf8fafc : 0x1e2029,
                roughness: 0.15,
                metalness: 0.85
            });
        }

        // Shared Base Pedestal
        const baseGeo = new THREE.CylinderGeometry(0.5, 0.6, 0.25, 24);
        const baseMesh = new THREE.Mesh(baseGeo, mat);
        baseMesh.castShadow = true;
        pieceGroup.add(baseMesh);

        const typeLower = pieceType.toLowerCase();

        if (typeLower === 'p') {
            // PAWN
            const stem = new THREE.CylinderGeometry(0.25, 0.38, 0.7, 20);
            const stemMesh = new THREE.Mesh(stem, mat);
            stemMesh.position.y = 0.45;
            stemMesh.castShadow = true;
            pieceGroup.add(stemMesh);

            const head = new THREE.SphereGeometry(0.32, 20, 20);
            const headMesh = new THREE.Mesh(head, mat);
            headMesh.position.y = 0.95;
            headMesh.castShadow = true;
            pieceGroup.add(headMesh);
        } else if (typeLower === 'r') {
            // ROOK
            const tower = new THREE.CylinderGeometry(0.38, 0.45, 0.9, 20);
            const towerMesh = new THREE.Mesh(tower, mat);
            towerMesh.position.y = 0.55;
            towerMesh.castShadow = true;
            pieceGroup.add(towerMesh);

            const crown = new THREE.CylinderGeometry(0.48, 0.42, 0.3, 16);
            const crownMesh = new THREE.Mesh(crown, mat);
            crownMesh.position.y = 1.1;
            crownMesh.castShadow = true;
            pieceGroup.add(crownMesh);
        } else if (typeLower === 'n') {
            // KNIGHT (Steed)
            const body = new THREE.CylinderGeometry(0.32, 0.45, 0.7, 16);
            const bodyMesh = new THREE.Mesh(body, mat);
            bodyMesh.position.y = 0.45;
            bodyMesh.castShadow = true;
            pieceGroup.add(bodyMesh);

            const head = new THREE.ConeGeometry(0.42, 0.75, 12);
            head.rotateZ(isWhite ? -0.4 : 0.4);
            const headMesh = new THREE.Mesh(head, mat);
            headMesh.position.set(0, 1.0, 0);
            headMesh.castShadow = true;
            pieceGroup.add(headMesh);
        } else if (typeLower === 'b') {
            // BISHOP
            const stem = new THREE.CylinderGeometry(0.3, 0.42, 1.0, 20);
            const stemMesh = new THREE.Mesh(stem, mat);
            stemMesh.position.y = 0.6;
            stemMesh.castShadow = true;
            pieceGroup.add(stemMesh);

            const miter = new THREE.ConeGeometry(0.35, 0.6, 20);
            const miterMesh = new THREE.Mesh(miter, mat);
            miterMesh.position.y = 1.35;
            miterMesh.castShadow = true;
            pieceGroup.add(miterMesh);

            const ball = new THREE.SphereGeometry(0.1, 12, 12);
            const ballMesh = new THREE.Mesh(ball, mat);
            ballMesh.position.y = 1.7;
            pieceGroup.add(ballMesh);
        } else if (typeLower === 'q') {
            // QUEEN
            const stem = new THREE.CylinderGeometry(0.32, 0.45, 1.3, 24);
            const stemMesh = new THREE.Mesh(stem, mat);
            stemMesh.position.y = 0.75;
            stemMesh.castShadow = true;
            pieceGroup.add(stemMesh);

            const crown = new THREE.CylinderGeometry(0.5, 0.28, 0.35, 24);
            const crownMesh = new THREE.Mesh(crown, mat);
            crownMesh.position.y = 1.55;
            crownMesh.castShadow = true;
            pieceGroup.add(crownMesh);

            const finial = new THREE.SphereGeometry(0.14, 16, 16);
            const finialMesh = new THREE.Mesh(finial, mat);
            finialMesh.position.y = 1.8;
            pieceGroup.add(finialMesh);
        } else if (typeLower === 'k') {
            // KING
            const stem = new THREE.CylinderGeometry(0.35, 0.48, 1.5, 24);
            const stemMesh = new THREE.Mesh(stem, mat);
            stemMesh.position.y = 0.85;
            stemMesh.castShadow = true;
            pieceGroup.add(stemMesh);

            const crown = new THREE.CylinderGeometry(0.52, 0.35, 0.3, 24);
            const crownMesh = new THREE.Mesh(crown, mat);
            crownMesh.position.y = 1.7;
            crownMesh.castShadow = true;
            pieceGroup.add(crownMesh);

            // Cross Finial
            const vBar = new THREE.BoxGeometry(0.1, 0.35, 0.1);
            const hBar = new THREE.BoxGeometry(0.28, 0.1, 0.1);
            const vMesh = new THREE.Mesh(vBar, mat);
            const hMesh = new THREE.Mesh(hBar, mat);
            vMesh.position.y = 2.0;
            hMesh.position.y = 2.05;
            pieceGroup.add(vMesh);
            pieceGroup.add(hMesh);
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
            this.camera.position.set(0, 18, 18);
        } else if (view === 'black') {
            this.camera.position.set(0, 18, -18);
        } else if (view === 'top') {
            this.camera.position.set(0, 24, 0.1);
        }
        this.controls.target.set(0, 0.5, 0);
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
