class ScanResult {
  final bool success;
  final List<List<String>> faceGrid;
  final String annotatedImage;
  final String centerColor;
  final String? error;

  ScanResult({
    required this.success,
    required this.faceGrid,
    required this.annotatedImage,
    required this.centerColor,
    this.error,
  });

  factory ScanResult.fromJson(Map<String, dynamic> json) {
    final grid = <List<String>>[];
    if (json['face_grid'] is List) {
      for (final row in json['face_grid']) {
        if (row is List) {
          grid.add(row.map((cell) => cell.toString()).toList());
        }
      }
    }

    return ScanResult(
      success: json['success'] == true,
      faceGrid: grid,
      annotatedImage: json['annotated_image']?.toString() ?? '',
      centerColor: json['center_color']?.toString() ?? (grid.isNotEmpty ? grid[1][1] : 'U'),
      error: json['error']?.toString(),
    );
  }

  String toFlatFaceletString() {
    final sb = StringBuffer();
    for (final row in faceGrid) {
      for (final cell in row) {
        sb.write(cell);
      }
    }
    return sb.toString();
  }
}
