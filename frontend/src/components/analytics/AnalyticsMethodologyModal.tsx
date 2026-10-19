import React, { useEffect, useRef } from 'react';
import { X, BookOpen, Target, CalendarCheck2, Brain, AlertOctagon } from 'lucide-react';

interface AnalyticsMethodologyModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AnalyticsMethodologyModal: React.FC<AnalyticsMethodologyModalProps> = ({
  isOpen,
  onClose,
}) => {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    closeButtonRef.current?.focus();

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      aria-labelledby="methodology-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white/95 backdrop-blur z-10">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h2 id="methodology-title" className="text-xl font-bold text-slate-900">
                Analytics &amp; Diagnostic Methodology
              </h2>
              <p className="text-xs text-slate-500">
                Mathematical formulas, calibration rules, and pedagogical classification logic.
              </p>
            </div>
          </div>
          <button
            ref={closeButtonRef}
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition-colors"
            aria-label="Close methodology guide"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 text-sm text-slate-700 leading-relaxed">
          {/* Section 1: Practice Volume & Accuracy */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-indigo-700 font-bold text-sm">
              <Target className="w-4 h-4" />
              <span>1. Practice Accuracy &amp; The 5-Attempt Calibration Rule</span>
            </div>
            <p className="text-xs text-slate-600">
              Observed accuracy is calculated strictly from completed question attempts:
            </p>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 font-mono text-xs text-slate-800 text-center">
              Accuracy % = (Correct Attempts / Total Question Attempts) × 100
            </div>
            <p className="text-xs text-slate-600">
              <strong className="text-slate-800">Calibration threshold:</strong> A topic requires a minimum of <strong className="text-slate-800">5 attempts</strong> before classification into performance tiers (Needs Review, Developing, Strong). Topics with fewer than 5 attempts are tagged as <span className="font-semibold text-amber-700">INSUFFICIENT DATA</span> to avoid score volatility from tiny sample sizes. Days with zero questions report null accuracy rather than misleading 0.0%.
            </p>
          </div>

          {/* Section 2: Study Plan Adherence */}
          <div className="space-y-2 pt-4 border-t border-slate-100">
            <div className="flex items-center space-x-2 text-blue-700 font-bold text-sm">
              <CalendarCheck2 className="w-4 h-4" />
              <span>2. Study Plan Adherence &amp; Non-Punitive Rest Days</span>
            </div>
            <p className="text-xs text-slate-600">
              Adherence measures goal execution against your selected preferred study days:
            </p>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 font-mono text-xs text-slate-800 text-center">
              Adherence % = (Goals Met on Preferred Days / Total Preferred Days) × 100
            </div>
            <p className="text-xs text-slate-600">
              <strong className="text-slate-800">Non-punitive rest days:</strong> Days designated as non-preferred (rest days) are completely excluded from the denominator. Missed days do not accumulate in an unmanageable snowball; uncompleted tasks are cleanly rolled forward as skipped without inflating subsequent daily quotas.
            </p>
          </div>

          {/* Section 3: Spaced Repetition & Streaks */}
          <div className="space-y-2 pt-4 border-t border-slate-100">
            <div className="flex items-center space-x-2 text-violet-700 font-bold text-sm">
              <Brain className="w-4 h-4" />
              <span>3. Spaced Repetition Streaks &amp; Recall Aging</span>
            </div>
            <p className="text-xs text-slate-600">
              Memory recall relies on the SuperMemo SM-2 algorithm with IST calendar dates:
            </p>
            <ul className="list-disc pl-5 text-xs text-slate-600 space-y-1">
              <li>
                <strong className="text-slate-800">Active streak:</strong> Consecutive calendar days with at least one completed recall review. If you completed a review yesterday, your streak remains active throughout today until tonight.
              </li>
              <li>
                <strong className="text-slate-800">Overdue aging:</strong> Reviews overdue by 1–3 days carry mild memory decay risk, while 4+ days overdue indicates urgent intervention is needed before full retention loss occurs.
              </li>
              <li>
                <strong className="text-slate-800">Interval progression:</strong> Intervals expand exponentially based on ease factor (clamped between 1.30 and 2.50) with a maximum interval cap of 180 days.
              </li>
            </ul>
          </div>

          {/* Section 4: Diagnostic Matrix Hierarchy */}
          <div className="space-y-2 pt-4 border-t border-slate-100">
            <div className="flex items-center space-x-2 text-rose-700 font-bold text-sm">
              <AlertOctagon className="w-4 h-4" />
              <span>4. Diagnostic Topic Matrix Classification Hierarchy</span>
            </div>
            <p className="text-xs text-slate-600">
              Topics are evaluated across 5 diagnostic tiers in strict precedence order:
            </p>
            <div className="space-y-2 text-xs">
              <div className="p-2.5 rounded-xl bg-rose-50 border border-rose-200">
                <span className="font-bold text-rose-800">1. CRITICAL GAP:</span> Accuracy &lt; 60% with &ge; 5 attempts, or learning review item lapsed. Immediate lesson re-study and targeted drills recommended.
              </div>
              <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200">
                <span className="font-bold text-amber-800">2. UNPRACTICED FOUNDATION:</span> Lesson completed, but fewer than 5 practice questions attempted. Attempt drill to calibrate baseline.
              </div>
              <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-200">
                <span className="font-bold text-emerald-800">3. MASTERED:</span> Accuracy &ge; 80% across &ge; 5 attempts AND Review status reached MASTERED (repetition &ge; 5, interval &ge; 21d, EF &ge; 2.50).
              </div>
              <div className="p-2.5 rounded-xl bg-blue-50 border border-blue-200">
                <span className="font-bold text-blue-800">4. SOLIDIFYING:</span> Steady progress with accuracy &ge; 60% or active recall queue progression.
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                <span className="font-bold text-slate-700">5. NOT STARTED:</span> No lesson activity or questions attempted yet.
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-5 border-t border-slate-100 bg-slate-50 rounded-b-3xl flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-all shadow-sm"
          >
            Got it, close guide
          </button>
        </div>
      </div>
    </div>
  );
};
