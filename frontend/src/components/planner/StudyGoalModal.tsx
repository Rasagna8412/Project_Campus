import React, { useState } from 'react';
import { X, Clock, Calendar, Check, Sliders } from 'lucide-react';
import { StudyGoal, StudyGoalPayload } from '../../types/planner';

interface StudyGoalModalProps {
  goal: StudyGoal | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (payload: StudyGoalPayload) => Promise<void>;
}

const ALL_DAYS = [
  { key: 'MON', label: 'Mon' },
  { key: 'TUE', label: 'Tue' },
  { key: 'WED', label: 'Wed' },
  { key: 'THU', label: 'Thu' },
  { key: 'FRI', label: 'Fri' },
  { key: 'SAT', label: 'Sat' },
  { key: 'SUN', label: 'Sun' },
];

export const StudyGoalModal: React.FC<StudyGoalModalProps> = ({
  goal,
  isOpen,
  onClose,
  onSave,
}) => {
  const [title, setTitle] = useState<string>(goal?.title || 'Academic Preparation');
  const [dailyMinutes, setDailyMinutes] = useState<number>(
    goal?.daily_study_minutes || 120
  );
  const [targetDate, setTargetDate] = useState<string>(
    goal?.target_date || ''
  );
  const [selectedDays, setSelectedDays] = useState<string[]>(
    goal?.preferred_days || ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
  );
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  React.useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const toggleDay = (day: string) => {
    if (selectedDays.includes(day)) {
      if (selectedDays.length <= 1) {
        setError('At least one preferred study day must be selected.');
        return;
      }
      setSelectedDays(selectedDays.filter((d) => d !== day));
    } else {
      setSelectedDays([...selectedDays, day]);
    }
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);

    try {
      await onSave({
        title,
        daily_study_minutes: dailyMinutes,
        target_date: targetDate || null,
        preferred_days: selectedDays,
      });
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to update study goal.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const todayStr = new Date().toISOString().split('T')[0];

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="goal-modal-title"
    >
      <div
        className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-brand-50 text-brand-600">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h3 id="goal-modal-title" className="font-bold text-base text-slate-900">
                Adjust Study Target & Schedule
              </h3>
              <p className="text-xs text-slate-500">
                Personalize your daily workload and active preparation calendar
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="my-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5 pt-4">
          {/* Goal Title */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
              Study Goal Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. CBSE Board Exam Prep"
              maxLength={150}
              required
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          {/* Daily Study Target Slider */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center space-x-1.5">
                <Clock className="w-4 h-4 text-brand-600" />
                <span>Daily Study Time</span>
              </label>
              <span className="text-sm font-black text-brand-700">
                {dailyMinutes} minutes ({Math.floor(dailyMinutes / 60)}h{' '}
                {dailyMinutes % 60}m)
              </span>
            </div>
            <input
              type="range"
              min={15}
              max={300}
              step={15}
              value={dailyMinutes}
              onChange={(e) => setDailyMinutes(Number(e.target.value))}
              className="w-full accent-brand-600 cursor-pointer"
            />
            <div className="flex justify-between text-[11px] text-slate-400 mt-1">
              <span>15 min</span>
              <span>1 hr</span>
              <span>2 hrs</span>
              <span>3 hrs</span>
              <span>5 hrs</span>
            </div>
          </div>

          {/* Target Exam Date */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1 flex items-center space-x-1.5">
              <Calendar className="w-4 h-4 text-brand-600" />
              <span>Target Exam Date (Optional)</span>
            </label>
            <input
              type="date"
              min={todayStr}
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          {/* Preferred Study Days */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
              Active Study Days
            </label>
            <div className="grid grid-cols-7 gap-1.5">
              {ALL_DAYS.map((d) => {
                const isSelected = selectedDays.includes(d.key);
                return (
                  <button
                    key={d.key}
                    type="button"
                    onClick={() => toggleDay(d.key)}
                    className={`py-2 rounded-xl text-xs font-bold transition-all border ${
                      isSelected
                        ? 'bg-brand-600 text-white border-brand-600 shadow-sm'
                        : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    {d.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isSaving}
              className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="inline-flex items-center space-x-1.5 px-5 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white shadow transition-all disabled:opacity-50"
            >
              <Check className="w-4 h-4" />
              <span>{isSaving ? 'Saving...' : 'Save Study Target'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
