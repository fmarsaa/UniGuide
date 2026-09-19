import React, { useState, useEffect } from 'react';
import { MobileDeviceFrame } from './components/MobileDeviceFrame';
import { MobileAppBar } from './components/MobileAppBar';
import { MobileBottomNav, MobileTabType } from './components/MobileBottomNav';
import { HomeScreen } from './components/HomeScreen';
import { ProfileScreen } from './components/ProfileScreen';
import { RecommendationScreen } from './components/RecommendationScreen';
import { SavedProgrammesScreen } from './components/SavedProgrammesScreen';
import { FeedbackScreen } from './components/FeedbackScreen';
import { DirectoryScreen } from './components/DirectoryScreen';
import { AdminDashboardScreen } from './components/AdminDashboardScreen';
import { AuthScreen } from './components/AuthScreen';
import { ShapExplanationModal } from './components/ShapExplanationModal';
import { ProgrammeDetailsModal } from './components/ProgrammeDetailsModal';
import { FlutterProposalModal } from './components/FlutterProposalModal';

import {
  StudentProfile,
  RecommendationResult,
  ProgrammeInfo,
  FeedbackEntry,
  UserRole,
  AdminAuditLog,
} from './types';
import { DEFAULT_PROGRAMMES } from './data/programmes';
import { runRecommendationEngine } from './services/recommendationEngine';
import { db } from './services/database';

const SAMPLE_PROFILE: StudentProfile = {
  uid: 'user_candidate',
  fullName: 'Candidate Profile',
  indexNumber: '12345678/2025',
  kcseMeanGrade: 'A-',
  kcseMeanPoints: 11,
  calculatedClusterScore: 41.8,
  grades: {
    'English': 'A-',
    'Mathematics': 'A',
    'Physics': 'A-',
    'Chemistry': 'B+',
    'Biology': 'B',
    'Computer Studies': 'A',
    'Business Studies': 'A',
    'Geography': 'B+',
    'History': 'B',
    'CRE': 'A',
  },
  interests: ['Healthcare & Clinical Medicine', 'Pharmaceutical Sciences'],
  skills: ['Clinical Diagnostics & Health Care', 'Scientific Laboratory Research', 'Problem Solving & Analytical Logic'],
  strengths: ['Empathy & Human Care', 'Attention to Precision'],
  aspirations: ['Medical Doctor (Physician/Surgeon)', 'Pharmacist'],
  updatedAt: new Date().toISOString(),
};

