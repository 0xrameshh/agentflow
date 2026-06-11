"use client";

import { useEffect, useState } from "react";
import { getHealth, type HealthResponse } from "@/lib/api";

const PIPELINE = [
  { step: "Ingest", detail: "PDF · MD · TXT → Chroma" },
  { step: "Retrieve", detail: "Semantic + keyword search" },
  { step: "Reason", detail: "LangGraph agent + tools" },
  { step: "Verify", detail: "Structured critic loop" },
  { step: "Cite", detail: "Source snippets + page refs" },
];

export default function Sidebar() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [online, setOnline] = useState(false);

  useEffect(() => {
    getHealth()
      .then((data) => {
        setHealth(data);
        setOnline(data.status === "ok");
      })
      .catch(() => {
        setHealth(null);
        setOnline(false);
      });
  }, []);

  return (
    <aside className="hidden lg:flex w-72 flex-col border-r border-slate-200/80 bg-slate-950 text-slate-100">
      <div className="px-5 py-6 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 text-sm font-bold text-white shadow-lg shadow-cyan-500/20">
            AF
          </div>
          <div>
            <p className="text-sm font-semibold tracking-tight">Agentflow</p>
            <p className="text-xs text-slate-400">Document Copilot</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-5 space-y-6">
        <section>
          <h2 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-3">
            System status
          </h2>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">API</span>
              <span className={`inline-flex items-center gap-1.5 ${online ? "text-emerald-400" : "text-amber-400"}`}>
                <span className={`h-1.5 w-1.5 rounded-full ${online ? "bg-emerald-400" : "bg-amber-400 animate-pulse"}`} />
                {online ? "Online" : "Offline"}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Indexed docs</span>
              <span className="font-mono text-slate-200">{health?.kb_documents ?? "—"}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Eval suite</span>
              <span className="font-mono text-cyan-300">92% pass</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Version</span>
              <span className="font-mono text-slate-300">{health?.version ?? "0.2.0"}</span>
            </div>
          </div>
        </section>

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

        <section>
          <h2 className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-3">
            Built for
          </h2>
          <ul className="space-y-2 text-xs text-slate-400">
            <li>Internal policy & compliance Q&A</li>
            <li>Onboarding & ops runbooks</li>
            <li>Multi-format document search</li>
            <li>Auditable cited responses</li>
          </ul>
        </section>
      </div>

      <div className="px-5 py-4 border-t border-slate-800 text-[11px] text-slate-500">
        LangGraph · FastAPI · Chroma · Next.js
      </div>
    </aside>
  );
}
