"use client";

import { useState, useRef, useEffect } from "react";
import AppShell from "./AppShell";
import MessageBubble, { type RunMeta } from "./MessageBubble";
import Composer from "./Composer";
import WelcomePanel from "./WelcomePanel";
import TypingIndicator from "./TypingIndicator";
import StatusBadge from "./StatusBadge";
import MobileInfoSheet from "./MobileInfoSheet";
import { streamSupport } from "@/lib/api";
import type { Citation } from "@/lib/api";
import { useApp } from "@/context/AppContext";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  streaming?: boolean;
  meta?: RunMeta;
}

function ChatView() {
  const { online, kbCount } = useApp();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, status]);

  const handleSend = async (text: string) => {
    if (!online) {
      setError("API is offline. Start the backend with: uv run agentflow-api");
      return;
    }

    setLoading(true);
    setStatus("Searching knowledge base…");
    setError(null);

    let assistantIndex = 0;
    setMessages((prev) => {
      const withUser = [...prev, { role: "user" as const, content: text }];
      assistantIndex = withUser.length;
      return [...withUser, { role: "assistant" as const, content: "", streaming: true }];
    });

    try {
      await streamSupport(text, {
        onStatus: (phase) => {
          if (phase === "searching") {
            setStatus("Searching knowledge base…");
          }
        },
        onChunk: (chunk) => {
          setStatus(null);
          setMessages((prev) => {
            const next = [...prev];
            const msg = next[assistantIndex];
            if (!msg || msg.role !== "assistant") return prev;
            next[assistantIndex] = {
              ...msg,
              content: msg.content + chunk,
              streaming: true,
            };
            return next;
          });
        },
        onDone: (data) => {
          setStatus(null);
          setMessages((prev) => {
            const next = [...prev];
            const msg = next[assistantIndex];
            if (!msg || msg.role !== "assistant") return prev;
            next[assistantIndex] = {
              role: "assistant",
              content: data.answer,
              citations: data.citations,
              streaming: false,
              meta: {
                latency_ms: data.latency_ms,
                tool_call_count: data.tool_call_count,
                revision_count: data.revision_count,
              },
            };
            return next;
          });
        },
        onError: (message) => {
          setError(message);
          setMessages((prev) => {
            const next = [...prev];
            next[assistantIndex] = {
              role: "assistant",
              content: `**Error:** ${message}`,
              streaming: false,
            };
            return next;
          });
        },
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Connection error";
      setError(msg);
      setMessages((prev) => {
        const next = [...prev];
        next[assistantIndex] = {
          role: "assistant",
          content: `**Error:** ${msg}\n\nMake sure the API server is running on \`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081"}\`.`,
          streaming: false,
        };
        return next;
      });
    }

    setStatus(null);
    setLoading(false);
  };

  const handleNewChat = () => {
    setMessages([]);
    setError(null);
    setStatus(null);
  };

  const showWelcome = messages.length === 0;

  return (
      <div className="flex flex-col h-full min-h-0">
        <header className="shrink-0 border-b border-slate-200/80 bg-white/90 dark:bg-slate-900/90 dark:border-slate-800 backdrop-blur px-4 py-3 lg:px-6">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="lg:hidden flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 text-xs font-bold text-white">
                AF
              </div>
              <div className="min-w-0">
                <h1 className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
                  {process.env.NEXT_PUBLIC_KB_NAME || "Internal Knowledge Base"}
                </h1>
                <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                  Cited answers · LangGraph · SSE
                  {kbCount !== null ? ` · ${kbCount} docs` : ""}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {!showWelcome && (
                <button
                  type="button"
                  onClick={handleNewChat}
                  className="hidden sm:inline-flex rounded-lg border border-slate-200 px-2.5 py-1 text-[11px] text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                >
                  New chat
                </button>
              )}
              <span className="hidden sm:inline rounded-full border border-slate-200 dark:border-slate-700 px-2 py-0.5 text-[11px] text-slate-500">
                Eval 92%
              </span>
              <StatusBadge online={online} />
              <MobileInfoSheet />
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-6 lg:px-8">
          <div className="mx-auto max-w-3xl space-y-5">
            {showWelcome && (
              <WelcomePanel onSelectPrompt={handleSend} disabled={loading || !online} />
            )}

            {!online && showWelcome && (
              <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200">
                Start the API server: <code className="font-mono text-xs">uv run agentflow-api</code>
              </div>
            )}

            {messages.map((msg, i) => (
              <MessageBubble
                key={i}
                role={msg.role}
                content={msg.content}
                citations={msg.citations}
                streaming={msg.streaming}
                meta={msg.meta}
              />
            ))}

            {status && <TypingIndicator label={status} />}

            {error && (
              <div className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 px-3 py-2 rounded-lg border border-red-200 dark:border-red-900/50">
                {error}
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        </div>

        <div className="shrink-0 border-t border-slate-200/80 bg-white/90 dark:bg-slate-900/90 dark:border-slate-800 backdrop-blur px-4 py-4 lg:px-8">
          <div className="mx-auto max-w-3xl">
            <Composer onSend={handleSend} disabled={loading || !online} />
            <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-2 text-center">
              Grounded in indexed documents · verify critical decisions against originals
            </p>
          </div>
        </div>
      </div>
  );
}

export default function Chat() {
  return (
    <AppShell>
      <ChatView />
    </AppShell>
  );
}
