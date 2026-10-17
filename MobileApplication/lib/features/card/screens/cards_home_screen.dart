/// Cards tab: wallet, resume banner, the Classic Suite catalogue and the
/// practice / money table entry points.
library;

import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import '../card_service.dart';
import '../models/card_game.dart';
import 'card_game_screen.dart';

class CardsHomeScreen extends StatefulWidget {
  final CardService cardService;

  const CardsHomeScreen({super.key, required this.cardService});

  @override
  State<CardsHomeScreen> createState() => _CardsHomeScreenState();
}

class _CardsHomeScreenState extends State<CardsHomeScreen> {
  List<CatalogEntry> _entries = const [];
  WalletSnapshot? _wallet;
  CardGame? _practiceGame;
  CardGame? _classicGame;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final entries = await widget.cardService.fetchCatalog();
    final wallet = await widget.cardService.fetchWallet();
    final practice = await widget.cardService.practiceActive();
    final classic = await widget.cardService.classicActive();
    if (!mounted) return;
    setState(() {
      _entries = entries ?? _entries;
      _wallet = wallet;
      _practiceGame = practice;
      _classicGame = classic;
      _loading = false;
    });
  }

  Future<void> _openGame(CardGame game) async {
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => CardGameScreen(
          cardService: widget.cardService,
          initialGame: game,
          onClosed: () {},
          onDealFinished: (_) async {
            final wallet = await widget.cardService.fetchWallet();
            if (mounted && wallet != null) setState(() => _wallet = wallet);
          },
        ),
      ),
    );
    if (mounted) _load();
  }

  Future<void> _start(CatalogEntry entry, {required bool money}) async {
    var stake = 0;
    if (money) {
      final picked = await _stakeSheet(entry.name);
      if (picked == null) return;
      stake = picked;
    }

    final CardGame? game = money
        ? await widget.cardService.classicStart(
            slug: entry.slug, mode: 'ai', stake: stake)
        : await widget.cardService.practiceStart(entry.slug);

    if (!mounted) return;
    if (game == null) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(widget.cardService.lastError ?? 'Could not start table'),
        backgroundColor: AppTheme.accentRose,
      ));
      return;
    }
    await _openGame(game);
  }

  Future<int?> _stakeSheet(String gameName) async {
    return showModalBottomSheet<int>(
      context: context,
      backgroundColor: AppTheme.bgCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        var stake = 0;
        return StatefulBuilder(
          builder: (ctx, setSheetState) {
            final balance = _wallet?.personal ?? 0;
            return Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Money table · $gameName',
                      style: const TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.w800)),
                  const SizedBox(height: 6),
                  Text('Your coins: $balance',
                      style: const TextStyle(
                          color: AppTheme.accentAmber, fontSize: 13)),
                  const SizedBox(height: 16),
                  Wrap(
                    spacing: 8,
                    children: [
                      for (final v in [0, 10, 25, 50, 100, 250, 500])
                        ChoiceChip(
                          label: Text('$v'),
                          selected: stake == v,
                          selectedColor: AppTheme.accentEmerald,
                          onSelected: (_) =>
                              setSheetState(() => stake = v),
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    stake == 0
                        ? 'No stake - winner takes bragging rights only.'
                        : 'Stake is escrowed from your wallet; the pot is '
                            'settled back out in one zero-sum ledger entry.',
                    style: const TextStyle(
                        color: AppTheme.borderSubtle, fontSize: 12),
                  ),
                  const SizedBox(height: 18),
                  Row(
                    children: [
                      TextButton(
                        onPressed: () => Navigator.of(ctx).pop(),
                        child: const Text('Cancel',
                            style: TextStyle(color: AppTheme.borderSubtle)),
                      ),
                      const Spacer(),
                      ElevatedButton(
                        onPressed: () => Navigator.of(ctx).pop(stake),
                        style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.accentEmerald),
                        child: const Text('Deal me in'),
                      ),
                    ],
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  void _showLedger() {
    final wallet = _wallet;
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: AppTheme.bgCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.account_balance_wallet,
                    color: AppTheme.accentAmber, size: 18),
                const SizedBox(width: 8),
                Text('Coin ledger · ${wallet?.personal ?? 0}',
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 15,
                        fontWeight: FontWeight.w800)),
              ],
            ),
            const SizedBox(height: 4),
            const Text('Hash-chained, newest first',
                style: TextStyle(color: AppTheme.borderSubtle, fontSize: 11)),
            const SizedBox(height: 12),
            SizedBox(
              height: 320,
              child: (wallet == null || wallet.ledger.isEmpty)
                  ? const Center(
                      child: Text('No transactions yet',
                          style: TextStyle(color: AppTheme.borderSubtle)))
                  : ListView.separated(
                      itemCount: wallet.ledger.length,
                      separatorBuilder: (_, __) => const Divider(
                          color: AppTheme.borderSubtle, height: 1),
                      itemBuilder: (_, i) {
                        final e = wallet.ledger[i];
                        final color = e.amount >= 0
                            ? AppTheme.accentEmerald
                            : AppTheme.accentRose;
                        return ListTile(
                          dense: true,
                          title: Text(
                              '${e.entryType}${e.refType == 'classic_game' ? ' · classic table ${e.refId ?? ''}' : ''}',
                              style: const TextStyle(
                                  color: Colors.white, fontSize: 13)),
                          subtitle: Text(
                              '#${e.seq} · ${e.note}',
                              style: const TextStyle(
                                  color: AppTheme.borderSubtle,
                                  fontSize: 11)),
                          trailing: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text('${e.amount >= 0 ? '+' : ''}${e.amount}',
                                  style: TextStyle(
                                      color: color,
                                      fontWeight: FontWeight.bold)),
                              Text('${e.balanceAfter}',
                                  style: const TextStyle(
                                      color: AppTheme.borderSubtle,
                                      fontSize: 11)),
                            ],
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _walletCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppTheme.accentAmber.withOpacity(0.18),
            AppTheme.bgCard,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.accentAmber.withOpacity(0.5)),
      ),
      child: Row(
        children: [
          const Icon(Icons.monetization_on_outlined,
              color: AppTheme.accentAmber, size: 34),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('WALLET',
                    style: TextStyle(
                        color: AppTheme.accentAmber,
                        fontSize: 10,
                        letterSpacing: 2)),
                Text(
                  '${_wallet?.personal ?? 0} coins',
                  style: const TextStyle(
                      color: Colors.white,
                      fontSize: 22,
                      fontWeight: FontWeight.w800),
                ),
                Text('escrow hold ${_wallet?.reserve ?? 0} · chain verified',
                    style: const TextStyle(
                        color: AppTheme.borderSubtle, fontSize: 11)),
              ],
            ),
          ),
          TextButton.icon(
            onPressed: _showLedger,
            icon: const Icon(Icons.receipt_long,
                size: 16, color: AppTheme.accentCyan),
            label: const Text('Ledger',
                style: TextStyle(color: AppTheme.accentCyan, fontSize: 12)),
          ),
        ],
      ),
    );
  }

  Widget _resumeCard() {
    final game = _classicGame ?? _practiceGame;
    if (game == null) return const SizedBox.shrink();
    final isMoney = _classicGame != null;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.bgGlass,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.borderGlowCyan),
      ),
      child: Row(
        children: [
          const Icon(Icons.play_circle_outline,
              color: AppTheme.accentCyan, size: 30),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isMoney ? 'Money table in progress' : 'Practice deal in progress',
                  style: const TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      fontWeight: FontWeight.w700),
                ),
                Text(
                  '${game.title} · ${game.phase} · ${game.hand.length} cards',
                  style: const TextStyle(
                      color: AppTheme.borderSubtle, fontSize: 12),
                ),
              ],
            ),
          ),
          ElevatedButton(
            onPressed: () => _openGame(game),
            style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.accentMain),
            child: const Text('Resume'),
          ),
        ],
      ),
    );
  }

  Widget _catalogCard(CatalogEntry entry) {
    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: () => _showStartSheet(entry),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppTheme.bgCard,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppTheme.borderSubtle),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.style, color: AppTheme.accentPurple, size: 18),
                const Spacer(),
                Text(entry.players,
                    style: const TextStyle(
                        color: AppTheme.borderSubtle, fontSize: 10)),
              ],
            ),
            const SizedBox(height: 8),
            Text(entry.name,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w800)),
            const SizedBox(height: 4),
            Expanded(
              child: Text(
                entry.description,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                    color: AppTheme.borderSubtle, fontSize: 11, height: 1.3),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showStartSheet(CatalogEntry entry) {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: AppTheme.bgCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(entry.name,
                style: const TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.w800)),
            const SizedBox(height: 4),
            Text(entry.description,
                style: const TextStyle(
                    color: AppTheme.borderSubtle, fontSize: 12)),
            const SizedBox(height: 18),
            ListTile(
              leading: const Icon(Icons.smart_toy_outlined,
                  color: AppTheme.accentEmerald),
              title: const Text('Practice vs AI',
                  style: TextStyle(color: Colors.white)),
              subtitle: const Text('Free, no coins at stake',
                  style:
                      TextStyle(color: AppTheme.borderSubtle, fontSize: 12)),
              onTap: () {
                Navigator.of(ctx).pop();
                _start(entry, money: false);
              },
            ),
            ListTile(
              leading: const Icon(Icons.payments_outlined,
                  color: AppTheme.accentAmber),
              title: const Text('Money table (stake)',
                  style: TextStyle(color: Colors.white)),
              subtitle:
                  const Text('Escrowed coins, zero-sum settlement',
                      style:
                          TextStyle(color: AppTheme.borderSubtle, fontSize: 12)),
              onTap: () {
                Navigator.of(ctx).pop();
                _start(entry, money: true);
              },
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPure,
      appBar: AppBar(
        backgroundColor: AppTheme.bgDark0,
        title: const Text('Playing Cards',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
        actions: [
          IconButton(
            tooltip: 'Refresh wallet and tables',
            icon: const Icon(Icons.refresh, size: 20),
            onPressed: _loading ? null : _load,
          ),
        ],
      ),
      body: RefreshIndicator(
        color: AppTheme.accentCyan,
        onRefresh: _load,
        child: _loading && _entries.isEmpty
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _walletCard(),
                  const SizedBox(height: 14),
                  _resumeCard(),
                  const SizedBox(height: 18),
                  Row(
                    children: [
                      const Icon(Icons.grid_view,
                          color: AppTheme.accentIndigo, size: 16),
                      const SizedBox(width: 8),
                      const Text('CLASSIC SUITE',
                          style: TextStyle(
                              color: AppTheme.accentIndigo,
                              fontSize: 11,
                              letterSpacing: 2,
                              fontWeight: FontWeight.w800)),
                      const Spacer(),
                      if (widget.cardService.isBusy)
                        const SizedBox(
                          width: 14,
                          height: 14,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: AppTheme.accentCyan),
                        ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  GridView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    gridDelegate:
                        const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      mainAxisSpacing: 12,
                      crossAxisSpacing: 12,
                      childAspectRatio: 0.95,
                    ),
                    itemCount: _entries.length,
                    itemBuilder: (_, i) => _catalogCard(_entries[i]),
                  ),
                  const SizedBox(height: 24),
                ],
              ),
      ),
    );
  }
}
