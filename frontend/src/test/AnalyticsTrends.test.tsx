import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { PracticeTrendChart } from '../components/analytics/PracticeTrendChart';
import { PlannerAdherenceChart } from '../components/analytics/PlannerAdherenceChart';
import { RetentionTrendsCard } from '../components/analytics/RetentionTrendsCard';
import { DiagnosticMatrixCard } from '../components/analytics/DiagnosticMatrixCard';
import { AnalyticsMethodologyModal } from '../components/analytics/AnalyticsMethodologyModal';
import { StudentDashboard } from '../components/dashboard/StudentDashboard';
import * as api from '../services/api';
import * as authContext from '../context/AuthContext';
import {
  DiagnosticMatrixResponse,
  PlannerTrendsResponse,
  PracticeTrendsResponse,
  RetentionTrendsResponse,
} from '../types/analytics_trends';

vi.mock('../services/api');
vi.mock('../context/AuthContext');

const mockUser = {
  id: 'user-trends-1',
  email: 'student.trends@example.com',
  full_name: 'Trend Analyst',
  is_active: true,
  is_verified: true,
  roles: ['STUDENT'],
  onboarding_completed: true,
  created_at: '2026-01-01T00:00:00Z',
};

const mockProfile = {
  id: 'prof-trends-1',
  user_id: 'user-trends-1',
  full_name: 'Trend Analyst',
  email: 'student.trends@example.com',
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
  selected_subjects: [{ id: 'sub-1', code: 'MATH', name: 'Mathematics', display_order: 1 }],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const mockPracticeTrends: PracticeTrendsResponse = {
  days_count: 7,
  start_date: '2026-10-13',
  end_date: '2026-10-19',
  total_questions_answered: 25,
  total_correct_count: 20,
  overall_accuracy_percentage: 80.0,
  total_practice_minutes: 35.5,
  daily_trends: [
    {
      date: '2026-10-13',
      questions_answered: 5,
      correct_count: 4,
      accuracy_percentage: 80.0,
      practice_minutes: 7.0,
    },
    {
      date: '2026-10-14',
      questions_answered: 0,
      correct_count: 0,
      accuracy_percentage: null,
      practice_minutes: 0.0,
    },
    {
      date: '2026-10-15',
      questions_answered: 10,
      correct_count: 9,
      accuracy_percentage: 90.0,
      practice_minutes: 15.0,
    },
    {
      date: '2026-10-16',
      questions_answered: 0,
      correct_count: 0,
      accuracy_percentage: null,
      practice_minutes: 0.0,
    },
    {
      date: '2026-10-17',
      questions_answered: 5,
      correct_count: 3,
      accuracy_percentage: 60.0,
      practice_minutes: 6.5,
    },
    {
      date: '2026-10-18',
      questions_answered: 0,
      correct_count: 0,
      accuracy_percentage: null,
      practice_minutes: 0.0,
    },
    {
      date: '2026-10-19',
      questions_answered: 5,
      correct_count: 4,
      accuracy_percentage: 80.0,
      practice_minutes: 7.0,
    },
  ],
};

const mockPlannerTrends: PlannerTrendsResponse = {
  daily_study_goal_minutes: 90,
  days_count: 7,
  preferred_days_count: 5,
  goals_met_count: 4,
  adherence_rate_percentage: 80.0,
  total_planned_minutes: 420,
  total_completed_minutes: 380,
  daily_trends: [
    {
      date: '2026-10-13',
      day_of_week: 'MON',
      is_preferred_day: true,
      has_plan: true,
      planned_minutes: 90,
      completed_minutes: 90,
      tasks_count: 3,
      completed_tasks_count: 3,
      is_goal_met: true,
    },
    {
      date: '2026-10-14',
      day_of_week: 'TUE',
      is_preferred_day: true,
      has_plan: true,
      planned_minutes: 90,
      completed_minutes: 90,
      tasks_count: 3,
      completed_tasks_count: 3,
      is_goal_met: true,
    },
    {
      date: '2026-10-15',
      day_of_week: 'WED',
      is_preferred_day: false,
      has_plan: false,
      planned_minutes: 0,
      completed_minutes: 0,
      tasks_count: 0,
      completed_tasks_count: 0,
      is_goal_met: false,
    },
    {
      date: '2026-10-16',
      day_of_week: 'THU',
      is_preferred_day: true,
      has_plan: true,
      planned_minutes: 60,
      completed_minutes: 30,
      tasks_count: 2,
      completed_tasks_count: 1,
      is_goal_met: false,
    },
    {
      date: '2026-10-17',
      day_of_week: 'FRI',
      is_preferred_day: true,
      has_plan: true,
      planned_minutes: 90,
      completed_minutes: 90,
      tasks_count: 3,
      completed_tasks_count: 3,
      is_goal_met: true,
    },
    {
      date: '2026-10-18',
      day_of_week: 'SAT',
      is_preferred_day: true,
      has_plan: true,
      planned_minutes: 90,
      completed_minutes: 80,
      tasks_count: 3,
      completed_tasks_count: 3,
      is_goal_met: true,
    },
    {
      date: '2026-10-19',
      day_of_week: 'SUN',
      is_preferred_day: false,
      has_plan: false,
      planned_minutes: 0,
      completed_minutes: 0,
      tasks_count: 0,
      completed_tasks_count: 0,
      is_goal_met: false,
    },
  ],
};

const mockRetentionTrends: RetentionTrendsResponse = {
  active_streak_days: 5,
  last_reviewed_date: '2026-10-19',
  is_streak_active_today: true,
  due_today_count: 2,
  overdue_1_to_3_days: 1,
  overdue_4_plus_days: 2,
  total_overdue_count: 3,
  forecast_next_7_days: [
    { date: '2026-10-20', due_count: 2 },
    { date: '2026-10-21', due_count: 0 },
    { date: '2026-10-22', due_count: 3 },
    { date: '2026-10-23', due_count: 1 },
    { date: '2026-10-24', due_count: 4 },
    { date: '2026-10-25', due_count: 2 },
    { date: '2026-10-26', due_count: 1 },
  ],
};

const mockDiagnosticMatrix: DiagnosticMatrixResponse = {
  total_topics_analyzed: 4,
  critical_gaps_count: 1,
  unpracticed_foundations_count: 1,
  solidifying_count: 1,
  mastered_count: 1,
  topics: [
    {
      topic_id: 'top-1',
      topic_title: 'Definite Integrals',
      subject_id: 'sub-1',
      subject_name: 'Mathematics',
      chapter_title: 'Calculus',
      lesson_status: 'COMPLETED',
      total_attempts: 10,
      observed_accuracy_percentage: 40.0,
      practice_category: 'NEEDS_REVIEW',
      review_status: 'LEARNING',
      review_interval_days: 1,
      is_review_overdue: true,
      diagnostic_state: 'CRITICAL_GAP',
      action_recommendation: 'Urgent review required: re-study core lesson concepts.',
    },
    {
      topic_id: 'top-2',
      topic_title: 'Matrices & Determinants',
      subject_id: 'sub-1',
      subject_name: 'Mathematics',
      chapter_title: 'Algebra',
      lesson_status: 'COMPLETED',
      total_attempts: 2,
      observed_accuracy_percentage: 50.0,
      practice_category: 'INSUFFICIENT_DATA',
      review_status: null,
      review_interval_days: null,
      is_review_overdue: false,
      diagnostic_state: 'UNPRACTICED_FOUNDATION',
      action_recommendation: 'Foundation studied: complete at least 5 practice questions.',
    },
    {
      topic_id: 'top-3',
      topic_title: 'Differential Equations',
      subject_id: 'sub-1',
      subject_name: 'Mathematics',
      chapter_title: 'Calculus',
      lesson_status: 'COMPLETED',
      total_attempts: 8,
      observed_accuracy_percentage: 75.0,
      practice_category: 'DEVELOPING',
      review_status: 'REVIEW',
      review_interval_days: 6,
      is_review_overdue: false,
      diagnostic_state: 'SOLIDIFYING',
      action_recommendation: 'Good progress: continue spaced repetition reviews.',
    },
    {
      topic_id: 'top-4',
      topic_title: 'Vectors & 3D Geometry',
      subject_id: 'sub-1',
      subject_name: 'Mathematics',
      chapter_title: 'Geometry',
      lesson_status: 'COMPLETED',
      total_attempts: 12,
      observed_accuracy_percentage: 91.7,
      practice_category: 'STRONG',
      review_status: 'MASTERED',
      review_interval_days: 28,
      is_review_overdue: false,
      diagnostic_state: 'MASTERED',
      action_recommendation: 'Topic fully mastered: retain high recall through maintenance reviews.',
    },
  ],
};

describe('Milestone 8: Analytics Trends and Progress Visualization Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(authContext, 'useAuth').mockReturnValue({
      user: mockUser as any,
      profile: mockProfile as any,
      isAuthenticated: true,
      isLoading: false,
      authError: null,
      clearAuthError: vi.fn(),
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn().mockResolvedValue(mockProfile as any),
      saveOnboarding: vi.fn(),
      deleteAccount: vi.fn().mockResolvedValue(undefined),
    });

    vi.mocked(api.getPracticeTrends).mockResolvedValue(mockPracticeTrends);
    vi.mocked(api.getPlannerTrends).mockResolvedValue(mockPlannerTrends);
    vi.mocked(api.getRetentionTrends).mockResolvedValue(mockRetentionTrends);
    vi.mocked(api.getDiagnosticMatrix).mockResolvedValue(mockDiagnosticMatrix);
    vi.mocked(api.getDailyStudyPlan).mockResolvedValue({
      date: '2026-10-19',
      day_of_week: 'MON',
      daily_study_goal_minutes: 90,
      planned_minutes: 90,
      completed_minutes: 45,
      tasks_count: 2,
      completed_tasks_count: 1,
      is_fully_completed: false,
      tasks: [],
    } as any);
    vi.mocked(api.getReviewQueue).mockResolvedValue({
      date: '2026-10-19',
      total_due_count: 0,
      overdue_count: 0,
      returned_count: 0,
      items: [],
    } as any);
  });

  it('renders PracticeTrendChart with KPI cards and accessible screen-reader table', () => {
    const onDaysChange = vi.fn();
    render(
      <PracticeTrendChart
        data={mockPracticeTrends}
        loading={false}
        selectedDays={7}
        onDaysChange={onDaysChange}
      />
    );

    expect(screen.getByText('Practice Volume & Accuracy Timeline')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument(); // total questions
    expect(screen.getAllByText('80%').length).toBeGreaterThanOrEqual(1); // accuracy present in card & table
    expect(screen.getByText('35.5m')).toBeInTheDocument(); // practice time

    // Verify screen-reader data table
    const table = screen.getByRole('table', { hidden: true });
    expect(table).toBeInTheDocument();
    expect(screen.getByText('2026-10-13')).toBeInTheDocument();
    expect(screen.getByText('2026-10-14')).toBeInTheDocument();

    // Verify 14 Days button triggers handler
    const btn14 = screen.getByRole('button', { name: '14 Days' });
    fireEvent.click(btn14);
    expect(onDaysChange).toHaveBeenCalledWith(14);
  });

  it('renders PlannerAdherenceChart with adherence rate, completed minutes, and rest days', () => {
    const onDaysChange = vi.fn();
    render(
      <PlannerAdherenceChart
        data={mockPlannerTrends}
        loading={false}
        selectedDays={7}
        onDaysChange={onDaysChange}
      />
    );

    expect(screen.getByText('Planned vs Completed Study Minutes')).toBeInTheDocument();
    expect(screen.getByText('80%')).toBeInTheDocument(); // adherence rate
    expect(screen.getByText('380m')).toBeInTheDocument(); // completed minutes
    expect(screen.getByText('2')).toBeInTheDocument(); // 2 rest days

    // Check rest day indicator in SVG
    expect(screen.getAllByText('REST').length).toBeGreaterThan(0);

    // Verify 14-day toggle button
    const btn14 = screen.getByRole('button', { name: '14 Days' });
    fireEvent.click(btn14);
    expect(onDaysChange).toHaveBeenCalledWith(14);
  });

  it('renders RetentionTrendsCard with streak, overdue breakdown, and forecast', () => {
    render(
      <RetentionTrendsCard
        data={mockRetentionTrends}
        loading={false}
      />
    );

    expect(screen.getByText('Memory Streaks & Recall Forecast')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument(); // 5 active streak days
    expect(screen.getByText('✓ Maintained today')).toBeInTheDocument();
    expect(screen.getByText('1 (1–3d)')).toBeInTheDocument();
    expect(screen.getByText('2 (4+d)')).toBeInTheDocument();

    // Screen reader table for 7-day forecast
    expect(screen.getByText('2026-10-20')).toBeInTheDocument();
  });

  it('renders DiagnosticMatrixCard and allows filtering by diagnostic state', () => {
    const onStartPractice = vi.fn();
    render(
      <DiagnosticMatrixCard
        data={mockDiagnosticMatrix}
        loading={false}
        onStartPractice={onStartPractice}
      />
    );

    expect(screen.getByText('Curriculum Diagnostic Matrix')).toBeInTheDocument();
    expect(screen.getByText('Definite Integrals')).toBeInTheDocument();
    expect(screen.getByText('Matrices & Determinants')).toBeInTheDocument();
    expect(screen.getByText('Differential Equations')).toBeInTheDocument();
    expect(screen.getByText('Vectors & 3D Geometry')).toBeInTheDocument();

    // Filter by CRITICAL_GAP
    const filterSelect = screen.getByLabelText('Filter by diagnostic state');
    fireEvent.change(filterSelect, { target: { value: 'CRITICAL_GAP' } });

    expect(screen.getByText('Definite Integrals')).toBeInTheDocument();
    expect(screen.queryByText('Matrices & Determinants')).not.toBeInTheDocument();

    // Search query filter
    const searchInput = screen.getByPlaceholderText('Search by topic, subject, or chapter...');
    fireEvent.change(searchInput, { target: { value: 'Geometry' } });
    expect(screen.queryByText('Definite Integrals')).not.toBeInTheDocument();

    // Practice button click
    fireEvent.change(filterSelect, { target: { value: 'ALL' } });
    fireEvent.change(searchInput, { target: { value: '' } });
    const practiceBtn = screen.getByTitle('Practice Definite Integrals');
    fireEvent.click(practiceBtn);
    expect(onStartPractice).toHaveBeenCalledWith('top-1', 'Definite Integrals');
  });

  it('renders AnalyticsMethodologyModal and closes on close button and Escape key', () => {
    const onClose = vi.fn();
    const { rerender } = render(
      <AnalyticsMethodologyModal isOpen={true} onClose={onClose} />
    );

    expect(screen.getByText('Analytics & Diagnostic Methodology')).toBeInTheDocument();
    expect(screen.getByText(/1\. Practice Accuracy & The 5-Attempt Calibration Rule/i)).toBeInTheDocument();
    expect(screen.getByText(/2\. Study Plan Adherence & Non-Punitive Rest Days/i)).toBeInTheDocument();

    // Close button
    const closeBtn = screen.getByLabelText('Close methodology guide');
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalledTimes(1);

    // Escape key
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(2);

    // Closed state
    rerender(<AnalyticsMethodologyModal isOpen={false} onClose={onClose} />);
    expect(screen.queryByText('Analytics & Diagnostic Methodology')).not.toBeInTheDocument();
  });

  it('integrates Trends & Diagnostics tab switching inside StudentDashboard', async () => {
    render(
      <StudentDashboard
        onOpenOnboarding={vi.fn()}
        onOpenLessons={vi.fn()}
      />
    );

    // Initial state: Daily Workspace tab is selected
    expect(screen.getByText('Daily Workspace & Tasks')).toBeInTheDocument();
    expect(screen.getByText('Automated Recall Schedule')).toBeInTheDocument();

    // Click Trends & Diagnostics tab
    const trendsTab = screen.getByRole('tab', { name: /Trends & Diagnostics/i });
    fireEvent.click(trendsTab);

    // Verify trends charts are displayed
    await waitFor(() => {
      expect(screen.getByText('Practice Volume & Accuracy Timeline')).toBeInTheDocument();
      expect(screen.getByText('Planned vs Completed Study Minutes')).toBeInTheDocument();
      expect(screen.getByText('Memory Streaks & Recall Forecast')).toBeInTheDocument();
      expect(screen.getByText('Curriculum Diagnostic Matrix')).toBeInTheDocument();
    });

    expect(api.getPracticeTrends).toHaveBeenCalled();
    expect(api.getPlannerTrends).toHaveBeenCalled();
    expect(api.getRetentionTrends).toHaveBeenCalled();
    expect(api.getDiagnosticMatrix).toHaveBeenCalled();
  });
});
