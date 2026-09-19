import React from 'react';
import { ArrowLeft, GraduationCap, Shield, User, LogOut } from 'lucide-react';
import { UserRole } from '../types';

interface MobileAppBarProps {
  title: string;
  subtitle?: string;
  showBack?: boolean;
  onBack?: () => void;
  userRole: UserRole;
  onSwitchRole: (role: UserRole) => void;
  activeTab: string;
  onOpenAuditOrInfo?: () => void;
  isAuthenticated?: boolean;
  onLogout?: () => void;
}

export const MobileAppBar: React.FC<MobileAppBarProps> = ({
  title,
  subtitle,
  showBack = false,
  onBack,
  userRole,
  onSwitchRole,
  isAuthenticated = false,
  onLogout,
}) => {
  return (
    <header className="bg-[#14213D] text-white px-4 py-3 shrink-0 flex items-center justify-between border-b border-white/10 z-30 shadow-sm">
      <div className="flex items-center space-x-2.5">
        {showBack && onBack ? (
          <button
            id="mobile-appbar-back"
            onClick={onBack}
            className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-white hover:bg-white/20 transition-colors active:scale-95 cursor-pointer"
            aria-label="Back"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
        ) : (
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#0EA5A4] to-[#4F46E5] flex items-center justify-center text-white shadow-sm">
            <GraduationCap className="w-4 h-4" />
          </div>
        )}

        <div>
          <h1 className="text-sm font-bold tracking-tight text-white flex items-center space-x-1.5 leading-tight">
            <span>{title}</span>
          </h1>
          {subtitle && (
            <p className="text-[10px] text-slate-300 line-clamp-1 leading-tight">{subtitle}</p>
          )}
        </div>
      </div>

      {/* Right Actions: Role Badge & Log Out */}
      <div className="flex items-center space-x-2">
        {isAuthenticated && (
          <button
            id="btn-switch-role"
            onClick={() => onSwitchRole(userRole === 'student' ? 'admin' : 'student')}
            className={`px-2 py-1 rounded-full text-[10px] font-semibold flex items-center space-x-1 transition-all active:scale-95 border cursor-pointer ${
              userRole === 'admin'
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                : 'bg-[#0EA5A4]/20 text-[#0EA5A4] border-[#0EA5A4]/40'
            }`}
            title="Toggle between Student view and Admin mode"
          >
            {userRole === 'admin' ? (
              <>
                <Shield className="w-3 h-3 text-amber-400" />
                <span>Admin</span>
              </>
            ) : (
              <>
                <User className="w-3 h-3 text-teal-300" />
                <span>Student</span>
              </>
            )}
          </button>
        )}

        {isAuthenticated && onLogout && (
          <button
            id="btn-appbar-logout"
            onClick={onLogout}
            className="w-7 h-7 rounded-full bg-white/10 hover:bg-rose-500/30 hover:text-rose-200 flex items-center justify-center text-white/80 transition-colors cursor-pointer"
            title="Log Out"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </header>
  );
};
