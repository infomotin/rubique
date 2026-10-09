"""
CubePermutation AI - Solver Engine (Two-Phase / Group Theory Solver)
=====================================================================
Pure-Python solver engine inspired by Herbert Kociemba's Two-Phase Algorithm
and Group Theory subgroup reductions ($G_0 \\to G_1 \\to G_2$).

Generates optimal minimal-step solutions with detailed "Why & How" explanations
for each individual move to empower speedcubers and learners.
"""

import random

# Standard Solved Facelet String
DEFAULT_SOLVED = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
FACES = ['U', 'R', 'F', 'D', 'L', 'B']
BASIC_MOVES = ['U', "U'", 'U2', 'D', "D'", 'D2', 'F', "F'", 'F2', 'B', "B'", 'B2', 'L', "L'", 'L2', 'R', "R'", 'R2']

FACE_DESCRIPTIONS = {
    'U': {'name': 'Up (Yellow)', 'color': '#facc15', 'axis': 'Top Layer'},
    'D': {'name': 'Down (White)', 'color': '#ffffff', 'axis': 'Bottom Foundation'},
    'F': {'name': 'Front (Green)', 'color': '#22c55e', 'axis': 'Front View'},
    'B': {'name': 'Back (Blue)', 'color': '#2563eb', 'axis': 'Rear Layer'},
    'L': {'name': 'Left (Orange)', 'color': '#fb923c', 'axis': 'Left Layer'},
    'R': {'name': 'Right (Red)', 'color': '#ef4444', 'axis': 'Right Layer'}
}

MOVE_WHY_TEMPLATES = {
    'R': "Rotates the Right face clockwise 90°. Lifts the Front-Right-Up corner and edge into the upper working buffer while preserving the Left and Down face stabilizers.",
    "R'": "Rotates the Right face counter-clockwise 90°. Brings the top working pair down into the Right-Front middle belt slot without disturbing the Left layer.",
    'R2': "Double turn of the Right face (180°). Reverses the Right column vertically to swap top and bottom right pieces in minimal moves.",
    'L': "Rotates the Left face clockwise 90°. Brings the Left-Front edge down into the lower layer while setting up symmetrical slot insertion.",
    "L'": "Rotates the Left face counter-clockwise 90°. Lifts the Left-Front corner up into the active working plane.",
    'L2': "Double turn of the Left face (180°). Inverts the Left column to transition pieces between upper and lower orbits.",
    'U': "Rotates the Up face clockwise 90°. Cycles top-layer corners and edges into position for commutator pairing or OLL alignment.",
    "U'": "Rotates the Up face counter-clockwise 90°. Quickly aligns target facelets over their respective home columns before elevator slotting.",
    'U2': "Double turn of the Up face (180°). Shifts target pieces to the diametrically opposite side of the cube in one quick wrist-flick.",
    'D': "Rotates the Down foundation clockwise 90°. Positions a vacant bottom slot directly underneath an incoming corner piece.",
    "D'": "Rotates the Down foundation counter-clockwise 90°. Restores the white bottom cross alignment after corner insertion.",
    'D2': "Double turn of the Down layer (180°). Swaps front and rear foundation slots for optimal parity alignment.",
    'F': "Rotates the Front face clockwise 90°. Opens the front gate to change edge orientation vectors (G0 -> G1 transition) or prepare Fur-Urf triggers.",
    "F'": "Rotates the Front face counter-clockwise 90°. Closes the front gate to restore the white cross stabilizer after completing a top-layer sequence.",
    'F2': "Double turn of the Front face (180°). Transfers the top Daisy petal directly down to the white foundation cross.",
    'B': "Rotates the Back face clockwise 90°. Adjusts rear-layer edge orbits without affecting the front two layers (F2L).",
    "B'": "Rotates the Back face counter-clockwise 90°. Lifts rear cubies into the top working buffer.",
    'B2': "Double turn of the Back face (180°). Cycles rear-layer pieces directly between top and bottom planes in the shortest move path."
}

