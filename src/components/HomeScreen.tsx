import React from 'react';
import { Sparkles, UserCheck, ArrowRight, Bookmark, Award, BookOpen, Layers, CheckCircle2, ChevronRight, GraduationCap, LogOut } from 'lucide-react';
import { StudentProfile, RecommendationResult } from '../types';

interface HomeScreenProps {
  profile: StudentProfile | null;
  recommendations: RecommendationResult[];
  savedCount: number;
  onNavigate: (tab: 'profile' | 'recommendations' | 'directory' | 'feedback' | 'saved') => void;
  onLoadSampleProfile: () => void;
  onOpenDetails: (result: RecommendationResult) => void;
  onLogout?: () => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  profile,
  recommendations,
  savedCount,
  onNavigate,
  onLoadSampleProfile,
  onOpenDetails,
  onLogout,
}) => {
  const profileCompletion = React.useMemo(() => {
    if (!profile) return 0;
    let score = 0;
    if (profile.kcseMeanGrade) score += 20;
    if (Object.keys(profile.grades || {}).length >= 4) score += 20;
    if (profile.interests && profile.interests.length > 0) score += 15;
    if (profile.skills && profile.skills.length > 0) score += 15;
    if (profile.strengths && profile.strengths.length > 0) score += 15;
    if (profile.aspirations && profile.aspirations.length > 0) score += 15;
    return Math.min(100, score);
  }, [profile]);

  return (
    <div className="flex-1 overflow-y-auto bg-[#F8FAFC] p-4 space-y-4">
      {/* Welcome & Student Hero Card */}
      <div className="bg-gradient-to-br from-[#14213D] via-[#1E293B] to-[#3B82F6] rounded-2xl p-4 text-white shadow-md relative overflow-hidden space-y-3">
        {/* Background glow accent */}
        <div className="absolute -top-12 -right-12 w-32 h-32 bg-[#0EA5A4]/20 rounded-full blur-2xl pointer-events-none" />

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full bg-white/10 text-teal-300 border border-white/10">
              Student Portal
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] text-slate-300 font-mono">
              {profile?.indexNumber || 'KCSE 2025'}
            </span>
            {onLogout && (
              <button
                type="button"
                onClick={onLogout}
                className="px-2 py-0.5 rounded-full bg-white/10 hover:bg-white/20 text-slate-200 text-[10px] flex items-center space-x-1 cursor-pointer transition-colors"
                title="Log Out / Return to Splash"
              >
                <LogOut className="w-2.5 h-2.5" />
                <span>Log Out</span>
              </button>
            )}
          </div>
        </div>

        <div>
          <h2 className="text-lg font-black tracking-tight leading-tight">
            Hello, {profile?.fullName?.split(' ')[0] || 'Student'}!
          </h2>
          <p className="text-xs text-slate-200 mt-0.5 leading-snug">
            Ready to discover your ideal university degree programme based on your KCSE grades and aspirations?
          </p>
        </div>

        {/* Profile Readiness Bar */}
        <div className="bg-black/20 rounded-xl p-2.5 backdrop-blur-xs border border-white/10 space-y-1.5">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-300 flex items-center space-x-1">
              <UserCheck className="w-3.5 h-3.5 text-teal-300" />
              <span>Profile Readiness</span>
            </span>
            <span className="font-bold text-teal-300">{profileCompletion}% Complete</span>
          </div>

          <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
            <div
              className="bg-gradient-to-r from-teal-400 to-indigo-400 h-full rounded-full transition-all duration-500"
              style={{ width: `${profileCompletion}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-[10px] text-slate-300 pt-0.5">
            <span>Mean Grade: <strong className="text-white">{profile?.kcseMeanGrade || 'B+'}</strong></span>
            <button
              onClick={() => onNavigate('profile')}
              className="text-teal-300 hover:underline font-semibold"
            >
              Edit Academic Details &rarr;
            </button>
          </div>
        </div>

        {/* Main Actions */}
        <div className="grid grid-cols-2 gap-2 pt-1">
          <button
            id="home-btn-recommendations"
            onClick={() => onNavigate('recommendations')}
            className="py-2.5 px-3 bg-gradient-to-r from-[#0EA5A4] to-[#4F46E5] hover:opacity-95 text-white rounded-xl text-xs font-bold shadow-md flex items-center justify-center space-x-1.5 active:scale-98 cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5 text-teal-200" />
            <span>Top 3 Matches</span>
          </button>

          <button
            id="home-btn-profile"
            onClick={() => onNavigate('profile')}
            className="py-2.5 px-3 bg-white/15 hover:bg-white/25 text-white border border-white/20 rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 active:scale-98 cursor-pointer"
          >
            <GraduationCap className="w-3.5 h-3.5" />
            <span>Academic Profile</span>
          </button>
        </div>
      </div>

      {/* Top 3 Recommendation Teaser (If available) */}
      {recommendations && recommendations.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center space-x-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#4F46E5]" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                Your Top Degree Matches
              </h3>
            </div>
            <button
              onClick={() => onNavigate('recommendations')}
              className="text-[11px] font-bold text-[#4F46E5] hover:underline flex items-center space-x-0.5"
            >
              <span>View All 3</span>
              <ChevronRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2">
            {recommendations.slice(0, 2).map((item) => (
              <div
                key={item.programmeId}
                onClick={() => onOpenDetails(item)}
                className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs hover:shadow-sm transition-all flex items-center justify-between gap-2 cursor-pointer active:scale-99"
              >
                <div className="flex items-center space-x-2.5 flex-1 min-w-0">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-white font-extrabold text-xs shrink-0 ${
                    item.rank === 1 ? 'bg-amber-500' : 'bg-[#4F46E5]'
                  }`}>
                    #{item.rank}
                  </div>
                  <div className="truncate">
                    <h4 className="text-xs font-bold text-slate-800 truncate leading-snug">
                      {item.programme.name}
                    </h4>
                    <p className="text-[10px] text-slate-500 truncate">
                      {item.programme.category} &bull; {item.programme.universities[0]?.name || 'KUCCPS'}
                    </p>
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold border border-emerald-200">
                    {item.confidence.toFixed(1)}% Match
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Navigation Cards Grid */}
      <div className="grid grid-cols-2 gap-2.5">
        <button
          onClick={() => onNavigate('directory')}
          className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-xs hover:border-slate-300 text-left transition-all active:scale-98 cursor-pointer flex flex-col justify-between space-y-2"
        >
          <div className="w-8 h-8 rounded-lg bg-indigo-50 text-[#4F46E5] flex items-center justify-center">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-900">Explore Courses</h4>
            <p className="text-[10px] text-slate-500 mt-0.5">Browse Kenyan universities and KUCCPS cutoffs</p>
          </div>
        </button>

        <button
          onClick={() => onNavigate('saved')}
          className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-xs hover:border-slate-300 text-left transition-all active:scale-98 cursor-pointer flex flex-col justify-between space-y-2"
        >
          <div className="w-8 h-8 rounded-lg bg-teal-50 text-[#0EA5A4] flex items-center justify-center">
            <Bookmark className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-900">Shortlisted ({savedCount})</h4>
            <p className="text-[10px] text-slate-500 mt-0.5">Your saved bookmarked university programmes</p>
          </div>
        </button>
      </div>

      {/* Key Features (Explainable AI & KUCCPS) */}
      <div className="bg-white rounded-xl p-3.5 border border-slate-200/80 shadow-xs space-y-2">
        <h4 className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
          <Award className="w-4 h-4 text-[#4F46E5]" />
          <span>About UniGuide Decision Support</span>
        </h4>
        <p className="text-[11px] text-slate-600 leading-relaxed">
          UniGuide uses <strong>Machine Learning Classification</strong> and <strong>SHAP (SHapley Additive exPlanations)</strong> to bridge the gap between academic eligibility and career aspirations for students in Kenya.
        </p>
        <div className="grid grid-cols-2 gap-1.5 pt-1 text-[10px] text-slate-600">
          <div className="flex items-center space-x-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" />
            <span>KCSE Mean & Subject Weights</span>
          </div>
          <div className="flex items-center space-x-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" />
            <span>Transparent SHAP Drivers</span>
          </div>
          <div className="flex items-center space-x-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" />
            <span>KUCCPS Cluster Validation</span>
          </div>
          <div className="flex items-center space-x-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" />
            <span>Kenyan Universities Data</span>
          </div>
        </div>
      </div>
    </div>
  );
};
