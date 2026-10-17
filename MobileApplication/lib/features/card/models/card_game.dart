/// Data models for the Classic Playing Card Suite mobile client.
library;

/// One entry of the game catalogue (classic suite or card club).
class CatalogEntry {
  final String slug;
  final String name;
  final String players;
  final String description;

  const CatalogEntry({
    required this.slug,
    required this.name,
    this.players = '4 players',
    this.description = '',
  });

  factory CatalogEntry.fromJson(Map<String, dynamic> json) {
    return CatalogEntry(
      slug: json['slug']?.toString() ?? '',
      name: json['name']?.toString() ?? json['slug']?.toString() ?? '',
      players: json['players']?.toString() ??
          '${json['min'] ?? 4}-${json['max'] ?? 4} players',
      description: (json['description'] ?? json['desc'] ?? '').toString(),
    );
  }
}

/// One hash-chained coin ledger row for the signed-in player.
class LedgerEntry {
  final int seq;
  final int amount;
  final int balanceAfter;
  final String entryType;
  final String? refType;
  final int? refId;
  final String note;
  final String createdAt;

  const LedgerEntry({
    required this.seq,
    required this.amount,
    required this.balanceAfter,
    required this.entryType,
    this.refType,
    this.refId,
    this.note = '',
    this.createdAt = '',
  });

  factory LedgerEntry.fromJson(Map<String, dynamic> json) {
    return LedgerEntry(
      seq: json['seq'] is int ? json['seq'] as int : int.tryParse('${json['seq']}') ?? 0,
      amount: json['amount'] is int ? json['amount'] as int : int.tryParse('${json['amount']}') ?? 0,
      balanceAfter: json['balance_after'] is int
          ? json['balance_after'] as int
          : int.tryParse('${json['balance_after']}') ?? 0,
      entryType: json['entry_type']?.toString() ?? '',
      refType: json['ref_type']?.toString(),
      refId: json['ref_id'] is int ? json['ref_id'] as int : null,
      note: json['note']?.toString() ?? '',
      createdAt: json['created_at']?.toString() ?? '',
    );
  }
}

/// A seated player at the table.
class CardPlayer {
  final int seat;
  final int? userId;
  final String name;
  final bool isBot;
  final bool isMe;

  const CardPlayer({
    required this.seat,
    this.userId,
    required this.name,
    required this.isBot,
    required this.isMe,
  });

  factory CardPlayer.fromJson(Map<String, dynamic> json) {
    return CardPlayer(
      seat: json['seat'] is int ? json['seat'] as int : 0,
      userId: json['user_id'] is int ? json['user_id'] as int : null,
      name: json['name']?.toString() ?? '',
      isBot: json['is_bot'] == true || json['is_bot'] == 1,
      isMe: json['is_me'] == true,
    );
  }
}

/// The public/private view of one deal, as served by the card API.
class CardGame {
  final int gameId;
  final String slug;
  final String title;
  final String phase;
  final String status;
  final String kind; // 'practice' | classic modes ('ai' | 'group')
  final String mode;
  final bool over;
  final bool isMyTurn;
  final bool controlsDummy;
  final int mySeat;
  final int stake;
  final int pot;
  final int ownerId;
  final List<String> hand;
  final List<int> counts;
  final List<String> seatLabels;
  final List<TrickPlay> trick;
  final List<Map<String, dynamic>> legalActions;
  final List<Map<String, dynamic>> players;
  final List<int> botSeats;
  final List<String> log;
  final Map<String, dynamic>? settlement;
  final Map<String, dynamic> raw;

  const CardGame({
    required this.gameId,
    required this.slug,
    required this.title,
    required this.phase,
    required this.status,
    this.kind = 'practice',
    this.mode = 'ai',
    required this.over,
    required this.isMyTurn,
    this.controlsDummy = false,
    this.mySeat = 0,
    this.stake = 0,
    this.pot = 0,
    this.ownerId = 0,
    required this.hand,
    required this.counts,
    required this.seatLabels,
    required this.trick,
    required this.legalActions,
    required this.players,
    required this.botSeats,
    required this.log,
    this.settlement,
    required this.raw,
  });

