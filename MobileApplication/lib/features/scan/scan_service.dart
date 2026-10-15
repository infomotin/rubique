import 'dart:convert';
import 'package:flutter/foundation.dart';
import '../../core/network/api_client.dart';
import '../../core/constants/api_constants.dart';
import '../../core/database/app_database.dart';
import 'models/scan_result.dart';

class ScanService extends ChangeNotifier {
  final ApiClient _apiClient;
  final AppDatabase _db;
  bool _isProcessing = false;

  ScanService(this._apiClient, this._db);

  bool get isProcessing => _isProcessing;

  Future<ScanResult> scanImageBytes(Uint8List imageBytes, {String filename = 'cube_scan.jpg'}) async {
    _isProcessing = true;
    notifyListeners();

    final response = await _apiClient.postMultipart(
      ApiConstants.scanImage,
      fileBytes: imageBytes,
      filename: filename,
    );

    _isProcessing = false;
    notifyListeners();

    if (response.isSuccess && response.data is Map) {
      final res = ScanResult.fromJson(Map<String, dynamic>.from(response.data));
      await _cacheScanOffline(res);
      return res;
    } else {
      return ScanResult(
        success: false,
        faceGrid: [],
        annotatedImage: '',
        centerColor: '',
        error: response.error ?? 'OpenCV vision processing failed.',
      );
    }
  }

  Future<ScanResult> scanPreset(String sampleId) async {
    _isProcessing = true;
    notifyListeners();

    final response = await _apiClient.post(
      ApiConstants.scanJson,
      body: {'sample_id': sampleId},
    );

    _isProcessing = false;
    notifyListeners();

    if (response.isSuccess && response.data is Map) {
      final res = ScanResult.fromJson(Map<String, dynamic>.from(response.data));
      await _cacheScanOffline(res);
      return res;
    } else {
      return ScanResult(
        success: false,
        faceGrid: [],
        annotatedImage: '',
        centerColor: '',
        error: response.error ?? 'Failed to load OpenCV sample preset.',
      );
    }
  }

  Future<void> _cacheScanOffline(ScanResult res) async {
    if (!res.success) return;
    try {
      await _db.cacheScanResult(
        CachedScanResultsCompanion.insert(
          centerColor: res.centerColor,
          faceGridJson: jsonEncode(res.faceGrid),
          annotatedImageBase64: res.annotatedImage,
          scannedAt: DateTime.now().toIso8601String(),
        ),
      );
    } catch (_) {}
  }
}