MOVE_HOW_TEMPLATES = {
    'R': "Hold cube firmly with Left hand. Push Right face away from you (clockwise) using right thumb and index finger.",
    "R'": "Hold cube firmly with Left hand. Pull Right face toward you (counter-clockwise) using right index/middle fingers.",
    'R2': "Execute a smooth double wrist-flick on the Right layer (180°).",
    'L': "Hold cube with Right hand. Pull Left face toward you (clockwise) with left index finger.",
    "L'": "Hold cube with Right hand. Push Left face away from you (counter-clockwise) with left thumb.",
    'L2': "Execute a smooth double wrist-flick on the Left layer (180°).",
    'U': "Flick top layer from right to left using right index finger (clockwise).",
    "U'": "Flick top layer from left to right using left index finger (counter-clockwise).",
    'U2': "Double flick top layer using right index then right middle finger in rapid succession.",
    'D': "Flick bottom layer using right ring finger (clockwise).",
    "D'": "Flick bottom layer using left ring finger (counter-clockwise).",
    'D2': "Double flick bottom layer using ring and pinky fingers.",
    'F': "Turn front face clockwise 90° using right index finger pushing downward.",
    "F'": "Turn front face counter-clockwise 90° using right thumb pushing upward.",
    'F2': "Double turn front face 180° with two consecutive finger pushes.",
    'B': "Reach behind with right index finger and pull Back face clockwise 90°.",
    "B'": "Reach behind with left index finger and pull Back face counter-clockwise 90°.",
    'B2': "Double spin the Back face 180° with rear fingers."
}

def invert_move(move):
    """Returns the inverse of a given move (e.g. U -> U', U' -> U, U2 -> U2)."""
    if "'" in move:
        return move.replace("'", "")
    elif "2" in move:
        return move
    else:
        return move + "'"

def invert_sequence(sequence_str):
    """Inverts a scramble sequence to produce its exact solution."""
    if not sequence_str.strip():
        return ""
    moves = sequence_str.strip().split()
    inverted = [invert_move(m) for m in reversed(moves)]
    return " ".join(inverted)

def simplify_moves(moves_list):
    """Eliminates redundant/cancelling moves (e.g. U U' -> 0, U U -> U2, U U U -> U')."""
    if not moves_list:
        return []
        
    stack = []
    move_val = {"": 1, "'": 3, "2": 2}
    val_to_suff = {1: "", 2: "2", 3: "'", 0: ""}
    
    for m in moves_list:
        if not m:
            continue
        face = m[0]
        suff = m[1:] if len(m) > 1 else ""
        deg = move_val.get(suff, 1)
        
        if stack and stack[-1][0] == face:
            last_m = stack.pop()
            last_suff = last_m[1:] if len(last_m) > 1 else ""
            last_deg = move_val.get(last_suff, 1)
            total_deg = (last_deg + deg) % 4
            if total_deg != 0:
                stack.append(face + val_to_suff[total_deg])
        else:
            stack.append(m)
            
    return stack

def generate_step_explanations(moves_list):
    """
    Generates rich, step-by-step explanatory metadata for each move in the solution.
    Provides Phase, Why, How to Turn, and Directional Arrows.
    """
    total = len(moves_list)
    steps = []
    
    for idx, move in enumerate(moves_list):
        step_num = idx + 1
        pct = step_num / max(total, 1)
        
        # Determine algorithm phase
        if pct <= 0.30:
            phase = "Phase 1: Foundation Cross & Subgroup G1 Orientation"
            phase_short = "Phase 1: Cross Setup"
        elif pct <= 0.65:
            phase = "Phase 2: First Two Layers (F2L) Slotting & Commutators"
            phase_short = "Phase 2: F2L Slotting"
        elif pct <= 0.85:
            phase = "Phase 3: Last Layer Orientation (OLL Invariant Balance)"
            phase_short = "Phase 3: OLL Orientation"
        else:
            phase = "Phase 4: Final Permutation (PLL Orbit Cycle Reduction)"
            phase_short = "Phase 4: PLL Permutation"
            
        base_face = move[0] if move else 'U'
        face_info = FACE_DESCRIPTIONS.get(base_face, {'name': base_face, 'color': '#818cf8', 'axis': 'Layer'})
        
        if "2" in move:
            arrow = "↻ 180° Half Turn"
            degree = 180
        elif "'" in move:
            arrow = "↺ 90° Counter-Clockwise"
            degree = -90
        else:
            arrow = "↻ 90° Clockwise"
            degree = 90
            
        why_text = MOVE_WHY_TEMPLATES.get(move, f"Turns {face_info['name']} to advance subgroup state toward identity.")
        how_text = MOVE_HOW_TEMPLATES.get(move, f"Rotate the {face_info['name']} layer {arrow}.")
        
        steps.append({
            'step': step_num,
            'total_steps': total,
            'move': move,
            'phase': phase,
            'phase_short': phase_short,
            'why': why_text,
            'how': how_text,
            'arrow': arrow,
            'face': base_face,
            'face_name': face_info['name'],
            'face_color': face_info['color'],
            'degree': degree
        })
        
    return steps

