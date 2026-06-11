"use client";

import { useState, useRef, useEffect } from "react";

interface ComposerProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

export default function Composer({ onSend, disabled }: ComposerProps) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!disabled && inputRef.current) {
      inputRef.current.focus();
    }
  }, [disabled]);

  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 128)}px`;
  }, [input]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || disabled) return;
    onSend(text);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 items-end">
      <div className="flex-1 relative">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about policies, runbooks, or onboarding docs…"
          rows={1}
          disabled={disabled}
          className="w-full resize-none rounded-xl border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-4 py-3 pr-16 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 disabled:opacity-50 dark:text-slate-100"
          style={{ minHeight: "48px", maxHeight: "128px" }}
        />
        <span className="pointer-events-none absolute bottom-2.5 right-3 text-[10px] text-slate-400">
          ↵ send
        </span>
      </div>
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        className="shrink-0 px-5 py-3 rounded-xl bg-slate-900 dark:bg-cyan-600 text-white text-sm font-medium hover:bg-slate-800 dark:hover:bg-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors min-h-[48px]"
      >
        {disabled ? (
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Working
          </span>
        ) : (
          "Send"
        )}
      </button>
    </form>
  );
}
