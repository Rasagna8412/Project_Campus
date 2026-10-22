import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { AITutorDrawer } from '../components/tutor/AITutorDrawer';
import { CodingSandboxModal } from '../components/coding/CodingSandboxModal';
import { SubscriptionModal } from '../components/subscription/SubscriptionModal';
import * as api from '../services/api';
import {
  AITutorChatResponse,
  SubscriptionEntitlementResponse,
} from '../types/ai';

vi.mock('../services/api');

const mockEntitlements: SubscriptionEntitlementResponse = {
  tier: 'FREE',
  daily_tutor_quota: 20,
  daily_tutor_used: 2,
  daily_tutor_remaining: 18,
  is_unlimited: false,
  valid_until: null,
  features: [
    'CBSE & JEE Standard Curriculum Grounding',
    'Free Tier: 20 Daily Tutor Queries',
  ],
};

const mockChatResponse: AITutorChatResponse = {
  response: 'Coulomb\'s Law states that force is directly proportional to product of charges.',
  mode: 'EXPLAIN',
  lesson_id: 'lesson-1',
  lesson_title: 'Coulomb\'s Law & Superposition',
  grounding_sources: ['Section 1: Statement of Coulomb\'s Law'],
  provider: 'deterministic_grounded_engine',
  tokens_used: 120,
  tier: 'FREE',
  daily_quota: 20,
  daily_used: 3,
  daily_remaining: 17,
};

const mockQuizResponse: AITutorChatResponse = {
  response: 'Here are 3 practice quiz questions on Coulomb\'s Law:',
  mode: 'QUIZ',
  lesson_id: 'lesson-1',
  lesson_title: 'Coulomb\'s Law & Superposition',
  grounding_sources: ['Section 1: Statement of Coulomb\'s Law'],
  quiz_questions: [
    {
      question: 'How does force change if distance is doubled?',
      options: ['Halved', 'Quartered (1/4)', 'Doubled', 'Quadrupled'],
      correct_index: 1,
      explanation: 'Inverse-square law: 1/r^2 means 2^2 = 4 times smaller.',
    },
  ],
  provider: 'deterministic_grounded_engine',
  tokens_used: 140,
  tier: 'FREE',
  daily_quota: 20,
  daily_used: 4,
  daily_remaining: 16,
};

describe('Milestone D: Campus AI Tutor Component Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getSubscriptionEntitlements).mockResolvedValue(mockEntitlements);
    vi.mocked(api.askAITutor).mockResolvedValue(mockChatResponse);
  });

  it('renders AITutorDrawer with grounding header and mode pills', async () => {
    render(
      <AITutorDrawer
        isOpen={true}
        onClose={vi.fn()}
        initialLessonId="lesson-1"
        initialLessonTitle="Coulomb's Law & Superposition"
      />
    );

    expect(screen.getByText('Campus AI Tutor')).toBeInTheDocument();
    expect(screen.getAllByText(/Coulomb's Law & Superposition/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole('button', { name: 'Explain' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Simplify' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Worked Example' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Conceptual Hint' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Practice Quiz' })).toBeInTheDocument();
  });

  it('submits a student query and renders grounded response with citations', async () => {
    render(
      <AITutorDrawer
        isOpen={true}
        onClose={vi.fn()}
        initialLessonId="lesson-1"
        initialLessonTitle="Coulomb's Law & Superposition"
      />
    );

    const input = screen.getByPlaceholderText(/Ask a doubt about/);
    fireEvent.change(input, { target: { value: 'Can you explain the force formula?' } });

    const sendBtn = screen.getByLabelText('Send query');
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(api.askAITutor).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'Can you explain the force formula?',
          lesson_id: 'lesson-1',
          mode: 'EXPLAIN',
        })
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/Coulomb's Law states that force/)).toBeInTheDocument();
      expect(screen.getByText('Section 1: Statement of Coulomb\'s Law')).toBeInTheDocument();
    });
  });

  it('renders and completes an interactive AI-generated practice quiz', async () => {
    vi.mocked(api.askAITutor).mockResolvedValue(mockQuizResponse);

    render(
      <AITutorDrawer
        isOpen={true}
        onClose={vi.fn()}
        initialLessonId="lesson-1"
        initialLessonTitle="Coulomb's Law & Superposition"
      />
    );

    // Switch to QUIZ mode
    const quizPill = screen.getByRole('button', { name: 'Practice Quiz' });
    fireEvent.click(quizPill);

    const input = screen.getByPlaceholderText(/Ask a doubt about/);
    fireEvent.change(input, { target: { value: 'Give me a quiz' } });
    fireEvent.click(screen.getByLabelText('Send query'));

    await waitFor(() => {
      expect(screen.getByText(/How does force change if distance is doubled?/)).toBeInTheDocument();
      expect(screen.getByText('Quartered (1/4)')).toBeInTheDocument();
    });

    // Select the correct option
    const optionBtn = screen.getByText('Quartered (1/4)');
    fireEvent.click(optionBtn);

    // Click submit answers
    const submitBtn = screen.getByText('Submit Quiz Answers');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Quiz Completed! Review verified derivations above/)).toBeInTheDocument();
      expect(screen.getByText(/Inverse-square law/)).toBeInTheDocument();
    });
  });
});

