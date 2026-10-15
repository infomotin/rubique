import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../auth_service.dart';

class RegisterScreen extends StatefulWidget {
  final AuthService authService;
  final VoidCallback onRegisterSuccess;

  const RegisterScreen({
    super.key,
    required this.authService,
    required this.onRegisterSuccess,
  });

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _usernameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _dobController = TextEditingController(text: '2000-01-01');

  bool _obscurePassword = true;
  String? _errorMessage;

  @override
  void dispose() {
    _usernameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _dobController.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final eighteenYearsAgo = DateTime(now.year - 18, now.month, now.day);

    final picked = await showDatePicker(
      context: context,
      initialDate: eighteenYearsAgo,
      firstDate: DateTime(1920),
      lastDate: now,
      builder: (context, child) {
        return Theme(
          data: ThemeData.dark().copyWith(
            colorScheme: const ColorScheme.dark(
              primary: AppTheme.accentMain,
              surface: AppTheme.bgDark1,
            ),
          ),
          child: child!,
        );
      },
    );

    if (picked != null) {
      final yyyy = picked.year.toString().padLeft(4, '0');
      final mm = picked.month.toString().padLeft(2, '0');
      final dd = picked.day.toString().padLeft(2, '0');
      setState(() {
        _dobController.text = '$yyyy-$mm-$dd';
      });
    }
  }

  Future<void> _handleRegister() async {
    setState(() => _errorMessage = null);

    if (_usernameController.text.trim().isEmpty) {
      setState(() => _errorMessage = 'Username is required.');
      return;
    }
    if (_passwordController.text.length < 6) {
      setState(() => _errorMessage = 'Password must be at least 6 characters long.');
      return;
    }
    if (_passwordController.text != _confirmPasswordController.text) {
      setState(() => _errorMessage = 'Passwords do not match.');
      return;
    }

    final res = await widget.authService.register(
      username: _usernameController.text,
      email: _emailController.text,
      password: _passwordController.text,
      confirmPassword: _confirmPasswordController.text,
      dateOfBirth: _dobController.text,
    );

    if (!mounted) return;

    if (res.success) {
      Navigator.pop(context);
      widget.onRegisterSuccess();
    } else {
      setState(() => _errorMessage = res.errorMessage);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = widget.authService.isLoading;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Create Cuber Account'),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const Text(
                        'Join CubePermutation AI',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        '18+ verified platform registration with MySQL backing & welcome coins.',
                        style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                      ),
                      const SizedBox(height: 18),

                      if (_errorMessage != null) ...[
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: AppTheme.accentRose.withOpacity(0.15),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: AppTheme.accentRose.withOpacity(0.4)),
                          ),
                          child: Text(
                            _errorMessage!,
                            style: const TextStyle(color: AppTheme.accentRose, fontSize: 13),
                          ),
                        ),
                        const SizedBox(height: 14),
                      ],

                      // Username
                      TextField(
                        controller: _usernameController,
                        decoration: const InputDecoration(labelText: 'Username (alphanumeric)'),
                      ),
                      const SizedBox(height: 12),

                      // Email
                      TextField(
                        controller: _emailController,
                        decoration: const InputDecoration(labelText: 'Email Address (optional)'),
                      ),
                      const SizedBox(height: 12),

                      // Date of Birth (Age Gate 18+)
                      TextField(
                        controller: _dobController,
                        readOnly: true,
                        onTap: _pickDate,
                        decoration: InputDecoration(
                          labelText: 'Date of Birth (YYYY-MM-DD)',
                          suffixIcon: IconButton(
                            icon: const Icon(Icons.calendar_today, size: 20),
                            onPressed: _pickDate,
                          ),
                          helperText: 'Must be at least 18 years old to join',
                          helperStyle: const TextStyle(color: AppTheme.accentAmber, fontSize: 11),
                        ),
                      ),
                      const SizedBox(height: 12),

                      // Password
                      TextField(
                        controller: _passwordController,
                        obscureText: _obscurePassword,
                        decoration: const InputDecoration(labelText: 'Password (min 6 characters)'),
                      ),
                      const SizedBox(height: 12),

                      // Confirm Password
                      TextField(
                        controller: _confirmPasswordController,
                        obscureText: _obscurePassword,
                        decoration: const InputDecoration(labelText: 'Confirm Password'),
                      ),
                      const SizedBox(height: 20),

                      ElevatedButton(
                        onPressed: isLoading ? null : _handleRegister,
                        child: isLoading
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                              )
                            : const Text('Complete 18+ Registration'),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
