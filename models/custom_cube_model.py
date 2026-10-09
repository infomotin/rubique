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
        'face_names': ['Up (Yellow)', 'Down (White)', 'Front (Green)', 'Back (Blue)', 'Left (Orange)', 'Right (Red)'],
        'dossier': {
            '1': {'title': '1. Mechanical Architecture & Geometry', 'icon': 'fa-solid fa-gears', 'color': 'cyan', 'content': 'Central 3-axis internal spider core with 6 spring-tensioned center spindles, 12 dual-anchoring edge feet, and 8 triangular corner bases. 26 visible cubies rotating around 3 orthogonal axes with sub-millisecond magnetic alignment.'},
            '2': {'title': '2. Mathematical Group Theory & State Space', 'icon': 'fa-solid fa-calculator', 'color': 'amber', 'content': 'Permutation group G = (Z_3^7 x Z_2^11) ⋊ (A_8 x A_12) with 43,252,003,274,489,856,000 states (~4.33x10^19). God\'s Number is proven to be exactly 20 moves in HTM (Half-Turn Metric) and 26 in QTM (Rokicki et al., 2010).'},
            '3': {'title': '3. Color & Aesthetic Surface Customization', 'icon': 'fa-solid fa-palette', 'color': 'pink', 'content': 'Standard WCA BOY scheme: Yellow opposite White, Green opposite Blue, Red opposite Orange. Dual-contrast theory optimizes high-speed sub-10 inspection. Fully customizable with UV-coated, frosted, or cyber neon palettes.'},
            '4': {'title': '4. Kinematics, Rearrangement & Parity', 'icon': 'fa-solid fa-code-compare', 'color': 'emerald', 'content': 'Strict alternating parity group A_n. Single face turns induce an even permutation of corners and edges simultaneously. Strict invariants: Corner orientation sum ≡ 0 (mod 3), Edge orientation sum ≡ 0 (mod 2). Isolated twists are impossible without mechanical disassembly.'},
            '5': {'title': '5. Clan/Group Challenge & Collaborative Solving', 'icon': 'fa-solid fa-users-rays', 'color': 'indigo', 'content': 'Clan workshops challenge members with FMC (Fewest Moves Challenge, target <26 moves), Blindfolded 3BLD M2/Pochmann buffer setups, and Roux block-building speed scrims. Broadcast scramble states to study clans in real-time.'}
        }
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
        'face_names': ['Up', 'Down', 'Front', 'Back', 'Left', 'Right'],
        'dossier': {
            '1': {'title': '1. Mechanical Architecture & Geometry', 'icon': 'fa-solid fa-gears', 'color': 'cyan', 'content': 'Corner-only mechanism engineered around a concealed asymmetric core enclosed within an enlarged stationary corner. 8 corner cubies with interlocking internal tracks and no exposed centers or edges.'},
            '2': {'title': '2. Mathematical Group Theory & State Space', 'icon': 'fa-solid fa-calculator', 'color': 'amber', 'content': 'Permutation group order |G| = 7! · 3^6 / 1 = 3,674,160 states. God\'s Number is 11 moves in HTM and 14 in QTM. Solved via Ortega, CLL, and EG-1/EG-2 algorithm sets.'},
            '3': {'title': '3. Color & Aesthetic Surface Customization', 'icon': 'fa-solid fa-palette', 'color': 'pink', 'content': 'Traditional 6-face coloring without fixed central markers. Visual recognition relies entirely on relative corner color juxtaposition and facelet pairing.'},
            '4': {'title': '4. Kinematics, Rearrangement & Parity', 'icon': 'fa-solid fa-code-compare', 'color': 'emerald', 'content': 'No edge parity is possible since edges do not exist. Corner orientation invariant holds: sum o_c ≡ 0 (mod 3). Ortega algorithms manipulate opposite face orientation and separation in two swift algorithmic sweeps.'},
            '5': {'title': '5. Clan/Group Challenge & Collaborative Solving', 'icon': 'fa-solid fa-users-rays', 'color': 'indigo', 'content': 'High-velocity clan sprints: sub-2.5 second benchmark challenges. Clans collaborate on 15-second one-look prediction (anticipating full first face, OLL, and PBL simultaneously).'}
        }
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
        'face_names': ['Cyber Cyan', 'Pure White', 'Electric Lime', 'Neon Blue', 'Solar Amber', 'Laser Rose'],
        'dossier': {
            '1': {'title': '1. Mechanical Architecture & Geometry', 'icon': 'fa-solid fa-gears', 'color': 'cyan', 'content': 'Beveled rounded cubie chassis embedding a 3-axis gyro IMU, contact-free Hall effect magnetic tracking sensors on every face spindle, 60Hz telemetry processor, and rechargeable lithium cell with internal RGB LED light guides.'},
            '2': {'title': '2. Mathematical Group Theory & State Space', 'icon': 'fa-solid fa-calculator', 'color': 'amber', 'content': 'Real-time orientation quaternions map into digital twin permutation matrices P(t). Instantaneous Kociemba 2-phase solution computation in under 15ms directly on device telemetry feeds.'},
            '3': {'title': '3. Color & Aesthetic Surface Customization', 'icon': 'fa-solid fa-palette', 'color': 'pink', 'content': 'Cyber Neon futuristic palette (Cyan, Neon Blue, Electric Lime, Laser Rose) with glowing translucent facelet borders and reactive LED pulse cues signifying algorithm execution correctness.'},
            '4': {'title': '4. Kinematics, Rearrangement & Parity', 'icon': 'fa-solid fa-code-compare', 'color': 'emerald', 'content': 'Sub-millisecond kinematic turn registration: logs TPS (Turns Per Second), split times for Cross/F2L/OLL/PLL, and automatically flags turn overshooting or slice misalignment.'},
            '5': {'title': '5. Clan/Group Challenge & Collaborative Solving', 'icon': 'fa-solid fa-users-rays', 'color': 'indigo', 'content': 'Synchronous 1v1 live head-to-head racing arena. Clans broadcast scramble seeds, track live millimeter delta feeds, and review AI move efficiency heatmaps.'}
        }
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
        'face_names': ['Top', 'Bottom', 'Front', 'Back', 'Left', 'Right'],
        'dossier': {
            '1': {'title': '1. Mechanical Architecture & Geometry', 'icon': 'fa-solid fa-gears', 'color': 'cyan', 'content': 'Concentric spherical core track with floating center tiles. 4x4 has no fixed center spindle (24 floating center pieces, 24 dedge wings, 8 corners). 5x5 includes 54 centers, 36 edge wings, and 8 corners.'},
            '2': {'title': '2. Mathematical Group Theory & State Space', 'icon': 'fa-solid fa-calculator', 'color': 'amber', 'content': '4x4 state space: 7.40x10^45 permutations. 5x5 state space: 2.83x10^74 permutations. Centers and edges form independent permutation orbits governed by inner-slice commutator subgroups [x,y] = xyx^-1y^-1.'},
            '3': {'title': '3. Color & Aesthetic Surface Customization', 'icon': 'fa-solid fa-palette', 'color': 'pink', 'content': 'Standard 6-face palette requiring memorization of the relative color scheme: with White on bottom, Green is to the right of Orange and opposite Blue. Center building sets the reference frame.'},
            '4': {'title': '4. Kinematics, Rearrangement & Parity', 'icon': 'fa-solid fa-code-compare', 'color': 'emerald', 'content': 'Even-cube parity phenomenon: OLL parity (single dedge flipped via r U2 x r U2 r U2 r\' U2 l U2 r\' U2 r U2 r\' U2 r\') and PLL parity (two opposite edge pairs swapped via 2R2 U2 2R2 u2 2R2 2U2) caused by quarter-slice turns inducing odd permutations in the edge wing orbit.'},
            '5': {'title': '5. Clan/Group Challenge & Collaborative Solving', 'icon': 'fa-solid fa-users-rays', 'color': 'indigo', 'content': 'Clan reduction scrims: practice Yau method (building White cross dedges before finishing last 4 centers) and 3-2-2-2-3 edge-pairing speed challenges with penalty points for parity algorithm lockups.'}
        }
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
        'face_names': ['Top', 'Bottom', 'Front', 'Back', 'Left', 'Right'],
        'dossier': {
            '1': {'title': '1. Mechanical Architecture & Geometry', 'icon': 'fa-solid fa-gears', 'color': 'cyan', 'content': 'Multi-tiered conical internal rails with interlocking anti-pop torpedo hooks. 6x6 contains 152 moving pieces; 7x7 has 218 moving pieces. Magnetic capsule stabilization across inner and outer slice channels.'},
            '2': {'title': '2. Mathematical Group Theory & State Space', 'icon': 'fa-solid fa-calculator', 'color': 'amber', 'content': 'State space exceeds 1.57x10^116 for 6x6 and 1.95x10^160 for 7x7. Multiple concentric center orbits: Oblique centers, Plus centers, and X-centers, each forming independent alternating permutation orbits.'},
            '3': {'title': '3. Color & Aesthetic Surface Customization', 'icon': 'fa-solid fa-palette', 'color': 'pink', 'content': 'High-contrast frosted finish preventing glare across massive 16-center (6x6) and 25-center (7x7) grids. Precision edge pairing requires distinct shade contrast between adjacent orange and red slices.'},
            '4': {'title': '4. Kinematics, Rearrangement & Parity', 'icon': 'fa-solid fa-code-compare', 'color': 'emerald', 'content': 'Multi-slice parity: inner wing flips and outer wing flips require targeted inner-slice slice-turn combinations (3r vs 2r). Commutator algorithms cycle 3 center pieces across distinct orbits without disturbing solved perimeters.'},
            '5': {'title': '5. Clan/Group Challenge & Collaborative Solving', 'icon': 'fa-solid fa-users-rays', 'color': 'indigo', 'content': 'Marathon relay challenges: Clan members tackle divided segments (Member A completes first 2 centers, Member B pairs last 4 centers, Member C handles Free Slice edge pairing, Member D executes 3x3 stage).'}
        }
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
        'face_names': ['Up (Yellow)', 'Front (Green)', 'Left (Blue)', 'Right (Red)'],
        'dossier': {
            '1': {'title': '1. Mechanical Architecture & Geometry', 'icon': 'fa-solid fa-gears', 'color': 'cyan', 'content': 'Regular tetrahedron with 4 triangular faces. Mechanical core features 4 internal vertex axles, 6 edge pieces, and 4 independent corner tips that rotate without altering internal orbits.'},
            '2': {'title': '2. Mathematical Group Theory & State Space', 'icon': 'fa-solid fa-calculator', 'color': 'amber', 'content': 'Group order is only 933,120 permutations (excluding the trivial tips, which add 3^4 = 81, totaling 75,582,480 states). God\'s Number is exactly 11 moves in optimal axial metric.'},
            '3': {'title': '3. Color & Aesthetic Surface Customization', 'icon': 'fa-solid fa-palette', 'color': 'pink', 'content': '4 primary colors (Yellow, Green, Blue, Red). Each triangular face features 9 triangular facets: 1 center, 3 inner edges, 3 outer edges, and 3 tip facets.'},
            '4': {'title': '4. Kinematics, Rearrangement & Parity', 'icon': 'fa-solid fa-code-compare', 'color': 'emerald', 'content': '120-degree axial turns around the tetrahedral vertices. Corner tips do not translate pieces. Edges can be permuted in 3-cycles or flipped in pairs. L4E (Last 4 Edges) methods solve the remaining state in 1 algorithm.'},
            '5': {'title': '5. Clan/Group Challenge & Collaborative Solving', 'icon': 'fa-solid fa-users-rays', 'color': 'indigo', 'content': 'Sprint speedcubing clan battles: sub-3 second solves. Clan members train in 1-look inspection, predicting the complete V-bottom stage and last-layer edge cycler case.'}
        }
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
        'face_names': ['Silver High', 'Silver Low', 'Silver Deep', 'Silver Wide', 'Silver Left', 'Silver Right'],
        'dossier': {
            '1': {'title': '1. Mechanical Architecture & Geometry', 'icon': 'fa-solid fa-gears', 'color': 'cyan', 'content': 'Traditional 3x3 mechanical core with an offset spindle intersection. Every single one of the 26 cubies has distinct volumetric dimensions (varied heights, widths, and depths), producing extreme jutting silhouettes when turned.'},
            '2': {'title': '2. Mathematical Group Theory & State Space', 'icon': 'fa-solid fa-calculator', 'color': 'amber', 'content': 'Mathematically isomorphic to the 3x3 Rubik group (4.33x10^19 states). God\'s Number is 20 HTM. However, human cognitive processing shifts completely from chromatic color recognition to 3D volumetric tactile depth perception.'},
            '3': {'title': '3. Color & Aesthetic Surface Customization', 'icon': 'fa-solid fa-palette', 'color': 'pink', 'content': 'Monochrome brushed metallic silver, mirror gold, or carbon foil. Solved state is achieved when all six faces form perfectly flush, planar bounding surfaces rather than matching color patches.'},
            '4': {'title': '4. Kinematics, Rearrangement & Parity', 'icon': 'fa-solid fa-code-compare', 'color': 'emerald', 'content': 'Turning any slice distorts the cubic shape into an asymmetric sculpture. Layer alignment requires identifying piece thickness: the thickest corner pairs with the deepest edge. Standard CFOP algorithms apply without modification.'},
            '5': {'title': '5. Clan/Group Challenge & Collaborative Solving', 'icon': 'fa-solid fa-users-rays', 'color': 'indigo', 'content': 'Blindfolded tactile clan trials: competitors solve without sight, identifying pieces solely by fingertip edge height steps. Scrambles produce dramatic obstacle challenges for study groups.'}
        }
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
        'face_names': ['White', 'Yellow', 'Green', 'Blue', 'Red', 'Purple', 'Orange', 'Cyan', 'Pink', 'Lime', 'Grey', 'Bronze'],
        'dossier': {
            '1': {'title': '1. Mechanical Architecture & Geometry', 'icon': 'fa-solid fa-gears', 'color': 'cyan', 'content': '12-sided regular dodecahedron with 12 fixed star-centers, 30 edge pieces, and 20 corner pieces (62 total pieces, 50 movable). Heavy internal spring-tensioned spider core with magnetic corner-edge positioning.'},
            '2': {'title': '2. Mathematical Group Theory & State Space', 'icon': 'fa-solid fa-calculator', 'color': 'amber', 'content': 'Enormous state space: 1.01x10^68 permutations (~100 million times larger than a 4x4). God\'s Number is estimated between 45 and 55 moves. Subgroup symmetry is Z_5 (72-degree pentagonal rotations).'},
            '3': {'title': '3. Color & Aesthetic Surface Customization', 'icon': 'fa-solid fa-palette', 'color': 'pink', 'content': '12 distinct vibrant colors arranged across two hemispheric clusters. Color scheme recognition requires memorizing adjacent star-face relationships (e.g., White top paired with Red/Green/Blue/Yellow/Purple ring).'},
            '4': {'title': '4. Kinematics, Rearrangement & Parity', 'icon': 'fa-solid fa-code-compare', 'color': 'emerald', 'content': '72-degree and 144-degree pentagonal face turns. Block building proceeds through the Star cross, First Two Layers (F2L), Second Two Layers (S2L), and Megaminx Last Layer (4-look LL: CP, CO, EP, EO). Parity algorithms do not exist due to odd vertex symmetry.'},
            '5': {'title': '5. Clan/Group Challenge & Collaborative Solving', 'icon': 'fa-solid fa-users-rays', 'color': 'indigo', 'content': 'Endurance speedcubing leagues: sub-40 second clan benchmarks. Clans share custom Star cross-planning algorithms and Last Layer corner orientation commutators.'}
        }
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
        'face_names': ['Top', 'Bottom', 'Front', 'Back', 'Left', 'Right'],
        'dossier': {
            '1': {'title': '1. Mechanical Architecture & Geometry', 'icon': 'fa-solid fa-gears', 'color': 'cyan', 'content': 'Deep-cut hexahedron with 4 internal cutting planes passing directly through the geometric center of the cube. Turning any corner splits the cube into two equal halves, moving 4 corners and 3 square centers simultaneously.'},
            '2': {'title': '2. Mathematical Group Theory & State Space', 'icon': 'fa-solid fa-calculator', 'color': 'amber', 'content': 'Group order is 3,149,280 states. God\'s Number is only 11 moves. Solved via Sarah\'s Method (Beginner, Intermediate, Advanced) and NS (Northern States) commutators.'},
            '3': {'title': '3. Color & Aesthetic Surface Customization', 'icon': 'fa-solid fa-palette', 'color': 'pink', 'content': '6 square faces, each divided into 1 center diamond and 4 corner triangles (30 total visible facets). Standard WCA BOY color scheme.'},
            '4': {'title': '4. Kinematics, Rearrangement & Parity', 'icon': 'fa-solid fa-code-compare', 'color': 'emerald', 'content': 'Corner-turning deep-cut kinematics couple centers and corners in fixed orbits. The primary algorithm is the Sledgehammer commutator (R\' F R F\'), which has an order of 3 and cycles three center diamonds while twisting corners.'},
            '5': {'title': '5. Clan/Group Challenge & Collaborative Solving', 'icon': 'fa-solid fa-users-rays', 'color': 'indigo', 'content': 'Lightning fingertrick clan challenges: sub-2 second single solves. Clans master finger-roll Sledgehammer and Hedgeslammer executions without regripping.'}
        }
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
        'face_names': ['Carbon Prime', 'Slate Offset', 'Titanium Axis', 'Shadow Grid', 'Graphite Layer', 'Phantom Core'],
        'dossier': {
            '1': {'title': '1. Mechanical Architecture & Geometry', 'icon': 'fa-solid fa-gears', 'color': 'cyan', 'content': 'Extreme 3x3 modification with internal rotational axes skewed and offset relative to the exterior cube faces. In its solved cubic resting state, NO layer can turn because the internal cutting planes do not align with the outer boundaries.'},
            '2': {'title': '2. Mathematical Group Theory & State Space', 'icon': 'fa-solid fa-calculator', 'color': 'amber', 'content': 'Isomorphic to the 3x3 permutation group, but with additional hidden center orientation constraints: all 6 centers must be oriented with exact angular precision, increasing the effective state space to ~1.77x10^23.'},
            '3': {'title': '3. Color & Aesthetic Surface Customization', 'icon': 'fa-solid fa-palette', 'color': 'pink', 'content': 'Uniform stealth monochrome (Carbon, Titanium Slate, Phantom Black). Absence of color forces the cuber to identify individual pieces by trapezoidal angles, facet slope, and irregular polygonal volume.'},
            '4': {'title': '4. Kinematics, Rearrangement & Parity', 'icon': 'fa-solid fa-code-compare', 'color': 'emerald', 'content': 'Requires a mandatory setup turn: rotating the middle and side layers by ~15 degrees to align the internal cutting planes before any kinematic turn can execute. Misaligned layers immediately bind and lock.'},
            '5': {'title': '5. Clan/Group Challenge & Collaborative Solving', 'icon': 'fa-solid fa-users-rays', 'color': 'indigo', 'content': 'Master Clan Trials: members challenge one another to reconstruct scrambled "chaos" states without piece removal, sharing visual angle proofs to identify the true phantom center.'}
        }
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
