"""
CubePermutation AI - Custom Cube Builder & Workshop Model (MVC Pattern)
=======================================================================
Handles Custom Rubik's Cubes (10 Shapes/Archetypes, Custom Color Schemes,
Permutation States, Solved/Unsolved Status, Group Mentions & Challenges).
"""

import json
from .db import query_one, query_all, execute_insert, execute_update

# 10 Supported Shape Archetypes & Presets
SUPPORTED_SHAPES = {
    'classic_3x3': {
        'id': 'classic_3x3',
        'name': "Classic 3x3 Rubik's Cube",
        'badge': 'WCA Standard',
        'faces': 6,
        'stickers_per_face': 9,
        'total_stickers': 54,
        'icon': 'fa-solid fa-cube',
        'tag': '3x3x3',
        'desc': 'The iconic 1974 masterpiece by Ernő Rubik. 43 quintillion permutations.',
        'default_palette': ['#facc15', '#ffffff', '#22c55e', '#3b82f6', '#f97316', '#ef4444'],
        'face_names': ['Up (Yellow)', 'Down (White)', 'Front (Green)', 'Back (Blue)', 'Left (Orange)', 'Right (Red)']
    },
    'mini_2x2': {
        'id': 'mini_2x2',
        'name': "2x2 Rubik's Cube (Pocket Cube)",
        'badge': 'Pocket Mini',
        'faces': 6,
        'stickers_per_face': 4,
        'total_stickers': 24,
        'icon': 'fa-solid fa-cubes',
        'tag': '2x2x2',
        'desc': 'Corner-only mini puzzle with 3.67 million permutations. Rapid burst solving.',
        'default_palette': ['#facc15', '#ffffff', '#22c55e', '#3b82f6', '#f97316', '#ef4444'],
        'face_names': ['Up', 'Down', 'Front', 'Back', 'Left', 'Right']
    },
    'gocube_3x3': {
        'id': 'gocube_3x3',
        'name': 'GoCube Smart 3x3 & 2x2',
        'badge': 'Smart Connected',
        'faces': 6,
        'stickers_per_face': 9,
        'total_stickers': 54,
        'icon': 'fa-solid fa-microchip',
        'tag': 'Bluetooth IMU',
        'desc': 'Smart connected speedcube with beveled ergonomic corners, internal IMU gyro and LED illumination.',
        'default_palette': ['#38bdf8', '#e0e7ff', '#10b981', '#6366f1', '#f59e0b', '#f43f5e'],
        'face_names': ['Cyber Cyan', 'Pure White', 'Electric Lime', 'Neon Blue', 'Solar Amber', 'Laser Rose']
    },
    'rubiks_revenge_4x4': {
        'id': 'rubiks_revenge_4x4',
        'name': "4x4 Rubik's Revenge & 5x5 Professor's Cube",
        'badge': 'Even & Odd Big Cubes',
        'faces': 6,
        'stickers_per_face': 16,
        'total_stickers': 96,
        'icon': 'fa-solid fa-table-cells',
        'tag': '4x4 & 5x5',
        'desc': 'Centerless 4x4 with OLL/PLL parity algorithms plus the 5x5 classic professor expansion.',
        'default_palette': ['#facc15', '#ffffff', '#22c55e', '#3b82f6', '#f97316', '#ef4444'],
        'face_names': ['Top', 'Bottom', 'Front', 'Back', 'Left', 'Right']
    },
    'big_cubes_6x6_7x7': {
        'id': 'big_cubes_6x6_7x7',
        'name': '6x6 and 7x7 Multi-Layer Big Cubes',
        'badge': 'High Order Mega',
        'faces': 6,
        'stickers_per_face': 36,
        'total_stickers': 216,
        'icon': 'fa-solid fa-border-all',
        'tag': '6x6 & 7x7',
        'desc': 'Multi-slice reduction puzzles requiring center building, edge pairing, and inner-slice commutators.',
        'default_palette': ['#fde047', '#f8fafc', '#16a34a', '#2563eb', '#ea580c', '#dc2626'],
        'face_names': ['Top', 'Bottom', 'Front', 'Back', 'Left', 'Right']
    },
    'pyraminx': {
        'id': 'pyraminx',
        'name': 'Pyraminx Tetrahedron',
        'badge': 'Tetrahedron',
        'faces': 4,
        'stickers_per_face': 9,
        'total_stickers': 36,
        'icon': 'fa-solid fa-play text-rotate-270',
        'tag': 'Tetrahedral',
        'desc': '4-sided regular tetrahedron puzzle invented by Uwe Mèffert. Axial vertex & tip twist mechanics.',
        'default_palette': ['#facc15', '#22c55e', '#3b82f6', '#ef4444'],
        'face_names': ['Up (Yellow)', 'Front (Green)', 'Left (Blue)', 'Right (Red)']
    },
    'mirror_cube': {
        'id': 'mirror_cube',
        'name': 'Mirror Blocks (Bump Cube)',
        'badge': 'Monochrome Shape-Shifter',
        'faces': 6,
        'stickers_per_face': 9,
        'total_stickers': 54,
        'icon': 'fa-solid fa-clone',
        'tag': 'Shape-Shifting',
        'desc': 'Uniform brushed silver/gold foil with asymmetrical cubie sizes. Solved purely by geometry rather than color.',
        'default_palette': ['#e2e8f0', '#cbd5e1', '#94a3b8', '#64748b', '#475569', '#334155'],
        'face_names': ['Silver High', 'Silver Low', 'Silver Deep', 'Silver Wide', 'Silver Left', 'Silver Right']
    },
    'megaminx': {
        'id': 'megaminx',
        'name': 'Megaminx Dodecahedron',
        'badge': 'Dodecahedron (12 Faces)',
        'faces': 12,
        'stickers_per_face': 11,
        'total_stickers': 132,
        'icon': 'fa-solid fa-gem',
        'tag': '12 Faces',
        'desc': 'Star-dodecahedron with 12 pentagonal faces and 50 movable pieces. WCA sanctioned speed puzzle.',
        'default_palette': [
            '#ffffff', '#facc15', '#22c55e', '#3b82f6', '#ef4444', '#a855f7',
            '#f97316', '#06b6d4', '#ec4899', '#84cc16', '#64748b', '#b45309'
        ],
        'face_names': ['White', 'Yellow', 'Green', 'Blue', 'Red', 'Purple', 'Orange', 'Cyan', 'Pink', 'Lime', 'Grey', 'Bronze']
    },
    'skewb': {
        'id': 'skewb',
        'name': 'Skewb (Corner-Turning Cube)',
        'badge': 'Deep-Cut Hexahedron',
        'faces': 6,
        'stickers_per_face': 5,
        'total_stickers': 30,
        'icon': 'fa-solid fa-dice-d6',
        'tag': 'Deep-Cut',
        'desc': 'Cube with four cutting planes passing through center, causing deep-cut corner rotation instead of face slice turns.',
        'default_palette': ['#facc15', '#ffffff', '#22c55e', '#3b82f6', '#f97316', '#ef4444'],
        'face_names': ['Top', 'Bottom', 'Front', 'Back', 'Left', 'Right']
    },
    'ghost_cube': {
        'id': 'ghost_cube',
        'name': 'Ghost Cube (Asymmetric Stealth)',
        'badge': 'Master Shape-Shifter',
        'faces': 6,
        'stickers_per_face': 9,
        'total_stickers': 54,
        'icon': 'fa-solid fa-ghost',
        'tag': 'Misaligned Axes',
        'desc': 'Cut with misaligned rotational layers. Solvable only when first rotated out of cube shape into mid-turn offset.',
        'default_palette': ['#0f172a', '#1e293b', '#334155', '#475569', '#64748b', '#94a3b8'],
        'face_names': ['Carbon Prime', 'Slate Offset', 'Titanium Axis', 'Shadow Grid', 'Graphite Layer', 'Phantom Core']
    }
}