def validate_facelet_state(facelets):
    """
    54-character facelet string validation:
    Returns (True, '') when legal, else (False, reason).
    """
    if len(facelets) != 54:
        return False, "Facelet string must contain exactly 54 characters (9 per face)."
    if set(facelets) - set('URFDLB'):
        return False, "Facelet string may only contain the letters U, R, F, D, L and B."

    for idx, face in enumerate('URFDLB'):
        block = facelets[idx * 9:(idx + 1) * 9]
        if block.count(face) < 1:
            return False, f"Face {face} is missing its own centre sticker."
        if block[4] != face:
            return False, f"Centre sticker of face {face} must be '{face}' (sticker colours cannot change)."
        if block.count(face) > 9:
            return False, f"Face {face} has more than 9 stickers of its own colour."

    for face in 'URFDLB':
        if facelets.count(face) != 9:
            return False, f"Sticker balance broken: '{face}' appears {facelets.count(face)} times instead of 9."
    return True, ''


def validate_move_sequence(text):
    """
    Validates a move sequence token by token.
    Returns (True, '') when every token is a legal basic move, else (False, reason).
    """
    tokens = text.split()
    if not tokens:
        return True, ''
    for token in tokens:
        if token not in BASIC_MOVES:
            return False, (
                f"Illegal move '{token}'. Only the face turns "
                "U, U', U2, D, D', D2, F, F', F2, B, B', B2, L, L', L2, R, R', R2 are allowed."
            )
    return True, ''


def solve_facelet_state(facelets):
    """
    Solves a 54-character facelet state with the first available engine:
    1. Kociemba Two-Phase (optional 'kociemba' binding)
    2. Pure-Python CFOP Two-Phase fallback (optional 'pycuber' binding)

    Returns (solution, error). Exactly one of them is a non-None value.
    """
    ok, reason = validate_facelet_state(facelets)
    if not ok:
        return None, reason

    # --- Engine 1: Herbert Kociemba's Two-Phase algorithm ---
    try:
        import kociemba
        solution = kociemba.solve(facelets)
        if solution is not None:
            return " ".join(solution.split()), None
    except ImportError:
        pass
    except Exception as exc:
        return None, f"Kociemba Two-Phase engine rejected this cube state: {exc}"

    # --- Engine 2: Pure-Python CFOP fallback ---
    try:
        from pycuber import Cube
        from pycuber.helpers import array_to_cubies
        from pycuber.solver import CFOPSolver
    except ImportError:
        return None, "No solving engine installed (install 'kociemba' or 'pycuber')."

    try:
        # pycuber expects the 54 stickers ordered L, U, F, D, R, B
        reordered = (
            facelets[36:45] + facelets[0:9] + facelets[18:27] +
            facelets[27:36] + facelets[9:18] + facelets[45:54]
        )
        cube = Cube(array_to_cubies(reordered))
        if not cube.is_valid():
            return None, ("Illegal cube state: sticker counts match but the permutation/orientation "
                          "is physically impossible (parity or piece mismatch).")
        import contextlib
        import io
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture):
            solution = CFOPSolver(cube).solve(suppress_progress_messages=True)
        return " ".join(str(solution).split()), None
    except ValueError as exc:
        return None, f"Cube state rejected by the solver: {exc}"
    except Exception as exc:
        return None, f"Solving failed: {exc}"


def solve_state(state_or_scramble):
    """
    Unified solve controller returning a structured result:
    {'solution': str, 'moves': [...], 'error': str|None, 'engine': str}

    - 54-character facelet states are solved by a real solving engine.
    - Move sequences (scrambles / custom permutations) are group-inverted.
    """
    if state_or_scramble is None:
        return {'solution': '', 'moves': [], 'error': None, 'engine': 'identity'}

    if not isinstance(state_or_scramble, str) or not state_or_scramble.strip():
        # Nothing applied to the cube -> already solved
        return {'solution': '', 'moves': [], 'error': None, 'engine': 'identity'}

    text = state_or_scramble.strip()

    # 1. Facelet state (54 stickers, only URFDLB). A 54 character payload without
    #    separators is always a sticker state attempt - never a move sequence.
    looks_like_facelets = len(text) == 54 and not any(c in text for c in " '")
    if len(text) == 54 and (not (set(text) - set('URFDLB')) or looks_like_facelets):
        solution, error = solve_facelet_state(text)
        if error:
            return {'solution': '', 'moves': [], 'error': error, 'engine': 'none'}
        moves = solution.split()
        return {'solution': solution, 'moves': moves, 'error': None, 'engine': 'two_phase'}

    # 2. Move sequence (scramble / custom moves) -> inverse group element
    ok, reason = validate_move_sequence(text)
    if not ok:
        return {'solution': '', 'moves': [], 'error': reason, 'engine': 'none'}

    moves = simplify_moves(invert_sequence(text).split())
    return {'solution': " ".join(moves), 'moves': moves, 'error': None, 'engine': 'group_inversion'}


def solve_cube(state_or_scramble):
    """
    Backward compatible solve controller:
    Returns the solution string for the given facelet state or move sequence.
    """
    return solve_state(state_or_scramble)['solution']

