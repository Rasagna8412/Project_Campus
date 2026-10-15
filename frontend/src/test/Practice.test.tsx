import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QuestionCard } from '../components/practice/QuestionCard';
import { PracticeModal } from '../components/practice/PracticeModal';
import { ErrataModal } from '../components/practice/ErrataModal';
import * as api from '../services/api';
import { QuestionEvaluation, StudentQuestion } from '../types/assessment';

vi.mock('../services/api');

const mockSingleChoiceQuestion: StudentQuestion = {
  id: 'q-mcq-1',
  topic_id: 'topic-coulomb-1',
  question_type: 'single_choice',
  difficulty: 'MEDIUM',
  content_latex: 'Two identical charges $q$ are separated by distance $r$. What happens if the distance is doubled?',
  options: [
    { id: 'opt-a', option_key: 'A', content_latex: 'Force doubles', order: 1 },
    { id: 'opt-b', option_key: 'B', content_latex: 'Force becomes $F/4$', order: 2 },
    { id: 'opt-c', option_key: 'C', content_latex: 'Force quadruples', order: 3 },
    { id: 'opt-d', option_key: 'D', content_latex: 'Force remains unchanged', order: 4 },
  ],
  created_at: '2026-03-30T10:00:00Z',
};

const mockNumericalQuestion: StudentQuestion = {
  id: 'q-num-1',
  topic_id: 'topic-coulomb-1',
  question_type: 'numerical',
  difficulty: 'EASY',
  content_latex: 'Calculate the magnitude of electrostatic force between two $1\\,\\mu\\text{C}$ charges at $1\\,\\text{m}$.',
  options: [],
  tolerance: 0.05,
  created_at: '2026-03-30T10:00:00Z',
};

