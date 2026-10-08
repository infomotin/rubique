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
    """HSV color classifier helper for OpenCV pipeline"""
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
    return 'W'

def process_cube_image(image_bytes):
    """OpenCV 3x3 facelet grid extractor"""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Image decode kora jayni!")
        
    target_size = 500
    img = cv2.resize(img, (target_size, target_size), interpolation=cv2.INTER_AREA)
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    debug_img = img.copy()
    
    margin = int(target_size * 0.15)
    grid_size = target_size - (2 * margin)
    cell_size = grid_size // 3
    sample_radius = int(cell_size * 0.22)
    
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
            cv2.circle(debug_img, (cx, cy), sample_radius, (20, 20, 20), 2)
            cv2.putText(debug_img, color_code, (cx - 7, cy + 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        detected_face.append(row_colors)
        
    _, buffer = cv2.imencode('.jpg', debug_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
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
    """Solves current cube sequence and records solve to user profile database if logged in"""
    data = request.get_json() or {}
    custom_moves = data.get('custom_moves', 'R U R\' U\'')
    
    solution = solver_engine.solve_cube(custom_moves)
    moves_list = solution.split()
    
    user_id = session.get('user_id')
    if user_id:
        SolveModel.record_solve(user_id, custom_moves, solution, len(moves_list))
        
    return jsonify({
        'success': True,
        'solution': solution,
        'moves': moves_list,
        'move_count': len(moves_list)
    })

@api_bp.route('/scan-image', methods=['POST'])
def scan_image():
    """OpenCV facelet segmentation scanner endpoint"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image uploaded!'}), 400
        
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

@api_bp.route('/history', methods=['GET'])
def history():
    """Fetches user solve history for visualizer drawer"""
    user_id = session.get('user_id')
    if user_id:
        user_history = SolveModel.get_user_history(user_id, limit=10)
    else:
        user_history = []
    return jsonify({'history': user_history})
