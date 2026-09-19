import React from 'react';
import { Home, Sparkles, BookOpen, Bookmark, User, ShieldCheck, History, MessageSquare } from 'lucide-react';
import { UserRole } from '../types';

export type MobileTabType = 'home' | 'profile' | 'recommendations' | 'saved' | 'directory' | 'feedback' | 'admin' | 'auth';

interface MobileBottomNavProps {
  activeTab: MobileTabType;
  onTabChange: (tab: MobileTabType) => void;
  savedCount: number;
  hasRecommendations: boolean;
  userRole: UserRole;
}

export const MobileBottomNav: React.FC<MobileBottomNavProps> = ({
  activeTab,
  onTabChange,
  savedCount,
  hasRecommendations,
  userRole,
}) => {
  // ADMIN NAVIGATION (Purely Administrative Tools)
  if (userRole === 'admin') {
    return (
      <nav
        id="mobile-bottom-nav-admin"
        className="bg-white border-t border-slate-200/90 px-3 py-2 shrink-0 z-30 shadow-[0_-4px_16px_rgba(0,0,0,0.04)] flex items-center justify-around select-none"
      >
        {/* 1. Admin Console / Overview */}
        <button
          id="nav-tab-admin-console"
          onClick={() => onTabChange('admin')}
          className={`flex flex-col items-center justify-center py-1 px-3 rounded-xl transition-all cursor-pointer ${
            activeTab === 'admin' || activeTab === 'home'
              ? 'text-amber-600 font-bold'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <ShieldCheck className={`w-5 h-5 transition-transform ${activeTab === 'admin' || activeTab === 'home' ? 'scale-110 stroke-[2.5]' : 'stroke-2'}`} />
          <span className="text-[10px] mt-0.5">Console</span>
        </button>

        {/* 2. Degree Programmes & Cutoffs Catalog */}
        <button
          id="nav-tab-admin-courses"
          onClick={() => onTabChange('directory')}
          className={`flex flex-col items-center justify-center py-1 px-3 rounded-xl transition-all cursor-pointer ${
            activeTab === 'directory'
              ? 'text-indigo-600 font-bold'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <BookOpen className={`w-5 h-5 transition-transform ${activeTab === 'directory' ? 'scale-110 stroke-[2.5]' : 'stroke-2'}`} />
          <span className="text-[10px] mt-0.5">Cutoffs & Catalog</span>
        </button>

        {/* 3. Student Evaluation Feedback */}
        <button
          id="nav-tab-admin-feedback"
          onClick={() => onTabChange('feedback')}
          className={`flex flex-col items-center justify-center py-1 px-3 rounded-xl transition-all cursor-pointer ${
            activeTab === 'feedback'
              ? 'text-teal-600 font-bold'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <MessageSquare className={`w-5 h-5 transition-transform ${activeTab === 'feedback' ? 'scale-110 stroke-[2.5]' : 'stroke-2'}`} />
          <span className="text-[10px] mt-0.5">Model Feedback</span>
        </button>
      </nav>
    );
  }

  // STUDENT NAVIGATION (Academic Leaver Decision Support)
  return (
    <nav
      id="mobile-bottom-nav-student"
      className="bg-white border-t border-slate-200/90 px-2 py-1.5 shrink-0 z-30 shadow-[0_-4px_16px_rgba(0,0,0,0.04)] flex items-center justify-around select-none"
    >
      {/* 1. Home */}
      <button
        id="nav-tab-home"
        onClick={() => onTabChange('home')}
        className={`flex flex-col items-center justify-center py-1 px-2.5 rounded-xl transition-all cursor-pointer ${
          activeTab === 'home'
            ? 'text-[#4F46E5] font-bold'
            : 'text-slate-500 hover:text-slate-800'
        }`}
      >
        <Home className={`w-5 h-5 transition-transform ${activeTab === 'home' ? 'scale-110 stroke-[2.5]' : 'stroke-2'}`} />
        <span className="text-[10px] mt-0.5">Home</span>
      </button>

      {/* 2. Programmes Directory */}
      <button
        id="nav-tab-directory"
        onClick={() => onTabChange('directory')}
        className={`flex flex-col items-center justify-center py-1 px-2.5 rounded-xl transition-all cursor-pointer ${
          activeTab === 'directory'
            ? 'text-[#4F46E5] font-bold'
            : 'text-slate-500 hover:text-slate-800'
        }`}
      >
        <BookOpen className={`w-5 h-5 transition-transform ${activeTab === 'directory' ? 'scale-110 stroke-[2.5]' : 'stroke-2'}`} />
        <span className="text-[10px] mt-0.5">Courses</span>
      </button>

      {/* 3. Center Recommender Pill */}
      <button
        id="nav-tab-recommendations"
        onClick={() => onTabChange('recommendations')}
        className="flex flex-col items-center justify-center -mt-3.5 relative group cursor-pointer"
      >
        <div
          className={`w-12 h-12 rounded-full flex items-center justify-center text-white shadow-lg transition-all transform active:scale-95 ${
            activeTab === 'recommendations'
              ? 'bg-gradient-to-tr from-[#0EA5A4] to-[#4F46E5] ring-3 ring-indigo-200 shadow-indigo-300/50'
              : 'bg-gradient-to-tr from-[#14213D] to-[#3B82F6]'
          }`}
        >
          <Sparkles className="w-5 h-5 text-teal-200 animate-pulse" />
        </div>
        <span
          className={`text-[10px] mt-0.5 font-medium ${
            activeTab === 'recommendations' ? 'text-[#4F46E5] font-bold' : 'text-slate-600'
          }`}
        >
          Top 3 AI
        </span>
        {hasRecommendations && (
          <span className="absolute top-0 right-0 w-3 h-3 bg-amber-400 border-2 border-white rounded-full" />
        )}
      </button>

      {/* 4. Saved */}
      <button
        id="nav-tab-saved"
        onClick={() => onTabChange('saved')}
        className={`relative flex flex-col items-center justify-center py-1 px-2.5 rounded-xl transition-all cursor-pointer ${
          activeTab === 'saved'
            ? 'text-[#4F46E5] font-bold'
            : 'text-slate-500 hover:text-slate-800'
        }`}
      >
        <Bookmark className={`w-5 h-5 transition-transform ${activeTab === 'saved' ? 'scale-110 stroke-[2.5]' : 'stroke-2'}`} />
        <span className="text-[10px] mt-0.5">Saved</span>
        {savedCount > 0 && (
          <span className="absolute top-1 right-2.5 w-4 h-4 bg-[#0EA5A4] text-white text-[9px] font-bold rounded-full flex items-center justify-center">
            {savedCount}
          </span>
        )}
      </button>

      {/* 5. Profile */}
      <button
        id="nav-tab-profile"
        onClick={() => onTabChange('profile')}
        className={`flex flex-col items-center justify-center py-1 px-2.5 rounded-xl transition-all cursor-pointer ${
          activeTab === 'profile'
            ? 'text-[#4F46E5] font-bold'
            : 'text-slate-500 hover:text-slate-800'
        }`}
      >
        <User className={`w-5 h-5 transition-transform ${activeTab === 'profile' ? 'scale-110 stroke-[2.5]' : 'stroke-2'}`} />
        <span className="text-[10px] mt-0.5">Profile</span>
      </button>
    </nav>
  );
};
