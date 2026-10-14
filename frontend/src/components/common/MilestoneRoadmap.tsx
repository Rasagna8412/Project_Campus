import React from 'react';
import { CheckCircle2, Clock, Sparkles, BookOpen, Brain, Calendar, BarChart3, ShieldAlert } from 'lucide-react';

export const MilestoneRoadmap: React.FC = () => {
  const modules = [
    {
      title: 'Scaffolding & Core Architecture',
      milestone: 'Milestone 1',
      status: 'active',
      icon: CheckCircle2,
      desc: 'FastAPI service, React+TS shell, SQLAlchemy models, Alembic migrations, health monitoring.',
    },
    {
      title: 'Authentication & Academic Profiles',
      milestone: 'Milestone 2',
      status: 'planned',
      icon: Clock,
      desc: 'Argon2id hashing, JWT access/refresh lifecycle, RBAC, student target exam onboarding.',
    },
    {
      title: 'Curriculum & Structured Lessons',
      milestone: 'Milestone 3',
      status: 'planned',
      icon: BookOpen,
      desc: 'CBSE & JEE Main syllabus trees, KaTeX reading modules, educator CMS with markdown preview.',
    },
    {
      title: 'Question Bank & Evaluation Engine',
      milestone: 'Milestone 4',
      status: 'planned',
      icon: Sparkles,
      desc: 'MCQ, numerical with decimal tolerance, verified educator solutions, student errata reporting.',
    },
    {
      title: 'Analytics & Learning-Gap Diagnostics',
      milestone: 'Milestone 5',
      status: 'planned',
      icon: BarChart3,
      desc: 'Topic mastery calculation, weak concept identification, diagnostic heatmaps.',
    },
    {
      title: 'Transparent AI Concept Clarifier',
      milestone: 'Milestone 6',
      status: 'planned',
      icon: Brain,
      desc: 'Grounded RAG tutor, syllabus context injection, safety guardrails, prominent AI provenance.',
    },
    {
      title: 'Spaced Repetition & Study Planner',
      milestone: 'Milestone 7',
      status: 'planned',
      icon: Calendar,
      desc: 'SuperMemo-2 review scheduler, daily revision queue, target exam countdown timer.',
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
          <span>No Premature or Fake Mocks</span>
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {modules.map((mod, index) => {
          const Icon = mod.icon;
          const isActive = mod.status === 'active';

          return (
            <div
              key={index}
              className={`p-4 rounded-lg border transition-all ${
                isActive
                  ? 'border-brand-300 bg-brand-50/50 shadow-sm ring-1 ring-brand-200'
                  : 'border-slate-200 bg-slate-50/50 opacity-80'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span
                  className={`text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                    isActive
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                      : 'bg-slate-200 text-slate-600'
                  }`}
                >
                  {isActive ? 'Current Release' : 'Planned'}
                </span>
                <span className="text-xs font-semibold text-slate-500">{mod.milestone}</span>
              </div>

              <div className="flex items-start space-x-2.5 mt-2">
                <Icon
                  className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
                    isActive ? 'text-brand-600' : 'text-slate-400'
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
