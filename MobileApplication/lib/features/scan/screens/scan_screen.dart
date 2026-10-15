import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../../core/theme/app_theme.dart';
import '../scan_service.dart';
import '../models/scan_result.dart';

class ScanScreen extends StatefulWidget {
  final ScanService scanService;
  final Function(String faceletString)? onSendToSolver;

  const ScanScreen({
    super.key,
    required this.scanService,
    this.onSendToSolver,
  });

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  final ImagePicker _picker = ImagePicker();
  ScanResult? _scanResult;
  String? _errorMessage;

  Future<void> _pickImage(ImageSource source) async {
    setState(() => _errorMessage = null);
    try {
      final XFile? file = await _picker.pickImage(
        source: source,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 85,
      );
      if (file == null) return;

      final bytes = await file.readAsBytes();
      final result = await widget.scanService.scanImageBytes(bytes, filename: file.name);

      if (!mounted) return;
      if (result.success) {
        setState(() => _scanResult = result);
      } else {
        setState(() => _errorMessage = result.error);
      }
    } catch (e) {
      setState(() => _errorMessage = 'Failed to capture image: $e');
    }
  }

  Future<void> _loadPreset(String presetId) async {
    setState(() => _errorMessage = null);
    final result = await widget.scanService.scanPreset(presetId);
    if (!mounted) return;
    if (result.success) {
      setState(() => _scanResult = result);
    } else {
      setState(() => _errorMessage = result.error);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isProcessing = widget.scanService.isProcessing;

    return Scaffold(
      appBar: AppBar(
        title: const Text('OpenCV Computer Vision Scanner'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Header description
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppTheme.bgDark1,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppTheme.borderSubtle),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.camera_enhance, color: AppTheme.accentCyan, size: 28),
                    SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Real-Time Facelet Segmentation',
                            style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white, fontSize: 14),
                          ),
                          SizedBox(height: 2),
                          Text(
                            'Uses OpenCV CLAHE adaptive illumination and HSV color clustering on the FastAPI backend.',
                            style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Device Input Buttons (Camera & Gallery)
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      icon: const Icon(Icons.camera_alt, size: 20),
                      label: const Text('Take Photo'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.accentMain,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      onPressed: isProcessing ? null : () => _pickImage(ImageSource.camera),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.photo_library, size: 20),
                      label: const Text('Gallery Pick'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppTheme.accentCyan,
                        side: const BorderSide(color: AppTheme.accentCyan),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      onPressed: isProcessing ? null : () => _pickImage(ImageSource.gallery),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // Sample Presets Row (Matches Web App Parity)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'OR TEST WITH SAMPLE PRESETS (WEB PLATFORM SAMPLES):',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF94A3B8),
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 10),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _buildPresetChip('Sample U (Yellow)', 'sample_u', AppTheme.cubeYellow),
                          _buildPresetChip('Sample F (Green)', 'sample_f', AppTheme.cubeGreen),
                          _buildPresetChip('Sample R (Red)', 'sample_r', AppTheme.cubeRed),
                          _buildPresetChip('Solved Face', 'sample_solved', AppTheme.cubeWhite),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Loading Indicator
              if (isProcessing) ...[
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(24),
                    child: Column(
                      children: [
                        CircularProgressIndicator(color: AppTheme.accentCyan),
                        SizedBox(height: 12),
                        Text(
                          'OpenCV CLAHE & HSV Segmentation in progress...',
                          style: TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
                        ),
                      ],
                    ),
                  ),
                ),
              ],

              // Error banner
              if (_errorMessage != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.accentRose.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppTheme.accentRose.withOpacity(0.4)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline, color: AppTheme.accentRose, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(_errorMessage!, style: const TextStyle(color: AppTheme.accentRose, fontSize: 13)),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // OpenCV Results Section
              if (_scanResult != null && _scanResult!.success) ...[
                _buildResultView(_scanResult!),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPresetChip(String label, String presetId, Color dotColor) {
    return ActionChip(
      avatar: CircleAvatar(backgroundColor: dotColor, radius: 5),
      label: Text(label, style: const TextStyle(fontSize: 12, color: Colors.white)),
      backgroundColor: AppTheme.bgDark2,
      side: const BorderSide(color: AppTheme.borderSubtle),
      onPressed: () => _loadPreset(presetId),
    );
  }

  Widget _buildResultView(ScanResult res) {
    Uint8List? imageBytes;
    if (res.annotatedImage.startsWith('data:image/jpeg;base64,')) {
      final b64 = res.annotatedImage.replaceFirst('data:image/jpeg;base64,', '');
      try {
        imageBytes = base64Decode(b64);
      } catch (_) {}
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Row(
                  children: [
                    Icon(Icons.check_circle_outline, color: AppTheme.accentEmerald, size: 22),
                    SizedBox(width: 8),
                    Text(
                      'OpenCV Detection Output',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.getFaceletColor(res.centerColor).withOpacity(0.2),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: AppTheme.getFaceletColor(res.centerColor)),
                  ),
                  child: Text(
                    'Center: ${res.centerColor}',
                    style: TextStyle(
                      color: AppTheme.getFaceletColor(res.centerColor),
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Annotated Image View
            if (imageBytes != null) ...[
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Image.memory(
                  imageBytes,
                  height: 240,
                  fit: BoxFit.contain,
                ),
              ),
              const SizedBox(height: 16),
            ],

            // 3x3 Detected Face Grid Badges
            const Text(
              'DETECTED 3x3 FACELET GRID:',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF94A3B8)),
            ),
            const SizedBox(height: 8),
            Center(
              child: SizedBox(
                width: 180,
                height: 180,
                child: GridView.builder(
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 3,
                    crossAxisSpacing: 6,
                    mainAxisSpacing: 6,
                  ),
                  itemCount: 9,
                  itemBuilder: (_, i) {
                    final r = i ~/ 3;
                    final c = i % 3;
                    final code = (r < res.faceGrid.length && c < res.faceGrid[r].length)
                        ? res.faceGrid[r][c]
                        : '?';
                    return Container(
                      decoration: BoxDecoration(
                        color: AppTheme.getFaceletColor(code),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.black87, width: 1.5),
                      ),
                      child: Center(
                        child: Text(
                          code,
                          style: const TextStyle(
                            color: Colors.black87,
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Send to Solver Button
            ElevatedButton.icon(
              icon: const Icon(Icons.arrow_forward),
              label: const Text('Send Facelet Grid to 3D Solver'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.accentEmerald,
              ),
              onPressed: () {
                final flat = res.toFlatFaceletString();
                if (widget.onSendToSolver != null) {
                  widget.onSendToSolver!(flat);
                } else {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Detected Facelet Sequence: $flat'),
                      backgroundColor: AppTheme.accentEmerald,
                    ),
                  );
                }
              },
            ),
          ],
        ),
      ),
    );
  }
}
