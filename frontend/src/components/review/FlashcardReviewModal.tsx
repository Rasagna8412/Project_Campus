import React, { useState, useEffect, useCallback } from 'react';
import {
  X,
  RotateCw,
  AlertTriangle,
  Brain,
  Target,
} from 'lucide-react';
import { ReviewItemSummary } from '../../types/repetition';

interface FlashcardReviewModalProps {
  item: ReviewItemSummary | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmitRating: (itemId: string, score: number, timeSpentSeconds: number) => Promise<void>;
  onStartPractice?: (topicId: string, topicTitle?: string) => void;
}

interface RatingOption {
  score: number;
  label: string;
  sublabel: string;
  badgeClass: string;
  hoverClass: string;
  keyLabel: string;
}

const RATING_OPTIONS: RatingOption[] = [
  {
    score: 0,
    label: 'Blackout',
    sublabel: 'Complete memory lapse',
    badgeClass: 'bg-rose-100 text-rose-800 border-rose-300',
    hoverClass: 'hover:bg-rose-50 hover:border-rose-400',
    keyLabel: '0',
  },
  {
    score: 1,
    label: 'Wrong',
    sublabel: 'Incorrect; remembered on reveal',
    badgeClass: 'bg-orange-100 text-orange-800 border-orange-300',
    hoverClass: 'hover:bg-orange-50 hover:border-orange-400',
    keyLabel: '1',
  },
  {
    score: 2,
    label: 'Almost',
    sublabel: 'Partially correct or serious hesitation',
    badgeClass: 'bg-amber-100 text-amber-800 border-amber-300',
    hoverClass: 'hover:bg-amber-50 hover:border-amber-400',
    keyLabel: '2',
  },
  {
    score: 3,
    label: 'Hard',
    sublabel: 'Correct with substantial recall effort',
    badgeClass: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    hoverClass: 'hover:bg-yellow-50 hover:border-yellow-400',
    keyLabel: '3',
  },
  {
    score: 4,
    label: 'Good',
    sublabel: 'Correct after modest hesitation',
    badgeClass: 'bg-lime-100 text-lime-800 border-lime-300',
    hoverClass: 'hover:bg-lime-50 hover:border-lime-400',
    keyLabel: '4',
  },
  {
    score: 5,
    label: 'Easy',
    sublabel: 'Perfect, instantaneous recall',
    badgeClass: 'bg-emerald-100 text-emerald-800 border-emerald-300',
    hoverClass: 'hover:bg-emerald-50 hover:border-emerald-400',
    keyLabel: '5',
  },
];

