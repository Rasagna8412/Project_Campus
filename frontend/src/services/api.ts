import { HealthResponse } from '../types/api';
import {
  CurriculumBoard,
  OnboardingPayload,
  StudentProfile,
  TokenResponse,
  User,
} from '../types/auth';
import {
  Chapter,
  LessonDetail,
  LessonSummary,
  Topic,
} from '../types/content';
import {
  CreateErrataPayload,
  CreatePracticeSessionPayload,
  ErrataReport,
  PracticeSession,
  PracticeSessionSummary,
  QuestionEvaluation,
  StudentQuestion,
  SubmitAnswerPayload,
} from '../types/assessment';
import {
  DashboardAnalytics,
  LearningRecommendation,
  LessonProgress,
  TopicPerformance,
} from '../types/progress';
import {
  CurriculumRoadmap,
  DailyStudyPlan,
  StudyGoal,
  StudyGoalPayload,
  StudyTask,
} from '../types/planner';
import {
  ReviewHistoryResponse,
  ReviewQueueResponse,
  ReviewStatsResponse,
  ReviewSubmitRequest,
  ReviewSubmitResponse,
} from '../types/repetition';
import {
    DiagnosticMatrixResponse,
    PlannerTrendsResponse,
    PracticeTrendsResponse,
    RetentionTrendsResponse,
} from '../types/analytics_trends';
import {
  AITutorChatRequest,
  AITutorChatResponse,
  AITutorHistoryItem,
  SubscriptionEntitlementResponse,
} from '../types/ai';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const TOKEN_STORAGE_KEY = 'campus_auth_token';

export function getAuthToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setAuthToken(token: string): void {
  try {
    sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
  } catch {
    // SessionStorage unavailable
  }
}

export function removeAuthToken(): void {
  try {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    // SessionStorage unavailable
  }
}

/**
 * Fetch wrapper with timeout and automatic Authorization header attachment.
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs = 6000
): Promise<T> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  const headers: Record<string, string> = {
    'Accept': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (options.body && typeof options.body === 'string' && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
      signal: controller.signal,
    });

    if (response.status === 401) {
      // Clear token on 401 unauthorized
      removeAuthToken();
    }

    if (!response.ok) {
      let errorMessage = `HTTP error ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map((d: { msg?: string }) => d.msg || '').join(', ');
          } else {
            errorMessage = errorData.detail;
          }
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
      } catch {
        // Body was not json
      }
      throw new Error(errorMessage);
    }

    return await response.json() as T;
  } catch (err: unknown) {
    if (err instanceof Error) {
      if (err.name === 'AbortError') {
        throw new Error('Backend request timed out (service unreachable)');
      }
      throw err;
    }
    throw new Error('Unknown network communication error');
  } finally {
    clearTimeout(id);
  }
}

/**
 * Backend Health Verification
 */
export async function checkBackendHealth(verifyDatabase = true): Promise<HealthResponse> {
  const endpoint = verifyDatabase
    ? '/api/v1/health?check_db=true'
    : '/health';
  return await apiRequest<HealthResponse>(endpoint, { method: 'GET' });
}

/**
 * Authentication Endpoints
 */
export async function registerStudent(payload: {
  email: string;
  password: string;
  full_name: string;
}): Promise<TokenResponse> {
  const data = await apiRequest<TokenResponse>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (data.access_token) {
    setAuthToken(data.access_token);
  }
  return data;
}

export async function loginUser(payload: {
  email: string;
  password: string;
}): Promise<TokenResponse> {
  const data = await apiRequest<TokenResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (data.access_token) {
    setAuthToken(data.access_token);
  }
  return data;
}

export async function logoutUser(): Promise<{ status: string; message: string }> {
  try {
    const res = await apiRequest<{ status: string; message: string }>('/api/v1/auth/logout', {
      method: 'POST',
    });
    return res;
  } finally {
    removeAuthToken();
  }
}

export async function getCurrentUser(): Promise<User> {
  return await apiRequest<User>('/api/v1/auth/me', { method: 'GET' });
}

/**
 * Curriculum Taxonomy
 */
export async function getCurricula(): Promise<CurriculumBoard[]> {
  return await apiRequest<CurriculumBoard[]>('/api/v1/curricula/', { method: 'GET' });
}

export async function getSubjectChapters(subjectId: string): Promise<Chapter[]> {
  return await apiRequest<Chapter[]>(`/api/v1/curricula/subjects/${subjectId}/chapters`, {
    method: 'GET',
  });
}

export async function getChapterTopics(chapterId: string): Promise<Topic[]> {
  return await apiRequest<Topic[]>(`/api/v1/curricula/chapters/${chapterId}/topics`, {
    method: 'GET',
  });
}

export async function getTopicLessons(topicId: string): Promise<LessonSummary[]> {
  return await apiRequest<LessonSummary[]>(`/api/v1/curricula/topics/${topicId}/lessons`, {
    method: 'GET',
  });
}

