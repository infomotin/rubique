"""
CubePermutation AI - Custom Cube Builder & Workshop Controller (MVC Architecture)
=================================================================================
Dedicated Controller for:
- 10 Rubik's Cube Shape Archetypes (Particula-tech knowledge base)
- Custom Color Palettes & Texture Definition
- Kinematic Rearrangement & Scrambler
- Solvability & Mathematical Parity Verification
- Public & Private Clan Challenges & Group Mentions
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.custom_cube_model import CustomCubeModel, SUPPORTED_SHAPES
from models.user_model import UserModel
from models.community_model import CommunityModel
from controllers.auth_controller import login_required

custom_cube_bp = Blueprint('custom_cubes', __name__, url_prefix='/custom-cubes')

@custom_cube_bp.route('/')
@login_required
def index():
    """Custom Cubes Workshop Hub & Gallery"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    user_cubes = CustomCubeModel.get_user_cubes(user_id)
    public_cubes = CustomCubeModel.get_public_cubes(limit=30)
    challenges = CustomCubeModel.get_group_challenges(limit=30)
    groups = CommunityModel.get_all_groups()

    return render_template(
        'custom_cubes/gallery.html',
        user=user,
        user_cubes=user_cubes,
        public_cubes=public_cubes,
        challenges=challenges,
        groups=groups,
        supported_shapes=SUPPORTED_SHAPES
    )

@custom_cube_bp.route('/builder')
@login_required
def builder():
    """Full Standalone Interactive Custom Cube Studio with 10 Shapes & Color Engine"""
    user_id = session.get('user_id')
    user = UserModel.find_by_id(user_id)
    initial_shape = request.args.get('shape', 'classic_3x3')
    if initial_shape not in SUPPORTED_SHAPES:
        initial_shape = 'classic_3x3'

    user_cubes = CustomCubeModel.get_user_cubes(user_id)
    groups = CommunityModel.get_all_groups()

    return render_template(
        'custom_cubes/builder.html',
        user=user,
        initial_shape=initial_shape,
        supported_shapes=SUPPORTED_SHAPES,
        user_cubes=user_cubes,
        groups=groups
    )

@custom_cube_bp.route('/save', methods=['POST'])
@login_required
def save_cube():
    """Saves a subscriber's custom built cube"""
    user_id = session.get('user_id')
    name = request.form.get('name', '').strip() or "My Custom Puzzle"
    shape_type = request.form.get('shape_type', 'classic_3x3').strip()
    description = request.form.get('description', '').strip()
    color_scheme = request.form.get('color_scheme', '').strip()
    cube_state = request.form.get('cube_state', '').strip()
    scramble = request.form.get('scramble', '').strip()
    status = request.form.get('status', 'unsolved').strip()
    is_public = 1 if request.form.get('is_public') in ('1', 'true', 'on') else 0

    cube_id = CustomCubeModel.save_cube(
        user_id=user_id,
        name=name,
        shape_type=shape_type,
        description=description,
        color_scheme=color_scheme,
        cube_state=cube_state,
        scramble=scramble,
        status=status,
        is_public=is_public
    )

    # Optional Clan challenge mention
    challenge_group_id = request.form.get('challenge_group_id')
    challenge_note = request.form.get('challenge_note', '').strip()
    if challenge_group_id and challenge_group_id.isdigit() and int(challenge_group_id) > 0:
        try:
            CustomCubeModel.challenge_group(cube_id, int(challenge_group_id), user_id, challenge_note)
            flash(f'Custom cube "{name}" saved and Clan Challenge launched in study group chat!', 'success')
            return redirect(url_for('custom_cubes.index'))
        except Exception:
            pass

    flash(f'Custom cube "{name}" successfully saved to your workshop collection!', 'success')
    return redirect(url_for('custom_cubes.index'))

@custom_cube_bp.route('/create-group', methods=['POST'])
@login_required
def create_group():
    """Quick Clan creation directly inside the Custom Cube Workshop"""
    user_id = session.get('user_id')
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    is_private = 1 if request.form.get('is_private') in ('1', 'true', 'on') else 0
    passcode = request.form.get('passcode', '').strip() or None
    
    if name:
        CommunityModel.create_group(name, description, is_private, passcode, created_by=user_id)
        flash(f'Study Clan "{name}" successfully created! You can now mention and challenge it to solve custom puzzles.', 'success')
    else:
        flash('Clan name is required.', 'error')
    return redirect(url_for('custom_cubes.builder'))

@custom_cube_bp.route('/delete/<int:cube_id>', methods=['POST'])
@login_required
def delete_cube(cube_id):
    """Deletes custom cube if owned by current user"""
    user_id = session.get('user_id')
    CustomCubeModel.delete_cube(cube_id, user_id)
    flash('Custom puzzle deleted from your collection.', 'info')
    return redirect(url_for('custom_cubes.index'))

@custom_cube_bp.route('/challenge-group', methods=['POST'])
@login_required
def challenge_group():
    """Mentions and challenges a study clan / group to solve a custom cube problem"""
    user_id = session.get('user_id')
    cube_id = request.form.get('cube_id')
    group_id = request.form.get('group_id')
    challenge_note = request.form.get('challenge_note', '').strip()

    try:
        cube_id = int(cube_id)
        group_id = int(group_id)
    except (TypeError, ValueError):
        cube_id = 0
        group_id = 0

    if cube_id and group_id:
        CustomCubeModel.challenge_group(cube_id, group_id, user_id, challenge_note)
        flash('Puzzle challenge dispatched! Group members have been tagged & notified in clan chat.', 'success')
    else:
        flash('Please select both a valid cube and target group.', 'error')
    return redirect(url_for('custom_cubes.index'))

@custom_cube_bp.route('/solve-challenge/<int:challenge_id>', methods=['POST'])
@login_required
def solve_challenge(challenge_id):
    """Submits solution algorithm for an open group challenge"""
    user_id = session.get('user_id')
    solution = request.form.get('solution', '').strip()
    if solution:
        CustomCubeModel.solve_challenge(challenge_id, user_id, solution)
        flash('Congratulations! Your solution algorithm has been verified and registered on the Clan Challenge!', 'success')
    else:
        flash('Please provide a valid solution move sequence.', 'error')
    return redirect(url_for('custom_cubes.index'))

@custom_cube_bp.route('/api/<int:cube_id>')
@login_required
def get_cube_api(cube_id):
    """Returns custom cube details as JSON"""
    cube = CustomCubeModel.get_cube_by_id(cube_id)
    if cube:
        return jsonify({'success': True, 'cube': cube})
    return jsonify({'success': False, 'error': 'Cube not found'}), 404
