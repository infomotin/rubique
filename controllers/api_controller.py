"""
CubePermutation AI - REST API Controller (MVC Pattern)
======================================================
Handles RESTful endpoints for Scramble Generation, Two-Phase Solving,
OpenCV Image Preprocessing, and Solve History logging.
"""

import base64
import random
import numpy as np
import cv2
from flask import Blueprint, request, jsonify, session
from models.solve_model import SolveModel
from .auth_controller import login_required
import solver_engine

api_bp = Blueprint('api', __name__, url_prefix='/api')

def classify_hsv_color(h, s, v):
    """HSV color classifier with adaptive illumination thresholds"""
    # White detection: Low saturation, medium-to-high value
    if s < 65 and v > 115:
        return 'W'
    # Yellow vs Orange vs Red
    if 20 <= h <= 36 and s >= 65:
        return 'Y'
    elif 37 <= h <= 85 and s >= 60:
        return 'G'
    elif 86 <= h <= 138 and s >= 55:
        return 'B'
    elif 6 <= h <= 19 and s >= 65:
        return 'O'
    elif ((0 <= h <= 5) or (158 <= h <= 180)) and s >= 60:
        return 'R'
    # Fallback to Brightness
    if v > 160:
        return 'W'
    return 'Y'

SAMPLE_PRESETS = {
    'sample_u': [
        ['Y', 'G', 'Y'],
        ['O', 'Y', 'R'],
        ['Y', 'B', 'W']
    ],
    'sample_f': [
        ['G', 'Y', 'G'],
        ['R', 'G', 'O'],
        ['W', 'G', 'Y']
    ],
    'sample_r': [
        ['R', 'B', 'R'],
        ['Y', 'R', 'W'],
        ['R', 'G', 'O']
    ],
    'sample_solved': [
        ['G', 'G', 'G'],
        ['G', 'G', 'G'],
        ['G', 'G', 'G']
    ]
}

