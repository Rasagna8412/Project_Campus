import React, { useState } from 'react';
import { AlertCircle, CheckCircle2, Flag, Loader2, X } from 'lucide-react';
import { reportQuestionErrata } from '../../services/api';
import { CreateErrataPayload, ErrataIssueType } from '../../types/assessment';

interface ErrataModalProps {
  questionId: string;
  isOpen: boolean;
  onClose: () => void;
}

const ISSUE_OPTIONS: { value: ErrataIssueType; label: string; description: string }[] = [
  {
    value: 'INCORRECT_ANSWER',
    label: 'Incorrect Answer Key',
    description: 'The marked answer is wrong or conflicts with the step-by-step derivation.',
  },
  {
    value: 'LATEX_RENDERING_ERROR',
    label: 'LaTeX / Math Rendering Issue',
    description: 'Math formulas are broken, illegible, or show rendering error codes.',
  },
  {
    value: 'AMBIGUOUS_QUESTION',
    label: 'Ambiguous or Incomplete Question',
    description: 'Essential variables, diagrams, or context are missing.',
  },
  {
    value: 'TYPO_OR_GRAMMAR',
    label: 'Typo or Grammatical Error',
    description: 'Spelling mistakes or phrasing issues in the question prompt.',
  },
  {
    value: 'OTHER',
    label: 'Other Quality Concern',
    description: 'Any other curriculum quality, syllabus mismatch, or pedagogical flaw.',
  },
];

export const ErrataModal: React.FC<ErrataModalProps> = ({
  questionId,
  isOpen,
  onClose,
}) => {
  const [issueType, setIssueType] = useState<ErrataIssueType>('INCORRECT_ANSWER');
  const [description, setDescription] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState<boolean>(false);

  React.useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isSubmitting) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, isSubmitting, onClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (description.trim().length < 10) {
      setErrorMessage('Please provide at least 10 characters describing the issue.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const payload: CreateErrataPayload = {
        issue_type: issueType,
        description: description.trim(),
      };
      await reportQuestionErrata(questionId, payload);
      setIsSuccess(true);
      setTimeout(() => {
        setIsSuccess(false);
        setDescription('');
        onClose();
      }, 1600);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to submit question report. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="errata-modal-title"
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose();
      }}
    >
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 relative animate-in fade-in zoom-in-95 duration-150">
        <button
          onClick={onClose}
          disabled={isSubmitting}
          aria-label="Close dialog"
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1 rounded-lg transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2.5 rounded-xl bg-amber-50 text-amber-700 border border-amber-200">
            <Flag className="w-5 h-5" />
          </div>
          <div>
            <h2 id="errata-modal-title" className="text-lg font-bold text-slate-900">
              Report Question Issue
            </h2>
            <p className="text-xs text-slate-500">
              Help us maintain verified, gold-standard educational content.
            </p>
          </div>
        </div>

        {isSuccess ? (
          <div className="py-8 text-center space-y-3">
            <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto" />
            <h3 className="font-bold text-slate-900 text-base">Report Submitted</h3>
            <p className="text-xs text-slate-600 max-w-xs mx-auto">
              Thank you! Our academic editorial team will review this question and verify its derivation.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {errorMessage && (
              <div
                role="alert"
                className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start space-x-2"
              >
                <AlertCircle className="w-4 h-4 text-rose-600 mt-0.5 flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            <div>
              <label
                htmlFor="errata-issue-type"
                className="block text-xs font-semibold text-slate-700 mb-1"
              >
                Nature of the Issue
              </label>
              <select
                id="errata-issue-type"
                value={issueType}
                onChange={(e) => setIssueType(e.target.value as ErrataIssueType)}
                className="w-full text-xs font-medium text-slate-800 bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                {ISSUE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-slate-500 mt-1">
                {ISSUE_OPTIONS.find((opt) => opt.value === issueType)?.description}
              </p>
            </div>

            <div>
              <label
                htmlFor="errata-description"
                className="block text-xs font-semibold text-slate-700 mb-1"
              >
                Specific Details (Minimum 10 characters)
              </label>
              <textarea
                id="errata-description"
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe where the error occurs (e.g. step 2 in the derivation, sign convention error, missing exponent in option C)..."
                className="w-full text-xs text-slate-800 bg-slate-50 border border-slate-200 rounded-lg p-3 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || description.trim().length < 10}
                className="px-5 py-2 text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 rounded-lg transition-colors shadow-sm disabled:opacity-50 flex items-center space-x-1.5"
              >
                {isSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Submit Report</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
