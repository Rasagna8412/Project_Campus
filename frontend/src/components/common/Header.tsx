import React, { useState } from 'react';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  GraduationCap,
  XCircle,
  LogIn,
  UserPlus,
  BookOpen,
  Compass,
  LogOut,
} from 'lucide-react';
import { HealthResponse, ConnectionState } from '../../types/api';
import { useAuth } from '../../context/AuthContext';

interface HeaderProps {
  connectionState: ConnectionState;
  healthData: HealthResponse | null;
  errorMessage: string | null;
  onRefresh: () => void;
  isRefreshing: boolean;
  onOpenAuth: (mode: 'signin' | 'register') => void;
  onOpenOnboarding: () => void;
  onOpenLessons?: () => void;
  onOpenHome?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  connectionState,
  healthData,
  errorMessage,
  onRefresh,
  isRefreshing,
  onOpenAuth,
  onOpenOnboarding,
  onOpenLessons,
  onOpenHome,
}) => {
  const { user, profile, isAuthenticated, logout } = useAuth();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await logout();
    } finally {
      setIsLoggingOut(false);
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/95 backdrop-blur shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand identity */}
        <button
          onClick={onOpenHome}
          className="flex items-center space-x-3 text-left focus:outline-none"
        >
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-brand-600 to-brand-800 flex items-center justify-center text-white shadow-md">
            <GraduationCap className="w-6 h-6" aria-hidden="true" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-tight text-slate-900">Project Campus</span>
              <span className="text-xs px-2 py-0.5 rounded-full font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                Milestone 3 Active
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium">Academic Learning & Examination Platform</p>
          </div>
        </button>

        {/* Right side controls: Health Badge + Auth Controls */}
        <div className="flex items-center space-x-4">
          {/* Live System Health Badge */}
          <div className="hidden sm:flex items-center space-x-2">
            <div
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                connectionState === 'connected'
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  : connectionState === 'checking'
                  ? 'bg-blue-50 text-blue-800 border-blue-200 animate-pulse'
                  : connectionState === 'disconnected'
                  ? 'bg-rose-50 text-rose-800 border-rose-200'
                  : 'bg-amber-50 text-amber-800 border-amber-200'
              }`}
              role="status"
              aria-live="polite"
            >
              {connectionState === 'connected' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}
              {connectionState === 'checking' && <Activity className="w-3.5 h-3.5 text-blue-600 animate-spin" />}
              {connectionState === 'disconnected' && <XCircle className="w-3.5 h-3.5 text-rose-600" />}
              {connectionState === 'error' && <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />}

              <span>
                {connectionState === 'connected' && `API v${healthData?.version} • DB Connected`}
                {connectionState === 'checking' && 'Connecting...'}
                {connectionState === 'disconnected' && 'Backend Offline'}
                {connectionState === 'error' && (errorMessage || 'Degraded')}
              </span>
            </div>

            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 border border-slate-200 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:opacity-50"
              title="Refresh API Connection"
              aria-label="Refresh Backend Connectivity Status"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-brand-600' : ''}`} />
            </button>
          </div>

          {/* User Session Navigation */}
          {isAuthenticated && user ? (
            <div className="flex items-center space-x-3 pl-2 border-l border-slate-200">
              <div className="flex items-center space-x-2 text-left">
                <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center font-bold text-xs border border-brand-200">
                  {user.full_name ? user.full_name[0].toUpperCase() : 'S'}
                </div>
                <div className="hidden md:block">
                  <p className="text-xs font-bold text-slate-900 leading-tight">{user.full_name}</p>
                  <p className="text-[11px] text-slate-500 leading-tight">
                    {profile?.target_curriculum_code ? `${profile.target_curriculum_code} Student` : 'Student'}
                  </p>
                </div>
              </div>

              {onOpenLessons && (
                <button
                  onClick={onOpenLessons}
                  className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200 transition-colors"
                  title="Browse Lessons"
                >
                  <BookOpen className="w-3.5 h-3.5 text-brand-600" />
                  <span>Lessons</span>
                </button>
              )}

              <button
                onClick={onOpenOnboarding}
                className="hidden lg:inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
                title="Curriculum Setup"
              >
                <Compass className="w-3.5 h-3.5 text-brand-600" />
                <span>Curriculum</span>
              </button>

              <button
                onClick={handleLogout}
                disabled={isLoggingOut}
                className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 hover:text-rose-700 hover:bg-rose-50 border border-slate-200 transition-colors"
                title="Sign Out"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Sign Out</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
              {onOpenLessons && (
                <button
                  onClick={onOpenLessons}
                  className="hidden sm:inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200 transition-colors"
                >
                  <BookOpen className="w-3.5 h-3.5 text-brand-600" />
                  <span>Browse Lessons</span>
                </button>
              )}

              <button
                onClick={() => onOpenAuth('signin')}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-slate-700 hover:text-slate-900 hover:bg-slate-100 transition-colors"
              >
                <LogIn className="w-3.5 h-3.5 text-slate-500" />
                <span>Sign In</span>
              </button>

              <button
                onClick={() => onOpenAuth('register')}
                className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 shadow-sm transition-all"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>Create Account</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
