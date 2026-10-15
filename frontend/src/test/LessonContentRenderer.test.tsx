import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { LessonContentRenderer } from '../components/curriculum/LessonContentRenderer';

describe('LessonContentRenderer', () => {
  it('renders standard markdown headings and paragraphs', () => {
    const markdown = '## Chapter Overview\n\nThis is a fundamental concept in electrostatics.';
    const { container } = render(<LessonContentRenderer content={markdown} />);

    expect(container.querySelector('h2')).toHaveTextContent('Chapter Overview');
    expect(container.querySelector('p')).toHaveTextContent('This is a fundamental concept in electrostatics.');
  });

  it('renders bullet lists and inline bold text', () => {
    const markdown = '* First property of **electric charge**\n* Second property of **conservation**';
    const { container } = render(<LessonContentRenderer content={markdown} />);

    const listItems = container.querySelectorAll('li');
    expect(listItems.length).toBe(2);
    expect(container.querySelector('strong')).toHaveTextContent('electric charge');
  });

  it('renders inline math with KaTeX markup', () => {
    const markdown = 'The charge is denoted by $q = 1.6 \\times 10^{-19}\\text{ C}$.';
    const { container } = render(<LessonContentRenderer content={markdown} />);

    // KaTeX outputs elements with class "katex"
    const katexEl = container.querySelector('.katex');
    expect(katexEl).toBeInTheDocument();
  });

  it('renders display math equations in display mode', () => {
    const markdown = 'The Coulomb force formula is:\n\n$$F = \\frac{1}{4\\pi\\varepsilon_0} \\frac{q_1 q_2}{r^2}$$\n\nWhere $r$ is distance.';
    const { container } = render(<LessonContentRenderer content={markdown} />);

    const displayKatex = container.querySelector('.katex-display');
    expect(displayKatex).toBeInTheDocument();
  });

  it('renders markdown tables properly', () => {
    const markdown = '| Property | Value |\n| :--- | :--- |\n| Speed of Light | $3 \\times 10^8$ m/s |\n| Electron Mass | $9.1 \\times 10^{-31}$ kg |';
    const { container } = render(<LessonContentRenderer content={markdown} />);

    expect(container.querySelector('table')).toBeInTheDocument();
    expect(container.querySelectorAll('th').length).toBe(2);
    expect(container.querySelectorAll('tr').length).toBe(3); // 1 header + 2 body rows
  });
});
