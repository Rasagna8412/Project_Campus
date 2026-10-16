export interface LessonProgress {
  id: string;
  user_id: string;
  lesson_id: string;
  topic_id?: string;
  lesson_title?: string;
  status: 'IN_PROGRESS' | 'COMPLETED';
  started_at: string;
  completed_at?: string;
  last_accessed_at: string;
}

export interface ActivityItem {
  activity_type: 'PRACTICE_SESSION' | 'LESSON_COMPLETED';
  id: string;
  title: string;
  subject_name?: string;
  subtitle: string;
  timestamp: string;
  is_completed: boolean;
}

export interface DashboardAnalytics {
  lessons_completed_count: number;
  lessons_in_progress_count: number;
  practice_sessions_completed_count: number;
  total_questions_answered: number;
  total_correct_answers: number;
  overall_accuracy_percentage: number | null;
  total_practice_time_seconds: number;
  daily_study_goal_minutes: number;
  recent_activity: ActivityItem[];
}

export interface TopicPerformance {
  topic_id: string;
  topic_title: string;
  topic_number: number;
  chapter_title: string;
  subject_name: string;
  total_attempts: number;
  correct_attempts: number;
  incorrect_attempts: number;
  observed_accuracy_percentage: number | null;
  completed_sessions_count: number;
  last_practiced_at?: string;
  status_category: 'STRONG' | 'DEVELOPING' | 'NEEDS_REVIEW' | 'INSUFFICIENT_DATA';
}

export interface LearningRecommendation {
  type: 'RESUME_LESSON' | 'REVISE_TOPIC' | 'PRACTICE_TOPIC' | 'NEXT_LESSON';
  priority: number;
  title: string;
  reason: string;
  target_id: string;
  target_title: string;
  subject_name?: string;
  action_label: string;
}
