import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { CurriculumBrowser } from '../components/curriculum/CurriculumBrowser';
import * as api from '../services/api';
import { CurriculumBoard } from '../types/auth';
import { Chapter, LessonSummary } from '../types/content';

vi.mock('../services/api');

const mockCurricula: CurriculumBoard[] = [
  {
    id: 'board-1',
    code: 'CBSE',
    name: 'Central Board of Secondary Education',
    country_code: 'IND',
    description: 'National Board',
    is_active: true,
    grades: [
      {
        id: 'grade-12',
        board_id: 'board-1',
        code: 'CLASS_12',
        name: 'Class 12 (+2)',
        display_order: 1,
        subjects: [
          {
            id: 'sub-phy',
            code: 'PHYSICS',
            name: 'Physics',
            display_order: 1,
          },
          {
            id: 'sub-chem',
            code: 'CHEMISTRY',
            name: 'Chemistry',
            display_order: 2,
          },
        ],
      },
    ],
  },
];

const mockChapters: Chapter[] = [
  {
    id: 'chap-1',
    subject_id: 'sub-phy',
    chapter_number: 1,
    title: 'Electric Charges and Fields',
    slug: 'electric-charges-and-fields',
    summary: 'Study of electrostatics and Coulomb forces.',
    display_order: 1,
    topics: [
      {
        id: 'topic-1',
        chapter_id: 'chap-1',
        topic_number: 1,
        title: "Coulomb's Law and Superposition",
        slug: 'coulombs-law-and-superposition',
        importance_weight: 3,
        display_order: 1,
        published_lessons_count: 1,
      },
    ],
  },
];

const mockLessons: LessonSummary[] = [
  {
    id: 'les-1',
    topic_id: 'topic-1',
    title: "Coulomb's Law and Superposition Principle",
    slug: 'coulombs-law-and-superposition-principle',
    summary: 'Detailed explanation of Coulomb inverse-square law.',
    learning_objectives: ["State Coulomb's Law"],
    estimated_read_time_minutes: 12,
    status: 'PUBLISHED',
    display_order: 1,
    provenance: 'CBSE Verified',
    is_verified: true,
    created_at: '2026-10-15T10:00:00Z',
    updated_at: '2026-10-15T10:00:00Z',
  },
];

describe('CurriculumBrowser Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders boards, subjects, chapters, and topics', async () => {
    vi.spyOn(api, 'getCurricula').mockResolvedValue(mockCurricula);
    vi.spyOn(api, 'getSubjectChapters').mockResolvedValue(mockChapters);
    vi.spyOn(api, 'getTopicLessons').mockResolvedValue(mockLessons);

    const onSelectLesson = vi.fn();

    render(
      <CurriculumBrowser
        onSelectLesson={onSelectLesson}
        initialBoardCode="CBSE"
        initialGradeCode="CLASS_12"
      />
    );

    // Verify curriculum boards rendered
    await waitFor(() => {
      expect(
        screen.getByText('Central Board of Secondary Education')
      ).toBeInTheDocument();
    });

    // Verify Grade and Subject tabs
    expect(screen.getByText('Class 12 (+2)')).toBeInTheDocument();
    expect(screen.getByText('Physics')).toBeInTheDocument();

    // Verify Chapters and Topics
    await waitFor(() => {
      expect(screen.getByText('Electric Charges and Fields')).toBeInTheDocument();
      expect(screen.getByText(/1 lesson/i)).toBeInTheDocument();
    });

    // Verify Lessons rendered for topic
    await waitFor(() => {
      expect(
        screen.getByText("Coulomb's Law and Superposition Principle")
      ).toBeInTheDocument();
    });

    // Click "Read Full Lesson"
    const readBtn = screen.getByRole('button', { name: /read full lesson/i });
    fireEvent.click(readBtn);

    expect(onSelectLesson).toHaveBeenCalledWith('les-1', expect.any(Array));
  });

  it('switches subject and loads corresponding chapters', async () => {
    vi.spyOn(api, 'getCurricula').mockResolvedValue(mockCurricula);
    const getChaptersSpy = vi
      .spyOn(api, 'getSubjectChapters')
      .mockResolvedValue(mockChapters);
    vi.spyOn(api, 'getTopicLessons').mockResolvedValue(mockLessons);

    render(
      <CurriculumBrowser
        onSelectLesson={vi.fn()}
        initialBoardCode="CBSE"
        initialGradeCode="CLASS_12"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Physics')).toBeInTheDocument();
    });

    const chemBtn = screen.getByRole('button', { name: /chemistry/i });
    fireEvent.click(chemBtn);

    await waitFor(() => {
      expect(getChaptersSpy).toHaveBeenCalledWith('sub-chem');
    });
  });
});
