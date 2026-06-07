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
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0 ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
        }`}
      >
        {isUser ? "U" : "🤖"}
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[80%] px-4 py-2.5 rounded-2xl leading-relaxed text-sm ${
          isUser
            ? "bg-blue-600 text-white rounded-tr-sm"
            : "bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-tl-sm"
        }`}
      >
        <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0.5 prose-code:px-1 prose-code:py-0.5 prose-code:bg-gray-100 dark:prose-code:bg-gray-700 prose-code:rounded prose-code:text-xs">
          {content ? (
            <ReactMarkdown>{content}</ReactMarkdown>
          ) : streaming ? (
            <span className="text-gray-400">…</span>
          ) : null}
          {streaming && content && (
            <span className="inline-block w-2 h-4 ml-0.5 bg-blue-500 animate-pulse align-middle" />
          )}
        </div>

        {!isUser && !streaming && citations && citations.length > 0 && (
          <CitationChips citations={citations} />
        )}
      </div>
    </div>
  );
}
