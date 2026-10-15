// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_database.dart';

// ignore_for_file: type=lint
class $CachedSolvesTable extends CachedSolves
    with TableInfo<$CachedSolvesTable, CachedSolve> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedSolvesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _remoteIdMeta = const VerificationMeta(
    'remoteId',
  );
  @override
  late final GeneratedColumn<int> remoteId = GeneratedColumn<int>(
    'remote_id',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _scrambleMeta = const VerificationMeta(
    'scramble',
  );
  @override
  late final GeneratedColumn<String> scramble = GeneratedColumn<String>(
    'scramble',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _solutionMeta = const VerificationMeta(
    'solution',
  );
  @override
  late final GeneratedColumn<String> solution = GeneratedColumn<String>(
    'solution',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _moveCountMeta = const VerificationMeta(
    'moveCount',
  );
  @override
  late final GeneratedColumn<int> moveCount = GeneratedColumn<int>(
    'move_count',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<String> createdAt = GeneratedColumn<String>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    remoteId,
    scramble,
    solution,
    moveCount,
    createdAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_solves';
  @override
  VerificationContext validateIntegrity(
    Insertable<CachedSolve> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('remote_id')) {
      context.handle(
        _remoteIdMeta,
        remoteId.isAcceptableOrUnknown(data['remote_id']!, _remoteIdMeta),
      );
    }
    if (data.containsKey('scramble')) {
      context.handle(
        _scrambleMeta,
        scramble.isAcceptableOrUnknown(data['scramble']!, _scrambleMeta),
      );
    } else if (isInserting) {
      context.missing(_scrambleMeta);
    }
    if (data.containsKey('solution')) {
      context.handle(
        _solutionMeta,
        solution.isAcceptableOrUnknown(data['solution']!, _solutionMeta),
      );
    } else if (isInserting) {
      context.missing(_solutionMeta);
    }
    if (data.containsKey('move_count')) {
      context.handle(
        _moveCountMeta,
        moveCount.isAcceptableOrUnknown(data['move_count']!, _moveCountMeta),
      );
    } else if (isInserting) {
      context.missing(_moveCountMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CachedSolve map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedSolve(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      remoteId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}remote_id'],
      ),
      scramble: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}scramble'],
      )!,
      solution: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}solution'],
      )!,
      moveCount: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}move_count'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}created_at'],
      )!,
    );
  }

  @override
  $CachedSolvesTable createAlias(String alias) {
    return $CachedSolvesTable(attachedDatabase, alias);
  }
}

