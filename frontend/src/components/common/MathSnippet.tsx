import React, { useMemo } from 'react';
import katex from 'katex';
import { BookOpen } from 'lucide-react';

interface MathSnippetProps {
  formula: string;
  label: string;
  context: string;
}

export const MathSnippet: React.FC<MathSnippetProps> = ({ formula, label, context }) => {
  const renderedHtml = useMemo(() => {
    try {
      return katex.renderToString(formula, {
        displayMode: true,
        throwOnError: false,
      });
    } catch {
      return `<code class="text-rose-600">${formula}</code>`;
    }
  }, [formula]);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:border-brand-300 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-brand-700 bg-brand-50 px-2 py-0.5 rounded">
          {label}
        </span>
        <span className="text-xs text-slate-400 flex items-center space-x-1">
          <BookOpen className="w-3.5 h-3.5" />
          <span>{context}</span>
        </span>
      </div>

      <div
        className="overflow-x-auto py-2 text-slate-800 text-center"
        dangerouslySetInnerHTML={{ __html: renderedHtml }}
      />
    </div>
  );
};
