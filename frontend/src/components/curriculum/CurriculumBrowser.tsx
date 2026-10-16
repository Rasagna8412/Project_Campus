import React, { useEffect, useState } from 'react';
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Compass,
  FileText,
  GraduationCap,
  Layers,
  PenTool,
  Sparkles,
} from 'lucide-react';
import {
  getCurricula,
  getStudentLessonProgress,
  getSubjectChapters,
  getTopicLessons,
} from '../../services/api';
import { CurriculumBoard, GradeStageItem, SubjectItem } from '../../types/auth';
import { Chapter, LessonSummary } from '../../types/content';
import { BreadcrumbItem } from './LessonViewer';

interface CurriculumBrowserProps {
  onSelectLesson: (lessonId: string, breadcrumbs: BreadcrumbItem[]) => void;
  onStartPractice?: (topicId: string, topicTitle?: string) => void;
  initialBoardCode?: string;
  initialGradeCode?: string;
}

export const CurriculumBrowser: React.FC<CurriculumBrowserProps> = ({
  onSelectLesson,
  onStartPractice,
  initialBoardCode,
  initialGradeCode,
}) => {
  const [boards, setBoards] = useState<CurriculumBoard[]>([]);
  const [loadingBoards, setLoadingBoards] = useState<boolean>(true);
  const [selectedBoard, setSelectedBoard] = useState<CurriculumBoard | null>(null);
  const [selectedGrade, setSelectedGrade] = useState<GradeStageItem | null>(null);
  const [selectedSubject, setSelectedSubject] = useState<SubjectItem | null>(null);

  // Chapters & Topics state
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loadingChapters, setLoadingChapters] = useState<boolean>(false);
  const [expandedChapterId, setExpandedChapterId] = useState<string | null>(null);

  // Topic lessons cache
  const [topicLessons, setTopicLessons] = useState<Record<string, LessonSummary[]>>({});
  const [loadingTopicId, setLoadingTopicId] = useState<string | null>(null);
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null);

  // Lesson progress tracking map (lessonId -> status)
  const [progressMap, setProgressMap] = useState<Record<string, string>>({});

  // Error state
  const [error, setError] = useState<string | null>(null);

  // Load lesson progress for authenticated student
  useEffect(() => {
    let mounted = true;
    if (getStudentLessonProgress) {
      Promise.resolve(getStudentLessonProgress())
        .then((records) => {
          if (mounted && Array.isArray(records)) {
            const map: Record<string, string> = {};
            records.forEach((r) => {
              map[r.lesson_id] = r.status;
            });
            setProgressMap(map);
          }
        })
        .catch(() => {
          // Unauthenticated guest browsing, map remains empty
        });
    }

    return () => {
      mounted = false;
    };
  }, []);

  // Load curricula boards on mount
  useEffect(() => {
    setLoadingBoards(true);
    getCurricula()
      .then((data) => {
        setBoards(data);
        if (data.length > 0) {
          // Preselect board if initialBoardCode matches
          const matchBoard = initialBoardCode
            ? data.find((b) => b.code === initialBoardCode)
            : data[0];
          const boardToUse = matchBoard || data[0];
          setSelectedBoard(boardToUse);

          if (boardToUse.grades && boardToUse.grades.length > 0) {
            const matchGrade = initialGradeCode
              ? boardToUse.grades.find((g) => g.code === initialGradeCode)
              : boardToUse.grades[0];
            const gradeToUse = matchGrade || boardToUse.grades[0];
            setSelectedGrade(gradeToUse);

            if (gradeToUse.subjects && gradeToUse.subjects.length > 0) {
              setSelectedSubject(gradeToUse.subjects[0]);
            }
          }
        }
        setLoadingBoards(false);
      })
      .catch((err: Error) => {
        setError(err.message || 'Failed to load curricula');
        setLoadingBoards(false);
      });
  }, [initialBoardCode, initialGradeCode]);

  // Load chapters when selectedSubject changes
  useEffect(() => {
    if (!selectedSubject) {
      setChapters([]);
      return;
    }

    setLoadingChapters(true);
    setError(null);
    setSelectedTopicId(null);

    getSubjectChapters(selectedSubject.id)
      .then((data) => {
        setChapters(data);
        if (data.length > 0) {
          setExpandedChapterId(data[0].id);
          // If first chapter has topics, load lessons for first topic
          if (data[0].topics && data[0].topics.length > 0) {
            const firstTopic = data[0].topics[0];
            handleSelectTopic(firstTopic.id);
          }
        }
        setLoadingChapters(false);
      })
      .catch((err: Error) => {
        setError(err.message || 'Failed to load subject chapters');
        setLoadingChapters(false);
      });
  }, [selectedSubject]);

  const handleSelectTopic = (topicId: string) => {
    setSelectedTopicId(topicId);
    if (!topicLessons[topicId]) {
      setLoadingTopicId(topicId);
      getTopicLessons(topicId)
        .then((lessons) => {
          setTopicLessons((prev) => ({ ...prev, [topicId]: lessons }));
          setLoadingTopicId(null);
        })
        .catch(() => {
          setLoadingTopicId(null);
        });
    }
  };

  const handleBoardChange = (board: CurriculumBoard) => {
    setSelectedBoard(board);
    if (board.grades && board.grades.length > 0) {
      const firstGrade = board.grades[0];
      setSelectedGrade(firstGrade);
      if (firstGrade.subjects && firstGrade.subjects.length > 0) {
        setSelectedSubject(firstGrade.subjects[0]);
      } else {
        setSelectedSubject(null);
      }
    } else {
      setSelectedGrade(null);
      setSelectedSubject(null);
    }
  };

  const handleGradeChange = (grade: GradeStageItem) => {
    setSelectedGrade(grade);
    if (grade.subjects && grade.subjects.length > 0) {
      setSelectedSubject(grade.subjects[0]);
    } else {
      setSelectedSubject(null);
    }
  };

  const buildBreadcrumbs = (lesson: LessonSummary, topicTitle: string, chapterTitle: string): BreadcrumbItem[] => {
    const crumbs: BreadcrumbItem[] = [];
    if (selectedBoard) {
      crumbs.push({ label: selectedBoard.code });
    }
    if (selectedGrade) {
      crumbs.push({ label: selectedGrade.name });
    }
    if (selectedSubject) {
      crumbs.push({ label: selectedSubject.name });
    }
    crumbs.push({ label: chapterTitle });
    crumbs.push({ label: topicTitle });
    crumbs.push({ label: lesson.title });
    return crumbs;
  };

  if (loadingBoards) {
    return (
      <div className="max-w-6xl mx-auto py-12 px-4">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-slate-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="h-24 bg-slate-200 rounded-xl"></div>
            <div className="h-24 bg-slate-200 rounded-xl"></div>
            <div className="h-24 bg-slate-200 rounded-xl"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      {/* Title & Introduction */}
      <div className="mb-8">
        <div className="flex items-center space-x-2 text-brand-600 font-semibold text-xs uppercase tracking-wider mb-2">
          <Compass className="w-4 h-4" />
          <span>Curriculum Content Library</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Explore Academic Lessons
        </h1>
        <p className="mt-1 text-slate-600 text-sm sm:text-base">
          Browse verified curriculum chapters, topics, and structured lessons with comprehensive mathematical formulations.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">
          {error}
        </div>
      )}

      {/* Curriculum Hierarchy Selectors */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 sm:p-6 mb-8 space-y-5">
        {/* Step 1: Board selection */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
            1. Educational Board / Exam
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {boards.map((b) => (
              <button
                key={b.id}
                onClick={() => handleBoardChange(b)}
                className={`p-3 rounded-xl border text-left transition-all flex items-center justify-between ${
                  selectedBoard?.id === b.id
                    ? 'border-brand-500 bg-brand-50/50 shadow-sm ring-1 ring-brand-500'
                    : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'
                }`}
              >
                <div>
                  <div className="font-bold text-slate-900 text-sm">{b.name}</div>
                  <div className="text-xs text-slate-500">{b.country_code} • {b.code}</div>
                </div>
                {selectedBoard?.id === b.id && (
                  <CheckCircle2 className="w-5 h-5 text-brand-600 flex-shrink-0" />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Step 2: Grade Stage */}
        {selectedBoard && selectedBoard.grades && selectedBoard.grades.length > 0 && (
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              2. Academic Level
            </label>
            <div className="flex flex-wrap gap-2">
              {selectedBoard.grades.map((g) => (
                <button
                  key={g.id}
                  onClick={() => handleGradeChange(g)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors flex items-center space-x-2 ${
                    selectedGrade?.id === g.id
                      ? 'bg-brand-600 text-white border-brand-600 shadow-sm'
                      : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <GraduationCap className="w-4 h-4" />
                  <span>{g.name}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Subject Tabs */}
        {selectedGrade && selectedGrade.subjects && selectedGrade.subjects.length > 0 && (
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              3. Subject
            </label>
            <div className="flex flex-wrap gap-2">
              {selectedGrade.subjects.map((s: SubjectItem) => (
                <button
                  key={s.id}
                  onClick={() => setSelectedSubject(s)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium border transition-all flex items-center space-x-2 ${
                    selectedSubject?.id === s.id
                      ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                      : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <BookOpen className="w-4 h-4" />
                  <span>{s.name}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Chapters, Topics & Lessons Content View */}
      {loadingChapters ? (
        <div className="py-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600 mx-auto mb-3"></div>
          <p className="text-slate-500 text-sm">Loading chapters and verified curriculum content...</p>
        </div>
      ) : chapters.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
          <div className="w-12 h-12 bg-slate-100 text-slate-400 rounded-full flex items-center justify-center mx-auto mb-3">
            <BookOpen className="w-6 h-6" />
          </div>
          <h3 className="font-bold text-slate-800 text-base mb-1">No Chapters Available Yet</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Content for this subject is currently undergoing editorial and pedagogical review. Check CBSE Class 12 Physics, Chemistry, or Mathematics for verified lessons.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Chapters & Topics (5 cols) */}
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                <Layers className="w-4 h-4 text-brand-600" />
                <span>Chapters & Topics</span>
              </h2>
              <span className="text-xs text-slate-500 font-medium">
                {chapters.length} Chapter{chapters.length === 1 ? '' : 's'}
              </span>
            </div>

            <div className="space-y-3">
              {chapters.map((chapter) => {
                const isExpanded = expandedChapterId === chapter.id;
                return (
                  <div
                    key={chapter.id}
                    className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm"
                  >
                    <button
                      onClick={() => setExpandedChapterId(isExpanded ? null : chapter.id)}
                      className="w-full p-4 text-left flex items-start justify-between hover:bg-slate-50/60 transition-colors"
                    >
                      <div className="flex-1 pr-3">
                        <div className="flex items-center space-x-2 text-xs font-semibold text-brand-600 uppercase tracking-wider mb-1">
                          <span>Chapter {chapter.chapter_number}</span>
                        </div>
                        <div className="font-bold text-slate-900 text-sm leading-snug">
                          {chapter.title}
                        </div>
                        {chapter.summary && (
                          <div className="text-xs text-slate-500 mt-1 line-clamp-2">
                            {chapter.summary}
                          </div>
                        )}
                      </div>
                      <ChevronDown
                        className={`w-5 h-5 text-slate-400 flex-shrink-0 transition-transform ${
                          isExpanded ? 'rotate-180' : ''
                        }`}
                      />
                    </button>

                    {isExpanded && chapter.topics && chapter.topics.length > 0 && (
                      <div className="border-t border-slate-100 bg-slate-50/40 p-2 space-y-1">
                        {chapter.topics.map((topic) => {
                          const isSelectedTopic = selectedTopicId === topic.id;
                          return (
                            <button
                              key={topic.id}
                              onClick={() => handleSelectTopic(topic.id)}
                              className={`w-full p-2.5 rounded-lg text-left text-xs sm:text-sm font-medium transition-all flex items-center justify-between ${
                                isSelectedTopic
                                  ? 'bg-brand-50 text-brand-900 font-bold border border-brand-200'
                                  : 'text-slate-700 hover:bg-white hover:text-slate-900 border border-transparent'
                              }`}
                            >
                              <div className="flex items-center space-x-2 truncate">
                                <span className="text-slate-400 font-mono text-xs">
                                  {chapter.chapter_number}.{topic.topic_number}
                                </span>
                                <span className="truncate">{topic.title}</span>
                              </div>
                              <div className="flex items-center space-x-1.5 flex-shrink-0 ml-2">
                                {topic.published_lessons_count > 0 && (
                                  <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                                    {topic.published_lessons_count} lesson{topic.published_lessons_count === 1 ? '' : 's'}
                                  </span>
                                )}
                                <ChevronRight className="w-4 h-4 text-slate-400" />
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Lessons for Selected Topic (7 cols) */}
          <div className="lg:col-span-7">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sticky top-6">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-4 pb-3 border-b border-slate-100">
                <div className="flex items-center space-x-2">
                  <h3 className="font-bold text-slate-900 text-base flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-brand-600" />
                    <span>Structured Lessons</span>
                  </h3>
                  {selectedTopicId && (
                    <span className="text-xs text-slate-500 font-medium">
                      (Topic {chapters.flatMap((c) => c.topics).find((t) => t.id === selectedTopicId)?.topic_number || ''})
                    </span>
                  )}
                </div>

                {selectedTopicId && onStartPractice && (
                  <button
                    onClick={() => {
                      const topic = chapters
                        .flatMap((c) => c.topics)
                        .find((t) => t.id === selectedTopicId);
                      onStartPractice(selectedTopicId, topic?.title);
                    }}
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-brand-50 hover:bg-brand-100 text-brand-700 font-bold text-xs rounded-lg transition-colors border border-brand-200 shadow-sm"
                  >
                    <PenTool className="w-3.5 h-3.5 text-brand-600" />
                    <span>Practise Questions</span>
                  </button>
                )}
              </div>

              {!selectedTopicId ? (
                <div className="py-12 text-center text-slate-500 text-sm">
                  <Sparkles className="w-8 h-8 text-brand-300 mx-auto mb-2" />
                  Select a topic from the left panel to explore its lessons.
                </div>
              ) : loadingTopicId === selectedTopicId ? (
                <div className="py-12 text-center">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-brand-600 mx-auto mb-2"></div>
                  <span className="text-xs text-slate-500">Loading published lessons...</span>
                </div>
              ) : (topicLessons[selectedTopicId] || []).length === 0 ? (
                <div className="py-8 text-center text-slate-500 text-sm">
                  <BookOpen className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                  <p className="font-medium text-slate-700">No Published Lessons in this Topic</p>
                  <p className="text-xs text-slate-400 mt-1">
                    Lessons for this specific topic are currently in drafting or pedagogical review.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {(topicLessons[selectedTopicId] || []).map((lesson) => {
                    const currentTopic = chapters
                      .flatMap((c) => c.topics)
                      .find((t) => t.id === selectedTopicId);
                    const currentChapter = chapters.find((c) =>
                      c.topics.some((t) => t.id === selectedTopicId)
                    );

                    return (
                      <div
                        key={lesson.id}
                        className="rounded-xl border border-slate-200 p-5 hover:border-brand-300 hover:shadow-md transition-all bg-white"
                      >
                        <div className="flex flex-wrap items-center gap-2 mb-2">
                          {lesson.is_verified && (
                            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                              <span>Verified</span>
                            </span>
                          )}
                          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs text-slate-500 bg-slate-100">
                            <Clock className="w-3 h-3" />
                            <span>{lesson.estimated_read_time_minutes} min</span>
                          </span>
                          {progressMap[lesson.id] === 'COMPLETED' ? (
                            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                              <span>Completed</span>
                            </span>
                          ) : progressMap[lesson.id] === 'IN_PROGRESS' ? (
                            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                              <Clock className="w-3 h-3 text-amber-600" />
                              <span>In Progress</span>
                            </span>
                          ) : Object.keys(progressMap).length > 0 ? (
                            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium text-slate-500 bg-slate-100">
                              <span>Not Started</span>
                            </span>
                          ) : null}
                        </div>

                        <h4 className="font-bold text-slate-900 text-base mb-1.5 leading-snug">
                          {lesson.title}
                        </h4>

                        {lesson.summary && (
                          <p className="text-xs sm:text-sm text-slate-600 line-clamp-2 mb-3">
                            {lesson.summary}
                          </p>
                        )}

                        {lesson.learning_objectives && lesson.learning_objectives.length > 0 && (
                          <div className="mb-4 text-xs text-slate-500">
                            <span className="font-semibold text-slate-700">Covers: </span>
                            {lesson.learning_objectives.slice(0, 2).join(' • ')}
                            {lesson.learning_objectives.length > 2 && ' ...'}
                          </div>
                        )}

                        <button
                          onClick={() =>
                            onSelectLesson(
                              lesson.id,
                              buildBreadcrumbs(
                                lesson,
                                currentTopic?.title || 'Topic',
                                currentChapter?.title || 'Chapter'
                              )
                            )
                          }
                          className="w-full inline-flex items-center justify-center space-x-2 px-4 py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-medium text-sm rounded-lg transition-colors shadow-sm"
                        >
                          <span>Read Full Lesson</span>
                          <ArrowRight className="w-4 h-4" />
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
