import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../constants/api_constants.dart';

class ApiResponse {
  final int statusCode;
  final bool isSuccess;
  final dynamic data;
  final String? error;

  ApiResponse({
    required this.statusCode,
    required this.isSuccess,
    this.data,
    this.error,
  });
}

class ApiClient {
  static const String _prefCookieKey = 'flask_session_cookie';
  static const String _prefTokenKey = 'firebase_auth_token';
  static const String _prefBaseUrlKey = 'api_base_url';

  final SharedPreferences _prefs;
  String _baseUrl;

  ApiClient(this._prefs)
      : _baseUrl = _prefs.getString(_prefBaseUrlKey) ?? ApiConstants.defaultBaseUrl;

  String get baseUrl => _baseUrl;

  Future<void> setBaseUrl(String url) async {
    _baseUrl = url.trim().replaceAll(RegExp(r'/+$'), '');
    await _prefs.setString(_prefBaseUrlKey, _baseUrl);
  }

  String? get sessionCookie => _prefs.getString(_prefCookieKey);
  String? get firebaseToken => _prefs.getString(_prefTokenKey);

  Future<void> saveSessionCookie(String cookie) async {
    await _prefs.setString(_prefCookieKey, cookie);
  }

  Future<void> saveFirebaseToken(String token) async {
    await _prefs.setString(_prefTokenKey, token);
  }

  Future<void> clearSession() async {
    await _prefs.remove(_prefCookieKey);
    await _prefs.remove(_prefTokenKey);
  }

  bool get hasSession => sessionCookie != null || firebaseToken != null;

  Map<String, String> _buildHeaders({Map<String, String>? extraHeaders}) {
    final headers = <String, String>{
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };

    final cookie = sessionCookie;
    if (cookie != null && cookie.isNotEmpty) {
      // Re-use exact Flask session cookie in standard Cookie header + X-Session-Cookie
      headers['Cookie'] = 'session=$cookie';
      headers['X-Session-Cookie'] = cookie;
    }

    final token = firebaseToken;
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }

    if (extraHeaders != null) {
      headers.addAll(extraHeaders);
    }
    return headers;
  }

  void _extractAndSaveCookies(http.Response response) {
    // 1. Check Set-Cookie headers
    final setCookie = response.headers['set-cookie'];
    if (setCookie != null) {
      final match = RegExp(r'session=([^;]+)').firstMatch(setCookie);
      if (match != null && match.group(1) != null) {
        saveSessionCookie(match.group(1)!);
      }
    }

    // 2. Check JSON payload for explicit session_cookie field
    try {
      final body = jsonDecode(response.body);
      if (body is Map && body['session_cookie'] != null) {
        saveSessionCookie(body['session_cookie'].toString());
      }
    } catch (_) {}
  }

  Future<ApiResponse> get(String endpoint) async {
    try {
      final uri = Uri.parse('$_baseUrl$endpoint');
      final response = await http
          .get(uri, headers: _buildHeaders())
          .timeout(const Duration(seconds: 15));

      _extractAndSaveCookies(response);
      return _parseResponse(response);
    } catch (e) {
      return ApiResponse(
        statusCode: 0,
        isSuccess: false,
        error: 'Network connection error: $e',
      );
    }
  }

  Future<ApiResponse> post(String endpoint, {Map<String, dynamic>? body}) async {
    try {
      final uri = Uri.parse('$_baseUrl$endpoint');
      final response = await http
          .post(
            uri,
            headers: _buildHeaders(),
            body: body != null ? jsonEncode(body) : null,
          )
          .timeout(const Duration(seconds: 20));

      _extractAndSaveCookies(response);
      return _parseResponse(response);
    } catch (e) {
      return ApiResponse(
        statusCode: 0,
        isSuccess: false,
        error: 'Network connection error: $e',
      );
    }
  }

  Future<ApiResponse> delete(String endpoint) async {
    try {
      final uri = Uri.parse('$_baseUrl$endpoint');
      final response = await http
          .delete(uri, headers: _buildHeaders())
          .timeout(const Duration(seconds: 20));

      _extractAndSaveCookies(response);
      return _parseResponse(response);
    } catch (e) {
      return ApiResponse(
        statusCode: 0,
        isSuccess: false,
        error: 'Network connection error: $e',
      );
    }
  }

  Future<ApiResponse> postMultipart(
    String endpoint, {
    required Uint8List fileBytes,
    required String filename,
    Map<String, String>? fields,
  }) async {
    try {
      final uri = Uri.parse('$_baseUrl$endpoint');
      final request = http.MultipartRequest('POST', uri);

      // Add auth headers
      final headers = _buildHeaders();
      headers.remove('Content-Type'); // Let multipart set boundary
      request.headers.addAll(headers);

      if (fields != null) {
        request.fields.addAll(fields);
      }

      final multipartFile = http.MultipartFile.fromBytes(
        'image',
        fileBytes,
        filename: filename,
        contentType: MediaType('image', 'jpeg'),
      );
      request.files.add(multipartFile);

      final streamedResponse = await request.send().timeout(const Duration(seconds: 30));
      final response = await http.Response.fromStream(streamedResponse);

      _extractAndSaveCookies(response);
      return _parseResponse(response);
    } catch (e) {
      return ApiResponse(
        statusCode: 0,
        isSuccess: false,
        error: 'Network upload error: $e',
      );
    }
  }

  ApiResponse _parseResponse(http.Response response) {
    try {
      final decoded = jsonDecode(response.body);
      final isSuccess = response.statusCode >= 200 && response.statusCode < 300;

      String? error;
      if (!isSuccess) {
        if (decoded is Map && decoded['detail'] != null) {
          error = decoded['detail'].toString();
        } else if (decoded is Map && decoded['error'] != null) {
          error = decoded['error'].toString();
        } else {
          error = 'HTTP Error ${response.statusCode}';
        }
      }

      return ApiResponse(
        statusCode: response.statusCode,
        isSuccess: isSuccess,
        data: decoded,
        error: error,
      );
    } catch (e) {
      return ApiResponse(
        statusCode: response.statusCode,
        isSuccess: response.statusCode >= 200 && response.statusCode < 300,
        data: response.body,
        error: response.statusCode >= 400 ? 'HTTP ${response.statusCode}: ${response.body}' : null,
      );
    }
  }
}
