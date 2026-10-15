import 'package:flutter_test/flutter_test.dart';
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:mobile_app/core/database/app_database.dart';

void main() {
  late AppDatabase db;

  setUp(() {
    // In-memory SQLite database executor for deterministic tests
    db = AppDatabase(NativeDatabase.memory());
  });

  tearDown(() async {
    await db.close();
  });

  group('Drift SQLite Offline Cache Tests', () {
    test('Can cache and retrieve user profile offline', () async {
      await db.cacheProfile(
        CachedUserProfileCompanion.insert(
          id: const Value(1),
          username: 'speedcuber',
          email: const Value('cuber@cubeverse.io'),
          role: const Value('user'),
          bio: const Value('Speedcuber Bio'),
          avatarColor: const Value('#818cf8'),
          wcaId: const Value('2026CUBE01'),
          totalSolves: const Value(42),
          minMoves: const Value(16),
          avgMoves: const Value(24.5),
          lastSyncedAt: '2026-10-15T12:00:00Z',
        ),
      );

      final cached = await db.getOfflineProfile();
      expect(cached, isNotNull);
      expect(cached!.username, 'speedcuber');
      expect(cached.totalSolves, 42);
      expect(cached.minMoves, 16);
      expect(cached.avgMoves, 24.5);
    });

    test('Can cache solves and retrieve in reverse chronological order', () async {
      await db.cacheSolves([
        CachedSolvesCompanion.insert(
          remoteId: const Value(101),
          scramble: "R U R' U'",
          solution: "U R U' R'",
          moveCount: 4,
          createdAt: '2026-10-15 10:00:00',
        ),
        CachedSolvesCompanion.insert(
          remoteId: const Value(102),
          scramble: "F2 B2",
          solution: "B2 F2",
          moveCount: 2,
          createdAt: '2026-10-15 10:05:00',
        ),
      ]);

      final offlineSolves = await db.getOfflineSolves();
      expect(offlineSolves.length, 2);
      expect(offlineSolves.first.moveCount, 2); // ordered by id desc
    });

    test('Can cache patterns and query offline', () async {
      await db.cachePatternsList([
        CachedPatternsCompanion.insert(
          id: 'checkerboard',
          name: 'Checkerboard',
          moves: 'M2 E2 S2',
          description: const Value('Classic checkerboard'),
        ),
        CachedPatternsCompanion.insert(
          id: 'superflip',
          name: 'Superflip',
          moves: "U R2 F B R B2 R U2 L B2 R U' D' R2 F R' L B2 U2 F2",
          description: const Value('All 12 edges flipped'),
        ),
      ]);

      final patterns = await db.getOfflinePatterns();
      expect(patterns.length, 2);
      expect(patterns.map((p) => p.id), contains('superflip'));
    });

    test('Can cache scan results and query offline', () async {
      await db.cacheScanResult(
        CachedScanResultsCompanion.insert(
          centerColor: 'Y',
          faceGridJson: '[["Y","Y","Y"],["Y","Y","Y"],["Y","Y","Y"]]',
          annotatedImageBase64: 'data:image/jpeg;base64,...',
          scannedAt: '2026-10-15T12:00:00Z',
        ),
      );

      final scans = await db.getOfflineScanResults();
      expect(scans.length, 1);
      expect(scans.first.centerColor, 'Y');
    });

    test('Can clear all offline cache', () async {
      await db.cacheProfile(
        CachedUserProfileCompanion.insert(
          id: const Value(1),
          username: 'temp',
          lastSyncedAt: '2026-10-15',
        ),
      );
      await db.clearAllCache();

      final cached = await db.getOfflineProfile();
      expect(cached, isNull);
    });
  });
}
