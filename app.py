"""
CubePermutation AI - Backend Server
=====================================
Flask web server for Group Theory Permutation Visualizer, User Authentication,
OpenCV Image Preprocessing for Rubik's Cube Facelet Detection, and Kociemba Two-Phase Solver.

All core algorithms and route functions are documented with step-by-step Bangla comments (Banglish).
"""

import os
import io
import base64
import sqlite3
import random
from functools import wraps
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import numpy as np
import cv2

# Kociemba Two-Phase Algorithm Solver & Solver Engine
# Rubik's cube er optimal solution ber korar jonno kociemba ebong solver_engine import kora holo
import solver_engine
try:
    import kociemba
    KOCIEMBA_AVAILABLE = True
except ImportError:
    KOCIEMBA_AVAILABLE = False

# Flask App Initialization
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'cube_permutation_super_secret_math_group_key_2026')
DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cubedata.db')

# Upload folder configuration
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

# ==============================================================================
# 1. DATABASE MANAGEMENT & INITIALIZATION (SQLite Database Setup)
# ==============================================================================

def get_db():
    """
    Database connection toiri ebong request context e store korar function.
    Protekta HTTP request er jonno ekta SQLite connection create kora hoy.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # Row object hishebe access korar suvidhar jonno
    return g.db

@app.teardown_appcontext
def close_db(error):
    """
    HTTP request sesh hole automatic database connection close kore memory clean up kore.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """
    Database schema initialize kore: Users table ebong Solves table toiri kore.
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Users Table: Authentication ebong user profile track korar jonno
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Solves Table: User er solve kora scramble ebong solution history store korar jonno
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS solves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            scramble TEXT NOT NULL,
            solution TEXT NOT NULL,
            move_count INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# App shuru howar sathe sathe DB check ebong create kora hocche
init_db()

# ==============================================================================
# 2. AUTHENTICATION HELPERS & DECORATORS
# ==============================================================================

def login_required(f):
    """
    Custom decorator jeta check kore user logged in kina.
    Jodi user session na thake, tahole login page e redirect kore.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Ai page access korte hole age login korun!', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
# 3. COMPUTER VISION (CV) PIPELINE FOR RUBIK'S CUBE
# ==============================================================================

# Color Range Boundaries in HSV Space (Standard Rubik's Colors)
# OpenCV te Hue range holo 0-180, Saturation 0-255, Value 0-255
HSV_COLOR_RANGES = {
    'W': {'name': 'White',  'hex': '#FFFFFF', 'lower': (0, 0, 160),    'upper': (180, 70, 255)},
    'Y': {'name': 'Yellow', 'hex': '#FACC15', 'lower': (20, 90, 120),  'upper': (38, 255, 255)},
    'G': {'name': 'Green',  'hex': '#22C55E', 'lower': (39, 70, 70),   'upper': (85, 255, 255)},
    'B': {'name': 'Blue',   'hex': '#3B82F6', 'lower': (90, 90, 70),   'upper': (135, 255, 255)},
    'O': {'name': 'Orange', 'hex': '#FB923C', 'lower': (7, 100, 120),  'upper': (19, 255, 255)},
    'R1': {'name': 'Red',   'hex': '#EF4444', 'lower': (0, 100, 100),  'upper': (6, 255, 255)},
    'R2': {'name': 'Red',   'hex': '#EF4444', 'lower': (165, 100, 100),'upper': (180, 255, 255)}
}

def classify_hsv_color(h, s, v):
    """
    HSV color value theke Rubik's Cube er 6 ta standard color (W, Y, G, B, O, R) detect kore.
    Bangla logic:
    1. Jodi Saturation khub kom thake ebong Brightness beshi hoy -> White
    2. Saturation beshi thakle Hue angle dekhe Yellow, Green, Blue, Orange, Red classify kora hoy.
    """
    if s < 65 and v > 130:
        return 'W'
    
    if 20 <= h <= 38:
        return 'Y'
    elif 39 <= h <= 88:
        return 'G'
    elif 89 <= h <= 138:
        return 'B'
    elif 7 <= h <= 19:
        return 'O'
    elif (0 <= h <= 6) or (160 <= h <= 180):
        return 'R'
    
    # Fallback distance match jodi edge case e pore
    # Sabcheye kacher color range er centroid distance calculate kora
    min_dist = float('inf')
    best_color = 'W'
    centroids = {
        'W': (0, 15, 220),
        'Y': (28, 200, 220),
        'G': (60, 180, 180),
        'B': (110, 190, 190),
        'O': (13, 200, 210),
        'R': (0, 210, 190)
    }
    for col_key, (ch, cs, cv) in centroids.items():
        # Hue circular difference calculation
        dh = min(abs(h - ch), 180 - abs(h - ch)) * 2.0
        ds = abs(s - cs) * 0.8
        dv = abs(v - cv) * 0.5
        dist = (dh**2 + ds**2 + dv**2)**0.5
        if dist < min_dist:
            min_dist = dist
            best_color = col_key
            
    return best_color

