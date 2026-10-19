/**
 * TypeScript Interfaces for Student Analytics Trends, Adherence, and Diagnostic Matrix.
 */

export interface DailyPracticeTrendItem {
  date: string;
  questions_answered: number;
  correct_count: number;
  accuracy_percentage: number | null;
  practice_minutes: number;
}

export interface PracticeTrendsResponse {
  days_count: number;
  start_date: string;
  end_date: string;
  total_questions_answered: number;
  total_correct_count: number;
  overall_accuracy_percentage: number | null;
  total_practice_minutes: number;
  daily_trends: DailyPracticeTrendItem[];
}

export interface DailyPlannerTrendItem {
  date: string;
  day_of_week: string;
  is_preferred_day: boolean;
  has_plan: boolean;
  planned_minutes: number;
  completed_minutes: number;
  tasks_count: number;
  completed_tasks_count: number;
  is_goal_met: boolean;
}

export interface PlannerTrendsResponse {
  daily_study_goal_minutes: number;
  days_count: number;
  preferred_days_count: number;
  goals_met_count: number;
  adherence_rate_percentage: number | null;
  total_planned_minutes: number;
  total_completed_minutes: number;
  daily_trends: DailyPlannerTrendItem[];
}

export interface RetentionForecastItem {
  date: string;
  due_count: number;
}

export interface RetentionTrendsResponse {
  active_streak_days: number;
  last_reviewed_date: string | null;
  is_streak_active_today: boolean;
  due_today_count: number;
  overdue_1_to_3_days: number;
  overdue_4_plus_days: number;
  total_overdue_count: number;
  forecast_next_7_days: RetentionForecastItem[];
}

export type DiagnosticState =
  | 'CRITICAL_GAP'
  | 'UNPRACTICED_FOUNDATION'
  | 'SOLIDIFYING'
  | 'MASTERED'
  | 'NOT_STARTED';

export interface DiagnosticTopicItem {
  topic_id: string;
  topic_title: string;
  subject_id: string;
  subject_name: string;
  chapter_title: string;
  lesson_status: string;
  total_attempts: number;
  observed_accuracy_percentage: number | null;
  practice_category: string;
  review_status: string | null;
  review_interval_days: number | null;
  is_review_overdue: boolean;
  diagnostic_state: DiagnosticState;
  action_recommendation: string;
}

export interface DiagnosticMatrixResponse {
  total_topics_analyzed: number;
  critical_gaps_count: number;
  unpracticed_foundations_count: number;
  solidifying_count: number;
  mastered_count: number;
  topics: DiagnosticTopicItem[];
}
