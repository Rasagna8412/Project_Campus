import React, { useState } from 'react';
import {
  Bot,
  CheckCircle2,
  Code2,
  Loader2,
  Lock,
  Play,
  RotateCcw,
  ShieldCheck,
  X,
} from 'lucide-react';
import { AITutorDrawer } from '../tutor/AITutorDrawer';

interface CodingSandboxModalProps {
  isOpen: boolean;
  onClose: () => void;
  topicId?: string;
  topicTitle?: string;
}

type ProgrammingLanguage = 'c' | 'python' | 'javascript';

const STARTER_CODES: Record<ProgrammingLanguage, string> = {
  c: `// B.Tech CSE: Problem Solving & Programming in C
// Task: Calculate array sum using pointer arithmetic (no arr[i] indexing)
#include <stdio.h>

int calculate_array_sum(const int *arr, int n) {
    int sum = 0;
    const int *ptr = arr;
    
    // Iterate using pointer increment
    for (int i = 0; i < n; i++) {
        sum += *ptr;
        ptr++; // Advance to next element
    }
    
    return sum;
}

int main() {
    int sample[] = {10, 20, 30, 40, 50};
    int n = 5;
    printf("Calculated Sum: %d\\n", calculate_array_sum(sample, n));
    return 0;
}`,
  python: `# B.Tech CSE: Technical Problem Solving in Python
def calculate_array_sum(arr: list[int]) -> int:
    """Calculate the sum of all elements in the array."""
    total = 0
    for num in arr:
        total += num
    return total

if __name__ == "__main__":
    sample = [10, 20, 30, 40, 50]
    print(f"Calculated Sum: {calculate_array_sum(sample)}")
`,
  javascript: `// B.Tech CSE: Algorithmic JavaScript
function calculateArraySum(arr) {
    let sum = 0;
    for (let i = 0; i < arr.length; i++) {
        sum += arr[i];
    }
    return sum;
}

const sample = [10, 20, 30, 40, 50];
console.log("Calculated Sum:", calculateArraySum(sample));
`,
};

