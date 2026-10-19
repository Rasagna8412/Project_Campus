import React, { useState, useEffect, useCallback } from 'react';
import {
  BookOpen,
  Clock,
  Compass,
  GraduationCap,
  Layers,
  Trash2,
  AlertTriangle,
  Loader2,
  PenTool,
  Award,
  Sparkles,
  CheckCircle2,
  Target,
  ArrowRight,
  RotateCcw,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import {
  getDashboardAnalytics,
  getTopicAnalytics,
  getLearningRecommendations,
  updateStudentProfile,
  getDailyStudyPlan,
  generateDailyStudyPlan,
  toggleTaskComplete,
  getStudyGoal,
  updateStudyGoal,
  getCurriculumRoadmap,
  getReviewQueue,
  submitReviewRating,
  getReviewStats,
} from '../../services/api';
import {
  DashboardAnalytics,
  LearningRecommendation,
  TopicPerformance,
} from '../../types/progress';
import {
  DailyStudyPlan,
  StudyGoal,
  CurriculumRoadmap,
  StudyGoalPayload,
} from '../../types/planner';
import {
  ReviewItemSummary,
  ReviewQueueResponse,
  ReviewStatsResponse,
} from '../../types/repetition';
import { DailyStudyPlanCard } from '../planner/DailyStudyPlanCard';
import { StudyGoalModal } from '../planner/StudyGoalModal';
import { CurriculumRoadmapCard } from '../planner/CurriculumRoadmapCard';
import { DailyReviewQueueCard } from '../review/DailyReviewQueueCard';
import { FlashcardReviewModal } from '../review/FlashcardReviewModal';

interface StudentDashboardProps {
  onOpenOnboarding: () => void;
  onOpenLessons: () => void;
  onSelectLesson?: (lessonId: string) => void;
  onStartPractice?: (topicId: string, topicTitle?: string) => void;
}

export const StudentDashboard: React.FC<StudentDashboardProps> = ({
  onOpenOnboarding,
  onOpenLessons,
  onSelectLesson,
  onStartPractice,
}) => {
  const { user, profile, refreshProfile, deleteAccount } = useAuth();

  const [isEditingGoal, setIsEditingGoal] = useState<boolean>(false);
  const [newGoalMinutes, setNewGoalMinutes] = useState<number>(
    profile?.daily_study_goal_minutes || 120
  );
  const [isSavingGoal, setIsSavingGoal] = useState<boolean>(false);
  const [isDeletingAccount, setIsDeletingAccount] = useState<boolean>(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<boolean>(false);

  // Analytics states
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null);
  const [topics, setTopics] = useState<TopicPerformance[]>([]);
  const [recommendations, setRecommendations] = useState<LearningRecommendation[]>([]);
  const [loadingAnalytics, setLoadingAnalytics] = useState<boolean>(true);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);

  // Milestone 6 Planner states
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    return new Date().toISOString().split('T')[0];
  });
  const [plan, setPlan] = useState<DailyStudyPlan | null>(null);
  const [goal, setGoal] = useState<StudyGoal | null>(null);
  const [roadmap, setRoadmap] = useState<CurriculumRoadmap | null>(null);
  const [loadingPlan, setLoadingPlan] = useState<boolean>(true);
  const [loadingRoadmap, setLoadingRoadmap] = useState<boolean>(true);
  const [planError, setPlanError] = useState<string | null>(null);
  const [isGoalModalOpen, setIsGoalModalOpen] = useState<boolean>(false);

  const fetchPlan = useCallback(async (date: string, forceGenerate: boolean = false) => {
    setLoadingPlan(true);
    setPlanError(null);
    try {
      const data = forceGenerate
        ? await generateDailyStudyPlan(date)
        : await getDailyStudyPlan(date);
      setPlan(data);
    } catch {
      setPlanError('Failed to load study plan. Please try refreshing.');
    } finally {
      setLoadingPlan(false);
    }
  }, []);

  const fetchGoalAndRoadmap = useCallback(async () => {
    setLoadingRoadmap(true);
    try {
      const [goalData, roadmapData] = await Promise.all([
        getStudyGoal().catch(() => null),
        getCurriculumRoadmap().catch(() => null),
      ]);
      if (goalData) setGoal(goalData);
      if (roadmapData) setRoadmap(roadmapData);
    } catch {
      // Handled gracefully
    } finally {
      setLoadingRoadmap(false);
    }
  }, []);

  useEffect(() => {
    fetchPlan(selectedDate, false);
  }, [fetchPlan, selectedDate]);

  useEffect(() => {
    fetchGoalAndRoadmap();
  }, [fetchGoalAndRoadmap]);

  // Milestone 7 Spaced Repetition states
  const [reviewQueue, setReviewQueue] = useState<ReviewQueueResponse | null>(null);
  const [reviewStats, setReviewStats] = useState<ReviewStatsResponse | null>(null);
  const [loadingReview, setLoadingReview] = useState<boolean>(true);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [activeReviewItem, setActiveReviewItem] = useState<ReviewItemSummary | null>(null);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState<boolean>(false);

  const fetchReviewData = useCallback(async () => {
    setLoadingReview(true);
    setReviewError(null);
    try {
      const [queueData, statsData] = await Promise.all([
        getReviewQueue().catch((e) => {
          throw e;
        }),
        getReviewStats().catch(() => null),
      ]);
      setReviewQueue(queueData);
      if (statsData) setReviewStats(statsData);
    } catch {
      setReviewError('Failed to load spaced repetition review queue.');
    } finally {
      setLoadingReview(false);
    }
  }, []);

  useEffect(() => {
    fetchReviewData();
  }, [fetchReviewData]);

  const handleStartReview = (item: ReviewItemSummary) => {
    setActiveReviewItem(item);
    setIsReviewModalOpen(true);
  };

  const handleSubmitReviewRating = async (itemId: string, score: number, timeSpent: number) => {
    await submitReviewRating(itemId, score, timeSpent);
    await Promise.all([
      fetchReviewData(),
      fetchPlan(selectedDate, false),
    ]);
  };

  const handleToggleTaskComplete = async (taskId: string, isCompleted: boolean) => {
    try {
      const updatedTask = await toggleTaskComplete(taskId, isCompleted);
      setPlan((prev) => {
        if (!prev) return null;
        const updatedTasks = prev.tasks.map((t) => (t.id === taskId ? updatedTask : t));
        const completedMins = updatedTasks
          .filter((t) => t.is_completed)
          .reduce((sum, t) => sum + t.estimated_minutes, 0);
        const plannedMins = updatedTasks.reduce((sum, t) => sum + t.estimated_minutes, 0);
        return {
          ...prev,
          tasks: updatedTasks,
          completed_minutes: completedMins,
          planned_minutes: plannedMins,
          is_fully_completed: updatedTasks.length > 0 && updatedTasks.every((t) => t.is_completed),
        };
      });
    } catch {
      fetchPlan(selectedDate, false);
    }
  };

  const handleSaveGoal = async (payload: StudyGoalPayload) => {
    const updated = await updateStudyGoal(payload);
    setGoal(updated);
    setNewGoalMinutes(payload.daily_study_minutes);
    await refreshProfile();
    fetchPlan(selectedDate, true);
  };

  const fetchAnalytics = useCallback(async () => {
    setLoadingAnalytics(true);
    setAnalyticsError(null);
    try {
      const [dashData, topicData, recData] = await Promise.all([
        getDashboardAnalytics ? Promise.resolve(getDashboardAnalytics()) : null,
        getTopicAnalytics ? Promise.resolve(getTopicAnalytics()) : [],
        getLearningRecommendations ? Promise.resolve(getLearningRecommendations()) : [],
      ]);
      if (dashData && typeof dashData === 'object') {
        setAnalytics(dashData);
      }
      if (Array.isArray(topicData)) {
        setTopics(topicData);
      }
      if (Array.isArray(recData)) {
        setRecommendations(recData);
      }
    } catch {
      setAnalyticsError('Failed to load real-time analytics. Please try refreshing.');
    } finally {
      setLoadingAnalytics(false);
    }
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const handleUpdateGoal = async () => {
    setIsSavingGoal(true);
    try {
      await updateStudentProfile({ daily_study_goal_minutes: newGoalMinutes });
      await refreshProfile();
      setIsEditingGoal(false);
    } catch {
      // Handled
    } finally {
      setIsSavingGoal(false);
    }
  };

  const handleDeleteAccount = async () => {
    setIsDeletingAccount(true);
    try {
      await deleteAccount();
    } catch {
      // Handled
    } finally {
      setIsDeletingAccount(false);
    }
  };

  if (!user) return null;

  const isOnboardingIncomplete = !profile?.onboarding_completed;
  const isFreshStudent =
    !loadingAnalytics &&
    analytics &&
    analytics.total_questions_answered === 0 &&
    analytics.lessons_completed_count === 0;

  // Format practice seconds into human-readable duration
  const formatPracticeTime = (seconds: number): string => {
    if (!seconds || seconds <= 0) return '0m';
    const mins = Math.floor(seconds / 60);
    const hrs = Math.floor(mins / 60);
    const remMins = mins % 60;
    if (hrs > 0) {
      return `${hrs}h ${remMins}m`;
    }
    return `${mins}m`;
  };

  const renderStatusBadge = (category: string) => {
    switch (category) {
      case 'STRONG':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            <span>Strong Grasp</span>
          </span>
        );
      case 'DEVELOPING':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3 h-3 text-amber-600" />
            <span>Developing</span>
          </span>
        );
      case 'NEEDS_REVIEW':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">
            <RotateCcw className="w-3 h-3 text-rose-600" />
            <span>Needs Revision</span>
          </span>
        );
      case 'INSUFFICIENT_DATA':
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
            <span>Getting Started (&lt;5 Qs)</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Student Welcome Banner */}
      <div className="bg-gradient-to-r from-brand-900 via-brand-800 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-lg border border-brand-700/50">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-brand-300 uppercase tracking-wider mb-2">
              <GraduationCap className="w-4 h-4 text-brand-400" />
              <span>Student Academic Workspace</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Welcome, {user.full_name}
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1">
              Account: <span className="font-mono text-brand-200">{user.email}</span> • Status:{' '}
              <span className="text-emerald-400 font-semibold">Active Learner</span>
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={onOpenLessons}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold bg-brand-500 hover:bg-brand-400 text-white shadow-md transition-all"
            >
              <BookOpen className="w-4 h-4" />
              <span>Browse Curriculum Lessons</span>
            </button>

            <button
              onClick={onOpenOnboarding}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold bg-white text-slate-900 hover:bg-slate-100 shadow-md transition-all"
            >
              <Compass className="w-4 h-4 text-brand-600" />
              <span>{isOnboardingIncomplete ? 'Resume Setup' : 'Edit Curriculum Setup'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Incomplete Onboarding Alert Banner */}
      {isOnboardingIncomplete && (
        <div
          className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-xs text-amber-900 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4"
          role="alert"
        >
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-bold text-sm text-amber-950">Academic Onboarding Incomplete</h3>
              <p className="mt-0.5 text-amber-800 leading-relaxed">
                Your target curriculum and subject choices have been saved as draft. Complete your academic setup to finalize your personalized curriculum view.
              </p>
            </div>
          </div>
          <button
            onClick={onOpenOnboarding}
            className="px-4 py-2 rounded-lg text-xs font-bold bg-amber-600 text-white hover:bg-amber-700 shadow-sm transition-colors whitespace-nowrap self-start sm:self-auto"
          >
            Resume Onboarding Now
          </button>
        </div>
      )}

      {/* Analytics Fetch Error Banner */}
      {analyticsError && (
        <div
          className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-900 shadow-sm flex items-center justify-between"
          role="alert"
        >
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{analyticsError}</span>
          </div>
          <button
            onClick={fetchAnalytics}
            className="px-3 py-1 bg-white hover:bg-slate-50 border border-rose-300 rounded text-rose-700 font-bold text-xs transition-colors"
          >
            Retry Analytics
          </button>
        </div>
      )}

      {/* Analytics KPI Bar */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Card 1: Lessons Completed */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-bold uppercase tracking-wider mb-2">
            <span>Lessons Completed</span>
            <BookOpen className="w-4 h-4 text-brand-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">
            {loadingAnalytics ? (
              <div className="h-7 w-12 bg-slate-200 animate-pulse rounded"></div>
            ) : (
              analytics?.lessons_completed_count ?? 0
            )}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            {analytics?.lessons_in_progress_count ? `${analytics.lessons_in_progress_count} in progress` : 'Self-paced syllabus study'}
          </p>
        </div>

        {/* Card 2: Practice Sessions */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-bold uppercase tracking-wider mb-2">
            <span>Practice Drills</span>
            <Award className="w-4 h-4 text-brand-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">
            {loadingAnalytics ? (
              <div className="h-7 w-12 bg-slate-200 animate-pulse rounded"></div>
            ) : (
              analytics?.practice_sessions_completed_count ?? 0
            )}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Topic drill sessions finished</p>
        </div>

        {/* Card 3: Questions Answered */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-bold uppercase tracking-wider mb-2">
            <span>Questions Solved</span>
            <PenTool className="w-4 h-4 text-brand-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">
            {loadingAnalytics ? (
              <div className="h-7 w-12 bg-slate-200 animate-pulse rounded"></div>
            ) : (
              analytics?.total_questions_answered ?? 0
            )}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            {analytics?.total_correct_answers ? `${analytics.total_correct_answers} correct answers` : 'Deliberate practice attempts'}
          </p>
        </div>

        {/* Card 4: Observed Practice Accuracy */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-bold uppercase tracking-wider mb-2">
            <span>Observed Accuracy</span>
            <Target className="w-4 h-4 text-brand-600" />
          </div>
          <div className="text-2xl font-black">
            {loadingAnalytics ? (
              <div className="h-7 w-16 bg-slate-200 animate-pulse rounded"></div>
            ) : analytics?.overall_accuracy_percentage !== null && analytics?.overall_accuracy_percentage !== undefined ? (
              <span
                className={
                  analytics.overall_accuracy_percentage >= 75
                    ? 'text-emerald-600'
                    : analytics.overall_accuracy_percentage >= 50
                    ? 'text-amber-600'
                    : 'text-rose-600'
                }
              >
                {analytics.overall_accuracy_percentage}%
              </span>
            ) : (
              <span className="text-slate-400 text-lg font-bold">No attempts</span>
            )}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            {analytics?.overall_accuracy_percentage !== null ? 'Cumulative accepted accuracy' : 'Solve questions to evaluate'}
          </p>
        </div>

        {/* Card 5: Estimated Practice Time */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-bold uppercase tracking-wider mb-2">
            <span>Practice Time</span>
            <Clock className="w-4 h-4 text-brand-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">
            {loadingAnalytics ? (
              <div className="h-7 w-16 bg-slate-200 animate-pulse rounded"></div>
            ) : (
              formatPracticeTime(analytics?.total_practice_time_seconds || 0)
            )}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Estimated active practice</p>
        </div>
      </div>

      {/* Daily Study Plan Card (Approved Milestone 6 Dashboard Placement) */}
      <DailyStudyPlanCard
        plan={plan}
        loading={loadingPlan}
        error={planError}
        onRefresh={(force) => fetchPlan(selectedDate, force)}
        onToggleComplete={handleToggleTaskComplete}
        onSelectLesson={onSelectLesson}
        onStartPractice={onStartPractice}
        onOpenGoalModal={() => setIsGoalModalOpen(true)}
        selectedDate={selectedDate}
        onDateChange={setSelectedDate}
      />

      {/* Spaced Repetition & Revision Queue (Milestone 7) */}
      <DailyReviewQueueCard
        queue={reviewQueue}
        stats={reviewStats}
        loading={loadingReview}
        error={reviewError}
        onRefresh={fetchReviewData}
        onStartReview={handleStartReview}
        onStartPractice={onStartPractice}
      />

      {/* Curriculum Roadmap Card */}
      <CurriculumRoadmapCard
        roadmap={roadmap}
        loading={loadingRoadmap}
        onOpenLessons={onOpenLessons}
      />

      {/* Fresh Student Onboarding Empty State */}
      {isFreshStudent && (
        <div className="bg-gradient-to-r from-brand-50 via-indigo-50 to-white rounded-2xl border border-brand-200 p-6 sm:p-8 shadow-sm text-center">
          <div className="w-12 h-12 bg-brand-600 text-white rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-md">
            <Sparkles className="w-6 h-6 text-brand-200" />
          </div>
          <h2 className="text-lg sm:text-xl font-extrabold text-slate-900">
            Welcome to Your Academic Learning Dashboard
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 max-w-lg mx-auto mt-2 leading-relaxed">
            As you read curriculum lessons and solve targeted question sets, your actual observed accuracy, topic mastery breakdown, and personalized recommendations will update here in real-time.
          </p>
          <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={onOpenLessons}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white shadow-md transition-all"
            >
              <BookOpen className="w-4 h-4" />
              <span>Start Your First Lesson</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={onOpenOnboarding}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 shadow-sm transition-all"
            >
              <Compass className="w-4 h-4 text-brand-600" />
              <span>Review Enrolled Subjects</span>
            </button>
          </div>
        </div>
      )}

      {/* Recommended Next Steps */}
      {recommendations.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-brand-700 mb-4 pb-2 border-b border-slate-100">
            <Sparkles className="w-4 h-4 text-brand-600" />
            <span>Recommended Next Learning Actions</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-slate-200 p-4 hover:border-brand-300 hover:shadow-md transition-all flex flex-col justify-between bg-slate-50/50"
              >
                <div>
                  <div className="flex items-center justify-between text-xs font-bold text-slate-500 mb-1">
                    <span className="text-brand-600 uppercase tracking-wider text-[10px]">
                      {rec.subject_name || 'Academic'}
                    </span>
                    <span className="text-[10px] bg-white px-2 py-0.5 rounded border border-slate-200">
                      Step {rec.priority}
                    </span>
                  </div>
                  <div className="text-xs font-bold text-brand-700">{rec.title}</div>
                  <h4 className="font-bold text-sm text-slate-900 leading-snug mt-0.5">
                    {rec.target_title}
                  </h4>
                  <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                    {rec.reason}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-200/60">
                  <button
                    onClick={() => {
                      if (rec.type === 'RESUME_LESSON' || rec.type === 'NEXT_LESSON') {
                        if (onSelectLesson) {
                          onSelectLesson(rec.target_id);
                        } else {
                          onOpenLessons();
                        }
                      } else if (rec.type === 'REVISE_TOPIC' || rec.type === 'PRACTICE_TOPIC') {
                        if (onStartPractice) {
                          onStartPractice(rec.target_id, rec.target_title);
                        } else {
                          onOpenLessons();
                        }
                      }
                    }}
                    className="w-full inline-flex items-center justify-center space-x-1.5 px-3 py-2 bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs rounded-lg shadow-sm transition-all"
                  >
                    <span>{rec.action_label}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Topic Practice Performance Matrix */}
      {topics.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
            <div>
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-brand-700">
                <Target className="w-4 h-4 text-brand-600" />
                <span>Topic-Level Practice Performance</span>
              </div>
              <h3 className="text-base font-bold text-slate-900 mt-0.5">
                Observed Conceptual Accuracy & Practice Evidence
              </h3>
            </div>
            <button
              onClick={fetchAnalytics}
              disabled={loadingAnalytics}
              className="inline-flex items-center space-x-1 px-2.5 py-1 text-xs font-semibold text-slate-600 hover:text-brand-600 rounded border border-slate-200 hover:bg-slate-50 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingAnalytics ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Topic & Subject</th>
                  <th className="py-3 px-4">Attempts</th>
                  <th className="py-3 px-4">Observed Accuracy</th>
                  <th className="py-3 px-4">Observed Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {topics.map((t) => (
                  <tr key={t.topic_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="font-bold text-slate-900 text-sm">{t.topic_title}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        {t.subject_name} • {t.chapter_title}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-700">
                      {t.total_attempts} questions ({t.correct_attempts} correct)
                    </td>
                    <td className="py-3.5 px-4 font-bold">
                      {t.observed_accuracy_percentage !== null ? (
                        <span
                          className={
                            t.observed_accuracy_percentage >= 80
                              ? 'text-emerald-700'
                              : t.observed_accuracy_percentage >= 60
                              ? 'text-amber-700'
                              : 'text-rose-700'
                          }
                        >
                          {t.observed_accuracy_percentage}%
                        </span>
                      ) : (
                        <span className="text-slate-400 font-normal">—</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      {renderStatusBadge(t.status_category)}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      {onStartPractice && (
                        <button
                          onClick={() => onStartPractice(t.topic_id, t.topic_title)}
                          className="inline-flex items-center space-x-1 px-3 py-1 rounded-lg text-xs font-bold text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200 transition-colors"
                        >
                          <PenTool className="w-3 h-3 text-brand-600" />
                          <span>Practise</span>
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recent Learning Activity Feed */}
      {Boolean(analytics?.recent_activity?.length) && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-brand-700 mb-3 pb-2 border-b border-slate-100">
            <Award className="w-4 h-4 text-brand-600" />
            <span>Recent Learning Activity</span>
          </div>

          <div className="divide-y divide-slate-100">
            {analytics?.recent_activity?.map((act) => (
              <div
                key={act.id}
                className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2"
              >
                <div className="flex items-start space-x-3">
                  <div className="mt-0.5 p-1.5 rounded-lg bg-slate-100 text-slate-600 flex-shrink-0">
                    {act.activity_type === 'LESSON_COMPLETED' ? (
                      <BookOpen className="w-4 h-4 text-emerald-600" />
                    ) : (
                      <PenTool className="w-4 h-4 text-brand-600" />
                    )}
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-slate-900 leading-snug">
                      {act.title}
                    </h4>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {act.subject_name ? `${act.subject_name} • ` : ''}
                      {act.subtitle}
                    </p>
                  </div>
                </div>

                <div className="text-xs text-slate-400 self-start sm:self-auto font-mono">
                  {new Date(act.timestamp).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Profile Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1: Target Board & Stage */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-brand-700 mb-3">
            <Layers className="w-4 h-4 text-brand-600" />
            <span>Target Curriculum & Stage</span>
          </div>

          <div className="space-y-3">
            <div>
              <span className="text-xs text-slate-400">Board / Examination</span>
              <p className="text-sm font-bold text-slate-900">
                {profile?.target_curriculum_name || (
                  <span className="text-slate-400 italic">Not yet selected</span>
                )}
              </p>
            </div>

            <div>
              <span className="text-xs text-slate-400">Academic Grade Stage</span>
              <p className="text-sm font-bold text-slate-900">
                {profile?.grade_stage_name || (
                  <span className="text-slate-400 italic">Not yet selected</span>
                )}
              </p>
            </div>

            <div>
              <span className="text-xs text-slate-400">Target Exam Year</span>
              <p className="text-sm font-bold text-slate-900">
                {profile?.target_exam_year ? `${profile.target_exam_year} Session` : 'Not set'}
              </p>
            </div>
          </div>
        </div>

        {/* Card 2: Enrolled Subjects */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-brand-700 mb-3">
            <BookOpen className="w-4 h-4 text-brand-600" />
            <span>Enrolled Subjects ({profile?.selected_subjects?.length || 0})</span>
          </div>

          {profile?.selected_subjects && profile.selected_subjects.length > 0 ? (
            <div className="flex flex-wrap gap-2 pt-1">
              {profile.selected_subjects.map((sub) => (
                <span
                  key={sub.id}
                  className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-brand-50 text-brand-800 border border-brand-200"
                >
                  <BookOpen className="w-3.5 h-3.5 text-brand-600" />
                  <span>{sub.name}</span>
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">
              No subjects enrolled yet. Complete onboarding to select your subjects.
            </p>
          )}
        </div>

        {/* Card 3: Daily Study Goal & Commitment */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-brand-700">
              <Clock className="w-4 h-4 text-brand-600" />
              <span>Daily Study Target</span>
            </div>
            {!isEditingGoal && (
              <button
                onClick={() => setIsEditingGoal(true)}
                className="text-xs font-semibold text-brand-600 hover:text-brand-800"
              >
                Adjust
              </button>
            )}
          </div>

          {!isEditingGoal ? (
            <div>
              <div className="text-2xl font-extrabold text-slate-900">
                {profile?.daily_study_goal_minutes || 120} Min
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Equivalent to {Math.floor((profile?.daily_study_goal_minutes || 120) / 60)} hours per day of focused deliberate practice.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-bold text-slate-800">
                <span>{newGoalMinutes} Minutes</span>
                <span>({Math.floor(newGoalMinutes / 60)}h {newGoalMinutes % 60}m)</span>
              </div>
              <input
                type="range"
                min="30"
                max="360"
                step="15"
                value={newGoalMinutes}
                onChange={(e) => setNewGoalMinutes(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-brand-600"
              />
              <div className="flex items-center space-x-2 pt-1">
                <button
                  onClick={handleUpdateGoal}
                  disabled={isSavingGoal}
                  className="px-3 py-1 rounded-lg text-xs font-bold bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50 flex items-center space-x-1"
                >
                  {isSavingGoal && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save</span>
                </button>
                <button
                  onClick={() => setIsEditingGoal(false)}
                  className="px-3 py-1 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Privacy and Account Rights Card (DPDP Act Compliance) */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Student Privacy & Account Rights</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              In accordance with India&apos;s Digital Personal Data Protection Act (DPDP Act 2023), you hold the right to complete erasure of your academic records.
            </p>
          </div>

          {!showDeleteConfirm ? (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-rose-700 hover:bg-rose-50 border border-rose-200 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5 text-rose-600" />
              <span>Delete Account</span>
            </button>
          ) : (
            <div className="flex items-center space-x-2">
              <span className="text-xs text-rose-700 font-semibold">Permanently delete?</span>
              <button
                onClick={handleDeleteAccount}
                disabled={isDeletingAccount}
                className="px-3 py-1.5 rounded-lg text-xs font-bold bg-rose-600 text-white hover:bg-rose-700 disabled:opacity-50 flex items-center space-x-1"
              >
                {isDeletingAccount && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Yes, Erase Everything</span>
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100 border border-slate-200"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Study Goal Configuration Modal */}
      <StudyGoalModal
        goal={goal}
        isOpen={isGoalModalOpen}
        onClose={() => setIsGoalModalOpen(false)}
        onSave={handleSaveGoal}
      />

      {/* Spaced Repetition Active Recall Modal (Milestone 7) */}
      <FlashcardReviewModal
        item={activeReviewItem}
        isOpen={isReviewModalOpen}
        onClose={() => {
          setIsReviewModalOpen(false);
          setActiveReviewItem(null);
        }}
        onSubmitRating={handleSubmitReviewRating}
        onStartPractice={onStartPractice}
      />
    </div>
  );
};
