import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_app/features/auth/models/user_model.dart';
import 'package:mobile_app/features/cube/models/solve_result.dart';
import 'package:mobile_app/features/cube/models/pattern_item.dart';
import 'package:mobile_app/features/cube/cube_service.dart';
import 'package:mobile_app/features/scan/models/scan_result.dart';

void main() {
  group('Models & Parsing Tests', () {
    test('UserModel parses MySQL user payload correctly', () {
      final json = {
        'id': 3,
        'username': 'speedcuber',
        'email': 'cuber@cubeverse.io',
        'role': 'user',
        'bio': 'WCA Speedcubing Contender',
        'avatar_color': '#818cf8',
        'wca_id': '2026CUBE01',
        'country': 'USA',
        'main_cube': 'GAN 12 MagLev 3x3',
        'preferred_method': 'CFOP',
        'pb_single': '6.42',
        'pb_ao5': '8.15',
        'created_at': '2026-01-01 12:00:00',
      };

      final user = UserModel.fromJson(json);
      expect(user.id, 3);
      expect(user.username, 'speedcuber');
      expect(user.email, 'cuber@cubeverse.io');
      expect(user.preferredMethod, 'CFOP');
      expect(user.pbSingle, '6.42');
    });

    test('SolveResult parses solution moves and step explanations', () {
      final json = {
        'success': true,
        'solution': "U R U' R'",
        'moves': ['U', 'R', "U'", "R'"],
        'steps': [
          {
            'step': 1,
            'move': 'U',
            'why': 'Cycles top-layer corners and edges into position.',
            'how': 'Flick top layer from right to left using right index finger.',
          },
          {
            'step': 2,
            'move': 'R',
            'why': 'Rotates Right face clockwise.',
            'how': 'Push Right face away from you.',
          }
        ],
        'move_count': 4,
        'engine': 'two_phase',
        'method': 'Two-Phase Kociemba Minimal Step Solver',
      };

      final result = SolveResult.fromJson(json);
      expect(result.success, isTrue);
      expect(result.moves.length, 4);
      expect(result.steps.length, 2);
      expect(result.steps[0].move, 'U');
      expect(result.steps[0].why, contains('top-layer'));
      expect(result.steps[0].how, contains('index finger'));
      expect(result.moveCount, 4);
    });

    test('PatternItem parses pattern library item', () {
      final json = {
        'id': 'checkerboard',
        'name': 'Checkerboard (Order 2)',
        'moves': "M2 E2 S2",
        'description': 'Classic alternating opposite color checkerboard.',
      };

      final pattern = PatternItem.fromJson(json);
      expect(pattern.id, 'checkerboard');
      expect(pattern.name, contains('Checkerboard'));
      expect(pattern.moves, "M2 E2 S2");
    });

    test('ScanResult parses OpenCV 3x3 face grid and generates flat facelets', () {
      final json = {
        'success': true,
        'face_grid': [
          ['Y', 'G', 'Y'],
          ['O', 'Y', 'R'],
          ['Y', 'B', 'W'],
        ],
        'annotated_image': 'data:image/jpeg;base64,/9j/4AAQSkZJRg...',
        'center_color': 'Y',
      };

      final scan = ScanResult.fromJson(json);
      expect(scan.success, isTrue);
      expect(scan.faceGrid.length, 3);
      expect(scan.centerColor, 'Y');
      expect(scan.toFlatFaceletString(), 'YGYOYRYBW');
    });

    test('ScrambleResult parses WCA scramble and preliminary solution', () {
      final json = {
        'scramble': "R U R' U' F2 D B' L2",
        'solution': "L2 B D' F2 U R U' R'",
        'move_count': 8,
      };

      final scramble = ScrambleResult.fromJson(json);
      expect(scramble.scramble, contains("R U"));
      expect(scramble.moveCount, 8);
    });
  });
}