class CachedSolve extends DataClass implements Insertable<CachedSolve> {
  final int id;
  final int? remoteId;
  final String scramble;
  final String solution;
  final int moveCount;
  final String createdAt;
  const CachedSolve({
    required this.id,
    this.remoteId,
    required this.scramble,
    required this.solution,
    required this.moveCount,
    required this.createdAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    if (!nullToAbsent || remoteId != null) {
      map['remote_id'] = Variable<int>(remoteId);
    }
    map['scramble'] = Variable<String>(scramble);
    map['solution'] = Variable<String>(solution);
    map['move_count'] = Variable<int>(moveCount);
    map['created_at'] = Variable<String>(createdAt);
    return map;
  }

  CachedSolvesCompanion toCompanion(bool nullToAbsent) {
    return CachedSolvesCompanion(
      id: Value(id),
      remoteId: remoteId == null && nullToAbsent
          ? const Value.absent()
          : Value(remoteId),
      scramble: Value(scramble),
      solution: Value(solution),
      moveCount: Value(moveCount),
      createdAt: Value(createdAt),
    );
  }

  factory CachedSolve.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedSolve(
      id: serializer.fromJson<int>(json['id']),
      remoteId: serializer.fromJson<int?>(json['remoteId']),
      scramble: serializer.fromJson<String>(json['scramble']),
      solution: serializer.fromJson<String>(json['solution']),
      moveCount: serializer.fromJson<int>(json['moveCount']),
      createdAt: serializer.fromJson<String>(json['createdAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'remoteId': serializer.toJson<int?>(remoteId),
      'scramble': serializer.toJson<String>(scramble),
      'solution': serializer.toJson<String>(solution),
      'moveCount': serializer.toJson<int>(moveCount),
      'createdAt': serializer.toJson<String>(createdAt),
    };
  }

  CachedSolve copyWith({
    int? id,
    Value<int?> remoteId = const Value.absent(),
    String? scramble,
    String? solution,
    int? moveCount,
    String? createdAt,
  }) => CachedSolve(
    id: id ?? this.id,
    remoteId: remoteId.present ? remoteId.value : this.remoteId,
    scramble: scramble ?? this.scramble,
    solution: solution ?? this.solution,
    moveCount: moveCount ?? this.moveCount,
    createdAt: createdAt ?? this.createdAt,
  );
  CachedSolve copyWithCompanion(CachedSolvesCompanion data) {
    return CachedSolve(
      id: data.id.present ? data.id.value : this.id,
      remoteId: data.remoteId.present ? data.remoteId.value : this.remoteId,
      scramble: data.scramble.present ? data.scramble.value : this.scramble,
      solution: data.solution.present ? data.solution.value : this.solution,
      moveCount: data.moveCount.present ? data.moveCount.value : this.moveCount,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedSolve(')
          ..write('id: $id, ')
          ..write('remoteId: $remoteId, ')
          ..write('scramble: $scramble, ')
          ..write('solution: $solution, ')
          ..write('moveCount: $moveCount, ')
          ..write('createdAt: $createdAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(id, remoteId, scramble, solution, moveCount, createdAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedSolve &&
          other.id == this.id &&
          other.remoteId == this.remoteId &&
          other.scramble == this.scramble &&
          other.solution == this.solution &&
          other.moveCount == this.moveCount &&
          other.createdAt == this.createdAt);
}

class CachedSolvesCompanion extends UpdateCompanion<CachedSolve> {
  final Value<int> id;
  final Value<int?> remoteId;
  final Value<String> scramble;
  final Value<String> solution;
  final Value<int> moveCount;
  final Value<String> createdAt;
  const CachedSolvesCompanion({
    this.id = const Value.absent(),
    this.remoteId = const Value.absent(),
    this.scramble = const Value.absent(),
    this.solution = const Value.absent(),
    this.moveCount = const Value.absent(),
    this.createdAt = const Value.absent(),
  });
  CachedSolvesCompanion.insert({
    this.id = const Value.absent(),
    this.remoteId = const Value.absent(),
    required String scramble,
    required String solution,
    required int moveCount,
    required String createdAt,
  }) : scramble = Value(scramble),
       solution = Value(solution),
       moveCount = Value(moveCount),
       createdAt = Value(createdAt);
  static Insertable<CachedSolve> custom({
    Expression<int>? id,
    Expression<int>? remoteId,
    Expression<String>? scramble,
    Expression<String>? solution,
    Expression<int>? moveCount,
    Expression<String>? createdAt,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (remoteId != null) 'remote_id': remoteId,
      if (scramble != null) 'scramble': scramble,
      if (solution != null) 'solution': solution,
      if (moveCount != null) 'move_count': moveCount,
      if (createdAt != null) 'created_at': createdAt,
    });
  }

  CachedSolvesCompanion copyWith({
    Value<int>? id,
    Value<int?>? remoteId,
    Value<String>? scramble,
    Value<String>? solution,
    Value<int>? moveCount,
    Value<String>? createdAt,
  }) {
    return CachedSolvesCompanion(
      id: id ?? this.id,
      remoteId: remoteId ?? this.remoteId,
      scramble: scramble ?? this.scramble,
      solution: solution ?? this.solution,
      moveCount: moveCount ?? this.moveCount,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (remoteId.present) {
      map['remote_id'] = Variable<int>(remoteId.value);
    }
    if (scramble.present) {
      map['scramble'] = Variable<String>(scramble.value);
    }
    if (solution.present) {
      map['solution'] = Variable<String>(solution.value);
    }
    if (moveCount.present) {
      map['move_count'] = Variable<int>(moveCount.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<String>(createdAt.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedSolvesCompanion(')
          ..write('id: $id, ')
          ..write('remoteId: $remoteId, ')
          ..write('scramble: $scramble, ')
          ..write('solution: $solution, ')
          ..write('moveCount: $moveCount, ')
          ..write('createdAt: $createdAt')
          ..write(')'))
        .toString();
  }
}

class $CachedUserProfileTable extends CachedUserProfile
    with TableInfo<$CachedUserProfileTable, CachedUserProfileData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedUserProfileTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _usernameMeta = const VerificationMeta(
    'username',
  );
  @override
  late final GeneratedColumn<String> username = GeneratedColumn<String>(
    'username',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _emailMeta = const VerificationMeta('email');
  @override
  late final GeneratedColumn<String> email = GeneratedColumn<String>(
    'email',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant(''),
  );
  static const VerificationMeta _roleMeta = const VerificationMeta('role');
  @override
  late final GeneratedColumn<String> role = GeneratedColumn<String>(
    'role',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('user'),
  );
  static const VerificationMeta _bioMeta = const VerificationMeta('bio');
  @override
  late final GeneratedColumn<String> bio = GeneratedColumn<String>(
    'bio',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant(''),
  );
  static const VerificationMeta _avatarColorMeta = const VerificationMeta(
    'avatarColor',
  );
  @override
  late final GeneratedColumn<String> avatarColor = GeneratedColumn<String>(
    'avatar_color',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('#818cf8'),
  );
  static const VerificationMeta _wcaIdMeta = const VerificationMeta('wcaId');
  @override
  late final GeneratedColumn<String> wcaId = GeneratedColumn<String>(
    'wca_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant(''),
  );
  static const VerificationMeta _countryMeta = const VerificationMeta(
    'country',
  );
  @override
  late final GeneratedColumn<String> country = GeneratedColumn<String>(
    'country',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant(''),
  );
  static const VerificationMeta _mainCubeMeta = const VerificationMeta(
    'mainCube',
  );
  @override
  late final GeneratedColumn<String> mainCube = GeneratedColumn<String>(
    'main_cube',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('GAN 12 MagLev 3x3'),
  );
  static const VerificationMeta _preferredMethodMeta = const VerificationMeta(
    'preferredMethod',
  );
  @override
  late final GeneratedColumn<String> preferredMethod = GeneratedColumn<String>(
    'preferred_method',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('CFOP'),
  );
  static const VerificationMeta _pbSingleMeta = const VerificationMeta(
    'pbSingle',
  );
  @override
  late final GeneratedColumn<String> pbSingle = GeneratedColumn<String>(
    'pb_single',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant(''),
  );
  static const VerificationMeta _pbAo5Meta = const VerificationMeta('pbAo5');
  @override
  late final GeneratedColumn<String> pbAo5 = GeneratedColumn<String>(
    'pb_ao5',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant(''),
  );
  static const VerificationMeta _totalSolvesMeta = const VerificationMeta(
    'totalSolves',
  );
  @override
  late final GeneratedColumn<int> totalSolves = GeneratedColumn<int>(
    'total_solves',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(0),
  );
  static const VerificationMeta _minMovesMeta = const VerificationMeta(
    'minMoves',
  );
  @override
  late final GeneratedColumn<int> minMoves = GeneratedColumn<int>(
    'min_moves',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(0),
  );
  static const VerificationMeta _avgMovesMeta = const VerificationMeta(
    'avgMoves',
  );
  @override
  late final GeneratedColumn<double> avgMoves = GeneratedColumn<double>(
    'avg_moves',
    aliasedName,
    false,
    type: DriftSqlType.double,
    requiredDuringInsert: false,
    defaultValue: const Constant(0.0),
  );
  static const VerificationMeta _coinsBalanceMeta = const VerificationMeta(
    'coinsBalance',
  );
  @override
  late final GeneratedColumn<int> coinsBalance = GeneratedColumn<int>(
    'coins_balance',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(1000),
  );
  static const VerificationMeta _lastSyncedAtMeta = const VerificationMeta(
    'lastSyncedAt',
  );
  @override
  late final GeneratedColumn<String> lastSyncedAt = GeneratedColumn<String>(
    'last_synced_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    username,
    email,
    role,
    bio,
    avatarColor,
    wcaId,
    country,
    mainCube,
    preferredMethod,
    pbSingle,
    pbAo5,
    totalSolves,
    minMoves,
    avgMoves,
    coinsBalance,
    lastSyncedAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_user_profile';
  @override
  VerificationContext validateIntegrity(
    Insertable<CachedUserProfileData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('username')) {
      context.handle(
        _usernameMeta,
        username.isAcceptableOrUnknown(data['username']!, _usernameMeta),
      );
    } else if (isInserting) {
      context.missing(_usernameMeta);
    }
    if (data.containsKey('email')) {
      context.handle(
        _emailMeta,
        email.isAcceptableOrUnknown(data['email']!, _emailMeta),
      );
    }
    if (data.containsKey('role')) {
      context.handle(
        _roleMeta,
        role.isAcceptableOrUnknown(data['role']!, _roleMeta),
      );
    }
    if (data.containsKey('bio')) {
      context.handle(
        _bioMeta,
        bio.isAcceptableOrUnknown(data['bio']!, _bioMeta),
      );
    }
    if (data.containsKey('avatar_color')) {
      context.handle(
        _avatarColorMeta,
        avatarColor.isAcceptableOrUnknown(
          data['avatar_color']!,
          _avatarColorMeta,
        ),
      );
    }
    if (data.containsKey('wca_id')) {
      context.handle(
        _wcaIdMeta,
        wcaId.isAcceptableOrUnknown(data['wca_id']!, _wcaIdMeta),
      );
    }
    if (data.containsKey('country')) {
      context.handle(
        _countryMeta,
        country.isAcceptableOrUnknown(data['country']!, _countryMeta),
      );
    }
    if (data.containsKey('main_cube')) {
      context.handle(
        _mainCubeMeta,
        mainCube.isAcceptableOrUnknown(data['main_cube']!, _mainCubeMeta),
      );
    }
    if (data.containsKey('preferred_method')) {
      context.handle(
        _preferredMethodMeta,
        preferredMethod.isAcceptableOrUnknown(
          data['preferred_method']!,
          _preferredMethodMeta,
        ),
      );
    }
    if (data.containsKey('pb_single')) {
      context.handle(
        _pbSingleMeta,
        pbSingle.isAcceptableOrUnknown(data['pb_single']!, _pbSingleMeta),
      );
    }
    if (data.containsKey('pb_ao5')) {
      context.handle(
        _pbAo5Meta,
        pbAo5.isAcceptableOrUnknown(data['pb_ao5']!, _pbAo5Meta),
      );
    }
    if (data.containsKey('total_solves')) {
      context.handle(
        _totalSolvesMeta,
        totalSolves.isAcceptableOrUnknown(
          data['total_solves']!,
          _totalSolvesMeta,
        ),
      );
    }
    if (data.containsKey('min_moves')) {
      context.handle(
        _minMovesMeta,
        minMoves.isAcceptableOrUnknown(data['min_moves']!, _minMovesMeta),
      );
    }
    if (data.containsKey('avg_moves')) {
      context.handle(
        _avgMovesMeta,
        avgMoves.isAcceptableOrUnknown(data['avg_moves']!, _avgMovesMeta),
      );
    }
    if (data.containsKey('coins_balance')) {
      context.handle(
        _coinsBalanceMeta,
        coinsBalance.isAcceptableOrUnknown(
          data['coins_balance']!,
          _coinsBalanceMeta,
        ),
      );
    }
    if (data.containsKey('last_synced_at')) {
      context.handle(
        _lastSyncedAtMeta,
        lastSyncedAt.isAcceptableOrUnknown(
          data['last_synced_at']!,
          _lastSyncedAtMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_lastSyncedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CachedUserProfileData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedUserProfileData(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      username: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}username'],
      )!,
      email: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}email'],
      )!,
      role: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}role'],
      )!,
      bio: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}bio'],
      )!,
      avatarColor: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}avatar_color'],
      )!,
      wcaId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}wca_id'],
      )!,
      country: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}country'],
      )!,
      mainCube: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}main_cube'],
      )!,
      preferredMethod: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}preferred_method'],
      )!,
      pbSingle: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}pb_single'],
      )!,
      pbAo5: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}pb_ao5'],
      )!,
      totalSolves: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}total_solves'],
      )!,
      minMoves: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}min_moves'],
      )!,
      avgMoves: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}avg_moves'],
      )!,
      coinsBalance: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}coins_balance'],
      )!,
      lastSyncedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}last_synced_at'],
      )!,
    );
  }

  @override
  $CachedUserProfileTable createAlias(String alias) {
    return $CachedUserProfileTable(attachedDatabase, alias);
  }
}

