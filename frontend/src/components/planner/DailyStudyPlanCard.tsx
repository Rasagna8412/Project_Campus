import React, { useState } from 'react';
import {
  Calendar,
  CheckCircle2,
  Circle,
  Clock,
  Sparkles,
  ArrowRight,
  RefreshCw,
  BookOpen,
  Target,
  Sliders,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
} from 'lucide-react';
import { DailyStudyPlan, StudyTask, TaskType } from '../../types/planner';
import { rescheduleTask } from '../../services/api';

interface DailyStudyPlanCardProps {
  plan: DailyStudyPlan | null;
  loading: boolean;
  error: string | null;
  onRefresh: (force?: boolean) => void;
  onToggleComplete: (taskId: string, isCompleted: boolean) => Promise<void>;
  onSelectLesson?: (lessonId: string) => void;
  onStartPractice?: (topicId: string, topicTitle?: string) => void;
  onOpenGoalModal: () => void;
  selectedDate: string;
  onDateChange: (newDate: string) => void;
}

export const DailyStudyPlanCard: React.FC<DailyStudyPlanCardProps> = ({
  plan,
  loading,
  error,
  onRefresh,
  onToggleComplete,
  onSelectLesson,
  onStartPractice,
  onOpenGoalModal,
  selectedDate,
  onDateChange,
}) => {
  const [reschedulingTaskId, setReschedulingTaskId] = useState<string | null>(null);

  const getTaskTypeBadge = (type: TaskType) => {
    switch (type) {
      case 'RESUME_LESSON':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
            <BookOpen className="w-3 h-3" />
            <span>Resume Lesson</span>
          </span>
        );
      case 'STUDY_LESSON':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <BookOpen className="w-3 h-3" />
            <span>Syllabus Lesson</span>
          </span>
        );
      case 'REVISE_TOPIC':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
            <RotateCcw className="w-3 h-3" />
            <span>Revision Drill</span>
          </span>
        );
      case 'PRACTICE_TOPIC':
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
            <Target className="w-3 h-3" />
            <span>Confidence Drill</span>
          </span>
        );
    }
  };

  const handleRescheduleTomorrow = async (task: StudyTask) => {
    try {
      setReschedulingTaskId(task.id);
      const curr = new Date(selectedDate);
      curr.setDate(curr.getDate() + 1);
      const tomorrowStr = curr.toISOString().split('T')[0];
      await rescheduleTask(task.id, tomorrowStr);
      onRefresh(false);
    } catch {
      // Ignored or handled by parent
    } finally {
      setReschedulingTaskId(null);
    }
  };

  const handlePrevDay = () => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() - 1);
    onDateChange(d.toISOString().split('T')[0]);
  };

  const handleNextDay = () => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() + 1);
    onDateChange(d.toISOString().split('T')[0]);
  };

  const handleToday = () => {
    onDateChange(new Date().toISOString().split('T')[0]);
  };

  const todayStr = new Date().toISOString().split('T')[0];
  const isToday = selectedDate === todayStr;

  const completionPct =
    plan && plan.planned_minutes > 0
      ? Math.min(100, Math.round((plan.completed_minutes / plan.planned_minutes) * 100))
      : 0;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Top Header Bar */}
      <div className="p-5 sm:p-6 bg-gradient-to-r from-slate-900 via-brand-900 to-slate-900 text-white">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-brand-300 uppercase tracking-wider mb-1">
              <Calendar className="w-4 h-4 text-brand-400" />
              <span>Today's Learning Roadmap & Study Plan</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black">
              {new Date(selectedDate + 'T00:00:00').toLocaleDateString(undefined, {
                weekday: 'long',
                month: 'short',
                day: 'numeric',
              })}
            </h2>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Date controls */}
            <div className="flex items-center bg-white/10 rounded-xl p-0.5 border border-white/20">
              <button
                onClick={handlePrevDay}
                aria-label="Previous Day"
                className="p-1.5 hover:bg-white/10 text-white rounded-lg transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={handleToday}
                className={`px-2.5 py-1 text-xs font-bold rounded-lg transition-colors ${
                  isToday ? 'bg-white text-slate-900' : 'text-white hover:bg-white/10'
                }`}
              >
                Today
              </button>
              <button
                onClick={handleNextDay}
                aria-label="Next Day"
                className="p-1.5 hover:bg-white/10 text-white rounded-lg transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            <button
              onClick={() => onRefresh(true)}
              disabled={loading}
              title="Regenerate today's tasks"
              className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-xl text-xs font-semibold bg-white/10 hover:bg-white/20 text-white border border-white/20 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </button>

            <button
              onClick={onOpenGoalModal}
              title="Adjust target daily minutes and study days"
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-brand-500 hover:bg-brand-400 text-white shadow transition-all"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Adjust Goal</span>
            </button>
          </div>
        </div>

        {/* Workload Progress Bar */}
        {plan && (
          <div className="mt-5 pt-4 border-t border-white/10">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-slate-300">
                Planned Workload:{' '}
                <strong className="text-white">
                  {plan.completed_minutes}m / {plan.planned_minutes}m
                </strong>{' '}
                completed (Goal: {plan.target_minutes}m)
              </span>
              <span className="font-bold text-emerald-400">{completionPct}% Done</span>
            </div>
            <div className="w-full h-2.5 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-500 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${completionPct}%` }}
              ></div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="p-5 sm:p-6">
        {loading && !plan ? (
          <div className="space-y-3 py-6">
            <div className="h-14 bg-slate-100 animate-pulse rounded-xl"></div>
            <div className="h-14 bg-slate-100 animate-pulse rounded-xl"></div>
            <div className="h-14 bg-slate-100 animate-pulse rounded-xl"></div>
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl border border-rose-200 bg-rose-50 text-xs text-rose-800 flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={() => onRefresh(false)}
              className="px-3 py-1 bg-white hover:bg-slate-50 border border-rose-300 rounded font-bold text-rose-700"
            >
              Retry
            </button>
          </div>
        ) : plan && plan.is_fully_completed && Array.isArray(plan.tasks) && plan.tasks.length > 0 ? (
          <div className="mb-6 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-950 flex items-center space-x-3">
            <Sparkles className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <div>
              <h4 className="font-bold text-sm">All Daily Tasks Completed! 🎉</h4>
              <p className="text-xs text-emerald-800 mt-0.5">
                Outstanding dedication! You have achieved your daily study plan. Feel free to browse additional lessons or review weak topics below.
              </p>
            </div>
          </div>
        ) : null}

        {/* Task List */}
        {plan && Array.isArray(plan.tasks) && plan.tasks.length > 0 ? (
          <div className="space-y-3">
            {plan.tasks.map((task) => (
              <div
                key={task.id}
                className={`p-4 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                  task.is_completed
                    ? 'bg-slate-50 border-slate-200 opacity-75'
                    : 'bg-white border-slate-200 hover:border-brand-300 hover:shadow-sm'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <button
                    onClick={() => onToggleComplete(task.id, !task.is_completed)}
                    aria-label={task.is_completed ? 'Mark as incomplete' : 'Mark as complete'}
                    className="mt-0.5 text-slate-400 hover:text-emerald-600 transition-colors flex-shrink-0"
                  >
                    {task.is_completed ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    ) : (
                      <Circle className="w-5 h-5" />
                    )}
                  </button>

                  <div>
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      {getTaskTypeBadge(task.task_type)}
                      {task.subject_name && (
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                          {task.subject_name}
                        </span>
                      )}
                      <span className="inline-flex items-center space-x-1 text-[11px] text-slate-400 font-mono">
                        <Clock className="w-3 h-3" />
                        <span>~{task.estimated_minutes} min</span>
                      </span>
                    </div>

                    <h4
                      className={`font-bold text-sm ${
                        task.is_completed
                          ? 'line-through text-slate-500'
                          : 'text-slate-900'
                      }`}
                    >
                      {task.title}
                    </h4>

                    {task.reason && (
                      <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                        {task.reason}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-2 self-end sm:self-center flex-shrink-0">
                  {/* Reschedule button */}
                  {!task.is_completed && isToday && (
                    <button
                      onClick={() => handleRescheduleTomorrow(task)}
                      disabled={reschedulingTaskId === task.id}
                      title="Move task to tomorrow"
                      className="px-2.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100 border border-slate-200 transition-colors"
                    >
                      <span>Move Tomorrow</span>
                    </button>
                  )}

                  {/* Primary Action Button */}
                  {task.lesson_id && onSelectLesson ? (
                    <button
                      onClick={() => onSelectLesson(task.lesson_id!)}
                      className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white shadow-sm transition-all"
                    >
                      <span>{task.task_type === 'RESUME_LESSON' ? 'Resume' : 'Start'}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  ) : task.topic_id && onStartPractice ? (
                    <button
                      onClick={() => onStartPractice(task.topic_id!, task.title)}
                      className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white shadow-sm transition-all"
                    >
                      <span>Practise</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        ) : !loading ? (
          <div className="py-8 px-4 text-center">
            <div className="w-12 h-12 bg-brand-50 text-brand-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
              <Calendar className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-slate-900 text-sm">
              No tasks scheduled for {isToday ? 'today' : selectedDate}
            </h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
              {isToday
                ? 'Generate a fresh study plan based on your active progress and topic weaknesses.'
                : 'Select today or use the controls above to navigate your study schedule.'}
            </p>
            {isToday && (
              <button
                onClick={() => onRefresh(true)}
                className="inline-flex items-center space-x-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs rounded-xl shadow-sm transition-all"
              >
                <Sparkles className="w-4 h-4" />
                <span>Generate Today's Study Plan</span>
              </button>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
};
