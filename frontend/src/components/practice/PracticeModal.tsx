import React, { useState, useEffect } from 'react';
import {
  X,
  Award,
  XCircle,
  RotateCcw,
  BookOpen,
  Sparkles,
} from 'lucide-react';
import {
  createPracticeSession,
  getTopicQuestions,
  submitAnswer,
} from '../../services/api';
import {
  PracticeSession,
  QuestionEvaluation,
  StudentQuestion,
} from '../../types/assessment';
import { QuestionCard } from './QuestionCard';

interface PracticeModalProps {
  topicId: string;
  topicTitle?: string;
  isOpen: boolean;
  onClose: () => void;
  onOpenLessons?: () => void;
}

export const PracticeModal: React.FC<PracticeModalProps> = ({
  topicId,
  topicTitle = 'Topic Practice',
  isOpen,
  onClose,
  onOpenLessons,
}) => {
  const [questions, setQuestions] = useState<StudentQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Session tracking
  const [session, setSession] = useState<PracticeSession | null>(null);
  const [results, setResults] = useState<{ [questionId: string]: QuestionEvaluation }>({});
  const [isCompleted, setIsCompleted] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen || !topicId) return;

    let mounted = true;
    setLoading(true);
    setError(null);
    setCurrentIndex(0);
    setResults({});
    setIsCompleted(false);

    // Attempt to start a tracked session, fallback to public questions if unauthenticated
    const loadSessionOrQuestions = async () => {
      try {
        const sessionData = await createPracticeSession({ topic_id: topicId });
        if (mounted && sessionData.questions && sessionData.questions.length > 0) {
          setSession(sessionData);
          setQuestions(sessionData.questions);
          setLoading(false);
          return;
        }
      } catch {
        // May be unauthenticated or session start failed; fallback to fetching public questions
      }

      try {
        const qList = await getTopicQuestions(topicId);
        if (mounted) {
          setQuestions(qList);
          setSession(null);
          setLoading(false);
        }
      } catch (err: unknown) {
        if (mounted) {
          if (err instanceof Error) {
            setError(err.message);
          } else {
            setError('Failed to load topic practice questions.');
          }
          setLoading(false);
        }
      }
    };

    loadSessionOrQuestions();

    return () => {
      mounted = false;
    };
  }, [isOpen, topicId]);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const currentQuestion = questions[currentIndex];

  const handleAnswerSubmit = async (payload: {
    question_id: string;
    selected_options?: string[];
    numerical_value?: number;
    integer_value?: number;
    time_spent_seconds: number;
  }): Promise<QuestionEvaluation> => {
    const evalResult = await submitAnswer({
      ...payload,
      session_id: session?.id || null,
    });

    setResults((prev) => ({
      ...prev,
      [payload.question_id]: evalResult,
    }));

    return evalResult;
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    } else {
      setIsCompleted(true);
    }
  };

  const handleRestart = () => {
    setCurrentIndex(0);
    setResults({});
    setIsCompleted(false);
  };

  // Calculate session summary stats
  const totalAnswered = Object.keys(results).length;
  const correctCount = Object.values(results).filter((r) => r.is_correct).length;
  const accuracyPct =
    totalAnswered > 0 ? Math.round((correctCount / totalAnswered) * 100) : 0;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="practice-modal-title"
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-slate-50 rounded-2xl max-w-4xl w-full shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[92vh]">
        {/* Modal Top Header */}
        <div className="bg-white px-6 py-4 border-b border-slate-200 flex items-center justify-between flex-shrink-0">
          <div>
            <div className="flex items-center space-x-2 text-xs font-bold text-brand-700 uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Deliberate Practice Engine</span>
            </div>
            <h2 id="practice-modal-title" className="text-base sm:text-lg font-extrabold text-slate-900 mt-0.5">
              {topicTitle}
            </h2>
          </div>

          <div className="flex items-center space-x-3">
            {questions.length > 0 && !isCompleted && (
              <div className="hidden sm:flex items-center space-x-2 text-xs text-slate-500 font-semibold bg-slate-100 px-3 py-1.5 rounded-lg">
                <span>Progress:</span>
                <span className="text-brand-700 font-bold">
                  {totalAnswered} / {questions.length} answered
                </span>
              </div>
            )}
            <button
              onClick={onClose}
              aria-label="Close practice"
              className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Content Scroll Area */}
        <div className="p-4 sm:p-6 overflow-y-auto flex-grow">
          {loading ? (
            <div className="py-20 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600 mx-auto mb-3"></div>
              <p className="text-sm font-medium text-slate-600">
                Loading authentic curriculum questions...
              </p>
            </div>
          ) : error ? (
            <div className="py-12 text-center max-w-md mx-auto">
              <XCircle className="w-10 h-10 text-rose-500 mx-auto mb-3" />
              <h3 className="font-bold text-slate-900 text-base mb-1">
                Unable to Load Questions
              </h3>
              <p className="text-xs text-slate-600 mb-4">{error}</p>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-slate-200 hover:bg-slate-300 rounded-lg text-xs font-semibold text-slate-800 transition-colors"
              >
                Close
              </button>
            </div>
          ) : questions.length === 0 ? (
            <div className="py-16 text-center max-w-md mx-auto">
              <BookOpen className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <h3 className="font-bold text-slate-800 text-base mb-1">
                No Practice Questions Available Yet
              </h3>
              <p className="text-xs text-slate-500 mb-4">
                Questions for this topic are currently undergoing rigorous pedagogical review and fact-checking.
              </p>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-brand-600 hover:bg-brand-700 rounded-lg text-xs font-bold text-white transition-colors"
              >
                Return to Curriculum
              </button>
            </div>
          ) : isCompleted ? (
            /* Session Completed Summary Screen */
            <div className="max-w-lg mx-auto py-8 text-center bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
              <div className="w-16 h-16 rounded-full bg-brand-50 border-2 border-brand-200 flex items-center justify-center mx-auto mb-4">
                <Award className="w-8 h-8 text-brand-600" />
              </div>

              <h3 className="text-2xl font-extrabold text-slate-900 mb-1">
                Practice Session Complete!
              </h3>
              <p className="text-xs text-slate-500 mb-6">
                Topic: <span className="font-semibold text-slate-800">{topicTitle}</span>
              </p>

              {/* Accuracy & Score Stats */}
              <div className="grid grid-cols-3 gap-3 mb-6 p-4 bg-slate-50 rounded-xl border border-slate-200">
                <div>
                  <span className="text-[11px] font-semibold text-slate-500 uppercase">
                    Questions
                  </span>
                  <p className="text-xl font-extrabold text-slate-900 mt-0.5">
                    {questions.length}
                  </p>
                </div>
                <div>
                  <span className="text-[11px] font-semibold text-emerald-600 uppercase">
                    Correct
                  </span>
                  <p className="text-xl font-extrabold text-emerald-600 mt-0.5">
                    {correctCount}
                  </p>
                </div>
                <div>
                  <span className="text-[11px] font-semibold text-brand-600 uppercase">
                    Accuracy
                  </span>
                  <p className="text-xl font-extrabold text-brand-600 mt-0.5">
                    {accuracyPct}%
                  </p>
                </div>
              </div>

              {/* Pedagogical Encouragement */}
              <div className="p-4 rounded-xl bg-brand-50/50 border border-brand-100 text-xs text-slate-700 leading-relaxed mb-6 text-left">
                {accuracyPct >= 80 ? (
                  <p>
                    <strong className="text-brand-900">Excellent mastery!</strong> You demonstrated strong command over the foundational principles in this topic.
                  </p>
                ) : accuracyPct >= 50 ? (
                  <p>
                    <strong className="text-brand-900">Good effort!</strong> Review the verified derivations for any missed questions before advancing to higher difficulty problems.
                  </p>
                ) : (
                  <p>
                    <strong className="text-brand-900">Keep practising!</strong> We recommend re-reading the topic lesson to reinforce core formulas and problem-solving techniques.
                  </p>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                <button
                  onClick={handleRestart}
                  className="w-full sm:w-auto inline-flex items-center justify-center space-x-1.5 px-5 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-xl transition-colors shadow-sm"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Try Questions Again</span>
                </button>

                {onOpenLessons && (
                  <button
                    onClick={() => {
                      onClose();
                      onOpenLessons();
                    }}
                    className="w-full sm:w-auto inline-flex items-center justify-center space-x-1.5 px-5 py-2.5 bg-brand-50 hover:bg-brand-100 text-brand-700 font-semibold text-xs rounded-xl transition-colors border border-brand-200 shadow-sm"
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>Explore Lessons</span>
                  </button>
                )}

                <button
                  onClick={onClose}
                  className="w-full sm:w-auto inline-flex items-center justify-center space-x-1.5 px-6 py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs rounded-xl transition-colors shadow-sm"
                >
                  <span>Done</span>
                </button>
              </div>
            </div>
          ) : (
            /* Active Question View */
            <div className="space-y-4">
              {/* Question Navigation Stepper */}
              <div className="flex items-center space-x-2 overflow-x-auto pb-2">
                {questions.map((q, idx) => {
                  const evalResult = results[q.id];
                  let stepStyle = 'bg-white border-slate-200 text-slate-600 hover:border-slate-300';

                  if (evalResult) {
                    stepStyle = evalResult.is_correct
                      ? 'bg-emerald-50 border-emerald-300 text-emerald-700 font-bold'
                      : 'bg-rose-50 border-rose-300 text-rose-700 font-bold';
                  } else if (idx === currentIndex) {
                    stepStyle = 'bg-brand-600 border-brand-600 text-white font-bold shadow-sm';
                  }

                  return (
                    <button
                      key={q.id}
                      onClick={() => setCurrentIndex(idx)}
                      className={`flex-shrink-0 w-8 h-8 rounded-lg border text-xs flex items-center justify-center transition-all ${stepStyle}`}
                    >
                      {idx + 1}
                    </button>
                  );
                })}
              </div>

              {/* Current Question Card */}
              {currentQuestion && (
                <QuestionCard
                  key={currentQuestion.id}
                  question={currentQuestion}
                  questionNumber={currentIndex + 1}
                  totalQuestions={questions.length}
                  onAnswerSubmit={handleAnswerSubmit}
                  onNext={handleNext}
                  isLast={currentIndex === questions.length - 1}
                />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
