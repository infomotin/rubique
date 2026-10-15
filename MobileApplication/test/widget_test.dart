import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:drift/native.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/core/database/app_database.dart';
import 'package:mobile_app/core/theme/app_theme.dart';
import 'package:mobile_app/features/auth/auth_service.dart';
import 'package:mobile_app/features/auth/screens/login_screen.dart';
import 'package:mobile_app/features/cube/cube_service.dart';
import 'package:mobile_app/features/cube/screens/visualizer_screen.dart';

void main() {
  late SharedPreferences prefs;
  late AppDatabase db;
  late ApiClient apiClient;
  late AuthService authService;
  late CubeService cubeService;

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    prefs = await SharedPreferences.getInstance();
    db = AppDatabase(NativeDatabase.memory());
    apiClient = ApiClient(prefs);
    authService = AuthService(apiClient, db);
    cubeService = CubeService(apiClient, db);
  });

  tearDown(() async {
    await db.close();
  });

  testWidgets('LoginScreen renders brand, demo fill buttons, and input fields', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.darkTheme,
        home: LoginScreen(
          authService: authService,
          apiClient: apiClient,
          onLoginSuccess: () {},
        ),
      ),
    );

    // Verify brand
    expect(find.text('CubePermutation AI'), findsWidgets);
    expect(find.text('Member Sign In'), findsOneWidget);

    // Verify demo quick-fill chips
    expect(find.text('Speedcuber (speedcuber)'), findsOneWidget);
    expect(find.text('Admin (admin)'), findsOneWidget);
    expect(find.text('Developer (developer)'), findsOneWidget);

    // Verify Firebase token sign in button
    expect(find.text('Sign In via Firebase Auth Token'), findsOneWidget);

    // Tap demo chip for admin
    await tester.tap(find.text('Admin (admin)'));
    await tester.pump();

    // Verify username text field updated
    expect(find.text('admin'), findsOneWidget);
  });

  testWidgets('VisualizerScreen renders 3x3 interactive facelet grid and action buttons', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.darkTheme,
        home: VisualizerScreen(
          cubeService: cubeService,
        ),
      ),
    );

    // Verify laboratory title
    expect(find.text('Cube Permutation Laboratory'), findsOneWidget);

    // Verify face selector tabs
    expect(find.text('Up (Top)'), findsOneWidget);
    expect(find.text('Front'), findsOneWidget);

    // Verify Scramble and Solve buttons
    expect(find.text('Scramble'), findsOneWidget);
    expect(find.text('Solve Cube'), findsOneWidget);

    // Verify 9 stickers rendered for current face
    expect(find.byType(GridView), findsOneWidget);
  });
}