export const FlashcardReviewModal: React.FC<FlashcardReviewModalProps> = ({
  item,
  isOpen,
  onClose,
  onSubmitRating,
  onStartPractice,
}) => {
  const [isFlipped, setIsFlipped] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [startTime, setStartTime] = useState<number>(Date.now());

  useEffect(() => {
    if (isOpen) {
      setIsFlipped(false);
      setSubmitting(false);
      setError(null);
      setStartTime(Date.now());
    }
  }, [isOpen, item]);

  const handleRate = useCallback(
    async (score: number) => {
      if (!item || submitting) return;
      setSubmitting(true);
      setError(null);
      const timeSpent = Math.max(1, Math.round((Date.now() - startTime) / 1000));
      try {
        await onSubmitRating(item.id, score, timeSpent);
        onClose();
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('Failed to submit review rating. Please try again.');
        }
        setSubmitting(false);
      }
    },
    [item, submitting, startTime, onSubmitRating, onClose]
  );

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === ' ' || e.key === 'Enter') {
        if (!isFlipped) {
          e.preventDefault();
          setIsFlipped(true);
        }
      } else if (isFlipped && !submitting && ['0', '1', '2', '3', '4', '5'].includes(e.key)) {
        e.preventDefault();
        const score = parseInt(e.key, 10);
        handleRate(score);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isFlipped, submitting, onClose, handleRate]);

  if (!isOpen || !item) return null;

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="review-modal-title"
    >
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-xl w-full border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header Bar */}
        <div className="p-5 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-indigo-300">
              <Brain className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2 text-[10px] uppercase font-bold tracking-wider text-indigo-300">
                <span>{item.subject_name}</span>
                <span>•</span>
                <span>{item.chapter_title}</span>
              </div>
              <h2 id="review-modal-title" className="text-base sm:text-lg font-bold leading-tight">
                Active Recall Drill
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close active recall modal"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Schedule Metadata Banner */}
        <div className="px-5 py-3 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center space-x-3 text-slate-600">
            <span>
              Repetition: <strong className="text-slate-900">#{item.repetition_count}</strong>
            </span>
            <span>•</span>
            <span>
              Interval:{' '}
              <strong className="text-slate-900">
                {item.interval_days} {item.interval_days === 1 ? 'day' : 'days'}
              </strong>
            </span>
            <span>•</span>
            <span>
              Ease Factor: <strong className="text-slate-900">{item.ease_factor != null ? item.ease_factor.toFixed(2) : '2.50'}</strong>
            </span>
          </div>

          <span
            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
              item.status === 'MASTERED'
                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                : item.status === 'REVIEW'
                ? 'bg-indigo-100 text-indigo-800 border border-indigo-300'
                : 'bg-amber-100 text-amber-800 border border-amber-300'
            }`}
          >
            {item.status}
          </span>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="p-4 bg-rose-50 border-b border-rose-200 text-xs text-rose-800 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Flashcard Area */}
        <div className="p-6">
          <div
            className={`min-h-[220px] rounded-2xl border-2 p-6 flex flex-col justify-between transition-all duration-300 ${
              isFlipped
                ? 'bg-gradient-to-br from-indigo-50/50 via-white to-brand-50/30 border-indigo-300 shadow-sm'
                : 'bg-slate-50 border-dashed border-slate-300 hover:border-slate-400'
            }`}
          >
            <div>
              <div className="flex items-center justify-between text-xs text-slate-400 font-semibold mb-2">
                <span>{isFlipped ? 'Topic Concepts & Self-Assessment' : 'Recall Prompt'}</span>
                <span className="text-[11px] font-mono">
                  {item.sample_question_count} practice questions available
                </span>
              </div>

              <h3 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                {item.topic_title}
              </h3>

              {!isFlipped ? (
                <div className="mt-4 space-y-2 text-slate-600 text-sm leading-relaxed">
                  <p>
                    Pause for a moment before flipping. Actively retrieve the foundational principles, key formulas, core definitions, and edge cases associated with <strong>{item.topic_title}</strong> from memory.
                  </p>
                  <p className="text-xs text-slate-400 italic">
                    Press <kbd className="px-1.5 py-0.5 rounded bg-slate-200 text-slate-800 font-mono text-[10px]">Space</kbd> or click below to reveal the self-assessment options.
                  </p>
                </div>
              ) : (
                <div className="mt-4 space-y-3 text-sm text-slate-700">
                  <p className="leading-relaxed">
                    How well did you recall the key principles of this topic without looking?
                  </p>
                  <div className="p-3 bg-white/80 rounded-xl border border-indigo-100 text-xs text-slate-600">
                    <p className="font-semibold text-slate-800 mb-1">
                      SM-2 Algorithm Calibration:
                    </p>
                    <ul className="list-disc list-inside space-y-0.5 text-slate-500">
                      <li>Scores 3–5 advance your review interval and strengthen memory retention.</li>
                      <li>Scores 0–2 reset your interval to 1 day for prompt reinforcement.</li>
                    </ul>
                  </div>
                </div>
              )}
            </div>

            {/* Flip Card Action Button */}
            {!isFlipped ? (
              <div className="mt-6 flex justify-center">
                <button
                  type="button"
                  onClick={() => setIsFlipped(true)}
                  className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white shadow transition-all hover:scale-[1.02]"
                >
                  <RotateCw className="w-4 h-4" />
                  <span>Reveal Self-Assessment (Space / Enter)</span>
                </button>
              </div>
            ) : null}
          </div>

          {/* Rating Scale Selection Buttons (Visible only when flipped) */}
          {isFlipped && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Select Your Recall Quality (0 to 5)
                </h4>
                <span className="text-[11px] text-slate-400 font-mono">
                  Keys 0–5 supported
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                {RATING_OPTIONS.map((opt) => (
                  <button
                    key={opt.score}
                    type="button"
                    disabled={submitting}
                    onClick={() => handleRate(opt.score)}
                    className={`p-3 rounded-xl border text-left transition-all flex flex-col justify-between ${
                      opt.badgeClass
                    } ${opt.hoverClass} disabled:opacity-50`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-black text-sm">{opt.label}</span>
                      <span className="w-5 h-5 rounded-full bg-white/80 text-slate-700 font-mono text-[11px] font-bold flex items-center justify-center border border-slate-200">
                        {opt.keyLabel}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-600 leading-tight">
                      {opt.sublabel}
                    </span>
                  </button>
                ))}
              </div>

              {/* Optional: Deep Practice Link */}
              {onStartPractice && item.sample_question_count > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Need problem-solving practice first?</span>
                  <button
                    type="button"
                    onClick={() => {
                      onClose();
                      onStartPractice(item.topic_id, item.topic_title);
                    }}
                    className="inline-flex items-center space-x-1 font-bold text-brand-600 hover:text-brand-700"
                  >
                    <Target className="w-3.5 h-3.5" />
                    <span>Launch Topic Drill</span>
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
