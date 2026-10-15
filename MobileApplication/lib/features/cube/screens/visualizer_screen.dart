import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../cube_service.dart';
import '../models/solve_result.dart';
import '../models/pattern_item.dart';

class VisualizerScreen extends StatefulWidget {
  final CubeService cubeService;
  final String? initialFacelets;

  const VisualizerScreen({
    super.key,
    required this.cubeService,
    this.initialFacelets,
  });

  @override
  State<VisualizerScreen> createState() => _VisualizerScreenState();
}

class _VisualizerScreenState extends State<VisualizerScreen> {
  // 6 faces: U(0), L(1), F(2), R(3), B(4), D(5)
  // Each face has 9 stickers (3x3)
  late List<String> _facelets;
  String _activeScramble = '';
  SolveResult? _solveResult;
  int _currentStepIndex = 0;
  String _selectedColor = 'Y';
  int _activeFaceIndex = 0; // 0=U, 1=L, 2=F, 3=R, 4=B, 5=D

  static const List<String> _faceNames = ['Up (Top)', 'Left', 'Front', 'Right', 'Back', 'Down (Bottom)'];
  static const List<String> _faceCenterColors = ['Y', 'O', 'G', 'R', 'B', 'W'];

  @override
  void initState() {
    super.initState();
    _resetToSolved();
    if (widget.initialFacelets != null && widget.initialFacelets!.length == 54) {
      _facelets = widget.initialFacelets!.split('');
    }
  }

  void _resetToSolved() {
    // Solved standard facelet state: 9 Y, 9 R, 9 G, 9 W, 9 O, 9 B
    // U=Yellow, L=Orange, F=Green, R=Red, B=Blue, D=White
    final list = <String>[];
    for (int i = 0; i < 9; i++) list.add('Y'); // U
    for (int i = 0; i < 9; i++) list.add('O'); // L
    for (int i = 0; i < 9; i++) list.add('G'); // F
    for (int i = 0; i < 9; i++) list.add('R'); // R
    for (int i = 0; i < 9; i++) list.add('B'); // B
    for (int i = 0; i < 9; i++) list.add('W'); // D
    setState(() {
      _facelets = list;
      _activeScramble = '';
      _solveResult = null;
      _currentStepIndex = 0;
    });
  }

  Future<void> _handleScramble() async {
    final res = await widget.cubeService.generateScramble();
    if (!mounted || res == null) return;

    setState(() {
      _activeScramble = res.scramble;
      _solveResult = null;
      _currentStepIndex = 0;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('WCA Scramble: ${res.scramble}'),
        backgroundColor: AppTheme.bgDark2,
        duration: const Duration(seconds: 3),
      ),
    );
  }

