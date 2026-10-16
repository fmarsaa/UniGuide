import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'screens/splash_screen.dart';
import 'screens/auth_screen.dart';
import 'screens/email_verification_screen.dart';
import 'screens/recommendations_screen.dart';
import 'screens/profile_setup_screen.dart';
import 'screens/admin_dashboard_screen.dart';
import 'screens/programme_detail_screen.dart';
import 'screens/programme_catalog_screen.dart';
import 'screens/shortlist_screen.dart';
import 'screens/feedback_dialog.dart';
import 'models/student_profile.dart';
import 'models/recommendation.dart';
import 'models/programme.dart';
import 'services/api_service.dart';
import 'services/recommendation_cache.dart';
import 'services/shortlist_controller.dart';
import 'theme/app_colors.dart';
import 'theme/theme_controller.dart';

/// Firebase settings for the web admin portal. They are build-time settings
/// (flutter run/build --dart-define-from-file=web_firebase.json) kept out of git,
/// the same way android/app/google-services.json is for the phone app.
const FirebaseOptions _webFirebaseOptions = FirebaseOptions(
  apiKey: String.fromEnvironment('FIREBASE_API_KEY'),
  appId: String.fromEnvironment('FIREBASE_APP_ID'),
  messagingSenderId: String.fromEnvironment('FIREBASE_MESSAGING_SENDER_ID'),
  projectId: String.fromEnvironment('FIREBASE_PROJECT_ID'),
  authDomain: String.fromEnvironment('FIREBASE_AUTH_DOMAIN'),
  storageBucket: String.fromEnvironment('FIREBASE_STORAGE_BUCKET'),
);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // On Android the settings come from google-services.json; on the web build
  // they come from the defines above.
  await Firebase.initializeApp(options: kIsWeb ? _webFirebaseOptions : null);
  runApp(const UniGuideApp());
}

/// Base light theme: teal-seeded Material 3 colour scheme on a light
/// slate background, matching the app's original brand palette.
ThemeData _buildLightTheme() {
  return ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    primaryColor: const Color(0xFF14213D),
    scaffoldBackgroundColor: const Color(0xFFF1F5F9),
    colorScheme: ColorScheme.fromSeed(
      seedColor: const Color(0xFF0EA5A4),
      brightness: Brightness.light,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: Colors.white,
      indicatorColor: const Color(0xFF0EA5A4).withValues(alpha: 0.18),
      surfaceTintColor: Colors.transparent,
    ),
  );
}

/// Dark counterpart of [_buildLightTheme]: navy surfaces, blue-grey secondary
/// text and a warm tan accent, set in Inter. Colours were matched by eye from
/// a small reference crop, so tweak [_darkAccent] / the font here if needed.
const Color _darkAccent = Color(0xFFD9A066);

ThemeData _buildDarkTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: const Color(0xFF0EA5A4),
    brightness: Brightness.dark,
  ).copyWith(
    primary: _darkAccent,
    onPrimary: const Color(0xFF1B1204),
  );
  return ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    primaryColor: const Color(0xFF14213D),
    scaffoldBackgroundColor: const Color(0xFF0F172A),
    colorScheme: scheme,
    textTheme: GoogleFonts.interTextTheme(ThemeData(brightness: Brightness.dark).textTheme),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: const Color(0xFF1E293B),
      indicatorColor: _darkAccent.withValues(alpha: 0.28),
      surfaceTintColor: Colors.transparent,
    ),
  );
}

class UniGuideApp extends StatelessWidget {
  const UniGuideApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<ThemeController>(create: (_) => ThemeController()..load()),
        ChangeNotifierProvider<ShortlistController>(create: (_) => ShortlistController()),
      ],
      child: Consumer<ThemeController>(
        builder: (context, themeController, _) {
          return MaterialApp(
            title: 'UniGuide',
            debugShowCheckedModeBanner: false,
            theme: _buildLightTheme(),
            darkTheme: _buildDarkTheme(),
            themeMode: themeController.mode,
            home: const AuthGate(),
          );
        },
      ),
    );
  }
}

/// Shows the splash screen briefly, then reacts to real Firebase auth state:
/// signed out -> AuthScreen, signed in -> resolves role via the backend
/// (/api/auth/whoami) before entering the student or admin experience.
class AuthGate extends StatefulWidget {
  const AuthGate({Key? key}) : super(key: key);

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  bool _showSplash = true;

