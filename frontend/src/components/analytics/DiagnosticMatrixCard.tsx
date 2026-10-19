import React, { useState, useMemo } from 'react';
import {
  Layers,
  AlertOctagon,
  BookOpen,
  Sparkles,
  CheckCircle,
  HelpCircle,
  Search,
  Filter,
  ArrowRight,
  Info,
} from 'lucide-react';
import {
  DiagnosticMatrixResponse,
  DiagnosticState,
} from '../../types/analytics_trends';

interface DiagnosticMatrixCardProps {
  data: DiagnosticMatrixResponse | null;
  loading: boolean;
  onStartPractice?: (topicId: string, topicTitle?: string) => void;
  onNavigateToLessons?: () => void;
  onOpenMethodology?: () => void;
}

export const DiagnosticMatrixCard: React.FC<DiagnosticMatrixCardProps> = ({
  data,
  loading,
  onStartPractice,
  onOpenMethodology,
}) => {
  const [selectedFilter, setSelectedFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const topics = data?.topics || [];

  const filteredTopics = useMemo(() => {
    return topics.filter((t) => {
      const matchesFilter =
        selectedFilter === 'ALL' || t.diagnostic_state === selectedFilter;
      const matchesSearch =
        searchQuery.trim() === '' ||
        t.topic_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.subject_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.chapter_title.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesFilter && matchesSearch;
    });
  }, [topics, selectedFilter, searchQuery]);

  const getStateBadge = (state: DiagnosticState) => {
    switch (state) {
      case 'CRITICAL_GAP':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200">
            <AlertOctagon className="w-3.5 h-3.5 mr-1 text-rose-600 flex-shrink-0" />
            Critical Gap
          </span>
        );
      case 'UNPRACTICED_FOUNDATION':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200">
            <BookOpen className="w-3.5 h-3.5 mr-1 text-amber-600 flex-shrink-0" />
            Unpracticed Foundation
          </span>
        );
      case 'SOLIDIFYING':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold bg-blue-100 text-blue-800 border border-blue-200">
            <Sparkles className="w-3.5 h-3.5 mr-1 text-blue-600 flex-shrink-0" />
            Solidifying
          </span>
        );
      case 'MASTERED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
            <CheckCircle className="w-3.5 h-3.5 mr-1 text-emerald-600 flex-shrink-0" />
            Mastered
          </span>
        );
      case 'NOT_STARTED':
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
            <HelpCircle className="w-3.5 h-3.5 mr-1 text-slate-400 flex-shrink-0" />
            Not Started
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden p-5 sm:p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold text-indigo-600 uppercase tracking-wider mb-1">
            <Layers className="w-4 h-4" />
            <span>Multi-Dimensional Diagnosis</span>
          </div>
          <h3 className="text-lg sm:text-xl font-bold text-slate-900">
            Curriculum Diagnostic Matrix
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Synthesis of lesson completion, practice accuracy calibration, and spaced recall status.
          </p>
        </div>

        {onOpenMethodology && (
          <button
            onClick={onOpenMethodology}
            className="inline-flex items-center text-xs text-slate-500 hover:text-indigo-600 transition-colors p-1 self-start sm:self-auto"
            title="View metric formulas and rules"
            aria-label="View diagnostic matrix classification rules"
          >
            <Info className="w-4 h-4 mr-1" />
            <span>Diagnostic Rules</span>
          </button>
        )}
      </div>

      {/* Summary KPI Cards & Filters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <button
          type="button"
          onClick={() => setSelectedFilter(selectedFilter === 'CRITICAL_GAP' ? 'ALL' : 'CRITICAL_GAP')}
          className={`p-3 rounded-xl border text-left transition-all ${
            selectedFilter === 'CRITICAL_GAP'
              ? 'bg-rose-50 border-rose-300 ring-2 ring-rose-400/20'
              : 'bg-slate-50 border-slate-200/80 hover:bg-slate-100/70'
          }`}
        >
          <div className="flex items-center text-xs font-bold text-rose-700 mb-1">
            <AlertOctagon className="w-3.5 h-3.5 mr-1" />
            <span>Critical Gaps</span>
          </div>
          <div className="text-2xl font-black text-rose-950">
            {data ? data.critical_gaps_count : '—'}
          </div>
          <div className="text-[11px] text-rose-600">Accuracy &lt; 60% or lapsed</div>
        </button>

        <button
          type="button"
          onClick={() =>
            setSelectedFilter(
              selectedFilter === 'UNPRACTICED_FOUNDATION' ? 'ALL' : 'UNPRACTICED_FOUNDATION'
            )
          }
          className={`p-3 rounded-xl border text-left transition-all ${
            selectedFilter === 'UNPRACTICED_FOUNDATION'
              ? 'bg-amber-50 border-amber-300 ring-2 ring-amber-400/20'
              : 'bg-slate-50 border-slate-200/80 hover:bg-slate-100/70'
          }`}
        >
          <div className="flex items-center text-xs font-bold text-amber-700 mb-1">
            <BookOpen className="w-3.5 h-3.5 mr-1" />
            <span>Unpracticed</span>
          </div>
          <div className="text-2xl font-black text-amber-950">
            {data ? data.unpracticed_foundations_count : '—'}
          </div>
          <div className="text-[11px] text-amber-600">Lesson done, &lt; 5 attempts</div>
        </button>

        <button
          type="button"
          onClick={() => setSelectedFilter(selectedFilter === 'SOLIDIFYING' ? 'ALL' : 'SOLIDIFYING')}
          className={`p-3 rounded-xl border text-left transition-all ${
            selectedFilter === 'SOLIDIFYING'
              ? 'bg-blue-50 border-blue-300 ring-2 ring-blue-400/20'
              : 'bg-slate-50 border-slate-200/80 hover:bg-slate-100/70'
          }`}
        >
          <div className="flex items-center text-xs font-bold text-blue-700 mb-1">
            <Sparkles className="w-3.5 h-3.5 mr-1" />
            <span>Solidifying</span>
          </div>
          <div className="text-2xl font-black text-blue-950">
            {data ? data.solidifying_count : '—'}
          </div>
          <div className="text-[11px] text-blue-600">Active recall progression</div>
        </button>

        <button
          type="button"
          onClick={() => setSelectedFilter(selectedFilter === 'MASTERED' ? 'ALL' : 'MASTERED')}
          className={`p-3 rounded-xl border text-left transition-all ${
            selectedFilter === 'MASTERED'
              ? 'bg-emerald-50 border-emerald-300 ring-2 ring-emerald-400/20'
              : 'bg-slate-50 border-slate-200/80 hover:bg-slate-100/70'
          }`}
        >
          <div className="flex items-center text-xs font-bold text-emerald-700 mb-1">
            <CheckCircle className="w-3.5 h-3.5 mr-1" />
            <span>Mastered</span>
          </div>
          <div className="text-2xl font-black text-emerald-950">
            {data ? data.mastered_count : '—'}
          </div>
          <div className="text-[11px] text-emerald-600">Acc &ge; 80% &amp; SM-2 mature</div>
        </button>
      </div>

      {/* Search and Filter Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mb-4">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search by topic, subject, or chapter..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
            aria-label="Search topics in diagnostic matrix"
          />
        </div>

        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={selectedFilter}
            onChange={(e) => setSelectedFilter(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            aria-label="Filter by diagnostic state"
          >
            <option value="ALL">All States ({topics.length})</option>
            <option value="CRITICAL_GAP">Critical Gaps ({data?.critical_gaps_count ?? 0})</option>
            <option value="UNPRACTICED_FOUNDATION">
              Unpracticed Foundations ({data?.unpracticed_foundations_count ?? 0})
            </option>
            <option value="SOLIDIFYING">Solidifying ({data?.solidifying_count ?? 0})</option>
            <option value="MASTERED">Mastered ({data?.mastered_count ?? 0})</option>
            <option value="NOT_STARTED">Not Started</option>
          </select>
        </div>
      </div>

      {/* Table Container */}
      {loading ? (
        <div className="h-48 flex items-center justify-center text-sm text-slate-400">
          Loading diagnostic matrix...
        </div>
      ) : filteredTopics.length === 0 ? (
        <div className="h-48 flex flex-col items-center justify-center text-sm text-slate-400">
          <Layers className="w-8 h-8 text-slate-300 mb-2" />
          <p>No topics match the selected diagnostic filter.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-200">
              <tr>
                <th scope="col" className="p-3">
                  Topic &amp; Subject
                </th>
                <th scope="col" className="p-3">
                  Lesson
                </th>
                <th scope="col" className="p-3">
                  Practice Calibration
                </th>
                <th scope="col" className="p-3">
                  Recall Status
                </th>
                <th scope="col" className="p-3">
                  Diagnostic State
                </th>
                <th scope="col" className="p-3">
                  Action Recommendation
                </th>
                <th scope="col" className="p-3 text-right">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredTopics.map((topic) => (
                <tr key={topic.topic_id} className="hover:bg-slate-50/70 transition-colors">
                  {/* Topic Title & Context */}
                  <td className="p-3">
                    <div className="font-bold text-slate-900">{topic.topic_title}</div>
                    <div className="text-[11px] text-slate-500">
                      {topic.subject_name} • {topic.chapter_title}
                    </div>
                  </td>

                  {/* Lesson Progress Status */}
                  <td className="p-3 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold ${
                        topic.lesson_status === 'COMPLETED'
                          ? 'bg-emerald-50 text-emerald-700'
                          : topic.lesson_status === 'IN_PROGRESS'
                          ? 'bg-blue-50 text-blue-700'
                          : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {topic.lesson_status === 'COMPLETED'
                        ? 'Completed'
                        : topic.lesson_status === 'IN_PROGRESS'
                        ? 'In Progress'
                        : 'Not Started'}
                    </span>
                  </td>

                  {/* Practice Accuracy & Attempts */}
                  <td className="p-3 whitespace-nowrap">
                    <div>
                      <span className="font-semibold text-slate-800">
                        {topic.total_attempts}{' '}
                        {topic.total_attempts === 1 ? 'attempt' : 'attempts'}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-500">
                      {topic.observed_accuracy_percentage !== null
                        ? `${topic.observed_accuracy_percentage}% observed`
                        : 'Uncalibrated'}
                    </div>
                  </td>

                  {/* Recall Status */}
                  <td className="p-3 whitespace-nowrap">
                    {topic.review_status ? (
                      <div>
                        <span className="font-semibold text-indigo-700">
                          {topic.review_status}
                        </span>
                        {topic.review_interval_days !== null && (
                          <span className="text-[11px] text-slate-500 ml-1">
                            ({topic.review_interval_days}d interval)
                          </span>
                        )}
                        {topic.is_review_overdue && (
                          <div className="text-[10px] text-rose-600 font-bold">Overdue</div>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-400 italic">Not queued</span>
                    )}
                  </td>

                  {/* Diagnostic State Badge */}
                  <td className="p-3 whitespace-nowrap">{getStateBadge(topic.diagnostic_state)}</td>

                  {/* Action Recommendation */}
                  <td className="p-3 text-[11px] text-slate-600 max-w-xs">
                    {topic.action_recommendation}
                  </td>

                  {/* Action Buttons */}
                  <td className="p-3 text-right whitespace-nowrap">
                    {onStartPractice && (
                      <button
                        onClick={() => onStartPractice(topic.topic_id, topic.topic_title)}
                        className="inline-flex items-center px-2.5 py-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 rounded-lg transition-all"
                        title={`Practice ${topic.topic_title}`}
                      >
                        <span>Practice</span>
                        <ArrowRight className="w-3 h-3 ml-1" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
