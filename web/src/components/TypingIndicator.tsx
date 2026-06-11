"use client";

export default function TypingIndicator({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 pl-11">
      <div className="flex items-center gap-1 rounded-full border border-slate-200 bg-white px-3 py-1.5 dark:border-slate-800 dark:bg-slate-900">
        <span className="h-1.5 w-1.5 rounded-full bg-cyan-500 animate-bounce [animation-delay:0ms]" />
        <span className="h-1.5 w-1.5 rounded-full bg-cyan-500 animate-bounce [animation-delay:150ms]" />
        <span className="h-1.5 w-1.5 rounded-full bg-cyan-500 animate-bounce [animation-delay:300ms]" />
      </div>
      <p className="text-xs text-slate-500 dark:text-slate-400">{label}</p>
    </div>
  );
}