  // authStateChanges() snapshots don't auto-refresh when a user clicks the
  // verification link elsewhere; EmailVerificationScreen confirms this via
  // user.reload() and reports back here so we don't force a re-login.
  bool _emailVerifiedOverride = false;

  @override
  Widget build(BuildContext context) {
    if (_showSplash) {
      return SplashScreen(onSplashComplete: () => setState(() => _showSplash = false));
    }

    return StreamBuilder<User?>(
      stream: FirebaseAuth.instance.authStateChanges(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const _LoadingScaffold(message: 'Connecting...');
        }
        final user = snapshot.data;
        if (user == null) {
          if (_emailVerifiedOverride) {
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (mounted) setState(() => _emailVerifiedOverride = false);
            });
          }
          return const AuthScreen();
        }

        if (!user.emailVerified && !_emailVerifiedOverride) {
          return EmailVerificationScreen(
            key: ValueKey(user.uid),
            user: user,
            onVerified: () => setState(() => _emailVerifiedOverride = true),
            onSignOut: () => FirebaseAuth.instance.signOut(),
          );
        }

        return RoleResolver(key: ValueKey(user.uid), user: user);
      },
    );
  }
}

/// Calls /api/auth/whoami once per signed-in user to determine whether they
/// are a student or administrator, and loads any saved profile.
class RoleResolver extends StatefulWidget {
  final User user;

  const RoleResolver({Key? key, required this.user}) : super(key: key);

  @override
  State<RoleResolver> createState() => _RoleResolverState();
}

class _RoleResolverState extends State<RoleResolver> {
  late Future<Map<String, dynamic>> _whoamiFuture;

  @override
  void initState() {
    super.initState();
    _whoamiFuture = ApiService.whoami();
  }

  void _retry() {
    setState(() => _whoamiFuture = ApiService.whoami());
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: _whoamiFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const _LoadingScaffold(message: 'Loading your account...');
        }
        if (snapshot.hasError) {
          return _ErrorScaffold(
            message: snapshot.error.toString(),
            onRetry: _retry,
            onSignOut: () => FirebaseAuth.instance.signOut(),
          );
        }

        final data = snapshot.data!;
        final role = data['role'] as String? ?? 'student';
        final profileJson = data['profile'] as Map<String, dynamic>?;

        if (role == 'administrator') {
          return AdminHome(onLogout: () => FirebaseAuth.instance.signOut());
        }

        // The web build is the administrators' portal; students use the phone app.
        if (kIsWeb) {
          return _AdminPortalOnlyScaffold(onSignOut: () => FirebaseAuth.instance.signOut());
        }

        final initialProfile = profileJson != null
            ? StudentProfile.fromJson(profileJson)
            : StudentProfile(uid: widget.user.uid, fullName: widget.user.email ?? 'Candidate');

        return StudentHome(
          key: ValueKey(widget.user.uid),
          initialProfile: initialProfile,
          onLogout: () => FirebaseAuth.instance.signOut(),
        );
      },
    );
  }
}

class AdminHome extends StatefulWidget {
  final VoidCallback onLogout;

  const AdminHome({Key? key, required this.onLogout}) : super(key: key);

  @override
  State<AdminHome> createState() => _AdminHomeState();
}

class _AdminHomeState extends State<AdminHome> {
  List<Programme>? _programmes;

  @override
  void initState() {
    super.initState();
    _loadProgrammes();
  }

  Future<void> _loadProgrammes() async {
    try {
      final live = await ApiService.fetchProgrammes();
      if (mounted) setState(() => _programmes = live);
    } on ApiException {
      // AdminDashboardScreen falls back to the bundled catalog on its own
      // when `programmes` is left null.
    }
  }

  @override
  Widget build(BuildContext context) {
    final dashboard = _buildDashboard();
    if (!kIsWeb) return dashboard;
    // Centre the phone-sized dashboard in a readable column on a wide browser window.
    return Container(
      color: AppColors.scaffoldBackground(context),
      alignment: Alignment.topCenter,
      child: ConstrainedBox(constraints: const BoxConstraints(maxWidth: 960), child: dashboard),
    );
  }

