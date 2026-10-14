import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import App from '../App';

describe('Frontend Authentication and Session Management', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    sessionStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('opens and closes the authentication modal', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'healthy', version: '0.1.0', database: 'connected' }),
    }));

    await act(async () => {
      render(<App />);
    });

    // Click "Sign In" button in header
    const signInBtn = screen.getByRole('button', { name: /^sign in$/i });
    await act(async () => {
      fireEvent.click(signInBtn);
    });

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Welcome back to Project Campus')).toBeInTheDocument();

    // Close button
    const closeBtn = screen.getByRole('button', { name: /close modal/i });
    await act(async () => {
      fireEvent.click(closeBtn);
    });

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('validates registration form inputs on client side', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'healthy', version: '0.1.0', database: 'connected' }),
    }));

    await act(async () => {
      render(<App />);
    });

    const createAccountBtn = screen.getByRole('button', { name: /^create account$/i });
    await act(async () => {
      fireEvent.click(createAccountBtn);
    });

    // Enter name, email and short password
    const nameInput = screen.getByLabelText(/full name/i);
    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/^password$/i);

    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Test Student' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'short' } });
    });

    const submitBtn = screen.getByTestId('auth-submit-button');
    await act(async () => {
      fireEvent.click(submitBtn);
    });

    expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument();
  });

  it('displays error message when login fails with invalid credentials', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation((url: string) => {
        if (url.includes('/api/v1/auth/login')) {
          return Promise.resolve({
            ok: false,
            status: 401,
            json: async () => ({ detail: 'Invalid email or password' }),
          });
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({ status: 'healthy', version: '0.1.0', database: 'connected' }),
        });
      })
    );

    await act(async () => {
      render(<App />);
    });

    const signInBtn = screen.getByRole('button', { name: /^sign in$/i });
    await act(async () => {
      fireEvent.click(signInBtn);
    });

    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/^password$/i);

    await act(async () => {
      fireEvent.change(emailInput, { target: { value: 'wrong@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'WrongPass123' } });
    });

    const submitBtn = screen.getByTestId('auth-submit-button');
    await act(async () => {
      fireEvent.click(submitBtn);
    });

    await waitFor(() => {
      expect(screen.getByText('Invalid email or password')).toBeInTheDocument();
    });
  });

  it('renders student workspace when login succeeds and logs out cleanly', async () => {
    const mockUser = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      email: 'student@example.com',
      full_name: 'Aditya Sen',
      is_active: true,
      is_verified: true,
      roles: ['STUDENT'],
      onboarding_completed: true,
      created_at: '2026-10-14T10:00:00Z',
    };

    const mockProfile = {
      id: '123e4567-e89b-12d3-a456-426614174001',
      user_id: mockUser.id,
      full_name: mockUser.full_name,
      email: mockUser.email,
      target_curriculum_name: 'Central Board of Secondary Education',
      target_curriculum_code: 'CBSE',
      grade_stage_name: 'Class 12 (+2)',
      target_exam_year: 2027,
      daily_study_goal_minutes: 120,
      preferred_language: 'en',
      onboarding_completed: true,
      selected_subjects: [{ id: 'sub-1', code: 'PHYSICS', name: 'Physics', display_order: 1 }],
      created_at: '2026-10-14T10:00:00Z',
      updated_at: '2026-10-14T10:00:00Z',
    };

    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation((url: string) => {
        if (url.includes('/api/v1/auth/login')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              access_token: 'fake-jwt-token-xyz',
              token_type: 'bearer',
              expires_in_minutes: 60,
              user: mockUser,
            }),
          });
        }
        if (url.includes('/api/v1/student/profile')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => mockProfile,
          });
        }
        if (url.includes('/api/v1/auth/logout')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ status: 'success', message: 'Logged out' }),
          });
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({ status: 'healthy', version: '0.1.0', database: 'connected' }),
        });
      })
    );

    await act(async () => {
      render(<App />);
    });

    // 1. Log in
    const signInBtn = screen.getByRole('button', { name: /^sign in$/i });
    await act(async () => {
      fireEvent.click(signInBtn);
    });

    await act(async () => {
      fireEvent.change(screen.getByLabelText(/email address/i), {
        target: { value: 'student@example.com' },
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), {
        target: { value: 'ValidPassword123' },
      });
    });

    await act(async () => {
      fireEvent.click(screen.getByTestId('auth-submit-button'));
    });

    // 2. Verify dashboard renders
    await waitFor(() => {
      expect(screen.getByText(/Welcome, Aditya Sen/i)).toBeInTheDocument();
      expect(screen.getByText('Student Academic Workspace')).toBeInTheDocument();
      expect(screen.getByText('Central Board of Secondary Education')).toBeInTheDocument();
    });

    // 3. Log out
    const signOutBtn = screen.getByRole('button', { name: /sign out/i });
    await act(async () => {
      fireEvent.click(signOutBtn);
    });

    // 4. Verify returned to guest view
    await waitFor(() => {
      expect(screen.queryByText(/Welcome, Aditya Sen/i)).not.toBeInTheDocument();
      expect(screen.getByText(/Create Student Account/i)).toBeInTheDocument();
    });
  });
});
