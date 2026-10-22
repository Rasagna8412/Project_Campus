import React, { useState, useEffect, useRef } from 'react';
import {
  AlertCircle,
  Bot,
  CheckCircle2,
  ChevronRight,
  Crown,
  Lightbulb,
  Loader2,
  Send,
  ShieldCheck,
  Sparkles,
  X,
  XCircle,
  Zap,
} from 'lucide-react';
import {
  AITutorChatRequest,
  AITutorChatResponse,
  AITutorMode,
  AITutorQuizQuestion,
  SubscriptionEntitlementResponse,
} from '../../types/ai';
import {
  askAITutor,
  getSubscriptionEntitlements,
} from '../../services/api';
import { renderMarkdown, renderMathInText } from '../curriculum/LessonContentRenderer';
import { SubscriptionModal } from '../subscription/SubscriptionModal';

interface MessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  groundingSources?: string[];
  quizQuestions?: AITutorQuizQuestion[];
  provider?: string;
  timestamp: string;
}

interface AITutorDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  initialLessonId?: string;
  initialLessonTitle?: string;
  initialTopicId?: string;
  initialTopicTitle?: string;
  initialPrompt?: string;
  initialMode?: AITutorMode;
}

export const AITutorDrawer: React.FC<AITutorDrawerProps> = ({
  isOpen,
  onClose,
  initialLessonId,
  initialLessonTitle,
  initialTopicId,
  initialTopicTitle,
  initialPrompt,
  initialMode = 'EXPLAIN',
}) => {
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [selectedMode, setSelectedMode] = useState<AITutorMode>(initialMode);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Quota & entitlements state
  const [entitlements, setEntitlements] = useState<SubscriptionEntitlementResponse | null>(null);
  const [isSubscriptionModalOpen, setIsSubscriptionModalOpen] = useState<boolean>(false);

  // Quiz state: questionIndex -> selectedOptionIndex
  const [quizAnswers, setQuizAnswers] = useState<Record<number, number>>({});
  const [quizSubmitted, setQuizSubmitted] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && typeof getSubscriptionEntitlements === 'function') {
      try {
        const promise = getSubscriptionEntitlements();
        if (promise && typeof promise.then === 'function') {
          promise
            .then((data) => {
              if (data) setEntitlements(data);
            })
            .catch(() => {});
        }
      } catch {
        // Handled gracefully
      }
    }
  }, [isOpen]);

  // Initial prompt handling
  useEffect(() => {
    if (isOpen && initialPrompt && messages.length === 0) {
      handleSendMessage(initialPrompt, initialMode);
    }
  }, [isOpen, initialPrompt]);

  // Scroll to bottom when messages update
  useEffect(() => {
    if (typeof messagesEndRef.current?.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  if (!isOpen) return null;

  const handleSendMessage = async (textToSend?: string, modeToUse?: AITutorMode) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || isLoading) return;

    const mode = modeToUse || selectedMode;

    const userMsg: MessageItem = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputMessage('');
    setIsLoading(true);
    setError(null);
    setQuizAnswers({});
    setQuizSubmitted(false);

    try {
      const payload: AITutorChatRequest = {
        message: text,
        lesson_id: initialLessonId,
        topic_id: initialTopicId,
        mode: mode,
      };

      const resp: AITutorChatResponse = await askAITutor(payload);

      const assistantMsg: MessageItem = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: resp.response,
        groundingSources: resp.grounding_sources,
        quizQuestions: resp.quiz_questions,
        provider: resp.provider,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);

      // Update remaining quota locally
      if (entitlements) {
        setEntitlements({
          ...entitlements,
          daily_tutor_used: resp.daily_used,
          daily_tutor_remaining: resp.daily_remaining,
        });
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to reach AI Tutor. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = (mode: AITutorMode, defaultQuery: string) => {
    setSelectedMode(mode);
    handleSendMessage(defaultQuery, mode);
  };

  const remaining = entitlements?.daily_tutor_remaining ?? 20;
  const isPro = entitlements?.tier === 'PRO';

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="tutor-drawer-title"
      className="fixed inset-0 z-50 overflow-hidden bg-slate-900/50 backdrop-blur-sm flex justify-end"
    >
      <div className="bg-white w-full max-w-xl h-full shadow-2xl flex flex-col relative animate-in slide-in-from-right duration-200">
        {/* Drawer Header */}
        <header className="p-4 sm:p-5 border-b border-slate-200 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-brand-600 flex items-center justify-center text-white shadow-md">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 id="tutor-drawer-title" className="font-bold text-base text-white">
                  Campus AI Tutor
                </h2>
                {isPro ? (
                  <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-amber-500 text-slate-950">
                    <Crown className="w-3 h-3" />
                    <span>PRO</span>
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                    Free Tier
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                {initialLessonTitle || initialTopicTitle
                  ? `Active: ${(initialLessonTitle || initialTopicTitle)?.slice(0, 32)}...`
                  : 'Grounded Academic Concept Clarifier'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsSubscriptionModalOpen(true)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-white/10 hover:bg-white/15 text-brand-300 border border-brand-400/30 transition-all flex items-center space-x-1"
              title="View quota and subscription options"
            >
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              <span>{isPro ? 'Unlimited' : `${remaining} left`}</span>
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
              aria-label="Close tutor panel"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Grounding Context Banner */}
        <div className="bg-slate-50 border-b border-slate-200 px-4 py-2.5 flex items-center justify-between text-xs text-slate-600">
          <div className="flex items-center space-x-2 overflow-hidden">
            <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span className="truncate">
              {initialLessonTitle || initialTopicTitle
                ? `Context: ${initialLessonTitle || initialTopicTitle}`
                : 'General Syllabus Grounding Active'}
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-400 flex-shrink-0 ml-2">
            Zero-Hallucination Guardrails
          </span>
        </div>

        {/* Mode Selector Pill Strip */}
        <div className="bg-white border-b border-slate-100 p-2 overflow-x-auto flex items-center space-x-1.5 text-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider px-2">Mode:</span>
          {(['EXPLAIN', 'SIMPLIFY', 'EXAMPLE', 'HINT', 'QUIZ'] as AITutorMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setSelectedMode(mode)}
              className={`px-3 py-1 rounded-lg font-semibold transition-all whitespace-nowrap text-xs ${
                selectedMode === mode
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {mode === 'EXPLAIN' && 'Explain'}
              {mode === 'SIMPLIFY' && 'Simplify'}
              {mode === 'EXAMPLE' && 'Worked Example'}
              {mode === 'HINT' && 'Conceptual Hint'}
              {mode === 'QUIZ' && 'Practice Quiz'}
            </button>
          ))}
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500 space-y-4">
              <div className="w-14 h-14 rounded-2xl bg-brand-50 border border-brand-200 text-brand-600 flex items-center justify-center shadow-sm">
                <Bot className="w-8 h-8" />
              </div>
              <div className="max-w-sm">
                <h3 className="font-bold text-slate-800 text-base">
                  What would you like to master today?
                </h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  Ask doubts, request analogies, generate practice quizzes, or walk through step-by-step derivations.
                </p>
              </div>

              {/* Quick Action Suggestion Chips */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-md pt-2">
                <button
                  onClick={() =>
                    handleQuickAction(
                      'EXPLAIN',
                      `Can you explain the main concept of ${initialLessonTitle || 'this topic'}?`
                    )
                  }
                  className="p-3 text-left rounded-xl border border-slate-200 hover:border-brand-400 hover:bg-brand-50/30 transition-all text-xs group"
                >
                  <p className="font-bold text-slate-800 group-hover:text-brand-700 flex items-center justify-between">
                    <span>Explain Concept</span>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-brand-600" />
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5">Foundational breakdown with formulas</p>
                </button>

                <button
                  onClick={() =>
                    handleQuickAction(
                      'SIMPLIFY',
                      `Can you explain ${initialLessonTitle || 'this concept'} using a simple everyday analogy?`
                    )
                  }
                  className="p-3 text-left rounded-xl border border-slate-200 hover:border-brand-400 hover:bg-brand-50/30 transition-all text-xs group"
                >
                  <p className="font-bold text-slate-800 group-hover:text-brand-700 flex items-center justify-between">
                    <span>Simplify Analogy</span>
                    <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5">Intuitive, beginner-friendly comparison</p>
                </button>

                <button
                  onClick={() =>
                    handleQuickAction(
                      'EXAMPLE',
                      `Show me a step-by-step numerical example for ${initialLessonTitle || 'this lesson'}.`
                    )
                  }
                  className="p-3 text-left rounded-xl border border-slate-200 hover:border-brand-400 hover:bg-brand-50/30 transition-all text-xs group"
                >
                  <p className="font-bold text-slate-800 group-hover:text-brand-700 flex items-center justify-between">
                    <span>Worked Example</span>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-brand-600" />
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5">Step-by-step problem & calculation</p>
                </button>

                <button
                  onClick={() =>
                    handleQuickAction(
                      'QUIZ',
                      `Generate a 3-question practice quiz based on ${initialLessonTitle || 'this lesson'}.`
                    )
                  }
                  className="p-3 text-left rounded-xl border border-slate-200 hover:border-brand-400 hover:bg-brand-50/30 transition-all text-xs group"
                >
                  <p className="font-bold text-slate-800 group-hover:text-brand-700 flex items-center justify-between">
                    <span>Practice Quiz</span>
                    <Sparkles className="w-3.5 h-3.5 text-brand-600" />
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5">3 multiple-choice check questions</p>
                </button>
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-[90%] rounded-2xl p-4 shadow-sm text-xs sm:text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-brand-600 text-white rounded-br-none'
                    : 'bg-white border border-slate-200 text-slate-800 rounded-bl-none'
                }`}
              >
                {msg.role === 'assistant' ? (
                  <div>
                    {/* Rendered Markdown & Math */}
                    <div
                      className="prose prose-slate max-w-none text-xs sm:text-sm text-slate-800 leading-relaxed"
                      dangerouslySetInnerHTML={{
                        __html: renderMarkdown(renderMathInText(msg.content)),
                      }}
                    />

                    {/* Interactive Quiz Runner if present */}
                    {msg.quizQuestions && msg.quizQuestions.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-slate-200 space-y-4">
                        <div className="flex items-center space-x-1.5 text-xs font-bold text-brand-700">
                          <Sparkles className="w-4 h-4 text-brand-600" />
                          <span>Interactive AI Check Questions</span>
                        </div>

                        {msg.quizQuestions.map((q, qIdx) => {
                          const selectedOpt = quizAnswers[qIdx];
                          const isCorrect = selectedOpt === q.correct_index;

                          return (
                            <div
                              key={qIdx}
                              className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 space-y-2.5"
                            >
                              <p className="font-bold text-slate-900 text-xs">
                                {qIdx + 1}. {q.question}
                              </p>

                              <div className="space-y-1.5">
                                {q.options.map((opt, optIdx) => {
                                  const isSelected = selectedOpt === optIdx;
                                  let optClass = 'border-slate-200 bg-white hover:bg-slate-100 text-slate-700';

                                  if (quizSubmitted) {
                                    if (optIdx === q.correct_index) {
                                      optClass = 'border-emerald-400 bg-emerald-50 text-emerald-900 font-bold';
                                    } else if (isSelected && !isCorrect) {
                                      optClass = 'border-rose-300 bg-rose-50 text-rose-800';
                                    } else {
                                      optClass = 'border-slate-200 opacity-50 bg-white';
                                    }
                                  } else if (isSelected) {
                                    optClass = 'border-brand-500 bg-brand-50 text-brand-900 font-bold ring-1 ring-brand-500';
                                  }

                                  return (
                                    <button
                                      key={optIdx}
                                      type="button"
                                      disabled={quizSubmitted}
                                      onClick={() =>
                                        setQuizAnswers((prev) => ({ ...prev, [qIdx]: optIdx }))
                                      }
                                      className={`w-full text-left p-2 rounded-lg border text-xs flex items-center justify-between transition-all ${optClass}`}
                                    >
                                      <span>{opt}</span>
                                      {quizSubmitted && optIdx === q.correct_index && (
                                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                                      )}
                                      {quizSubmitted && isSelected && !isCorrect && (
                                        <XCircle className="w-3.5 h-3.5 text-rose-600" />
                                      )}
                                    </button>
                                  );
                                })}
                              </div>

                              {quizSubmitted && (
                                <div className="mt-2 p-2.5 rounded-lg bg-white border border-slate-200 text-[11px] text-slate-600 leading-normal">
                                  <span className="font-bold text-slate-800">Explanation: </span>
                                  {q.explanation}
                                </div>
                              )}
                            </div>
                          );
                        })}

                        {!quizSubmitted ? (
                          <button
                            type="button"
                            onClick={() => setQuizSubmitted(true)}
                            disabled={Object.keys(quizAnswers).length < msg.quizQuestions.length}
                            className="w-full py-2 px-4 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white transition-all shadow-sm disabled:opacity-50"
                          >
                            Submit Quiz Answers
                          </button>
                        ) : (
                          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs font-bold text-emerald-900 text-center">
                            Quiz Completed! Review verified derivations above.
                          </div>
                        )}
                      </div>
                    )}

                    {/* Grounding Sources Badge */}
                    {msg.groundingSources && msg.groundingSources.length > 0 && (
                      <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-wrap items-center gap-1.5 text-[11px] text-slate-500">
                        <span className="font-semibold text-slate-600">Grounded In:</span>
                        {msg.groundingSources.map((src, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200"
                          >
                            {src}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <p>{msg.content}</p>
                )}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 px-1">{msg.timestamp}</span>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-start space-x-2.5">
              <div className="w-7 h-7 rounded-lg bg-brand-600 text-white flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-white border border-slate-200 p-3.5 rounded-2xl rounded-bl-none shadow-sm flex items-center space-x-2 text-xs text-slate-600">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-600" />
                <span>Consulting verified lesson syllabus and generating guidance...</span>
              </div>
            </div>
          )}

          {error && (
            <div
              role="alert"
              className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start space-x-2"
            >
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-bold">Tutoring Query Paused</p>
                <p className="mt-0.5">{error}</p>
                {error.includes('limit reached') && (
                  <button
                    onClick={() => setIsSubscriptionModalOpen(true)}
                    className="mt-2 inline-flex items-center space-x-1 px-3 py-1 rounded-lg bg-amber-600 text-white font-bold text-xs hover:bg-amber-700 shadow-sm"
                  >
                    <Crown className="w-3.5 h-3.5" />
                    <span>Upgrade to Pro for Unlimited Queries</span>
                  </button>
                )}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <footer className="p-4 border-t border-slate-200 bg-white space-y-2">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center space-x-2"
          >
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={`Ask a doubt about ${initialLessonTitle || 'this topic'}...`}
              disabled={isLoading}
              maxLength={1000}
              className="flex-grow px-4 py-2.5 rounded-xl border border-slate-200 text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:bg-slate-50"
            />
            <button
              type="submit"
              disabled={!inputMessage.trim() || isLoading}
              className="p-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white shadow-sm transition-all flex-shrink-0"
              aria-label="Send query"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>

          <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
            <span>Powered by Campus Grounded AI Engine</span>
            <span>{inputMessage.length}/1000</span>
          </div>
        </footer>

        {/* Subscription Modal */}
        <SubscriptionModal
          isOpen={isSubscriptionModalOpen}
          onClose={() => setIsSubscriptionModalOpen(false)}
          entitlements={entitlements}
          onEntitlementsUpdated={(updated) => setEntitlements(updated)}
        />
      </div>
    </div>
  );
};
