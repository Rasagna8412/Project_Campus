import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { DailyReviewQueueCard } from '../components/review/DailyReviewQueueCard';
import { FlashcardReviewModal } from '../components/review/FlashcardReviewModal';
import { StudentDashboard } from '../components/dashboard/StudentDashboard';
import * as api from '../services/api';
import * as authContext from '../context/AuthContext';
import {
  ReviewItemSummary,
  ReviewQueueResponse,
  ReviewStatsResponse,
} from '../types/repetition';

vi.mock('../services/api');
vi.mock('../context/AuthContext');

const mockUser = {
  id: 'user-sr-1',
  email: 'student.sr@example.com',
  full_name: 'Aditya Verma',
  is_active: true,
  is_verified: true,
  roles: ['STUDENT'],
  onboarding_completed: true,
  created_at: '2026-01-01T00:00:00Z',
};

const mockProfile = {
  id: 'prof-sr-1',
  user_id: 'user-sr-1',
  full_name: 'Aditya Verma',
  email: 'student.sr@example.com',
  target_curriculum_id: 'curr-1',
  target_curriculum_name: 'CBSE Secondary',
  target_curriculum_code: 'CBSE',
  grade_stage_id: 'grade-1',
  grade_stage_name: 'Class 12',
  grade_stage_code: 'CLASS_12',
  target_exam_year: 2027,
  daily_study_goal_minutes: 120,
  preferred_language: 'en',
  onboarding_completed: true,
  selected_subjects: [{ id: 'sub-1', code: 'PHY', name: 'Physics', display_order: 1 }],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const mockDueItem1: ReviewItemSummary = {
  id: 'review-item-1',
  topic_id: 'topic-101',
  topic_title: "Coulomb's Law and Electrostatic Force",
  subject_id: 'sub-1',
  subject_name: 'Physics',
  chapter_title: 'Electric Charges and Fields',
  due_date: '2026-10-18', // overdue
  repetition_count: 2,
  interval_days: 6,
  ease_factor: 2.50,
  status: 'REVIEW',
  is_overdue: true,
  sample_question_count: 5,
};

const mockDueItem2: ReviewItemSummary = {
  id: 'review-item-2',
  topic_id: 'topic-102',
  topic_title: 'Gauss Law and Electric Flux',
  subject_id: 'sub-1',
  subject_name: 'Physics',
  chapter_title: 'Electric Charges and Fields',
  due_date: '2026-10-19', // due today
  repetition_count: 5,
  interval_days: 28,
  ease_factor: 2.65,
  status: 'MASTERED',
  is_overdue: false,
  sample_question_count: 8,
};

const mockQueue: ReviewQueueResponse = {
  date: '2026-10-19',
  total_due_count: 2,
  overdue_count: 1,
  returned_count: 2,
  items: [mockDueItem1, mockDueItem2],
};

const mockEmptyQueue: ReviewQueueResponse = {
  date: '2026-10-19',
  total_due_count: 0,
  overdue_count: 0,
  returned_count: 0,
  items: [],
};

const mockStats: ReviewStatsResponse = {
  total_tracked_topics: 12,
  due_today_count: 2,
  mastered_count: 4,
  average_ease_factor: 2.48,
  successful_review_rate_percentage: 85.5,
};

describe('Milestone 7 Spaced Repetition & Revision Queue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(authContext, 'useAuth').mockReturnValue({
      user: mockUser,
      profile: mockProfile,
      isAuthenticated: true,
      isLoading: false,
      authError: null,
      clearAuthError: vi.fn(),
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn().mockResolvedValue(mockProfile),
      saveOnboarding: vi.fn(),
      deleteAccount: vi.fn().mockResolvedValue(undefined),
    });
  });

  describe('DailyReviewQueueCard Component', () => {
    it('renders queue items, overdue badges, and aggregate stats correctly', () => {
      const handleRefresh = vi.fn();
      const handleStartReview = vi.fn();
      const handleStartPractice = vi.fn();

      render(
        <DailyReviewQueueCard
          queue={mockQueue}
          stats={mockStats}
          loading={false}
          error={null}
          onRefresh={handleRefresh}
          onStartReview={handleStartReview}
          onStartPractice={handleStartPractice}
        />
      );

      // Verify Header & Badges
      expect(screen.getByText(/Spaced Repetition & Revision Queue/i)).toBeInTheDocument();
      expect(screen.getByText(/Automated Recall Schedule/i)).toBeInTheDocument();
      expect(screen.getByText('1 Overdue')).toBeInTheDocument();
      expect(screen.getByText('2 Due Today')).toBeInTheDocument();

      // Verify Stats
      expect(screen.getByText('Tracked Topics')).toBeInTheDocument();
      expect(screen.getByText('12')).toBeInTheDocument();
      expect(screen.getByText('Mastered Topics')).toBeInTheDocument();
      expect(screen.getByText('4')).toBeInTheDocument();
      expect(screen.getByText('2.48')).toBeInTheDocument();
      expect(screen.getByText('85.5%')).toBeInTheDocument();

      // Verify Item details
      expect(screen.getByText("Coulomb's Law and Electrostatic Force")).toBeInTheDocument();
      expect(screen.getByText('Gauss Law and Electric Flux')).toBeInTheDocument();
      expect(screen.getByText('Overdue')).toBeInTheDocument();
      expect(screen.getByText('Due Today')).toBeInTheDocument();
      expect(screen.getByText('REVIEW')).toBeInTheDocument();
      expect(screen.getByText('MASTERED')).toBeInTheDocument();

      // Clicking Review Recall triggers callback
      const reviewButtons = screen.getAllByRole('button', { name: /Review Recall/i });
      fireEvent.click(reviewButtons[0]);
      expect(handleStartReview).toHaveBeenCalledWith(mockDueItem1);

      // Clicking Drill triggers practice callback
      const drillButton = screen.getByRole('button', { name: /Drill \(5\)/i });
      fireEvent.click(drillButton);
      expect(handleStartPractice).toHaveBeenCalledWith('topic-101', "Coulomb's Law and Electrostatic Force");
    });

    it('renders clean empty state when no reviews are due', () => {
      render(
        <DailyReviewQueueCard
          queue={mockEmptyQueue}
          stats={mockStats}
          loading={false}
          error={null}
          onRefresh={vi.fn()}
          onStartReview={vi.fn()}
        />
      );

      expect(screen.getByText(/All Reviews Completed for Today! 🎉/i)).toBeInTheDocument();
      expect(
        screen.getByText(/No topics are currently due for spaced repetition review/i)
      ).toBeInTheDocument();
    });

    it('renders error state and triggers refresh upon retry click', () => {
      const handleRefresh = vi.fn();
      render(
        <DailyReviewQueueCard
          queue={null}
          stats={null}
          loading={false}
          error="Network connection lost"
          onRefresh={handleRefresh}
          onStartReview={vi.fn()}
        />
      );

      expect(screen.getByText('Network connection lost')).toBeInTheDocument();
      const retryBtn = screen.getByRole('button', { name: /Retry/i });
      fireEvent.click(retryBtn);
      expect(handleRefresh).toHaveBeenCalledTimes(1);
    });
  });

  describe('FlashcardReviewModal Component', () => {
    it('supports front-to-back flip, displays rating scale, and submits score', async () => {
      const handleClose = vi.fn();
      const handleSubmitRating = vi.fn().mockResolvedValue(undefined);

      render(
        <FlashcardReviewModal
          item={mockDueItem1}
          isOpen={true}
          onClose={handleClose}
          onSubmitRating={handleSubmitRating}
        />
      );

      // Verify modal header and metadata
      expect(screen.getByText('Active Recall Drill')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: "Coulomb's Law and Electrostatic Force" })).toBeInTheDocument();
      expect(screen.getByText('#2')).toBeInTheDocument(); // Repetition #2
      expect(screen.getByText('6 days')).toBeInTheDocument();

      // Initially unflipped: reveal prompt is visible
      const flipBtn = screen.getByRole('button', { name: /Reveal Self-Assessment/i });
      expect(flipBtn).toBeInTheDocument();

      // Click to flip
      fireEvent.click(flipBtn);

      // Rating buttons should now be visible
      expect(screen.getByText('Select Your Recall Quality (0 to 5)')).toBeInTheDocument();
      expect(screen.getByText('Blackout')).toBeInTheDocument();
      expect(screen.getByText('Wrong')).toBeInTheDocument();
      expect(screen.getByText('Almost')).toBeInTheDocument();
      expect(screen.getByText('Hard')).toBeInTheDocument();
      expect(screen.getByText('Good')).toBeInTheDocument();
      expect(screen.getByText('Easy')).toBeInTheDocument();

      // Select 'Good' (Score 4)
      const goodBtn = screen.getByRole('button', { name: /Good/i });
      fireEvent.click(goodBtn);

      await waitFor(() => {
        expect(handleSubmitRating).toHaveBeenCalledTimes(1);
        expect(handleSubmitRating).toHaveBeenCalledWith(
          'review-item-1',
          4,
          expect.any(Number)
        );
        expect(handleClose).toHaveBeenCalled();
      });
    });

    it('handles keyboard shortcuts: Space to reveal, number key 5 to rate, Escape to close', async () => {
      const handleClose = vi.fn();
      const handleSubmitRating = vi.fn().mockResolvedValue(undefined);

      render(
        <FlashcardReviewModal
          item={mockDueItem2}
          isOpen={true}
          onClose={handleClose}
          onSubmitRating={handleSubmitRating}
        />
      );

      // Press Space to reveal
      fireEvent.keyDown(window, { key: ' ' });
      expect(screen.getByText('Select Your Recall Quality (0 to 5)')).toBeInTheDocument();

      // Press key '5' for Easy rating
      fireEvent.keyDown(window, { key: '5' });

      await waitFor(() => {
        expect(handleSubmitRating).toHaveBeenCalledWith(
          'review-item-2',
          5,
          expect.any(Number)
        );
        expect(handleClose).toHaveBeenCalled();
      });
    });

    it('closes on Escape key press when not submitted', () => {
      const handleClose = vi.fn();

      render(
        <FlashcardReviewModal
          item={mockDueItem1}
          isOpen={true}
          onClose={handleClose}
          onSubmitRating={vi.fn()}
        />
      );

      fireEvent.keyDown(window, { key: 'Escape' });
      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it('displays error message if submission fails', async () => {
      const handleSubmitRating = vi.fn().mockRejectedValue(new Error('Same-day review already recorded'));

      render(
        <FlashcardReviewModal
          item={mockDueItem1}
          isOpen={true}
          onClose={vi.fn()}
          onSubmitRating={handleSubmitRating}
        />
      );

      // Flip card
      fireEvent.click(screen.getByRole('button', { name: /Reveal Self-Assessment/i }));

      // Click Hard
      fireEvent.click(screen.getByRole('button', { name: /Hard/i }));

      await waitFor(() => {
        expect(screen.getByText('Same-day review already recorded')).toBeInTheDocument();
      });
    });
  });

  describe('StudentDashboard Integration', () => {
    it('fetches review queue, displays review card, and opens recall modal upon click', async () => {
      vi.mocked(api.getDailyStudyPlan).mockResolvedValue({
        date: '2026-10-19',
        target_minutes: 120,
        planned_minutes: 60,
        completed_minutes: 0,
        is_fully_completed: false,
        tasks: [],
      });
      vi.mocked(api.getStudyGoal).mockResolvedValue(null as any);
      vi.mocked(api.getCurriculumRoadmap).mockResolvedValue({
        total_lessons_count: 10,
        completed_lessons_count: 2,
        overall_completion_percentage: 20.0,
        subjects: [],
      });
      vi.mocked(api.getReviewQueue).mockResolvedValue(mockQueue);
      vi.mocked(api.getReviewStats).mockResolvedValue(mockStats);
      vi.mocked(api.submitReviewRating).mockResolvedValue({
        review_item_id: 'review-item-1',
        repetition_count: 3,
        ease_factor: 2.50,
        interval_days: 15,
        next_due_date: '2026-11-03',
        quality_score: 4,
        status: 'REVIEW',
        message: 'Review recorded successfully',
      });

      render(
        <StudentDashboard
          onOpenOnboarding={vi.fn()}
          onOpenLessons={vi.fn()}
          onSelectLesson={vi.fn()}
          onStartPractice={vi.fn()}
        />
      );

      // Verify Review Queue Card is mounted and loaded
      await waitFor(() => {
        expect(screen.getByText(/Spaced Repetition & Revision Queue/i)).toBeInTheDocument();
        expect(screen.getByText("Coulomb's Law and Electrostatic Force")).toBeInTheDocument();
      });

      // Click Review Recall on the first item
      const reviewButtons = screen.getAllByRole('button', { name: /Review Recall/i });
      fireEvent.click(reviewButtons[0]);

      // Active recall modal should appear
      await waitFor(() => {
        expect(screen.getByText('Active Recall Drill')).toBeInTheDocument();
      });

      // Flip card and submit rating
      fireEvent.click(screen.getByRole('button', { name: /Reveal Self-Assessment/i }));
      fireEvent.click(screen.getByRole('button', { name: /Good/i }));

      // API submit should be called
      await waitFor(() => {
        expect(api.submitReviewRating).toHaveBeenCalledWith(
          'review-item-1',
          4,
          expect.any(Number)
        );
      });
    });
  });
});
