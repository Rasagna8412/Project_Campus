import React, { useState } from 'react';
import {
  BookOpen,
  Clock,
  Compass,
  GraduationCap,
  Layers,
  Trash2,
  AlertTriangle,
  Loader2,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { updateStudentProfile } from '../../services/api';

interface StudentDashboardProps {
  onOpenOnboarding: () => void;
  onOpenLessons: () => void;
}

export const StudentDashboard: React.FC<StudentDashboardProps> = ({
  onOpenOnboarding,
  onOpenLessons,
}) => {
  const { user, profile, refreshProfile, deleteAccount } = useAuth();

  const [isEditingGoal, setIsEditingGoal] = useState<boolean>(false);
  const [newGoalMinutes, setNewGoalMinutes] = useState<number>(
    profile?.daily_study_goal_minutes || 120
  );
  const [isSavingGoal, setIsSavingGoal] = useState<boolean>(false);
  const [isDeletingAccount, setIsDeletingAccount] = useState<boolean>(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<boolean>(false);

  const handleUpdateGoal = async () => {
    setIsSavingGoal(true);
    try {
      await updateStudentProfile({ daily_study_goal_minutes: newGoalMinutes });
      await refreshProfile();
      setIsEditingGoal(false);
    } catch {
      // Error handled
    } finally {
      setIsSavingGoal(false);
    }
  };

  const handleDeleteAccount = async () => {
    setIsDeletingAccount(true);
    try {
      await deleteAccount();
    } catch {
      // Handled
    } finally {
      setIsDeletingAccount(false);
    }
  };

  if (!user) return null;

  const isOnboardingIncomplete = !profile?.onboarding_completed;

  return (
    <div className="space-y-6">
      {/* Student Welcome Banner */}
      <div className="bg-gradient-to-r from-brand-900 via-brand-800 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-lg border border-brand-700/50">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-semibold text-brand-300 uppercase tracking-wider mb-2">
              <GraduationCap className="w-4 h-4 text-brand-400" />
              <span>Student Academic Workspace</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Welcome, {user.full_name}
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1">
              Account: <span className="font-mono text-brand-200">{user.email}</span> • Status:{' '}
              <span className="text-emerald-400 font-semibold">Active Learner</span>
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={onOpenLessons}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold bg-brand-500 hover:bg-brand-400 text-white shadow-md transition-all"
            >
              <BookOpen className="w-4 h-4" />
              <span>Browse Curriculum Lessons</span>
            </button>

            <button
              onClick={onOpenOnboarding}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold bg-white text-slate-900 hover:bg-slate-100 shadow-md transition-all"
            >
              <Compass className="w-4 h-4 text-brand-600" />
              <span>{isOnboardingIncomplete ? 'Resume Setup' : 'Edit Curriculum Setup'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Incomplete Onboarding Alert Banner */}
      {isOnboardingIncomplete && (
        <div
          className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-xs text-amber-900 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4"
          role="alert"
        >
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-bold text-sm text-amber-950">Academic Onboarding Incomplete</h3>
              <p className="mt-0.5 text-amber-800 leading-relaxed">
                Your target curriculum and subject choices have been saved as draft. Complete your academic setup to finalize your personalized curriculum view.
              </p>
            </div>
          </div>
          <button
            onClick={onOpenOnboarding}
            className="px-4 py-2 rounded-lg text-xs font-bold bg-amber-600 text-white hover:bg-amber-700 shadow-sm transition-colors whitespace-nowrap self-start sm:self-auto"
          >
            Resume Onboarding Now
          </button>
        </div>
      )}

      {/* Profile Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1: Target Board & Stage */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-brand-700 mb-3">
            <Layers className="w-4 h-4 text-brand-600" />
            <span>Target Curriculum & Stage</span>
          </div>

          <div className="space-y-3">
            <div>
              <span className="text-xs text-slate-400">Board / Examination</span>
              <p className="text-sm font-bold text-slate-900">
                {profile?.target_curriculum_name || (
                  <span className="text-slate-400 italic">Not yet selected</span>
                )}
              </p>
            </div>

            <div>
              <span className="text-xs text-slate-400">Academic Grade Stage</span>
              <p className="text-sm font-bold text-slate-900">
                {profile?.grade_stage_name || (
                  <span className="text-slate-400 italic">Not yet selected</span>
                )}
              </p>
            </div>

            <div>
              <span className="text-xs text-slate-400">Target Exam Year</span>
              <p className="text-sm font-bold text-slate-900">
                {profile?.target_exam_year ? `${profile.target_exam_year} Session` : 'Not set'}
              </p>
            </div>
          </div>
        </div>

        {/* Card 2: Enrolled Subjects */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-brand-700 mb-3">
            <BookOpen className="w-4 h-4 text-brand-600" />
            <span>Enrolled Subjects ({profile?.selected_subjects?.length || 0})</span>
          </div>

          {profile?.selected_subjects && profile.selected_subjects.length > 0 ? (
            <div className="flex flex-wrap gap-2 pt-1">
              {profile.selected_subjects.map((sub) => (
                <span
                  key={sub.id}
                  className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-brand-50 text-brand-800 border border-brand-200"
                >
                  <BookOpen className="w-3.5 h-3.5 text-brand-600" />
                  <span>{sub.name}</span>
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">
              No subjects enrolled yet. Complete onboarding to select your subjects.
            </p>
          )}
        </div>

        {/* Card 3: Daily Study Goal & Commitment */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-brand-700">
              <Clock className="w-4 h-4 text-brand-600" />
              <span>Daily Study Target</span>
            </div>
            {!isEditingGoal && (
              <button
                onClick={() => setIsEditingGoal(true)}
                className="text-xs font-semibold text-brand-600 hover:text-brand-800"
              >
                Adjust
              </button>
            )}
          </div>

          {!isEditingGoal ? (
            <div>
              <div className="text-2xl font-extrabold text-slate-900">
                {profile?.daily_study_goal_minutes || 120} Min
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Equivalent to {Math.floor((profile?.daily_study_goal_minutes || 120) / 60)} hours per day of focused deliberate practice.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-bold text-slate-800">
                <span>{newGoalMinutes} Minutes</span>
                <span>({Math.floor(newGoalMinutes / 60)}h {newGoalMinutes % 60}m)</span>
              </div>
              <input
                type="range"
                min="30"
                max="360"
                step="15"
                value={newGoalMinutes}
                onChange={(e) => setNewGoalMinutes(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-brand-600"
              />
              <div className="flex items-center space-x-2 pt-1">
                <button
                  onClick={handleUpdateGoal}
                  disabled={isSavingGoal}
                  className="px-3 py-1 rounded-lg text-xs font-bold bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50 flex items-center space-x-1"
                >
                  {isSavingGoal && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save</span>
                </button>
                <button
                  onClick={() => setIsEditingGoal(false)}
                  className="px-3 py-1 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Privacy and Account Rights Card (DPDP Act Compliance) */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Student Privacy & Account Rights</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              In accordance with India&apos;s Digital Personal Data Protection Act (DPDP Act 2023), you hold the right to complete erasure of your academic records.
            </p>
          </div>

          {!showDeleteConfirm ? (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-rose-700 hover:bg-rose-50 border border-rose-200 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5 text-rose-600" />
              <span>Delete Account</span>
            </button>
          ) : (
            <div className="flex items-center space-x-2">
              <span className="text-xs text-rose-700 font-semibold">Permanently delete?</span>
              <button
                onClick={handleDeleteAccount}
                disabled={isDeletingAccount}
                className="px-3 py-1.5 rounded-lg text-xs font-bold bg-rose-600 text-white hover:bg-rose-700 disabled:opacity-50 flex items-center space-x-1"
              >
                {isDeletingAccount && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Yes, Erase Everything</span>
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100 border border-slate-200"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
