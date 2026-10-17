/// Service layer for the Classic Playing Card Suite on mobile.
///
/// Talks to `/api/v1/cards/*` (FastAPI) with the shared Flask session cookie,
/// so a phone plays the same tables, wallets and hash-chained ledger as the
/// web app.
library;

import 'package:flutter/foundation.dart';
import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';
import 'models/card_game.dart';

/// Coin balance plus the player's own ledger history.
class WalletSnapshot {
  final int personal;
  final int reserve;
  final List<LedgerEntry> ledger;

  const WalletSnapshot({
    required this.personal,
    required this.reserve,
    required this.ledger,
  });

  factory WalletSnapshot.fromJson(Map<String, dynamic> json) {
    final balances = json['balances'];
    int read(String key) {
      if (balances is Map && balances[key] != null) {
        return balances[key] is int
            ? balances[key] as int
            : int.tryParse('${balances[key]}') ?? 0;
      }
      return 0;
    }

    return WalletSnapshot(
      personal: json['personal'] is int
          ? json['personal'] as int
          : read('personal'),
      reserve: json['reserve'] is int ? json['reserve'] as int : read('reserve'),
      ledger: [
        if (json['ledger'] is List)
          ...json['ledger'].map(
              (e) => LedgerEntry.fromJson(Map<String, dynamic>.from(e as Map))),
      ],
    );
  }
}

class CardService extends ChangeNotifier {
  final ApiClient _api;
  bool _busy = false;
  String? _error;

  CardService(this._api);

  bool get isBusy => _busy;
  String? get lastError => _error;

  void clearError() {
    _error = null;
  }

  String _detail(ApiResponse res) {
    final data = res.data;
    if (data is Map && data['detail'] != null) return data['detail'].toString();
    if (data is Map && data['error'] != null) return data['error'].toString();
    return res.error ?? 'Request failed (${res.statusCode})';
  }

  Future<T> _guard<T>(Future<T> Function() run) async {
    _busy = true;
    _error = null;
    notifyListeners();
    try {
      return await run();
    } finally {
      _busy = false;
      notifyListeners();
    }
  }

  CardGame? _state(ApiResponse res) {
    final data = res.data;
    if (res.isSuccess && data is Map && data['state'] is Map) {
      return CardGame.fromJson(Map<String, dynamic>.from(data['state'] as Map));
    }
    _error = _detail(res);
    return null;
  }

  // ---------------------------------------------------------------- catalogue
  Future<List<CatalogEntry>?> fetchCatalog() {
    return _guard(() async {
      final res = await _api.get(ApiConstants.cardCatalog);
      if (!res.isSuccess || res.data is! Map) {
        _error = _detail(res);
        return null;
      }
      final data = Map<String, dynamic>.from(res.data as Map);
      return <CatalogEntry>[
        if (data['classic'] is List)
          ...data['classic'].map((e) =>
              CatalogEntry.fromJson(Map<String, dynamic>.from(e as Map))),
      ];
    });
  }

  // ------------------------------------------------------------------ wallet
  Future<WalletSnapshot?> fetchWallet() {
    return _guard(() async {
      final res = await _api.get(ApiConstants.cardWallet);
      if (!res.isSuccess || res.data is! Map) {
        _error = _detail(res);
        return null;
      }
      return WalletSnapshot.fromJson(Map<String, dynamic>.from(res.data as Map));
    });
  }

  Future<List<LedgerEntry>> fetchLedger({int limit = 30}) {
    return _guard(() async {
      final res = await _api.get('${ApiConstants.cardLedger}?limit=$limit');
      if (!res.isSuccess || res.data is! Map) return <LedgerEntry>[];
      final data = Map<String, dynamic>.from(res.data as Map);
      if (data['entries'] is! List) return <LedgerEntry>[];
      return (data['entries'] as List)
          .map((e) => LedgerEntry.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    });
  }

  // --------------------------------------------------------------- practice
  Future<CardGame?> practiceActive() {
    return _guard(() async {
      final res = await _api.get(ApiConstants.cardPracticeActive);
      if (!res.isSuccess || res.data is! Map) return null;
      final data = Map<String, dynamic>.from(res.data as Map);
      if (data['state'] is! Map) return null;
      return CardGame.fromJson(Map<String, dynamic>.from(data['state'] as Map));
    });
  }

  Future<CardGame?> practiceStart(String slug) {
    return _guard(() async {
      final res = await _api.post(ApiConstants.cardPractice, body: {'slug': slug});
      return _state(res);
    });
  }

  Future<CardGame?> practiceMove(int gameId, Map<String, dynamic> action) {
    return _guard(() async {
      final res = await _api.post(
        '${ApiConstants.cardPractice}/$gameId/action',
        body: action,
      );
      return _state(res);
    });
  }

  Future<bool> practiceAbandon(int gameId) {
    return _guard(() async {
      final res = await _api.delete('${ApiConstants.cardPractice}/$gameId');
      if (!res.isSuccess) _error = _detail(res);
      return res.isSuccess;
    });
  }

  // ------------------------------------------------------------ classic tables
  Future<CardGame?> classicActive() {
    return _guard(() async {
      final res = await _api.get(ApiConstants.cardClassicActive);
      if (!res.isSuccess || res.data is! Map) return null;
      final data = Map<String, dynamic>.from(res.data as Map);
      if (data['state'] is! Map) return null;
      return CardGame.fromJson(Map<String, dynamic>.from(data['state'] as Map));
    });
  }

  Future<CardGame?> classicStart({
    required String slug,
    String mode = 'ai',
    int stake = 0,
    int groupId = 0,
  }) {
    return _guard(() async {
      final res = await _api.post(ApiConstants.cardClassic, body: {
        'slug': slug,
        'mode': mode,
        'stake': stake,
        'group_id': groupId,
      });
      return _state(res);
    });
  }

  Future<CardGame?> classicMove(int gameId, Map<String, dynamic> action) {
    return _guard(() async {
      final res = await _api.post(
        '${ApiConstants.cardClassic}/$gameId/action',
        body: action,
      );
      return _state(res);
    });
  }

  /// Re-read one table (used to follow group tables played by other humans).
  Future<CardGame?> classicState(int gameId) {
    return _guard(() async {
      final res = await _api.get('${ApiConstants.cardClassic}/$gameId');
      if (!res.isSuccess || res.data is! Map) return null;
      final data = Map<String, dynamic>.from(res.data as Map);
      if (data['state'] is! Map) return null;
      return CardGame.fromJson(Map<String, dynamic>.from(data['state'] as Map));
    });
  }

  Future<CardGame?> classicJoin(int gameId) {
    return _guard(() async {
      final res = await _api.post('${ApiConstants.cardClassic}/$gameId/join');
      return _state(res);
    });
  }

  Future<CardGame?> classicStartTable(int gameId) {
    return _guard(() async {
      final res = await _api.post('${ApiConstants.cardClassic}/$gameId/start');
      return _state(res);
    });
  }

  Future<bool> classicCancel(int gameId) {
    return _guard(() async {
      final res = await _api.post('${ApiConstants.cardClassic}/$gameId/cancel');
      if (!res.isSuccess) _error = _detail(res);
      return res.isSuccess;
    });
  }
}