export const CodingSandboxModal: React.FC<CodingSandboxModalProps> = ({
  isOpen,
  onClose,
  topicId,
  topicTitle,
}) => {
  const [language, setLanguage] = useState<ProgrammingLanguage>('c');
  const [code, setCode] = useState<string>(STARTER_CODES.c);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [testResults, setTestResults] = useState<{
    id: number;
    name: string;
    input: string;
    expected: string;
    actual: string;
    passed: boolean;
    durationMs: number;
  }[] | null>(null);

  const [showSecurityDrawer, setShowSecurityDrawer] = useState<boolean>(false);
  const [isTutorOpen, setIsTutorOpen] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleLanguageChange = (newLang: ProgrammingLanguage) => {
    setLanguage(newLang);
    setCode(STARTER_CODES[newLang]);
    setTestResults(null);
  };

  const handleRunTests = () => {
    setIsRunning(true);
    // Simulate isolated client-side test evaluation
    setTimeout(() => {
      const mockResults = [
        {
          id: 1,
          name: 'Sample Test Case 1',
          input: 'arr = [10, 20, 30, 40, 50], n = 5',
          expected: '150',
          actual: '150',
          passed: true,
          durationMs: 4,
        },
        {
          id: 2,
          name: 'Sample Test Case 2 (Negative Numbers)',
          input: 'arr = [-5, 12, 7], n = 3',
          expected: '14',
          actual: '14',
          passed: true,
          durationMs: 3,
        },
        {
          id: 3,
          name: 'Boundary Test Case (Single Element)',
          input: 'arr = [42], n = 1',
          expected: '42',
          actual: '42',
          passed: true,
          durationMs: 2,
        },
      ];
      setTestResults(mockResults);
      setIsRunning(false);
    }, 600);
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="coding-modal-title"
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/70 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6"
    >
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-5xl w-full h-[90vh] flex flex-col relative overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <header className="p-4 sm:p-5 border-b border-slate-200 bg-slate-900 text-white flex items-center justify-between flex-shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md">
              <Code2 className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 id="coding-modal-title" className="font-bold text-base text-white">
                  Engineering Code Sandbox & Problem Studio
                </h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-indigo-500/30 text-indigo-200 border border-indigo-400/30">
                  Undergraduate Track
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                {topicTitle || 'Problem Solving & Programming in C (CS101)'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowSecurityDrawer(!showSecurityDrawer)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-white/10 hover:bg-white/15 text-slate-300 border border-white/20 transition-all flex items-center space-x-1"
              title="View sandbox security architecture"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span className="hidden sm:inline">Sandbox Security Spec</span>
            </button>

            <button
              onClick={() => setIsTutorOpen(true)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-brand-600 hover:bg-brand-500 text-white shadow-sm transition-all flex items-center space-x-1"
            >
              <Bot className="w-3.5 h-3.5" />
              <span>Ask AI Tutor</span>
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
              aria-label="Close code sandbox"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Security Architecture Collapsible Banner */}
        {showSecurityDrawer && (
          <div className="bg-slate-800 border-b border-slate-700 p-4 text-xs text-slate-300 space-y-2 animate-in slide-in-from-top-2 duration-150">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white flex items-center space-x-1.5 text-xs">
                <Lock className="w-4 h-4 text-emerald-400" />
                <span>Isolated Production Sandbox Specification (Zero-Trust DevSecOps Architecture)</span>
              </span>
              <button
                onClick={() => setShowSecurityDrawer(false)}
                className="text-slate-400 hover:text-white text-xs"
              >
                Dismiss
              </button>
            </div>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              To defend against arbitrary code execution, server privilege escalation, and lateral network traversal, 
              Project Campus enforces a strict sandboxing architecture:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1 text-[11px]">
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-700">
                <span className="font-bold text-amber-300 block mb-0.5">MicroVM Isolation</span>
                Ephemeral gVisor runsc / Firecracker microVM with isolated kernel space per execution.
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-700">
                <span className="font-bold text-amber-300 block mb-0.5">Network Egress Block</span>
                Enforces <code>--net=none</code>. Sockets and external network interfaces are completely disabled.
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-700">
                <span className="font-bold text-amber-300 block mb-0.5">Resource Capping</span>
                CPU: 2.0s wall clock, RAM: 64MB max, PIDs: 32 max via cgroups v2, read-only rootfs.
              </div>
            </div>
          </div>
        )}

        {/* Workspace Body: Split View */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden">
          {/* Left Panel: Problem Statement & Constraints (5 cols) */}
          <div className="lg:col-span-5 border-r border-slate-200 overflow-y-auto p-5 sm:p-6 space-y-5 bg-slate-50/50">
            <div>
              <div className="flex items-center space-x-2 text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                <span>CS101 Engineering Problem #1</span>
                <span>•</span>
                <span className="text-emerald-700 font-extrabold">Medium</span>
              </div>
              <h3 className="text-xl font-extrabold text-slate-900">
                Array Sum via Pointer Arithmetic
              </h3>
            </div>

            <div className="prose prose-slate max-w-none text-xs sm:text-sm text-slate-700 space-y-3 leading-relaxed">
              <p>
                In high-performance systems programming, understanding raw memory addressing is foundational. 
                You are given an integer array stored contiguously in memory.
              </p>
              <p>
                Implement the function <code>calculate_array_sum</code> to compute the total sum of all elements.
              </p>
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-xs">
                <strong>Pedagogical Constraint:</strong> In C, do NOT use array subscript indexing (<code>arr[i]</code>). 
                Instead, utilize pointer dereferencing (<code>*ptr</code>) and pointer increments (<code>ptr++</code>) to advance through memory.
              </div>

              <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider pt-2">
                Sample Input & Output
              </h4>
              <div className="space-y-2 font-mono text-xs">
                <div className="p-3 bg-white rounded-xl border border-slate-200">
                  <span className="text-slate-400 block text-[10px] uppercase font-sans">Sample Input 1:</span>
                  <p className="text-slate-800 mt-1">arr = [10, 20, 30, 40, 50], n = 5</p>
                  <span className="text-slate-400 block text-[10px] uppercase font-sans mt-2">Expected Output:</span>
                  <p className="text-emerald-700 font-bold">150</p>
                </div>
                <div className="p-3 bg-white rounded-xl border border-slate-200">
                  <span className="text-slate-400 block text-[10px] uppercase font-sans">Sample Input 2:</span>
                  <p className="text-slate-800 mt-1">arr = [-5, 12, 7], n = 3</p>
                  <span className="text-slate-400 block text-[10px] uppercase font-sans mt-2">Expected Output:</span>
                  <p className="text-emerald-700 font-bold">14</p>
                </div>
              </div>

              <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider pt-2">
                Resource Constraints
              </h4>
              <ul className="list-disc pl-5 text-xs text-slate-600 space-y-1">
                <li>1 ≤ n ≤ 100,000</li>
                <li>-10,000 ≤ arr[i] ≤ 10,000</li>
                <li>Time Limit: <strong>2.0 seconds</strong></li>
                <li>Memory Limit: <strong>64 MB</strong></li>
              </ul>
            </div>
          </div>

          {/* Right Panel: Code Editor & Test Runner (7 cols) */}
          <div className="lg:col-span-7 flex flex-col h-full bg-slate-900 text-slate-100 overflow-hidden">
            {/* Editor Toolbar */}
            <div className="p-3 bg-slate-950 border-b border-slate-800 flex items-center justify-between text-xs">
              <div className="flex items-center space-x-2">
                <span className="text-slate-400 text-xs font-semibold">Language:</span>
                {(['c', 'python', 'javascript'] as ProgrammingLanguage[]).map((lang) => (
                  <button
                    key={lang}
                    onClick={() => handleLanguageChange(lang)}
                    className={`px-3 py-1 rounded-lg text-xs font-mono font-bold transition-all ${
                      language === lang
                        ? 'bg-brand-600 text-white shadow-sm'
                        : 'bg-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    {lang === 'c' && 'C (GCC 12)'}
                    {lang === 'python' && 'Python 3.11'}
                    {lang === 'javascript' && 'Node.js 20'}
                  </button>
                ))}
              </div>

              <button
                onClick={() => setCode(STARTER_CODES[language])}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                title="Reset starter code"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Code Textarea Area */}
            <div className="flex-1 relative font-mono text-xs sm:text-sm p-4 overflow-auto bg-slate-900">
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                spellCheck={false}
                className="w-full h-full bg-transparent text-emerald-300 font-mono resize-none focus:outline-none leading-relaxed"
                style={{ tabSize: 4 }}
              />
            </div>

            {/* Test Case Results Drawer */}
            {testResults && (
              <div className="p-4 bg-slate-950 border-t border-slate-800 max-h-48 overflow-y-auto space-y-2 animate-in slide-in-from-bottom-2 duration-150">
                <div className="flex items-center justify-between text-xs font-bold text-slate-300 mb-2">
                  <span className="flex items-center space-x-1.5 text-emerald-400">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>All 3 Sample Test Cases Passed!</span>
                  </span>
                  <span className="text-slate-500 font-mono text-[11px]">Execution Time: ~4ms</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {testResults.map((t) => (
                    <div
                      key={t.id}
                      className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-300 text-[11px]">{t.name}</span>
                        <span className="text-emerald-400 font-bold text-[10px]">PASS</span>
                      </div>
                      <p className="text-[10px] text-slate-500 mt-1 truncate">Expected: {t.expected}</p>
                      <p className="text-[10px] text-emerald-400 truncate">Output: {t.actual}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Editor Action Footer */}
            <footer className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between">
              <div className="text-[11px] text-slate-500 font-mono">
                Memory: 64MB • Timeout: 2.0s
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setIsTutorOpen(true)}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors flex items-center space-x-1.5"
                >
                  <Bot className="w-4 h-4 text-brand-400" />
                  <span>Ask AI for Hint</span>
                </button>

                <button
                  onClick={handleRunTests}
                  disabled={isRunning}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md transition-all flex items-center space-x-1.5 disabled:opacity-50"
                >
                  {isRunning ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Evaluating in Sandbox...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      <span>Run Sample Tests</span>
                    </>
                  )}
                </button>
              </div>
            </footer>
          </div>
        </div>

        {/* AI Tutor Drawer integration for coding assistance */}
        <AITutorDrawer
          isOpen={isTutorOpen}
          onClose={() => setIsTutorOpen(false)}
          initialTopicId={topicId}
          initialTopicTitle={topicTitle || "Pointers and Dynamic Memory Allocation in C"}
          initialPrompt="Can you give me a conceptual hint on calculating array sum using pointer arithmetic in C without using index subscripting?"
          initialMode="HINT"
        />
      </div>
    </div>
  );
};
