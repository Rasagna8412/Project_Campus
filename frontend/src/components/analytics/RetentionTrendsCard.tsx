import React from 'react';
import { Flame, Clock, AlertTriangle, Calendar, Brain, ArrowRight, Info } from 'lucide-react';
import { RetentionTrendsResponse } from '../../types/analytics_trends';

interface RetentionTrendsCardProps {
  data: RetentionTrendsResponse | null;
  loading: boolean;
  onNavigateToReviewQueue?: () => void;
  onOpenMethodology?: () => void;
}

export const RetentionTrendsCard: React.FC<RetentionTrendsCardProps> = ({
  data,
  loading,
  onNavigateToReviewQueue,
  onOpenMethodology,
}) => {
  const forecast = data?.forecast_next_7_days || [];
  const maxDue = Math.max(...forecast.map((f) => f.due_count), 5);

  // SVG dimensions for forecast bar chart
  const svgWidth = 420;
  const svgHeight = 130;
  const paddingX = 30;
  const paddingTop = 20;
  const paddingBottom = 25;
  const chartWidth = svgWidth - paddingX * 2;
  const chartHeight = svgHeight - paddingTop - paddingBottom;
  const stepX = forecast.length > 1 ? chartWidth / (forecast.length - 1) : chartWidth / 2;
  const barWidth = 20;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden p-5 sm:p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold text-violet-600 uppercase tracking-wider mb-1">
            <Brain className="w-4 h-4" />
            <span>Spaced Repetition & Retention</span>
          </div>
          <h3 className="text-lg sm:text-xl font-bold text-slate-900">
            Memory Streaks & Recall Forecast
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Active recall consistency and 7-day upcoming revision workload distribution.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {onOpenMethodology && (
            <button
              onClick={onOpenMethodology}
              className="inline-flex items-center text-xs text-slate-500 hover:text-violet-600 transition-colors p-1"
              title="View metric formulas and rules"
              aria-label="View spaced repetition retention methodology guide"
            >
              <Info className="w-4 h-4 mr-1" />
              <span className="hidden sm:inline">Guide</span>
            </button>
          )}

          {onNavigateToReviewQueue && (
            <button
              onClick={onNavigateToReviewQueue}
              className="inline-flex items-center px-3 py-1.5 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-all shadow-sm"
            >
              <span>Review Queue</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="h-48 flex items-center justify-center text-sm text-slate-400">
          Loading retention trends...
        </div>
      ) : (
        <div className="space-y-6">
          {/* Top Row: Streak and Overdue Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Active Streak Card */}
            <div className="bg-gradient-to-br from-amber-500/10 via-orange-500/5 to-transparent border border-amber-200/60 rounded-2xl p-4 flex items-center space-x-4">
              <div
                className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                  (data?.active_streak_days ?? 0) > 0
                    ? 'bg-amber-500 text-white shadow-md shadow-amber-500/30'
                    : 'bg-slate-100 text-slate-400'
                }`}
              >
                <Flame className="w-6 h-6" />
              </div>
              <div>
                <div className="text-xs font-bold uppercase tracking-wider text-amber-700">
                  Active Review Streak
                </div>
                <div className="text-2xl font-black text-slate-900">
                  {data?.active_streak_days ?? 0}{' '}
                  <span className="text-sm font-semibold text-slate-600">
                    {(data?.active_streak_days ?? 0) === 1 ? 'day' : 'days'}
                  </span>
                </div>
                <div className="text-[11px] text-slate-500">
                  {data?.is_streak_active_today ? (
                    <span className="text-emerald-600 font-semibold">
                      ✓ Maintained today
                    </span>
                  ) : (data?.active_streak_days ?? 0) > 0 ? (
                    <span className="text-amber-600 font-semibold">
                      Review today to continue streak!
                    </span>
                  ) : (
                    'Complete a review to start'
                  )}
                </div>
              </div>
            </div>

            {/* Due Today & Overdue Breakdown */}
            <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex flex-col justify-between">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-600 uppercase">Due Today</span>
                <Clock className="w-4 h-4 text-indigo-600" />
              </div>
              <div className="text-2xl font-black text-slate-900">
                {data?.due_today_count ?? 0}
              </div>
              <p className="text-[11px] text-slate-500">
                Topics scheduled for recall drill today in IST.
              </p>
            </div>

            <div className="bg-rose-50/60 border border-rose-200/70 rounded-2xl p-4 flex flex-col justify-between">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-rose-800 uppercase">Overdue Aging</span>
                <AlertTriangle className="w-4 h-4 text-rose-600" />
              </div>
              <div className="flex items-baseline space-x-3">
                <span className="text-2xl font-black text-rose-950">
                  {data?.total_overdue_count ?? 0}
                </span>
                <div className="flex items-center space-x-2 text-[11px]">
                  <span className="px-2 py-0.5 rounded-md bg-rose-100 text-rose-800 font-bold">
                    {data?.overdue_1_to_3_days ?? 0} (1–3d)
                  </span>
                  <span className="px-2 py-0.5 rounded-md bg-rose-200 text-rose-900 font-bold">
                    {data?.overdue_4_plus_days ?? 0} (4+d)
                  </span>
                </div>
              </div>
              <p className="text-[11px] text-rose-700">
                High overdue items risk memory trace decay.
              </p>
            </div>
          </div>

          {/* Bottom Section: 7-Day Recall Forecast SVG */}
          <div className="bg-slate-50/70 border border-slate-200/80 rounded-2xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-violet-600" />
                <span className="text-xs font-bold text-slate-700 uppercase">
                  7-Day Upcoming Review Forecast
                </span>
              </div>
              <span className="text-[11px] text-slate-500">
                Daily scheduled item count maturing over the next 7 days
              </span>
            </div>

            {forecast.length === 0 ? (
              <div className="h-28 flex items-center justify-center text-xs text-slate-400">
                No upcoming review items scheduled.
              </div>
            ) : (
              <div className="w-full overflow-x-auto">
                <svg
                  viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                  className="w-full h-28 font-sans select-none"
                  aria-label="7-day upcoming review items forecast"
                  role="img"
                >
                  <title>7-Day Spaced Repetition Workload Forecast</title>
                  <desc>Bar chart showing upcoming due review items per day.</desc>

                  {/* Reference line */}
                  <line
                    x1={paddingX}
                    y1={paddingTop + chartHeight}
                    x2={svgWidth - paddingX}
                    y2={paddingTop + chartHeight}
                    stroke="#cbd5e1"
                    strokeWidth="1"
                  />

                  {forecast.map((f, idx) => {
                    const cx = paddingX + idx * stepX;
                    const barH = (f.due_count / maxDue) * chartHeight;
                    const barY = paddingTop + chartHeight - barH;
                    const dateFormatted = f.date.slice(5);

                    return (
                      <g
                        key={f.date}
                        tabIndex={0}
                        role="graphics-symbol"
                        aria-label={`${f.date}: ${f.due_count} review items maturing`}
                        className="cursor-pointer focus:outline-none"
                      >
                        {f.due_count > 0 && (
                          <rect
                            x={cx - barWidth / 2}
                            y={barY}
                            width={barWidth}
                            height={Math.max(barH, 3)}
                            rx="3"
                            fill="#8b5cf6"
                            className="hover:fill-violet-700 transition-colors"
                          />
                        )}

                        {/* Count text label above bar */}
                        <text
                          x={cx}
                          y={f.due_count > 0 ? barY - 4 : paddingTop + chartHeight - 4}
                          textAnchor="middle"
                          fontSize="9"
                          fontWeight="bold"
                          fill={f.due_count > 0 ? '#6d28d9' : '#94a3b8'}
                        >
                          {f.due_count}
                        </text>

                        {/* Date label */}
                        <text
                          x={cx}
                          y={svgHeight - 8}
                          textAnchor="middle"
                          fontSize="9"
                          fill="#64748b"
                        >
                          {dateFormatted}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            )}

            {/* Screen Reader Table */}
            <table className="sr-only">
              <caption>7-Day Review Forecast Data Table</caption>
              <thead>
                <tr>
                  <th scope="col">Forecast Date (IST)</th>
                  <th scope="col">Due Review Items</th>
                </tr>
              </thead>
              <tbody>
                {forecast.map((f) => (
                  <tr key={f.date}>
                    <td>{f.date}</td>
                    <td>{f.due_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
