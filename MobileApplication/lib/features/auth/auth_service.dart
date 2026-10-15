import 'package:flutter/foundation.dart';
import 'package:drift/drift.dart';
import '../../core/network/api_client.dart';
import '../../core/constants/api_constants.dart';
import '../../core/database/app_database.dart';
import 'models/user_model.dart';

class AuthResult {
  final bool success;
  final UserModel? user;
  final String? errorMessage;

  AuthResult({required this.success, this.user, this.errorMessage});
}

class AuthService extends ChangeNotifier {
  final ApiClient _apiClient;
  final AppDatabase _db;
  UserModel? _currentUser;
  bool _isLoading = false;

  AuthService(this._apiClient, this._db);

  UserModel? get currentUser => _currentUser;
  bool get isAuthenticated => _currentUser != null;
  bool get isLoading => _isLoading;

  Future<AuthResult> login(String username, String password) async {
    _isLoading = true;
    notifyListeners();

    final response = await _apiClient.post(
      ApiConstants.login,
      body: {
        'username': username.trim(),
        'password': password.trim(),
      },
    );

    _isLoading = false;
    if (response.isSuccess && response.data is Map && response.data['user'] != null) {
      _currentUser = UserModel.fromJson(response.data['user']);
      await _cacheUserOffline(_currentUser!);
      notifyListeners();
      return AuthResult(success: true, user: _currentUser);
    } else {
      notifyListeners();
      return AuthResult(
        success: false,
        errorMessage: response.error ?? 'Login failed. Please check credentials.',
      );
    }
  }

  Future<AuthResult> register({
    required String username,
    required String email,
    required String password,
    required String confirmPassword,
    required String dateOfBirth,
  }) async {
    _isLoading = true;
    notifyListeners();

    final response = await _apiClient.post(
      ApiConstants.register,
      body: {
        'username': username.trim(),
        'email': email.trim(),
        'password': password.trim(),
        'confirm_password': confirmPassword.trim(),
        'date_of_birth': dateOfBirth.trim(),
      },
    );

    _isLoading = false;
    if (response.isSuccess && response.data is Map && response.data['user'] != null) {
      _currentUser = UserModel.fromJson(response.data['user']);
      await _cacheUserOffline(_currentUser!);
      notifyListeners();
      return AuthResult(success: true, user: _currentUser);
    } else {
      notifyListeners();
      return AuthResult(
        success: false,
        errorMessage: response.error ?? 'Registration failed. Verify inputs and 18+ age requirement.',
      );
    }
  }

  Future<AuthResult> loginWithFirebaseToken(String idToken) async {
    _isLoading = true;
    notifyListeners();

    final response = await _apiClient.post(
      ApiConstants.firebaseLogin,
      body: {'id_token': idToken},
    );

    _isLoading = false;
    if (response.isSuccess && response.data is Map && response.data['user'] != null) {
      _currentUser = UserModel.fromJson(response.data['user']);
      await _cacheUserOffline(_currentUser!);
      notifyListeners();
      return AuthResult(success: true, user: _currentUser);
    } else {
      notifyListeners();
      return AuthResult(
        success: false,
        errorMessage: response.error ?? 'Firebase authentication failed.',
      );
    }
  }

  Future<bool> restoreSession() async {
    if (!_apiClient.hasSession) {
      // Try restoring from offline database if first-use already completed
      final cached = await _db.getOfflineProfile();
      if (cached != null) {
        _currentUser = UserModel(
          id: cached.id,
          username: cached.username,
          email: cached.email,
          role: cached.role,
          bio: cached.bio,
          avatarColor: cached.avatarColor,
          wcaId: cached.wcaId,
          country: cached.country,
          mainCube: cached.mainCube,
          preferredMethod: cached.preferredMethod,
          pbSingle: cached.pbSingle,
          pbAo5: cached.pbAo5,
          createdAt: cached.lastSyncedAt,
        );
        notifyListeners();
        return true;
      }
      return false;
    }

    final response = await _apiClient.get(ApiConstants.me);
    if (response.isSuccess && response.data is Map && response.data['user'] != null) {
      _currentUser = UserModel.fromJson(response.data['user']);
      await _cacheUserOffline(_currentUser!);
      notifyListeners();
      return true;
    } else {
      // Network failed or session expired. Fallback to offline cached profile if available
      final cached = await _db.getOfflineProfile();
      if (cached != null) {
        _currentUser = UserModel(
          id: cached.id,
          username: cached.username,
          email: cached.email,
          role: cached.role,
          bio: cached.bio,
          avatarColor: cached.avatarColor,
          wcaId: cached.wcaId,
          country: cached.country,
          mainCube: cached.mainCube,
          preferredMethod: cached.preferredMethod,
          pbSingle: cached.pbSingle,
          pbAo5: cached.pbAo5,
          createdAt: cached.lastSyncedAt,
        );
        notifyListeners();
        return true;
      }
      return false;
    }
  }

  Future<void> logout() async {
    try {
      await _apiClient.post(ApiConstants.logout);
    } catch (_) {}
    await _apiClient.clearSession();
    _currentUser = null;
    notifyListeners();
  }

  Future<void> _cacheUserOffline(UserModel user) async {
    try {
      await _db.cacheProfile(
        CachedUserProfileCompanion.insert(
          id: const Value<int>(1),
          username: user.username,
          email: Value(user.email),
          role: Value(user.role),
          bio: Value(user.bio),
          avatarColor: Value(user.avatarColor),
          wcaId: Value(user.wcaId),
          country: Value(user.country),
          mainCube: Value(user.mainCube),
          preferredMethod: Value(user.preferredMethod),
          pbSingle: Value(user.pbSingle),
          pbAo5: Value(user.pbAo5),
          lastSyncedAt: DateTime.now().toIso8601String(),
        ),
      );
    } catch (_) {}
  }
}
