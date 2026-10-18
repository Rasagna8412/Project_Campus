/**
 * Study Planner, Goals, Tasks, and Learning Roadmap Type Definitions
 */

export type GoalStatus = 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'ARCHIVED';

export type TaskType =
  | 'STUDY_LESSON'
  | 'RESUME_LESSON'
  | 'PRACTICE_TOPIC'
  | 'REVISE_TOPIC';

export type TaskStatus = 'PENDING' | 'COMPLETED' | 'SKIPPED' | 'RESCHEDULED';

export interface StudyGoal {
  id: string;
  user_id: string;
  title: string;
  target_date: string | null;
  daily_study_minutes: number;
  preferred_days: string[];
  status: GoalStatus;
  created_at: string;
  updated_at: string;
}

export interface StudyGoalPayload {
  title?: string;
  target_date?: string | null;
  daily_study_minutes: number;
  preferred_days?: string[];
}

export interface StudyTask {
  id: string;
  user_id: string;
  goal_id: string | null;
  scheduled_date: string;
  task_type: TaskType;
  title: string;
  subject_id: string | null;
  subject_name: string | null;
  chapter_id: string | null;
  topic_id: string | null;
  lesson_id: string | null;
  estimated_minutes: number;
  status: TaskStatus;
  is_completed: boolean;
  completed_at: string | null;
  display_order: number;
  reason: string | null;
}

export interface DailyStudyPlan {
  date: string;
  target_minutes: number;
  planned_minutes: number;
  completed_minutes: number;
  is_fully_completed: boolean;
  tasks: StudyTask[];
}

export interface ChapterRoadmapItem {
  chapter_id: string;
  chapter_number: number;
  title: string;
  total_lessons: number;
  completed_lessons: number;
  is_completed: boolean;
}

export interface SubjectRoadmapItem {
  subject_id: string;
  subject_name: string;
  total_lessons: number;
  completed_lessons: number;
  in_progress_lessons: number;
  completion_percentage: number;
  chapters: ChapterRoadmapItem[];
}

export interface CurriculumRoadmap {
  total_lessons_count: number;
  completed_lessons_count: number;
  overall_completion_percentage: number;
  subjects: SubjectRoadmapItem[];
}
