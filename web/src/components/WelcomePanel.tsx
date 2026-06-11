"use client";

const CAPABILITIES = [
  {
    title: "Grounded answers",
    body: "Every response is retrieved from indexed policies, manuals, and runbooks — not guessed from model memory.",
  },
  {
    title: "Source citations",
    body: "Answers include document name, snippet, file type, and page number so teams can verify before acting.",
  },
  {
    title: "Quality loop",
    body: "A structured critic scores drafts and sends low-confidence answers back for revision before delivery.",
  },
];

export default function WelcomePanel({
  onSelectPrompt,
  disabled,
  kbCount,
}: {
  onSelectPrompt: (prompt: string) => void;
  disabled: boolean;
  kbCount: number | null;
}) {
  const prompts = [
    "What is the meal expense limit per day?",
    "What is the SEV1 incident response time?",
    "What does the onboarding manual say about laptops?",
    "How many days can I work remotely per week?",
  ];

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white/80 dark:bg-slate-900/50 dark:border-slate-800 p-6 shadow-sm backdrop-blur-sm">
      <div className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-wider text-cyan-600 dark:text-cyan-400">
          Enterprise knowledge copilot
        </p>
        <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
          Ask your document library
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400 max-w-xl">
          Agentflow ingests PDFs, markdown, and text into a vector index, runs a LangGraph
          agent with tool use and critic verification, and returns cited answers you can audit.
          {kbCount !== null && kbCount > 0 && (
            <span className="text-slate-500 dark:text-slate-500">
              {" "}
              · {kbCount} documents indexed
            </span>
          )}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3 mb-6">
        {CAPABILITIES.map((cap) => (
          <div
            key={cap.title}
            className="rounded-xl border border-slate-100 bg-slate-50/80 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/60"
          >
            <p className="text-sm font-medium text-slate-900 dark:text-slate-100">{cap.title}</p>
            <p className="mt-1 text-xs leading-relaxed text-slate-600 dark:text-slate-400">{cap.body}</p>
          </div>
        ))}
      </div>

      <p className="text-xs font-medium text-slate-500 dark:text-slate-500 mb-2">Try a question</p>
      <div className="flex flex-wrap gap-2">
        {prompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => onSelectPrompt(prompt)}
            disabled={disabled}
            className="text-left text-xs px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:border-cyan-500/50 hover:text-cyan-700 dark:hover:text-cyan-300 disabled:opacity-50 transition-colors cursor-pointer"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
