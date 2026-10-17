import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

class ApiConstants {
  // Default host resolution:
  // Android emulator uses 10.0.2.2 to reach host machine localhost:8000
  // Windows, macOS, Linux, and iOS simulator use 127.0.0.1:8000
  static String get defaultBaseUrl {
    if (kIsWeb) return 'http://127.0.0.1:8000';
    try {
      if (Platform.isAndroid) {
        return 'http://10.0.2.2:8000';
      }
    } catch (_) {}
    return 'http://127.0.0.1:8000';
  }

  // Endpoints
  static const String login = '/api/v1/auth/login';
  static const String register = '/api/v1/auth/register';
  static const String firebaseLogin = '/api/v1/auth/firebase-login';
  static const String me = '/api/v1/auth/me';
  static const String logout = '/api/v1/auth/logout';

  static const String scramble = '/api/scramble';
  static const String solve = '/api/solve';
  static const String scanImage = '/api/scan-image';
  static const String scanJson = '/api/v1/cube/scan-json';
  static const String history = '/api/history';
  static const String patterns = '/api/patterns';

  static const String profile = '/api/v1/profile';
  static const String profileUpdate = '/api/v1/profile/update';
  static const String clearHistory = '/api/v1/profile/clear-history';

  // Playing cards (Classic Suite practice + money tables)
  static const String cardCatalog = '/api/v1/cards/catalog';
  static const String cardWallet = '/api/v1/cards/wallet';
  static const String cardLedger = '/api/v1/cards/ledger';
  static const String cardPractice = '/api/v1/cards/practice';
  static const String cardPracticeActive = '/api/v1/cards/practice/active';
  static const String cardClassic = '/api/v1/cards/classic';
  static const String cardClassicActive = '/api/v1/cards/classic/active';
  static const String cardClassicTables = '/api/v1/cards/classic/tables';
}