export async function getLessonDetail(lessonId: string): Promise<LessonDetail> {
  return await apiRequest<LessonDetail>(`/api/v1/curricula/lessons/${lessonId}`, {
    method: 'GET',
  });
}

/**
 * Student Profile & Onboarding
 */
export async function getStudentProfile(): Promise<StudentProfile> {
  return await apiRequest<StudentProfile>('/api/v1/student/profile', { method: 'GET' });
}

export async function submitStudentOnboarding(
  payload: OnboardingPayload
): Promise<StudentProfile> {
  return await apiRequest<StudentProfile>('/api/v1/student/onboarding', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export async function updateStudentProfile(payload: {
  daily_study_goal_minutes?: number;
  target_exam_year?: number;
  preferred_language?: string;
}): Promise<StudentProfile> {
  return await apiRequest<StudentProfile>('/api/v1/student/profile', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export async function deleteStudentAccount(): Promise<{ status: string; message: string }> {
  try {
    return await apiRequest<{ status: string; message: string }>(
      '/api/v1/student/account',
      { method: 'DELETE' }
    );
  } finally {
    removeAuthToken();
  }
}

/**
 * Question Bank, Topic Practice Engine & Assessment
 */
export async function getTopicQuestions(
  topicId: string,
  difficulty?: string
): Promise<StudentQuestion[]> {
  const query = difficulty ? `?difficulty=${encodeURIComponent(difficulty)}` : '';
  return await apiRequest<StudentQuestion[]>(
    `/api/v1/practice/topics/${topicId}/questions${query}`,
    { method: 'GET' }
  );
}

export async function createPracticeSession(
  payload: CreatePracticeSessionPayload
): Promise<PracticeSession> {
  return await apiRequest<PracticeSession>('/api/v1/practice/sessions', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getPracticeSession(sessionId: string): Promise<PracticeSession> {
  return await apiRequest<PracticeSession>(`/api/v1/practice/sessions/${sessionId}`, {
    method: 'GET',
  });
}

export async function submitAnswer(
  payload: SubmitAnswerPayload
): Promise<QuestionEvaluation> {
  return await apiRequest<QuestionEvaluation>('/api/v1/practice/submit', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function reportQuestionErrata(
  questionId: string,
  payload: CreateErrataPayload
): Promise<ErrataReport> {
  return await apiRequest<ErrataReport>(
    `/api/v1/practice/questions/${questionId}/report-errata`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    }
  );
}

export async function getPracticeHistory(
  limit = 20
): Promise<PracticeSessionSummary[]> {
  return await apiRequest<PracticeSessionSummary[]>(
    `/api/v1/practice/history?limit=${limit}`,
    { method: 'GET' }
  );
}

/**
 * Lesson Progress Tracking
 */
export async function getStudentLessonProgress(): Promise<LessonProgress[]> {
  return await apiRequest<LessonProgress[]>('/api/v1/student/progress/lessons', {
    method: 'GET',
  });
}

export async function getLessonProgress(lessonId: string): Promise<LessonProgress> {
  return await apiRequest<LessonProgress>(`/api/v1/student/progress/lessons/${lessonId}`, {
    method: 'GET',
  });
}

export async function startLessonProgress(lessonId: string): Promise<LessonProgress> {
  return await apiRequest<LessonProgress>(`/api/v1/student/progress/lessons/${lessonId}/start`, {
    method: 'POST',
  });
}

export async function completeLessonProgress(lessonId: string): Promise<LessonProgress> {
  return await apiRequest<LessonProgress>(`/api/v1/student/progress/lessons/${lessonId}/complete`, {
    method: 'POST',
  });
}

/**
 * Learning Analytics & Diagnostic Recommendations
 */
export async function getDashboardAnalytics(): Promise<DashboardAnalytics> {
  return await apiRequest<DashboardAnalytics>('/api/v1/student/analytics/dashboard', {
    method: 'GET',
  });
}

export async function getTopicAnalytics(): Promise<TopicPerformance[]> {
  return await apiRequest<TopicPerformance[]>('/api/v1/student/analytics/topics', {
    method: 'GET',
  });
}

export async function getLearningRecommendations(): Promise<LearningRecommendation[]> {
  return await apiRequest<LearningRecommendation[]>('/api/v1/student/analytics/recommendations', {
    method: 'GET',
  });
}

/**
 * Study Planner & Learning Roadmap
 */
export async function getStudyGoal(): Promise<StudyGoal> {
  return await apiRequest<StudyGoal>('/api/v1/planner/goal', {
    method: 'GET',
  });
}

export async function updateStudyGoal(payload: StudyGoalPayload): Promise<StudyGoal> {
  return await apiRequest<StudyGoal>('/api/v1/planner/goal', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getDailyStudyPlan(planDate?: string): Promise<DailyStudyPlan> {
  const query = planDate ? `?plan_date=${planDate}` : '';
  return await apiRequest<DailyStudyPlan>(`/api/v1/planner/daily${query}`, {
    method: 'GET',
  });
}

export async function generateDailyStudyPlan(
  planDate?: string,
  forceRefresh: boolean = false
): Promise<DailyStudyPlan> {
  const params = new URLSearchParams();
  if (planDate) params.append('plan_date', planDate);
  if (forceRefresh) params.append('force_refresh', 'true');
  const qs = params.toString() ? `?${params.toString()}` : '';
  return await apiRequest<DailyStudyPlan>(`/api/v1/planner/daily/generate${qs}`, {
    method: 'POST',
  });
}

export async function toggleTaskComplete(
  taskId: string,
  isCompleted: boolean
): Promise<StudyTask> {
  return await apiRequest<StudyTask>(`/api/v1/planner/tasks/${taskId}/complete`, {
    method: 'PATCH',
    body: JSON.stringify({ is_completed: isCompleted }),
  });
}

export async function rescheduleTask(
  taskId: string,
  newDate: string
): Promise<StudyTask> {
  return await apiRequest<StudyTask>(`/api/v1/planner/tasks/${taskId}/reschedule`, {
    method: 'PATCH',
    body: JSON.stringify({ new_date: newDate }),
  });
}

export async function getCurriculumRoadmap(): Promise<CurriculumRoadmap> {
  return await apiRequest<CurriculumRoadmap>('/api/v1/planner/roadmap', {
    method: 'GET',
  });
}

/**
 * Spaced Repetition and Revision Queue Endpoints
 */
export async function getReviewQueue(
  subjectId?: string,
  limit?: number
): Promise<ReviewQueueResponse> {
  const params = new URLSearchParams();
  if (subjectId) params.append('subject_id', subjectId);
  if (limit !== undefined) params.append('limit', limit.toString());
  const qs = params.toString() ? `?${params.toString()}` : '';
  return await apiRequest<ReviewQueueResponse>(`/api/v1/review/queue${qs}`, {
    method: 'GET',
  });
}

export async function submitReviewRating(
  itemId: string,
  qualityScore: number,
  timeSpentSeconds?: number
): Promise<ReviewSubmitResponse> {
  const payload: ReviewSubmitRequest = {
    quality_score: qualityScore,
    time_spent_seconds: timeSpentSeconds,
  };
  return await apiRequest<ReviewSubmitResponse>(`/api/v1/review/items/${itemId}/submit`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getReviewHistory(
  page: number = 1,
  pageSize: number = 20
): Promise<ReviewHistoryResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  return await apiRequest<ReviewHistoryResponse>(`/api/v1/review/history?${params.toString()}`, {
    method: 'GET',
  });
}

export async function getReviewStats(): Promise<ReviewStatsResponse> {
  return await apiRequest<ReviewStatsResponse>('/api/v1/review/stats', {
    method: 'GET',
  });
}

/**
 * Milestone 8: Student Learning Analytics, Diagnostic Trends & Progress Visualization Endpoints
 */

export async function getPracticeTrends(
  days: number = 7
): Promise<PracticeTrendsResponse> {
  return await apiRequest<PracticeTrendsResponse>(
    `/api/v1/student/analytics/trends/practice?days=${days}`,
    { method: 'GET' }
  );
}

export async function getPlannerTrends(
  days: number = 7
): Promise<PlannerTrendsResponse> {
  return await apiRequest<PlannerTrendsResponse>(
    `/api/v1/student/analytics/trends/planner?days=${days}`,
    { method: 'GET' }
  );
}

export async function getRetentionTrends(): Promise<RetentionTrendsResponse> {
  return await apiRequest<RetentionTrendsResponse>(
    '/api/v1/student/analytics/trends/retention',
    { method: 'GET' }
  );
}

export async function getDiagnosticMatrix(): Promise<DiagnosticMatrixResponse> {
  return await apiRequest<DiagnosticMatrixResponse>(
    '/api/v1/student/analytics/diagnostic-matrix',
    { method: 'GET' }
  );
}

/**
 * Campus AI Tutor and Subscription Entitlements API Endpoints
 */

export async function askAITutor(
  payload: AITutorChatRequest
): Promise<AITutorChatResponse> {
  return await apiRequest<AITutorChatResponse>('/api/v1/tutor/chat', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getSubscriptionEntitlements(): Promise<SubscriptionEntitlementResponse> {
  return await apiRequest<SubscriptionEntitlementResponse>('/api/v1/tutor/entitlements', {
    method: 'GET',
  });
}

export async function upgradeSubscriptionTier(
  targetTier: 'FREE' | 'PRO'
): Promise<SubscriptionEntitlementResponse> {
  return await apiRequest<SubscriptionEntitlementResponse>('/api/v1/tutor/upgrade-preview', {
    method: 'POST',
    body: JSON.stringify({ target_tier: targetTier }),
  });
}

export async function getAITutorHistory(
  limit: number = 10
): Promise<AITutorHistoryItem[]> {
  return await apiRequest<AITutorHistoryItem[]>(`/api/v1/tutor/history?limit=${limit}`, {
    method: 'GET',
  });
}





