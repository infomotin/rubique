import 'dart:io';
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;

part 'app_database.g.dart';

class CachedSolves extends Table {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get remoteId => integer().nullable()();
  TextColumn get scramble => text()();
  TextColumn get solution => text()();
  IntColumn get moveCount => integer()();
  TextColumn get createdAt => text()();
}

class CachedUserProfile extends Table {
  IntColumn get id => integer()(); // fixed 1
  TextColumn get username => text()();
  TextColumn get email => text().withDefault(const Constant(''))();
  TextColumn get role => text().withDefault(const Constant('user'))();
  TextColumn get bio => text().withDefault(const Constant(''))();
  TextColumn get avatarColor => text().withDefault(const Constant('#818cf8'))();
  TextColumn get wcaId => text().withDefault(const Constant(''))();
  TextColumn get country => text().withDefault(const Constant(''))();
  TextColumn get mainCube => text().withDefault(const Constant('GAN 12 MagLev 3x3'))();
  TextColumn get preferredMethod => text().withDefault(const Constant('CFOP'))();
  TextColumn get pbSingle => text().withDefault(const Constant(''))();
  TextColumn get pbAo5 => text().withDefault(const Constant(''))();
  IntColumn get totalSolves => integer().withDefault(const Constant(0))();
  IntColumn get minMoves => integer().withDefault(const Constant(0))();
  RealColumn get avgMoves => real().withDefault(const Constant(0.0))();
  IntColumn get coinsBalance => integer().withDefault(const Constant(1000))();
  TextColumn get lastSyncedAt => text()();

  @override
  Set<Column> get primaryKey => {id};
}

class CachedPatterns extends Table {
  TextColumn get id => text()();
  TextColumn get name => text()();
  TextColumn get moves => text()();
  TextColumn get description => text().withDefault(const Constant(''))();

  @override
  Set<Column> get primaryKey => {id};
}

class CachedScanResults extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get centerColor => text()();
  TextColumn get faceGridJson => text()();
  TextColumn get annotatedImageBase64 => text()();
  TextColumn get scannedAt => text()();
}

@DriftDatabase(tables: [CachedSolves, CachedUserProfile, CachedPatterns, CachedScanResults])
class AppDatabase extends _$AppDatabase {
  AppDatabase([QueryExecutor? e]) : super(e ?? _openConnection());

  @override
  int get schemaVersion => 1;

  // Helper methods for offline cache management

  Future<void> cacheSolves(List<CachedSolvesCompanion> solves) async {
    await batch((b) {
      b.deleteAll(cachedSolves);
      b.insertAll(cachedSolves, solves);
    });
  }

  Future<List<CachedSolve>> getOfflineSolves() {
    return (select(cachedSolves)..orderBy([(t) => OrderingTerm.desc(t.id)])).get();
  }

  Future<void> cacheProfile(CachedUserProfileCompanion profile) async {
    await into(cachedUserProfile).insertOnConflictUpdate(profile);
  }

  Future<CachedUserProfileData?> getOfflineProfile() {
    return (select(cachedUserProfile)..where((t) => t.id.equals(1))).getSingleOrNull();
  }

  Future<void> cachePatternsList(List<CachedPatternsCompanion> patterns) async {
    await batch((b) {
      b.deleteAll(cachedPatterns);
      b.insertAll(cachedPatterns, patterns);
    });
  }

  Future<List<CachedPattern>> getOfflinePatterns() {
    return select(cachedPatterns).get();
  }

  Future<int> cacheScanResult(CachedScanResultsCompanion scan) {
    return into(cachedScanResults).insert(scan);
  }

  Future<List<CachedScanResult>> getOfflineScanResults() {
    return (select(cachedScanResults)..orderBy([(t) => OrderingTerm.desc(t.id)])).get();
  }

  Future<void> clearAllCache() async {
    await delete(cachedSolves).go();
    await delete(cachedUserProfile).go();
    await delete(cachedPatterns).go();
    await delete(cachedScanResults).go();
  }
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final dbFolder = await getApplicationDocumentsDirectory();
    final file = File(p.join(dbFolder.path, 'cube_offline_cache.sqlite'));
    return NativeDatabase.createInBackground(file);
  });
}
