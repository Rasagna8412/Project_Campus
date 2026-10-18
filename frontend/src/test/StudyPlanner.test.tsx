import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { StudentDashboard } from '../components/dashboard/StudentDashboard';
import { DailyStudyPlanCard } from '../components/planner/DailyStudyPlanCard';
import { StudyGoalModal } from '../components/planner/StudyGoalModal';
import { CurriculumRoadmapCard } from '../components/planner/CurriculumRoadmapCard';
import * as api from '../services/api';
import * as authContext from '../context/AuthContext';
import { DailyStudyPlan, StudyGoal, CurriculumRoadmap } from '../types/planner';

vi.mock('../services/api');
vi.mock('../context/AuthContext');

const mockUser = {
  id: 'user-planner-1',
  email: 'student.planner@example.com',
  full_name: 'Priya Sharma',
  is_active: true,
  is_verified: true,
  roles: ['STUDENT'],
  onboarding_completed: true,
  created_at: '2026-01-01T00:00:00Z',
};

const mockProfile = {
  id: 'prof-planner-1',
  user_id: 'user-planner-1',
  full_name: 'Priya Sharma',
  email: 'student.planner@example.com',
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

const mockGoal: StudyGoal = {
  id: 'goal-1',
  user_id: 'user-planner-1',
  title: 'CBSE Class 12 Boards Preparation',
  target_date: '2027-03-01',
  daily_study_minutes: 120,
  preferred_days: ['MON', 'TUE', 'WED', 'THU', 'FRI'],
  status: 'ACTIVE',
  created_at: '2026-10-16T00:00:00Z',
  updated_at: '2026-10-16T00:00:00Z',
};

const mockPlan: DailyStudyPlan = {
  date: new Date().toISOString().split('T')[0],
  planned_minutes: 65,
  target_minutes: 120,
  completed_minutes: 20,
  is_fully_completed: false,
  tasks: [
    {
      id: 'task-1',
      user_id: 'user-planner-1',
      goal_id: 'goal-1',
      scheduled_date: new Date().toISOString().split('T')[0],
      task_type: 'RESUME_LESSON',
      title: 'Resume: Coulomb Law and Superposition Principle',
      subject_id: 'sub-1',
      subject_name: 'Physics',
      chapter_id: 'chap-1',
      topic_id: 'topic-1',
      lesson_id: 'lesson-101',
      estimated_minutes: 20,
      display_order: 1,
      status: 'COMPLETED',
      is_completed: true,
      completed_at: '2026-10-16T10:00:00Z',
      reason: 'In-progress curriculum lesson awaiting completion',
    },
    {
      id: 'task-2',
      user_id: 'user-planner-1',
      goal_id: 'goal-1',
      scheduled_date: new Date().toISOString().split('T')[0],
      task_type: 'REVISE_TOPIC',
      title: 'Revise: Electric Flux & Gauss Theorem Drill',
      subject_id: 'sub-1',
      subject_name: 'Physics',
      chapter_id: 'chap-1',
      topic_id: 'topic-2',
      lesson_id: null,
      estimated_minutes: 15,
      display_order: 2,
      status: 'PENDING',
      is_completed: false,
      completed_at: null,
      reason: 'Recent practice accuracy is 40.0% (<60% mastery threshold)',
    },
    {
      id: 'task-3',
      user_id: 'user-planner-1',
      goal_id: 'goal-1',
      scheduled_date: new Date().toISOString().split('T')[0],
      task_type: 'STUDY_LESSON',
      title: 'Study: Electric Potential and Capacitance',
      subject_id: 'sub-1',
      subject_name: 'Physics',
      chapter_id: 'chap-2',
      topic_id: 'topic-3',
      lesson_id: 'lesson-102',
      estimated_minutes: 30,
      display_order: 3,
      status: 'PENDING',
      is_completed: false,
      completed_at: null,
      reason: 'Next unstudied lesson in your enrolled Physics curriculum',
    },
  ],
};

const mockRoadmap: CurriculumRoadmap = {
  total_lessons_count: 20,
  completed_lessons_count: 5,
  overall_completion_percentage: 25.0,
  subjects: [
    {
      subject_id: 'sub-1',
      subject_name: 'Physics',
      total_lessons: 20,
      completed_lessons: 5,
      in_progress_lessons: 2,
      completion_percentage: 25.0,
      chapters: [
        {
          chapter_id: 'chap-1',
          chapter_number: 1,
          title: 'Electric Charges and Fields',
          total_lessons: 4,
          completed_lessons: 4,
          is_completed: true,
        },
        {
          chapter_id: 'chap-2',
          chapter_number: 2,
          title: 'Electrostatic Potential and Capacitance',
          total_lessons: 6,
          completed_lessons: 1,
          is_completed: false,
        },
      ],
    },
  ],
};

describe('Milestone 6 Study Planner & Learning Roadmap', () => {
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

  describe('DailyStudyPlanCard Component', () => {
    it('renders planned workload progress and study tasks correctly', () => {
      const handleToggle = vi.fn();
      const handleRefresh = vi.fn();
      const handleOpenGoal = vi.fn();

      render(
        <DailyStudyPlanCard
          plan={mockPlan}
          loading={false}
          error={null}
          onRefresh={handleRefresh}
          onToggleComplete={handleToggle}
          onOpenGoalModal={handleOpenGoal}
          selectedDate={mockPlan.date}
          onDateChange={vi.fn()}
        />
      );

      // Verify date header and workload indicator
      expect(screen.getByText(/Today's Learning Roadmap & Study Plan/i)).toBeInTheDocument();
      expect(screen.getByText(/20m \/ 65m/i)).toBeInTheDocument();
      expect(screen.getByText(/Goal: 120m/i)).toBeInTheDocument();

      // Verify tasks rendered
      expect(screen.getByText('Resume: Coulomb Law and Superposition Principle')).toBeInTheDocument();
      expect(screen.getByText('Revise: Electric Flux & Gauss Theorem Drill')).toBeInTheDocument();
      expect(screen.getByText('Study: Electric Potential and Capacitance')).toBeInTheDocument();

      // Verify task type badges
      expect(screen.getByText('Resume Lesson')).toBeInTheDocument();
      expect(screen.getByText('Revision Drill')).toBeInTheDocument();
      expect(screen.getByText('Syllabus Lesson')).toBeInTheDocument();
    });

    it('toggles task completion when checkbox button is clicked', () => {
      const handleToggle = vi.fn();

      render(
        <DailyStudyPlanCard
          plan={mockPlan}
          loading={false}
          error={null}
          onRefresh={vi.fn()}
          onToggleComplete={handleToggle}
          onOpenGoalModal={vi.fn()}
          selectedDate={mockPlan.date}
          onDateChange={vi.fn()}
        />
      );

      const markIncompleteButtons = screen.getAllByRole('button', { name: /Mark as incomplete/i });
      expect(markIncompleteButtons.length).toBe(1);
      fireEvent.click(markIncompleteButtons[0]);
      expect(handleToggle).toHaveBeenCalledWith('task-1', false);

      const markCompleteButtons = screen.getAllByRole('button', { name: /Mark as complete/i });
      expect(markCompleteButtons.length).toBe(2);
      fireEvent.click(markCompleteButtons[0]);
      expect(handleToggle).toHaveBeenCalledWith('task-2', true);
    });

    it('displays celebration banner when all daily tasks are completed', () => {
      const completedPlan: DailyStudyPlan = {
        ...mockPlan,
        completed_minutes: 65,
        planned_minutes: 65,
        is_fully_completed: true,
        tasks: mockPlan.tasks.map((t) => ({ ...t, is_completed: true, status: 'COMPLETED' })),
      };

      render(
        <DailyStudyPlanCard
          plan={completedPlan}
          loading={false}
          error={null}
          onRefresh={vi.fn()}
          onToggleComplete={vi.fn()}
          onOpenGoalModal={vi.fn()}
          selectedDate={completedPlan.date}
          onDateChange={vi.fn()}
        />
      );

      expect(screen.getByText('All Daily Tasks Completed! 🎉')).toBeInTheDocument();
      expect(screen.getByText(/100% Done/i)).toBeInTheDocument();
    });

    it('displays empty state with generate button when no tasks scheduled', () => {
      const emptyPlan: DailyStudyPlan = {
        date: new Date().toISOString().split('T')[0],
        planned_minutes: 0,
        target_minutes: 120,
        completed_minutes: 0,
        is_fully_completed: false,
        tasks: [],
      };

      const handleRefresh = vi.fn();

      render(
        <DailyStudyPlanCard
          plan={emptyPlan}
          loading={false}
          error={null}
          onRefresh={handleRefresh}
          onToggleComplete={vi.fn()}
          onOpenGoalModal={vi.fn()}
          selectedDate={emptyPlan.date}
          onDateChange={vi.fn()}
        />
      );

      expect(screen.getByText(/No tasks scheduled for today/i)).toBeInTheDocument();
      const generateBtn = screen.getByRole('button', { name: /Generate Today's Study Plan/i });
      expect(generateBtn).toBeInTheDocument();
      fireEvent.click(generateBtn);
      expect(handleRefresh).toHaveBeenCalledWith(true);
    });
  });

  describe('StudyGoalModal Component', () => {
    it('allows adjusting daily study minutes slider and active days', async () => {
      const handleSave = vi.fn().mockResolvedValue(undefined);
      const handleClose = vi.fn();

      render(
        <StudyGoalModal
          goal={mockGoal}
          isOpen={true}
          onClose={handleClose}
          onSave={handleSave}
        />
      );

      expect(screen.getByText('Adjust Study Target & Schedule')).toBeInTheDocument();
      expect(screen.getByDisplayValue('CBSE Class 12 Boards Preparation')).toBeInTheDocument();

      // Toggle study day
      const satButton = screen.getByRole('button', { name: 'Sat' });
      fireEvent.click(satButton);

      // Submit form
      const saveButton = screen.getByRole('button', { name: /Save Study Target/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(handleSave).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'CBSE Class 12 Boards Preparation',
            daily_study_minutes: 120,
            preferred_days: expect.arrayContaining(['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']),
          })
        );
      });
    });
  });

  describe('CurriculumRoadmapCard Component', () => {
    it('renders overall syllabus completion, subject tabs, and expandable chapters', () => {
      render(
        <CurriculumRoadmapCard
          roadmap={mockRoadmap}
          loading={false}
          onOpenLessons={vi.fn()}
        />
      );

      expect(screen.getByText('Academic Curriculum Roadmap')).toBeInTheDocument();
      expect(screen.getByText(/5 \/ 20 Lessons \(25%\)/i)).toBeInTheDocument();
      expect(screen.getByText('Electric Charges and Fields')).toBeInTheDocument();
      expect(screen.getByText('Mastered')).toBeInTheDocument();

      // Click chapter to expand details
      fireEvent.click(screen.getByText('Electric Charges and Fields'));
      expect(screen.getByText(/4 verified educational lesson modules/i)).toBeInTheDocument();
    });
  });

  describe('Integrated Dashboard Planner Section', () => {
    it('fetches and mounts planner card directly below KPI section on dashboard', async () => {
      vi.spyOn(api, 'getDashboardAnalytics').mockResolvedValue({
        lessons_completed_count: 5,
        lessons_in_progress_count: 2,
        practice_sessions_completed_count: 8,
        total_questions_answered: 40,
        total_correct_answers: 32,
        overall_accuracy_percentage: 80.0,
        total_practice_time_seconds: 1800,
        daily_study_goal_minutes: 120,
        recent_activity: [],
      });
      vi.spyOn(api, 'getTopicAnalytics').mockResolvedValue([]);
      vi.spyOn(api, 'getLearningRecommendations').mockResolvedValue([]);
      vi.spyOn(api, 'getDailyStudyPlan').mockResolvedValue(mockPlan);
      vi.spyOn(api, 'getStudyGoal').mockResolvedValue(mockGoal);
      vi.spyOn(api, 'getCurriculumRoadmap').mockResolvedValue(mockRoadmap);

      render(
        <StudentDashboard
          onOpenOnboarding={vi.fn()}
          onOpenLessons={vi.fn()}
        />
      );

      // Verify KPI loaded
      await waitFor(() => {
        expect(screen.getByText('5')).toBeInTheDocument();
      });

      // Verify Daily Study Plan Card mounted
      await waitFor(() => {
        expect(screen.getByText(/Today's Learning Roadmap & Study Plan/i)).toBeInTheDocument();
        expect(screen.getByText('Resume: Coulomb Law and Superposition Principle')).toBeInTheDocument();
      });

      // Verify Curriculum Roadmap Card mounted
      expect(screen.getByText('Academic Curriculum Roadmap')).toBeInTheDocument();
      expect(screen.getByText('Syllabus Completion & Mastery Tracker')).toBeInTheDocument();
    });
  });
});
