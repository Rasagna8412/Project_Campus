import React from 'react';
import { ShieldCheck, Heart, Terminal } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-auto border-t border-slate-200 bg-white py-8 text-xs text-slate-500">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>DPDP Act (India 2023) Compliant Architecture • Zero Synthetic Claims</span>
          </div>

          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <Terminal className="w-3.5 h-3.5 text-slate-400" />
              <span>FastAPI 0.115 + React 18</span>
            </span>
            <span>•</span>
            <span className="flex items-center space-x-1">
              <span>Pilot Feedback:</span>
              <a
                href="mailto:pilot@projectcampus.local"
                className="text-brand-600 hover:text-brand-700 underline font-medium"
              >
                pilot@projectcampus.local
              </a>
            </span>
            <span>•</span>
            <span className="flex items-center space-x-1">
              <span>Academic Edition</span>
              <Heart className="w-3.5 h-3.5 text-rose-500 inline fill-rose-500" />
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