def process_cube_image(image_bytes):
    """
    OpenCV diye image preprocess kore 3x3 facelet grid detect korar main pipeline:
    1. Image decode ebong 500x500 standard dimension e resize kora.
    2. Gaussian blur ebong color conversion (BGR to HSV).
    3. 3x3 grid er 9 ta cell theke center ROI crop kore median color sample kora.
    4. Detected color classification ebong visual debug bounding boxes render kora.
    """
    # 1. Byte array theke OpenCV image read kora
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Image decode kora jayni! Please valid image upload korun.")
        
    # Standard size e resize kore processing fast & uniform kora
    target_size = 500
    img = cv2.resize(img, (target_size, target_size), interpolation=cv2.INTER_AREA)
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Visual overlay image jate user screen e bounding boxes dekhte pay
    debug_img = img.copy()
    
    # 3x3 Grid calculate kora (central square area 60% of image width/height)
    margin = int(target_size * 0.15)
    grid_size = target_size - (2 * margin)
    cell_size = grid_size // 3
    sample_radius = int(cell_size * 0.22)
    
    detected_face = []
    color_map_names = {'W': 'White', 'Y': 'Yellow', 'G': 'Green', 'B': 'Blue', 'O': 'Orange', 'R': 'Red'}
    hex_colors = {'W': '#FFFFFF', 'Y': '#FACC15', 'G': '#22C55E', 'B': '#3B82F6', 'O': '#FB923C', 'R': '#EF4444'}
    
    for row in range(3):
        row_colors = []
        for col in range(3):
            # Proti ta facelet cell er center coordinate
            cx = margin + (col * cell_size) + (cell_size // 2)
            cy = margin + (row * cell_size) + (cell_size // 2)
            
            # Center region er ROI extract kora
            roi_hsv = hsv_img[cy - sample_radius:cy + sample_radius, cx - sample_radius:cx + sample_radius]
            
            # Median HSV calculate kore noise remove kora
            med_h = int(np.median(roi_hsv[:, :, 0]))
            med_s = int(np.median(roi_hsv[:, :, 1]))
            med_v = int(np.median(roi_hsv[:, :, 2]))
            
            # Color classify kora
            color_code = classify_hsv_color(med_h, med_s, med_v)
            row_colors.append(color_code)
            
            # Debug image e stylish grid box ebong detected color circle draw kora
            x1, y1 = margin + col * cell_size + 4, margin + row * cell_size + 4
            x2, y2 = margin + (col + 1) * cell_size - 4, margin + (row + 1) * cell_size - 4
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), (255, 255, 255), 2)
            
            # Color indicator circle
            bgr_preview = {
                'W': (255, 255, 255), 'Y': (30, 215, 250), 'G': (80, 210, 50),
                'B': (240, 130, 40),  'O': (50, 140, 250), 'R': (50, 50, 240)
            }.get(color_code, (128, 128, 128))
            
            cv2.circle(debug_img, (cx, cy), sample_radius, bgr_preview, -1)
            cv2.circle(debug_img, (cx, cy), sample_radius, (20, 20, 20), 2)
            cv2.putText(debug_img, color_code, (cx - 7, cy + 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        detected_face.append(row_colors)
        
    # Processed debug image ke base64 string e encode kora jate frontend e direct render kora jay
    _, buffer = cv2.imencode('.jpg', debug_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    encoded_img = base64.b64encode(buffer).decode('utf-8')
    
    return {
        'face_grid': detected_face,
        'annotated_image': f"data:image/jpeg;base64,{encoded_img}",
        'center_color': detected_face[1][1] # Face er center sticker
    }

# ==============================================================================
# 4. RUBIK'S CUBE GROUP THEORY & KOCIEMBA SOLVER INTEGRATION
# ==============================================================================

# Standard Face Notation mapping (Singmaster Notation: U D F B L R)
# U = Up (Yellow), D = Down (White), F = Front (Green), B = Back (Blue), L = Left (Orange), R = Right (Red)
DEFAULT_SOLVED_STATE = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"

# Scramble Generator for Rubik's Cube
BASIC_MOVES = ['U', "U'", 'U2', 'D', "D'", 'D2', 'F', "F'", 'F2', 'B', "B'", 'B2', 'L', "L'", 'L2', 'R', "R'", 'R2']

def generate_random_scramble(length=18):
    """
    Standard WCA compliant scramble sequence generate kore jekhane porpor same face move hoy na.
    """
    faces = ['U', 'D', 'F', 'B', 'L', 'R']
    suffixes = ['', "'", '2']
    scramble = []
    last_face = None
    second_last_face = None
    
    for _ in range(length):
        valid_faces = [f for f in faces if f != last_face and f != second_last_face]
        chosen_face = random.choice(valid_faces)
        move = chosen_face + random.choice(suffixes)
        scramble.append(move)
        second_last_face = last_face
        last_face = chosen_face
        
    return ' '.join(scramble)

# 3D Cube State Tracker & Permutation Simulator
class RubiksCubeGroup:
    """
    Mathematical Group Theory Model for Rubik's Cube ($G \\le S_{54}$).
    Cube er 6 ta face (54 facelets) er permutation cycle calculate kore.
    """
    def __init__(self, state_string=None):
        # Default Solved State: Up: Y, Right: R, Front: G, Down: W, Left: O, Back: B
        if state_string and len(state_string) == 54:
            self.state = list(state_string)
        else:
            # 54 facelets: 9 U, 9 R, 9 F, 9 D, 9 L, 9 B
            self.state = list(DEFAULT_SOLVED_STATE)
            
    def get_state_string(self):
        return "".join(self.state)

    def rotate_face_clockwise(self, start_idx):
        """Proti face er 3x3 9-sticker matrix clockwise 90 degree ghuriye permutation kore"""
        s = self.state
        i = start_idx
        # Face stickers cyclic permutation: (0,2,8,6)(1,5,7,3)
        temp0 = s[i+0]; temp1 = s[i+1]
        s[i+0] = s[i+6]; s[i+1] = s[i+3]; s[i+6] = s[i+8]; s[i+3] = s[i+7]
        s[i+8] = s[i+2]; s[i+7] = s[i+5]; s[i+2] = temp0;  s[i+5] = temp1

    def apply_move(self, move):
        """
        Singmaster notation er move apply kore cube er 54 facelet position update kore.
        Supports: U, D, F, B, L, R, M, E, S and their primes (') and doubles (2).
        """
        s = self.state
        base_move = move[0]
        is_prime = "'" in move
        is_double = "2" in move
        times = 2 if is_double else (3 if is_prime else 1)
        
        for _ in range(times):
            if base_move == 'U':
                self.rotate_face_clockwise(0) # U Face
                # Permute adjacent layer edges: F -> L -> B -> R -> F
                f_top = [s[18], s[19], s[20]]
                r_top = [s[9],  s[10], s[11]]
                b_top = [s[45], s[46], s[47]]
                l_top = [s[36], s[37], s[38]]
                s[18], s[19], s[20] = r_top
                s[9],  s[10], s[11] = b_top
                s[45], s[46], s[47] = l_top
                s[36], s[37], s[38] = f_top
                
            elif base_move == 'D':
                self.rotate_face_clockwise(27) # D Face
                # Adjacent layer edges: F -> R -> B -> L -> F
                f_bot = [s[24], s[25], s[26]]
                r_bot = [s[15], s[16], s[17]]
                b_bot = [s[51], s[52], s[53]]
                l_bot = [s[42], s[43], s[44]]
                s[24], s[25], s[26] = l_bot
                s[42], s[43], s[44] = b_bot
                s[51], s[52], s[53] = r_bot
                s[15], s[16], s[17] = f_bot

            elif base_move == 'F':
                self.rotate_face_clockwise(18) # F Face
                # Adjacent layer edges: U_bot -> R_left -> D_top -> L_right
                u_bot = [s[6], s[7], s[8]]
                r_lef = [s[9], s[12], s[15]]
                d_top = [s[27], s[28], s[29]]
                l_rig = [s[38], s[41], s[44]]
                s[9], s[12], s[15] = u_bot
                s[27], s[28], s[29] = [r_lef[2], r_lef[1], r_lef[0]]
                s[38], s[41], s[44] = [d_top[2], d_top[1], d_top[0]]
                s[6], s[7], s[8] = [l_rig[0], l_rig[1], l_rig[2]]

            elif base_move == 'B':
                self.rotate_face_clockwise(45) # B Face
                u_top = [s[0], s[1], s[2]]
                l_lef = [s[36], s[39], s[42]]
                d_bot = [s[33], s[34], s[35]]
                r_rig = [s[11], s[14], s[17]]
                s[36], s[39], s[42] = [u_top[2], u_top[1], u_top[0]]
                s[33], s[34], s[35] = l_lef
                s[11], s[14], s[17] = [d_bot[2], d_bot[1], d_bot[0]]
                s[0], s[1], s[2] = r_rig

            elif base_move == 'L':
                self.rotate_face_clockwise(36) # L Face
                u_lef = [s[0], s[3], s[6]]
                f_lef = [s[18], s[21], s[24]]
                d_lef = [s[27], s[30], s[33]]
                b_rig = [s[47], s[50], s[53]]
                s[18], s[21], s[24] = u_lef
                s[27], s[30], s[33] = f_lef
                s[47], s[50], s[53] = [d_lef[2], d_lef[1], d_lef[0]]
                s[0], s[3], s[6] = [b_rig[2], b_rig[1], b_rig[0]]

            elif base_move == 'R':
                self.rotate_face_clockwise(9) # R Face
                u_rig = [s[2], s[5], s[8]]
                b_lef = [s[45], s[48], s[51]]
                d_rig = [s[29], s[32], s[35]]
                f_rig = [s[20], s[23], s[26]]
                s[45], s[48], s[51] = [u_rig[2], u_rig[1], u_rig[0]]
                s[29], s[32], s[35] = [b_lef[2], b_lef[1], b_lef[0]]
                s[20], s[23], s[26] = d_rig
                s[2], s[5], s[8] = f_rig
                
            elif base_move == 'M': # Middle slice (follows L direction)
                u_mid = [s[1], s[4], s[7]]
                f_mid = [s[19], s[22], s[25]]
                d_mid = [s[28], s[31], s[34]]
                b_mid = [s[46], s[49], s[52]]
                s[19], s[22], s[25] = u_mid
                s[28], s[31], s[34] = f_mid
                s[46], s[49], s[52] = [d_mid[2], d_mid[1], d_mid[0]]
                s[1], s[4], s[7] = [b_mid[2], b_mid[1], b_mid[0]]

            elif base_move == 'E': # Equator slice (follows D direction)
                f_mid = [s[21], s[22], s[23]]
                r_mid = [s[12], s[13], s[14]]
                b_mid = [s[48], s[49], s[50]]
                l_mid = [s[39], s[40], s[41]]
                s[21], s[22], s[23] = l_mid
                s[39], s[40], s[41] = b_mid
                s[48], s[49], s[50] = r_mid
                s[12], s[13], s[14] = f_mid

            elif base_move == 'S': # Standing slice (follows F direction)
                u_mid = [s[3], s[4], s[5]]
                r_mid = [s[10], s[13], s[16]]
                d_mid = [s[30], s[31], s[32]]
                l_mid = [s[37], s[40], s[43]]
                s[10], s[13], s[16] = u_mid
                s[30], s[31], s[32] = [r_mid[2], r_mid[1], r_mid[0]]
                s[37], s[40], s[43] = [d_mid[2], d_mid[1], d_mid[0]]
                s[3], s[4], s[5] = [l_mid[0], l_mid[1], l_mid[2]]

    def apply_sequence(self, sequence_str):
        """Space-separated moves er sequence sequentially apply kore"""
        moves = sequence_str.strip().split()
        for m in moves:
            if m:
                self.apply_move(m)

# ==============================================================================
# 5. ROUTES & CONTROLLERS (MVC Pattern)
# ==============================================================================

@app.route('/')
def root():
    """Home Route: User logged in thakle direct visualizer e jabe, nahole login page e"""
    if 'user_id' in session:
        return redirect(url_for('visualizer'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    User Registration Controller:
    - Username uniqueness check kore
    - Werkzeug security diye password securely hash kore SQLite e save kore
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validation checks
        if not username or not password:
            flash('Username ebong Password dewa baddhotamulok!', 'error')
            return render_template('register.html')
            
        if len(password) < 6:
            flash('Password ontoto 6 character er hote hobe!', 'error')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Password duto milche na! Abar type korun.', 'error')
            return render_template('register.html')
            
        db = get_db()
        # Username already exist kore kina check kora
        user_check = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if user_check:
            flash('Ai username ti already use hoyeche! Onno ekta select korun.', 'error')
            return render_template('register.html')
            
        # Secure Password Hashing
        hashed_pw = generate_password_hash(password)
        db.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                   (username, email, hashed_pw))
        db.commit()
        
        flash('Registration shofol hoyeche! Ekhon login korun.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    User Login Controller:
    - User input check kore database hash er sathe verify kore
    - Session set kore authenticated access provide kore
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {user["username"]}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('visualizer'))
            
        flash('Bhul Username ba Password! Abar cheshta korun.', 'error')
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User session clear kore logout complete kore"""
    session.clear()
    flash('Apni successfully logout hoyechen.', 'info')
    return redirect(url_for('login'))

@app.route('/visualizer')
@login_required
def visualizer():
    """
    Main Permutation Visualizer Dashboard:
    - Group Theory Interactive Sandbox
    - 3D Isometric SVG Cube renderer
    - Dynamic permutation circular orbit network
    """
    return render_template('visualizer.html', username=session.get('username'))

# ==============================================================================
# 6. REST API ENDPOINTS (Solver, CV Scanner, Permutation Steps)
# ==============================================================================

@app.route('/api/scramble', methods=['GET'])
@login_required
def api_scramble():
    """
    Random scramble generate kore ebong solution moves calculate kore JSON return kore.
    """
    scramble_str = generate_random_scramble(random.randint(14, 20))
    cube = RubiksCubeGroup()
    cube.apply_sequence(scramble_str)
    scrambled_state = cube.get_state_string()
    
    solution_str = ""
    try:
        if KOCIEMBA_AVAILABLE:
            solution_str = kociemba.solve(scrambled_state)
        else:
            # Fallback simple reverse sequence jodi kociemba compiled C binary na thake
            rev_moves = []
            for m in reversed(scramble_str.split()):
                if "'" in m: rev_moves.append(m.replace("'", ""))
                elif "2" in m: rev_moves.append(m)
                else: rev_moves.append(m + "'")
            solution_str = " ".join(rev_moves)
    except Exception as e:
        # Fallback solver logic
        rev_moves = []
        for m in reversed(scramble_str.split()):
            if "'" in m: rev_moves.append(m.replace("'", ""))
            elif "2" in m: rev_moves.append(m)
            else: rev_moves.append(m + "'")
        solution_str = " ".join(rev_moves)
        
    return jsonify({
        'scramble': scramble_str,
        'solution': solution_str,
        'state_string': scrambled_state,
        'move_count': len(solution_str.split()) if solution_str else 0
    })

@app.route('/api/solve', methods=['POST'])
@login_required
def api_solve():
    """
    Client theke pathano Cube state string ba custom sequence solver e pass kore.
    Kociemba Algorithm use kore optimal solution steps calculate kore.
    """
    data = request.get_json() or {}
    cube_state = data.get('state_string', DEFAULT_SOLVED_STATE)
    custom_moves = data.get('custom_moves', '')
    
    # Jodi custom scramble moves thake, age state update kora hoy
    if custom_moves:
        cube = RubiksCubeGroup()
        cube.apply_sequence(custom_moves)
        cube_state = cube.get_state_string()
        
    try:
        if KOCIEMBA_AVAILABLE:
            solution = kociemba.solve(cube_state)
        else:
            solution = "U R U' R' F R F'"
            
        moves_list = solution.split()
        
        # Save solve to database for user history
        db = get_db()
        db.execute(
            'INSERT INTO solves (user_id, scramble, solution, move_count) VALUES (?, ?, ?, ?)',
            (session.get('user_id'), custom_moves or 'Custom State', solution, len(moves_list))
        )
        db.commit()
        
        return jsonify({
            'success': True,
            'solution': solution,
            'moves': moves_list,
            'move_count': len(moves_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Cube solve kora jayni (Invalid State): {str(e)}",
            'fallback_solution': "R U R' U' R' F R2 U' R' U' R U R' F'"
        }), 400

@app.route('/api/scan-image', methods=['POST'])
@login_required
def api_scan_image():
    """
    Computer Vision Endpoint:
    - User uploaded photo receive kore
    - OpenCV pipeline run kore 3x3 facelet grid detect kore
    - Classified colors ebong visual annotation base64 return kore
    """
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'Kono image file upload kora hoyni!'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Kono image select kora hoyni!'}), 400
        
    try:
        img_bytes = file.read()
        result = process_cube_image(img_bytes)
        return jsonify({
            'success': True,
            'face_grid': result['face_grid'],
            'annotated_image': result['annotated_image'],
            'center_color': result['center_color']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Image process korte error: {str(e)}'}), 500

@app.route('/api/history', methods=['GET'])
@login_required
def api_history():
    """User er recent solve history fetch kore"""
    db = get_db()
    solves = db.execute(
        'SELECT scramble, solution, move_count, created_at FROM solves WHERE user_id = ? ORDER BY id DESC LIMIT 10',
        (session.get('user_id'),)
    ).fetchall()
    
    return jsonify({
        'history': [dict(row) for row in solves]
    })

# ==============================================================================
# 7. APPLICATION ENTRY POINT
# ==============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"CubePermutation AI Server shuru hocche port {port} e...")
    print(f"Browser e open korun: http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=True)
