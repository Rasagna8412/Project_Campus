import React, { useState } from 'react';
import { Map, CheckCircle2, Circle, ChevronDown, ChevronRight, BookOpen } from 'lucide-react';
import { CurriculumRoadmap } from '../../types/planner';

interface CurriculumRoadmapCardProps {
  roadmap: CurriculumRoadmap | null;
  loading: boolean;
  onOpenLessons?: () => void;
}

export const CurriculumRoadmapCard: React.FC<CurriculumRoadmapCardProps> = ({
  roadmap,
  loading,
  onOpenLessons,
}) => {
  const [activeSubjectIdx, setActiveSubjectIdx] = useState<number>(0);
  const [expandedChapterIds, setExpandedChapterIds] = useState<Record<string, boolean>>({});

  if (loading && !roadmap) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm animate-pulse space-y-4">
        <div className="h-6 w-48 bg-slate-200 rounded"></div>
        <div className="h-20 bg-slate-100 rounded-xl"></div>
        <div className="h-40 bg-slate-50 rounded-xl"></div>
      </div>
    );
  }

  if (!roadmap || !Array.isArray(roadmap.subjects) || roadmap.subjects.length === 0) {
    return null;
  }

  const activeSubject = roadmap.subjects[activeSubjectIdx] || roadmap.subjects[0];

  const toggleChapter = (chapterId: string) => {
    setExpandedChapterIds((prev) => ({
      ...prev,
      [chapterId]: !prev[chapterId],
    }));
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 sm:p-6 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-brand-700">
            <Map className="w-4 h-4 text-brand-600" />
            <span>Academic Curriculum Roadmap</span>
          </div>
          <h3 className="text-base sm:text-lg font-bold text-slate-900 mt-0.5">
            Syllabus Completion & Mastery Tracker
          </h3>
        </div>

        <div className="flex items-center space-x-3">
          <div className="text-right">
            <span className="text-xs text-slate-500 font-medium">Overall Syllabus</span>
            <div className="text-sm font-black text-brand-700">
              {roadmap.completed_lessons_count} / {roadmap.total_lessons_count} Lessons ({roadmap.overall_completion_percentage}%)
            </div>
          </div>
          {onOpenLessons && (
            <button
              onClick={onOpenLessons}
              className="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-800 transition-colors"
            >
              Browse Curriculum
            </button>
          )}
        </div>
      </div>

      {/* Subject Tabs */}
      {roadmap.subjects.length > 1 && (
        <div className="flex flex-wrap gap-2">
          {roadmap.subjects.map((subj, idx) => (
            <button
              key={subj.subject_id}
              onClick={() => setActiveSubjectIdx(idx)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
                activeSubjectIdx === idx
                  ? 'bg-brand-600 text-white border-brand-600 shadow-sm'
                  : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              <span>{subj.subject_name}</span>
              <span className="ml-2 text-[10px] opacity-80">
                {subj.completion_percentage}%
              </span>
            </button>
          ))}
        </div>
      )}

      {/* Active Subject Details */}
      {activeSubject && (
        <div className="space-y-4">
          {/* Subject Progress Bar */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="font-bold text-slate-900">
                {activeSubject.subject_name} Progress:{' '}
                <span className="text-slate-600 font-normal">
                  {activeSubject.completed_lessons} of {activeSubject.total_lessons} lessons completed
                </span>
              </span>
              <span className="font-extrabold text-brand-700">
                {activeSubject.completion_percentage}% Complete
              </span>
            </div>
            <div className="w-full h-2.5 bg-slate-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-brand-600 rounded-full transition-all duration-500"
                style={{ width: `${activeSubject.completion_percentage}%` }}
              ></div>
            </div>
          </div>

          {/* Chapter Progression List */}
          <div className="space-y-2">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              Chapters ({activeSubject.chapters.length})
            </div>

            <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
              {activeSubject.chapters.map((chap) => {
                const isExpanded = expandedChapterIds[chap.chapter_id];
                return (
                  <div key={chap.chapter_id} className="p-3.5 bg-white hover:bg-slate-50/50 transition-colors">
                    <div
                      onClick={() => toggleChapter(chap.chapter_id)}
                      className="flex items-center justify-between cursor-pointer select-none"
                    >
                      <div className="flex items-center space-x-3">
                        {chap.is_completed ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                        ) : (
                          <Circle className="w-4 h-4 text-slate-300 flex-shrink-0" />
                        )}
                        <div>
                          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mr-2">
                            Chapter {chap.chapter_number}
                          </span>
                          <span className="text-xs font-bold text-slate-900">
                            {chap.title}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <span className="text-[11px] font-mono text-slate-500">
                          {chap.completed_lessons} / {chap.total_lessons} Lessons
                        </span>
                        {chap.is_completed && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            Mastered
                          </span>
                        )}
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 text-slate-400" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-slate-400" />
                        )}
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="mt-3 pt-3 border-t border-slate-100 pl-7 text-xs text-slate-600 flex items-center justify-between">
                        <span>
                          Structured syllabus chapter with {chap.total_lessons} verified educational lesson modules.
                        </span>
                        {onOpenLessons && (
                          <button
                            onClick={onOpenLessons}
                            className="inline-flex items-center space-x-1 text-xs font-bold text-brand-600 hover:text-brand-800"
                          >
                            <BookOpen className="w-3.5 h-3.5" />
                            <span>View Lessons</span>
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
