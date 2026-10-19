import React, { useState } from 'react';
import { CalendarCheck2, Clock, CheckCircle2, Coffee, Info } from 'lucide-react';
import { PlannerTrendsResponse } from '../../types/analytics_trends';

interface PlannerAdherenceChartProps {
  data: PlannerTrendsResponse | null;
  loading: boolean;
  selectedDays: number;
  onDaysChange: (days: number) => void;
  onOpenMethodology?: () => void;
}

export const PlannerAdherenceChart: React.FC<PlannerAdherenceChartProps> = ({
  data,
  loading,
  selectedDays,
  onDaysChange,
  onOpenMethodology,
}) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const dailyTrends = data?.daily_trends || [];
  const maxMinutes = Math.max(
    ...dailyTrends.map((d) => Math.max(d.planned_minutes, d.completed_minutes)),
    data?.daily_study_goal_minutes || 60,
    60
  );

  // SVG dimensions
  const svgWidth = 600;
  const svgHeight = 220;
  const paddingX = 40;
  const paddingTop = 25;
  const paddingBottom = 35;
  const chartWidth = svgWidth - paddingX * 2;
  const chartHeight = svgHeight - paddingTop - paddingBottom;

  const barGroupWidth = Math.max(16, (chartWidth / Math.max(dailyTrends.length, 1)) * 0.65);
  const singleBarWidth = barGroupWidth / 2 - 2;
  const stepX = dailyTrends.length > 1 ? chartWidth / (dailyTrends.length - 1) : chartWidth / 2;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden p-5 sm:p-6">
      {/* Header with Title and Range Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold text-blue-600 uppercase tracking-wider mb-1">
            <CalendarCheck2 className="w-4 h-4" />
            <span>Study Plan Adherence</span>
          </div>
          <h3 className="text-lg sm:text-xl font-bold text-slate-900">
            Planned vs Completed Study Minutes
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Non-punitive weekly goal adherence measured against your preferred study days.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {onOpenMethodology && (
            <button
              onClick={onOpenMethodology}
              className="inline-flex items-center text-xs text-slate-500 hover:text-blue-600 transition-colors p-1"
              title="View metric formulas and rules"
              aria-label="View study plan adherence methodology guide"
            >
              <Info className="w-4 h-4 mr-1" />
              <span className="hidden sm:inline">Guide</span>
            </button>
          )}

          <div
            className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200"
            role="group"
            aria-label="Adherence window size"
          >
            <button
              type="button"
              onClick={() => onDaysChange(7)}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
                selectedDays === 7
                  ? 'bg-white text-blue-700 shadow-sm border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
              aria-pressed={selectedDays === 7}
            >
              7 Days
            </button>
            <button
              type="button"
              onClick={() => onDaysChange(14)}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
                selectedDays === 14
                  ? 'bg-white text-blue-700 shadow-sm border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
              aria-pressed={selectedDays === 14}
            >
              14 Days
            </button>
          </div>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3">
          <div className="flex items-center text-xs font-semibold text-slate-500 mb-1">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 text-emerald-600" />
            <span>Adherence Rate</span>
          </div>
          <div className="text-xl font-black text-slate-900">
            {data?.adherence_rate_percentage !== null && data?.adherence_rate_percentage !== undefined
              ? `${data.adherence_rate_percentage}%`
              : '—'}
          </div>
          <div className="text-[11px] text-slate-500">
            {data ? `${data.goals_met_count}/${data.preferred_days_count} preferred days` : ''}
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3">
          <div className="flex items-center text-xs font-semibold text-slate-500 mb-1">
            <Clock className="w-3.5 h-3.5 mr-1.5 text-blue-600" />
            <span>Completed Study</span>
          </div>
          <div className="text-xl font-black text-slate-900">
            {data ? `${data.total_completed_minutes}m` : '—'}
          </div>
          <div className="text-[11px] text-slate-500">
            {data ? `${data.total_planned_minutes}m planned` : ''}
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3">
          <div className="flex items-center text-xs font-semibold text-slate-500 mb-1">
            <Clock className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
            <span>Daily Goal Target</span>
          </div>
          <div className="text-xl font-black text-slate-900">
            {data ? `${data.daily_study_goal_minutes}m` : '—'}
          </div>
          <div className="text-[11px] text-slate-500">Target per study day</div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3">
          <div className="flex items-center text-xs font-semibold text-slate-500 mb-1">
            <Coffee className="w-3.5 h-3.5 mr-1.5 text-amber-600" />
            <span>Rest Days</span>
          </div>
          <div className="text-xl font-black text-slate-900">
            {data ? data.days_count - data.preferred_days_count : '—'}
          </div>
          <div className="text-[11px] text-slate-500">Non-punitive off-days</div>
        </div>
      </div>

      {/* SVG Chart Container */}
      <div className="relative">
        {loading ? (
          <div className="h-56 flex items-center justify-center text-sm text-slate-400">
            Loading study adherence...
          </div>
        ) : dailyTrends.length === 0 ? (
          <div className="h-56 flex flex-col items-center justify-center text-sm text-slate-400">
            <CalendarCheck2 className="w-8 h-8 text-slate-300 mb-2" />
            <p>No study plans recorded in this window.</p>
          </div>
        ) : (
          <div>
            <div className="w-full overflow-x-auto">
              <svg
                viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                className="w-full h-56 font-sans select-none"
                aria-label="Planned vs completed study minutes chart"
                role="img"
              >
                <title>Study Plan Minutes and Adherence</title>
                <desc>
                  Grouped bar chart showing planned study minutes versus completed study minutes with rest day indicators.
                </desc>

                {/* Horizontal reference grid lines */}
                {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
                  const y = paddingTop + pct * chartHeight;
                  const mVal = Math.round((1 - pct) * maxMinutes);
                  return (
                    <g key={i}>
                      <line
                        x1={paddingX}
                        y1={y}
                        x2={svgWidth - paddingX}
                        y2={y}
                        stroke="#f1f5f9"
                        strokeDasharray={pct === 1 ? undefined : '3,3'}
                        strokeWidth="1"
                      />
                      <text
                        x={paddingX - 6}
                        y={y + 4}
                        textAnchor="end"
                        fontSize="9"
                        fill="#94a3b8"
                      >
                        {`${mVal}m`}
                      </text>
                    </g>
                  );
                })}

                {/* Bars for Planned & Completed Minutes */}
                {dailyTrends.map((d, idx) => {
                  const cx = paddingX + idx * stepX;
                  const plannedH = (d.planned_minutes / maxMinutes) * chartHeight;
                  const completedH = (d.completed_minutes / maxMinutes) * chartHeight;

                  const plannedY = paddingTop + chartHeight - plannedH;
                  const completedY = paddingTop + chartHeight - completedH;

                  const isHovered = hoveredIdx === idx;
                  const formattedDate = d.date.slice(5);

                  return (
                    <g
                      key={d.date}
                      onMouseEnter={() => setHoveredIdx(idx)}
                      onMouseLeave={() => setHoveredIdx(null)}
                      tabIndex={0}
                      role="graphics-symbol"
                      aria-label={`${d.date} (${d.day_of_week}): Planned ${d.planned_minutes}m, Completed ${d.completed_minutes}m. ${d.is_preferred_day ? (d.is_goal_met ? 'Goal Met' : 'Pending') : 'Rest Day'}`}
                      className="cursor-pointer focus:outline-none"
                    >
                      {/* Rest Day Shading */}
                      {!d.is_preferred_day && (
                        <rect
                          x={cx - barGroupWidth / 2 - 2}
                          y={paddingTop}
                          width={barGroupWidth + 4}
                          height={chartHeight}
                          fill="#f8fafc"
                          rx="4"
                        />
                      )}

                      {/* Planned Bar */}
                      {d.planned_minutes > 0 && (
                        <rect
                          x={cx - barGroupWidth / 2}
                          y={plannedY}
                          width={singleBarWidth}
                          height={Math.max(plannedH, 2)}
                          rx="2"
                          fill={isHovered ? '#93c5fd' : '#bfdbfe'}
                          className="transition-colors"
                        />
                      )}

                      {/* Completed Bar */}
                      {d.completed_minutes > 0 && (
                        <rect
                          x={cx - barGroupWidth / 2 + singleBarWidth + 2}
                          y={completedY}
                          width={singleBarWidth}
                          height={Math.max(completedH, 2)}
                          rx="2"
                          fill={
                            d.is_goal_met
                              ? isHovered
                                ? '#059669'
                                : '#10b981'
                              : isHovered
                              ? '#2563eb'
                              : '#3b82f6'
                          }
                          className="transition-colors"
                        />
                      )}

                      {/* Goal Met / Rest indicator icon */}
                      {d.is_preferred_day ? (
                        d.is_goal_met ? (
                          <circle
                            cx={cx}
                            y={paddingTop - 10}
                            r="3"
                            fill="#10b981"
                          />
                        ) : null
                      ) : (
                        <text
                          x={cx}
                          y={paddingTop - 6}
                          textAnchor="middle"
                          fontSize="7"
                          fill="#94a3b8"
                          fontWeight="bold"
                        >
                          REST
                        </text>
                      )}

                      {/* Date and Day label */}
                      <text
                        x={cx}
                        y={svgHeight - 14}
                        textAnchor="middle"
                        fontSize="9"
                        fill={isHovered ? '#1e293b' : '#64748b'}
                        fontWeight={isHovered ? 'bold' : 'normal'}
                      >
                        {formattedDate}
                      </text>
                      <text
                        x={cx}
                        y={svgHeight - 4}
                        textAnchor="middle"
                        fontSize="8"
                        fill={d.is_preferred_day ? '#94a3b8' : '#cbd5e1'}
                      >
                        {d.day_of_week}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>

            {/* Hover tooltip / info banner */}
            {hoveredIdx !== null && dailyTrends[hoveredIdx] && (
              <div className="mt-2 p-2.5 bg-slate-900 text-white text-xs rounded-xl flex items-center justify-between">
                <div>
                  <span className="font-bold text-blue-300">
                    {dailyTrends[hoveredIdx].date} ({dailyTrends[hoveredIdx].day_of_week}):
                  </span>{' '}
                  <span>
                    Planned {dailyTrends[hoveredIdx].planned_minutes}m • Completed{' '}
                    {dailyTrends[hoveredIdx].completed_minutes}m (
                    {dailyTrends[hoveredIdx].completed_tasks_count}/
                    {dailyTrends[hoveredIdx].tasks_count} tasks)
                  </span>
                </div>
                <div className="font-semibold">
                  {!dailyTrends[hoveredIdx].is_preferred_day ? (
                    <span className="text-amber-400">Rest Day (Non-punitive)</span>
                  ) : dailyTrends[hoveredIdx].is_goal_met ? (
                    <span className="text-emerald-400">✓ Goal Met</span>
                  ) : (
                    <span className="text-slate-400">Goal Incomplete</span>
                  )}
                </div>
              </div>
            )}

            {/* Legend */}
            <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-slate-600 mt-4 pt-3 border-t border-slate-100">
              <div className="flex items-center space-x-2">
                <span className="w-3 h-3 rounded bg-blue-200 inline-block" />
                <span>Planned Minutes</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-3 h-3 rounded bg-blue-500 inline-block" />
                <span>Completed Minutes</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
                <span>Goal Met</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-500 font-bold">
                  REST
                </span>
                <span>Rest Day (Excluded from Adherence denominator)</span>
              </div>
            </div>
          </div>
        )}

        {/* Screen Reader Data Table for WCAG 2.1 AA Compliance */}
        <table className="sr-only">
          <caption>Study Plan Adherence Data Table</caption>
          <thead>
            <tr>
              <th scope="col">Date (IST)</th>
              <th scope="col">Day</th>
              <th scope="col">Preferred Day?</th>
              <th scope="col">Planned Minutes</th>
              <th scope="col">Completed Minutes</th>
              <th scope="col">Tasks Completed</th>
              <th scope="col">Goal Met?</th>
            </tr>
          </thead>
          <tbody>
            {dailyTrends.map((d) => (
              <tr key={d.date}>
                <td>{d.date}</td>
                <td>{d.day_of_week}</td>
                <td>{d.is_preferred_day ? 'Yes' : 'No (Rest Day)'}</td>
                <td>{d.planned_minutes}</td>
                <td>{d.completed_minutes}</td>
                <td>{`${d.completed_tasks_count}/${d.tasks_count}`}</td>
                <td>{d.is_goal_met ? 'Met' : 'Unmet'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
