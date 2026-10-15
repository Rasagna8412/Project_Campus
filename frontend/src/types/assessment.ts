/**
 * Assessment, Question Bank, Practice Engine, and Errata Types.
 */

export type QuestionType = 'single_choice' | 'multiple_choice' | 'numerical' | 'integer';

export type DifficultyLevel = 'EASY' | 'MEDIUM' | 'HARD';

export type ErrataIssueType =
  | 'INCORRECT_ANSWER'
  | 'TYPO_OR_GRAMMAR'
  | 'AMBIGUOUS_QUESTION'
  | 'LATEX_RENDERING_ERROR'
  | 'OTHER';

export interface QuestionOption {
  id: string;
  option_key: string;
  content_latex: string;
  order: number;
}

export interface StudentQuestion {
  id: string;
  topic_id: string;
  lesson_id?: string | null;
  question_type: QuestionType;
  difficulty: DifficultyLevel;
  content_latex: string;
  options: QuestionOption[];
  tolerance?: number | null;
  created_at: string;
}

export interface QuestionEvaluation {
  question_id: string;
  is_correct: boolean;
  score: number;
  correct_options?: string[] | null;
  correct_numerical?: number | null;
  correct_integer?: number | null;
  explanation_latex?: string | null;
  attempt_id?: string | null;
  session_id?: string | null;
}

export interface PracticeSession {
  id: string;
  user_id: string;
  topic_id: string;
  total_questions: number;
  correct_count: number;
  score: number;
  is_completed: boolean;
  started_at: string;
  completed_at?: string | null;
  question_ids?: string[];
  questions?: StudentQuestion[];
}

export interface PracticeSessionSummary {
  id: string;
  topic_id: string;
  topic_title?: string;
  total_questions: number;
  correct_count: number;
  score: number;
  is_completed: boolean;
  started_at: string;
  completed_at?: string | null;
}

export interface CreatePracticeSessionPayload {
  topic_id: string;
  difficulty?: DifficultyLevel | null;
  limit?: number;
}

export interface SubmitAnswerPayload {
  question_id: string;
  session_id?: string | null;
  selected_options?: string[] | null;
  numerical_value?: number | null;
  integer_value?: number | null;
  time_spent_seconds?: number;
}

export interface CreateErrataPayload {
  issue_type: ErrataIssueType;
  description: string;
}

export interface ErrataReport {
  id: string;
  question_id: string;
  user_id: string;
  issue_type: string;
  description: string;
  status: string;
  created_at: string;
}
