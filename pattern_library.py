"""
CubePermutation AI - Pattern Studio Library
=============================================
Artistic Rubik's Cube patterns served to the Pattern Studio dashboard stage.

Algorithms are adapted from Particula's "Rubik's Cube Patterns" guide
(particula-tech.com/blogs/news/rubiks-cube-patterns) and extended with the
classic Superflip. Every pattern is verified with pycuber at load time:
it must parse, must change the cube, and must return to solved when its
inverse is applied - so the UI never ships a broken algorithm.
"""

import pycuber as pc

from solver_engine import invert_sequence

PATTERN_DEFS = [
    {
        'id': 'checkerboard',
        'name': 'Checkerboard',
        'difficulty': 'beginner',
        'algorithm': 'M2 E2 S2',
        'description': 'Alternating squares of two opposite colours on every face - the first pattern most cubers learn.',
    },
    {
        'id': 'six_spots',
        'name': 'Six Spots',
        'difficulty': 'beginner',
        'algorithm': "M E M' E'",
        'description': 'Four moves: every face keeps its own colour while a single contrasting dot floats in the centre.',
    },
    {
        'id': 'cube_in_cube',
        'name': 'Cube in a Cube',
        'difficulty': 'intermediate',
        'algorithm': "F L F U' R U F2 L2 U' L' B D' B' L2 U",
        'description': 'A smaller 2x2 cube appears nested inside the 3x3 on every single face.',
    },
    {
        'id': 'cube_in_cube_in_cube',
        'name': 'Cube in a Cube in a Cube',
        'difficulty': 'advanced',
        'algorithm': "F' L F D2 R' B R F2 L2 U F U' D2 F2",
        'description': 'Two cubes inside one - the showstopper that makes people ask how it is even possible.',
    },
    {
        'id': 'superflip',
        'name': 'Superflip',
        'difficulty': 'advanced',
        'algorithm': "U R2 F B R B2 R U2 L B2 R U' D' R2 F R' L B2 U2 F2",
        'description': 'All twelve edges flipped in place - the famous position behind God\'s Number being 20 moves.',
    },
]

_pattern_cache = None


def verify_pattern(algorithm):
    """Applies an algorithm, checks it changes the cube and that its inverse restores solved."""
    cube = pc.Cube()
    cube(algorithm)
    if str(cube) == str(pc.Cube()):
        raise ValueError(f'Pattern algorithm leaves the cube solved: {algorithm}')
    cube(invert_sequence(algorithm))
    if str(cube) != str(pc.Cube()):
        raise ValueError(f'Pattern algorithm does not revert to solved: {algorithm}')
    return True


def get_patterns():
    """Returns the verified Pattern Studio library (cached after first call)."""
    global _pattern_cache
    if _pattern_cache is None:
        patterns = []
        for definition in PATTERN_DEFS:
            verify_pattern(definition['algorithm'])
            moves = definition['algorithm'].split()
            pattern = dict(definition)
            pattern['moves'] = moves
            pattern['move_count'] = len(moves)
            pattern['verified'] = True
            patterns.append(pattern)
        _pattern_cache = patterns
    return _pattern_cache
