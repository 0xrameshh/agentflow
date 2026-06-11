"use client";

import { useApp } from "@/context/AppContext";

const CAPABILITIES = [
  {
    title: "Grounded answers",
    body: "Retrieved from indexed policies, manuals, and runbooks — not model memory.",
  },
  {
    title: "Source citations",
    body: "Document name, snippet, file type, and page number for audit trails.",
  },
  {
    title: "Quality loop",
    body: "Structured critic re-scores drafts before answers are delivered.",
  },
];

export default function WelcomePanel({
  onSelectPrompt,
  disabled,
}: {
  onSelectPrompt: (prompt: string) => void;
  disabled: boolean;
}) {
  const { kbCount } = useApp();

  const prompts = [
    "What is the meal expense limit per day?",
    "What is the SEV1 incident response time?",
    "What does the onboarding manual say about laptops?",
    "How many days can I work remotely per week?",
  ];

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white/90 dark:bg-slate-900/60 dark:border-slate-800 p-6 shadow-sm backdrop-blur-sm">
      <div className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-wider text-cyan-600 dark:text-cyan-400">
          Enterprise document copilot
        </p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
          Ask your document library
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400 max-w-xl">
          Multi-format RAG with LangGraph orchestration, critic verification, and cited streaming answers.
          {kbCount !== null && kbCount > 0 && (
            <span className="text-slate-500"> · {kbCount} documents indexed</span>
          )}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3 mb-6">
        {CAPABILITIES.map((cap) => (
          <div
            key={cap.title}
            className="rounded-xl border border-slate-100 bg-slate-50/90 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/60"
          >
            <p className="text-sm font-medium text-slate-900 dark:text-slate-100">{cap.title}</p>
            <p className="mt-1 text-xs leading-relaxed text-slate-600 dark:text-slate-400">{cap.body}</p>
          </div>
        ))}
      </div>

      <p className="text-xs font-medium text-slate-500 mb-2">Suggested questions</p>
      <div className="grid gap-2 sm:grid-cols-2">
        {prompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => onSelectPrompt(prompt)}
            disabled={disabled}
            className="text-left text-xs px-3 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:border-cyan-500/50 hover:bg-cyan-50/50 dark:hover:bg-cyan-950/20 disabled:opacity-50 transition-colors cursor-pointer"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
