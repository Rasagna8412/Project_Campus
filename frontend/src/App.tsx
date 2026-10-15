import React, { useState, useEffect, useCallback } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Header } from './components/common/Header';
import { Footer } from './components/common/Footer';
import { MathSnippet } from './components/common/MathSnippet';
import { CurriculumFoundation } from './components/common/CurriculumFoundation';
import { MilestoneRoadmap } from './components/common/MilestoneRoadmap';
import { AuthModal } from './components/auth/AuthModal';
import { OnboardingWizard } from './components/onboarding/OnboardingWizard';
import { StudentDashboard } from './components/dashboard/StudentDashboard';
import { CurriculumBrowser } from './components/curriculum/CurriculumBrowser';
import { LessonViewer, BreadcrumbItem } from './components/curriculum/LessonViewer';
import { PracticeModal } from './components/practice/PracticeModal';
import { checkBackendHealth } from './services/api';
import { HealthResponse, ConnectionState } from './types/api';
import {
  Server,
  Cpu,
  Database,
  AlertCircle,
  RefreshCw,
  ArrowRight,
  ShieldCheck,
  UserPlus,
  BookOpen,
} from 'lucide-react';

const AppContent: React.FC = () => {
  const { user, profile, isAuthenticated } = useAuth();

  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>('checking');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  // View States
  const [activeView, setActiveView] = useState<'home' | 'lessons'>('home');
  const [currentLessonId, setCurrentLessonId] = useState<string | null>(null);
  const [lessonBreadcrumbs, setLessonBreadcrumbs] = useState<BreadcrumbItem[]>([]);
  const [activePracticeTopic, setActivePracticeTopic] = useState<{
    topicId: string;
    topicTitle?: string;
  } | null>(null);

  // Modal and Onboarding View States
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [authModalMode, setAuthModalMode] = useState<'signin' | 'register'>('signin');
  const [isOnboardingOpen, setIsOnboardingOpen] = useState<boolean>(false);

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
    }
  }, []);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  const handleOpenAuth = (mode: 'signin' | 'register') => {
    setAuthModalMode(mode);
    setIsAuthModalOpen(true);
  };

  const handleOpenLessons = () => {
    setActiveView('lessons');
    setCurrentLessonId(null);
    setIsOnboardingOpen(false);
  };

  const handleOpenHome = () => {
    setActiveView('home');
    setCurrentLessonId(null);
    setIsOnboardingOpen(false);
  };

  const handleSelectLesson = (lessonId: string, breadcrumbs: BreadcrumbItem[]) => {
    setCurrentLessonId(lessonId);
    setLessonBreadcrumbs(breadcrumbs);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 font-sans">
      <Header
        connectionState={connectionState}
        healthData={healthData}
        errorMessage={errorMessage}
        onRefresh={fetchHealth}
        isRefreshing={isRefreshing}
        onOpenAuth={handleOpenAuth}
        onOpenOnboarding={() => setIsOnboardingOpen(true)}
        onOpenLessons={handleOpenLessons}
        onOpenHome={handleOpenHome}
      />

      <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full space-y-8">
        {/* Backend Unavailable Warning Box */}
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
                  <code>python scripts/run_backend.py</code>
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

        {/* 1. If viewing a specific lesson, show LessonViewer */}
        {currentLessonId ? (
          <LessonViewer
            lessonId={currentLessonId}
            onBack={() => setCurrentLessonId(null)}
            breadcrumbs={lessonBreadcrumbs}
            onStartPractice={(topicId, title) =>
              setActivePracticeTopic({ topicId, topicTitle: title })
            }
          />
        ) : activeView === 'lessons' ? (
          /* 2. If browsing lessons, show CurriculumBrowser */
          <div>
            <div className="mb-4">
              <button
                onClick={handleOpenHome}
                className="text-xs font-semibold text-slate-500 hover:text-brand-600 flex items-center space-x-1"
              >
                <span>← Back to {isAuthenticated ? 'Dashboard' : 'Home'}</span>
              </button>
            </div>
            <CurriculumBrowser
              onSelectLesson={handleSelectLesson}
              onStartPractice={(topicId, title) =>
                setActivePracticeTopic({ topicId, topicTitle: title })
              }
              initialBoardCode={profile?.target_curriculum_code || undefined}
              initialGradeCode={profile?.grade_stage_code || undefined}
            />
          </div>
        ) : isAuthenticated && user ? (
          /* 3. Authenticated Student Dashboard */
          <div>
            {isOnboardingOpen ? (
              <OnboardingWizard
                onCompleted={() => setIsOnboardingOpen(false)}
                onCancel={() => setIsOnboardingOpen(false)}
              />
            ) : (
              <StudentDashboard
                onOpenOnboarding={() => setIsOnboardingOpen(true)}
                onOpenLessons={handleOpenLessons}
                onStartPractice={(topicId, title) =>
                  setActivePracticeTopic({ topicId, topicTitle: title })
                }
              />
            )}
          </div>
        ) : (
          /* 4. Guest Home Experience */
          <div className="space-y-8">
            {/* Hero Banner */}
            <div className="bg-gradient-to-r from-slate-900 via-brand-950 to-slate-900 rounded-2xl p-6 sm:p-10 text-white shadow-xl border border-slate-800">
              <div className="max-w-3xl">
                <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-brand-500/20 text-brand-300 border border-brand-500/30 mb-4">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Verified Curriculum Content & Mathematical Formatting Active</span>
                </div>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight leading-tight">
                  Master High School & Entrance Exam Curricula
                </h1>
                <p className="mt-3 text-sm sm:text-base text-slate-300 leading-relaxed">
                  Engineered for serious learners preparing for CBSE Boards, JEE Main, and NEET. 
                  Experience rigorous syllabus alignment, verified solutions, transparent AI guidance, and individualized revision scheduling.
                </p>

                {/* Primary Guest Call to Actions */}
                <div className="mt-8 flex flex-col sm:flex-row items-center space-y-3 sm:space-y-0 sm:space-x-4">
                  <button
                    onClick={() => handleOpenAuth('register')}
                    className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3 rounded-xl font-bold text-sm bg-brand-600 hover:bg-brand-500 text-white shadow-lg transition-all"
                  >
                    <UserPlus className="w-4 h-4" />
                    <span>Create Student Account</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>

                  <button
                    onClick={handleOpenLessons}
                    className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3 rounded-xl font-bold text-sm bg-white/10 hover:bg-white/15 text-white border border-white/20 transition-all"
                  >
                    <BookOpen className="w-4 h-4" />
                    <span>Browse Structured Lessons</span>
                  </button>

                  <button
                    onClick={() => handleOpenAuth('signin')}
                    className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3 rounded-xl font-bold text-sm bg-white/10 hover:bg-white/15 text-white border border-white/20 transition-all"
                  >
                    <span>Sign In to Existing Account</span>
                  </button>
                </div>
              </div>

              {/* Real-time Diagnostics Grid */}
              <div className="mt-8 pt-6 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div className="flex items-center space-x-3 p-3 rounded-xl bg-white/5 border border-white/10">
                  <Server className="w-5 h-5 text-brand-400" />
                  <div>
                    <p className="text-slate-400 font-medium">FastAPI Backend</p>
                    <p className="font-bold text-white mt-0.5">
                      {connectionState === 'connected' ? `v${healthData?.version} • Online` : 'Offline'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 p-3 rounded-xl bg-white/5 border border-white/10">
                  <Database className="w-5 h-5 text-brand-400" />
                  <div>
                    <p className="text-slate-400 font-medium">Database Persistence</p>
                    <p className="font-bold text-white mt-0.5">
                      {connectionState === 'connected' ? 'SQLite (Async) • Migrated' : 'Disconnected'}
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

            {/* Mathematical Typesetting Engine */}
            <div>
              <div className="mb-3">
                <h2 className="text-base font-bold text-slate-900">Verified Mathematical Typesetting Engine</h2>
                <p className="text-xs text-slate-600">
                  Zero-latency client-side rendering via KaTeX ensuring crystal-clear formulas across all viewports:
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

            {/* Foundational Curriculum Taxonomy */}
            <CurriculumFoundation />

            {/* Implementation Roadmap */}
            <MilestoneRoadmap />
          </div>
        )}
      </main>

      <Footer />

      {/* Authentication Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        initialMode={authModalMode}
      />

      {/* Topic Practice Modal */}
      {activePracticeTopic && (
        <PracticeModal
          topicId={activePracticeTopic.topicId}
          topicTitle={activePracticeTopic.topicTitle}
          isOpen={!!activePracticeTopic}
          onClose={() => setActivePracticeTopic(null)}
          onOpenLessons={handleOpenLessons}
        />
      )}
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
