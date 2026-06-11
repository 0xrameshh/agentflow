"use client";

import { useState, useRef, useEffect } from "react";
import AppShell from "./AppShell";
import MessageBubble from "./MessageBubble";
import Composer from "./Composer";
import WelcomePanel from "./WelcomePanel";
import { streamSupport, getKbArticles } from "@/lib/api";
import type { Citation } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  streaming?: boolean;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [kbCount, setKbCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const initialized = useRef(false);

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    getKbArticles()
      .then((data) => setKbCount(data.count))
      .catch(() => setKbCount(0));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, status]);

  const handleSend = async (text: string) => {
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
          } else if (phase === "critique") {
            setStatus("Running critic verification…");
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

  const showWelcome = messages.length === 0;

  return (
    <AppShell>
      <div className="flex flex-col h-full min-h-0">
        <header className="shrink-0 border-b border-slate-200/80 bg-white/90 dark:bg-slate-900/90 dark:border-slate-800 backdrop-blur px-4 py-3 lg:px-6">
          <div className="flex items-center justify-between gap-4">
            <div className="lg:hidden flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 text-xs font-bold text-white">
                AF
              </div>
              <div>
                <h1 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Agentflow</h1>
                <p className="text-[11px] text-slate-500">Document Copilot</p>
              </div>
            </div>
            <div className="hidden lg:block">
              <h1 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                {process.env.NEXT_PUBLIC_KB_NAME || "Internal Knowledge Base"}
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Cited answers · LangGraph agent · SSE streaming
                {kbCount !== null ? ` · ${kbCount} docs` : ""}
              </p>
            </div>
            <div className="flex items-center gap-2 text-[11px] text-slate-500">
              <span className="hidden sm:inline rounded-full border border-slate-200 dark:border-slate-700 px-2 py-0.5">
                Eval 92%
              </span>
              <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2 py-0.5 text-cyan-700 dark:text-cyan-300">
                Live
              </span>
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-6 lg:px-8">
          <div className="mx-auto max-w-3xl space-y-4">
            {showWelcome && (
              <WelcomePanel
                onSelectPrompt={handleSend}
                disabled={loading}
                kbCount={kbCount}
              />
            )}

            {messages.map((msg, i) => (
              <MessageBubble
                key={i}
                role={msg.role}
                content={msg.content}
                citations={msg.citations}
                streaming={msg.streaming}
              />
            ))}

            {status && (
              <p className="text-xs text-slate-500 dark:text-slate-400 pl-11 animate-pulse">
                {status}
              </p>
            )}

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
            <Composer onSend={handleSend} disabled={loading} />
            <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-2 text-center">
              Responses are grounded in indexed documents. Verify critical decisions against originals.
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
