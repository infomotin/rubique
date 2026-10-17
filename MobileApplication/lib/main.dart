import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'core/theme/app_theme.dart';
import 'core/network/api_client.dart';
import 'core/database/app_database.dart';
import 'features/auth/auth_service.dart';
import 'features/auth/screens/login_screen.dart';
import 'features/cube/cube_service.dart';
import 'features/cube/screens/visualizer_screen.dart';
import 'features/scan/scan_service.dart';
import 'features/scan/screens/scan_screen.dart';
import 'features/profile/screens/profile_screen.dart';
import 'features/card/card_service.dart';
import 'features/card/screens/cards_home_screen.dart';
import 'features/offline/screens/offline_view_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize SharedPreferences and Drift SQLite database
  final prefs = await SharedPreferences.getInstance();
  final db = AppDatabase();
  final apiClient = ApiClient(prefs);

  final authService = AuthService(apiClient, db);
  final cubeService = CubeService(apiClient, db);
  final scanService = ScanService(apiClient, db);
  final cardService = CardService(apiClient);

  // Restore active Flask session or cached profile
  await authService.restoreSession();

  runApp(CubePermutationApp(
    prefs: prefs,
    db: db,
    apiClient: apiClient,
    authService: authService,
    cubeService: cubeService,
    scanService: scanService,
    cardService: cardService,
  ));
}

class CubePermutationApp extends StatelessWidget {
  final SharedPreferences prefs;
  final AppDatabase db;
  final ApiClient apiClient;
  final AuthService authService;
  final CubeService cubeService;
  final ScanService scanService;
  final CardService cardService;

  const CubePermutationApp({
    super.key,
    required this.prefs,
    required this.db,
    required this.apiClient,
    required this.authService,
    required this.cubeService,
    required this.scanService,
    required this.cardService,
  });

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CubePermutation AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: AppRoot(
        db: db,
        apiClient: apiClient,
        authService: authService,
        cubeService: cubeService,
        scanService: scanService,
        cardService: cardService,
      ),
    );
  }
}

class AppRoot extends StatefulWidget {
  final AppDatabase db;
  final ApiClient apiClient;
  final AuthService authService;
  final CubeService cubeService;
  final ScanService scanService;
  final CardService cardService;

  const AppRoot({
    super.key,
    required this.db,
    required this.apiClient,
    required this.authService,
    required this.cubeService,
    required this.scanService,
    required this.cardService,
  });

  @override
  State<AppRoot> createState() => _AppRootState();
}

class _AppRootState extends State<AppRoot> {
  int _selectedTabIndex = 0;
  String? _pendingFaceletToSolve;

  @override
  void initState() {
    super.initState();
    widget.authService.addListener(_onAuthChanged);
  }

  @override
  void dispose() {
    widget.authService.removeListener(_onAuthChanged);
    super.dispose();
  }

  void _onAuthChanged() {
    setState(() {});
  }

  void _handleSendToSolver(String faceletString) {
    setState(() {
      _pendingFaceletToSolve = faceletString;
      _selectedTabIndex = 0; // Switch to Visualizer tab
    });
  }

  @override
  Widget build(BuildContext context) {
    // If not authenticated, prompt sign in
    if (!widget.authService.isAuthenticated) {
      return LoginScreen(
        authService: widget.authService,
        apiClient: widget.apiClient,
        onLoginSuccess: () => setState(() {}),
      );
    }

    final pages = [
      VisualizerScreen(
        key: ValueKey(_pendingFaceletToSolve ?? 'visualizer_root'),
        cubeService: widget.cubeService,
        initialFacelets: _pendingFaceletToSolve,
      ),
      ScanScreen(
        scanService: widget.scanService,
        onSendToSolver: _handleSendToSolver,
      ),
      CardsHomeScreen(cardService: widget.cardService),
      ProfileScreen(
        authService: widget.authService,
        apiClient: widget.apiClient,
        cubeService: widget.cubeService,
        onLogout: () => setState(() {}),
      ),
      OfflineViewScreen(
        db: widget.db,
        apiClient: widget.apiClient,
        onRetryOnline: () async {
          final ok = await widget.authService.restoreSession();
          if (!mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(ok ? 'Online connection restored!' : 'Unable to reach backend server.'),
              backgroundColor: ok ? AppTheme.accentEmerald : AppTheme.accentRose,
            ),
          );
        },
      ),
    ];

    return Scaffold(
      body: IndexedStack(
        index: _selectedTabIndex,
        children: pages,
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: AppTheme.borderSubtle, width: 1)),
        ),
        child: BottomNavigationBar(
          currentIndex: _selectedTabIndex,
          onTap: (index) => setState(() => _selectedTabIndex = index),
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.view_in_ar_outlined),
              activeIcon: Icon(Icons.view_in_ar, color: AppTheme.accentCyan),
              label: 'Visualizer',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.camera_alt_outlined),
              activeIcon: Icon(Icons.camera_alt, color: AppTheme.accentCyan),
              label: 'OpenCV Scan',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.style_outlined),
              activeIcon: Icon(Icons.style, color: AppTheme.accentCyan),
              label: 'Cards',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.person_outline),
              activeIcon: Icon(Icons.person, color: AppTheme.accentCyan),
              label: 'Profile',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.cloud_done_outlined),
              activeIcon: Icon(Icons.cloud_done, color: AppTheme.accentAmber),
              label: 'Offline Vault',
            ),
          ],
        ),
      ),
    );
  }
}
