/// One deal of a Classic Suite game on the phone: your hand at the bottom,
/// the three bots (or group opponents) around it, the bidding / trump drawers
/// and the coin settlement when the deal ends.
library;

import 'dart:async';

import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import '../card_service.dart';
import '../models/card_game.dart';

class CardGameScreen extends StatefulWidget {
  final CardService cardService;
  final CardGame initialGame;
  final VoidCallback? onClosed;
  final Future<void> Function(CardGame game)? onDealFinished;

  const CardGameScreen({
    super.key,
    required this.cardService,
    required this.initialGame,
    this.onClosed,
    this.onDealFinished,
  });

  @override
  State<CardGameScreen> createState() => _CardGameScreenState();
}

class _CardGameScreenState extends State<CardGameScreen> {
  static const _suitSymbol = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'};
  static const _suitColor = {
    'S': Color(0xFFE2E8F0),
    'H': Color(0xFFF43F5E),
    'D': Color(0xFFF59E0B),
    'C': Color(0xFF38BDF8),
  };

  late CardGame _game;
  bool _sending = false;
  bool _endShown = false;
  String? _hint;
  Timer? _poll;

  @override
  void initState() {
    super.initState();
    _game = widget.initialGame;
    _syncPolling();
    if (_game.over) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _showSettlement());
    }
  }

  @override
  void dispose() {
    _poll?.cancel();
    super.dispose();
  }

  // ------------------------------------------------------------------ moves
  void _syncPolling() {
    _poll?.cancel();
    _poll = null;
    if (!_game.over && _game.kind != 'practice' && _game.mode == 'group') {
      _poll = Timer.periodic(const Duration(seconds: 4), (_) => _refresh());
    }
  }

  Future<void> _refresh() async {
    if (_sending || _game.kind == 'practice') return;
    final next = await widget.cardService.classicState(_game.gameId);
    if (!mounted || next == null) return;
    setState(() => _game = next);
    _syncPolling();
  }

  Future<void> _send(Map<String, dynamic> action) async {
    if (_sending || _game.over) return;
    setState(() {
      _sending = true;
      _hint = null;
    });
    final next = _game.kind == 'practice'
        ? await widget.cardService.practiceMove(_game.gameId, action)
        : await widget.cardService.classicMove(_game.gameId, action);
    if (!mounted) return;
    setState(() => _sending = false);
    if (next != null) {
      final wasOver = _game.over;
      setState(() => _game = next);
      _syncPolling();
      if (next.over && !wasOver) {
        _showSettlement();
        if (widget.onDealFinished != null) {
          await widget.onDealFinished!(next);
        }
      }
    } else {
      setState(() => _hint = widget.cardService.lastError);
      _refresh();
    }
  }

  Future<void> _startTable() async {
    setState(() => _sending = true);
    final next = await widget.cardService.classicStartTable(_game.gameId);
    if (!mounted) return;
    setState(() => _sending = false);
    if (next != null) {
      setState(() => _game = next);
      _syncPolling();
    } else {
      setState(() => _hint = widget.cardService.lastError);
    }
  }

  Future<void> _cancelTable() async {
    final ok = await widget.cardService.classicCancel(_game.gameId);
    if (!mounted) return;
    if (ok) {
      widget.onClosed?.call();
      Navigator.of(context).maybePop();
    } else {
      setState(() => _hint = widget.cardService.lastError);
    }
  }

  // -------------------------------------------------------------- settlement
  void _showSettlement() {
    if (_endShown || !mounted) return;
    _endShown = true;
    final st = _game.settlement;
    final lines = <Widget>[];

    if (st != null && st['kind'] == 'settlement') {
      final winners = (st['winner_names'] as List? ?? const []).join(', ');
      lines.add(Text(
        winners.isEmpty ? 'Deal settled' : '$winners take the pot',
        style: const TextStyle(
            color: AppTheme.accentEmerald,
            fontWeight: FontWeight.bold,
            fontSize: 16),
      ));
      final payouts = st['payouts'];
      if (payouts is Map) {
        final names = <String, String>{
          for (final p in _game.players) '${p['user_id']}': '${p['name']}',
        };
        payouts.forEach((key, value) {
          lines.add(Padding(
            padding: const EdgeInsets.symmetric(vertical: 2),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(names['$key'] ?? 'Player $key',
                    style: const TextStyle(color: AppTheme.borderSubtle)),
                Text('+$value',
                    style: const TextStyle(
                        color: AppTheme.accentEmerald,
                        fontWeight: FontWeight.bold)),
              ],
            ),
          ));
        });
      }
      lines.add(const Divider(color: AppTheme.borderSubtle));
      Object? myId;
      for (final p in _game.players) {
        if (p['is_me'] == true) {
          myId = p['user_id'];
          break;
        }
      }
      int myPayout = 0;
      if (payouts is Map && myId != null) {
        myPayout = int.tryParse('${payouts[myId] ?? payouts['$myId']}') ?? 0;
      }
      if (myPayout > 0) {
        lines.add(Text(
          'You staked ${_game.stake} and won $myPayout '
          '(+${myPayout - _game.stake} coins)',
          style: const TextStyle(color: AppTheme.accentCyan),
        ));
      } else if (_game.stake > 0) {
        lines.add(Text('You lost your ${_game.stake} coin stake',
            style: const TextStyle(color: AppTheme.accentRose)));
      } else {
        lines.add(const Text('Practice deal - no coins moved',
            style: TextStyle(color: AppTheme.accentAmber)));
      }
    } else if (st != null && st['kind'] == 'refund') {
      lines.add(const Text('No winner: every stake was refunded.',
          style: TextStyle(color: AppTheme.accentAmber)));
    } else {
      lines.add(Text(
        _game.winnerText(),
        style: const TextStyle(color: AppTheme.accentEmerald, fontSize: 16),
      ));
    }

    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.bgCard,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: AppTheme.borderGlow),
        ),
        title: const Text('Deal complete',
            style: TextStyle(color: Colors.white, fontSize: 18)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('${_game.title} · pot ${st != null ? st['pot'] ?? _game.pot : _game.pot} coins',
                style: const TextStyle(
                    color: AppTheme.accentAmber, fontSize: 13)),
            const SizedBox(height: 10),
            ...lines,
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Review table',
                style: TextStyle(color: AppTheme.accentCyan)),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              widget.onClosed?.call();
              Navigator.of(context).maybePop();
            },
            style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.accentMain),
            child: const Text('Back to cards'),
          ),
        ],
      ),
    );
  }

  // ----------------------------------------------------------------- helpers
  Widget _cardFace(
    String code, {
    double width = 54,
    double height = 76,
    bool playable = false,
    bool muted = false,
    VoidCallback? onTap,
  }) {
    final suit = code.isNotEmpty ? code[0] : '';
    final rankRaw = code.length > 1 ? code.substring(1) : '';
    final rank = rankRaw == 'T' ? '10' : rankRaw;
    final color = _suitColor[suit] ?? Colors.white;
    final face = Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: AppTheme.bgDark1,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: playable ? AppTheme.accentEmerald : AppTheme.borderSubtle,
          width: playable ? 2 : 1,
        ),
        boxShadow: [
          BoxShadow(
            color: playable
                ? AppTheme.accentEmerald.withOpacity(0.35)
                : Colors.black.withOpacity(0.35),
            blurRadius: 8,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      padding: const EdgeInsets.all(4),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('$rank${_suitSymbol[suit] ?? ''}',
              style: TextStyle(
                  color: color,
                  fontSize: width > 46 ? 14 : 11,
                  fontWeight: FontWeight.w800)),
          Expanded(
            child: Center(
              child: Text(
                _suitSymbol[suit] ?? '',
                style: TextStyle(color: color, fontSize: height * 0.34),
              ),
            ),
          ),
          RotatedBox(
            quarterTurns: 2,
            child: Text('$rank${_suitSymbol[suit] ?? ''}',
                style: TextStyle(
                    color: color,
                    fontSize: width > 46 ? 14 : 11,
                    fontWeight: FontWeight.w800)),
          ),
        ],
      ),
    );
    if (muted) {
      return Opacity(opacity: 0.55, child: face);
    }
    if (onTap == null) return face;
    return GestureDetector(onTap: onTap, child: face);
  }

  Widget _opponentSeat(int position, {bool isPartner = false}) {
    final seat = _game.seatAtPosition(position);
    final label = _game.labelFor(seat);
    final count = seat >= 0 && seat < _game.counts.length
        ? _game.counts[seat]
        : 0;
    final bot = _game.isBotSeat(seat);
    final color = isPartner ? AppTheme.accentEmerald : AppTheme.accentAmber;

    return Expanded(
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 4),
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 6),
        decoration: BoxDecoration(
          color: AppTheme.bgGlass,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withOpacity(0.4)),
        ),
        child: Column(
          children: [
            Icon(bot ? Icons.smart_toy_outlined : Icons.person_outline,
                size: 18, color: color),
            const SizedBox(height: 4),
            Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 11,
                  fontWeight: FontWeight.w700),
            ),
            Text('$count cards',
                style: const TextStyle(
                    color: AppTheme.borderSubtle, fontSize: 10)),
            const SizedBox(height: 6),
            SizedBox(
              height: 34,
              child: ListView(
                scrollDirection: Axis.horizontal,
                shrinkWrap: true,
                children: [
                  for (var i = 0; i < (count > 6 ? 6 : count); i++)
                    Container(
                      width: 14,
                      margin: const EdgeInsets.only(right: 2),
                      decoration: BoxDecoration(
                        color: AppTheme.bgDark2,
                        borderRadius: BorderRadius.circular(3),
                        border: Border.all(color: color.withOpacity(0.5)),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _trickArea() {
    final plays = _game.trick;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.bgDark0.withOpacity(0.6),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.borderGlowCyan),
      ),
      child: Column(
        children: [
          const Text('CENTER TRICK',
              style: TextStyle(
                  color: AppTheme.accentAmber,
                  fontSize: 10,
                  letterSpacing: 2,
                  fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          if (plays.isEmpty)
            const Text('Lead a card to start the trick',
                style: TextStyle(color: AppTheme.borderSubtle, fontSize: 12))
          else
            Wrap(
              spacing: 10,
              runSpacing: 6,
              alignment: WrapAlignment.center,
              children: [
                for (final p in plays)
                  Column(
                    children: [
                      Text(_game.labelFor(p.seat),
                          style: const TextStyle(
                              color: AppTheme.accentAmber, fontSize: 10)),
                      _cardFace(p.card, width: 44, height: 62),
                    ],
                  ),
              ],
            ),
        ],
      ),
    );
  }

  Widget _promptButtons() {
    final actions = <Map<String, dynamic>>[
      ..._game.promptActions,
      if (_game.isMyTurn) ..._game.trumpActions,
      if (_game.isMyTurn && _game.revealTrumpAction != null)
        _game.revealTrumpAction!,
    ];
    if (actions.isEmpty || !_game.isMyTurn) return const SizedBox.shrink();

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 6),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: AppTheme.bgGlass,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.borderGlow),
      ),
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        alignment: WrapAlignment.center,
        children: [
          for (final a in actions) _actionButton(a),
        ],
      ),
    );
  }

  Widget _actionButton(Map<String, dynamic> action) {
    final name = '${action['action']}';
    String label;
    Color color;
    switch (name) {
      case 'pass':
        label = 'Pass';
        color = AppTheme.borderSubtle;
        break;
      case 'bid':
        label = 'Bid ${action['value'] ?? ''}';
        color = AppTheme.accentEmerald;
        break;
      case 'level':
        label = 'Bid ${action['level'] ?? ''}${action['suit'] ?? ''}';
        color = AppTheme.accentEmerald;
        break;
      case 'set_trump':
        final suit = '${action['suit'] ?? ''}';
        label = '${_suitSymbol[suit] ?? '★'} Trump';
        color = _suitColor[suit] ?? AppTheme.accentAmber;
        break;
      case 'reveal_trump':
        label = 'Reveal trump';
        color = AppTheme.accentAmber;
        break;
      case 'call':
        label = 'Call ${action['value'] ?? ''}';
        color = AppTheme.accentEmerald;
        break;
      default:
        label = name.isEmpty ? 'Action' : name[0].toUpperCase() + name.substring(1);
        color = AppTheme.accentCyan;
    }

    final isDarkChip = color == AppTheme.borderSubtle;
    return ElevatedButton(
      onPressed: _sending ? null : () => _send(action),
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        foregroundColor: isDarkChip ? Colors.white : AppTheme.bgDark0,
        elevation: 2,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
      child: Text(label,
          style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 12)),
    );
  }

  Widget _waitingPanel() {
    final isOwner = _game.ownerId != 0 &&
        _game.players.any((p) => p['is_me'] == true && p['seat'] == 0);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.table_restaurant,
                size: 54, color: AppTheme.accentCyan),
            const SizedBox(height: 12),
            Text('Waiting for players ${_game.players.length}/4',
                style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            Text(
              _game.players.map((p) => '${p['name']}').join(', '),
              textAlign: TextAlign.center,
              style:
                  const TextStyle(color: AppTheme.borderSubtle, fontSize: 13),
            ),
            const SizedBox(height: 22),
            if (isOwner)
              ElevatedButton.icon(
                onPressed: _sending ? null : _startTable,
                icon: const Icon(Icons.play_arrow),
                label: const Text('Start now (fill with bots)'),
                style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.accentEmerald),
              ),
            const SizedBox(height: 10),
            if (isOwner)
              TextButton(
                onPressed: _sending ? null : _cancelTable,
                child: const Text('Cancel & refund stake',
                    style: TextStyle(color: AppTheme.accentRose)),
              ),
          ],
        ),
      ),
    );
  }

  // ------------------------------------------------------------------ render
  @override
  Widget build(BuildContext context) {
    final phase = _game.phase.toUpperCase();
    final turnText = _game.over
        ? 'Deal complete'
        : _game.isMyTurn
            ? (_game.controlsDummy
                ? 'Play dummy'
                : _game.phase == 'setting_trump'
                    ? 'Choose trump'
                    : 'Your turn')
            : 'Waiting...';

    return Scaffold(
      backgroundColor: AppTheme.bgPure,
      appBar: AppBar(
        backgroundColor: AppTheme.bgDark0,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(_game.title,
                style: const TextStyle(
                    fontSize: 16, fontWeight: FontWeight.w800)),
            Text(
              '$phase · $turnText'
              '${_game.stake > 0 ? ' · stake ${_game.stake}' : ''}',
              style: TextStyle(
                  fontSize: 11,
                  color: _game.isMyTurn
                      ? AppTheme.accentEmerald
                      : AppTheme.borderSubtle),
            ),
          ],
        ),
        actions: [
          if (_game.pot > 0)
            Center(
              child: Container(
                margin: const EdgeInsets.only(right: 8),
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: AppTheme.accentAmber.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: AppTheme.accentAmber),
                ),
                child: Text('pot ${_game.pot}',
                    style: const TextStyle(
                        color: AppTheme.accentAmber,
                        fontSize: 12,
                        fontWeight: FontWeight.bold)),
              ),
            ),
          IconButton(
            tooltip: 'Re-read table',
            icon: const Icon(Icons.refresh, size: 20),
            onPressed: _sending ? null : _refresh,
          ),
        ],
      ),
      body: _game.status == 'waiting'
          ? _waitingPanel()
          : SafeArea(
              child: Column(
                children: [
                  if (_hint != null)
                    Container(
                      width: double.infinity,
                      margin: const EdgeInsets.fromLTRB(12, 8, 12, 0),
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: AppTheme.accentRose.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: AppTheme.accentRose),
                      ),
                      child: Text(_hint!,
                          style: const TextStyle(
                              color: Colors.white, fontSize: 12)),
                    ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(12, 10, 12, 4),
                    child: Row(
                      children: [
                        _opponentSeat(1),
                        _opponentSeat(2, isPartner: true),
                        _opponentSeat(3),
                      ],
                    ),
                  ),
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 6),
                      child: Column(
                        children: [
                          _trickArea(),
                          const SizedBox(height: 10),
                          _promptButtons(),
                          const SizedBox(height: 4),
                          _logPanel(),
                        ],
                      ),
                    ),
                  ),
                  if (_sending)
                    const LinearProgressIndicator(
                        minHeight: 2, color: AppTheme.accentCyan),
                  _myHandBar(),
                ],
              ),
            ),
    );
  }

  Widget _logPanel() {
    final lines = _game.log.length > 6
        ? _game.log.sublist(_game.log.length - 6)
        : _game.log;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: AppTheme.bgGlass,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.borderSubtle),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('TABLE LOG',
              style: TextStyle(
                  color: AppTheme.borderSubtle,
                  fontSize: 10,
                  letterSpacing: 1.5)),
          const SizedBox(height: 6),
          for (final line in lines)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 1),
              child: Text(line,
                  style: const TextStyle(
                      color: AppTheme.accentIndigo, fontSize: 11)),
            ),
        ],
      ),
    );
  }

  Widget _myHandBar() {
    final hand = _game.hand;
    final playable = _game.playableCards;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 14),
      decoration: const BoxDecoration(
        color: AppTheme.bgDark1,
        border: Border(top: BorderSide(color: AppTheme.borderSubtle)),
      ),
      child: Column(
        children: [
          Row(
            children: [
              const Icon(Icons.person, size: 14, color: AppTheme.accentCyan),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  '${_game.labelFor(_game.mySeat)}'
                  '${hand.isEmpty ? '' : ' · ${hand.length} cards'}'
                  '${_game.isMyTurn ? ' · YOUR TURN' : ''}',
                  style: TextStyle(
                      color: _game.isMyTurn
                          ? AppTheme.accentEmerald
                          : AppTheme.borderSubtle,
                      fontSize: 12,
                      fontWeight: FontWeight.w700),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          SizedBox(
            height: 96,
            child: ListView(
              scrollDirection: Axis.horizontal,
              children: [
                for (final card in hand)
                  Padding(
                    padding: const EdgeInsets.only(right: 6),
                    child: _cardFace(
                      card,
                      playable: playable.contains(card),
                      onTap: playable.contains(card)
                          ? () => _send({'action': 'play', 'card': card})
                          : null,
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

extension on CardGame {
  String winnerText() {
    final winner = raw['winner'];
    if (winner is int) return '${labelFor(winner)} wins the deal!';
    final team = raw['winner_team'];
    if (team is String && team.isNotEmpty) {
      final seats = team == 'team0' ? [0, 2] : [1, 3];
      return '${seats.map(labelFor).join(' & ')} win the deal!';
    }
    return 'Scores have been settled.';
  }
}
