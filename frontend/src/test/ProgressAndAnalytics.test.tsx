import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { StudentDashboard } from '../components/dashboard/StudentDashboard';
import { LessonViewer } from '../components/curriculum/LessonViewer';
import * as api from '../services/api';
import * as authContext from '../context/AuthContext';
import { DashboardAnalytics, TopicPerformance, LearningRecommendation, LessonProgress } from '../types/progress';
import { LessonDetail } from '../types/content';

vi.mock('../services/api');
vi.mock('../context/AuthContext');

const mockUser = {
  id: 'user-123',
  email: 'student@example.com',
  full_name: 'Aarav Patel',
  is_active: true,
  is_verified: true,
  roles: ['STUDENT'],
  onboarding_completed: true,
  created_at: '2026-01-01T00:00:00Z',
};

const mockProfile = {
  id: 'prof-123',
  user_id: 'user-123',
  full_name: 'Aarav Patel',
  email: 'student@example.com',
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

const mockAnalytics: DashboardAnalytics = {
  lessons_completed_count: 5,
  lessons_in_progress_count: 2,
  practice_sessions_completed_count: 8,
  total_questions_answered: 40,
  total_correct_answers: 32,
  overall_accuracy_percentage: 80.0,
  total_practice_time_seconds: 1800,
  daily_study_goal_minutes: 120,
  recent_activity: [
    {
      activity_type: 'PRACTICE_SESSION',
      id: 'sess-1',
      title: "Coulomb's Law Practice",
      subject_name: 'Physics',
      subtitle: '5 questions • 4 correct (80%)',
      timestamp: '2026-10-16T08:00:00Z',
      is_completed: true,
    },
    {
      activity_type: 'LESSON_COMPLETED',
      id: 'lsn-1',
      title: 'Electric Field and Field Lines',
      subject_name: 'Physics',
      subtitle: 'Completed 15 min lesson',
      timestamp: '2026-10-16T07:00:00Z',
      is_completed: true,
    },
  ],
};

const mockTopics: TopicPerformance[] = [
  {
    topic_id: 'top-1',
    topic_title: "Coulomb's Law and Superposition",
    topic_number: 1,
    chapter_title: 'Electric Charges',
    subject_name: 'Physics',
    total_attempts: 10,
    correct_attempts: 9,
    incorrect_attempts: 1,
    observed_accuracy_percentage: 90.0,
    completed_sessions_count: 2,
    last_practiced_at: '2026-10-16T08:00:00Z',
    status_category: 'STRONG',
  },
  {
    topic_id: 'top-2',
    topic_title: "Electric Flux and Gauss's Law",
    topic_number: 2,
    chapter_title: 'Electric Charges',
    subject_name: 'Physics',
    total_attempts: 6,
    correct_attempts: 3,
    incorrect_attempts: 3,
    observed_accuracy_percentage: 50.0,
    completed_sessions_count: 1,
    last_practiced_at: '2026-10-15T10:00:00Z',
    status_category: 'NEEDS_REVIEW',
  },
];

const mockRecommendations: LearningRecommendation[] = [
  {
    type: 'RESUME_LESSON',
    priority: 1,
    title: 'Continue Reading Lesson',
    reason: 'You started this lesson recently. Complete it to finish the concept foundation.',
    target_id: 'lsn-resume-1',
    target_title: 'Electric Dipole and Dipole Moment',
    subject_name: 'Physics',
    action_label: 'Resume Lesson',
  },
  {
    type: 'REVISE_TOPIC',
    priority: 2,
    title: 'Targeted Revision Suggested',
    reason: 'Observed accuracy is 50.0% across 6 practice questions.',
    target_id: 'top-2',
    target_title: "Electric Flux and Gauss's Law",
    subject_name: 'Physics',
    action_label: 'Practise Topic',
  },
];

describe('Milestone 5 Frontend: Progress and Analytics', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
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
      refreshProfile: vi.fn(),
      saveOnboarding: vi.fn(),
      deleteAccount: vi.fn(),
    });
  });

  it('renders student dashboard with real aggregated KPI cards, topic breakdown, and recommendations', async () => {
    vi.spyOn(api, 'getDashboardAnalytics').mockResolvedValue(mockAnalytics);
    vi.spyOn(api, 'getTopicAnalytics').mockResolvedValue(mockTopics);
    vi.spyOn(api, 'getLearningRecommendations').mockResolvedValue(mockRecommendations);
    vi.spyOn(api, 'getPracticeHistory').mockResolvedValue([]);

    render(
      <StudentDashboard
        onOpenOnboarding={vi.fn()}
        onOpenLessons={vi.fn()}
        onSelectLesson={vi.fn()}
        onStartPractice={vi.fn()}
      />
    );

    // KPI cards render
    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument(); // Lessons completed
      expect(screen.getByText('8')).toBeInTheDocument(); // Practice drills
      expect(screen.getByText('40')).toBeInTheDocument(); // Questions solved
      expect(screen.getByText('80%')).toBeInTheDocument(); // Accuracy
    });

    // Topic performance table renders
    expect(screen.getByText("Coulomb's Law and Superposition")).toBeInTheDocument();
    expect(screen.getByText('Strong Grasp')).toBeInTheDocument();
    expect(screen.getAllByText("Electric Flux and Gauss's Law")[0]).toBeInTheDocument();
    expect(screen.getByText('Needs Revision')).toBeInTheDocument();

    // Recommendations render
    expect(screen.getByText('Continue Reading Lesson')).toBeInTheDocument();
    expect(screen.getByText('Electric Dipole and Dipole Moment')).toBeInTheDocument();
    expect(screen.getByText('Resume Lesson')).toBeInTheDocument();
  });

  it('renders a friendly first-step experience for fresh students with zero activity', async () => {
    const emptyAnalytics: DashboardAnalytics = {
      lessons_completed_count: 0,
      lessons_in_progress_count: 0,
      practice_sessions_completed_count: 0,
      total_questions_answered: 0,
      total_correct_answers: 0,
      overall_accuracy_percentage: null,
      total_practice_time_seconds: 0,
      daily_study_goal_minutes: 120,
      recent_activity: [],
    };

    vi.spyOn(api, 'getDashboardAnalytics').mockResolvedValue(emptyAnalytics);
    vi.spyOn(api, 'getTopicAnalytics').mockResolvedValue([]);
    vi.spyOn(api, 'getLearningRecommendations').mockResolvedValue([]);
    vi.spyOn(api, 'getPracticeHistory').mockResolvedValue([]);

    render(
      <StudentDashboard
        onOpenOnboarding={vi.fn()}
        onOpenLessons={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Welcome to Your Academic Learning Dashboard')).toBeInTheDocument();
    });

    expect(screen.getByText(/No attempts/i)).toBeInTheDocument();
    expect(screen.getByText('Start Your First Lesson')).toBeInTheDocument();
  });

  it('handles lesson completion action in LessonViewer', async () => {
    const mockLesson: LessonDetail = {
      id: 'lesson-456',
      topic_id: 'topic-789',
      title: 'Current Electricity and Drift Velocity',
      slug: 'current-electricity',
      summary: 'Comprehensive lesson on electron drift velocity and current density.',
      learning_objectives: ['Understand drift velocity formula', 'Calculate electron mobility'],
      provenance: 'NCERT Physics Class 12, Chapter 3',
      estimated_read_time_minutes: 10,
      status: 'PUBLISHED',
      display_order: 1,
      is_verified: true,
      created_at: '2026-10-15T10:00:00Z',
      updated_at: '2026-10-15T10:00:00Z',
      sections: [],
    };

    const initialProgress: LessonProgress = {
      id: 'prog-1',
      user_id: 'user-123',
      lesson_id: 'lesson-456',
      status: 'IN_PROGRESS',
      started_at: '2026-10-16T09:00:00Z',
      last_accessed_at: '2026-10-16T09:00:00Z',
    };

    const completedProgress: LessonProgress = {
      ...initialProgress,
      status: 'COMPLETED',
      completed_at: '2026-10-16T09:30:00Z',
    };

    vi.spyOn(api, 'getLessonDetail').mockResolvedValue(mockLesson);
    vi.spyOn(api, 'startLessonProgress').mockResolvedValue(initialProgress);
    vi.spyOn(api, 'completeLessonProgress').mockResolvedValue(completedProgress);

    render(
      <LessonViewer
        lessonId="lesson-456"
        onBack={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Current Electricity and Drift Velocity')).toBeInTheDocument();
    });

    // Mark completed button is present
    const completeBtn = screen.getByRole('button', { name: /Mark Lesson as Completed/i });
    expect(completeBtn).toBeInTheDocument();

    // Click complete button
    fireEvent.click(completeBtn);

    // Verify it updates to completed
    await waitFor(() => {
      expect(api.completeLessonProgress).toHaveBeenCalledWith('lesson-456');
      expect(screen.getByText(/You marked this lesson completed/i)).toBeInTheDocument();
    });
  });
});
