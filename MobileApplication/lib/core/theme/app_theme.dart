import 'package:flutter/material.dart';

class AppTheme {
  // Web Platform Dark Visual Palette
  static const Color bgPure = Color(0xFF090D16);
  static const Color bgDark0 = Color(0xFF060911);
  static const Color bgDark1 = Color(0xFF0D1322);
  static const Color bgDark2 = Color(0xFF141C30);
  static const Color bgCard = Color(0xFF10172A);
  static const Color bgGlass = Color(0xD90D1322); // 85% opacity

  static const Color borderSubtle = Color(0xFF334155);
  static const Color borderGlow = Color(0x736366F1); // Indigo glow
  static const Color borderGlowCyan = Color(0x7338BDF8); // Cyan glow

  // Vibrant Accents
  static const Color accentIndigo = Color(0xFF818CF8);
  static const Color accentMain = Color(0xFF6366F1);
  static const Color accentCyan = Color(0xFF38BDF8);
  static const Color accentEmerald = Color(0xFF10B981);
  static const Color accentAmber = Color(0xFFF59E0B);
  static const Color accentRose = Color(0xFFF43F5E);
  static const Color accentPurple = Color(0xFFC084FC);

  // Rubik's Cube Facelet Palette (Matches Web App / OpenCV Classification)
  static const Color cubeYellow = Color(0xFFFACC15); // U
  static const Color cubeWhite = Color(0xFFFFFFFF);  // D
  static const Color cubeGreen = Color(0xFF22C55E);  // F
  static const Color cubeBlue = Color(0xFF3B82F6);   // B
  static const Color cubeOrange = Color(0xFFF97316); // L
  static const Color cubeRed = Color(0xFFEF4444);    // R

  static Color getFaceletColor(String code) {
    switch (code.toUpperCase()) {
      case 'Y':
      case 'U':
        return cubeYellow;
      case 'W':
      case 'D':
        return cubeWhite;
      case 'G':
      case 'F':
        return cubeGreen;
      case 'B':
        return cubeBlue;
      case 'O':
      case 'L':
        return cubeOrange;
      case 'R':
        return cubeRed;
      default:
        return Colors.grey.shade700;
    }
  }

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: bgPure,
      primaryColor: accentMain,
      colorScheme: const ColorScheme.dark(
        primary: accentMain,
        secondary: accentCyan,
        surface: bgDark1,
        surfaceContainerHighest: bgDark2,
        error: accentRose,
        onPrimary: Colors.white,
        onSecondary: Colors.black,
        onSurface: Color(0xFFE2E8F0),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: bgDark0,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: Colors.white,
          fontSize: 18,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.5,
        ),
      ),
      cardTheme: CardThemeData(
        color: bgCard,
        elevation: 2,
        shape: RoundedRectangleBorder(
          side: const BorderSide(color: borderSubtle, width: 1),
          borderRadius: BorderRadius.circular(16),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: accentMain,
          foregroundColor: Colors.white,
          elevation: 4,
          shadowColor: accentMain.withOpacity(0.4),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.3,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: bgDark2,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: borderSubtle),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: borderSubtle),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: accentIndigo, width: 2),
        ),
        hintStyle: const TextStyle(color: Color(0xFF64748B), fontSize: 14),
        labelStyle: const TextStyle(color: Color(0xFF94A3B8), fontSize: 14),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: bgDark0,
        selectedItemColor: accentCyan,
        unselectedItemColor: Color(0xFF64748B),
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),
    );
  }
}
