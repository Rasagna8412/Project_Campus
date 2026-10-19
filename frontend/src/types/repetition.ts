/**
 * Spaced Repetition and Revision Queue TypeScript Interfaces.
 */

export interface ReviewItemSummary {
  id: string;
  topic_id: string;
  topic_title: string;
  subject_id: string;
  subject_name: string;
  chapter_title: string;
  due_date: string;
  repetition_count: number;
  interval_days: number;
  ease_factor: number;
  status: 'LEARNING' | 'REVIEW' | 'MASTERED';
  is_overdue: boolean;
  sample_question_count: number;
}

export interface ReviewQueueResponse {
  date: string;
  total_due_count: number;
  overdue_count: number;
  returned_count: number;
  items: ReviewItemSummary[];
}

export interface ReviewSubmitRequest {
  quality_score: number;
  time_spent_seconds?: number;
}

export interface ReviewSubmitResponse {
  review_item_id: string;
  repetition_count: number;
  ease_factor: number;
  interval_days: number;
  next_due_date: string;
  quality_score: number;
  status: string;
  message: string;
}

export interface ReviewLogItem {
  id: string;
  review_item_id: string;
  topic_id: string;
  topic_title: string;
  quality_score: number;
  time_spent_seconds: number;
  scheduled_interval_days: number;
  next_interval_days: number;
  ease_factor_before: number;
  ease_factor_after: number;
  reviewed_at: string;
}

export interface ReviewHistoryResponse {
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: ReviewLogItem[];
}

export interface ReviewStatsResponse {
  total_tracked_topics: number;
  due_today_count: number;
  mastered_count: number;
  average_ease_factor: number;
  successful_review_rate_percentage: number | null;
}
