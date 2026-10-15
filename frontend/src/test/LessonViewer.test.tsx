import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { LessonViewer } from '../components/curriculum/LessonViewer';
import * as api from '../services/api';
import { LessonDetail } from '../types/content';

vi.mock('../services/api');

const mockLessonDetail: LessonDetail = {
  id: 'lesson-123',
  topic_id: 'topic-456',
  title: "Coulomb's Law, Electrostatic Force, and Superposition",
  slug: 'coulombs-law-and-superposition',
  summary: 'In-depth analysis of electrostatic forces between stationary point charges.',
  learning_objectives: [
    "State Coulomb's Law in scalar and vector formulations",
    'Calculate the net electrostatic force using superposition',
  ],
  estimated_read_time_minutes: 12,
  status: 'PUBLISHED',
  display_order: 1,
  provenance: 'Aligned with CBSE Class 12 Physics (NCERT Chapter 1). Verified by Senior Faculty.',
  is_verified: true,
  created_at: '2026-10-15T10:00:00Z',
  updated_at: '2026-10-15T10:00:00Z',
  sections: [
    {
      id: 'sec-1',
      lesson_id: 'lesson-123',
      section_number: 1,
      title: "Statement of Coulomb's Law",
      content_markdown: 'Electrostatic force is proportional to charge product: $F = k \\frac{|q_1 q_2|}{r^2}$.',
      section_type: 'CONCEPT',
      display_order: 1,
    },
    {
      id: 'sec-2',
      lesson_id: 'lesson-123',
      section_number: 2,
      title: 'Vector Formulation & Permittivity',
      content_markdown: 'The vector form is: $$\\vec{F}_{12} = \\frac{1}{4\\pi\\varepsilon_0} \\frac{q_1 q_2}{r^2} \\hat{r}_{12}$$',
      section_type: 'KEY_FORMULA',
      display_order: 2,
    },
    {
      id: 'sec-3',
      lesson_id: 'lesson-123',
      section_number: 3,
      title: 'Worked Example: Net Force on Equilateral Triangle',
      content_markdown: '**Problem Statement:** Three identical charges are placed at vertices of an equilateral triangle.',
      section_type: 'WORKED_EXAMPLE',
      display_order: 3,
    },
    {
      id: 'sec-4',
      lesson_id: 'lesson-123',
      section_number: 4,
      title: 'Common Misconceptions with Permittivity',
      content_markdown: '* Note: Permittivity in a dielectric reduces the net force by factor $K$.',
      section_type: 'NOTE',
      display_order: 4,
    },
  ],
};

describe('LessonViewer Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders lesson detail, learning objectives, and ordered sections', async () => {
    vi.spyOn(api, 'getLessonDetail').mockResolvedValue(mockLessonDetail);
    const onBack = vi.fn();

    render(
      <LessonViewer
        lessonId="lesson-123"
        onBack={onBack}
        breadcrumbs={[
          { label: 'CBSE' },
          { label: 'Physics' },
          { label: "Coulomb's Law" },
        ]}
      />
    );

    // Verify title and summary
    await waitFor(() => {
      expect(
        screen.getByText("Coulomb's Law, Electrostatic Force, and Superposition")
      ).toBeInTheDocument();
    });

    expect(screen.getByText(/12 min read/i)).toBeInTheDocument();
    expect(screen.getByText(/Verified Content/i)).toBeInTheDocument();
    expect(screen.getByText(/Aligned with CBSE Class 12 Physics/i)).toBeInTheDocument();

    // Verify Learning Objectives
    expect(screen.getByText('Learning Objectives')).toBeInTheDocument();
    expect(
      screen.getByText("State Coulomb's Law in scalar and vector formulations")
    ).toBeInTheDocument();

    // Verify all 4 sections are rendered
    expect(screen.getByText("Statement of Coulomb's Law")).toBeInTheDocument();
    expect(screen.getByText('Vector Formulation & Permittivity')).toBeInTheDocument();
    expect(
      screen.getByText('Worked Example: Net Force on Equilateral Triangle')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Common Misconceptions with Permittivity')
    ).toBeInTheDocument();

    // Verify section badges
    expect(screen.getByText(/Key Formulation & Derivation/i)).toBeInTheDocument();
    expect(screen.getByText(/Worked Examination Example/i)).toBeInTheDocument();
    expect(screen.getByText(/Pedagogical Note/i)).toBeInTheDocument();

    // Verify back navigation
    const backBtn = screen.getByRole('button', { name: /^back to topics$/i });
    fireEvent.click(backBtn);
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it('renders error state when lesson is not found or unapproved', async () => {
    vi.spyOn(api, 'getLessonDetail').mockRejectedValue(
      new Error('Lesson not found or not published')
    );
    const onBack = vi.fn();

    render(<LessonViewer lessonId="invalid-id" onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText(/Lesson Unavailable/i)).toBeInTheDocument();
      expect(
        screen.getByText(/Lesson not found or not published/i)
      ).toBeInTheDocument();
    });

    const returnBtn = screen.getByRole('button', { name: /Return to Curriculum/i });
    fireEvent.click(returnBtn);
    expect(onBack).toHaveBeenCalledTimes(1);
  });
});
