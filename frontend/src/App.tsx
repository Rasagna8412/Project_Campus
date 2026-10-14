import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/common/Header';
import { Footer } from './components/common/Footer';
import { MathSnippet } from './components/common/MathSnippet';
import { CurriculumFoundation } from './components/common/CurriculumFoundation';
import { MilestoneRoadmap } from './components/common/MilestoneRoadmap';
import { checkBackendHealth } from './services/api';
import { HealthResponse, ConnectionState } from './types/api';
import { Server, Cpu, Database, AlertCircle, RefreshCw, CheckCircle2 } from 'lucide-react';

export const App: React.FC = () => {
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>('checking');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [lastCheckedAt, setLastCheckedAt] = useState<Date | null>(null);

  const fetchHealth = useCallback(async () => {
    setIsRefreshing(true);
    setConnectionState('checking');
    setErrorMessage(null);

    try {
      const data = await checkBackendHealth(true);
      setHealthData(data);
      if (data.status === 'healthy') {
        setConnectionState('connected');
      } else {
        setConnectionState('error');
        setErrorMessage(data.database ? `Database ${data.database}` : 'Degraded service');
      }
    } catch (err: unknown) {
      setConnectionState('disconnected');
      setHealthData(null);
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to connect to backend server');
      }
    } finally {
      setIsRefreshing(false);
      setLastCheckedAt(new Date());
    }
  }, []);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 font-sans">
      <Header
        connectionState={connectionState}
        healthData={healthData}
        errorMessage={errorMessage}
        onRefresh={fetchHealth}
        isRefreshing={isRefreshing}
      />

      <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full space-y-8">
        {/* Welcome & System Status Hero Banner */}
        <div className="bg-gradient-to-r from-slate-900 via-brand-950 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-lg border border-slate-800">
          <div className="max-w-3xl">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-brand-500/20 text-brand-300 border border-brand-500/30 mb-4">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Milestone 1 Architecture Active</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Project Campus
            </h1>
            <p className="mt-2 text-sm sm:text-base text-slate-300 leading-relaxed">
              A high-precision educational platform built for secondary and competitive exam preparation (CBSE, JEE Main, NEET). 
              Currently deployed with core application scaffolding, live async database connectivity, and verified mathematical typesetting.
            </p>
          </div>

          {/* Real-time Diagnostics Grid */}
          <div className="mt-6 pt-6 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="flex items-center space-x-3 p-3 rounded-xl bg-white/5 border border-white/10">
              <Server className="w-5 h-5 text-brand-400" />
              <div>
                <p className="text-slate-400 font-medium">FastAPI Backend</p>
                <p className="font-bold text-white mt-0.5">
                  {connectionState === 'connected' ? `v${healthData?.version} • Online` : 'Offline / Unreachable'}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-3 rounded-xl bg-white/5 border border-white/10">
              <Database className="w-5 h-5 text-brand-400" />
              <div>
                <p className="text-slate-400 font-medium">Database Storage</p>
                <p className="font-bold text-white mt-0.5">
                  {connectionState === 'connected' ? 'SQLite (Async) / Migrated' : 'Disconnected'}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-3 rounded-xl bg-white/5 border border-white/10">
              <Cpu className="w-5 h-5 text-brand-400" />
              <div>
                <p className="text-slate-400 font-medium">Math Typography</p>
                <p className="font-bold text-white mt-0.5">KaTeX 0.16 Client Engine</p>
              </div>
            </div>
          </div>
        </div>

        {/* Backend Unavailable Warning Box (conditional) */}
        {connectionState === 'disconnected' && (
          <div
            className="rounded-xl border border-rose-200 bg-rose-50 p-5 shadow-sm text-xs text-rose-900"
            role="alert"
          >
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-rose-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="font-bold text-sm text-rose-950">Backend Server Unreachable</h3>
                <p className="mt-1 text-rose-800">
                  {errorMessage || 'Unable to connect to http://127.0.0.1:8000/health.'}
                </p>
                <div className="mt-3 bg-white/80 p-3 rounded-lg border border-rose-200 font-mono text-[11px] text-slate-800">
                  <p className="text-slate-600 font-sans mb-1 font-semibold">Start the backend development server using:</p>
                  <code>uvicorn app.main:app --reload --port 8000</code>
                </div>
                <button
                  onClick={fetchHealth}
                  disabled={isRefreshing}
                  className="mt-3 inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-rose-600 text-white font-semibold hover:bg-rose-700 transition-colors shadow-sm disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
                  <span>Retry Live Ping</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Live Backend Connection Details (when connected) */}
        {connectionState === 'connected' && healthData && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-4 shadow-sm flex items-center justify-between text-xs text-emerald-900">
            <div className="flex items-center space-x-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
              <div>
                <span className="font-bold text-emerald-950">Backend API Connectivity Verified:</span>
                <span className="ml-1 text-emerald-800">
                  `GET /health` returned HTTP 200 with status &quot;{healthData.status}&quot; and database connectivity confirmed.
                </span>
              </div>
            </div>
            {lastCheckedAt && (
              <span className="text-[11px] text-emerald-700 hidden sm:inline">
                Last checked: {lastCheckedAt.toLocaleTimeString()}
              </span>
            )}
          </div>
        )}

        {/* Mathematical Typesetting Showcase */}
        <div>
          <div className="mb-3">
            <h2 className="text-base font-bold text-slate-900">Verified Mathematical Typesetting Engine</h2>
            <p className="text-xs text-slate-600">
              Rendered client-side via KaTeX with zero latency to guarantee readable physics and chemistry formulas:
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MathSnippet
              label="Electrostatics"
              context="CBSE 12 / JEE Physics"
              formula="\vec{F} = \frac{1}{4\pi\varepsilon_0} \frac{q_1 q_2}{r^2} \hat{r}"
            />
            <MathSnippet
              label="Special Relativity"
              context="Modern Physics"
              formula="E = \sqrt{(pc)^2 + (m_0 c^2)^2}"
            />
            <MathSnippet
              label="Calculus"
              context="JEE Mathematics"
              formula="\int_{-\infty}^{\infty} e^{-x^2} \, dx = \sqrt{\pi}"
            />
          </div>
        </div>

        {/* Curriculum Taxonomy Foundation */}
        <CurriculumFoundation />

        {/* Milestone Implementation Roadmap */}
        <MilestoneRoadmap />
      </main>

      <Footer />
    </div>
  );
};
export default App;
