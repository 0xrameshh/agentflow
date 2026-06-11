"use client";

import { useState } from "react";
import type { Citation } from "@/lib/api";

function fileBadge(source: string, fileType?: string | null) {
  const ext = fileType || source.split(".").pop()?.toUpperCase() || "DOC";
  return ext.slice(0, 4);
}

export default function CitationChips({ citations }: { citations: Citation[] }) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  if (!citations || citations.length === 0) return null;

  const toggle = (key: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  return (
    <div className="mt-3 pt-3 border-t border-slate-200/80 dark:border-slate-700/80">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
        Sources ({citations.length})
      </p>
      <div className="flex flex-col gap-2">
        {citations.map((c, i) => {
          const key = `${c.source}-${c.page ?? ""}-${i}`;
          const label = c.page ? `${c.source} · p.${c.page}` : c.source;
          const open = expanded.has(key);
          return (
            <div key={key} className="rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
              <button
                type="button"
                onClick={() => toggle(key)}
                className="flex w-full items-center gap-2 px-2.5 py-2 text-left text-xs hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors cursor-pointer"
              >
                <span className="rounded-md bg-cyan-500/10 px-1.5 py-0.5 font-mono text-[10px] text-cyan-700 dark:text-cyan-300">
                  {fileBadge(c.source, c.file_type)}
                </span>
                <span className="flex-1 truncate text-slate-700 dark:text-slate-200">{label}</span>
                <span className="text-slate-400">{open ? "−" : "+"}</span>
              </button>
              {open && c.snippet && (
                <div className="border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 px-2.5 py-2 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
                  {c.snippet}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
