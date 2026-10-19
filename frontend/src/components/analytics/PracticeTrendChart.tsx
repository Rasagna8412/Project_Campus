import React, { useState } from 'react';
import { BarChart3, Calendar, Clock, Target, Info } from 'lucide-react';
import { PracticeTrendsResponse } from '../../types/analytics_trends';

interface PracticeTrendChartProps {
  data: PracticeTrendsResponse | null;
  loading: boolean;
  selectedDays: number;
  onDaysChange: (days: number) => void;
  onOpenMethodology?: () => void;
}

export const PracticeTrendChart: React.FC<PracticeTrendChartProps> = ({
  data,
  loading,
  selectedDays,
  onDaysChange,
  onOpenMethodology,
}) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const dailyTrends = data?.daily_trends || [];
  const maxQuestions = Math.max(...dailyTrends.map((d) => d.questions_answered), 10);

  // Chart dimensions for SVG
  const svgWidth = 600;
  const svgHeight = 220;
  const paddingX = 40;
  const paddingTop = 25;
  const paddingBottom = 35;
  const chartWidth = svgWidth - paddingX * 2;
  const chartHeight = svgHeight - paddingTop - paddingBottom;

  const barWidth = Math.max(8, Math.min(28, (chartWidth / Math.max(dailyTrends.length, 1)) * 0.55));
  const stepX = dailyTrends.length > 1 ? chartWidth / (dailyTrends.length - 1) : chartWidth / 2;

  // Compute accuracy polyline points (skip days where accuracy is null)
  const accuracyPoints: { x: number; y: number; acc: number; date: string }[] = [];
  dailyTrends.forEach((d, idx) => {
    if (d.accuracy_percentage !== null) {
      const x = paddingX + idx * stepX;
      // y-axis for accuracy: 0% is bottom, 100% is top
      const y = paddingTop + (1 - d.accuracy_percentage / 100) * chartHeight;
      accuracyPoints.push({ x, y, acc: d.accuracy_percentage, date: d.date });
    }
  });

  const accuracyPathD = accuracyPoints.reduce((acc, pt, idx) => {
    return `${acc} ${idx === 0 ? 'M' : 'L'} ${pt.x} ${pt.y}`;
  }, '');

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden p-5 sm:p-6">
      {/* Header with Title and Range Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold text-indigo-600 uppercase tracking-wider mb-1">
            <BarChart3 className="w-4 h-4" />
            <span>Practice Trends & Volume</span>
          </div>
          <h3 className="text-lg sm:text-xl font-bold text-slate-900">
            Practice Volume & Accuracy Timeline
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Daily answered questions in IST compared with observed question accuracy.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {onOpenMethodology && (
            <button
              onClick={onOpenMethodology}
              className="inline-flex items-center text-xs text-slate-500 hover:text-indigo-600 transition-colors p-1"
              title="View metric formulas and rules"
              aria-label="View metric methodology guide"
            >
              <Info className="w-4 h-4 mr-1" />
              <span className="hidden sm:inline">Guide</span>
            </button>
          )}

          <div
            className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200"
            role="group"
            aria-label="Trend window size"
          >
            <button
              type="button"
              onClick={() => onDaysChange(7)}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
                selectedDays === 7
                  ? 'bg-white text-indigo-700 shadow-sm border border-slate-200'
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
                  ? 'bg-white text-indigo-700 shadow-sm border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
              aria-pressed={selectedDays === 14}
            >
              14 Days
            </button>
          </div>
        </div>
      </div>

      {/* Summary KPI Badges */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3">
          <div className="flex items-center text-xs font-semibold text-slate-500 mb-1">
            <BarChart3 className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
            <span>Questions</span>
          </div>
          <div className="text-xl font-black text-slate-900">
            {data ? data.total_questions_answered : '—'}
          </div>
          <div className="text-[11px] text-slate-500">
            {data ? `${data.total_correct_count} correct` : ''}
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3">
          <div className="flex items-center text-xs font-semibold text-slate-500 mb-1">
            <Target className="w-3.5 h-3.5 mr-1.5 text-emerald-600" />
            <span>Observed Accuracy</span>
          </div>
          <div className="text-xl font-black text-slate-900">
            {data?.overall_accuracy_percentage !== null && data?.overall_accuracy_percentage !== undefined
              ? `${data.overall_accuracy_percentage}%`
              : '—'}
          </div>
          <div className="text-[11px] text-slate-500">
            {data?.overall_accuracy_percentage !== null ? 'Aggregate rate' : 'No attempts'}
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3">
          <div className="flex items-center text-xs font-semibold text-slate-500 mb-1">
            <Clock className="w-3.5 h-3.5 mr-1.5 text-blue-600" />
            <span>Practice Time</span>
          </div>
          <div className="text-xl font-black text-slate-900">
            {data ? `${data.total_practice_minutes}m` : '—'}
          </div>
          <div className="text-[11px] text-slate-500">Total active drill</div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3">
          <div className="flex items-center text-xs font-semibold text-slate-500 mb-1">
            <Calendar className="w-3.5 h-3.5 mr-1.5 text-violet-600" />
            <span>Window</span>
          </div>
          <div className="text-sm font-bold text-slate-900 truncate">
            {data ? `${data.start_date.slice(5)} to ${data.end_date.slice(5)}` : '—'}
          </div>
          <div className="text-[11px] text-slate-500">{selectedDays} IST calendar days</div>
        </div>
      </div>

      {/* SVG Chart Container */}
      <div className="relative">
        {loading ? (
          <div className="h-56 flex items-center justify-center text-sm text-slate-400">
            Loading practice trends...
          </div>
        ) : dailyTrends.length === 0 ? (
          <div className="h-56 flex flex-col items-center justify-center text-sm text-slate-400">
            <BarChart3 className="w-8 h-8 text-slate-300 mb-2" />
            <p>No practice activity recorded in this period.</p>
          </div>
        ) : (
          <div>
            <div className="w-full overflow-x-auto">
              <svg
                viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                className="w-full h-56 font-sans select-none"
                aria-label="Practice questions and accuracy chart"
                role="img"
              >
                <title>Daily Practice Volume and Accuracy</title>
                <desc>
                  Bar chart showing daily questions answered and line overlay showing accuracy percentage.
                </desc>

                {/* Horizontal reference grid lines */}
                {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
                  const y = paddingTop + pct * chartHeight;
                  const qVal = Math.round((1 - pct) * maxQuestions);
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
                      {/* Left Axis: Questions */}
                      <text
                        x={paddingX - 6}
                        y={y + 4}
                        textAnchor="end"
                        fontSize="9"
                        fill="#94a3b8"
                      >
                        {qVal}
                      </text>
                      {/* Right Axis: Accuracy % */}
                      <text
                        x={svgWidth - paddingX + 6}
                        y={y + 4}
                        textAnchor="start"
                        fontSize="9"
                        fill="#94a3b8"
                      >
                        {`${Math.round((1 - pct) * 100)}%`}
                      </text>
                    </g>
                  );
                })}

                {/* Bars for Questions Answered & Correct */}
                {dailyTrends.map((d, idx) => {
                  const cx = paddingX + idx * stepX;
                  const barHeight = (d.questions_answered / maxQuestions) * chartHeight;
                  const barY = paddingTop + chartHeight - barHeight;

                  const correctHeight =
                    d.questions_answered > 0
                      ? (d.correct_count / maxQuestions) * chartHeight
                      : 0;
                  const correctY = paddingTop + chartHeight - correctHeight;

                  const isHovered = hoveredIdx === idx;
                  const formattedDate = d.date.slice(5);

                  return (
                    <g
                      key={d.date}
                      onMouseEnter={() => setHoveredIdx(idx)}
                      onMouseLeave={() => setHoveredIdx(null)}
                      tabIndex={0}
                      role="graphics-symbol"
                      aria-label={`${d.date}: ${d.questions_answered} questions, ${d.correct_count} correct, accuracy ${d.accuracy_percentage ?? 'N/A'}%`}
                      className="cursor-pointer focus:outline-none"
                    >
                      {/* Total Questions Bar */}
                      {d.questions_answered > 0 && (
                        <rect
                          x={cx - barWidth / 2}
                          y={barY}
                          width={barWidth}
                          height={Math.max(barHeight, 2)}
                          rx="3"
                          fill={isHovered ? '#818cf8' : '#c7d2fe'}
                          className="transition-colors"
                        />
                      )}

                      {/* Correct Answers Bar (Stacked/Overlay) */}
                      {d.correct_count > 0 && (
                        <rect
                          x={cx - barWidth / 2}
                          y={correctY}
                          width={barWidth}
                          height={Math.max(correctHeight, 2)}
                          rx="3"
                          fill={isHovered ? '#4f46e5' : '#6366f1'}
                          className="transition-colors"
                        />
                      )}

                      {/* Date label on X axis */}
                      <text
                        x={cx}
                        y={svgHeight - 12}
                        textAnchor="middle"
                        fontSize="9"
                        fill={isHovered ? '#1e293b' : '#64748b'}
                        fontWeight={isHovered ? 'bold' : 'normal'}
                      >
                        {formattedDate}
                      </text>
                    </g>
                  );
                })}

                {/* Accuracy Line Overlay */}
                {accuracyPoints.length > 1 && (
                  <path
                    d={accuracyPathD}
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                )}

                {/* Accuracy Data Points */}
                {accuracyPoints.map((pt, idx) => (
                  <g key={`pt-${idx}`}>
                    <circle
                      cx={pt.x}
                      cy={pt.y}
                      r="4"
                      fill="#ffffff"
                      stroke="#10b981"
                      strokeWidth="2.5"
                    />
                  </g>
                ))}
              </svg>
            </div>

            {/* Hover tooltip / info banner */}
            {hoveredIdx !== null && dailyTrends[hoveredIdx] && (
              <div className="mt-2 p-2.5 bg-slate-900 text-white text-xs rounded-xl flex items-center justify-between">
                <div>
                  <span className="font-bold text-indigo-300">
                    {dailyTrends[hoveredIdx].date}:
                  </span>{' '}
                  <span>
                    {dailyTrends[hoveredIdx].questions_answered} questions answered (
                    {dailyTrends[hoveredIdx].correct_count} correct)
                  </span>
                </div>
                <div className="font-semibold text-emerald-400">
                  Accuracy:{' '}
                  {dailyTrends[hoveredIdx].accuracy_percentage !== null
                    ? `${dailyTrends[hoveredIdx].accuracy_percentage}%`
                    : 'N/A'}
                </div>
              </div>
            )}

            {/* Legend */}
            <div className="flex items-center justify-center space-x-6 text-xs text-slate-600 mt-4 pt-3 border-t border-slate-100">
              <div className="flex items-center space-x-2">
                <span className="w-3 h-3 rounded bg-indigo-200 inline-block" />
                <span>Total Questions</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-3 h-3 rounded bg-indigo-600 inline-block" />
                <span>Correct Answers</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-3 h-0.5 bg-emerald-500 inline-block rounded-full" />
                <span>Accuracy %</span>
              </div>
            </div>
          </div>
        )}

        {/* Screen Reader Data Table for WCAG 2.1 AA Compliance */}
        <table className="sr-only">
          <caption>Daily Practice Volume and Accuracy Data Table</caption>
          <thead>
            <tr>
              <th scope="col">Date (IST)</th>
              <th scope="col">Questions Answered</th>
              <th scope="col">Correct Answers</th>
              <th scope="col">Accuracy %</th>
              <th scope="col">Practice Minutes</th>
            </tr>
          </thead>
          <tbody>
            {dailyTrends.map((d) => (
              <tr key={d.date}>
                <td>{d.date}</td>
                <td>{d.questions_answered}</td>
                <td>{d.correct_count}</td>
                <td>{d.accuracy_percentage !== null ? `${d.accuracy_percentage}%` : 'N/A'}</td>
                <td>{d.practice_minutes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