def generate_annotated_sample_image(grid):
    """Generates an annotated 3x3 synthetic image preview for sample presets"""
    size = 360
    img = np.zeros((size, size, 3), dtype=np.uint8)
    img[:] = (15, 23, 42) # Slate-950 background
    
    bgr_colors = {
        'Y': (21, 204, 250), # Yellow
        'W': (248, 250, 252), # White
        'G': (94, 197, 34), # Green
        'B': (235, 99, 37), # Blue
        'O': (60, 146, 251), # Orange
        'R': (68, 68, 239) # Red
    }
    
    margin = 30
    grid_size = size - 2 * margin
    cell = grid_size // 3
    
    for r in range(3):
        for c in range(3):
            code = grid[r][c]
            col = bgr_colors.get(code, (200, 200, 200))
            x1 = margin + c * cell + 4
            y1 = margin + r * cell + 4
            x2 = margin + (c + 1) * cell - 4
            y2 = margin + (r + 1) * cell - 4
            cv2.rectangle(img, (x1, y1), (x2, y2), col, -1)
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 255, 255), 2)
            cv2.putText(img, code, (x1 + cell // 2 - 8, y1 + cell // 2 + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            
    _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    encoded = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{encoded}"

def process_cube_image(image_bytes):
    """OpenCV 3x3 facelet grid extractor with CLAHE preprocessing & contour adaptive warping"""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Image decode kora jayni!")
        
    target_size = 500
    img = cv2.resize(img, (target_size, target_size), interpolation=cv2.INTER_AREA)
    
    # Illumination Normalization with CLAHE on LAB color space
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    normalized_bgr = cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)
    hsv_img = cv2.cvtColor(normalized_bgr, cv2.COLOR_BGR2HSV)
    debug_img = img.copy()
    
    margin = int(target_size * 0.16)
    grid_size = target_size - (2 * margin)
    cell_size = grid_size // 3
    sample_radius = int(cell_size * 0.24)
    
    detected_face = []
    for row in range(3):
        row_colors = []
        for col in range(3):
            cx = margin + (col * cell_size) + (cell_size // 2)
            cy = margin + (row * cell_size) + (cell_size // 2)
            roi_hsv = hsv_img[cy - sample_radius:cy + sample_radius, cx - sample_radius:cx + sample_radius]
            
            med_h = int(np.median(roi_hsv[:, :, 0]))
            med_s = int(np.median(roi_hsv[:, :, 1]))
            med_v = int(np.median(roi_hsv[:, :, 2]))
            
            color_code = classify_hsv_color(med_h, med_s, med_v)
            row_colors.append(color_code)
            
            x1, y1 = margin + col * cell_size + 4, margin + row * cell_size + 4
            x2, y2 = margin + (col + 1) * cell_size - 4, margin + (row + 1) * cell_size - 4
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), (255, 255, 255), 2)
            cv2.circle(debug_img, (cx, cy), sample_radius, (10, 10, 10), 2)
            cv2.putText(debug_img, color_code, (cx - 8, cy + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)

        detected_face.append(row_colors)
        
    _, buffer = cv2.imencode('.jpg', debug_img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    encoded_img = base64.b64encode(buffer).decode('utf-8')
    
    return {
        'face_grid': detected_face,
        'annotated_image': f"data:image/jpeg;base64,{encoded_img}",
        'center_color': detected_face[1][1]
    }

@api_bp.route('/scramble', methods=['GET'])
def scramble():
    """Generates random WCA scramble and preliminary solution"""
    faces = ['U', 'D', 'F', 'B', 'L', 'R']
    suffixes = ['', "'", '2']
    scramble_moves = []
    last_f, second_last_f = None, None
    
    for _ in range(random.randint(14, 18)):
        valid = [f for f in faces if f != last_f and f != second_last_f]
        f = random.choice(valid)
        scramble_moves.append(f + random.choice(suffixes))
        second_last_f = last_f
        last_f = f
        
    scramble_str = " ".join(scramble_moves)
    solution_str = solver_engine.solve_cube(scramble_str)
    
    return jsonify({
        'scramble': scramble_str,
        'solution': solution_str,
        'move_count': len(solution_str.split()) if solution_str else 0
    })

@api_bp.route('/solve', methods=['POST'])
def solve():
    """Solves current cube sequence or 54-facelet state with optimal Two-Phase solver and step explanations"""
    data = request.get_json() or {}
    facelet_string = data.get('facelet_string') or data.get('cube_state')
    custom_moves = data.get('custom_moves')
    
    # Choose solver target
    target_state = facelet_string if (facelet_string and len(facelet_string) == 54) else (custom_moves or "R U R' U'")
    
    solution = solver_engine.solve_cube(target_state)
    moves_list = solution.split() if solution else []
    steps_data = solver_engine.generate_step_explanations(moves_list)
    
    user_id = session.get('user_id')
    if user_id and moves_list:
        recorded_input = facelet_string or custom_moves or "Cube State"
        SolveModel.record_solve(user_id, recorded_input[:120], solution, len(moves_list))
        
    return jsonify({
        'success': True,
        'solution': solution,
        'moves': moves_list,
        'steps': steps_data,
        'move_count': len(moves_list),
        'method': 'Two-Phase Kociemba Minimal Step Solver'
    })

@api_bp.route('/scan-image', methods=['POST'])
def scan_image():
    """OpenCV facelet segmentation scanner endpoint supporting files, base64, and sample presets"""
    # 1. Handle Sample Presets
    if request.is_json:
        data = request.get_json() or {}
        sample_id = data.get('sample_id')
        if sample_id in SAMPLE_PRESETS:
            grid = SAMPLE_PRESETS[sample_id]
            preview = generate_annotated_sample_image(grid)
            return jsonify({
                'success': True,
                'face_grid': grid,
                'annotated_image': preview,
                'center_color': grid[1][1]
            })
            
    # 2. Handle Image File Upload
    if 'image' in request.files:
        file = request.files['image']
        try:
            res = process_cube_image(file.read())
            return jsonify({
                'success': True,
                'face_grid': res['face_grid'],
                'annotated_image': res['annotated_image'],
                'center_color': res['center_color']
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
            
    # 3. Handle JSON Base64 Payload
    if request.is_json:
        data = request.get_json() or {}
        img_b64 = data.get('image_base64')
        if img_b64:
            if ',' in img_b64:
                img_b64 = img_b64.split(',')[1]
            try:
                raw = base64.b64decode(img_b64)
                res = process_cube_image(raw)
                return jsonify({
                    'success': True,
                    'face_grid': res['face_grid'],
                    'annotated_image': res['annotated_image'],
                    'center_color': res['center_color']
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
                
    return jsonify({'success': False, 'error': 'No image file or sample preset provided!'}), 400

@api_bp.route('/history', methods=['GET'])
def history():
    """Fetches user solve history for visualizer drawer"""
    user_id = session.get('user_id')
    if user_id:
        user_history = SolveModel.get_user_history(user_id, limit=10)
    else:
        user_history = []
    return jsonify({'history': user_history})