describe('Milestone D: Coding Sandbox & Problem Studio Tests', () => {
  it('renders coding problem constraints, sample I/O, and switches languages', () => {
    render(
      <CodingSandboxModal
        isOpen={true}
        onClose={vi.fn()}
        topicTitle="Pointers and Dynamic Memory Allocation in C"
      />
    );

    expect(screen.getByText('Engineering Code Sandbox & Problem Studio')).toBeInTheDocument();
    expect(screen.getByText('Array Sum via Pointer Arithmetic')).toBeInTheDocument();
    expect(screen.getAllByText(/calculate_array_sum/).length).toBeGreaterThanOrEqual(1);

    // Switch to Python
    const pyBtn = screen.getByText('Python 3.11');
    fireEvent.click(pyBtn);
    expect(screen.getByDisplayValue(/def calculate_array_sum/)).toBeInTheDocument();

    // Switch back to C
    const cBtn = screen.getByText('C (GCC 12)');
    fireEvent.click(cBtn);
    expect(screen.getByDisplayValue(/int calculate_array_sum/)).toBeInTheDocument();
  });

  it('runs sample test cases and displays verified execution results', async () => {
    render(
      <CodingSandboxModal
        isOpen={true}
        onClose={vi.fn()}
        topicTitle="Pointers and Dynamic Memory Allocation in C"
      />
    );

    const runBtn = screen.getByText('Run Sample Tests');
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(screen.getByText('All 3 Sample Test Cases Passed!')).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it('toggles sandbox security architecture specification drawer', () => {
    render(
      <CodingSandboxModal
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    const specBtn = screen.getByText('Sandbox Security Spec');
    fireEvent.click(specBtn);

    expect(screen.getByText(/Isolated Production Sandbox Specification/)).toBeInTheDocument();
    expect(screen.getByText(/MicroVM Isolation/)).toBeInTheDocument();
    expect(screen.getByText(/Network Egress Block/)).toBeInTheDocument();
  });
});

describe('Milestone D: Subscription Entitlements & Upgrade Modal Tests', () => {
  it('renders Free and Pro tier plans with feature comparisons', () => {
    render(
      <SubscriptionModal
        isOpen={true}
        onClose={vi.fn()}
        entitlements={mockEntitlements}
        onEntitlementsUpdated={vi.fn()}
      />
    );

    expect(screen.getByText('Free Foundation')).toBeInTheDocument();
    expect(screen.getByText('Campus Pro')).toBeInTheDocument();
    expect(screen.getByText(/20 AI Tutor queries/)).toBeInTheDocument();
    expect(screen.getByText(/Unlimited Campus AI Tutor Queries/)).toBeInTheDocument();
    expect(screen.getByText('₹499')).toBeInTheDocument();
  });

  it('toggles subscription tier in pilot demo mode', async () => {
    const onUpdateMock = vi.fn();
    const updatedProEntitlements: SubscriptionEntitlementResponse = {
      ...mockEntitlements,
      tier: 'PRO',
      daily_tutor_quota: 500,
      daily_tutor_remaining: 500,
      is_unlimited: true,
    };
    vi.mocked(api.upgradeSubscriptionTier).mockResolvedValue(updatedProEntitlements);

    render(
      <SubscriptionModal
        isOpen={true}
        onClose={vi.fn()}
        entitlements={mockEntitlements}
        onEntitlementsUpdated={onUpdateMock}
      />
    );

    const activateBtn = screen.getByText(/Activate Pro/);
    fireEvent.click(activateBtn);

    await waitFor(() => {
      expect(api.upgradeSubscriptionTier).toHaveBeenCalledWith('PRO');
      expect(onUpdateMock).toHaveBeenCalledWith(updatedProEntitlements);
    });
  });
});
