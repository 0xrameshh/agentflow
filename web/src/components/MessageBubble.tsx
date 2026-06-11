"use client";

import ReactMarkdown from "react-markdown";
import CitationChips from "./CitationChips";
import type { Citation } from "@/lib/api";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  streaming?: boolean;
}

export default function MessageBubble({
  role,
  content,
  citations,
  streaming,
}: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={`flex gap-3 items-start ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-semibold flex-shrink-0 ${
          isUser
            ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
            : "bg-gradient-to-br from-cyan-500 to-blue-600 text-white shadow-sm"
        }`}
      >
        {isUser ? "You" : "AF"}
      </div>

      <div
        className={`max-w-[85%] px-4 py-3 rounded-2xl leading-relaxed text-sm shadow-sm ${
          isUser
            ? "bg-slate-900 text-white rounded-tr-md dark:bg-slate-100 dark:text-slate-900"
            : "bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 border border-slate-200/80 dark:border-slate-800 rounded-tl-md"
        }`}
      >
        <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0.5 prose-code:px-1 prose-code:py-0.5 prose-code:bg-slate-100 dark:prose-code:bg-slate-800 prose-code:rounded prose-code:text-xs">
          {content ? (
            <ReactMarkdown>{content}</ReactMarkdown>
          ) : streaming ? (
            <span className="text-slate-400">Generating answer…</span>
          ) : null}
          {streaming && content && (
            <span className="inline-block w-2 h-4 ml-0.5 bg-cyan-500 animate-pulse align-middle rounded-sm" />
          )}
        </div>

        {!isUser && !streaming && citations && citations.length > 0 && (
          <CitationChips citations={citations} />
        )}
      </div>
    </div>
  );
}
