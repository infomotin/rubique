# 🧊 CubePermutation AI

**CubePermutation AI** is a production-grade web application merging **Abstract Algebra / Permutation Group Theory ($G \le S_{54}$)** with **Computer Vision (OpenCV)** and **Optimal Two-Phase Rubik's Cube Solving**.

---

## 🚀 Key Features

1. **Mathematical Group Theory Permutation Visualizer**:
   - High-definition **3D Isometric SVG Rubik's Cube** displaying live facelet permutations with animated layer twisting.
   - **Symmetric Circular Orbit Network** with intersecting subgroup generator tracks, colored vertex clusters (Yellow, Blue, Orange, White, Green, Red), and glowing dynamic highlight arcs.
   - **Active Move Indicator** with neon glow typography (`U`, `R'`, `F2`, `M`, `E`, `S`) and dynamic step counter (`Step 13 / 15`).
   - **Interactive Move Ribbon** showing the full sequence with active move highlighting and click-to-jump navigation.
   - **Full Playback Deck**: Play/Pause, Step Forward/Backward, First/Last, Reset, and Speed controls (0.5x, 1x, 2x).

2. **Computer Vision & Image Preprocessing Pipeline (OpenCV)**:
   - Drag-and-drop cube photo uploader.
   - Automatic 3x3 facelet grid extraction, HSV color segmentation, centroid median sampling, and bounding box annotations.
   - Instant 1-click application of detected colors onto the 3D Isometric visualizer.

3. **Two-Phase Algorithm Solver**:
   - Integration with Kociemba Two-Phase algorithm for calculating optimal solve moves.
   - Disjoint cycle decomposition and permutation parity tracking.
   - Scramble generator and solve history database logging.

4. **Security & User Authentication**:
   - Secure registration and login with `werkzeug.security` password hashing.
   - Session-based route protection.
   - SQLite relational database storage.

5. **Codebase in Banglish**:
   - Every algorithmic step, route handler, and rendering pipeline is thoroughly documented with comments in Bangla (Latin alphabet).

---

## 🛠️ Installation & Local Setup

### 1. Clone or Open the Workspace
```bash
cd d:\laragon\www\rubique
```

### 2. Install Required Python Dependencies
```bash
pip install -r requirements.txt
```

*(Dependencies: `Flask`, `Werkzeug`, `opencv-python-headless`, `numpy`, `pillow`)*

---

## 🏃 Running the Application

Start the Flask development server:
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📁 Project Architecture

```
rubique/
│
├── app.py                     # Main Flask backend, SQLite DB, CV pipeline & REST APIs
├── solver_engine.py           # Pure Python Group Theory & Two-Phase solver engine
├── test_app.py                # Automated unit tests for Auth and APIs
├── requirements.txt           # Python package requirements
├── cubedata.db                # SQLite database (auto-generated)
│
├── templates/
│   ├── base.html              # Base layout with navbar, dark math canvas & alerts
│   ├── index.html             # Landing page
│   ├── login.html             # Glassmorphic user login page
│   ├── register.html          # User registration page
│   └── visualizer.html        # Main Group Theory Permutation Visualizer
│
└── static/
    ├── css/
    │   └── style.css          # Dark theme (#000000, #0b0c10), glowing neon accents & CSS variables
    ├── js/
    │   └── visualizer.js      # 3D Isometric SVG renderer, Orbit ring engine & playback controller
    └── uploads/               # Temporary image storage for OpenCV scanner
```
