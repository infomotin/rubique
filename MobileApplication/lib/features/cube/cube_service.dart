import 'package:flutter/foundation.dart';
import 'package:drift/drift.dart';
import '../../core/network/api_client.dart';
import '../../core/constants/api_constants.dart';
import '../../core/database/app_database.dart';
import 'models/solve_result.dart';
import 'models/pattern_item.dart';

class ScrambleResult {
  final String scramble;
  final String solution;
  final int moveCount;

  ScrambleResult({
    required this.scramble,
    required this.solution,
    required this.moveCount,
  });

  factory ScrambleResult.fromJson(Map<String, dynamic> json) {
    return ScrambleResult(
      scramble: json['scramble']?.toString() ?? '',
      solution: json['solution']?.toString() ?? '',
      moveCount: json['move_count'] is int ? json['move_count'] : int.tryParse(json['move_count']?.toString() ?? '0') ?? 0,
    );
  }
}

class SolveHistoryItem {
  final int id;
  final String scramble;
  final String solution;
  final int moveCount;
  final String createdAt;

  SolveHistoryItem({
    required this.id,
    required this.scramble,
    required this.solution,
    required this.moveCount,
    required this.createdAt,
  });

  factory SolveHistoryItem.fromJson(Map<String, dynamic> json) {
    return SolveHistoryItem(
      id: json['id'] is int ? json['id'] : int.tryParse(json['id']?.toString() ?? '0') ?? 0,
      scramble: json['scramble']?.toString() ?? '',
      solution: json['solution']?.toString() ?? '',
      moveCount: json['move_count'] is int ? json['move_count'] : int.tryParse(json['move_count']?.toString() ?? '0') ?? 0,
      createdAt: json['created_at']?.toString() ?? '',
    );
  }
}

class CubeService extends ChangeNotifier {
  final ApiClient _apiClient;
  final AppDatabase _db;
  bool _isLoading = false;

  CubeService(this._apiClient, this._db);

  bool get isLoading => _isLoading;

  Future<ScrambleResult?> generateScramble() async {
    _isLoading = true;
    notifyListeners();

    final response = await _apiClient.get(ApiConstants.scramble);
    _isLoading = false;
    notifyListeners();

    if (response.isSuccess && response.data is Map) {
      return ScrambleResult.fromJson(Map<String, dynamic>.from(response.data));
    }
    return null;
  }

  Future<SolveResult> solveCube({String? customMoves, String? faceletString}) async {
    _isLoading = true;
    notifyListeners();

    final payload = <String, dynamic>{};
    if (faceletString != null && faceletString.trim().isNotEmpty) {
      payload['facelet_string'] = faceletString.trim();
    } else if (customMoves != null && customMoves.trim().isNotEmpty) {
      payload['custom_moves'] = customMoves.trim();
    }

    final response = await _apiClient.post(ApiConstants.solve, body: payload);
    _isLoading = false;
    notifyListeners();

    if (response.isSuccess && response.data is Map) {
      final result = SolveResult.fromJson(Map<String, dynamic>.from(response.data));
      // Auto-refresh solve history in background
      fetchAndCacheSolveHistory();
      return result;
    } else {
      return SolveResult(
        success: false,
        solution: '',
        moves: [],
        steps: [],
        moveCount: 0,
        engine: 'none',
        method: '',
        error: response.error ?? 'Solving request failed.',
      );
    }
  }

  Future<List<PatternItem>> getPatterns() async {
    final response = await _apiClient.get(ApiConstants.patterns);
    if (response.isSuccess && response.data is Map && response.data['patterns'] is List) {
      final list = <PatternItem>[];
      final companions = <CachedPatternsCompanion>[];

      for (final item in response.data['patterns']) {
        if (item is Map) {
          final m = Map<String, dynamic>.from(item);
          final pattern = PatternItem.fromJson(m);
          list.add(pattern);
          companions.add(CachedPatternsCompanion.insert(
            id: pattern.id,
            name: pattern.name,
            moves: pattern.moves,
            description: Value(pattern.description),
          ));
        }
      }

      // Cache patterns in local Drift database for offline use
      if (companions.isNotEmpty) {
        await _db.cachePatternsList(companions);
      }
      return list;
    }

    // Network unavailable: Fallback to Drift SQLite offline cached patterns
    final offlinePatterns = await _db.getOfflinePatterns();
    return offlinePatterns
        .map((p) => PatternItem(
              id: p.id,
              name: p.name,
              moves: p.moves,
              description: p.description,
            ))
        .toList();
  }

  Future<List<SolveHistoryItem>> fetchAndCacheSolveHistory() async {
    final response = await _apiClient.get(ApiConstants.history);
    if (response.isSuccess && response.data is Map && response.data['history'] is List) {
      final items = <SolveHistoryItem>[];
      final companions = <CachedSolvesCompanion>[];

      for (final item in response.data['history']) {
        if (item is Map) {
          final m = Map<String, dynamic>.from(item);
          final historyItem = SolveHistoryItem.fromJson(m);
          items.add(historyItem);
          companions.add(CachedSolvesCompanion.insert(
            remoteId: Value(historyItem.id),
            scramble: historyItem.scramble,
            solution: historyItem.solution,
            moveCount: historyItem.moveCount,
            createdAt: historyItem.createdAt,
          ));
        }
      }

      // Cache in local Drift database for read-only offline view
      if (companions.isNotEmpty) {
        await _db.cacheSolves(companions);
      }
      return items;
    }

    // Network unavailable: Fallback to Drift SQLite offline cached history
    final cached = await _db.getOfflineSolves();
    return cached
        .map((s) => SolveHistoryItem(
              id: s.remoteId ?? s.id,
              scramble: s.scramble,
              solution: s.solution,
              moveCount: s.moveCount,
              createdAt: s.createdAt,
            ))
        .toList();
  }

  Future<List<SolveHistoryItem>> getOfflineHistory() async {
    final cached = await _db.getOfflineSolves();
    return cached
        .map((s) => SolveHistoryItem(
              id: s.remoteId ?? s.id,
              scramble: s.scramble,
              solution: s.solution,
              moveCount: s.moveCount,
              createdAt: s.createdAt,
            ))
        .toList();
  }
}
