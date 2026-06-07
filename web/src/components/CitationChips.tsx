"use client";

import { useState } from "react";
import type { Citation } from "@/lib/api";

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
    <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700 flex flex-wrap gap-1.5">
      {citations.map((c, i) => {
        const key = `${c.source}-${c.page ?? ""}-${i}`;
        const label = c.page ? `${c.source} (p.${c.page})` : c.source;
        return (
          <span key={key} className="inline-flex flex-col">
            <button
              onClick={() => toggle(key)}
              className="text-xs px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800 hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors cursor-pointer"
              title="Click to show/hide snippet"
            >
              📄 {label}
            </button>
            {expanded.has(key) && c.snippet && (
              <span className="mt-1 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded border border-gray-200 dark:border-gray-700 max-w-md break-words">
                {c.snippet}
              </span>
            )}
          </span>
        );
      })}
    </div>
  );
}
