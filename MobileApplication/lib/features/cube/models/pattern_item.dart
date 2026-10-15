class PatternItem {
  final String id;
  final String name;
  final String moves;
  final String description;

  PatternItem({
    required this.id,
    required this.name,
    required this.moves,
    required this.description,
  });

  factory PatternItem.fromJson(Map<String, dynamic> json) {
    return PatternItem(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      moves: json['moves']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
    );
  }
}