  factory CardGame.fromJson(Map<String, dynamic> json) {
    final counts = <int>[0, 0, 0, 0];
    final rawCounts = json['counts'];
    if (rawCounts is Map) {
      rawCounts.forEach((key, value) {
        final idx = int.tryParse(key.toString());
        if (idx != null && idx >= 0 && idx < 4) {
          counts[idx] = value is int ? value : int.tryParse('$value') ?? 0;
        }
      });
    }

    final labels = <String>[];
    final rawLabels = json['seat_labels'];
    if (rawLabels is List) {
      for (var i = 0; i < rawLabels.length && i < 4; i++) {
        labels.add('${rawLabels[i]}');
      }
    }
    while (labels.length < 4) {
      labels.add('Seat ${labels.length}');
    }

    final trick = <TrickPlay>[];
    final rawTrick = json['trick'];
    if (rawTrick is List) {
      for (final e in rawTrick) {
        if (e is Map) {
          trick.add(TrickPlay(
            seat: e['seat'] is int ? e['seat'] as int : int.tryParse('${e['seat']}') ?? 0,
            card: e['card']?.toString() ?? '',
          ));
        }
      }
    }

    return CardGame(
      gameId: json['game_id'] is int
          ? json['game_id'] as int
          : int.tryParse('${json['game_id']}') ?? 0,
      slug: json['slug']?.toString() ?? '',
      title: json['title']?.toString() ?? json['slug']?.toString() ?? '',
      phase: json['phase']?.toString() ?? 'playing',
      status: json['status']?.toString() ?? 'active',
      kind: json['kind']?.toString() ?? 'practice',
      mode: json['mode']?.toString() ?? 'ai',
      over: json['over'] == true,
      isMyTurn: json['is_my_turn'] == true,
      controlsDummy: json['controls_dummy'] == true,
      mySeat: json['my_seat'] is int ? json['my_seat'] as int : 0,
      stake: json['stake'] is int ? json['stake'] as int : 0,
      pot: json['pot'] is int ? json['pot'] as int : 0,
      ownerId: json['owner_id'] is int ? json['owner_id'] as int : 0,
      hand: [
        if (json['hand'] is List) ...json['hand'].map((c) => '$c'),
      ],
      counts: counts,
      seatLabels: labels,
      trick: trick,
      legalActions: [
        if (json['legal_actions'] is List)
          ...json['legal_actions'].map((a) => Map<String, dynamic>.from(a as Map)),
      ],
      players: [
        if (json['players'] is List)
          ...json['players'].map((p) => Map<String, dynamic>.from(p as Map)),
      ],
      botSeats: _intList(json['bot_seats']),
      log: [
        if (json['log'] is List) ...json['log'].map((l) => '$l'),
      ],
      settlement: json['settlement'] is Map
          ? Map<String, dynamic>.from(json['settlement'] as Map)
          : null,
      raw: json,
    );
  }

  /// The cards the human may legally put on the table right now.
  List<String> get playableCards => legalActions
      .where((a) => a['action'] == 'play')
      .map((a) => a['card']?.toString() ?? '')
      .where((c) => c.isNotEmpty)
      .toList();

  bool isPlayable(String card) =>
      isMyTurn && phase == 'playing' && playableCards.contains(card);

  /// Bids / passes / trump picks (anything that is not a card play).
  List<Map<String, dynamic>> get promptActions => legalActions
      .where((a) =>
          a['action'] != 'play' &&
          a['action'] != 'set_trump' &&
          a['action'] != 'reveal_trump')
      .toList();

  List<Map<String, dynamic>> get trumpActions =>
      legalActions.where((a) => a['action'] == 'set_trump').toList();

  Map<String, dynamic>? get revealTrumpAction {
    for (final a in legalActions) {
      if (a['action'] == 'reveal_trump') return a;
    }
    return null;
  }

  /// Seat numbers rotated so the human is always drawn at the bottom:
  /// 0 = me, 1 = left, 2 = partner/top, 3 = right.
  int seatAtPosition(int position) => (mySeat + position) % 4;

  String labelFor(int seat) =>
      seat >= 0 && seat < seatLabels.length ? seatLabels[seat] : 'Seat $seat';

  bool isBotSeat(int seat) {
    if (botSeats.isNotEmpty) return botSeats.contains(seat);
    final p = players.where((p) => p['seat'] == seat);
    if (p.isEmpty) return seat != mySeat;
    return p.first['is_bot'] == true || p.first['is_bot'] == 1;
  }
}

List<int> _intList(dynamic raw) {
  final out = <int>[];
  if (raw is List) {
    for (final value in raw) {
      final parsed = value is int ? value : int.tryParse('$value');
      if (parsed != null && parsed >= 0) out.add(parsed);
    }
  }
  return out;
}

/// One card laid down in the current trick.
class TrickPlay {
  final int seat;
  final String card;

  const TrickPlay({required this.seat, required this.card});
}
