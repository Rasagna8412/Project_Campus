import React, { useMemo } from 'react';
import katex from 'katex';

interface LessonContentRendererProps {
  content: string;
}

/**
 * Parses inline and display LaTeX math surrounded by $ or $$
 */
function renderMathInText(text: string): string {
  // First, replace display math $$...$$
  let processed = text.replace(/\$\$([\s\S]*?)\$\$/g, (_, math) => {
    try {
      return `<div class="my-3 overflow-x-auto py-1 text-center font-serif">${katex.renderToString(math.trim(), {
        displayMode: true,
        throwOnError: false,
      })}</div>`;
    } catch {
      return `<div class="my-2 p-2 bg-rose-50 text-rose-700 font-mono text-sm rounded">${math}</div>`;
    }
  });

  // Next, replace inline math $...$ (avoiding double $$ or empty $)
  processed = processed.replace(/(?<!\$)\$([^$\n]+?)\$(?!\$)/g, (_, math) => {
    try {
      return katex.renderToString(math.trim(), {
        displayMode: false,
        throwOnError: false,
      });
    } catch {
      return `<span class="px-1 py-0.5 bg-rose-50 text-rose-700 font-mono text-xs rounded">${math}</span>`;
    }
  });

  return processed;
}

/**
 * Formats basic Markdown structures: bold, italic, code, headings, lists, tables
 */
function renderMarkdown(content: string): string {
  const lines = content.split('\n');
  const result: string[] = [];
  let inList = false;
  let inTable = false;

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    // Table divider line: | :--- | :--- |
    if (trimmed.startsWith('|') && trimmed.includes('---')) {
      continue;
    }

    // Table row
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      const cells = trimmed
        .slice(1, -1)
        .split('|')
        .map((c) => c.trim());

      if (!inTable) {
        inTable = true;
        result.push('<div class="overflow-x-auto my-4"><table class="min-w-full divide-y divide-slate-200 border border-slate-200 rounded-lg text-sm">');
        result.push('<thead class="bg-slate-50"><tr class="divide-x divide-slate-200">');
        for (const cell of cells) {
          result.push(`<th class="px-4 py-2.5 text-left font-semibold text-slate-700">${renderMathInText(cell)}</th>`);
        }
        result.push('</tr></thead><tbody class="divide-y divide-slate-200 bg-white">');
      } else {
        result.push('<tr class="divide-x divide-slate-200 hover:bg-slate-50/50">');
        for (const cell of cells) {
          result.push(`<td class="px-4 py-2 text-slate-700">${renderMathInText(cell)}</td>`);
        }
        result.push('</tr>');
      }
      continue;
    } else if (inTable) {
      inTable = false;
      result.push('</tbody></table></div>');
    }

    // Close open list if line is not a list item
    if (inList && !trimmed.startsWith('* ') && !trimmed.startsWith('- ') && !/^\d+\.\s/.test(trimmed)) {
      inList = false;
      result.push('</ul>');
    }

    // Empty line
    if (!trimmed) {
      continue;
    }

    // Headings
    if (trimmed.startsWith('#### ')) {
      result.push(`<h4 class="text-base font-bold text-slate-800 mt-4 mb-2">${renderMathInText(trimmed.slice(5))}</h4>`);
      continue;
    }
    if (trimmed.startsWith('### ')) {
      result.push(`<h3 class="text-lg font-bold text-slate-900 mt-5 mb-2">${renderMathInText(trimmed.slice(4))}</h3>`);
      continue;
    }
    if (trimmed.startsWith('## ')) {
      result.push(`<h2 class="text-xl font-bold text-slate-900 mt-6 mb-3 border-b pb-1 border-slate-200">${renderMathInText(trimmed.slice(3))}</h2>`);
      continue;
    }

    // Bullet lists
    if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      if (!inList) {
        inList = true;
        result.push('<ul class="list-disc pl-5 my-2 space-y-1 text-slate-700">');
      }
      const itemText = trimmed.slice(2);
      result.push(`<li>${renderMathInText(formatInlineMarkdown(itemText))}</li>`);
      continue;
    }

    // Numbered lists
    const numMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
    if (numMatch) {
      result.push(
        `<div class="flex items-start space-x-2 my-2 text-slate-700">
          <span class="font-semibold text-brand-600">${numMatch[1]}.</span>
          <div class="flex-1">${renderMathInText(formatInlineMarkdown(numMatch[2]))}</div>
        </div>`
      );
      continue;
    }

    // Regular paragraph
    result.push(`<p class="my-2 leading-relaxed text-slate-700">${renderMathInText(formatInlineMarkdown(rawLine))}</p>`);
  }

  if (inTable) {
    result.push('</tbody></table></div>');
  }
  if (inList) {
    result.push('</ul>');
  }

  return result.join('\n');
}

function formatInlineMarkdown(text: string): string {
  // Bold: **text**
  let s = text.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-slate-900">$1</strong>');
  // Italic: *text* (unless inside math)
  s = s.replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em class="italic">$1</em>');
  // Inline code: `code`
  s = s.replace(/`([^`]+)`/g, '<code class="bg-slate-100 text-slate-800 px-1 py-0.5 rounded text-sm font-mono">$1</code>');
  return s;
}

export const LessonContentRenderer: React.FC<LessonContentRendererProps> = ({ content }) => {
  const renderedHtml = useMemo(() => {
    return renderMarkdown(content);
  }, [content]);

  return (
    <div
      className="prose prose-slate max-w-none text-slate-700"
      dangerouslySetInnerHTML={{ __html: renderedHtml }}
    />
  );
};