  Future<void> _handleSolve() async {
    SolveResult result;
    if (_activeScramble.isNotEmpty) {
      // Solve via scramble moves
      result = await widget.cubeService.solveCube(customMoves: _activeScramble);
    } else {
      // Build 54 character facelet string
      final faceletStr = _facelets.join('');
      result = await widget.cubeService.solveCube(faceletString: faceletStr);
    }

    if (!mounted) return;

    setState(() {
      _solveResult = result;
      _currentStepIndex = 0;
    });

    if (result.success) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Solved in ${result.moveCount} optimal moves!'),
          backgroundColor: AppTheme.accentEmerald,
        ),
      );
    } else if (result.error != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Solver Error: ${result.error}'),
          backgroundColor: AppTheme.accentRose,
        ),
      );
    }
  }

  void _showPatternStudio() async {
    final patterns = await widget.cubeService.getPatterns();
    if (!mounted) return;

    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.bgDark1,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    '🎨 Pattern Studio Library',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Color(0xFF94A3B8)),
                    onPressed: () => Navigator.pop(ctx),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              const Text(
                'Select a verified artistic permutation to apply and explore.',
                style: TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
              ),
              const SizedBox(height: 12),
              Expanded(
                child: ListView.separated(
                  itemCount: patterns.length,
                  separatorBuilder: (_, __) => const Divider(color: AppTheme.borderSubtle),
                  itemBuilder: (_, idx) {
                    final p = patterns[idx];
                    return ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text(p.name, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
                      subtitle: Text(p.moves, style: const TextStyle(fontFamily: 'monospace', color: AppTheme.accentCyan, fontSize: 12)),
                      trailing: ElevatedButton(
                        style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8)),
                        onPressed: () {
                          Navigator.pop(ctx);
                          setState(() {
                            _activeScramble = p.moves;
                          });
                          _handleSolve();
                        },
                        child: const Text('Apply'),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = widget.cubeService.isLoading;
    final currentFaceOffset = _activeFaceIndex * 9;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Cube Permutation Laboratory'),
        actions: [
          IconButton(
            icon: const Icon(Icons.auto_awesome, color: AppTheme.accentAmber),
            tooltip: 'Pattern Studio',
            onPressed: _showPatternStudio,
          ),
          IconButton(
            icon: const Icon(Icons.refresh, color: Color(0xFF94A3B8)),
            tooltip: 'Reset Cube',
            onPressed: _resetToSolved,
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Active Scramble Banner
              if (_activeScramble.isNotEmpty) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.bgDark1,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppTheme.borderGlowCyan),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'ACTIVE SEQUENCE / SCRAMBLE:',
                        style: TextStyle(fontSize: 10, color: AppTheme.accentCyan, fontWeight: FontWeight.bold, letterSpacing: 0.8),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _activeScramble,
                        style: const TextStyle(
                          fontFamily: 'monospace',
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),
              ],

              // Face Selector Tabs
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: List.generate(6, (index) {
                    final isSelected = _activeFaceIndex == index;
                    final centerColor = _faceCenterColors[index];
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              width: 12,
                              height: 12,
                              decoration: BoxDecoration(
                                color: AppTheme.getFaceletColor(centerColor),
                                borderRadius: BorderRadius.circular(3),
                                border: Border.all(color: Colors.black45),
                              ),
                            ),
                            const SizedBox(width: 6),
                            Text(_faceNames[index]),
                          ],
                        ),
                        selected: isSelected,
                        selectedColor: AppTheme.accentMain.withOpacity(0.3),
                        side: BorderSide(color: isSelected ? AppTheme.accentMain : AppTheme.borderSubtle),
                        onSelected: (selected) {
                          if (selected) setState(() => _activeFaceIndex = index);
                        },
                      ),
                    );
                  }),
                ),
              ),
              const SizedBox(height: 16),

              // 3x3 Interactive Facelet Grid Card
              Center(
                child: Container(
                  width: 280,
                  height: 280,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.bgDark0,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: AppTheme.borderGlow, width: 2),
                    boxShadow: [
                      BoxShadow(
                        color: AppTheme.accentMain.withOpacity(0.15),
                        blurRadius: 20,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                  child: GridView.builder(
                    physics: const NeverScrollableScrollPhysics(),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 3,
                      crossAxisSpacing: 8,
                      mainAxisSpacing: 8,
                    ),
                    itemCount: 9,
                    itemBuilder: (context, idx) {
                      final stickerIndex = currentFaceOffset + idx;
                      final colorCode = _facelets[stickerIndex];
                      final isCenter = idx == 4;

                      return GestureDetector(
                        onTap: () {
                          if (!isCenter) {
                            setState(() {
                              _facelets[stickerIndex] = _selectedColor;
                            });
                          }
                        },
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 180),
                          decoration: BoxDecoration(
                            color: AppTheme.getFaceletColor(colorCode),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: Colors.black87, width: 2),
                            boxShadow: const [
                              BoxShadow(color: Colors.black45, blurRadius: 4, offset: Offset(0, 2)),
                            ],
                          ),
                          child: Center(
                            child: isCenter
                                ? Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: Colors.black54,
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                    child: Text(
                                      colorCode,
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 14,
                                      ),
                                    ),
                                  )
                                : Text(
                                    colorCode,
                                    style: const TextStyle(
                                      color: Colors.black87,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 16,
                                    ),
                                  ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ),
              const SizedBox(height: 14),

              // Color Palette Picker (For manual facelet editing)
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: ['Y', 'W', 'G', 'B', 'O', 'R'].map((col) {
                  final isChosen = _selectedColor == col;
                  return GestureDetector(
                    onTap: () => setState(() => _selectedColor = col),
                    child: Container(
                      margin: const EdgeInsets.symmetric(horizontal: 6),
                      width: 34,
                      height: 34,
                      decoration: BoxDecoration(
                        color: AppTheme.getFaceletColor(col),
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: isChosen ? AppTheme.accentCyan : Colors.transparent,
                          width: isChosen ? 3 : 1,
                        ),
                        boxShadow: isChosen
                            ? [
                                BoxShadow(
                                  color: AppTheme.accentCyan.withOpacity(0.5),
                                  blurRadius: 8,
                                )
                              ]
                            : null,
                      ),
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 18),

              // Action Buttons Row
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.shuffle, size: 18),
                      label: const Text('Scramble'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppTheme.accentCyan,
                        side: const BorderSide(color: AppTheme.accentCyan),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      onPressed: isLoading ? null : _handleScramble,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton.icon(
                      icon: const Icon(Icons.play_arrow, size: 20),
                      label: isLoading
                          ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Text('Solve Cube'),
                      onPressed: isLoading ? null : _handleSolve,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Solution Playback Deck (Step-by-Step Navigation)
              if (_solveResult != null && _solveResult!.success) ...[
                _buildPlaybackDeck(),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPlaybackDeck() {
    final result = _solveResult!;
    final steps = result.steps;
    final hasSteps = steps.isNotEmpty;
    final currentStep = hasSteps && _currentStepIndex < steps.length ? steps[_currentStepIndex] : null;

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
                    Icon(Icons.psychology, color: AppTheme.accentCyan, size: 22),
                    SizedBox(width: 8),
                    Text(
                      'AI Solution Deck',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.accentEmerald.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppTheme.accentEmerald.withOpacity(0.4)),
                  ),
                  child: Text(
                    '${result.moveCount} Moves (${result.engine})',
                    style: const TextStyle(color: AppTheme.accentEmerald, fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Solution Ribbon
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppTheme.bgDark0,
                borderRadius: BorderRadius.circular(10),
              ),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: List.generate(result.moves.length, (idx) {
                    final move = result.moves[idx];
                    final isCurrent = idx == _currentStepIndex;
                    return Container(
                      margin: const EdgeInsets.only(right: 6),
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: isCurrent ? AppTheme.accentMain : AppTheme.bgDark2,
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(
                          color: isCurrent ? Colors.white : AppTheme.borderSubtle,
                        ),
                      ),
                      child: Text(
                        move,
                        style: TextStyle(
                          color: isCurrent ? Colors.white : const Color(0xFFCBD5E1),
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                      ),
                    );
                  }),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Step Explanation Box
            if (currentStep != null) ...[
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppTheme.bgDark2,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.borderSubtle),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          width: 36,
                          height: 36,
                          decoration: BoxDecoration(
                            color: AppTheme.accentMain,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Center(
                            child: Text(
                              currentStep.move,
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 16,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Step ${_currentStepIndex + 1} of ${result.moves.length}',
                              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
                            ),
                            const Text('Group Subgroup Transition', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 11)),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // Why
                    const Text('WHY THIS MOVE:', style: TextStyle(color: AppTheme.accentCyan, fontSize: 11, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 3),
                    Text(
                      currentStep.why,
                      style: const TextStyle(color: Color(0xFFCBD5E1), fontSize: 12, height: 1.4),
                    ),
                    const SizedBox(height: 10),

                    // How
                    const Text('HOW TO EXECUTE:', style: TextStyle(color: AppTheme.accentAmber, fontSize: 11, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 3),
                    Text(
                      currentStep.how,
                      style: const TextStyle(color: Color(0xFFCBD5E1), fontSize: 12, height: 1.4),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),

              // Stepper Controls
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  OutlinedButton.icon(
                    icon: const Icon(Icons.arrow_back, size: 16),
                    label: const Text('Previous'),
                    onPressed: _currentStepIndex > 0
                        ? () => setState(() => _currentStepIndex--)
                        : null,
                  ),
                  Text(
                    '${_currentStepIndex + 1} / ${result.moves.length}',
                    style: const TextStyle(color: Color(0xFF94A3B8), fontWeight: FontWeight.bold),
                  ),
                  ElevatedButton.icon(
                    icon: const Icon(Icons.arrow_forward, size: 16),
                    label: const Text('Next Move'),
                    onPressed: _currentStepIndex < result.moves.length - 1
                        ? () => setState(() => _currentStepIndex++)
                        : null,
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
