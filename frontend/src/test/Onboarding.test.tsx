import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { OnboardingWizard } from '../components/onboarding/OnboardingWizard';
import { AuthProvider } from '../context/AuthContext';

describe('Frontend Onboarding Wizard', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    sessionStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  const mockCurricula = [
    {
      id: 'board-cbse-1',
      code: 'CBSE',
      name: 'Central Board of Secondary Education',
      country_code: 'IND',
      description: 'National Indian School Board',
      is_active: true,
      grades: [
        {
          id: 'grade-11',
          board_id: 'board-cbse-1',
          code: 'CLASS_11',
          name: 'Class 11 (+1)',
          display_order: 1,
          subjects: [
            { id: 'sub-phy', code: 'PHYSICS', name: 'Physics', display_order: 1 },
            { id: 'sub-chem', code: 'CHEMISTRY', name: 'Chemistry', display_order: 2 },
            { id: 'sub-math', code: 'MATHEMATICS', name: 'Mathematics', display_order: 3 },
          ],
        },
        {
          id: 'grade-12',
          board_id: 'board-cbse-1',
          code: 'CLASS_12',
          name: 'Class 12 (+2)',
          display_order: 2,
          subjects: [
            { id: 'sub-phy-12', code: 'PHYSICS', name: 'Physics', display_order: 1 },
            { id: 'sub-chem-12', code: 'CHEMISTRY', name: 'Chemistry', display_order: 2 },
          ],
        },
      ],
    },
    {
      id: 'board-jee-2',
      code: 'JEE_MAIN',
      name: 'JEE Main Entrance',
      country_code: 'IND',
      description: 'Engineering Entrance',
      is_active: true,
      grades: [],
    },
  ];

  it('renders step 1 with real curriculum choices from API', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation((url: string) => {
        if (url.includes('/api/v1/curricula/')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => mockCurricula,
          });
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({}),
        });
      })
    );

    await act(async () => {
      render(
        <AuthProvider>
          <OnboardingWizard />
        </AuthProvider>
      );
    });

    await waitFor(() => {
      expect(screen.getByText('Academic Onboarding Setup')).toBeInTheDocument();
      expect(screen.getByText('Central Board of Secondary Education')).toBeInTheDocument();
      expect(screen.getByText('JEE Main Entrance')).toBeInTheDocument();
    });
  });

  it('navigates through steps to select grade, subjects, and study goal', async () => {
    let savedPayload: unknown = null;

    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation((url: string, options?: RequestInit) => {
        if (url.includes('/api/v1/curricula/')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => mockCurricula,
          });
        }
        if (url.includes('/api/v1/student/onboarding') && options?.method === 'PUT') {
          savedPayload = JSON.parse(options.body as string);
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              id: 'prof-1',
              user_id: 'user-1',
              full_name: 'Test Student',
              email: 'student@example.com',
              target_curriculum_name: 'Central Board of Secondary Education',
              onboarding_completed: true,
              daily_study_goal_minutes: 150,
              selected_subjects: [],
              created_at: '2026-10-14T10:00:00Z',
              updated_at: '2026-10-14T10:00:00Z',
            }),
          });
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({}),
        });
      })
    );

    const onCompletedMock = vi.fn();

    await act(async () => {
      render(
        <AuthProvider>
          <OnboardingWizard onCompleted={onCompletedMock} />
        </AuthProvider>
      );
    });

    await waitFor(() => {
      expect(screen.getByText('Central Board of Secondary Education')).toBeInTheDocument();
    });

    // Step 1 -> Step 2
    const continueBtn = screen.getByRole('button', { name: /continue/i });
    await act(async () => {
      fireEvent.click(continueBtn);
    });

    // Step 2: Grade selection
    expect(screen.getByText(/Step 2: Select Your Academic Stage/i)).toBeInTheDocument();
    expect(screen.getByText('Class 11 (+1)')).toBeInTheDocument();

    // Step 2 -> Step 3
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /continue/i }));
    });

    // Step 3: Choose subjects
    expect(screen.getByText(/Step 3: Choose Your Academic Subjects/i)).toBeInTheDocument();
    expect(screen.getByText('Mathematics')).toBeInTheDocument();

    // Select Physics and Mathematics
    await act(async () => {
      fireEvent.click(screen.getByText('Physics'));
      fireEvent.click(screen.getByText('Mathematics'));
    });

    // Step 3 -> Step 4
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /continue/i }));
    });

    // Step 4: Study Goals
    expect(screen.getByText(/Step 4: Set Your Daily Study Commitment/i)).toBeInTheDocument();

    // Complete Onboarding
    const completeBtn = screen.getByRole('button', { name: /complete academic setup/i });
    await act(async () => {
      fireEvent.click(completeBtn);
    });

    await waitFor(() => {
      expect(onCompletedMock).toHaveBeenCalled();
      expect(savedPayload).not.toBeNull();
      const p = savedPayload as { complete: boolean; selected_subject_ids: string[] };
      expect(p.complete).toBe(true);
      expect(p.selected_subject_ids.length).toBeGreaterThanOrEqual(1);
    });
  });
});
