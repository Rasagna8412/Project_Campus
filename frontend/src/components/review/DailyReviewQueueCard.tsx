import React from 'react';
import {
  Brain,
  RotateCcw,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Target,
} from 'lucide-react';
import { ReviewItemSummary, ReviewQueueResponse, ReviewStatsResponse } from '../../types/repetition';

interface DailyReviewQueueCardProps {
  queue: ReviewQueueResponse | null;
  stats: ReviewStatsResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onStartReview: (item: ReviewItemSummary) => void;
  onStartPractice?: (topicId: string, topicTitle?: string) => void;
}

export const DailyReviewQueueCard: React.FC<DailyReviewQueueCardProps> = ({
  queue,
  stats,
  loading,
  error,
  onRefresh,
  onStartReview,
  onStartPractice,
}) => {
  const items = queue?.items || [];
  const totalDue = queue?.total_due_count ?? 0;
  const overdueCount = queue?.overdue_count ?? 0;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header Bar */}
      <div className="p-5 sm:p-6 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-indigo-300 flex-shrink-0 mt-0.5">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2 text-xs font-semibold text-indigo-300 uppercase tracking-wider mb-1">
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Spaced Repetition & Revision Queue</span>
              </div>
              <h2 className="text-xl sm:text-2xl font-black">
                Automated Recall Schedule
              </h2>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {overdueCount > 0 && (
              <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-400/30">
                {overdueCount} Overdue
              </span>
            )}
            <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-500/20 text-indigo-200 border border-indigo-400/30">
              {totalDue} Due Today
            </span>

            <button
              onClick={onRefresh}
              disabled={loading}
              title="Refresh revision queue"
              className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-xl text-xs font-semibold bg-white/10 hover:bg-white/20 text-white border border-white/20 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
          </div>
        </div>

        {/* Aggregate Stats Sub-row */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5 pt-4 border-t border-white/10 text-xs">
            <div className="bg-white/5 rounded-xl p-2.5 border border-white/10">
              <span className="text-indigo-200 block text-[10px] font-bold uppercase tracking-wider">
                Tracked Topics
              </span>
              <span className="text-base sm:text-lg font-black text-white">
                {stats.total_tracked_topics ?? 0}
              </span>
            </div>

            <div className="bg-white/5 rounded-xl p-2.5 border border-white/10">
              <span className="text-indigo-200 block text-[10px] font-bold uppercase tracking-wider">
                Mastered Topics
              </span>
              <span className="text-base sm:text-lg font-black text-emerald-300">
                {stats.mastered_count ?? 0}
              </span>
            </div>

            <div className="bg-white/5 rounded-xl p-2.5 border border-white/10">
              <span className="text-indigo-200 block text-[10px] font-bold uppercase tracking-wider">
                Average Ease Factor
              </span>
              <span className="text-base sm:text-lg font-black text-white">
                {stats.average_ease_factor != null ? stats.average_ease_factor.toFixed(2) : '2.50'}
              </span>
            </div>

            <div className="bg-white/5 rounded-xl p-2.5 border border-white/10">
              <span className="text-indigo-200 block text-[10px] font-bold uppercase tracking-wider">
                Recall Success Rate
              </span>
              <span className="text-base sm:text-lg font-black text-emerald-300">
                {stats.successful_review_rate_percentage != null
                  ? `${stats.successful_review_rate_percentage}%`
                  : 'N/A'}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="p-5 sm:p-6">
        {loading && !queue ? (
          <div className="space-y-3 py-6">
            <div className="h-16 bg-slate-100 animate-pulse rounded-xl"></div>
            <div className="h-16 bg-slate-100 animate-pulse rounded-xl"></div>
            <div className="h-16 bg-slate-100 animate-pulse rounded-xl"></div>
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl border border-rose-200 bg-rose-50 text-xs text-rose-800 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={onRefresh}
              className="px-3 py-1 bg-white hover:bg-slate-50 border border-rose-300 rounded font-bold text-rose-700"
            >
              Retry
            </button>
          </div>
        ) : items.length > 0 ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-500 font-semibold px-1 pb-1">
              <span>Due Topics ({items.length} shown)</span>
              <span>Sorted by Urgency & Interval</span>
            </div>

            {items.map((item) => (
              <div
                key={item.id}
                className="p-4 rounded-xl border border-slate-200 bg-white hover:border-indigo-300 hover:shadow-sm transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                      {item.subject_name}
                    </span>
                    <span className="text-slate-300">•</span>
                    <span className="text-[10px] font-medium text-slate-600">
                      {item.chapter_title}
                    </span>

                    {item.is_overdue ? (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                        Overdue
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                        Due Today
                      </span>
                    )}

                    <span
                      className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        item.status === 'MASTERED'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : item.status === 'REVIEW'
                          ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                          : 'bg-slate-100 text-slate-600 border border-slate-200'
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>

                  <h4 className="font-bold text-sm text-slate-900">{item.topic_title}</h4>

                  <div className="flex items-center space-x-3 text-xs text-slate-500">
                    <span>
                      Repetition: <strong>#{item.repetition_count}</strong>
                    </span>
                    <span>•</span>
                    <span>
                      Interval:{' '}
                      <strong>
                        {item.interval_days} {item.interval_days === 1 ? 'day' : 'days'}
                      </strong>
                    </span>
                    <span>•</span>
                    <span>
                      Ease Factor: <strong>{item.ease_factor.toFixed(2)}</strong>
                    </span>
                  </div>
                </div>

                <div className="flex items-center space-x-2 self-end sm:self-center flex-shrink-0">
                  {onStartPractice && item.sample_question_count > 0 && (
                    <button
                      onClick={() => onStartPractice(item.topic_id, item.topic_title)}
                      title="Practice questions before recall"
                      className="px-2.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100 border border-slate-200 transition-colors inline-flex items-center space-x-1"
                    >
                      <Target className="w-3.5 h-3.5 text-slate-500" />
                      <span>Drill ({item.sample_question_count})</span>
                    </button>
                  )}

                  <button
                    onClick={() => onStartReview(item)}
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-all"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Review Recall</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-8 px-4 text-center">
            <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-slate-900 text-sm">
              All Reviews Completed for Today! 🎉
            </h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 leading-relaxed">
              No topics are currently due for spaced repetition review. Completed lessons and practice sessions will automatically appear here as their memory retention intervals mature.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
