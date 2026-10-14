import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import {
  User,
  StudentProfile,
  OnboardingPayload,
} from '../types/auth';
import {
  getCurrentUser,
  getStudentProfile,
  loginUser,
  logoutUser,
  registerStudent,
  submitStudentOnboarding,
  deleteStudentAccount,
  getAuthToken,
  removeAuthToken,
} from '../services/api';

interface AuthContextType {
  user: User | null;
  profile: StudentProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  authError: string | null;
  clearAuthError: () => void;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  saveOnboarding: (payload: OnboardingPayload) => Promise<StudentProfile>;
  deleteAccount: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [authError, setAuthError] = useState<string | null>(null);

  const clearAuthError = useCallback(() => {
    setAuthError(null);
  }, []);

  const refreshProfile = useCallback(async () => {
    try {
      const prof = await getStudentProfile();
      setProfile(prof);
    } catch (err) {
      // Profile fetch failed (e.g. unauthenticated)
    }
  }, []);

  // Check initial token and resolve session on mount
  useEffect(() => {
    const initAuth = async () => {
      const token = getAuthToken();
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
        const currentProfile = await getStudentProfile();
        setProfile(currentProfile);
      } catch (err) {
        // Expired or invalid token
        removeAuthToken();
        setUser(null);
        setProfile(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setAuthError(null);
    try {
      const res = await loginUser({ email, password });
      setUser(res.user);
      const prof = await getStudentProfile();
      setProfile(prof);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Login failed';
      setAuthError(msg);
      throw err;
    }
  };

  const register = async (email: string, password: string, fullName: string) => {
    setAuthError(null);
    try {
      const res = await registerStudent({ email, password, full_name: fullName });
      setUser(res.user);
      const prof = await getStudentProfile();
      setProfile(prof);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Registration failed';
      setAuthError(msg);
      throw err;
    }
  };

  const logout = async () => {
    try {
      await logoutUser();
    } catch {
      // Ignore network errors during logout
    } finally {
      setUser(null);
      setProfile(null);
      setAuthError(null);
    }
  };

  const saveOnboarding = async (payload: OnboardingPayload): Promise<StudentProfile> => {
    try {
      const updatedProfile = await submitStudentOnboarding(payload);
      setProfile(updatedProfile);
      if (user) {
        setUser({ ...user, onboarding_completed: updatedProfile.onboarding_completed });
      }
      return updatedProfile;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save onboarding selections';
      setAuthError(msg);
      throw err;
    }
  };

  const deleteAccount = async () => {
    try {
      await deleteStudentAccount();
    } finally {
      setUser(null);
      setProfile(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        isAuthenticated: !!user,
        isLoading,
        authError,
        clearAuthError,
        login,
        register,
        logout,
        refreshProfile,
        saveOnboarding,
        deleteAccount,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
