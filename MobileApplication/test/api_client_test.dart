import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:mobile_app/core/network/api_client.dart';

void main() {
  group('ApiClient Tests', () {
    test('Stores and updates Flask session cookie and Firebase token', () async {
      SharedPreferences.setMockInitialValues({});
      final prefs = await SharedPreferences.getInstance();
      final client = ApiClient(prefs);

      expect(client.hasSession, isFalse);

      const testCookie = '.eJyrVirKz0lVslIqLU4tUtIBU_GZKUpWxhB2XmIuSLa4IDU1Jbk0CaimFgC5qRFk.atB0sw.NQmR9yXixupBGcnQoRwMh2vyiC8';
      await client.saveSessionCookie(testCookie);

      expect(client.sessionCookie, testCookie);
      expect(client.hasSession, isTrue);

      const testToken = 'mock_firebase_jwt_token_12345';
      await client.saveFirebaseToken(testToken);
      expect(client.firebaseToken, testToken);

      await client.clearSession();
      expect(client.sessionCookie, isNull);
      expect(client.firebaseToken, isNull);
      expect(client.hasSession, isFalse);
    });

    test('Custom Base URL setting and normalization', () async {
      SharedPreferences.setMockInitialValues({});
      final prefs = await SharedPreferences.getInstance();
      final client = ApiClient(prefs);

      await client.setBaseUrl('http://192.168.1.50:8000///');
      expect(client.baseUrl, 'http://192.168.1.50:8000');
    });
  });
}
