import React from 'react';
import { Activity, CheckCircle2, AlertTriangle, RefreshCw, GraduationCap, XCircle } from 'lucide-react';
import { HealthResponse, ConnectionState } from '../../types/api';

interface HeaderProps {
  connectionState: ConnectionState;
  healthData: HealthResponse | null;
  errorMessage: string | null;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  connectionState,
  healthData,
  errorMessage,
  onRefresh,
  isRefreshing,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/95 backdrop-blur shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand identity */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-brand-600 to-brand-800 flex items-center justify-center text-white shadow-md">
            <GraduationCap className="w-6 h-6" aria-hidden="true" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-tight text-slate-900">Project Campus</span>
              <span className="text-xs px-2 py-0.5 rounded-full font-semibold bg-brand-50 text-brand-700 border border-brand-200">
                Milestone 1 Core
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium">Academic Learning & Examination Platform</p>
          </div>
        </div>

        {/* Live System Health Badge */}
        <div className="flex items-center space-x-3">
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
            {connectionState === 'connected' && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
            {connectionState === 'checking' && <Activity className="w-4 h-4 text-blue-600 animate-spin" />}
            {connectionState === 'disconnected' && <XCircle className="w-4 h-4 text-rose-600" />}
            {connectionState === 'error' && <AlertTriangle className="w-4 h-4 text-amber-600" />}

            <span>
              {connectionState === 'connected' && `Backend v${healthData?.version} • DB Connected`}
              {connectionState === 'checking' && 'Connecting to API...'}
              {connectionState === 'disconnected' && 'Backend Offline'}
              {connectionState === 'error' && (errorMessage || 'Connection Degraded')}
            </span>
          </div>

          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 border border-slate-200 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:opacity-50"
            title="Refresh API Connection"
            aria-label="Refresh Backend Connectivity Status"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-brand-600' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