class CustomCubeModel:

    @staticmethod
    def get_supported_shapes():
        """Returns the dictionary of all 10 prebuilt shape archetypes"""
        return SUPPORTED_SHAPES

    @staticmethod
    def save_cube(user_id, name, shape_type, description='', color_scheme='', cube_state='', scramble='', status='unsolved', is_public=1):
        """Saves a new custom cube blueprint created by a subscriber"""
        if not shape_type or shape_type not in SUPPORTED_SHAPES:
            shape_type = 'classic_3x3'
            
        return execute_insert(
            """INSERT INTO custom_cubes 
               (user_id, name, shape_type, description, color_scheme, cube_state, scramble, status, is_public)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            """INSERT INTO custom_cubes 
               (user_id, name, shape_type, description, color_scheme, cube_state, scramble, status, is_public)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, name, shape_type, description, color_scheme, cube_state, scramble, status, 1 if is_public else 0)
        )

    @staticmethod
    def update_cube(cube_id, user_id, name, shape_type, description='', color_scheme='', cube_state='', scramble='', status='unsolved', is_public=1):
        """Updates an existing custom cube owned by user"""
        return execute_update(
            """UPDATE custom_cubes
               SET name = %s, shape_type = %s, description = %s, color_scheme = %s, 
                   cube_state = %s, scramble = %s, status = %s, is_public = %s
               WHERE id = %s AND user_id = %s""",
            """UPDATE custom_cubes
               SET name = ?, shape_type = ?, description = ?, color_scheme = ?, 
                   cube_state = ?, scramble = ?, status = ?, is_public = ?
               WHERE id = ? AND user_id = ?""",
            (name, shape_type, description, color_scheme, cube_state, scramble, status, 1 if is_public else 0, cube_id, user_id)
        )

    @staticmethod
    def get_user_cubes(user_id):
        """Fetches all custom cubes created by a specific user"""
        return query_all(
            """SELECT c.*, u.username as creator_name, u.avatar_color,
               (SELECT COUNT(*) FROM cube_group_challenges ch WHERE ch.cube_id = c.id) as challenge_count
               FROM custom_cubes c
               JOIN users u ON c.user_id = u.id
               WHERE c.user_id = %s
               ORDER BY c.created_at DESC""",
            """SELECT c.*, u.username as creator_name, u.avatar_color,
               (SELECT COUNT(*) FROM cube_group_challenges ch WHERE ch.cube_id = c.id) as challenge_count
               FROM custom_cubes c
               JOIN users u ON c.user_id = u.id
               WHERE c.user_id = ?
               ORDER BY c.created_at DESC""",
            (user_id,)
        )

    @staticmethod
    def get_public_cubes(limit=25):
        """Fetches public custom cubes created across the community"""
        return query_all(
            """SELECT c.*, u.username as creator_name, u.avatar_color,
               (SELECT COUNT(*) FROM cube_group_challenges ch WHERE ch.cube_id = c.id) as challenge_count
               FROM custom_cubes c
               JOIN users u ON c.user_id = u.id
               WHERE c.is_public = 1
               ORDER BY c.created_at DESC LIMIT %s""",
            """SELECT c.*, u.username as creator_name, u.avatar_color,
               (SELECT COUNT(*) FROM cube_group_challenges ch WHERE ch.cube_id = c.id) as challenge_count
               FROM custom_cubes c
               JOIN users u ON c.user_id = u.id
               WHERE c.is_public = 1
               ORDER BY c.created_at DESC LIMIT ?""",
            (limit,)
        )

    @staticmethod
    def get_cube_by_id(cube_id):
        """Fetches a single custom cube blueprint by ID"""
        return query_one(
            """SELECT c.*, u.username as creator_name, u.avatar_color
               FROM custom_cubes c
               JOIN users u ON c.user_id = u.id
               WHERE c.id = %s""",
            """SELECT c.*, u.username as creator_name, u.avatar_color
               FROM custom_cubes c
               JOIN users u ON c.user_id = u.id
               WHERE c.id = ?""",
            (cube_id,)
        )

    @staticmethod
    def delete_cube(cube_id, user_id):
        """Deletes a custom cube if owned by user"""
        return execute_update(
            "DELETE FROM custom_cubes WHERE id = %s AND user_id = %s",
            "DELETE FROM custom_cubes WHERE id = ? AND user_id = ?",
            (cube_id, user_id)
        )

    # -------------------------------------------------------------------------
    # GROUP MENTION & PUZZLE CHALLENGES
    # -------------------------------------------------------------------------
    @staticmethod
    def challenge_group(cube_id, group_id, user_id, challenge_note=''):
        """Mentions and challenges a study clan / group to solve a custom puzzle state"""
        # 1. Insert into challenges table
        challenge_id = execute_insert(
            """INSERT INTO cube_group_challenges (cube_id, group_id, user_id, challenge_note, status)
               VALUES (%s, %s, %s, %s, 'open')""",
            """INSERT INTO cube_group_challenges (cube_id, group_id, user_id, challenge_note, status)
               VALUES (?, ?, ?, ?, 'open')""",
            (cube_id, group_id, user_id, challenge_note)
        )

        # 2. Automatically dispatch an announcement into the group chat feed
        cube = CustomCubeModel.get_cube_by_id(cube_id)
        cube_name = cube['name'] if cube else f"Custom Cube #{cube_id}"
        shape_info = SUPPORTED_SHAPES.get(cube['shape_type'] if cube else 'classic_3x3', {})
        shape_title = shape_info.get('name', 'Custom Cube')
        
        chat_msg = (
            f"🎯 [NEW PUZZLE CHALLENGE] @clan! I created a custom {shape_title}: \"{cube_name}\"!\n"
            f"Note: {challenge_note or 'Can your clan find a solution algorithm?'}\n"
            f"👉 Challenge #{challenge_id} is now LIVE in the Clan Workshop."
        )
        
        execute_insert(
            """INSERT INTO chat_messages (sender_id, receiver_id, group_id, message)
               VALUES (%s, NULL, %s, %s)""",
            """INSERT INTO chat_messages (sender_id, receiver_id, group_id, message)
               VALUES (?, NULL, ?, ?)""",
            (user_id, group_id, chat_msg)
        )

        return challenge_id

    @staticmethod
    def get_group_challenges(group_id=None, limit=20):
        """Fetches active group challenges with cube and creator metadata"""
        if group_id:
            return query_all(
                """SELECT ch.*, c.name as cube_name, c.shape_type, c.color_scheme, c.cube_state, c.scramble,
                          u.username as challenger_name, u.avatar_color as challenger_avatar,
                          g.name as group_name, g.is_private as group_is_private,
                          s.username as solver_name
                   FROM cube_group_challenges ch
                   JOIN custom_cubes c ON ch.cube_id = c.id
                   JOIN users u ON ch.user_id = u.id
                   JOIN chat_groups g ON ch.group_id = g.id
                   LEFT JOIN users s ON ch.solver_id = s.id
                   WHERE ch.group_id = %s
                   ORDER BY ch.created_at DESC LIMIT %s""",
                """SELECT ch.*, c.name as cube_name, c.shape_type, c.color_scheme, c.cube_state, c.scramble,
                          u.username as challenger_name, u.avatar_color as challenger_avatar,
                          g.name as group_name, g.is_private as group_is_private,
                          s.username as solver_name
                   FROM cube_group_challenges ch
                   JOIN custom_cubes c ON ch.cube_id = c.id
                   JOIN users u ON ch.user_id = u.id
                   JOIN chat_groups g ON ch.group_id = g.id
                   LEFT JOIN users s ON ch.solver_id = s.id
                   WHERE ch.group_id = ?
                   ORDER BY ch.created_at DESC LIMIT ?""",
                (group_id, limit)
            )
        else:
            return query_all(
                """SELECT ch.*, c.name as cube_name, c.shape_type, c.color_scheme, c.cube_state, c.scramble,
                          u.username as challenger_name, u.avatar_color as challenger_avatar,
                          g.name as group_name, g.is_private as group_is_private,
                          s.username as solver_name
                   FROM cube_group_challenges ch
                   JOIN custom_cubes c ON ch.cube_id = c.id
                   JOIN users u ON ch.user_id = u.id
                   JOIN chat_groups g ON ch.group_id = g.id
                   LEFT JOIN users s ON ch.solver_id = s.id
                   ORDER BY ch.created_at DESC LIMIT %s""",
                """SELECT ch.*, c.name as cube_name, c.shape_type, c.color_scheme, c.cube_state, c.scramble,
                          u.username as challenger_name, u.avatar_color as challenger_avatar,
                          g.name as group_name, g.is_private as group_is_private,
                          s.username as solver_name
                   FROM cube_group_challenges ch
                   JOIN custom_cubes c ON ch.cube_id = c.id
                   JOIN users u ON ch.user_id = u.id
                   JOIN chat_groups g ON ch.group_id = g.id
                   LEFT JOIN users s ON ch.solver_id = s.id
                   ORDER BY ch.created_at DESC LIMIT ?""",
                (limit,)
            )

    @staticmethod
    def solve_challenge(challenge_id, solver_id, solution):
        """Marks a group challenge as solved by a member"""
        return execute_update(
            """UPDATE cube_group_challenges 
               SET status = 'solved', solver_id = %s, solution = %s
               WHERE id = %s""",
            """UPDATE cube_group_challenges 
               SET status = 'solved', solver_id = ?, solution = ?
               WHERE id = ?""",
            (solver_id, solution, challenge_id)
        )
