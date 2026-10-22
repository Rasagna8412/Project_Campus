import React from 'react';
import { CheckCircle2, Sparkles, BookOpen, Brain, Calendar, BarChart3, ShieldAlert } from 'lucide-react';

export const MilestoneRoadmap: React.FC = () => {
  const modules = [
    {
      title: 'Scaffolding & Core Architecture',
      milestone: 'Milestone 1',
      status: 'completed',
      icon: CheckCircle2,
      desc: 'FastAPI service, React+TS shell, SQLAlchemy models, Alembic migrations, health monitoring.',
    },
    {
      title: 'Authentication & Academic Profiles',
      milestone: 'Milestone 2',
      status: 'completed',
      icon: CheckCircle2,
      desc: 'Argon2id hashing, JWT access/refresh lifecycle, RBAC, student target exam onboarding, DPDP compliance.',
    },
    {
      title: 'Curriculum & Structured Lessons',
      milestone: 'Milestone 3',
      status: 'completed',
      icon: BookOpen,
      desc: 'CBSE, JEE Main & NEET syllabus trees, KaTeX structured lesson viewer, ordered sections, publication review.',
    },
    {
      title: 'Question Bank & Evaluation Engine',
      milestone: 'Milestone 4',
      status: 'completed',
      icon: Sparkles,
      desc: 'MCQ, numerical with decimal tolerance, verified educator solutions, student errata reporting.',
    },
    {
      title: 'Analytics & Learning-Gap Diagnostics',
      milestone: 'Milestone 5',
      status: 'completed',
      icon: BarChart3,
      desc: 'Topic mastery calculation, weak concept identification, diagnostic heatmaps.',
    },
    {
      title: 'Transparent AI Concept Clarifier',
      milestone: 'Milestone 6',
      status: 'completed',
      icon: Brain,
      desc: 'Grounded RAG tutor, syllabus context injection, safety guardrails, prominent AI provenance.',
    },
    {
      title: 'Spaced Repetition & Study Planner',
      milestone: 'Milestone 7',
      status: 'completed',
      icon: Calendar,
      desc: 'SuperMemo-2 review scheduler, daily revision queue, target exam countdown timer.',
    },
    {
      title: 'Student Experience, UX Polish & Verification',
      milestone: 'Milestone 8',
      status: 'active',
      icon: CheckCircle2,
      desc: 'Local browser verification, UI navigation enhancements, full student journey test pass, staging deployment plan.',
    },
    {
      title: 'Staging Release & Supervised Pilot',
      milestone: 'Phase C / Pilot',
      status: 'planned',
      icon: Sparkles,
      desc: 'Automated off-site database backups, supervised cohort onboarding, telemetry, and pilot readiness review.',
    },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">Engineering Implementation Roadmap</h2>
          <p className="text-xs text-slate-600 mt-0.5">
            Phased development status conforming to change-control rules:
          </p>
        </div>
        <span className="flex items-center space-x-1 text-xs text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-200 font-medium">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
          <span>Strict Milestone Boundaries</span>
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {modules.map((mod, index) => {
          const Icon = mod.icon;
          const isCompleted = mod.status === 'completed';
          const isActive = mod.status === 'active';

          return (
            <div
              key={index}
              className={`p-4 rounded-lg border transition-all ${
                isActive
                  ? 'border-brand-500 bg-brand-50/50 shadow-sm ring-1 ring-brand-300'
                  : isCompleted
                  ? 'border-emerald-200 bg-emerald-50/30'
                  : 'border-slate-200 bg-slate-50/50 opacity-80'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span
                  className={`text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                    isActive
                      ? 'bg-brand-100 text-brand-800 border border-brand-200'
                      : isCompleted
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                      : 'bg-slate-200 text-slate-600'
                  }`}
                >
                  {isActive ? 'Current Release' : isCompleted ? 'Completed' : 'Planned'}
                </span>
                <span className="text-xs font-semibold text-slate-500">{mod.milestone}</span>
              </div>

              <div className="flex items-start space-x-2.5 mt-2">
                <Icon
                  className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
                    isActive ? 'text-brand-600' : isCompleted ? 'text-emerald-600' : 'text-slate-400'
                  }`}
                />
                <div>
                  <h3 className="text-xs font-bold text-slate-900">{mod.title}</h3>
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">{mod.desc}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
