/**
 * CubePermutation AI - 3D Interactive WebGL Rubik's Cube Engine
 * ===============================================================
 * Powered by Three.js with realistic glossy materials, embossed beveled stickers,
 * mouse pointer tracking spotlights, and 3D layer twist animations.
 */

class Interactive3DCube {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.options = Object.assign({
            interactive: true,
            autoRotate: false,
            rotationSpeed: 0.005,
            showControls: true,
            cameraZ: 6.5
        }, options);

        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.cubeGroup = null;
        this.cubies = [];
        this.isAnimatingTurn = false;
        
        // Face Color Hex Tokens (Realistic glossy & vibrant speedcube colors)
        this.COLORS = {
            'U': 0xfacc15, // Yellow (Top)
            'D': 0xffffff, // White (Bottom)
            'F': 0x16a34a, // Green (Front)
            'B': 0x2563eb, // Blue (Back)
            'L': 0xf97316, // Orange (Left)
            'R': 0xdc2626, // Red (Right)
            'CORE': 0x111318 // Deep Black Plastic Core
        };

        // 54 Facelet State: [U0-U8, R9-R17, F18-F26, D27-D35, L36-L44, B45-B53]
        this.state = [
            ...Array(9).fill('U'),
            ...Array(9).fill('R'),
            ...Array(9).fill('F'),
            ...Array(9).fill('D'),
            ...Array(9).fill('L'),
            ...Array(9).fill('B')
        ];

