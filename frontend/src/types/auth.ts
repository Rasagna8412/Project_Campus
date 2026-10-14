export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  roles: string[];
  onboarding_completed: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user: User;
}

export interface SubjectItem {
  id: string;
  grade_stage_id?: string;
  code: string;
  name: string;
  icon_url?: string | null;
  display_order: number;
}

export interface GradeStageItem {
  id: string;
  board_id: string;
  code: string;
  name: string;
  display_order: number;
  subjects: SubjectItem[];
}

export interface CurriculumBoard {
  id: string;
  code: string;
  name: string;
  country_code: string;
  description?: string | null;
  is_active: boolean;
  grades: GradeStageItem[];
}

export interface StudentProfile {
  id: string;
  user_id: string;
  full_name: string;
  email: string;
  target_curriculum_id?: string | null;
  target_curriculum_name?: string | null;
  target_curriculum_code?: string | null;
  grade_stage_id?: string | null;
  grade_stage_name?: string | null;
  grade_stage_code?: string | null;
  target_exam_year?: number | null;
  daily_study_goal_minutes: number;
  preferred_language: string;
  onboarding_completed: boolean;
  selected_subjects: SubjectItem[];
  created_at: string;
  updated_at: string;
}

export interface OnboardingPayload {
  target_curriculum_id: string;
  grade_stage_id: string;
  target_exam_year?: number;
  selected_subject_ids: string[];
  daily_study_goal_minutes: number;
  preferred_language?: string;
  complete: boolean;
}
