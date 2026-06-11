"use client";

import { useState } from "react";
import { useApp } from "@/context/AppContext";
import StatusBadge from "./StatusBadge";

const PIPELINE = [
  "Ingest PDF · MD · TXT",
  "Retrieve from Chroma",
  "LangGraph agent + tools",
  "Critic verification",
  "Cited answer",
];

export default function MobileInfoSheet() {
  const [open, setOpen] = useState(false);
  const { health, online, kbCount } = useApp();

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="lg:hidden rounded-lg border border-slate-200 px-2.5 py-1 text-[11px] text-slate-600 dark:border-slate-700 dark:text-slate-300"
      >
        Info
      </button>

      {open && (
        <div className="lg:hidden fixed inset-0 z-50">
          <button
            type="button"
            aria-label="Close"
            className="absolute inset-0 bg-slate-950/50 backdrop-blur-sm"
            onClick={() => setOpen(false)}
          />
          <div className="absolute bottom-0 left-0 right-0 max-h-[75vh] overflow-y-auto rounded-t-2xl border border-slate-800 bg-slate-950 p-5 text-slate-100">
            <div className="mx-auto mb-4 h-1 w-10 rounded-full bg-slate-700" />
            <div className="flex items-center justify-between gap-3 mb-4">
              <div>
                <p className="text-sm font-semibold">Agentflow</p>
                <p className="text-xs text-slate-400">Document Copilot</p>
              </div>
              <StatusBadge online={online} />
            </div>
            <div className="grid grid-cols-2 gap-2 mb-4 text-xs">
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
                <p className="text-slate-500">Indexed docs</p>
                <p className="mt-1 font-mono text-slate-200">{kbCount ?? "—"}</p>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
                <p className="text-slate-500">Version</p>
                <p className="mt-1 font-mono text-slate-200">{health?.version ?? "0.2.0"}</p>
              </div>
            </div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-2">
              Pipeline
            </p>
            <ol className="space-y-2 mb-4">
              {PIPELINE.map((step, i) => (
                <li key={step} className="flex gap-2 text-xs text-slate-300">
                  <span className="font-mono text-cyan-400">{i + 1}.</span>
                  {step}
                </li>
              ))}
            </ol>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="w-full rounded-xl bg-slate-800 py-2.5 text-sm font-medium"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </>
  );
}
