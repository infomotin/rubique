import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/network/api_client.dart';
import '../../../core/constants/api_constants.dart';
import '../../auth/auth_service.dart';
import '../../cube/cube_service.dart';

class ProfileScreen extends StatefulWidget {
  final AuthService authService;
  final ApiClient apiClient;
  final CubeService cubeService;
  final VoidCallback onLogout;

  const ProfileScreen({
    super.key,
    required this.authService,
    required this.apiClient,
    required this.cubeService,
    required this.onLogout,
  });

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  Map<String, dynamic>? _profileData;
  List<SolveHistoryItem> _history = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _fetchProfile();
  }

  Future<void> _fetchProfile() async {
    setState(() => _isLoading = true);
    final res = await widget.apiClient.get(ApiConstants.profile);
    final historyItems = await widget.cubeService.fetchAndCacheSolveHistory();

    if (!mounted) return;
    setState(() {
      _isLoading = false;
      if (res.isSuccess && res.data is Map) {
        _profileData = Map<String, dynamic>.from(res.data);
      }
      _history = historyItems;
    });
  }

  void _showEditDialog() {
    final user = widget.authService.currentUser;
    if (user == null) return;

    final bioCtrl = TextEditingController(text: user.bio);
    final wcaCtrl = TextEditingController(text: user.wcaId);
    final countryCtrl = TextEditingController(text: user.country);
    final cubeCtrl = TextEditingController(text: user.mainCube);
    final methodCtrl = TextEditingController(text: user.preferredMethod);
    final pbSingleCtrl = TextEditingController(text: user.pbSingle);
    final pbAo5Ctrl = TextEditingController(text: user.pbAo5);

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.bgDark1,
        title: const Text('Edit Speedcubing Credentials', style: TextStyle(color: Colors.white)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: bioCtrl, decoration: const InputDecoration(labelText: 'Bio')),
              const SizedBox(height: 10),
              TextField(controller: cubeCtrl, decoration: const InputDecoration(labelText: 'Main Cube (e.g. GAN 12)')),
              const SizedBox(height: 10),
              TextField(controller: methodCtrl, decoration: const InputDecoration(labelText: 'Method (CFOP/Roux/ZZ)')),
              const SizedBox(height: 10),
              TextField(controller: wcaCtrl, decoration: const InputDecoration(labelText: 'WCA ID')),
              const SizedBox(height: 10),
              TextField(controller: countryCtrl, decoration: const InputDecoration(labelText: 'Country')),
              const SizedBox(height: 10),
              TextField(controller: pbSingleCtrl, decoration: const InputDecoration(labelText: 'PB Single (seconds)')),
              const SizedBox(height: 10),
              TextField(controller: pbAo5Ctrl, decoration: const InputDecoration(labelText: 'PB Ao5 (seconds)')),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              await widget.apiClient.post(
                ApiConstants.profileUpdate,
                body: {
                  'bio': bioCtrl.text,
                  'main_cube': cubeCtrl.text,
                  'preferred_method': methodCtrl.text,
                  'wca_id': wcaCtrl.text,
                  'country': countryCtrl.text,
                  'pb_single': pbSingleCtrl.text,
                  'pb_ao5': pbAo5Ctrl.text,
                },
              );
              _fetchProfile();
            },
            child: const Text('Save Changes'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final user = widget.authService.currentUser;
    final stats = _profileData?['stats'] as Map?;
    final coins = _profileData?['coins_balance'] ?? 1000;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Speedcuber Profile'),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit_outlined, color: AppTheme.accentCyan),
            tooltip: 'Edit Credentials',
            onPressed: _showEditDialog,
          ),
          IconButton(
            icon: const Icon(Icons.logout, color: AppTheme.accentRose),
            tooltip: 'Sign Out',
            onPressed: () async {
              await widget.authService.logout();
              widget.onLogout();
            },
          ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _fetchProfile,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (_isLoading) ...[
                  const LinearProgressIndicator(color: AppTheme.accentCyan),
                  const SizedBox(height: 10),
                ],
                // Profile Header Card
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Row(
                      children: [
                        CircleAvatar(
                          radius: 32,
                          backgroundColor: AppTheme.accentMain,
                          child: Text(
                            (user?.username.isNotEmpty == true ? user!.username[0].toUpperCase() : 'C'),
                            style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Text(
                                    user?.username ?? 'Speedcuber',
                                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                                  ),
                                  const SizedBox(width: 8),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: AppTheme.accentIndigo.withOpacity(0.2),
                                      borderRadius: BorderRadius.circular(6),
                                      border: Border.all(color: AppTheme.accentIndigo.withOpacity(0.5)),
                                    ),
                                    child: Text(
                                      (user?.role ?? 'user').toUpperCase(),
                                      style: const TextStyle(fontSize: 10, color: AppTheme.accentIndigo, fontWeight: FontWeight.bold),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 4),
                              Text(
                                user?.bio.isNotEmpty == true ? user!.bio : 'Group Theory Explorer & Speedcuber',
                                style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
                              ),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  const Icon(Icons.monetization_on, color: AppTheme.accentAmber, size: 16),
                                  const SizedBox(width: 4),
                                  Text(
                                    '$coins Coins',
                                    style: const TextStyle(color: AppTheme.accentAmber, fontWeight: FontWeight.bold, fontSize: 12),
                                  ),
                                  const SizedBox(width: 14),
                                  const Icon(Icons.sports_esports, color: AppTheme.accentCyan, size: 16),
                                  const SizedBox(width: 4),
                                  Text(
                                    user?.mainCube ?? 'GAN 12 MagLev',
                                    style: const TextStyle(color: AppTheme.accentCyan, fontSize: 12),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Analytics Stats Row
                Row(
                  children: [
                    _buildStatCard(
                      'TOTAL SOLVES',
                      '${stats?['total_solves'] ?? 0}',
                      Icons.timer_outlined,
                      AppTheme.accentCyan,
                    ),
                    const SizedBox(width: 12),
                    _buildStatCard(
                      'MIN MOVES',
                      '${stats?['min_moves'] ?? 0}',
                      Icons.bolt,
                      AppTheme.accentEmerald,
                    ),
                    const SizedBox(width: 12),
                    _buildStatCard(
                      'AVG MOVES',
                      '${stats?['avg_moves'] ?? 0.0}',
                      Icons.bar_chart,
                      AppTheme.accentIndigo,
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // Speedcubing Credentials Card
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Speedcubing Credentials',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
                        ),
                        const SizedBox(height: 12),
                        _buildCredentialRow('Preferred Method', user?.preferredMethod ?? 'CFOP'),
                        _buildCredentialRow('WCA ID', user?.wcaId.isNotEmpty == true ? user!.wcaId : 'Unlinked'),
                        _buildCredentialRow('Country', user?.country.isNotEmpty == true ? user!.country : 'International'),
                        _buildCredentialRow('PB Single', user?.pbSingle.isNotEmpty == true ? '${user!.pbSingle}s' : '—'),
                        _buildCredentialRow('PB Ao5', user?.pbAo5.isNotEmpty == true ? '${user!.pbAo5}s' : '—'),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Solve History List
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
                              'Recent Solve History',
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
                            ),
                            Text(
                              '${_history.length} logged',
                              style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        if (_history.isEmpty) ...[
                          const Padding(
                            padding: EdgeInsets.symmetric(vertical: 20),
                            child: Center(
                              child: Text(
                                'No solves logged yet. Solve a scramble in the laboratory to record here!',
                                textAlign: TextAlign.center,
                                style: TextStyle(color: Color(0xFF64748B), fontSize: 13),
                              ),
                            ),
                          ),
                        ] else ...[
                          ListView.separated(
                            shrinkWrap: true,
                            physics: const NeverScrollableScrollPhysics(),
                            itemCount: _history.length > 10 ? 10 : _history.length,
                            separatorBuilder: (_, __) => const Divider(color: AppTheme.borderSubtle),
                            itemBuilder: (_, idx) {
                              final item = _history[idx];
                              return ListTile(
                                contentPadding: EdgeInsets.zero,
                                leading: Container(
                                  padding: const EdgeInsets.all(8),
                                  decoration: BoxDecoration(
                                    color: AppTheme.accentEmerald.withOpacity(0.15),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Text(
                                    '${item.moveCount}m',
                                    style: const TextStyle(
                                      color: AppTheme.accentEmerald,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 12,
                                    ),
                                  ),
                                ),
                                title: Text(
                                  item.solution,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(fontSize: 13, color: Colors.white, fontFamily: 'monospace'),
                                ),
                                subtitle: Text(
                                  item.scramble,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(fontSize: 11, color: Color(0xFF94A3B8)),
                                ),
                              );
                            },
                          ),
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

  Widget _buildStatCard(String label, String value, IconData icon, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 10),
        decoration: BoxDecoration(
          color: AppTheme.bgDark1,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppTheme.borderSubtle),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(height: 6),
            Text(
              value,
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w600, color: Color(0xFF94A3B8), letterSpacing: 0.5),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCredentialRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 13)),
          Text(value, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500, fontSize: 13)),
        ],
      ),
    );
  }
}
