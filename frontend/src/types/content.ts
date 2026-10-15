/**
 * Academic Curriculum Content Types for Milestone 3
 */

export type SectionType = 'CONCEPT' | 'WORKED_EXAMPLE' | 'KEY_FORMULA' | 'NOTE';

export type ContentStatus = 'DRAFT' | 'IN_REVIEW' | 'PUBLISHED' | 'ARCHIVED';

export interface LessonSection {
  id: string;
  lesson_id: string;
  section_number: number;
  title: string;
  content_markdown: string;
  section_type: SectionType;
  display_order: number;
}

export interface LessonSummary {
  id: string;
  topic_id: string;
  title: string;
  slug: string;
  summary: string | null;
  learning_objectives: string[] | null;
  estimated_read_time_minutes: number;
  status: ContentStatus;
  display_order: number;
  provenance: string | null;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface LessonDetail extends LessonSummary {
  sections: LessonSection[];
}

export interface Topic {
  id: string;
  chapter_id: string;
  topic_number: number;
  title: string;
  slug: string;
  importance_weight: number;
  display_order: number;
  published_lessons_count: number;
}

export interface Chapter {
  id: string;
  subject_id: string;
  chapter_number: number;
  title: string;
  slug: string;
  summary: string | null;
  display_order: number;
  topics: Topic[];
}