const INITIAL_AUDIT_LOGS: AdminAuditLog[] = [
  {
    id: 'log_01',
    timestamp: 'Today, 08:30 AM',
    action: 'recommendation_run',
    actorName: 'Candidate Inference Cycle',
    studentIndex: '12345678/2025',
    details: 'Generated Top 3 recommendations using Random Forest Model (Mean: A-)',
  },
  {
    id: 'log_02',
    timestamp: 'Yesterday, 04:15 PM',
    action: 'cutoff_adjusted',
    actorName: 'Dean of Admissions',
    details: 'Updated KUCCPS cutoff points for Medicine & Surgery to 43.5',
  },
  {
    id: 'log_03',
    timestamp: 'Yesterday, 11:20 AM',
    action: 'programme_update',
    actorName: 'Academic Registrar',
    details: 'Verified 2025/2026 KUCCPS cluster capacities across faculties',
  },
];

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<MobileTabType>('home');
  const [userRole, setUserRole] = useState<UserRole>(() => {
    const savedRole = localStorage.getItem('uniguide_role');
    return (savedRole as UserRole) || 'student';
  });

  // Authentication & Onboarding state: Starts unauthenticated on fresh session so the Splash & Auth flow is prominent
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return sessionStorage.getItem('uniguide_auth') === 'true';
  });
  const [isOnboarding, setIsOnboarding] = useState<boolean>(false);

  // Program catalog with custom cutoff adjustments supported
  const [programmes, setProgrammes] = useState<ProgrammeInfo[]>(() => {
    const saved = localStorage.getItem('uniguide_programmes');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          // Always synchronize latest rich university listings while preserving admin customized cutoffs
          const updated = DEFAULT_PROGRAMMES.map((defProg) => {
            const existing = parsed.find((p: ProgrammeInfo) => p.id === defProg.id);
            if (!existing) return defProg;
            return {
              ...defProg,
              universities: defProg.universities.map((u) => {
                const customUni = existing.universities?.find((cu: any) => cu.name === u.name);
                return customUni ? { ...u, lastCutoffPoints: customUni.lastCutoffPoints } : u;
              }),
            };
          });
          localStorage.setItem('uniguide_programmes', JSON.stringify(updated));
          return updated;
        }
      } catch (e) {
        /* ignore */
      }
    }
    return DEFAULT_PROGRAMMES;
  });

  // Stored state with local storage support
  const [profile, setProfile] = useState<StudentProfile | null>(() => {
    const saved = localStorage.getItem('uniguide_profile');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        /* ignore */
      }
    }
    return SAMPLE_PROFILE;
  });

  const [savedIds, setSavedIds] = useState<string[]>(() => {
    const saved = localStorage.getItem('uniguide_saved');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        /* ignore */
      }
    }
    return ['prog_01', 'prog_02'];
  });

  const [feedbacks, setFeedbacks] = useState<FeedbackEntry[]>(() => {
    const saved = localStorage.getItem('uniguide_feedbacks');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        /* ignore */
      }
    }
    return [
      {
        id: 'fb_1',
        uid: 'user_demo',
        programmeId: 'prog_01',
        programmeName: 'Bachelor of Science in Informatics and Computer Science',
        rating: 5,
        satisfactionScore: 10,
        plannedProgramme: 'BSc Informatics and Computer Science',
        comments: 'The SHAP explanation clearly proved how my Math and Computer Studies scores pushed the recommendation.',
        timestamp: 'Today, 09:15 AM',
      },
    ];
  });

  const [auditLogs, setAuditLogs] = useState<AdminAuditLog[]>(() => {
    const saved = localStorage.getItem('uniguide_audit_logs');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        /* ignore */
      }
    }
    return INITIAL_AUDIT_LOGS;
  });

  const [recommendations, setRecommendations] = useState<RecommendationResult[]>([]);
  const [selectedShapResult, setSelectedShapResult] = useState<RecommendationResult | null>(null);
  const [selectedProgramme, setSelectedProgramme] = useState<ProgrammeInfo | null>(null);
  const [feedbackProgrammeId, setFeedbackProgrammeId] = useState<string | undefined>(undefined);
  const [showFlutterModal, setShowFlutterModal] = useState<boolean>(false);

  // Sync role
  useEffect(() => {
    localStorage.setItem('uniguide_role', userRole);
  }, [userRole]);

  // Sync programmes
  useEffect(() => {
    localStorage.setItem('uniguide_programmes', JSON.stringify(programmes));
  }, [programmes]);

  // Sync profile & recalculate recommendations
  useEffect(() => {
    if (profile) {
      localStorage.setItem('uniguide_profile', JSON.stringify(profile));
      const results = runRecommendationEngine(profile, programmes);
      setRecommendations(results);
      if (results && results.length > 0 && profile.uid) {
        db.saveRecommendations(profile.uid, results);
      }
    }
  }, [profile, programmes]);

  // Sync saved IDs
  useEffect(() => {
    localStorage.setItem('uniguide_saved', JSON.stringify(savedIds));
  }, [savedIds]);

  // Sync feedbacks
  useEffect(() => {
    localStorage.setItem('uniguide_feedbacks', JSON.stringify(feedbacks));
  }, [feedbacks]);

  // Sync audit logs
  useEffect(() => {
    localStorage.setItem('uniguide_audit_logs', JSON.stringify(auditLogs));
  }, [auditLogs]);

  const handleToggleSave = (id: string) => {
    setSavedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleSaveProfile = (newProfile: StudentProfile) => {
    setProfile(newProfile);
    setIsOnboarding(false);
    db.updateStudentProfile(newProfile.uid, newProfile);

    // Append to audit trail
    const newLog: AdminAuditLog = {
      id: 'log_' + Date.now(),
      timestamp: 'Just now',
      action: 'recommendation_run',
      actorName: newProfile.fullName,
      studentIndex: newProfile.indexNumber,
      details: `Calculated Top 3 degrees for Mean Grade ${newProfile.kcseMeanGrade} (${newProfile.calculatedClusterScore || 40} cluster pts)`,
    };
    setAuditLogs((prev) => [newLog, ...prev]);
    db.saveAuditLog(newLog);

    setActiveTab('recommendations');
  };

  const handleLoadSample = () => {
    setProfile(SAMPLE_PROFILE);
  };

  const handleSubmitFeedback = (entry: Omit<FeedbackEntry, 'id' | 'timestamp'>) => {
    const newEntry: FeedbackEntry = {
      ...entry,
      id: 'fb_' + Date.now(),
      timestamp: 'Just now',
    };
    setFeedbacks((prev) => [newEntry, ...prev]);
    db.saveFeedback(newEntry);
  };

  const handleUpdateCutoff = (progId: string, newCutoff: number) => {
    setProgrammes((prev) =>
      prev.map((p) => {
        if (p.id === progId) {
          const updatedUnis = p.universities.map((u, i) =>
            i === 0 ? { ...u, lastCutoffPoints: newCutoff } : u
          );
          return { ...p, universities: updatedUnis };
        }
        return p;
      })
    );

    const updatedProg = programmes.find((p) => p.id === progId);
    const newLog: AdminAuditLog = {
      id: 'log_' + Date.now(),
      timestamp: 'Just now',
      action: 'cutoff_adjusted',
      actorName: 'Academic Registrar (Admin)',
      details: `Modified cutoff for ${updatedProg?.name || progId} to ${newCutoff.toFixed(1)} pts`,
    };
    setAuditLogs((prev) => [newLog, ...prev]);
    db.saveAuditLog(newLog);
  };

  const handleSwitchRole = (newRole: UserRole) => {
    setUserRole(newRole);
    if (newRole === 'admin') {
      setActiveTab('admin');
    } else {
      setActiveTab('home');
    }
  };

  const handleSignUpSuccess = (studentData: { fullName: string; indexNumber: string; email: string }) => {
    setIsAuthenticated(true);
    sessionStorage.setItem('uniguide_auth', 'true');
    setUserRole('student');
    setIsOnboarding(true);

    // Initialize fresh student profile with entered identity
    const newProfile: StudentProfile = {
      uid: 'student_' + Date.now(),
      fullName: studentData.fullName,
      indexNumber: studentData.indexNumber,
      kcseMeanGrade: 'B+',
      kcseMeanPoints: 10,
      grades: {
        'English': 'B+',
        'Mathematics': 'A-',
        'Physics': 'B',
        'Chemistry': 'B',
        'Biology': 'B',
        'Computer Studies': 'A',
      },
      interests: ['Software Development', 'Artificial Intelligence'],
      skills: ['Problem Solving', 'Python Coding'],
      strengths: ['Critical Thinking'],
      aspirations: ['Software Engineer'],
      calculatedClusterScore: 38.5,
      updatedAt: new Date().toISOString(),
    };

    setProfile(newProfile);
    // Student requirement: "as a student I need to sign up and input my info."
    setActiveTab('profile');
  };

  const handleLoginSuccess = (role: UserRole, studentData?: Partial<StudentProfile>) => {
    setIsAuthenticated(true);
    sessionStorage.setItem('uniguide_auth', 'true');
    setUserRole(role);
    setIsOnboarding(false);

    if (role === 'admin') {
      setActiveTab('admin');
    } else {
      if (studentData) {
        setProfile((prev) => ({
          ...(prev || SAMPLE_PROFILE),
          ...studentData,
        }));
      }
      setActiveTab('home');
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    sessionStorage.removeItem('uniguide_auth');
    setIsOnboarding(false);
    setActiveTab('home');
  };

  const savedProgrammesList = programmes.filter((p) => savedIds.includes(p.id));

  // Determine App Bar Title & Subtitle based on active tab
  const getScreenMeta = () => {
    if (!isAuthenticated) {
      return { title: 'UniGuide', subtitle: 'Decision Support System' };
    }
    switch (activeTab) {
      case 'home':
        if (userRole === 'admin') {
          return { title: 'Admin Console', subtitle: 'Admissions & Management' };
        }
        return { title: 'UniGuide', subtitle: 'Decision Support System' };
      case 'profile':
        return { 
          title: isOnboarding ? 'Input KCSE Info' : 'Academic Profile', 
          subtitle: isOnboarding ? 'Step 2: Enter Grades & Interests' : 'KCSE Mean & Subject Grades' 
        };
      case 'recommendations':
        return { title: 'Top 3 AI Recommendations', subtitle: 'Random Forest Inference' };
      case 'directory':
        return { title: 'Degree Courses', subtitle: 'KUCCPS Accredited Catalog' };
      case 'saved':
        return { title: 'Saved Shortlist', subtitle: `${savedIds.length} Programmes Bookmarked` };
      case 'feedback':
        return { title: 'Recommendation Feedback', subtitle: 'Model Accuracy Evaluation' };
      case 'admin':
        return { title: 'Admin Console', subtitle: 'Programmes & Audit Management' };
      case 'auth':
        return { title: 'UniGuide Portal', subtitle: 'Sign In & Role Verification' };
      default:
        return { title: 'UniGuide', subtitle: 'Mobile Decision Support' };
    }
  };

  const meta = getScreenMeta();
  const isSubPage = isAuthenticated && (userRole === 'admin' ? activeTab !== 'admin' && activeTab !== 'home' : activeTab !== 'home');

  return (
    <MobileDeviceFrame
      activeScreenTitle={meta.title}
      onOpenFlutterArchitecture={() => setShowFlutterModal(true)}
    >
      {/* Mobile Top App Bar */}
      <MobileAppBar
        title={meta.title}
        subtitle={meta.subtitle}
        showBack={isSubPage}
        onBack={() => setActiveTab(userRole === 'admin' ? 'admin' : 'home')}
        userRole={userRole}
        onSwitchRole={handleSwitchRole}
        activeTab={activeTab}
        isAuthenticated={isAuthenticated}
        onLogout={handleLogout}
        onOpenAuditOrInfo={() => setActiveTab(userRole === 'admin' ? 'admin' : 'auth')}
      />

      {/* Screen Body */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {!isAuthenticated ? (
          <AuthScreen
            onLoginSuccess={handleLoginSuccess}
            onSignUpSuccess={handleSignUpSuccess}
            initialMode="splash"
          />
        ) : (
          <>
            {activeTab === 'home' && (
              userRole === 'admin' ? (
                <AdminDashboardScreen
                  programmes={programmes}
                  auditLogs={auditLogs}
                  onUpdateCutoff={handleUpdateCutoff}
                  onNavigateToFeedback={() => setActiveTab('feedback')}
                  onLogout={handleLogout}
                />
              ) : (
                <HomeScreen
                  profile={profile}
                  recommendations={recommendations}
                  savedCount={savedIds.length}
                  onNavigate={(tab) => setActiveTab(tab)}
                  onLoadSampleProfile={handleLoadSample}
                  onOpenDetails={(result) => setSelectedProgramme(result.programme)}
                  onLogout={handleLogout}
                />
              )
            )}

            {activeTab === 'profile' && (
              <ProfileScreen
                profile={profile}
                onSaveProfile={handleSaveProfile}
                onLoadSample={handleLoadSample}
                isOnboarding={isOnboarding}
                onLogout={handleLogout}
              />
            )}

            {activeTab === 'recommendations' && (
              <RecommendationScreen
                results={recommendations}
                savedIds={savedIds}
                userEstimatedCluster={profile?.calculatedClusterScore || 41.8}
                onToggleSave={handleToggleSave}
                onOpenShap={(res) => setSelectedShapResult(res)}
                onOpenDetails={(prog) => setSelectedProgramme(prog)}
                onNavigateToProfile={() => setActiveTab('profile')}
                onNavigateToFeedback={(pId) => {
                  setFeedbackProgrammeId(pId);
                  setActiveTab('feedback');
                }}
              />
            )}

            {activeTab === 'directory' && (
              <DirectoryScreen
                programmes={programmes}
                savedIds={savedIds}
                onToggleSave={handleToggleSave}
                onOpenDetails={(prog) => setSelectedProgramme(prog)}
              />
            )}

            {activeTab === 'saved' && (
              <SavedProgrammesScreen
                savedProgrammes={savedProgrammesList}
                onRemoveSave={handleToggleSave}
                onOpenDetails={(prog) => setSelectedProgramme(prog)}
                onNavigateToRecommendations={() => setActiveTab('recommendations')}
              />
            )}

            {activeTab === 'feedback' && (
              <FeedbackScreen
                programmes={programmes}
                feedbacks={feedbacks}
                initialProgrammeId={feedbackProgrammeId}
                onSubmitFeedback={handleSubmitFeedback}
                onNavigateToProfile={() => setActiveTab('profile')}
              />
            )}

            {activeTab === 'admin' && (
              <AdminDashboardScreen
                programmes={programmes}
                auditLogs={auditLogs}
                onUpdateCutoff={handleUpdateCutoff}
                onNavigateToFeedback={() => setActiveTab('feedback')}
                onLogout={handleLogout}
              />
            )}

            {activeTab === 'auth' && (
              <AuthScreen
                onLoginSuccess={handleLoginSuccess}
                onSignUpSuccess={handleSignUpSuccess}
                initialMode="splash"
              />
            )}
          </>
        )}
      </main>

      {/* SHAP Explanation Modal Bottom Sheet */}
      {selectedShapResult && (
        <ShapExplanationModal
          result={selectedShapResult}
          onClose={() => setSelectedShapResult(null)}
        />
      )}

      {/* Programme Details Modal Bottom Sheet */}
      {selectedProgramme && (
        <ProgrammeDetailsModal
          programme={selectedProgramme}
          isSaved={savedIds.includes(selectedProgramme.id)}
          studentProfile={profile}
          onToggleSave={handleToggleSave}
          onClose={() => setSelectedProgramme(null)}
        />
      )}

      {/* Flutter Mobile & ML Architecture Modal */}
      <FlutterProposalModal
        isOpen={showFlutterModal}
        onClose={() => setShowFlutterModal(false)}
      />

      {/* Native Mobile Bottom Navigation Bar (Visible when authenticated) */}
      {isAuthenticated && (
        <MobileBottomNav
          activeTab={activeTab}
          onTabChange={(tab) => setActiveTab(tab)}
          savedCount={savedIds.length}
          hasRecommendations={recommendations.length > 0}
          userRole={userRole}
        />
      )}
    </MobileDeviceFrame>
  );
};
