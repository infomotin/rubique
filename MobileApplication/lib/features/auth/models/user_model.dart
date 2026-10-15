class UserModel {
  final int id;
  final String username;
  final String email;
  final String role;
  final String bio;
  final String avatarColor;
  final String wcaId;
  final String country;
  final String mainCube;
  final String preferredMethod;
  final String pbSingle;
  final String pbAo5;
  final String createdAt;

  UserModel({
    required this.id,
    required this.username,
    required this.email,
    required this.role,
    required this.bio,
    required this.avatarColor,
    required this.wcaId,
    required this.country,
    required this.mainCube,
    required this.preferredMethod,
    required this.pbSingle,
    required this.pbAo5,
    required this.createdAt,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] is int ? json['id'] : int.tryParse(json['id'].toString()) ?? 0,
      username: json['username']?.toString() ?? '',
      email: json['email']?.toString() ?? '',
      role: json['role']?.toString() ?? 'user',
      bio: json['bio']?.toString() ?? '',
      avatarColor: json['avatar_color']?.toString() ?? '#818cf8',
      wcaId: json['wca_id']?.toString() ?? '',
      country: json['country']?.toString() ?? '',
      mainCube: json['main_cube']?.toString() ?? 'GAN 12 MagLev 3x3',
      preferredMethod: json['preferred_method']?.toString() ?? 'CFOP',
      pbSingle: json['pb_single']?.toString() ?? '',
      pbAo5: json['pb_ao5']?.toString() ?? '',
      createdAt: json['created_at']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'role': role,
      'bio': bio,
      'avatar_color': avatarColor,
      'wca_id': wcaId,
      'country': country,
      'main_cube': mainCube,
      'preferred_method': preferredMethod,
      'pb_single': pbSingle,
      'pb_ao5': pbAo5,
      'created_at': createdAt,
    };
  }
}