class CachedUserProfileData extends DataClass
    implements Insertable<CachedUserProfileData> {
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
  final int totalSolves;
  final int minMoves;
  final double avgMoves;
  final int coinsBalance;
  final String lastSyncedAt;
  const CachedUserProfileData({
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
    required this.totalSolves,
    required this.minMoves,
    required this.avgMoves,
    required this.coinsBalance,
    required this.lastSyncedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['username'] = Variable<String>(username);
    map['email'] = Variable<String>(email);
    map['role'] = Variable<String>(role);
    map['bio'] = Variable<String>(bio);
    map['avatar_color'] = Variable<String>(avatarColor);
    map['wca_id'] = Variable<String>(wcaId);
    map['country'] = Variable<String>(country);
    map['main_cube'] = Variable<String>(mainCube);
    map['preferred_method'] = Variable<String>(preferredMethod);
    map['pb_single'] = Variable<String>(pbSingle);
    map['pb_ao5'] = Variable<String>(pbAo5);
    map['total_solves'] = Variable<int>(totalSolves);
    map['min_moves'] = Variable<int>(minMoves);
    map['avg_moves'] = Variable<double>(avgMoves);
    map['coins_balance'] = Variable<int>(coinsBalance);
    map['last_synced_at'] = Variable<String>(lastSyncedAt);
    return map;
  }

  CachedUserProfileCompanion toCompanion(bool nullToAbsent) {
    return CachedUserProfileCompanion(
      id: Value(id),
      username: Value(username),
      email: Value(email),
      role: Value(role),
      bio: Value(bio),
      avatarColor: Value(avatarColor),
      wcaId: Value(wcaId),
      country: Value(country),
      mainCube: Value(mainCube),
      preferredMethod: Value(preferredMethod),
      pbSingle: Value(pbSingle),
      pbAo5: Value(pbAo5),
      totalSolves: Value(totalSolves),
      minMoves: Value(minMoves),
      avgMoves: Value(avgMoves),
      coinsBalance: Value(coinsBalance),
      lastSyncedAt: Value(lastSyncedAt),
    );
  }

  factory CachedUserProfileData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedUserProfileData(
      id: serializer.fromJson<int>(json['id']),
      username: serializer.fromJson<String>(json['username']),
      email: serializer.fromJson<String>(json['email']),
      role: serializer.fromJson<String>(json['role']),
      bio: serializer.fromJson<String>(json['bio']),
      avatarColor: serializer.fromJson<String>(json['avatarColor']),
      wcaId: serializer.fromJson<String>(json['wcaId']),
      country: serializer.fromJson<String>(json['country']),
      mainCube: serializer.fromJson<String>(json['mainCube']),
      preferredMethod: serializer.fromJson<String>(json['preferredMethod']),
      pbSingle: serializer.fromJson<String>(json['pbSingle']),
      pbAo5: serializer.fromJson<String>(json['pbAo5']),
      totalSolves: serializer.fromJson<int>(json['totalSolves']),
      minMoves: serializer.fromJson<int>(json['minMoves']),
      avgMoves: serializer.fromJson<double>(json['avgMoves']),
      coinsBalance: serializer.fromJson<int>(json['coinsBalance']),
      lastSyncedAt: serializer.fromJson<String>(json['lastSyncedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'username': serializer.toJson<String>(username),
      'email': serializer.toJson<String>(email),
      'role': serializer.toJson<String>(role),
      'bio': serializer.toJson<String>(bio),
      'avatarColor': serializer.toJson<String>(avatarColor),
      'wcaId': serializer.toJson<String>(wcaId),
      'country': serializer.toJson<String>(country),
      'mainCube': serializer.toJson<String>(mainCube),
      'preferredMethod': serializer.toJson<String>(preferredMethod),
      'pbSingle': serializer.toJson<String>(pbSingle),
      'pbAo5': serializer.toJson<String>(pbAo5),
      'totalSolves': serializer.toJson<int>(totalSolves),
      'minMoves': serializer.toJson<int>(minMoves),
      'avgMoves': serializer.toJson<double>(avgMoves),
      'coinsBalance': serializer.toJson<int>(coinsBalance),
      'lastSyncedAt': serializer.toJson<String>(lastSyncedAt),
    };
  }

  CachedUserProfileData copyWith({
    int? id,
    String? username,
    String? email,
    String? role,
    String? bio,
    String? avatarColor,
    String? wcaId,
    String? country,
    String? mainCube,
    String? preferredMethod,
    String? pbSingle,
    String? pbAo5,
    int? totalSolves,
    int? minMoves,
    double? avgMoves,
    int? coinsBalance,
    String? lastSyncedAt,
  }) => CachedUserProfileData(
    id: id ?? this.id,
    username: username ?? this.username,
    email: email ?? this.email,
    role: role ?? this.role,
    bio: bio ?? this.bio,
    avatarColor: avatarColor ?? this.avatarColor,
    wcaId: wcaId ?? this.wcaId,
    country: country ?? this.country,
    mainCube: mainCube ?? this.mainCube,
    preferredMethod: preferredMethod ?? this.preferredMethod,
    pbSingle: pbSingle ?? this.pbSingle,
    pbAo5: pbAo5 ?? this.pbAo5,
    totalSolves: totalSolves ?? this.totalSolves,
    minMoves: minMoves ?? this.minMoves,
    avgMoves: avgMoves ?? this.avgMoves,
    coinsBalance: coinsBalance ?? this.coinsBalance,
    lastSyncedAt: lastSyncedAt ?? this.lastSyncedAt,
  );
  CachedUserProfileData copyWithCompanion(CachedUserProfileCompanion data) {
    return CachedUserProfileData(
      id: data.id.present ? data.id.value : this.id,
      username: data.username.present ? data.username.value : this.username,
      email: data.email.present ? data.email.value : this.email,
      role: data.role.present ? data.role.value : this.role,
      bio: data.bio.present ? data.bio.value : this.bio,
      avatarColor: data.avatarColor.present
          ? data.avatarColor.value
          : this.avatarColor,
      wcaId: data.wcaId.present ? data.wcaId.value : this.wcaId,
      country: data.country.present ? data.country.value : this.country,
      mainCube: data.mainCube.present ? data.mainCube.value : this.mainCube,
      preferredMethod: data.preferredMethod.present
          ? data.preferredMethod.value
          : this.preferredMethod,
      pbSingle: data.pbSingle.present ? data.pbSingle.value : this.pbSingle,
      pbAo5: data.pbAo5.present ? data.pbAo5.value : this.pbAo5,
      totalSolves: data.totalSolves.present
          ? data.totalSolves.value
          : this.totalSolves,
      minMoves: data.minMoves.present ? data.minMoves.value : this.minMoves,
      avgMoves: data.avgMoves.present ? data.avgMoves.value : this.avgMoves,
      coinsBalance: data.coinsBalance.present
          ? data.coinsBalance.value
          : this.coinsBalance,
      lastSyncedAt: data.lastSyncedAt.present
          ? data.lastSyncedAt.value
          : this.lastSyncedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedUserProfileData(')
          ..write('id: $id, ')
          ..write('username: $username, ')
          ..write('email: $email, ')
          ..write('role: $role, ')
          ..write('bio: $bio, ')
          ..write('avatarColor: $avatarColor, ')
          ..write('wcaId: $wcaId, ')
          ..write('country: $country, ')
          ..write('mainCube: $mainCube, ')
          ..write('preferredMethod: $preferredMethod, ')
          ..write('pbSingle: $pbSingle, ')
          ..write('pbAo5: $pbAo5, ')
          ..write('totalSolves: $totalSolves, ')
          ..write('minMoves: $minMoves, ')
          ..write('avgMoves: $avgMoves, ')
          ..write('coinsBalance: $coinsBalance, ')
          ..write('lastSyncedAt: $lastSyncedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    username,
    email,
    role,
    bio,
    avatarColor,
    wcaId,
    country,
    mainCube,
    preferredMethod,
    pbSingle,
    pbAo5,
    totalSolves,
    minMoves,
    avgMoves,
    coinsBalance,
    lastSyncedAt,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedUserProfileData &&
          other.id == this.id &&
          other.username == this.username &&
          other.email == this.email &&
          other.role == this.role &&
          other.bio == this.bio &&
          other.avatarColor == this.avatarColor &&
          other.wcaId == this.wcaId &&
          other.country == this.country &&
          other.mainCube == this.mainCube &&
          other.preferredMethod == this.preferredMethod &&
          other.pbSingle == this.pbSingle &&
          other.pbAo5 == this.pbAo5 &&
          other.totalSolves == this.totalSolves &&
          other.minMoves == this.minMoves &&
          other.avgMoves == this.avgMoves &&
          other.coinsBalance == this.coinsBalance &&
          other.lastSyncedAt == this.lastSyncedAt);
}

class CachedUserProfileCompanion
    extends UpdateCompanion<CachedUserProfileData> {
  final Value<int> id;
  final Value<String> username;
  final Value<String> email;
  final Value<String> role;
  final Value<String> bio;
  final Value<String> avatarColor;
  final Value<String> wcaId;
  final Value<String> country;
  final Value<String> mainCube;
  final Value<String> preferredMethod;
  final Value<String> pbSingle;
  final Value<String> pbAo5;
  final Value<int> totalSolves;
  final Value<int> minMoves;
  final Value<double> avgMoves;
  final Value<int> coinsBalance;
  final Value<String> lastSyncedAt;
  const CachedUserProfileCompanion({
    this.id = const Value.absent(),
    this.username = const Value.absent(),
    this.email = const Value.absent(),
    this.role = const Value.absent(),
    this.bio = const Value.absent(),
    this.avatarColor = const Value.absent(),
    this.wcaId = const Value.absent(),
    this.country = const Value.absent(),
    this.mainCube = const Value.absent(),
    this.preferredMethod = const Value.absent(),
    this.pbSingle = const Value.absent(),
    this.pbAo5 = const Value.absent(),
    this.totalSolves = const Value.absent(),
    this.minMoves = const Value.absent(),
    this.avgMoves = const Value.absent(),
    this.coinsBalance = const Value.absent(),
    this.lastSyncedAt = const Value.absent(),
  });
  CachedUserProfileCompanion.insert({
    this.id = const Value.absent(),
    required String username,
    this.email = const Value.absent(),
    this.role = const Value.absent(),
    this.bio = const Value.absent(),
    this.avatarColor = const Value.absent(),
    this.wcaId = const Value.absent(),
    this.country = const Value.absent(),
    this.mainCube = const Value.absent(),
    this.preferredMethod = const Value.absent(),
    this.pbSingle = const Value.absent(),
    this.pbAo5 = const Value.absent(),
    this.totalSolves = const Value.absent(),
    this.minMoves = const Value.absent(),
    this.avgMoves = const Value.absent(),
    this.coinsBalance = const Value.absent(),
    required String lastSyncedAt,
  }) : username = Value(username),
       lastSyncedAt = Value(lastSyncedAt);
  static Insertable<CachedUserProfileData> custom({
    Expression<int>? id,
    Expression<String>? username,
    Expression<String>? email,
    Expression<String>? role,
    Expression<String>? bio,
    Expression<String>? avatarColor,
    Expression<String>? wcaId,
    Expression<String>? country,
    Expression<String>? mainCube,
    Expression<String>? preferredMethod,
    Expression<String>? pbSingle,
    Expression<String>? pbAo5,
    Expression<int>? totalSolves,
    Expression<int>? minMoves,
    Expression<double>? avgMoves,
    Expression<int>? coinsBalance,
    Expression<String>? lastSyncedAt,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (username != null) 'username': username,
      if (email != null) 'email': email,
      if (role != null) 'role': role,
      if (bio != null) 'bio': bio,
      if (avatarColor != null) 'avatar_color': avatarColor,
      if (wcaId != null) 'wca_id': wcaId,
      if (country != null) 'country': country,
      if (mainCube != null) 'main_cube': mainCube,
      if (preferredMethod != null) 'preferred_method': preferredMethod,
      if (pbSingle != null) 'pb_single': pbSingle,
      if (pbAo5 != null) 'pb_ao5': pbAo5,
      if (totalSolves != null) 'total_solves': totalSolves,
      if (minMoves != null) 'min_moves': minMoves,
      if (avgMoves != null) 'avg_moves': avgMoves,
      if (coinsBalance != null) 'coins_balance': coinsBalance,
      if (lastSyncedAt != null) 'last_synced_at': lastSyncedAt,
    });
  }

  CachedUserProfileCompanion copyWith({
    Value<int>? id,
    Value<String>? username,
    Value<String>? email,
    Value<String>? role,
    Value<String>? bio,
    Value<String>? avatarColor,
    Value<String>? wcaId,
    Value<String>? country,
    Value<String>? mainCube,
    Value<String>? preferredMethod,
    Value<String>? pbSingle,
    Value<String>? pbAo5,
    Value<int>? totalSolves,
    Value<int>? minMoves,
    Value<double>? avgMoves,
    Value<int>? coinsBalance,
    Value<String>? lastSyncedAt,
  }) {
    return CachedUserProfileCompanion(
      id: id ?? this.id,
      username: username ?? this.username,
      email: email ?? this.email,
      role: role ?? this.role,
      bio: bio ?? this.bio,
      avatarColor: avatarColor ?? this.avatarColor,
      wcaId: wcaId ?? this.wcaId,
      country: country ?? this.country,
      mainCube: mainCube ?? this.mainCube,
      preferredMethod: preferredMethod ?? this.preferredMethod,
      pbSingle: pbSingle ?? this.pbSingle,
      pbAo5: pbAo5 ?? this.pbAo5,
      totalSolves: totalSolves ?? this.totalSolves,
      minMoves: minMoves ?? this.minMoves,
      avgMoves: avgMoves ?? this.avgMoves,
      coinsBalance: coinsBalance ?? this.coinsBalance,
      lastSyncedAt: lastSyncedAt ?? this.lastSyncedAt,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (username.present) {
      map['username'] = Variable<String>(username.value);
    }
    if (email.present) {
      map['email'] = Variable<String>(email.value);
    }
    if (role.present) {
      map['role'] = Variable<String>(role.value);
    }
    if (bio.present) {
      map['bio'] = Variable<String>(bio.value);
    }
    if (avatarColor.present) {
      map['avatar_color'] = Variable<String>(avatarColor.value);
    }
    if (wcaId.present) {
      map['wca_id'] = Variable<String>(wcaId.value);
    }
    if (country.present) {
      map['country'] = Variable<String>(country.value);
    }
    if (mainCube.present) {
      map['main_cube'] = Variable<String>(mainCube.value);
    }
    if (preferredMethod.present) {
      map['preferred_method'] = Variable<String>(preferredMethod.value);
    }
    if (pbSingle.present) {
      map['pb_single'] = Variable<String>(pbSingle.value);
    }
    if (pbAo5.present) {
      map['pb_ao5'] = Variable<String>(pbAo5.value);
    }
    if (totalSolves.present) {
      map['total_solves'] = Variable<int>(totalSolves.value);
    }
    if (minMoves.present) {
      map['min_moves'] = Variable<int>(minMoves.value);
    }
    if (avgMoves.present) {
      map['avg_moves'] = Variable<double>(avgMoves.value);
    }
    if (coinsBalance.present) {
      map['coins_balance'] = Variable<int>(coinsBalance.value);
    }
    if (lastSyncedAt.present) {
      map['last_synced_at'] = Variable<String>(lastSyncedAt.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedUserProfileCompanion(')
          ..write('id: $id, ')
          ..write('username: $username, ')
          ..write('email: $email, ')
          ..write('role: $role, ')
          ..write('bio: $bio, ')
          ..write('avatarColor: $avatarColor, ')
          ..write('wcaId: $wcaId, ')
          ..write('country: $country, ')
          ..write('mainCube: $mainCube, ')
          ..write('preferredMethod: $preferredMethod, ')
          ..write('pbSingle: $pbSingle, ')
          ..write('pbAo5: $pbAo5, ')
          ..write('totalSolves: $totalSolves, ')
          ..write('minMoves: $minMoves, ')
          ..write('avgMoves: $avgMoves, ')
          ..write('coinsBalance: $coinsBalance, ')
          ..write('lastSyncedAt: $lastSyncedAt')
          ..write(')'))
        .toString();
  }
}

class $CachedPatternsTable extends CachedPatterns
    with TableInfo<$CachedPatternsTable, CachedPattern> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedPatternsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
    'name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _movesMeta = const VerificationMeta('moves');
  @override
  late final GeneratedColumn<String> moves = GeneratedColumn<String>(
    'moves',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _descriptionMeta = const VerificationMeta(
    'description',
  );
  @override
  late final GeneratedColumn<String> description = GeneratedColumn<String>(
    'description',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant(''),
  );
  @override
  List<GeneratedColumn> get $columns => [id, name, moves, description];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_patterns';
  @override
  VerificationContext validateIntegrity(
    Insertable<CachedPattern> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
        _nameMeta,
        name.isAcceptableOrUnknown(data['name']!, _nameMeta),
      );
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('moves')) {
      context.handle(
        _movesMeta,
        moves.isAcceptableOrUnknown(data['moves']!, _movesMeta),
      );
    } else if (isInserting) {
      context.missing(_movesMeta);
    }
    if (data.containsKey('description')) {
      context.handle(
        _descriptionMeta,
        description.isAcceptableOrUnknown(
          data['description']!,
          _descriptionMeta,
        ),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CachedPattern map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedPattern(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      name: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}name'],
      )!,
      moves: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}moves'],
      )!,
      description: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}description'],
      )!,
    );
  }

  @override
  $CachedPatternsTable createAlias(String alias) {
    return $CachedPatternsTable(attachedDatabase, alias);
  }
}

class CachedPattern extends DataClass implements Insertable<CachedPattern> {
  final String id;
  final String name;
  final String moves;
  final String description;
  const CachedPattern({
    required this.id,
    required this.name,
    required this.moves,
    required this.description,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['name'] = Variable<String>(name);
    map['moves'] = Variable<String>(moves);
    map['description'] = Variable<String>(description);
    return map;
  }

  CachedPatternsCompanion toCompanion(bool nullToAbsent) {
    return CachedPatternsCompanion(
      id: Value(id),
      name: Value(name),
      moves: Value(moves),
      description: Value(description),
    );
  }

  factory CachedPattern.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedPattern(
      id: serializer.fromJson<String>(json['id']),
      name: serializer.fromJson<String>(json['name']),
      moves: serializer.fromJson<String>(json['moves']),
      description: serializer.fromJson<String>(json['description']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'name': serializer.toJson<String>(name),
      'moves': serializer.toJson<String>(moves),
      'description': serializer.toJson<String>(description),
    };
  }

  CachedPattern copyWith({
    String? id,
    String? name,
    String? moves,
    String? description,
  }) => CachedPattern(
    id: id ?? this.id,
    name: name ?? this.name,
    moves: moves ?? this.moves,
    description: description ?? this.description,
  );
  CachedPattern copyWithCompanion(CachedPatternsCompanion data) {
    return CachedPattern(
      id: data.id.present ? data.id.value : this.id,
      name: data.name.present ? data.name.value : this.name,
      moves: data.moves.present ? data.moves.value : this.moves,
      description: data.description.present
          ? data.description.value
          : this.description,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedPattern(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('moves: $moves, ')
          ..write('description: $description')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, name, moves, description);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedPattern &&
          other.id == this.id &&
          other.name == this.name &&
          other.moves == this.moves &&
          other.description == this.description);
}

class CachedPatternsCompanion extends UpdateCompanion<CachedPattern> {
  final Value<String> id;
  final Value<String> name;
  final Value<String> moves;
  final Value<String> description;
  final Value<int> rowid;
  const CachedPatternsCompanion({
    this.id = const Value.absent(),
    this.name = const Value.absent(),
    this.moves = const Value.absent(),
    this.description = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedPatternsCompanion.insert({
    required String id,
    required String name,
    required String moves,
    this.description = const Value.absent(),
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       name = Value(name),
       moves = Value(moves);
  static Insertable<CachedPattern> custom({
    Expression<String>? id,
    Expression<String>? name,
    Expression<String>? moves,
    Expression<String>? description,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (name != null) 'name': name,
      if (moves != null) 'moves': moves,
      if (description != null) 'description': description,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedPatternsCompanion copyWith({
    Value<String>? id,
    Value<String>? name,
    Value<String>? moves,
    Value<String>? description,
    Value<int>? rowid,
  }) {
    return CachedPatternsCompanion(
      id: id ?? this.id,
      name: name ?? this.name,
      moves: moves ?? this.moves,
      description: description ?? this.description,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (moves.present) {
      map['moves'] = Variable<String>(moves.value);
    }
    if (description.present) {
      map['description'] = Variable<String>(description.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedPatternsCompanion(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('moves: $moves, ')
          ..write('description: $description, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $CachedScanResultsTable extends CachedScanResults
    with TableInfo<$CachedScanResultsTable, CachedScanResult> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedScanResultsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _centerColorMeta = const VerificationMeta(
    'centerColor',
  );
  @override
  late final GeneratedColumn<String> centerColor = GeneratedColumn<String>(
    'center_color',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _faceGridJsonMeta = const VerificationMeta(
    'faceGridJson',
  );
  @override
  late final GeneratedColumn<String> faceGridJson = GeneratedColumn<String>(
    'face_grid_json',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _annotatedImageBase64Meta =
      const VerificationMeta('annotatedImageBase64');
  @override
  late final GeneratedColumn<String> annotatedImageBase64 =
      GeneratedColumn<String>(
        'annotated_image_base64',
        aliasedName,
        false,
        type: DriftSqlType.string,
        requiredDuringInsert: true,
      );
  static const VerificationMeta _scannedAtMeta = const VerificationMeta(
    'scannedAt',
  );
  @override
  late final GeneratedColumn<String> scannedAt = GeneratedColumn<String>(
    'scanned_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    centerColor,
    faceGridJson,
    annotatedImageBase64,
    scannedAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_scan_results';
  @override
  VerificationContext validateIntegrity(
    Insertable<CachedScanResult> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('center_color')) {
      context.handle(
        _centerColorMeta,
        centerColor.isAcceptableOrUnknown(
          data['center_color']!,
          _centerColorMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_centerColorMeta);
    }
    if (data.containsKey('face_grid_json')) {
      context.handle(
        _faceGridJsonMeta,
        faceGridJson.isAcceptableOrUnknown(
          data['face_grid_json']!,
          _faceGridJsonMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_faceGridJsonMeta);
    }
    if (data.containsKey('annotated_image_base64')) {
      context.handle(
        _annotatedImageBase64Meta,
        annotatedImageBase64.isAcceptableOrUnknown(
          data['annotated_image_base64']!,
          _annotatedImageBase64Meta,
        ),
      );
    } else if (isInserting) {
      context.missing(_annotatedImageBase64Meta);
    }
    if (data.containsKey('scanned_at')) {
      context.handle(
        _scannedAtMeta,
        scannedAt.isAcceptableOrUnknown(data['scanned_at']!, _scannedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_scannedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CachedScanResult map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedScanResult(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      centerColor: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}center_color'],
      )!,
      faceGridJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}face_grid_json'],
      )!,
      annotatedImageBase64: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}annotated_image_base64'],
      )!,
      scannedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}scanned_at'],
      )!,
    );
  }

  @override
  $CachedScanResultsTable createAlias(String alias) {
    return $CachedScanResultsTable(attachedDatabase, alias);
  }
}

class CachedScanResult extends DataClass
    implements Insertable<CachedScanResult> {
  final int id;
  final String centerColor;
  final String faceGridJson;
  final String annotatedImageBase64;
  final String scannedAt;
  const CachedScanResult({
    required this.id,
    required this.centerColor,
    required this.faceGridJson,
    required this.annotatedImageBase64,
    required this.scannedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['center_color'] = Variable<String>(centerColor);
    map['face_grid_json'] = Variable<String>(faceGridJson);
    map['annotated_image_base64'] = Variable<String>(annotatedImageBase64);
    map['scanned_at'] = Variable<String>(scannedAt);
    return map;
  }

  CachedScanResultsCompanion toCompanion(bool nullToAbsent) {
    return CachedScanResultsCompanion(
      id: Value(id),
      centerColor: Value(centerColor),
      faceGridJson: Value(faceGridJson),
      annotatedImageBase64: Value(annotatedImageBase64),
      scannedAt: Value(scannedAt),
    );
  }

  factory CachedScanResult.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedScanResult(
      id: serializer.fromJson<int>(json['id']),
      centerColor: serializer.fromJson<String>(json['centerColor']),
      faceGridJson: serializer.fromJson<String>(json['faceGridJson']),
      annotatedImageBase64: serializer.fromJson<String>(
        json['annotatedImageBase64'],
      ),
      scannedAt: serializer.fromJson<String>(json['scannedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'centerColor': serializer.toJson<String>(centerColor),
      'faceGridJson': serializer.toJson<String>(faceGridJson),
      'annotatedImageBase64': serializer.toJson<String>(annotatedImageBase64),
      'scannedAt': serializer.toJson<String>(scannedAt),
    };
  }

  CachedScanResult copyWith({
    int? id,
    String? centerColor,
    String? faceGridJson,
    String? annotatedImageBase64,
    String? scannedAt,
  }) => CachedScanResult(
    id: id ?? this.id,
    centerColor: centerColor ?? this.centerColor,
    faceGridJson: faceGridJson ?? this.faceGridJson,
    annotatedImageBase64: annotatedImageBase64 ?? this.annotatedImageBase64,
    scannedAt: scannedAt ?? this.scannedAt,
  );
  CachedScanResult copyWithCompanion(CachedScanResultsCompanion data) {
    return CachedScanResult(
      id: data.id.present ? data.id.value : this.id,
      centerColor: data.centerColor.present
          ? data.centerColor.value
          : this.centerColor,
      faceGridJson: data.faceGridJson.present
          ? data.faceGridJson.value
          : this.faceGridJson,
      annotatedImageBase64: data.annotatedImageBase64.present
          ? data.annotatedImageBase64.value
          : this.annotatedImageBase64,
      scannedAt: data.scannedAt.present ? data.scannedAt.value : this.scannedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedScanResult(')
          ..write('id: $id, ')
          ..write('centerColor: $centerColor, ')
          ..write('faceGridJson: $faceGridJson, ')
          ..write('annotatedImageBase64: $annotatedImageBase64, ')
          ..write('scannedAt: $scannedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    centerColor,
    faceGridJson,
    annotatedImageBase64,
    scannedAt,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedScanResult &&
          other.id == this.id &&
          other.centerColor == this.centerColor &&
          other.faceGridJson == this.faceGridJson &&
          other.annotatedImageBase64 == this.annotatedImageBase64 &&
          other.scannedAt == this.scannedAt);
}

class CachedScanResultsCompanion extends UpdateCompanion<CachedScanResult> {
  final Value<int> id;
  final Value<String> centerColor;
  final Value<String> faceGridJson;
  final Value<String> annotatedImageBase64;
  final Value<String> scannedAt;
  const CachedScanResultsCompanion({
    this.id = const Value.absent(),
    this.centerColor = const Value.absent(),
    this.faceGridJson = const Value.absent(),
    this.annotatedImageBase64 = const Value.absent(),
    this.scannedAt = const Value.absent(),
  });
  CachedScanResultsCompanion.insert({
    this.id = const Value.absent(),
    required String centerColor,
    required String faceGridJson,
    required String annotatedImageBase64,
    required String scannedAt,
  }) : centerColor = Value(centerColor),
       faceGridJson = Value(faceGridJson),
       annotatedImageBase64 = Value(annotatedImageBase64),
       scannedAt = Value(scannedAt);
  static Insertable<CachedScanResult> custom({
    Expression<int>? id,
    Expression<String>? centerColor,
    Expression<String>? faceGridJson,
    Expression<String>? annotatedImageBase64,
    Expression<String>? scannedAt,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (centerColor != null) 'center_color': centerColor,
      if (faceGridJson != null) 'face_grid_json': faceGridJson,
      if (annotatedImageBase64 != null)
        'annotated_image_base64': annotatedImageBase64,
      if (scannedAt != null) 'scanned_at': scannedAt,
    });
  }

  CachedScanResultsCompanion copyWith({
    Value<int>? id,
    Value<String>? centerColor,
    Value<String>? faceGridJson,
    Value<String>? annotatedImageBase64,
    Value<String>? scannedAt,
  }) {
    return CachedScanResultsCompanion(
      id: id ?? this.id,
      centerColor: centerColor ?? this.centerColor,
      faceGridJson: faceGridJson ?? this.faceGridJson,
      annotatedImageBase64: annotatedImageBase64 ?? this.annotatedImageBase64,
      scannedAt: scannedAt ?? this.scannedAt,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (centerColor.present) {
      map['center_color'] = Variable<String>(centerColor.value);
    }
    if (faceGridJson.present) {
      map['face_grid_json'] = Variable<String>(faceGridJson.value);
    }
    if (annotatedImageBase64.present) {
      map['annotated_image_base64'] = Variable<String>(
        annotatedImageBase64.value,
      );
    }
    if (scannedAt.present) {
      map['scanned_at'] = Variable<String>(scannedAt.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedScanResultsCompanion(')
          ..write('id: $id, ')
          ..write('centerColor: $centerColor, ')
          ..write('faceGridJson: $faceGridJson, ')
          ..write('annotatedImageBase64: $annotatedImageBase64, ')
          ..write('scannedAt: $scannedAt')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $CachedSolvesTable cachedSolves = $CachedSolvesTable(this);
  late final $CachedUserProfileTable cachedUserProfile =
      $CachedUserProfileTable(this);
  late final $CachedPatternsTable cachedPatterns = $CachedPatternsTable(this);
  late final $CachedScanResultsTable cachedScanResults =
      $CachedScanResultsTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
    cachedSolves,
    cachedUserProfile,
    cachedPatterns,
    cachedScanResults,
  ];
}

typedef $$CachedSolvesTableCreateCompanionBuilder =
    CachedSolvesCompanion Function({
      Value<int> id,
      Value<int?> remoteId,
      required String scramble,
      required String solution,
      required int moveCount,
      required String createdAt,
    });
typedef $$CachedSolvesTableUpdateCompanionBuilder =
    CachedSolvesCompanion Function({
      Value<int> id,
      Value<int?> remoteId,
      Value<String> scramble,
      Value<String> solution,
      Value<int> moveCount,
      Value<String> createdAt,
    });

class $$CachedSolvesTableFilterComposer
    extends Composer<_$AppDatabase, $CachedSolvesTable> {
  $$CachedSolvesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get remoteId => $composableBuilder(
    column: $table.remoteId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get scramble => $composableBuilder(
    column: $table.scramble,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get solution => $composableBuilder(
    column: $table.solution,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get moveCount => $composableBuilder(
    column: $table.moveCount,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CachedSolvesTableOrderingComposer
    extends Composer<_$AppDatabase, $CachedSolvesTable> {
  $$CachedSolvesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get remoteId => $composableBuilder(
    column: $table.remoteId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get scramble => $composableBuilder(
    column: $table.scramble,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get solution => $composableBuilder(
    column: $table.solution,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get moveCount => $composableBuilder(
    column: $table.moveCount,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CachedSolvesTableAnnotationComposer
    extends Composer<_$AppDatabase, $CachedSolvesTable> {
  $$CachedSolvesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<int> get remoteId =>
      $composableBuilder(column: $table.remoteId, builder: (column) => column);

  GeneratedColumn<String> get scramble =>
      $composableBuilder(column: $table.scramble, builder: (column) => column);

  GeneratedColumn<String> get solution =>
      $composableBuilder(column: $table.solution, builder: (column) => column);

  GeneratedColumn<int> get moveCount =>
      $composableBuilder(column: $table.moveCount, builder: (column) => column);

  GeneratedColumn<String> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);
}

class $$CachedSolvesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $CachedSolvesTable,
          CachedSolve,
          $$CachedSolvesTableFilterComposer,
          $$CachedSolvesTableOrderingComposer,
          $$CachedSolvesTableAnnotationComposer,
          $$CachedSolvesTableCreateCompanionBuilder,
          $$CachedSolvesTableUpdateCompanionBuilder,
          (
            CachedSolve,
            BaseReferences<_$AppDatabase, $CachedSolvesTable, CachedSolve>,
          ),
          CachedSolve,
          PrefetchHooks Function()
        > {
  $$CachedSolvesTableTableManager(_$AppDatabase db, $CachedSolvesTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedSolvesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedSolvesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedSolvesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<int?> remoteId = const Value.absent(),
                Value<String> scramble = const Value.absent(),
                Value<String> solution = const Value.absent(),
                Value<int> moveCount = const Value.absent(),
                Value<String> createdAt = const Value.absent(),
              }) => CachedSolvesCompanion(
                id: id,
                remoteId: remoteId,
                scramble: scramble,
                solution: solution,
                moveCount: moveCount,
                createdAt: createdAt,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<int?> remoteId = const Value.absent(),
                required String scramble,
                required String solution,
                required int moveCount,
                required String createdAt,
              }) => CachedSolvesCompanion.insert(
                id: id,
                remoteId: remoteId,
                scramble: scramble,
                solution: solution,
                moveCount: moveCount,
                createdAt: createdAt,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$CachedSolvesTable, CachedSolve>(table),
                  BaseReferences<
                    _$AppDatabase,
                    $CachedSolvesTable,
                    CachedSolve
                  >(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CachedSolvesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $CachedSolvesTable,
      CachedSolve,
      $$CachedSolvesTableFilterComposer,
      $$CachedSolvesTableOrderingComposer,
      $$CachedSolvesTableAnnotationComposer,
      $$CachedSolvesTableCreateCompanionBuilder,
      $$CachedSolvesTableUpdateCompanionBuilder,
      (
        CachedSolve,
        BaseReferences<_$AppDatabase, $CachedSolvesTable, CachedSolve>,
      ),
      CachedSolve,
      PrefetchHooks Function()
    >;
typedef $$CachedUserProfileTableCreateCompanionBuilder =
    CachedUserProfileCompanion Function({
      Value<int> id,
      required String username,
      Value<String> email,
      Value<String> role,
      Value<String> bio,
      Value<String> avatarColor,
      Value<String> wcaId,
      Value<String> country,
      Value<String> mainCube,
      Value<String> preferredMethod,
      Value<String> pbSingle,
      Value<String> pbAo5,
      Value<int> totalSolves,
      Value<int> minMoves,
      Value<double> avgMoves,
      Value<int> coinsBalance,
      required String lastSyncedAt,
    });
typedef $$CachedUserProfileTableUpdateCompanionBuilder =
    CachedUserProfileCompanion Function({
      Value<int> id,
      Value<String> username,
      Value<String> email,
      Value<String> role,
      Value<String> bio,
      Value<String> avatarColor,
      Value<String> wcaId,
      Value<String> country,
      Value<String> mainCube,
      Value<String> preferredMethod,
      Value<String> pbSingle,
      Value<String> pbAo5,
      Value<int> totalSolves,
      Value<int> minMoves,
      Value<double> avgMoves,
      Value<int> coinsBalance,
      Value<String> lastSyncedAt,
    });

class $$CachedUserProfileTableFilterComposer
    extends Composer<_$AppDatabase, $CachedUserProfileTable> {
  $$CachedUserProfileTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get username => $composableBuilder(
    column: $table.username,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get email => $composableBuilder(
    column: $table.email,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get role => $composableBuilder(
    column: $table.role,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get bio => $composableBuilder(
    column: $table.bio,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get avatarColor => $composableBuilder(
    column: $table.avatarColor,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get wcaId => $composableBuilder(
    column: $table.wcaId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get country => $composableBuilder(
    column: $table.country,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get mainCube => $composableBuilder(
    column: $table.mainCube,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get preferredMethod => $composableBuilder(
    column: $table.preferredMethod,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get pbSingle => $composableBuilder(
    column: $table.pbSingle,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get pbAo5 => $composableBuilder(
    column: $table.pbAo5,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get totalSolves => $composableBuilder(
    column: $table.totalSolves,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get minMoves => $composableBuilder(
    column: $table.minMoves,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get avgMoves => $composableBuilder(
    column: $table.avgMoves,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get coinsBalance => $composableBuilder(
    column: $table.coinsBalance,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get lastSyncedAt => $composableBuilder(
    column: $table.lastSyncedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CachedUserProfileTableOrderingComposer
    extends Composer<_$AppDatabase, $CachedUserProfileTable> {
  $$CachedUserProfileTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get username => $composableBuilder(
    column: $table.username,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get email => $composableBuilder(
    column: $table.email,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get role => $composableBuilder(
    column: $table.role,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get bio => $composableBuilder(
    column: $table.bio,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get avatarColor => $composableBuilder(
    column: $table.avatarColor,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get wcaId => $composableBuilder(
    column: $table.wcaId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get country => $composableBuilder(
    column: $table.country,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get mainCube => $composableBuilder(
    column: $table.mainCube,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get preferredMethod => $composableBuilder(
    column: $table.preferredMethod,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get pbSingle => $composableBuilder(
    column: $table.pbSingle,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get pbAo5 => $composableBuilder(
    column: $table.pbAo5,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get totalSolves => $composableBuilder(
    column: $table.totalSolves,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get minMoves => $composableBuilder(
    column: $table.minMoves,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get avgMoves => $composableBuilder(
    column: $table.avgMoves,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get coinsBalance => $composableBuilder(
    column: $table.coinsBalance,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get lastSyncedAt => $composableBuilder(
    column: $table.lastSyncedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CachedUserProfileTableAnnotationComposer
    extends Composer<_$AppDatabase, $CachedUserProfileTable> {
  $$CachedUserProfileTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get username =>
      $composableBuilder(column: $table.username, builder: (column) => column);

  GeneratedColumn<String> get email =>
      $composableBuilder(column: $table.email, builder: (column) => column);

  GeneratedColumn<String> get role =>
      $composableBuilder(column: $table.role, builder: (column) => column);

  GeneratedColumn<String> get bio =>
      $composableBuilder(column: $table.bio, builder: (column) => column);

  GeneratedColumn<String> get avatarColor => $composableBuilder(
    column: $table.avatarColor,
    builder: (column) => column,
  );

  GeneratedColumn<String> get wcaId =>
      $composableBuilder(column: $table.wcaId, builder: (column) => column);

  GeneratedColumn<String> get country =>
      $composableBuilder(column: $table.country, builder: (column) => column);

  GeneratedColumn<String> get mainCube =>
      $composableBuilder(column: $table.mainCube, builder: (column) => column);

  GeneratedColumn<String> get preferredMethod => $composableBuilder(
    column: $table.preferredMethod,
    builder: (column) => column,
  );

  GeneratedColumn<String> get pbSingle =>
      $composableBuilder(column: $table.pbSingle, builder: (column) => column);

  GeneratedColumn<String> get pbAo5 =>
      $composableBuilder(column: $table.pbAo5, builder: (column) => column);

  GeneratedColumn<int> get totalSolves => $composableBuilder(
    column: $table.totalSolves,
    builder: (column) => column,
  );

  GeneratedColumn<int> get minMoves =>
      $composableBuilder(column: $table.minMoves, builder: (column) => column);

  GeneratedColumn<double> get avgMoves =>
      $composableBuilder(column: $table.avgMoves, builder: (column) => column);

  GeneratedColumn<int> get coinsBalance => $composableBuilder(
    column: $table.coinsBalance,
    builder: (column) => column,
  );

  GeneratedColumn<String> get lastSyncedAt => $composableBuilder(
    column: $table.lastSyncedAt,
    builder: (column) => column,
  );
}

class $$CachedUserProfileTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $CachedUserProfileTable,
          CachedUserProfileData,
          $$CachedUserProfileTableFilterComposer,
          $$CachedUserProfileTableOrderingComposer,
          $$CachedUserProfileTableAnnotationComposer,
          $$CachedUserProfileTableCreateCompanionBuilder,
          $$CachedUserProfileTableUpdateCompanionBuilder,
          (
            CachedUserProfileData,
            BaseReferences<
              _$AppDatabase,
              $CachedUserProfileTable,
              CachedUserProfileData
            >,
          ),
          CachedUserProfileData,
          PrefetchHooks Function()
        > {
  $$CachedUserProfileTableTableManager(
    _$AppDatabase db,
    $CachedUserProfileTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedUserProfileTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedUserProfileTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedUserProfileTableAnnotationComposer(
                $db: db,
                $table: table,
              ),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> username = const Value.absent(),
                Value<String> email = const Value.absent(),
                Value<String> role = const Value.absent(),
                Value<String> bio = const Value.absent(),
                Value<String> avatarColor = const Value.absent(),
                Value<String> wcaId = const Value.absent(),
                Value<String> country = const Value.absent(),
                Value<String> mainCube = const Value.absent(),
                Value<String> preferredMethod = const Value.absent(),
                Value<String> pbSingle = const Value.absent(),
                Value<String> pbAo5 = const Value.absent(),
                Value<int> totalSolves = const Value.absent(),
                Value<int> minMoves = const Value.absent(),
                Value<double> avgMoves = const Value.absent(),
                Value<int> coinsBalance = const Value.absent(),
                Value<String> lastSyncedAt = const Value.absent(),
              }) => CachedUserProfileCompanion(
                id: id,
                username: username,
                email: email,
                role: role,
                bio: bio,
                avatarColor: avatarColor,
                wcaId: wcaId,
                country: country,
                mainCube: mainCube,
                preferredMethod: preferredMethod,
                pbSingle: pbSingle,
                pbAo5: pbAo5,
                totalSolves: totalSolves,
                minMoves: minMoves,
                avgMoves: avgMoves,
                coinsBalance: coinsBalance,
                lastSyncedAt: lastSyncedAt,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String username,
                Value<String> email = const Value.absent(),
                Value<String> role = const Value.absent(),
                Value<String> bio = const Value.absent(),
                Value<String> avatarColor = const Value.absent(),
                Value<String> wcaId = const Value.absent(),
                Value<String> country = const Value.absent(),
                Value<String> mainCube = const Value.absent(),
                Value<String> preferredMethod = const Value.absent(),
                Value<String> pbSingle = const Value.absent(),
                Value<String> pbAo5 = const Value.absent(),
                Value<int> totalSolves = const Value.absent(),
                Value<int> minMoves = const Value.absent(),
                Value<double> avgMoves = const Value.absent(),
                Value<int> coinsBalance = const Value.absent(),
                required String lastSyncedAt,
              }) => CachedUserProfileCompanion.insert(
                id: id,
                username: username,
                email: email,
                role: role,
                bio: bio,
                avatarColor: avatarColor,
                wcaId: wcaId,
                country: country,
                mainCube: mainCube,
                preferredMethod: preferredMethod,
                pbSingle: pbSingle,
                pbAo5: pbAo5,
                totalSolves: totalSolves,
                minMoves: minMoves,
                avgMoves: avgMoves,
                coinsBalance: coinsBalance,
                lastSyncedAt: lastSyncedAt,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$CachedUserProfileTable, CachedUserProfileData>(
                    table,
                  ),
                  BaseReferences<
                    _$AppDatabase,
                    $CachedUserProfileTable,
                    CachedUserProfileData
                  >(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CachedUserProfileTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $CachedUserProfileTable,
      CachedUserProfileData,
      $$CachedUserProfileTableFilterComposer,
      $$CachedUserProfileTableOrderingComposer,
      $$CachedUserProfileTableAnnotationComposer,
      $$CachedUserProfileTableCreateCompanionBuilder,
      $$CachedUserProfileTableUpdateCompanionBuilder,
      (
        CachedUserProfileData,
        BaseReferences<
          _$AppDatabase,
          $CachedUserProfileTable,
          CachedUserProfileData
        >,
      ),
      CachedUserProfileData,
      PrefetchHooks Function()
    >;
typedef $$CachedPatternsTableCreateCompanionBuilder =
    CachedPatternsCompanion Function({
      required String id,
      required String name,
      required String moves,
      Value<String> description,
      Value<int> rowid,
    });
typedef $$CachedPatternsTableUpdateCompanionBuilder =
    CachedPatternsCompanion Function({
      Value<String> id,
      Value<String> name,
      Value<String> moves,
      Value<String> description,
      Value<int> rowid,
    });

class $$CachedPatternsTableFilterComposer
    extends Composer<_$AppDatabase, $CachedPatternsTable> {
  $$CachedPatternsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get moves => $composableBuilder(
    column: $table.moves,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get description => $composableBuilder(
    column: $table.description,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CachedPatternsTableOrderingComposer
    extends Composer<_$AppDatabase, $CachedPatternsTable> {
  $$CachedPatternsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get moves => $composableBuilder(
    column: $table.moves,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get description => $composableBuilder(
    column: $table.description,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CachedPatternsTableAnnotationComposer
    extends Composer<_$AppDatabase, $CachedPatternsTable> {
  $$CachedPatternsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<String> get moves =>
      $composableBuilder(column: $table.moves, builder: (column) => column);

  GeneratedColumn<String> get description => $composableBuilder(
    column: $table.description,
    builder: (column) => column,
  );
}

class $$CachedPatternsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $CachedPatternsTable,
          CachedPattern,
          $$CachedPatternsTableFilterComposer,
          $$CachedPatternsTableOrderingComposer,
          $$CachedPatternsTableAnnotationComposer,
          $$CachedPatternsTableCreateCompanionBuilder,
          $$CachedPatternsTableUpdateCompanionBuilder,
          (
            CachedPattern,
            BaseReferences<_$AppDatabase, $CachedPatternsTable, CachedPattern>,
          ),
          CachedPattern,
          PrefetchHooks Function()
        > {
  $$CachedPatternsTableTableManager(
    _$AppDatabase db,
    $CachedPatternsTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedPatternsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedPatternsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedPatternsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<String> name = const Value.absent(),
                Value<String> moves = const Value.absent(),
                Value<String> description = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => CachedPatternsCompanion(
                id: id,
                name: name,
                moves: moves,
                description: description,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                required String name,
                required String moves,
                Value<String> description = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => CachedPatternsCompanion.insert(
                id: id,
                name: name,
                moves: moves,
                description: description,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$CachedPatternsTable, CachedPattern>(table),
                  BaseReferences<
                    _$AppDatabase,
                    $CachedPatternsTable,
                    CachedPattern
                  >(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CachedPatternsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $CachedPatternsTable,
      CachedPattern,
      $$CachedPatternsTableFilterComposer,
      $$CachedPatternsTableOrderingComposer,
      $$CachedPatternsTableAnnotationComposer,
      $$CachedPatternsTableCreateCompanionBuilder,
      $$CachedPatternsTableUpdateCompanionBuilder,
      (
        CachedPattern,
        BaseReferences<_$AppDatabase, $CachedPatternsTable, CachedPattern>,
      ),
      CachedPattern,
      PrefetchHooks Function()
    >;
typedef $$CachedScanResultsTableCreateCompanionBuilder =
    CachedScanResultsCompanion Function({
      Value<int> id,
      required String centerColor,
      required String faceGridJson,
      required String annotatedImageBase64,
      required String scannedAt,
    });
typedef $$CachedScanResultsTableUpdateCompanionBuilder =
    CachedScanResultsCompanion Function({
      Value<int> id,
      Value<String> centerColor,
      Value<String> faceGridJson,
      Value<String> annotatedImageBase64,
      Value<String> scannedAt,
    });

class $$CachedScanResultsTableFilterComposer
    extends Composer<_$AppDatabase, $CachedScanResultsTable> {
  $$CachedScanResultsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get centerColor => $composableBuilder(
    column: $table.centerColor,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get faceGridJson => $composableBuilder(
    column: $table.faceGridJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get annotatedImageBase64 => $composableBuilder(
    column: $table.annotatedImageBase64,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get scannedAt => $composableBuilder(
    column: $table.scannedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CachedScanResultsTableOrderingComposer
    extends Composer<_$AppDatabase, $CachedScanResultsTable> {
  $$CachedScanResultsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get centerColor => $composableBuilder(
    column: $table.centerColor,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get faceGridJson => $composableBuilder(
    column: $table.faceGridJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get annotatedImageBase64 => $composableBuilder(
    column: $table.annotatedImageBase64,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get scannedAt => $composableBuilder(
    column: $table.scannedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CachedScanResultsTableAnnotationComposer
    extends Composer<_$AppDatabase, $CachedScanResultsTable> {
  $$CachedScanResultsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get centerColor => $composableBuilder(
    column: $table.centerColor,
    builder: (column) => column,
  );

  GeneratedColumn<String> get faceGridJson => $composableBuilder(
    column: $table.faceGridJson,
    builder: (column) => column,
  );

  GeneratedColumn<String> get annotatedImageBase64 => $composableBuilder(
    column: $table.annotatedImageBase64,
    builder: (column) => column,
  );

  GeneratedColumn<String> get scannedAt =>
      $composableBuilder(column: $table.scannedAt, builder: (column) => column);
}

class $$CachedScanResultsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $CachedScanResultsTable,
          CachedScanResult,
          $$CachedScanResultsTableFilterComposer,
          $$CachedScanResultsTableOrderingComposer,
          $$CachedScanResultsTableAnnotationComposer,
          $$CachedScanResultsTableCreateCompanionBuilder,
          $$CachedScanResultsTableUpdateCompanionBuilder,
          (
            CachedScanResult,
            BaseReferences<
              _$AppDatabase,
              $CachedScanResultsTable,
              CachedScanResult
            >,
          ),
          CachedScanResult,
          PrefetchHooks Function()
        > {
  $$CachedScanResultsTableTableManager(
    _$AppDatabase db,
    $CachedScanResultsTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedScanResultsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedScanResultsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedScanResultsTableAnnotationComposer(
                $db: db,
                $table: table,
              ),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> centerColor = const Value.absent(),
                Value<String> faceGridJson = const Value.absent(),
                Value<String> annotatedImageBase64 = const Value.absent(),
                Value<String> scannedAt = const Value.absent(),
              }) => CachedScanResultsCompanion(
                id: id,
                centerColor: centerColor,
                faceGridJson: faceGridJson,
                annotatedImageBase64: annotatedImageBase64,
                scannedAt: scannedAt,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String centerColor,
                required String faceGridJson,
                required String annotatedImageBase64,
                required String scannedAt,
              }) => CachedScanResultsCompanion.insert(
                id: id,
                centerColor: centerColor,
                faceGridJson: faceGridJson,
                annotatedImageBase64: annotatedImageBase64,
                scannedAt: scannedAt,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$CachedScanResultsTable, CachedScanResult>(table),
                  BaseReferences<
                    _$AppDatabase,
                    $CachedScanResultsTable,
                    CachedScanResult
                  >(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CachedScanResultsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $CachedScanResultsTable,
      CachedScanResult,
      $$CachedScanResultsTableFilterComposer,
      $$CachedScanResultsTableOrderingComposer,
      $$CachedScanResultsTableAnnotationComposer,
      $$CachedScanResultsTableCreateCompanionBuilder,
      $$CachedScanResultsTableUpdateCompanionBuilder,
      (
        CachedScanResult,
        BaseReferences<
          _$AppDatabase,
          $CachedScanResultsTable,
          CachedScanResult
        >,
      ),
      CachedScanResult,
      PrefetchHooks Function()
    >;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$CachedSolvesTableTableManager get cachedSolves =>
      $$CachedSolvesTableTableManager(_db, _db.cachedSolves);
  $$CachedUserProfileTableTableManager get cachedUserProfile =>
      $$CachedUserProfileTableTableManager(_db, _db.cachedUserProfile);
  $$CachedPatternsTableTableManager get cachedPatterns =>
      $$CachedPatternsTableTableManager(_db, _db.cachedPatterns);
  $$CachedScanResultsTableTableManager get cachedScanResults =>
      $$CachedScanResultsTableTableManager(_db, _db.cachedScanResults);
}
