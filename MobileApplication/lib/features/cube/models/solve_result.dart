class MoveStep {
  final int step;
  final String move;
  final String why;
  final String how;

  MoveStep({
    required this.step,
    required this.move,
    required this.why,
    required this.how,
  });

  factory MoveStep.fromJson(Map<String, dynamic> json) {
    return MoveStep(
      step: json['step'] is int ? json['step'] : int.tryParse(json['step'].toString()) ?? 1,
      move: json['move']?.toString() ?? '',
      why: json['why']?.toString() ?? '',
      how: json['how']?.toString() ?? '',
    );
  }
}

class SolveResult {
  final bool success;
  final String solution;
  final List<String> moves;
  final List<MoveStep> steps;
  final int moveCount;
  final String engine;
  final String method;
  final String? error;

  SolveResult({
    required this.success,
    required this.solution,
    required this.moves,
    required this.steps,
    required this.moveCount,
    required this.engine,
    required this.method,
    this.error,
  });

  factory SolveResult.fromJson(Map<String, dynamic> json) {
    final movesList = <String>[];
    if (json['moves'] is List) {
      for (final m in json['moves']) {
        movesList.add(m.toString());
      }
    }

    final stepsList = <MoveStep>[];
    if (json['steps'] is List) {
      for (final s in json['steps']) {
        if (s is Map<String, dynamic>) {
          stepsList.add(MoveStep.fromJson(s));
        } else if (s is Map) {
          stepsList.add(MoveStep.fromJson(Map<String, dynamic>.from(s)));
        }
      }
    }

    return SolveResult(
      success: json['success'] == true,
      solution: json['solution']?.toString() ?? '',
      moves: movesList,
      steps: stepsList,
      moveCount: json['move_count'] is int ? json['move_count'] : int.tryParse(json['move_count']?.toString() ?? '0') ?? movesList.length,
      engine: json['engine']?.toString() ?? 'Two-Phase',
      method: json['method']?.toString() ?? 'Kociemba Minimal Step Solver',
      error: json['error']?.toString(),
    );
  }
}
