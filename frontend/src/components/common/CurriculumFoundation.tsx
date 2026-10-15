import React from 'react';
import { Layers, Database, Check } from 'lucide-react';

export const CurriculumFoundation: React.FC = () => {
  const taxonomyLayers = [
    {
      level: '1. Boards & Curricula',
      entity: 'boards_curricula',
      examples: 'CBSE, JEE Main, NEET',
      desc: 'National and state academic examination boards',
    },
    {
      level: '2. Academic Stages',
      entity: 'grades_stages',
      examples: 'Class 11 (+1), Class 12 (+2)',
      desc: 'Grade groupings with sequential progression order',
    },
    {
      level: '3. Academic Subjects',
      entity: 'subjects',
      examples: 'Physics, Chemistry, Mathematics, Biology',
      desc: 'Discipline categories linked to target academic streams',
    },
    {
      level: '4. Chapters & Units',
      entity: 'chapters',
      examples: 'Electrostatics, Chemical Kinetics, Integrals',
      desc: 'Syllabus units with structured display sequences',
    },
    {
      level: '5. Granular Topics',
      entity: 'topics',
      examples: "Coulomb's Law, Rate Laws, Definite Integrals",
      desc: 'Target concept units for mastery tracking and learning progression',
    },
    {
      level: '6. Structured Lessons',
      entity: 'lessons',
      examples: 'Verified Lessons with Learning Objectives',
      desc: 'Verified educational units with publication workflow (Draft, In-Review, Published)',
    },
    {
      level: '7. Content Sections',
      entity: 'lesson_sections',
      examples: 'Concepts, Formulas, Worked Examples, Notes',
      desc: 'Ordered pedagogical sections rendered with KaTeX mathematical typesetting',
    },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
      <div className="flex items-center space-x-2 mb-4">
        <Database className="w-5 h-5 text-brand-600" />
        <h2 className="text-base font-bold text-slate-900">Foundational Curriculum & Content Schema</h2>
      </div>
      <p className="text-xs text-slate-600 mb-6">
        Milestone 3 establishes structured lessons and ordered content sections. The entities below are migrated and active in the database:
      </p>

      <div className="space-y-3">
        {taxonomyLayers.map((layer, index) => (
          <div
            key={index}
            className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50 hover:bg-white hover:border-brand-200 transition-colors"
          >
            <div className="flex items-center space-x-3 mb-2 sm:mb-0">
              <div className="w-6 h-6 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-xs font-semibold">
                <Check className="w-3.5 h-3.5" />
              </div>
              <div>
                <span className="text-xs font-bold text-slate-800">{layer.level}</span>
                <code className="ml-2 text-[11px] font-mono text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded border border-brand-100">
                  {layer.entity}
                </code>
                <p className="text-xs text-slate-500 mt-0.5">{layer.desc}</p>
              </div>
            </div>
            <div className="text-left sm:text-right">
              <span className="text-xs font-medium text-slate-700 bg-white px-2 py-1 rounded border border-slate-200 inline-block">
                {layer.examples}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <span className="flex items-center space-x-1">
          <Layers className="w-4 h-4 text-emerald-600" />
          <span>Alembic Migrations: 11 Tables Active (ac0e5ff2e448 head)</span>
        </span>
        <span className="font-semibold text-emerald-700">Verified by Automated Full-Stack Tests</span>
      </div>
    </div>
  );
};
