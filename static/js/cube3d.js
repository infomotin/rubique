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

        this.init();
    }

    init() {
        const width = this.container.clientWidth || 320;
        const height = this.container.clientHeight || 320;

        // 1. Scene Setup
        this.scene = new THREE.Scene();

        // 2. Camera Setup
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
        this.camera.position.set(4.5, 4.2, 5.5);

        // 3. WebGL Renderer with High-Gloss Antialiasing & Shadow Support
        this.renderer = new THREE.WebGLRenderer({
            alpha: true,
            antialias: true,
            powerPreference: 'high-performance'
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.container.appendChild(this.renderer.domElement);

        // 4. Orbit Controls (Mouse Drag Interactive 3D Rotation)
        if (typeof THREE.OrbitControls !== 'undefined') {
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.05;
            this.controls.rotateSpeed = 0.8;
            this.controls.enableZoom = false; // Keep UI stable
            this.controls.autoRotate = this.options.autoRotate;
            this.controls.autoRotateSpeed = 1.2;
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
        if (!this.container || !this.renderer || !this.camera) return;
        const width = this.container.clientWidth || 360;
        const height = this.container.clientHeight || 280;
        if (width <= 0 || height <= 0) return;
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        if (this.controls) {
            this.controls.update();
        }

        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
    }

    /**
     * Queued Layer Turn Animation for robust, non-blocking 3D moves
     */
    animateLayerTurn(move, onComplete) {
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
            targetAngle = isPrime ? Math.PI / 2 : -Math.PI / 2;
        } else if (base === 'S') {
            axis = new THREE.Vector3(0, 0, 1);
            layerCondition = (c) => Math.abs(c.position.z) < 0.5;
            targetAngle = isPrime ? -Math.PI / 2 : Math.PI / 2;
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