describe('Practice Engine Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders question prompt, difficulty badge, and options', () => {
    const mockOnSubmit = vi.fn();
    render(
      <QuestionCard
        question={mockSingleChoiceQuestion}
        questionNumber={1}
        totalQuestions={3}
        onAnswerSubmit={mockOnSubmit}
      />
    );

    expect(screen.getByText('Question 1 of 3')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText(/Two identical charges/i)).toBeInTheDocument();

    // Check options are rendered
    expect(screen.getByText('A')).toBeInTheDocument();
    expect(screen.getByText('B')).toBeInTheDocument();
    expect(screen.getByText('Force doubles')).toBeInTheDocument();
    expect(screen.getByText('Submit Answer')).toBeInTheDocument();
  });

  it('allows selecting an option, submitting, and displays verified explanation', async () => {
    const mockEvaluation: QuestionEvaluation = {
      question_id: 'q-mcq-1',
      is_correct: true,
      score: 1.0,
      correct_options: ['B'],
      explanation_latex: 'By Inverse Square Law, force is inversely proportional to $r^2$, so $F \\to F/4$.',
    };
    const mockOnSubmit = vi.fn().mockResolvedValue(mockEvaluation);

    render(
      <QuestionCard
        question={mockSingleChoiceQuestion}
        questionNumber={1}
        totalQuestions={1}
        onAnswerSubmit={mockOnSubmit}
      />
    );

    // Click option B
    const optionBButton = screen.getByText('B').closest('button');
    expect(optionBButton).toBeInTheDocument();
    fireEvent.click(optionBButton!);

    // Click submit
    const submitBtn = screen.getByText('Submit Answer').closest('button');
    expect(submitBtn).toBeInTheDocument();
    fireEvent.click(submitBtn!);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          question_id: 'q-mcq-1',
          selected_options: ['B'],
        })
      );
    });

    // Verify feedback banner and educator derivation
    await waitFor(() => {
      expect(screen.getByText(/Correct! Outstanding work/i)).toBeInTheDocument();
      expect(screen.getByText(/Verified Step-by-Step Solution/i)).toBeInTheDocument();
      expect(screen.getByText(/Inverse Square Law/i)).toBeInTheDocument();
    });
  });

  it('renders numerical question and handles decimal input', async () => {
    const mockEvaluation: QuestionEvaluation = {
      question_id: 'q-num-1',
      is_correct: true,
      score: 1.0,
      correct_numerical: 0.009,
      explanation_latex: '$F = k \\frac{q_1 q_2}{r^2} = (9 \\times 10^9) \\frac{10^{-12}}{1} = 0.009\\,\\text{N}$.',
    };
    const mockOnSubmit = vi.fn().mockResolvedValue(mockEvaluation);

    render(
      <QuestionCard
        question={mockNumericalQuestion}
        questionNumber={2}
        totalQuestions={2}
        onAnswerSubmit={mockOnSubmit}
      />
    );

    const input = screen.getByPlaceholderText('e.g. 1.25');
    expect(input).toBeInTheDocument();

    fireEvent.change(input, { target: { value: '0.009' } });

    const submitBtn = screen.getByRole('button', { name: /Submit Answer/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          question_id: 'q-num-1',
          numerical_value: 0.009,
        })
      );
    });
  });

  it('submits question errata report successfully', async () => {
    vi.mocked(api.reportQuestionErrata).mockResolvedValue({
      id: 'errata-1',
      question_id: 'q-mcq-1',
      user_id: 'user-1',
      issue_type: 'INCORRECT_ANSWER',
      description: 'The second step in the formula derivation has a sign error.',
      status: 'SUBMITTED',
      created_at: '2026-03-30T10:00:00Z',
    });

    const mockOnClose = vi.fn();
    render(
      <ErrataModal
        questionId="q-mcq-1"
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Report Question Issue')).toBeInTheDocument();

    // Type description
    const textarea = screen.getByPlaceholderText(/Describe where the error occurs/i);
    fireEvent.change(textarea, {
      target: { value: 'The second step in the formula derivation has a sign error.' },
    });

    const submitBtn = screen.getByRole('button', { name: /Submit Report/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.reportQuestionErrata).toHaveBeenCalledWith('q-mcq-1', {
        issue_type: 'INCORRECT_ANSWER',
        description: 'The second step in the formula derivation has a sign error.',
      });
    });

    await waitFor(() => {
      expect(screen.getByText('Report Submitted')).toBeInTheDocument();
    });
  });

  it('renders PracticeModal and navigates through questions to summary', async () => {
    vi.mocked(api.createPracticeSession).mockResolvedValue({
      id: 'sess-123',
      user_id: 'u-1',
      topic_id: 'topic-coulomb-1',
      total_questions: 1,
      correct_count: 0,
      score: 0,
      is_completed: false,
      started_at: '2026-03-30T10:00:00Z',
      questions: [mockSingleChoiceQuestion],
    });

    vi.mocked(api.submitAnswer).mockResolvedValue({
      question_id: 'q-mcq-1',
      is_correct: true,
      score: 1.0,
      correct_options: ['B'],
      explanation_latex: 'Verified solution text.',
    });

    const mockOnClose = vi.fn();
    render(
      <PracticeModal
        topicId="topic-coulomb-1"
        topicTitle="Coulomb's Law Practice"
        isOpen={true}
        onClose={mockOnClose}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Coulomb's Law Practice")).toBeInTheDocument();
      expect(screen.getByText(/Two identical charges/i)).toBeInTheDocument();
    });

    // Select option B and submit
    const optionBButton = screen.getByText('B').closest('button');
    fireEvent.click(optionBButton!);

    const submitBtn = screen.getByText('Submit Answer').closest('button');
    expect(submitBtn).toBeInTheDocument();
    fireEvent.click(submitBtn!);

    await waitFor(() => {
      expect(screen.getByText('Complete Practice Session')).toBeInTheDocument();
    });

    // Click Complete Practice Session
    const completeBtn = screen.getByText('Complete Practice Session').closest('button');
    expect(completeBtn).toBeInTheDocument();
    fireEvent.click(completeBtn!);

    // Verify session summary screen
    await waitFor(() => {
      expect(screen.getByText('Practice Session Complete!')).toBeInTheDocument();
      expect(screen.getByText('100%')).toBeInTheDocument();
      expect(screen.getByText(/Excellent mastery!/i)).toBeInTheDocument();
    });
  });
});
