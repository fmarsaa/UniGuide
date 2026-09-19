import 'package:flutter/material.dart';
import 'screens/splash_screen.dart';
import 'screens/auth_screen.dart';
import 'screens/recommendations_screen.dart';
import 'screens/profile_setup_screen.dart';
import 'screens/admin_dashboard_screen.dart';
import 'screens/programme_detail_screen.dart';
import 'screens/programme_catalog_screen.dart';
import 'screens/feedback_dialog.dart';
import 'models/student_profile.dart';
import 'models/recommendation.dart';
import 'models/programme.dart';
import 'services/api_service.dart';
import 'data/programme_repository.dart';

void main() {
  runApp(const UniGuideApp());
}

class UniGuideApp extends StatelessWidget {
  const UniGuideApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'UniGuide',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        primaryColor: const Color(0xFF14213D),
        scaffoldBackgroundColor: const Color(0xFFF8FAFC),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF0EA5A4),
          primary: const Color(0xFF14213D),
          secondary: const Color(0xFF0EA5A4),
        ),
      ),
      home: const MainMobileNavigation(),
    );
  }
}

class MainMobileNavigation extends StatefulWidget {
  const MainMobileNavigation({Key? key}) : super(key: key);

  @override
  State<MainMobileNavigation> createState() => _MainMobileNavigationState();
}

class _MainMobileNavigationState extends State<MainMobileNavigation> {
  bool _showSplash = true;
  bool _isAuthenticated = false;
  String _userRole = 'student'; // 'student' or 'administrator'
  int _currentTabIndex = 0;

  late StudentProfile _currentProfile;
  List<RecommendationItem> _recommendations = [];
  bool _isLoadingRecommendations = false;

  @override
  void initState() {
    super.initState();
    // Professional initial candidate profile
    _currentProfile = StudentProfile(
      id: 'cand_2025_01',
      fullName: 'Form-Four Candidate',
      indexNumber: '12345678/2025',
      kcseMeanGrade: 'A-',
      grades: {
        'Mathematics': 'A',
        'English': 'A-',
        'Kiswahili': 'B+',
        'Biology': 'A-',
        'Chemistry': 'B+',
        'Physics': 'B+',
      },
      interests: [
        'Healthcare & Clinical Medicine',
        'Pharmaceutical Sciences',
      ],
      skills: [
        'Clinical Diagnostics & Health Care',
        'Scientific Laboratory Research',
        'Problem Solving & Analytical Logic',
      ],
      strengths: [
        'Empathy & Human Care',
        'Attention to Precision',
      ],
      aspirations: [
        'Medical Doctor (Physician/Surgeon)',
        'Pharmacist',
      ],
    );

    _loadRecommendations();
  }

  Future<void> _loadRecommendations() async {
    setState(() => _isLoadingRecommendations = true);
    final recs = await ApiService.getRecommendations(_currentProfile);
    setState(() {
      _recommendations = recs;
      _isLoadingRecommendations = false;
    });
  }

  void _handleLogout() {
    setState(() {
      _isAuthenticated = false;
      _userRole = 'student';
      _currentTabIndex = 0;
    });
  }

  @override
  Widget build(BuildContext context) {
    // 1. Initial Splash Screen
    if (_showSplash) {
      return SplashScreen(
        onSplashComplete: () {
          setState(() {
            _showSplash = false;
          });
        },
      );
    }

    // 2. Authentication Screen (starts logged out)
    if (!_isAuthenticated) {
      return AuthScreen(
        onLoginSuccess: (role) {
          setState(() {
            _userRole = role;
            _isAuthenticated = true;
            _currentTabIndex = 0;
          });
        },
      );
    }

    // 3. Administrator Portal (Direct full screen view for admin)
    if (_userRole == 'administrator') {
      return AdminDashboardScreen(
        programmes: ProgrammeRepository.allProgrammes,
        onLogout: _handleLogout,
        onUpdateCutoff: (id, newCutoff) {
          setState(() {
            final prog = ProgrammeRepository.findById(id);
            if (prog != null) {
              // Cutoff updated in repository
            }
          });
        },
      );
    }

    // 4. Student Decision Support View
    final List<Widget> studentPages = [
      // Tab 0: Top 3 Recommendations
      _isLoadingRecommendations
          ? const Scaffold(
              body: Center(
                child: CircularProgressIndicator(
                  valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF0EA5A4)),
                ),
              ),
            )
          : RecommendationsScreen(
              recommendations: _recommendations,
              onSelectProgramme: (prog) {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => ProgrammeDetailScreen(programme: prog),
                  ),
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
            ),

      // Tab 1: Profile Setup
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

      // Tab 2: Programme Directory
      const ProgrammeCatalogScreen(),
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
            icon: const Icon(Icons.logout, size: 20),
            tooltip: 'Sign Out',
            onPressed: _handleLogout,
          ),
        ],
      ),
      body: studentPages[_currentTabIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentTabIndex,
        backgroundColor: Colors.white,
        indicatorColor: const Color(0xFF0EA5A4).withOpacity(0.18),
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
        ],
      ),
    );
  }
}
