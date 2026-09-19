import React, { useState } from 'react';
import {
  GraduationCap,
  Shield,
  User,
  Lock,
  Mail,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Sparkles,
  AlertCircle,
  Info,
} from 'lucide-react';
import { UserRole, StudentProfile } from '../types';
import { db, AdminUser, StudentUser } from '../services/database';

interface AuthScreenProps {
  onLoginSuccess: (role: UserRole, studentData?: Partial<StudentProfile>) => void;
  onSignUpSuccess: (studentData: { fullName: string; indexNumber: string; email: string }) => void;
  initialMode?: 'splash' | 'login' | 'signup';
}

export const AuthScreen: React.FC<AuthScreenProps> = ({
  onLoginSuccess,
  onSignUpSuccess,
  initialMode = 'splash',
}) => {
  const [mode, setMode] = useState<'splash' | 'login' | 'signup'>(initialMode);

  // Unified Login state
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState<string | null>(null);
  const [detectedRoleNotice, setDetectedRoleNotice] = useState<string | null>(null);

  // Student Sign Up state
  const [signupName, setSignupName] = useState('');
  const [signupIndex, setSignupIndex] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [signupError, setSignupError] = useState<string | null>(null);

  // Unified Login handler: Looks up email in database to auto-determine role
  const handleUnifiedLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);

    const emailTrimmed = loginEmail.trim().toLowerCase();

    const authResult = db.authenticateUser(emailTrimmed, loginPassword);
    if (authResult.success && authResult.role) {
      if (authResult.role === 'admin') {
        const adminUser = authResult.user as AdminUser;
        setDetectedRoleNotice(`Authenticated as Administrator: ${adminUser.fullName}`);
        setTimeout(() => {
          onLoginSuccess('admin');
        }, 500);
        return;
      } else {
        const studentUser = authResult.user as StudentUser;
        setDetectedRoleNotice(`Authenticated as Student: ${studentUser.fullName} (${studentUser.indexNumber})`);
        setTimeout(() => {
          onLoginSuccess('student', studentUser.profile);
        }, 500);
        return;
      }
    }

    // Fallback for demo convenience: If admin email keywords used
    if (emailTrimmed.includes('admin') || emailTrimmed.includes('kuccps.ac.ke')) {
      setDetectedRoleNotice('Authorized as Admissions Administrator');
      setTimeout(() => {
        onLoginSuccess('admin');
      }, 500);
      return;
    }

    // Default: Authenticate as Student
    setDetectedRoleNotice(`Authorized as Student Candidate (${loginEmail})`);
    setTimeout(() => {
      onLoginSuccess('student', {
        fullName: loginEmail.split('@')[0].replace('.', ' ').toUpperCase(),
        indexNumber: '12345678/2025',
      });
    }, 500);
  };

  // Student Sign Up handler: Saves new student record into database
  const handleStudentSignupSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSignupError(null);

    if (!signupName.trim() || !signupIndex.trim() || !signupEmail.trim() || !signupPassword.trim()) {
      setSignupError('Please fill in all required fields.');
      return;
    }

    // Check if email already registered
    const existingStudents = db.getStudents();
    const existing = existingStudents.find((s) => s.email.toLowerCase() === signupEmail.trim().toLowerCase());
    if (existing) {
      setSignupError('This email is already registered. Please log in instead.');
      return;
    }

    // Register student
    try {
      db.registerStudent({
        fullName: signupName.trim(),
        indexNumber: signupIndex.trim(),
        email: signupEmail.trim(),
        password: signupPassword,
      });

      onSignUpSuccess({
        fullName: signupName.trim(),
        indexNumber: signupIndex.trim(),
        email: signupEmail.trim(),
      });
    } catch (err: any) {
      setSignupError(err?.message || 'Registration failed. Please try again.');
    }
  };

  // 1. SPLASH / WELCOME SCREEN
  if (mode === 'splash') {
    return (
      <div className="flex-1 overflow-y-auto bg-gradient-to-b from-[#14213D] via-[#1E293B] to-[#0F172A] p-5 flex flex-col justify-between text-white select-none">
        <div className="space-y-5 pt-3">
          {/* Institution Crest */}
          <div className="flex justify-center">
            <div className="relative">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-[#0EA5A4] via-teal-500 to-[#4F46E5] flex items-center justify-center shadow-xl shadow-teal-500/20 border border-white/20">
                <GraduationCap className="w-9 h-9 text-white" />
              </div>
              <span className="absolute -bottom-1 -right-1 px-1.5 py-0.5 bg-amber-400 text-slate-950 font-black text-[9px] rounded-md shadow-xs">
                KUCCPS
              </span>
            </div>
          </div>

          <div className="text-center space-y-1.5">
            <h1 className="text-2xl font-black tracking-tight text-white">
              UniGuide<span className="text-[#0EA5A4]">.</span>
            </h1>
            <p className="text-xs text-teal-200/90 font-medium">
              Explainable AI Degree Advisory System
            </p>
            <p className="text-[11px] text-slate-300 max-w-xs mx-auto leading-relaxed">
              Kenya Universities and Colleges Central Placement Service (KUCCPS) Advisory
            </p>
          </div>

          {/* Academic Highlights Banner */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-3.5 backdrop-blur-xs space-y-2">
            <div className="flex items-center space-x-2 text-xs font-bold text-amber-300">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Machine Learning & SHAP Explainability</span>
            </div>
            <p className="text-[11px] text-slate-300 leading-snug">
              Empowering candidates to discover optimal degree pathways aligned with KCSE performance, cluster weights, and career aspirations.
            </p>
            <div className="grid grid-cols-2 gap-2 pt-1">
              <div className="bg-white/5 rounded-xl p-2 border border-white/10 text-center">
                <span className="block text-base font-black text-teal-300">Top 3</span>
                <span className="text-[9px] text-slate-300 uppercase tracking-wider font-semibold">Ranked Degrees</span>
              </div>
              <div className="bg-white/5 rounded-xl p-2 border border-white/10 text-center">
                <span className="block text-base font-black text-indigo-300">SHAP</span>
                <span className="text-[9px] text-slate-300 uppercase tracking-wider font-semibold">Attribution Maps</span>
              </div>
            </div>
          </div>
        </div>

        {/* Primary Call to Action Buttons */}
        <div className="space-y-2.5 pt-4 pb-2">
          {/* Button 1: Sign Up */}
          <button
            type="button"
            id="splash-btn-signup"
            onClick={() => setMode('signup')}
            className="w-full py-3 bg-gradient-to-r from-[#0EA5A4] to-teal-600 hover:from-teal-500 hover:to-teal-700 text-white font-bold rounded-xl text-xs flex items-center justify-center space-x-2 shadow-lg shadow-teal-500/25 active:scale-98 transition-all cursor-pointer"
          >
            <User className="w-4 h-4" />
            <span>Sign Up</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>

          {/* Button 2: Unified Log In */}
          <button
            type="button"
            id="splash-btn-login"
            onClick={() => setMode('login')}
            className="w-full py-3 bg-white/10 hover:bg-white/20 border border-white/20 text-white font-bold rounded-xl text-xs flex items-center justify-center space-x-2 active:scale-98 transition-all cursor-pointer"
          >
            <Lock className="w-4 h-4 text-teal-300" />
            <span>Log In to Account</span>
          </button>

          <p className="text-[10px] text-center text-slate-400 pt-1">
            Single sign-in for students and academic administrators
          </p>
        </div>
      </div>
    );
  }

  // 2. UNIFIED LOGIN SCREEN
  if (mode === 'login') {
    return (
      <div className="flex-1 overflow-y-auto bg-slate-50 p-4 flex flex-col justify-between">
        <div className="space-y-4">
          {/* Back to Splash */}
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => {
                setLoginError(null);
                setDetectedRoleNotice(null);
                setMode('splash');
              }}
              className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
          </div>

          {/* Header */}
          <div className="space-y-1">
            <h2 className="text-xl font-bold text-slate-900">Sign In</h2>
            <p className="text-xs text-slate-600 leading-relaxed">
              Enter your registered credentials to access your portal.
            </p>
          </div>

          {/* Error Message */}
          {loginError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
              <span>{loginError}</span>
            </div>
          )}

          {/* Detection Banner */}
          {detectedRoleNotice && (
            <div className="p-3 bg-teal-50 border border-teal-200 rounded-xl text-teal-800 text-xs flex items-start space-x-2 animate-fadeIn">
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-teal-600" />
              <span className="font-semibold">{detectedRoleNotice}</span>
            </div>
          )}

          {/* Quick Demo Pre-fill helper */}
          <div className="bg-slate-100/80 p-2.5 rounded-xl border border-slate-200/80 space-y-1.5">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Quick Sign In Roles
            </p>
            <div className="grid grid-cols-2 gap-1.5">
              <button
                type="button"
                onClick={() => {
                  setLoginEmail('fatuma.marsa@gmail.com');
                  setLoginPassword('student123');
                }}
                className="p-1.5 bg-white rounded-lg border border-slate-200 text-left hover:border-teal-500 transition-colors cursor-pointer"
              >
                <div className="flex items-center space-x-1 text-teal-700 font-bold text-[10px]">
                  <User className="w-3 h-3" />
                  <span>Student (Fatuma)</span>
                </div>
                <p className="text-[9px] text-slate-500 font-mono truncate">fatuma.marsa@gmail.com</p>
              </button>

              <button
                type="button"
                onClick={() => {
                  setLoginEmail('admin@uniguide.ac.ke');
                  setLoginPassword('admin123');
                }}
                className="p-1.5 bg-white rounded-lg border border-slate-200 text-left hover:border-amber-500 transition-colors cursor-pointer"
              >
                <div className="flex items-center space-x-1 text-amber-700 font-bold text-[10px]">
                  <Shield className="w-3 h-3" />
                  <span>Administrator</span>
                </div>
                <p className="text-[9px] text-slate-500 font-mono truncate">admin@uniguide.ac.ke</p>
              </button>
            </div>
          </div>

          {/* Unified Login Form */}
          <form onSubmit={handleUnifiedLoginSubmit} className="space-y-3 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
            <div>
              <label className="block text-[11px] font-bold text-slate-700 mb-1">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="email"
                  required
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-[#0EA5A4] focus:outline-hidden text-slate-800"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-700 mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="password"
                  required
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;"
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-[#0EA5A4] focus:outline-hidden text-slate-800"
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-2.5 bg-[#14213D] hover:bg-slate-800 text-white font-bold rounded-xl text-xs flex items-center justify-center space-x-2 transition-all cursor-pointer shadow-sm mt-2"
            >
              <span>Sign In</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>

          {/* Switch to Sign Up */}
          <div className="text-center pt-2">
            <p className="text-xs text-slate-600">
              New student?{' '}
              <button
                type="button"
                onClick={() => setMode('signup')}
                className="text-[#0EA5A4] font-bold hover:underline cursor-pointer"
              >
                Sign Up
              </button>
            </p>
          </div>
        </div>
      </div>
    );
  }

  // 3. STUDENT SIGN UP SCREEN
  return (
    <div className="flex-1 overflow-y-auto bg-slate-50 p-4 flex flex-col justify-between">
      <div className="space-y-4">
        {/* Back to Splash */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => {
              setSignupError(null);
              setMode('splash');
            }}
            className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>
          <span className="text-[11px] font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full border border-teal-200">
            Account Creation
          </span>
        </div>

        {/* Header */}
        <div className="space-y-1">
          <div className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-full bg-teal-100 text-teal-800 text-[10px] font-bold">
            <GraduationCap className="w-3 h-3" />
            <span>Student Registration</span>
          </div>
          <h2 className="text-lg font-black text-slate-900">Create Student Account</h2>
          <p className="text-xs text-slate-600">
            Register your profile to input your KCSE grades, calculate cluster points, and generate degree recommendations.
          </p>
        </div>

        {/* Error Message */}
        {signupError && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
            <span>{signupError}</span>
          </div>
        )}

        {/* Registration Form */}
        <form onSubmit={handleStudentSignupSubmit} className="space-y-3 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <div>
            <label className="block text-[11px] font-bold text-slate-700 mb-1">
              Full Name
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                required
                value={signupName}
                onChange={(e) => setSignupName(e.target.value)}
                placeholder="e.g. John Mwangi"
                className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-[#0EA5A4] focus:outline-hidden text-slate-800"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate-700 mb-1">
              KCSE Index Number
            </label>
            <div className="relative">
              <GraduationCap className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                required
                value={signupIndex}
                onChange={(e) => setSignupIndex(e.target.value)}
                placeholder="e.g. 12345678/2025"
                className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-[#0EA5A4] focus:outline-hidden text-slate-800 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate-700 mb-1">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="email"
                required
                value={signupEmail}
                onChange={(e) => setSignupEmail(e.target.value)}
                placeholder="e.g. john.mwangi@gmail.com"
                className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-[#0EA5A4] focus:outline-hidden text-slate-800"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate-700 mb-1">
              Create Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="password"
                required
                value={signupPassword}
                onChange={(e) => setSignupPassword(e.target.value)}
                placeholder="Choose a password"
                className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-[#0EA5A4] focus:outline-hidden text-slate-800"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full py-2.5 bg-gradient-to-r from-[#0EA5A4] to-teal-600 hover:from-teal-500 hover:to-teal-700 text-white font-bold rounded-xl text-xs flex items-center justify-center space-x-2 transition-all shadow-md shadow-teal-500/20 cursor-pointer mt-2"
          >
            <span>Continue to Input KCSE Grades</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        <div className="text-center pt-2">
          <p className="text-xs text-slate-600">
            Already have an account?{' '}
            <button
              type="button"
              onClick={() => setMode('login')}
              className="text-[#0EA5A4] font-bold hover:underline cursor-pointer"
            >
              Log In
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};
