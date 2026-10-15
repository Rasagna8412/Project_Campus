import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  Flag,
  ArrowRight,
  Loader2,
  BookOpen,
} from 'lucide-react';
import { QuestionEvaluation, StudentQuestion } from '../../types/assessment';
import { renderMathInText, renderMarkdown } from '../curriculum/LessonContentRenderer';
import { ErrataModal } from './ErrataModal';

interface QuestionCardProps {
  question: StudentQuestion;
  questionNumber: number;
  totalQuestions: number;
  onAnswerSubmit: (payload: {
    question_id: string;
    selected_options?: string[];
    numerical_value?: number;
    integer_value?: number;
    time_spent_seconds: number;
  }) => Promise<QuestionEvaluation>;
  onNext?: () => void;
  isLast?: boolean;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({
  question,
  questionNumber,
  totalQuestions,
  onAnswerSubmit,
  onNext,
  isLast = false,
}) => {
  // Input state
  const [selectedOptions, setSelectedOptions] = useState<string[]>([]);
  const [numericalInput, setNumericalInput] = useState<string>('');
  const [integerInput, setIntegerInput] = useState<string>('');

  // Evaluation & submission state
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [evaluation, setEvaluation] = useState<QuestionEvaluation | null>(null);
  const [startTime] = useState<number>(Date.now());
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Errata modal state
  const [isErrataOpen, setIsErrataOpen] = useState<boolean>(false);

  // Handlers for option selection
  const handleToggleOption = (key: string) => {
    if (evaluation) return; // Answer already submitted

    if (question.question_type === 'single_choice') {
      setSelectedOptions([key]);
    } else if (question.question_type === 'multiple_choice') {
      if (selectedOptions.includes(key)) {
        setSelectedOptions(selectedOptions.filter((k) => k !== key));
      } else {
        setSelectedOptions([...selectedOptions, key]);
      }
    }
  };

  const isAnswerProvided = (): boolean => {
    if (question.question_type === 'single_choice' || question.question_type === 'multiple_choice') {
      return selectedOptions.length > 0;
    }
    if (question.question_type === 'numerical') {
      return numericalInput.trim() !== '' && !isNaN(Number(numericalInput));
    }
    if (question.question_type === 'integer') {
      return integerInput.trim() !== '' && Number.isInteger(Number(integerInput));
    }
    return false;
  };

  const handleSubmit = async () => {
    if (!isAnswerProvided() || isSubmitting || evaluation) return;

    setIsSubmitting(true);
    setSubmitError(null);

    const timeSpent = Math.max(1, Math.round((Date.now() - startTime) / 1000));

    try {
      const payload: {
        question_id: string;
        selected_options?: string[];
        numerical_value?: number;
        integer_value?: number;
        time_spent_seconds: number;
      } = {
        question_id: question.id,
        time_spent_seconds: timeSpent,
      };

      if (question.question_type === 'single_choice' || question.question_type === 'multiple_choice') {
        payload.selected_options = selectedOptions;
      } else if (question.question_type === 'numerical') {
        payload.numerical_value = parseFloat(numericalInput);
      } else if (question.question_type === 'integer') {
        payload.integer_value = parseInt(integerInput, 10);
      }

      const result = await onAnswerSubmit(payload);
      setEvaluation(result);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setSubmitError(err.message);
      } else {
        setSubmitError('Failed to evaluate answer. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Helper badge styles
  const getDifficultyBadge = () => {
    switch (question.difficulty) {
      case 'EASY':
        return (
          <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            Easy
          </span>
        );
      case 'HARD':
        return (
          <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            Hard
          </span>
        );
      case 'MEDIUM':
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            Medium
          </span>
        );
    }
  };

  const getQuestionTypeLabel = () => {
    switch (question.question_type) {
      case 'single_choice':
        return 'Single Choice (MCQ)';
      case 'multiple_choice':
        return 'Multiple Choice (Select all correct)';
      case 'numerical':
        return 'Numerical Value';
      case 'integer':
        return 'Integer Value';
      default:
        return 'Question';
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm">
      {/* Question Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6 pb-4 border-b border-slate-100">
        <div className="flex items-center space-x-2">
          <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-brand-50 text-brand-700 border border-brand-200">
            Question {questionNumber} of {totalQuestions}
          </span>
          <span className="text-xs text-slate-500 font-medium">
            {getQuestionTypeLabel()}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {getDifficultyBadge()}
          <button
            onClick={() => setIsErrataOpen(true)}
            className="text-xs text-slate-400 hover:text-slate-600 flex items-center space-x-1 p-1 rounded transition-colors"
            title="Report an error or issue with this question"
          >
            <Flag className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Report Issue</span>
          </button>
        </div>
      </div>

      {/* Question Content (Rendered LaTeX) */}
      <div
        className="text-base sm:text-lg text-slate-900 leading-relaxed font-medium mb-6 font-sans"
        dangerouslySetInnerHTML={{ __html: renderMarkdown(question.content_latex) }}
      />

      {/* Answer Input Area */}
      <div className="mb-6 space-y-3">
        {/* Single Choice / Multiple Choice Options */}
        {(question.question_type === 'single_choice' || question.question_type === 'multiple_choice') && (
          <div className="space-y-2.5">
            {question.options.map((opt) => {
              const isSelected = selectedOptions.includes(opt.option_key);
              const isCorrectOpt = evaluation?.correct_options?.includes(opt.option_key);
              const isWrongOpt = evaluation && isSelected && !isCorrectOpt;

              let cardStyle = 'border-slate-200 hover:border-brand-300 hover:bg-slate-50/50 bg-white';
              let badgeStyle = 'bg-slate-100 text-slate-700 border-slate-200';

              if (evaluation) {
                if (isCorrectOpt) {
                  cardStyle = 'border-emerald-300 bg-emerald-50/60 ring-1 ring-emerald-300';
                  badgeStyle = 'bg-emerald-600 text-white border-emerald-600';
                } else if (isWrongOpt) {
                  cardStyle = 'border-rose-300 bg-rose-50/60 ring-1 ring-rose-300';
                  badgeStyle = 'bg-rose-600 text-white border-rose-600';
                } else {
                  cardStyle = 'border-slate-200 opacity-60 bg-white';
                }
              } else if (isSelected) {
                cardStyle = 'border-brand-500 bg-brand-50/50 ring-1 ring-brand-500';
                badgeStyle = 'bg-brand-600 text-white border-brand-600';
              }

              return (
                <button
                  key={opt.id}
                  type="button"
                  disabled={!!evaluation}
                  onClick={() => handleToggleOption(opt.option_key)}
                  className={`w-full text-left p-4 rounded-xl border transition-all flex items-start space-x-3.5 ${cardStyle}`}
                >
                  <span
                    className={`flex-shrink-0 w-7 h-7 rounded-lg border font-bold text-xs flex items-center justify-center transition-colors ${badgeStyle}`}
                  >
                    {opt.option_key}
                  </span>
                  <div
                    className="flex-grow pt-0.5 text-sm sm:text-base text-slate-800 leading-normal"
                    dangerouslySetInnerHTML={{ __html: renderMathInText(opt.content_latex) }}
                  />
                  {evaluation && isCorrectOpt && (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                  )}
                  {evaluation && isWrongOpt && (
                    <XCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
                  )}
                </button>
              );
            })}
          </div>
        )}

        {/* Numerical Input */}
        {question.question_type === 'numerical' && (
          <div className="max-w-xs space-y-2">
            <label
              htmlFor={`num-input-${question.id}`}
              className="block text-xs font-semibold text-slate-700"
            >
              Enter Numerical Answer
            </label>
            <input
              id={`num-input-${question.id}`}
              type="number"
              step="any"
              disabled={!!evaluation}
              value={numericalInput}
              onChange={(e) => setNumericalInput(e.target.value)}
              placeholder="e.g. 1.25"
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-slate-900 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:bg-slate-50 disabled:text-slate-500"
            />
            {evaluation && (
              <p className="text-xs text-slate-600 font-medium">
                Accepted value: <span className="font-mono font-bold text-slate-900">{evaluation.correct_numerical}</span>
              </p>
            )}
          </div>
        )}

        {/* Integer Input */}
        {question.question_type === 'integer' && (
          <div className="max-w-xs space-y-2">
            <label
              htmlFor={`int-input-${question.id}`}
              className="block text-xs font-semibold text-slate-700"
            >
              Enter Integer Answer (0 to 9, or integer)
            </label>
            <input
              id={`int-input-${question.id}`}
              type="number"
              step="1"
              disabled={!!evaluation}
              value={integerInput}
              onChange={(e) => setIntegerInput(e.target.value)}
              placeholder="e.g. 4"
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-slate-900 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:bg-slate-50 disabled:text-slate-500"
            />
            {evaluation && (
              <p className="text-xs text-slate-600 font-medium">
                Correct integer: <span className="font-mono font-bold text-slate-900">{evaluation.correct_integer}</span>
              </p>
            )}
          </div>
        )}
      </div>

      {/* Error message */}
      {submitError && (
        <div
          role="alert"
          className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start space-x-2"
        >
          <XCircle className="w-4 h-4 text-rose-600 mt-0.5 flex-shrink-0" />
          <span>{submitError}</span>
        </div>
      )}

      {/* Action Footer: Submit or Next */}
      {!evaluation ? (
        <div className="flex items-center justify-between pt-4 border-t border-slate-100">
          <div className="text-xs text-slate-400">
            {question.question_type === 'multiple_choice'
              ? 'Select all options that apply before submitting.'
              : 'Select your answer and click submit for verified feedback.'}
          </div>

          <button
            onClick={handleSubmit}
            disabled={!isAnswerProvided() || isSubmitting}
            className="inline-flex items-center space-x-2 px-6 py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-semibold text-sm rounded-xl transition-all shadow-sm disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Evaluating...</span>
              </>
            ) : (
              <span>Submit Answer</span>
            )}
          </button>
        </div>
      ) : (
        <div className="space-y-6 pt-4 border-t border-slate-100">
          {/* Feedback Banner */}
          <div
            className={`p-4 rounded-xl border flex items-start space-x-3 ${
              evaluation.is_correct
                ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                : 'bg-rose-50 border-rose-200 text-rose-900'
            }`}
          >
            {evaluation.is_correct ? (
              <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-0.5" />
            ) : (
              <XCircle className="w-6 h-6 text-rose-600 flex-shrink-0 mt-0.5" />
            )}
            <div>
              <h4 className="font-bold text-sm sm:text-base">
                {evaluation.is_correct ? 'Correct! Outstanding work.' : 'Incorrect Answer'}
              </h4>
              <p className="text-xs sm:text-sm mt-0.5 opacity-90">
                {evaluation.is_correct
                  ? 'Your derivation matches the verified solution.'
                  : 'Review the verified step-by-step educator solution below to master this concept.'}
              </p>
            </div>
          </div>

          {/* Verified Step-by-Step Educator Derivation */}
          {evaluation.explanation_latex && (
            <div className="bg-slate-50 rounded-xl border border-slate-200 p-5 sm:p-6">
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-brand-700 mb-3">
                <BookOpen className="w-4 h-4 text-brand-600" />
                <span>Verified Step-by-Step Solution</span>
              </div>
              <div
                className="prose prose-slate max-w-none text-sm sm:text-base text-slate-800 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: renderMarkdown(evaluation.explanation_latex) }}
              />
            </div>
          )}

          {/* Next Question Navigation */}
          {onNext && (
            <div className="flex justify-end pt-2">
              <button
                onClick={onNext}
                className="inline-flex items-center space-x-2 px-6 py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-semibold text-sm rounded-xl transition-all shadow-sm"
              >
                <span>{isLast ? 'Complete Practice Session' : 'Next Question'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Errata Modal */}
      <ErrataModal
        questionId={question.id}
        isOpen={isErrataOpen}
        onClose={() => setIsErrataOpen(false)}
      />
    </div>
  );
};