        this.isSupported = false;
        this.init();
    }

    static isWebGLAvailable() {
        try {
            const canvas = document.createElement('canvas');
            return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
        } catch (e) {
            return false;
        }
    }

    showFallback(reason = '') {
        this.isSupported = false;
        if (!this.container) return;
        this.container.innerHTML = `
            <div class="w-full h-full min-h-[220px] flex flex-col items-center justify-center p-6 text-center select-none bg-slate-950/70 rounded-2xl border border-slate-800/80 backdrop-blur-md">
                <div class="relative mb-3 flex items-center justify-center">
                    <svg viewBox="-50 -50 100 100" class="w-20 h-20 animate-pulse">
                        <polygon points="0,-30 26,-15 26,15 0,30 -26,15 -26,-15" fill="#0f172a" stroke="#818cf8" stroke-width="2"/>
                        <line x1="0" y1="0" x2="0" y2="30" stroke="#38bdf8" stroke-width="1.5"/>
                        <line x1="0" y1="0" x2="26" y2="-15" stroke="#38bdf8" stroke-width="1.5"/>
                        <line x1="0" y1="0" x2="-26" y2="-15" stroke="#38bdf8" stroke-width="1.5"/>
                        <circle cx="0" cy="0" r="3" fill="#818cf8"/>
                    </svg>
                </div>
                <h4 class="text-xs font-bold font-outfit text-white tracking-wide uppercase">Rubik's Cube 3D Simulation</h4>
                <p class="text-[10px] font-mono text-slate-400 mt-1 max-w-[220px] leading-relaxed">
                    WebGL hardware acceleration unavailable in current browser mode. 2D Interactive Matrix & Solver Engine active.
                </p>
            </div>
        `;
    }

    init() {
        if (!Interactive3DCube.isWebGLAvailable()) {
            console.warn('[Interactive3DCube] WebGL is not supported or disabled in this browser.');
            this.showFallback();
            return;
        }

        const width = this.container.clientWidth || 320;
        const height = this.container.clientHeight || 320;

        // 1. Scene Setup
        this.scene = new THREE.Scene();

        // 2. Camera Setup
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
        this.camera.position.set(4.5, 4.2, 5.5);

        // 3. WebGL Renderer with High-Gloss Antialiasing & Shadow Support
        try {
            this.renderer = new THREE.WebGLRenderer({
                alpha: true,
                antialias: true,
                powerPreference: 'default'
            });
            this.renderer.setSize(width, height);
            this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
            this.renderer.shadowMap.enabled = true;
            this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            this.container.appendChild(this.renderer.domElement);
            this.isSupported = true;
        } catch (err) {
            console.warn('[Interactive3DCube] WebGL context creation failed:', err);
            this.showFallback();
            return;
        }

        // 4. Orbit Controls (Mouse Drag Interactive 3D Rotation)
        if (typeof THREE.OrbitControls !== 'undefined') {
            try {
                this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
                this.controls.enableDamping = true;
                this.controls.dampingFactor = 0.05;
                this.controls.rotateSpeed = 0.8;
                this.controls.enableZoom = false; // Keep UI stable
                this.controls.autoRotate = this.options.autoRotate;
                this.controls.autoRotateSpeed = 1.2;
            } catch (e) {
                console.warn('[Interactive3DCube] OrbitControls failed to attach:', e);
            }
        }

        // 5. Cinematic Glossy Lighting & Specular Highlights
        this.setupLighting();

        // 6. Build Realistic 3x3 Embossed Rubik's Cube Geometry
        this.buildCube();

        // 7. Mouse Pointer Spotlight Tracking
        this.setupMouseTracking();

        // 8. Resize Handler
        window.addEventListener('resize', () => this.onResize());

        // 9. Start Render Loop
        this.animate();
    }

    setupLighting() {
        // Soft Ambient fill
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
        this.scene.add(ambientLight);

        // Main Studio Key Light (Creates crisp glossy specular reflections)
        const keyLight = new THREE.DirectionalLight(0xffffff, 1.2);
        keyLight.position.set(8, 12, 8);
        this.scene.add(keyLight);

        // Blue/Indigo Cyber Rim Light
        const rimLight1 = new THREE.PointLight(0x818cf8, 2.5, 20);
        rimLight1.position.set(-8, 6, -8);
        this.scene.add(rimLight1);

        // Cyan Ambient Accent Light
        const rimLight2 = new THREE.PointLight(0x38bdf8, 2.0, 20);
        rimLight2.position.set(6, -6, 6);
        this.scene.add(rimLight2);

        // Dynamic Cursor Spotlight (Follows mouse pointer)
        this.cursorLight = new THREE.PointLight(0xffffff, 1.5, 15);
        this.cursorLight.position.set(0, 5, 5);
        this.scene.add(this.cursorLight);
    }

    createStickerMaterial(colorHex) {
        // Glossy Embossed Material with High Specular & Clearcoat Finish
        return new THREE.MeshPhysicalMaterial({
            color: colorHex,
            roughness: 0.15,
            metalness: 0.05,
            clearcoat: 0.9,
            clearcoatRoughness: 0.1,
            reflectivity: 0.85
        });
    }

    buildCube() {
        if (this.cubeGroup) {
            this.scene.remove(this.cubeGroup);
        }

        this.cubeGroup = new THREE.Group();
        this.cubies = [];

        const size = 0.94;
        const spacing = 1.0;
        const coreMat = new THREE.MeshStandardMaterial({
            color: this.COLORS.CORE,
            roughness: 0.4,
            metalness: 0.2
        });

        const cubieGeo = new THREE.BoxGeometry(size, size, size);

        for (let x = -1; x <= 1; x++) {
            for (let y = -1; y <= 1; y++) {
                for (let z = -1; z <= 1; z++) {
                    // Create black plastic cubie core
                    const materials = [
                        x === 1 ? this.createStickerMaterial(this.COLORS.R) : coreMat,   // Right (+X)
                        x === -1 ? this.createStickerMaterial(this.COLORS.L) : coreMat,  // Left (-X)
                        y === 1 ? this.createStickerMaterial(this.COLORS.U) : coreMat,   // Top (+Y)
                        y === -1 ? this.createStickerMaterial(this.COLORS.D) : coreMat,  // Bottom (-Y)
                        z === 1 ? this.createStickerMaterial(this.COLORS.F) : coreMat,   // Front (+Z)
                        z === -1 ? this.createStickerMaterial(this.COLORS.B) : coreMat   // Back (-Z)
                    ];

                    const cubie = new THREE.Mesh(cubieGeo, materials);
                    cubie.position.set(x * spacing, y * spacing, z * spacing);
                    cubie.castShadow = true;
                    cubie.receiveShadow = true;

                    // Store original grid position
                    cubie.userData = { gridX: x, gridY: y, gridZ: z };

                    this.cubies.push(cubie);
                    this.cubeGroup.add(cubie);
                }
            }
        }

        this.scene.add(this.cubeGroup);
    }

    /**
     * Updates 3D cube facelet stickers dynamically from 2D Net / OpenCV state
     * @param {Object} faceletMap - e.g. { U: ['yellow',...], L: [...], F: [...], R: [...], B: [...], D: [...] }
     */
    applyFaceletMap(faceletMap) {
        if (!faceletMap || !this.cubies.length) return;

        const hexMap = {
            'yellow': 0xfacc15, 'Y': 0xfacc15, 'U': 0xfacc15,
            'white': 0xffffff, 'W': 0xffffff, 'D': 0xffffff,
            'green': 0x16a34a, 'G': 0x16a34a, 'F': 0x16a34a,
            'blue': 0x2563eb, 'B': 0x2563eb,
            'orange': 0xf97316, 'O': 0xf97316, 'L': 0xf97316,
            'red': 0xdc2626, 'R': 0xdc2626
        };

        const getColor = (c) => hexMap[c] || hexMap[c?.toLowerCase?.()] || 0x111318;

        this.cubies.forEach(cubie => {
            const x = Math.round(cubie.position.x);
            const y = Math.round(cubie.position.y);
            const z = Math.round(cubie.position.z);

            // Right (+X)
            if (x === 1 && faceletMap.R && cubie.material[0]) {
                const idx = (1 - y) * 3 + (1 - z);
                if (faceletMap.R[idx]) cubie.material[0].color.setHex(getColor(faceletMap.R[idx]));
            }
            // Left (-X)
            if (x === -1 && faceletMap.L && cubie.material[1]) {
                const idx = (1 - y) * 3 + (z + 1);
                if (faceletMap.L[idx]) cubie.material[1].color.setHex(getColor(faceletMap.L[idx]));
            }
            // Top (+Y)
            if (y === 1 && faceletMap.U && cubie.material[2]) {
                const idx = (z + 1) * 3 + (x + 1);
                if (faceletMap.U[idx]) cubie.material[2].color.setHex(getColor(faceletMap.U[idx]));
            }
            // Bottom (-Y)
            if (y === -1 && faceletMap.D && cubie.material[3]) {
                const idx = (1 - z) * 3 + (x + 1);
                if (faceletMap.D[idx]) cubie.material[3].color.setHex(getColor(faceletMap.D[idx]));
            }
            // Front (+Z)
            if (z === 1 && faceletMap.F && cubie.material[4]) {
                const idx = (1 - y) * 3 + (x + 1);
                if (faceletMap.F[idx]) cubie.material[4].color.setHex(getColor(faceletMap.F[idx]));
            }
            // Back (-Z)
            if (z === -1 && faceletMap.B && cubie.material[5]) {
                const idx = (1 - y) * 3 + (1 - x);
                if (faceletMap.B[idx]) cubie.material[5].color.setHex(getColor(faceletMap.B[idx]));
            }
        });
    }

    resetToSolved() {
        this.buildCube();
    }

    lookAtFace(face) {
        if (!this.controls || !this.camera) return;
        const dist = 5.8;
        const targets = {
            'U': { x: 0, y: dist, z: 0.001 },
            'D': { x: 0, y: -dist, z: 0.001 },
            'F': { x: 0, y: 0.2, z: dist },
            'B': { x: 0, y: 0.2, z: -dist },
            'L': { x: -dist, y: 0.2, z: 0 },
            'R': { x: dist, y: 0.2, z: 0 },
            'ISO': { x: 3.8, y: 3.2, z: 4.2 }
        };
        const pos = targets[face] || targets.ISO;
        this.camera.position.set(pos.x, pos.y, pos.z);
        this.controls.target.set(0, 0, 0);
        this.controls.update();
    }

    setupMouseTracking() {
        this.container.addEventListener('mousemove', (e) => {
            const rect = this.container.getBoundingClientRect();
            const mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
            const mouseY = -((e.clientY - rect.top) / rect.height) * 2 + 1;

            if (this.cursorLight) {
                this.cursorLight.position.x = mouseX * 6;
                this.cursorLight.position.y = mouseY * 6 + 2;
                this.cursorLight.position.z = 6;
            }
        });
    }

    onResize() {
        if (!this.isSupported || !this.container || !this.renderer || !this.camera) return;
        const width = this.container.clientWidth || 360;
        const height = this.container.clientHeight || 280;
        if (width <= 0 || height <= 0) return;
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    animate() {
        if (!this.isSupported || !this.renderer || !this.scene || !this.camera) return;
        requestAnimationFrame(() => this.animate());

        if (this.controls) {
            this.controls.update();
        }

        this.renderer.render(this.scene, this.camera);
    }

    /**
     * Queued Layer Turn Animation for robust, non-blocking 3D moves
     */
    animateLayerTurn(move, onComplete) {
        if (!this.isSupported || !this.cubeGroup) {
            if (onComplete) onComplete();
            return;
        }
        if (!this.turnQueue) this.turnQueue = [];
        this.turnQueue.push({ move, onComplete });
        if (!this.isAnimatingTurn) {
            this.processNextTurn();
        }
    }

    processNextTurn() {
        if (!this.turnQueue || this.turnQueue.length === 0) {
            this.isAnimatingTurn = false;
            return;
        }

        this.isAnimatingTurn = true;
        const item = this.turnQueue.shift();
        const move = item.move;
        const onComplete = item.onComplete;

        const base = move[0];
        const isPrime = move.includes("'");
        const isDouble = move.includes("2");

        let axis = new THREE.Vector3(0, 1, 0);
        let layerCondition = (c) => c.position.y > 0.5;
        let targetAngle = -Math.PI / 2;

        if (base === 'U') {
            axis = new THREE.Vector3(0, 1, 0);
            layerCondition = (c) => c.position.y > 0.5;
            targetAngle = isPrime ? Math.PI / 2 : -Math.PI / 2;
        } else if (base === 'D') {
            axis = new THREE.Vector3(0, 1, 0);
            layerCondition = (c) => c.position.y < -0.5;
            targetAngle = isPrime ? -Math.PI / 2 : Math.PI / 2;
        } else if (base === 'R') {
            axis = new THREE.Vector3(1, 0, 0);
            layerCondition = (c) => c.position.x > 0.5;
            targetAngle = isPrime ? Math.PI / 2 : -Math.PI / 2;
        } else if (base === 'L') {
            axis = new THREE.Vector3(1, 0, 0);
            layerCondition = (c) => c.position.x < -0.5;
            targetAngle = isPrime ? -Math.PI / 2 : Math.PI / 2;
        } else if (base === 'F') {
            axis = new THREE.Vector3(0, 0, 1);
            layerCondition = (c) => c.position.z > 0.5;
            targetAngle = isPrime ? Math.PI / 2 : -Math.PI / 2;
        } else if (base === 'B') {
            axis = new THREE.Vector3(0, 0, 1);
            layerCondition = (c) => c.position.z < -0.5;
            targetAngle = isPrime ? -Math.PI / 2 : Math.PI / 2;
        } else if (base === 'M') {
            axis = new THREE.Vector3(1, 0, 0);
            layerCondition = (c) => Math.abs(c.position.x) < 0.5;
            targetAngle = isPrime ? -Math.PI / 2 : Math.PI / 2;
        } else if (base === 'E') {
            axis = new THREE.Vector3(0, 1, 0);
            layerCondition = (c) => Math.abs(c.position.y) < 0.5;
            // E follows D (equator slice turns in the same direction as D)
            targetAngle = isPrime ? -Math.PI / 2 : Math.PI / 2;
        } else if (base === 'S') {
            axis = new THREE.Vector3(0, 0, 1);
            layerCondition = (c) => Math.abs(c.position.z) < 0.5;
            // S follows F (standing slice turns in the same direction as F)
            targetAngle = isPrime ? Math.PI / 2 : -Math.PI / 2;
        }

        if (isDouble) {
            targetAngle *= 2;
        }

        // Group the selected layer cubies into a pivot group
        const pivotGroup = new THREE.Group();
        this.scene.add(pivotGroup);

        const activeCubies = this.cubies.filter(layerCondition);
        activeCubies.forEach(c => {
            this.cubeGroup.remove(c);
            pivotGroup.add(c);
        });

        const duration = 220; // ms
        const startTime = performance.now();

        const stepRotation = (now) => {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1.0);
            const ease = 1 - Math.pow(1 - progress, 3);
            const currentAngle = targetAngle * ease;

            pivotGroup.setRotationFromAxisAngle(axis, currentAngle);

            if (progress < 1.0) {
                requestAnimationFrame(stepRotation);
            } else {
                pivotGroup.setRotationFromAxisAngle(axis, targetAngle);
                pivotGroup.updateMatrixWorld();

                activeCubies.forEach(c => {
                    c.applyMatrix4(pivotGroup.matrix);
                    c.position.x = Math.round(c.position.x);
                    c.position.y = Math.round(c.position.y);
                    c.position.z = Math.round(c.position.z);
                    pivotGroup.remove(c);
                    this.cubeGroup.add(c);
                });

                this.scene.remove(pivotGroup);
                this.isAnimatingTurn = false;
                if (onComplete) onComplete();
                // Process subsequent queued turns
                this.processNextTurn();
            }
        };

        requestAnimationFrame(stepRotation);
    }
}

// Global Export
window.Interactive3DCube = Interactive3DCube;
