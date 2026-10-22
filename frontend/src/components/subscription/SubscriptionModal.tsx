import React, { useState } from 'react';
import {
  Check,
  Crown,
  Loader2,
  ShieldCheck,
  Sparkles,
  X,
  Zap,
} from 'lucide-react';
import { SubscriptionEntitlementResponse } from '../../types/ai';
import { upgradeSubscriptionTier } from '../../services/api';

interface SubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  entitlements: SubscriptionEntitlementResponse | null;
  onEntitlementsUpdated: (ent: SubscriptionEntitlementResponse) => void;
}

export const SubscriptionModal: React.FC<SubscriptionModalProps> = ({
  isOpen,
  onClose,
  entitlements,
  onEntitlementsUpdated,
}) => {
  const [isUpdating, setIsUpdating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const currentTier = entitlements?.tier || 'FREE';
  const isPro = currentTier === 'PRO';

  const handleToggleTier = async (targetTier: 'FREE' | 'PRO') => {
    setIsUpdating(true);
    setError(null);
    try {
      const updated = await upgradeSubscriptionTier(targetTier);
      onEntitlementsUpdated(updated);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to update subscription tier');
      }
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="subscription-modal-title"
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-3xl w-full p-6 sm:p-8 relative overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          aria-label="Close dialog"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="text-center max-w-xl mx-auto mb-8">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-200 mb-3">
            <Crown className="w-3.5 h-3.5 text-amber-600" />
            <span>Campus Membership & Entitlements</span>
          </div>
          <h2
            id="subscription-modal-title"
            className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight"
          >
            Choose the Right Plan for Your Academic Journey
          </h2>
          <p className="mt-2 text-xs sm:text-sm text-slate-600">
            Transparent student pricing engineered for serious high school learners and undergraduate engineering students.
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs text-center font-medium">
            {error}
          </div>
        )}

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Free Tier */}
          <div
            className={`rounded-2xl p-6 border transition-all ${
              !isPro
                ? 'border-brand-500 bg-brand-50/20 ring-2 ring-brand-500/20 shadow-md'
                : 'border-slate-200 bg-white hover:border-slate-300'
            }`}
          >
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-bold text-slate-900 text-lg">Free Foundation</h3>
                <p className="text-xs text-slate-500 mt-0.5">Essential tools for independent study</p>
              </div>
              {!isPro && (
                <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-brand-100 text-brand-800 border border-brand-200">
                  Current Tier
                </span>
              )}
            </div>

            <div className="mt-4 mb-6">
              <span className="text-3xl font-black text-slate-900">₹0</span>
              <span className="text-xs font-semibold text-slate-500"> / forever</span>
            </div>

            <ul className="space-y-3 text-xs text-slate-700 mb-6">
              <li className="flex items-center space-x-2.5">
                <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span><strong>20 AI Tutor queries</strong> per day</span>
              </li>
              <li className="flex items-center space-x-2.5">
                <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span>CBSE, JEE Main & NEET Core Curricula</span>
              </li>
              <li className="flex items-center space-x-2.5">
                <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span>Verified Step-by-Step Derivations</span>
              </li>
              <li className="flex items-center space-x-2.5">
                <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span>Spaced Repetition Active Recall</span>
              </li>
            </ul>

            {isPro ? (
              <button
                onClick={() => handleToggleTier('FREE')}
                disabled={isUpdating}
                className="w-full py-2.5 px-4 rounded-xl text-xs font-bold bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors disabled:opacity-50"
              >
                {isUpdating ? 'Updating...' : 'Downgrade to Free'}
              </button>
            ) : (
              <div className="py-2.5 text-center text-xs font-semibold text-slate-400 bg-slate-50 rounded-xl border border-slate-200">
                Active Plan
              </div>
            )}
          </div>

          {/* Pro Tier */}
          <div
            className={`rounded-2xl p-6 border relative transition-all ${
              isPro
                ? 'border-amber-500 bg-amber-50/20 ring-2 ring-amber-500/30 shadow-lg'
                : 'border-slate-200 bg-gradient-to-b from-white to-amber-50/10 hover:border-amber-300'
            }`}
          >
            <div className="absolute -top-3 right-6 bg-gradient-to-r from-amber-500 to-amber-600 text-white text-[10px] font-black uppercase tracking-wider px-3 py-0.5 rounded-full shadow-sm flex items-center space-x-1">
              <Sparkles className="w-3 h-3" />
              <span>Recommended</span>
            </div>

            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-bold text-slate-900 text-lg flex items-center space-x-1.5">
                  <span>Campus Pro</span>
                  <Crown className="w-4 h-4 text-amber-500" />
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">Complete AI tutoring & engineering access</p>
              </div>
              {isPro && (
                <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                  Active
                </span>
              )}
            </div>

            <div className="mt-4 mb-6">
              <span className="text-3xl font-black text-slate-900">₹499</span>
              <span className="text-xs font-semibold text-slate-500"> / month</span>
              <span className="ml-2 text-[11px] font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded">Save 33% yearly</span>
            </div>

            <ul className="space-y-3 text-xs text-slate-700 mb-6">
              <li className="flex items-center space-x-2.5">
                <Zap className="w-4 h-4 text-amber-500 flex-shrink-0" />
                <span><strong>Unlimited Campus AI Tutor Queries</strong></span>
              </li>
              <li className="flex items-center space-x-2.5">
                <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span><strong>Undergraduate Engineering Tracks</strong> (C, Python, DSA)</span>
              </li>
              <li className="flex items-center space-x-2.5">
                <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span><strong>Interactive Code Sandbox</strong> & Test Runner</span>
              </li>
              <li className="flex items-center space-x-2.5">
                <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span><strong>Automated AI Practice Quiz Generator</strong></span>
              </li>
              <li className="flex items-center space-x-2.5">
                <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span>Priority inference response latency</span>
              </li>
            </ul>

            <button
              onClick={() => handleToggleTier(isPro ? 'FREE' : 'PRO')}
              disabled={isUpdating}
              className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold transition-all shadow-md flex items-center justify-center space-x-2 ${
                isPro
                  ? 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  : 'bg-gradient-to-r from-amber-500 to-amber-600 text-white hover:from-amber-600 hover:to-amber-700'
              }`}
            >
              {isUpdating ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Updating Tier...</span>
                </>
              ) : isPro ? (
                <span>Manage Subscription (Active)</span>
              ) : (
                <>
                  <Crown className="w-3.5 h-3.5" />
                  <span>Activate Pro (Pilot Demo Access)</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Pilot Disclosure Note */}
        <div className="mt-8 pt-4 border-t border-slate-100 text-center">
          <p className="text-[11px] text-slate-500 flex items-center justify-center space-x-1.5">
            <ShieldCheck className="w-4 h-4 text-brand-600" />
            <span>Pilot Mode Active: Pro features can be enabled without charges during evaluation.</span>
          </p>
        </div>
      </div>
    </div>
  );
};
