import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Clock,
  HelpCircle,
  Lightbulb,
  PenTool,
  ShieldCheck,
  Sigma,
  Target,
} from 'lucide-react';
import { getLessonDetail } from '../../services/api';
import { LessonDetail, LessonSection, SectionType } from '../../types/content';
import { LessonContentRenderer } from './LessonContentRenderer';

export interface BreadcrumbItem {
  label: string;
  onClick?: () => void;
}

interface LessonViewerProps {
  lessonId: string;
  onBack: () => void;
  breadcrumbs?: BreadcrumbItem[];
  onStartPractice?: (topicId: string, topicTitle?: string) => void;
}

export const LessonViewer: React.FC<LessonViewerProps> = ({
  lessonId,
  onBack,
  breadcrumbs = [],
  onStartPractice,
}) => {
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    getLessonDetail(lessonId)
      .then((data) => {
        if (isMounted) {
          setLesson(data);
          setLoading(false);
        }
      })
      .catch((err: Error) => {
        if (isMounted) {
          setError(err.message || 'Failed to load lesson content');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [lessonId]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <div className="animate-pulse space-y-6">
          <div className="h-4 bg-slate-200 rounded w-1/4"></div>
          <div className="h-8 bg-slate-200 rounded w-3/4"></div>
          <div className="h-20 bg-slate-200 rounded-xl"></div>
          <div className="space-y-4">
            <div className="h-40 bg-slate-200 rounded-xl"></div>
            <div className="h-40 bg-slate-200 rounded-xl"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !lesson) {
    return (
      <div className="max-w-2xl mx-auto py-16 px-4 text-center">
        <div className="w-16 h-16 bg-rose-50 text-rose-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <HelpCircle className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">Lesson Unavailable</h2>
        <p className="text-slate-600 mb-6">
          {error || 'This lesson could not be found or has not been published for student access.'}
        </p>
        <button
          onClick={onBack}
          className="inline-flex items-center space-x-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-medium rounded-lg transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Curriculum</span>
        </button>
      </div>
    );
  }

  const renderSectionHeader = (sec: LessonSection) => {
    switch (sec.section_type as SectionType) {
      case 'KEY_FORMULA':
        return (
          <div className="flex items-center space-x-2 text-brand-700 font-semibold text-sm mb-3">
            <Sigma className="w-4 h-4 text-brand-600" />
            <span className="uppercase tracking-wider">Key Formulation & Derivation</span>
          </div>
        );
      case 'WORKED_EXAMPLE':
        return (
          <div className="flex items-center space-x-2 text-emerald-700 font-semibold text-sm mb-3">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span className="uppercase tracking-wider">Worked Examination Example</span>
          </div>
        );
      case 'NOTE':
        return (
          <div className="flex items-center space-x-2 text-amber-800 font-semibold text-sm mb-3">
            <Lightbulb className="w-4 h-4 text-amber-600" />
            <span className="uppercase tracking-wider">Pedagogical Note & Common Pitfalls</span>
          </div>
        );
      case 'CONCEPT':
      default:
        return (
          <div className="flex items-center space-x-2 text-slate-600 font-semibold text-sm mb-3">
            <BookOpen className="w-4 h-4 text-slate-500" />
            <span className="uppercase tracking-wider">Concept Foundation</span>
          </div>
        );
    }
  };

  const getSectionCardStyles = (secType: string) => {
    switch (secType as SectionType) {
      case 'KEY_FORMULA':
        return 'bg-brand-50/30 border-brand-200 border-l-4 border-l-brand-600';
      case 'WORKED_EXAMPLE':
        return 'bg-emerald-50/20 border-emerald-200 border-l-4 border-l-emerald-600';
      case 'NOTE':
        return 'bg-amber-50/25 border-amber-200 border-l-4 border-l-amber-500';
      case 'CONCEPT':
      default:
        return 'bg-white border-slate-200 border-l-4 border-l-slate-400';
    }
  };

  return (
    <article className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      {/* Breadcrumb Navigation */}
      <nav aria-label="Breadcrumb" className="mb-6">
        <ol className="flex flex-wrap items-center space-x-1 sm:space-x-2 text-sm text-slate-500">
          <li>
            <button
              onClick={onBack}
              className="hover:text-brand-600 flex items-center space-x-1 font-medium transition-colors"
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              <span>Back</span>
            </button>
          </li>
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={idx}>
              <li className="flex items-center">
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              </li>
              <li>
                {crumb.onClick ? (
                  <button
                    onClick={crumb.onClick}
                    className="hover:text-brand-600 hover:underline transition-colors"
                  >
                    {crumb.label}
                  </button>
                ) : (
                  <span className="text-slate-800 font-medium">{crumb.label}</span>
                )}
              </li>
            </React.Fragment>
          ))}
        </ol>
      </nav>

      {/* Lesson Header */}
      <header className="mb-8 border-b border-slate-200 pb-6">
        {/* Badges row */}
        <div className="flex flex-wrap items-center gap-2 mb-3">
          {lesson.is_verified && (
            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Verified Content</span>
            </span>
          )}
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span>{lesson.estimated_read_time_minutes} min read</span>
          </span>
        </div>

        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight leading-tight">
          {lesson.title}
        </h1>

        {lesson.summary && (
          <p className="mt-3 text-base sm:text-lg text-slate-600 leading-relaxed font-normal">
            {lesson.summary}
          </p>
        )}

        {lesson.provenance && (
          <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-500 flex items-start space-x-2">
            <BookOpen className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
            <span>{lesson.provenance}</span>
          </div>
        )}
      </header>

      {/* Learning Objectives */}
      {lesson.learning_objectives && lesson.learning_objectives.length > 0 && (
        <section
          aria-labelledby="learning-objectives-heading"
          className="mb-8 bg-brand-50/40 rounded-xl border border-brand-100 p-5 sm:p-6"
        >
          <div className="flex items-center space-x-2 text-brand-900 font-bold mb-3">
            <Target className="w-5 h-5 text-brand-600" />
            <h2 id="learning-objectives-heading" className="text-base sm:text-lg">
              Learning Objectives
            </h2>
          </div>
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm text-slate-700">
            {lesson.learning_objectives.map((obj, i) => (
              <li key={i} className="flex items-start space-x-2">
                <CheckCircle2 className="w-4 h-4 text-brand-600 flex-shrink-0 mt-0.5" />
                <span>{obj}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Ordered Sections */}
      <section aria-label="Lesson Sections" className="space-y-6">
        {lesson.sections.map((section) => (
          <div
            key={section.id}
            id={`section-${section.section_number}`}
            className={`rounded-xl border p-5 sm:p-7 shadow-sm transition-shadow ${getSectionCardStyles(
              section.section_type
            )}`}
          >
            {renderSectionHeader(section)}

            <h3 className="text-lg sm:text-xl font-bold text-slate-900 mb-4">
              {section.title}
            </h3>

            <LessonContentRenderer content={section.content_markdown} />
          </div>
        ))}
      </section>

      {/* Practice Topic Callout */}
      {onStartPractice && lesson.topic_id && (
        <section
          aria-label="Practice Topic"
          className="mt-10 bg-gradient-to-r from-brand-50 to-indigo-50 border border-brand-200 rounded-2xl p-6 sm:p-8 text-center shadow-sm"
        >
          <div className="w-12 h-12 rounded-xl bg-brand-600 text-white flex items-center justify-center mx-auto mb-3 shadow-md">
            <PenTool className="w-6 h-6" />
          </div>
          <h3 className="text-lg sm:text-xl font-extrabold text-slate-900 mb-2">
            Ready to Test Your Understanding?
          </h3>
          <p className="text-xs sm:text-sm text-slate-600 max-w-lg mx-auto mb-5 leading-relaxed">
            Consolidate your knowledge with deliberate practice questions, immediate feedback, and verified step-by-step educator derivations.
          </p>
          <button
            onClick={() => onStartPractice(lesson.topic_id, lesson.title)}
            className="inline-flex items-center space-x-2 px-6 py-3 bg-brand-600 hover:bg-brand-700 text-white font-bold text-sm rounded-xl shadow-md transition-all hover:scale-[1.02]"
          >
            <PenTool className="w-4 h-4" />
            <span>Practise Topic Questions</span>
          </button>
        </section>
      )}

      {/* Footer Navigation */}
      <footer className="mt-12 pt-6 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
        <button
          onClick={onBack}
          className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-5 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-medium rounded-lg transition-colors shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Topics</span>
        </button>

        <button
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-medium rounded-lg transition-colors shadow-sm"
        >
          <span>Back to Top</span>
        </button>
      </footer>
    </article>
  );
};
