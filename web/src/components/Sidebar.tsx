"use client";

import { useApp } from "@/context/AppContext";
import StatusBadge from "./StatusBadge";

const PIPELINE = [
  { step: "Ingest", detail: "PDF · MD · TXT → Chroma" },
  { step: "Retrieve", detail: "Semantic + keyword search" },
  { step: "Reason", detail: "LangGraph agent + tools" },
  { step: "Verify", detail: "Structured critic loop" },
  { step: "Cite", detail: "Source snippets + page refs" },
];

export default function Sidebar() {
  const { health, online, kbCount, kbArticles } = useApp();

  return (
    <aside className="hidden lg:flex w-72 flex-col border-r border-slate-800/80 bg-slate-950 text-slate-100">
      <div className="px-5 py-6 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 text-sm font-bold text-white shadow-lg shadow-cyan-500/20">
            AF
          </div>
          <div>
            <p className="text-sm font-semibold tracking-tight">Agentflow</p>
            <p className="text-xs text-slate-400">Document Intelligence</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-5 space-y-6">
        <section>
          <h2 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-3">
            System status
          </h2>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3 space-y-3">
            <div className="flex items-center justify-between">
              <StatusBadge online={online} />
              <span className="text-[11px] font-mono text-cyan-300">92% eval</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <p className="text-slate-500">Indexed docs</p>
                <p className="font-mono text-slate-200">{kbCount ?? "—"}</p>
              </div>
              <div>
                <p className="text-slate-500">Version</p>
                <p className="font-mono text-slate-300">{health?.version ?? "0.2.0"}</p>
              </div>
            </div>
          </div>
        </section>

        {kbArticles.length > 0 && (
          <section>
            <h2 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-3">
              Knowledge base
            </h2>
            <ul className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
              {kbArticles.slice(0, 8).map((name) => (
                <li
                  key={name}
                  className="truncate rounded-md bg-slate-900/50 px-2 py-1 text-[11px] font-mono text-slate-400"
                  title={name}
                >
                  {name}
                </li>
              ))}
            </ul>
          </section>
        )}

        <section>
          <h2 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-3">
            Answer pipeline
          </h2>
          <ol className="space-y-2">
            {PIPELINE.map((item, i) => (
              <li key={item.step} className="flex gap-3 text-xs">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-slate-800 font-mono text-[10px] text-cyan-300">
                  {i + 1}
                </span>
                <div>
                  <p className="font-medium text-slate-200">{item.step}</p>
                  <p className="text-slate-500">{item.detail}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>
      </div>

      <div className="px-5 py-4 border-t border-slate-800 text-[11px] text-slate-500">
        LangGraph · FastAPI · Chroma · Next.js
      </div>
    </aside>
  );
}
