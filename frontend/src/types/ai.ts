/**
 * Type definitions for Campus AI Tutor, Quiz Generation, and Subscription Entitlements.
 */

export type AITutorMode = 'EXPLAIN' | 'SIMPLIFY' | 'EXAMPLE' | 'HINT' | 'QUIZ';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AITutorChatRequest {
  message: string;
  lesson_id?: string;
  topic_id?: string;
  mode?: AITutorMode;
  history?: ChatMessage[];
}

export interface AITutorQuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

export interface AITutorChatResponse {
  response: string;
  mode: AITutorMode;
  lesson_id?: string;
  lesson_title?: string;
  grounding_sources: string[];
  quiz_questions?: AITutorQuizQuestion[];
  provider: string;
  tokens_used: number;
  tier: 'FREE' | 'PRO';
  daily_quota: number;
  daily_used: number;
  daily_remaining: number;
}

export interface SubscriptionEntitlementResponse {
  tier: 'FREE' | 'PRO';
  daily_tutor_quota: number;
  daily_tutor_used: number;
  daily_tutor_remaining: number;
  is_unlimited: boolean;
  valid_until?: string | null;
  features: string[];
}

export interface AITutorHistoryItem {
  id: string;
  lesson_id?: string | null;
  mode: AITutorMode;
  user_query: string;
  tutor_response: string;
  grounding_sources: string[];
  created_at: string;
}
