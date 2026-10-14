import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Calendar,
  Check,
  CheckCircle2,
  Clock,
  Loader2,
  AlertCircle,
  Save,
  ArrowRight,
  ArrowLeft,
  GraduationCap,
} from 'lucide-react';
import { CurriculumBoard, GradeStageItem, SubjectItem } from '../../types/auth';
import { getCurricula } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

interface OnboardingWizardProps {
  onCompleted?: () => void;
  onCancel?: () => void;
}

export const OnboardingWizard: React.FC<OnboardingWizardProps> = ({
  onCompleted,
  onCancel,
}) => {
  const { profile, saveOnboarding, authError } = useAuth();

  const [curricula, setCurricula] = useState<CurriculumBoard[]>([]);
  const [isLoadingCurricula, setIsLoadingCurricula] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [currentStep, setCurrentStep] = useState<number>(1);
  const [selectedBoardId, setSelectedBoardId] = useState<string>('');
  const [selectedGradeId, setSelectedGradeId] = useState<string>('');
  const [targetExamYear, setTargetExamYear] = useState<number>(2027);
  const [selectedSubjectIds, setSelectedSubjectIds] = useState<string[]>([]);
  const [dailyGoalMinutes, setDailyGoalMinutes] = useState<number>(120);
  const [preferredLanguage, setPreferredLanguage] = useState<string>('en');

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Fetch curricula taxonomy and pre-fill draft profile data
  useEffect(() => {
    let isMounted = true;
    const fetchTaxonomy = async () => {
      try {
        setIsLoadingCurricula(true);
        const data = await getCurricula();
        if (!isMounted) return;
        setCurricula(data);

        // Pre-fill from existing profile if available
        if (profile) {
          if (profile.target_curriculum_id) {
            setSelectedBoardId(profile.target_curriculum_id);
          } else if (data.length > 0) {
            setSelectedBoardId(data[0].id);
          }

          if (profile.grade_stage_id) {
            setSelectedGradeId(profile.grade_stage_id);
          }
          if (profile.target_exam_year) {
            setTargetExamYear(profile.target_exam_year);
          }
          if (profile.daily_study_goal_minutes) {
            setDailyGoalMinutes(profile.daily_study_goal_minutes);
          }
          if (profile.selected_subjects && profile.selected_subjects.length > 0) {
            setSelectedSubjectIds(profile.selected_subjects.map((s) => s.id));
          }
        } else if (data.length > 0) {
          setSelectedBoardId(data[0].id);
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        setLoadError(err instanceof Error ? err.message : 'Failed to load curricula taxonomy');
      } finally {
        if (isMounted) setIsLoadingCurricula(false);
      }
    };

    fetchTaxonomy();
    return () => {
      isMounted = false;
    };
  }, [profile]);

  // Derived selected board and grade objects
  const activeBoard = curricula.find((b) => b.id === selectedBoardId);
  const availableGrades: GradeStageItem[] = activeBoard ? activeBoard.grades : [];

  // Auto-select first grade if current selectedGradeId not in available grades
  useEffect(() => {
    if (availableGrades.length > 0) {
      const exists = availableGrades.some((g) => g.id === selectedGradeId);
      if (!exists) {
        setSelectedGradeId(availableGrades[0].id);
      }
    }
  }, [availableGrades, selectedGradeId]);

  const activeGrade = availableGrades.find((g) => g.id === selectedGradeId);
  const availableSubjects: SubjectItem[] = activeGrade ? activeGrade.subjects : [];

  // Toggle subject selection
  const handleToggleSubject = (subjectId: string) => {
    setSelectedSubjectIds((prev) => {
      if (prev.includes(subjectId)) {
        return prev.filter((id) => id !== subjectId);
      } else {
        return [...prev, subjectId];
      }
    });
  };

  // Submit onboarding (draft or complete)
  const handleSave = async (isFinal: boolean) => {
    setFormError(null);

    if (!selectedBoardId) {
      setFormError('Please select a curriculum.');
      setCurrentStep(1);
      return;
    }

    if (!selectedGradeId) {
      setFormError('Please select an academic grade stage.');
      setCurrentStep(2);
      return;
    }

    if (isFinal && selectedSubjectIds.length === 0) {
      setFormError('Please choose at least one academic subject to study.');
      setCurrentStep(3);
      return;
    }

    setIsSubmitting(true);
    try {
      await saveOnboarding({
        target_curriculum_id: selectedBoardId,
        grade_stage_id: selectedGradeId,
        target_exam_year: targetExamYear,
        selected_subject_ids: selectedSubjectIds.length > 0 ? selectedSubjectIds : (availableSubjects[0] ? [availableSubjects[0].id] : []),
        daily_study_goal_minutes: dailyGoalMinutes,
        preferred_language: preferredLanguage,
        complete: isFinal,
      });

      if (onCompleted) {
        onCompleted();
      }
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Error saving academic profile');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoadingCurricula) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-sm">
        <Loader2 className="w-8 h-8 text-brand-600 animate-spin mx-auto mb-3" />
        <p className="text-sm font-semibold text-slate-700">Loading curriculum taxonomies...</p>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="bg-white rounded-2xl border border-rose-200 p-8 text-center shadow-sm">
        <AlertCircle className="w-8 h-8 text-rose-600 mx-auto mb-3" />
        <h3 className="text-base font-bold text-rose-950">Unable to load curricula</h3>
        <p className="text-xs text-rose-700 mt-1 mb-4">{loadError}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 text-xs font-semibold rounded-lg bg-rose-600 text-white hover:bg-rose-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden">
      {/* Wizard Header & Stepper */}
      <div className="bg-gradient-to-r from-slate-900 via-brand-950 to-slate-900 text-white p-6 sm:p-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <GraduationCap className="w-6 h-6 text-brand-400" />
            <h2 className="text-lg sm:text-xl font-bold tracking-tight">Academic Onboarding Setup</h2>
          </div>
          {onCancel && (
            <button
              onClick={onCancel}
              className="text-xs font-semibold text-slate-400 hover:text-white transition-colors"
            >
              Exit to Dashboard
            </button>
          )}
        </div>
        <p className="text-xs text-slate-300 max-w-2xl">
          Personalize your curriculum, target examination, and subjects. You can save your draft at any point and resume later.
        </p>

        {/* 4 Step Progress Indicators */}
        <div className="mt-6 grid grid-cols-4 gap-2">
          {[
            { step: 1, label: 'Board' },
            { step: 2, label: 'Grade & Year' },
            { step: 3, label: 'Subjects' },
            { step: 4, label: 'Study Goals' },
          ].map((item) => (
            <button
              key={item.step}
              type="button"
              onClick={() => setCurrentStep(item.step)}
              className={`text-left p-2 rounded-lg border transition-all ${
                currentStep === item.step
                  ? 'bg-brand-500/20 border-brand-400 text-white'
                  : currentStep > item.step
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : 'bg-white/5 border-white/10 text-slate-400'
              }`}
            >
              <div className="flex items-center space-x-1.5 text-[11px] font-bold">
                {currentStep > item.step ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <span>{item.step}.</span>
                )}
                <span>{item.label}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Form Error Banner */}
      {(formError || authError) && (
        <div className="m-6 mb-0 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 text-rose-600 mt-0.5 flex-shrink-0" />
          <span>{formError || authError}</span>
        </div>
      )}

      {/* Step Body */}
      <div className="p-6 sm:p-8">
        {/* Step 1: Curriculum Board Selection */}
        {currentStep === 1 && (
          <div>
            <h3 className="text-base font-bold text-slate-900 mb-1">Step 1: Select Your Curriculum Board</h3>
            <p className="text-xs text-slate-500 mb-6">Choose your primary educational system or national entrance examination focus:</p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {curricula.map((board) => {
                const isSelected = selectedBoardId === board.id;
                return (
                  <div
                    key={board.id}
                    onClick={() => setSelectedBoardId(board.id)}
                    className={`cursor-pointer p-5 rounded-xl border-2 transition-all ${
                      isSelected
                        ? 'border-brand-600 bg-brand-50/50 shadow-md ring-1 ring-brand-600'
                        : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-brand-700 bg-brand-100/60 px-2 py-0.5 rounded">
                        {board.code}
                      </span>
                      {isSelected && <Check className="w-4 h-4 text-brand-600 font-bold" />}
                    </div>
                    <h4 className="text-sm font-bold text-slate-900 mt-2">{board.name}</h4>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">{board.description}</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Step 2: Grade Level & Target Exam Year */}
        {currentStep === 2 && (
          <div>
            <h3 className="text-base font-bold text-slate-900 mb-1">Step 2: Select Your Academic Stage & Exam Year</h3>
            <p className="text-xs text-slate-500 mb-6">
              Curriculum: <span className="font-semibold text-slate-800">{activeBoard?.name}</span>
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Grade Stage Options */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-2">
                  Academic Grade Stage
                </label>
                <div className="space-y-3">
                  {availableGrades.map((grade) => {
                    const isSelected = selectedGradeId === grade.id;
                    return (
                      <div
                        key={grade.id}
                        onClick={() => setSelectedGradeId(grade.id)}
                        className={`cursor-pointer p-4 rounded-xl border-2 transition-all flex items-center justify-between ${
                          isSelected
                            ? 'border-brand-600 bg-brand-50/50 shadow-sm'
                            : 'border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <div>
                          <p className="text-sm font-bold text-slate-900">{grade.name}</p>
                          <p className="text-xs text-slate-500 mt-0.5">{grade.subjects.length} subjects supported</p>
                        </div>
                        {isSelected && <Check className="w-5 h-5 text-brand-600" />}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Target Exam Year */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-2" htmlFor="exam-year">
                  Target Examination Year
                </label>
                <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-3">
                  <div className="flex items-center space-x-2 text-slate-600 text-xs">
                    <Calendar className="w-4 h-4 text-brand-600" />
                    <span>Select the year you anticipate appearing for your board or entrance exam:</span>
                  </div>
                  <select
                    id="exam-year"
                    value={targetExamYear}
                    onChange={(e) => setTargetExamYear(Number(e.target.value))}
                    className="w-full p-2.5 rounded-lg border border-slate-300 bg-white text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    {[2026, 2027, 2028, 2029].map((year) => (
                      <option key={year} value={year}>
                        {year} Academic Session
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Choose Academic Subjects */}
        {currentStep === 3 && (
          <div>
            <h3 className="text-base font-bold text-slate-900 mb-1">Step 3: Choose Your Academic Subjects</h3>
            <p className="text-xs text-slate-500 mb-6">
              Select the disciplines you are studying for {activeGrade?.name} ({activeBoard?.code}):
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              {availableSubjects.map((sub) => {
                const isSelected = selectedSubjectIds.includes(sub.id);
                return (
                  <div
                    key={sub.id}
                    onClick={() => handleToggleSubject(sub.id)}
                    className={`cursor-pointer p-4 rounded-xl border-2 transition-all flex items-center justify-between ${
                      isSelected
                        ? 'border-brand-600 bg-brand-50 shadow-sm'
                        : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <div
                        className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                          isSelected ? 'bg-brand-600 text-white' : 'bg-slate-200 text-slate-600'
                        }`}
                      >
                        <BookOpen className="w-4 h-4" />
                      </div>
                      <span className="text-sm font-bold text-slate-900">{sub.name}</span>
                    </div>
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => {}} // Handled by container onClick
                      className="w-4 h-4 rounded text-brand-600 focus:ring-brand-500"
                    />
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Step 4: Study Habits & Language */}
        {currentStep === 4 && (
          <div>
            <h3 className="text-base font-bold text-slate-900 mb-1">Step 4: Set Your Daily Study Commitment</h3>
            <p className="text-xs text-slate-500 mb-6">
              Establish a realistic daily practice target. You can adjust this anytime in your student dashboard:
            </p>

            <div className="max-w-xl space-y-6">
              {/* Daily study goal slider */}
              <div className="p-5 rounded-xl border border-slate-200 bg-slate-50 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-5 h-5 text-brand-600" />
                    <span className="text-sm font-bold text-slate-900">Daily Study Target</span>
                  </div>
                  <span className="text-sm font-extrabold text-brand-700 bg-brand-100 px-3 py-1 rounded-full">
                    {dailyGoalMinutes} Minutes ({Math.floor(dailyGoalMinutes / 60)}h {dailyGoalMinutes % 60}m)
                  </span>
                </div>

                <input
                  type="range"
                  min="30"
                  max="360"
                  step="15"
                  value={dailyGoalMinutes}
                  onChange={(e) => setDailyGoalMinutes(Number(e.target.value))}
                  className="w-full h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer accent-brand-600"
                />

                <div className="flex justify-between text-[11px] text-slate-400 font-medium">
                  <span>30 Min</span>
                  <span>1 Hour</span>
                  <span>2 Hours</span>
                  <span>4 Hours</span>
                  <span>6 Hours</span>
                </div>
              </div>

              {/* Preferred Language */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-2" htmlFor="language-select">
                  Instruction Language
                </label>
                <select
                  id="language-select"
                  value={preferredLanguage}
                  onChange={(e) => setPreferredLanguage(e.target.value)}
                  className="w-full p-2.5 rounded-lg border border-slate-300 bg-white text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="en">English (Scientific and Mathematical Unicode)</option>
                  <option value="hi">Hindi (Coming in future multilingual release)</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Wizard Controls */}
        <div className="mt-8 pt-6 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-3 w-full sm:w-auto">
            {currentStep > 1 && (
              <button
                type="button"
                onClick={() => setCurrentStep((s) => s - 1)}
                className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
            )}

            {currentStep < 4 ? (
              <button
                type="button"
                onClick={() => setCurrentStep((s) => s + 1)}
                className="inline-flex items-center space-x-1.5 px-5 py-2 text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 rounded-xl transition-all shadow-sm"
              >
                <span>Continue</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : null}
          </div>

          <div className="flex items-center space-x-3 w-full sm:w-auto justify-end">
            {/* Save as Draft option */}
            <button
              type="button"
              disabled={isSubmitting}
              onClick={() => handleSave(false)}
              className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-xl transition-colors disabled:opacity-50"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save Progress as Draft</span>
            </button>

            {/* Complete Setup */}
            <button
              type="button"
              disabled={isSubmitting}
              onClick={() => handleSave(true)}
              className="inline-flex items-center space-x-1.5 px-5 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl transition-all shadow-md disabled:opacity-50"
            >
              {isSubmitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <CheckCircle2 className="w-4 h-4" />
              )}
              <span>Complete Academic Setup</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