  Widget _buildDashboard() {
    return AdminDashboardScreen(
      key: ValueKey(_programmes?.length ?? 0),
      programmes: _programmes,
      onLogout: widget.onLogout,
      // Exceptions are left to propagate: AdminDashboardScreen awaits this call
      // and shows its own success/failure feedback from its own Scaffold context.
      onUpdateProgramme: (id, {averageCutoff, minMeanGrade, description}) async {
        await ApiService.updateProgramme(
          id,
          averageCutoff: averageCutoff,
          minMeanGrade: minMeanGrade,
          description: description,
        );
      },
    );
  }
}

class StudentHome extends StatefulWidget {
  final StudentProfile initialProfile;
  final VoidCallback onLogout;

  const StudentHome({Key? key, required this.initialProfile, required this.onLogout}) : super(key: key);

  @override
  State<StudentHome> createState() => _StudentHomeState();
}

class _StudentHomeState extends State<StudentHome> {
  int _currentTabIndex = 0;
  late StudentProfile _currentProfile;
  List<RecommendationItem> _recommendations = [];
  bool _isLoadingRecommendations = false;
  String? _loadError;
  bool _hasRequestedRecommendations = false;
  bool _isShowingCachedRecommendations = false;
  DateTime? _cachedRecommendationsAt;

  @override
  void initState() {
    super.initState();
    _currentProfile = widget.initialProfile;
    // Start on Profile Setup: recommendations only make sense once the
    // student has actually submitted their academic and career profile.
    _currentTabIndex = _currentProfile.grades.isEmpty ? 1 : 0;
    if (_currentTabIndex == 0) {
      _loadRecommendations();
    }
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) context.read<ShortlistController>().load();
    });
  }

  Future<void> _loadRecommendations() async {
    setState(() {
      _isLoadingRecommendations = true;
      _loadError = null;
      _hasRequestedRecommendations = true;
      _isShowingCachedRecommendations = false;
    });
    try {
      final recs = await ApiService.getRecommendations(_currentProfile);
      setState(() {
        _recommendations = recs;
        _isLoadingRecommendations = false;
      });
      RecommendationCache.save(recs);
    } on ApiException catch (e) {
      // A real server response (bad request, not qualified, etc.) should
      // still surface as an error, not be silently swapped for a stale
      // cached result - only fall back to the cache when ApiService has
      // already exhausted its own retries for a connectivity-type failure
      // (see ApiException.statusCode being null for those, same signal
      // ApiService._errorFor vs its catch-all distinguishes).
      final isConnectivityFailure = e.statusCode == null;
      final cached = isConnectivityFailure ? await RecommendationCache.load() : null;
      if (cached != null) {
        setState(() {
          _recommendations = cached.$1;
          _cachedRecommendationsAt = cached.$2;
          _isShowingCachedRecommendations = true;
          _isLoadingRecommendations = false;
        });
      } else {
        setState(() {
          _loadError = e.message;
          _isLoadingRecommendations = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final themeController = context.watch<ThemeController>();
    final isDark = themeController.mode == ThemeMode.dark ||
        (themeController.mode == ThemeMode.system &&
            MediaQuery.platformBrightnessOf(context) == Brightness.dark);

    final List<Widget> studentPages = [
      _buildRecommendationsTab(),
      ProfileSetupScreen(
        initialProfile: _currentProfile,
        onGenerateRecommendations: (updated) {
          setState(() {
            _currentProfile = updated;
            _currentTabIndex = 0;
          });
          _loadRecommendations();
        },
      ),
      const ProgrammeCatalogScreen(),
      const ShortlistScreen(),
    ];

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: const [
            Icon(Icons.school, size: 22, color: Color(0xFF0EA5A4)),
            SizedBox(width: 8),
            Text('UniGuide', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white)),
          ],
        ),
        backgroundColor: const Color(0xFF14213D),
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(isDark ? Icons.light_mode_outlined : Icons.dark_mode_outlined, size: 20),
            tooltip: isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode',
            onPressed: () => context.read<ThemeController>().toggle(),
          ),
          IconButton(
            icon: const Icon(Icons.logout, size: 20),
            tooltip: 'Sign Out',
            onPressed: widget.onLogout,
          ),
        ],
      ),
      body: studentPages[_currentTabIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentTabIndex,
        onDestinationSelected: (index) {
          setState(() => _currentTabIndex = index);
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.auto_awesome_outlined),
            selectedIcon: Icon(Icons.auto_awesome, color: Color(0xFF0EA5A4)),
            label: 'Top 3 Matches',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person, color: Color(0xFF0EA5A4)),
            label: 'Profile Setup',
          ),
          NavigationDestination(
            icon: Icon(Icons.menu_book_outlined),
            selectedIcon: Icon(Icons.menu_book, color: Color(0xFF0EA5A4)),
            label: 'Programmes',
          ),
          NavigationDestination(
            icon: Icon(Icons.bookmark_border),
            selectedIcon: Icon(Icons.bookmark, color: Color(0xFF0EA5A4)),
            label: 'Saved',
          ),
        ],
      ),
    );
  }

  Widget _buildRecommendationsTab() {
    if (_isLoadingRecommendations) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF0EA5A4))),
        ),
      );
    }

    if (_loadError != null) {
      return Scaffold(
        backgroundColor: AppColors.scaffoldBackground(context),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.cloud_off, size: 48, color: Colors.redAccent),
                const SizedBox(height: 12),
                Text(
                  'Could not load recommendations',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppColors.textPrimary(context)),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 6),
                Text(
                  _loadError!,
                  style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: _loadRecommendations,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Retry'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0EA5A4),
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    if (!_hasRequestedRecommendations || _recommendations.isEmpty) {
      return Scaffold(
        backgroundColor: AppColors.scaffoldBackground(context),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.auto_awesome_outlined, size: 48, color: Color(0xFF0EA5A4)),
                const SizedBox(height: 12),
                Text(
                  'Complete your profile to get recommendations',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppColors.textPrimary(context)),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: () => setState(() => _currentTabIndex = 1),
                  icon: const Icon(Icons.tune),
                  label: const Text('Go to Profile Setup'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0EA5A4),
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return RecommendationsScreen(
      recommendations: _recommendations,
      studentPrimaryInterest: _currentProfile.interests.isNotEmpty ? _currentProfile.interests.first : null,
      cachedAt: _isShowingCachedRecommendations ? _cachedRecommendationsAt : null,
      onRefresh: _loadRecommendations,
      onSelectProgramme: (prog) {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => ProgrammeDetailScreen(programme: prog)),
        );
      },
      onOpenFeedback: (rec) {
        showDialog(
          context: context,
          builder: (_) => FeedbackDialog(
            recommendation: rec,
            onFeedbackSubmitted: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Feedback saved successfully')),
              );
            },
          ),
        );
      },
      onAdjustProfile: () {
        setState(() => _currentTabIndex = 1);
      },
    );
  }
}

