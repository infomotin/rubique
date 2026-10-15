import 'dart:convert';
import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/database/app_database.dart';
import '../../../core/network/api_client.dart';

class OfflineViewScreen extends StatefulWidget {
  final AppDatabase db;
  final ApiClient apiClient;
  final VoidCallback onRetryOnline;

  const OfflineViewScreen({
    super.key,
    required this.db,
    required this.apiClient,
    required this.onRetryOnline,
  });

  @override
  State<OfflineViewScreen> createState() => _OfflineViewScreenState();
}

class _OfflineViewScreenState extends State<OfflineViewScreen> {
  CachedUserProfileData? _profile;
  List<CachedSolve> _solves = [];
  List<CachedPattern> _patterns = [];
  List<CachedScanResult> _scans = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadOfflineData();
  }

  Future<void> _loadOfflineData() async {
    setState(() => _isLoading = true);
    final prof = await widget.db.getOfflineProfile();
    final s = await widget.db.getOfflineSolves();
    final p = await widget.db.getOfflinePatterns();
    final sc = await widget.db.getOfflineScanResults();

    if (!mounted) return;
    setState(() {
      _profile = prof;
      _solves = s;
      _patterns = p;
      _scans = sc;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Offline Data Vault (Drift SQLite)'),
        actions: [
          IconButton(
            icon: const Icon(Icons.wifi_find, color: AppTheme.accentCyan),
            tooltip: 'Attempt Online Reconnect',
            onPressed: widget.onRetryOnline,
          ),
        ],
      ),
      body: SafeArea(
        child: _isLoading
            ? const Center(child: CircularProgressIndicator(color: AppTheme.accentCyan))
            : RefreshIndicator(
                onRefresh: _loadOfflineData,
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Offline Notice Banner
                      Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: AppTheme.accentAmber.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: AppTheme.accentAmber.withOpacity(0.4)),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.cloud_off, color: AppTheme.accentAmber, size: 28),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'READ-ONLY OFFLINE MODE',
                                    style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.accentAmber, fontSize: 13),
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    'Viewing previously synced records from local Drift SQLite database. Writes and new OpenCV processing require an active network connection.',
                                    style: TextStyle(color: Colors.white.withOpacity(0.85), fontSize: 12),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Reconnect Action Button
                      ElevatedButton.icon(
                        icon: const Icon(Icons.sync),
                        label: const Text('Try Reconnecting to Backend'),
                        onPressed: widget.onRetryOnline,
                      ),
                      const SizedBox(height: 16),

                      // Cached Profile Info
                      if (_profile != null) ...[
                        Card(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    CircleAvatar(
                                      backgroundColor: AppTheme.accentMain,
                                      child: Text(
                                        _profile!.username.isNotEmpty ? _profile!.username[0].toUpperCase() : 'C',
                                        style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
                                      ),
                                    ),
                                    const SizedBox(width: 12),
                                    Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          _profile!.username,
                                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white),
                                        ),
                                        Text(
                                          'Last synced: ${_profile!.lastSyncedAt.split('T').first}',
                                          style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 11),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 14),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                                  children: [
                                    _buildMiniStat('TOTAL SOLVES', '${_profile!.totalSolves}'),
                                    _buildMiniStat('MIN MOVES', '${_profile!.minMoves}'),
                                    _buildMiniStat('AVG MOVES', '${_profile!.avgMoves.toStringAsFixed(1)}'),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                      ],

                      // Cached Solves Section
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  const Text(
                                    'Cached Solve History',
                                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
                                  ),
                                  Text(
                                    '${_solves.length} cached',
                                    style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 10),
                              if (_solves.isEmpty) ...[
                                const Text(
                                  'No previously synced solves found in offline database.',
                                  style: TextStyle(color: Color(0xFF64748B), fontSize: 12),
                                ),
                              ] else ...[
                                ListView.separated(
                                  shrinkWrap: true,
                                  physics: const NeverScrollableScrollPhysics(),
                                  itemCount: _solves.length > 8 ? 8 : _solves.length,
                                  separatorBuilder: (_, __) => const Divider(color: AppTheme.borderSubtle),
                                  itemBuilder: (_, idx) {
                                    final s = _solves[idx];
                                    return ListTile(
                                      contentPadding: EdgeInsets.zero,
                                      leading: Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                        decoration: BoxDecoration(
                                          color: AppTheme.accentEmerald.withOpacity(0.15),
                                          borderRadius: BorderRadius.circular(6),
                                        ),
                                        child: Text(
                                          '${s.moveCount}m',
                                          style: const TextStyle(color: AppTheme.accentEmerald, fontWeight: FontWeight.bold),
                                        ),
                                      ),
                                      title: Text(
                                        s.solution,
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style: const TextStyle(color: Colors.white, fontSize: 12, fontFamily: 'monospace'),
                                      ),
                                      subtitle: Text(
                                        s.scramble,
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 11),
                                      ),
                                    );
                                  },
                                ),
                              ],
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Cached Patterns Section
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  const Text(
                                    'Cached Pattern Library',
                                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
                                  ),
                                  Text(
                                    '${_patterns.length} patterns',
                                    style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 10),
                              if (_patterns.isEmpty) ...[
                                const Text(
                                  'No patterns cached offline yet.',
                                  style: TextStyle(color: Color(0xFF64748B), fontSize: 12),
                                ),
                              ] else ...[
                                ..._patterns.take(4).map((p) => Padding(
                                      padding: const EdgeInsets.symmetric(vertical: 4),
                                      child: Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Text(p.name, style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold)),
                                          Text(p.moves, style: const TextStyle(color: AppTheme.accentCyan, fontSize: 11, fontFamily: 'monospace')),
                                        ],
                                      ),
                                    )),
                              ],
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
      ),
    );
  }

  Widget _buildMiniStat(String label, String value) {
    return Column(
      children: [
        Text(value, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.accentCyan)),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(fontSize: 9, color: Color(0xFF94A3B8), fontWeight: FontWeight.w600)),
      ],
    );
  }
}