class _AdminPortalOnlyScaffold extends StatelessWidget {
  final VoidCallback onSignOut;

  const _AdminPortalOnlyScaffold({required this.onSignOut});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground(context),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.phone_android, size: 48, color: Color(0xFF0EA5A4)),
                const SizedBox(height: 12),
                Text(
                  'This portal is for administrators',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.textPrimary(context)),
                ),
                const SizedBox(height: 6),
                Text(
                  'Students: please use the UniGuide mobile app to get your recommendations.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 13, color: AppColors.textSecondary(context), height: 1.4),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: onSignOut,
                  style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF0EA5A4), foregroundColor: Colors.white),
                  child: const Text('Sign out'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _LoadingScaffold extends StatelessWidget {
  final String message;

  const _LoadingScaffold({required this.message});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground(context),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF0EA5A4))),
            const SizedBox(height: 16),
            Text(message, style: TextStyle(color: AppColors.textSecondary(context), fontSize: 13)),
          ],
        ),
      ),
    );
  }
}

class _ErrorScaffold extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  final VoidCallback onSignOut;

  const _ErrorScaffold({required this.message, required this.onRetry, required this.onSignOut});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground(context),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.cloud_off, size: 48, color: Colors.redAccent),
              const SizedBox(height: 12),
              Text(
                'Could not reach the UniGuide server',
                style: TextStyle(color: AppColors.textPrimary(context), fontWeight: FontWeight.bold, fontSize: 15),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 6),
              Text(message, style: TextStyle(color: AppColors.textSecondary(context), fontSize: 12), textAlign: TextAlign.center),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF0EA5A4), foregroundColor: Colors.white),
              ),
              const SizedBox(height: 8),
              TextButton(
                onPressed: onSignOut,
                child: Text('Sign Out', style: TextStyle(color: AppColors.textSecondary(context))),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
