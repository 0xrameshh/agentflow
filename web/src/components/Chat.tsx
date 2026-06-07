"use client";

import { useState, useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import Composer from "./Composer";
import { postSupport, getKbArticles, type Citation } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
}

const EXAMPLE_PROMPTS = [
  "What is the meal expense limit per day?",
  "What security measures are required?",
  "How long after an expense should I submit?",
  "What does the onboarding manual say about laptops?",
  "What is the SEV1 incident response time?",
];

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm the Knowledge Copilot. Ask me about the documents in the knowledge base — policies, manuals, notes, and more. I cite my sources so you can verify the answers.",
    },
  ]);
  const [loading, setLoading] = useState(false);
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
  }, [messages]);

  const handleSend = async (text: string) => {
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);
    setError(null);

    try {
      const data = await postSupport(text);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          citations: data.citations,
        },
      ]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Connection error";
      setError(msg);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `**Error:** ${msg}\n\nMake sure the API server is running on \`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081"}\`.`,
        },
      ]);
    }

    setLoading(false);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-3">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">
            {process.env.NEXT_PUBLIC_KB_NAME || "Knowledge Copilot"}
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Cited answers from your documents
            {kbCount !== null ? ` · ${kbCount} documents indexed` : ""}
          </p>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.map((msg, i) => (
            <MessageBubble key={i} role={msg.role} content={msg.content} citations={msg.citations} />
          ))}

          {/* Example prompts on first message */}
          {messages.length === 1 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {EXAMPLE_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => handleSend(prompt)}
                  disabled={loading}
                  className="text-xs px-3 py-1.5 rounded-full border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/40 disabled:opacity-50 transition-colors cursor-pointer"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}

          {error && (
            <div className="text-xs text-red-500 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded-lg border border-red-200 dark:border-red-800">
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Composer */}
      <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-3">
        <div className="max-w-3xl mx-auto">
          <Composer onSend={handleSend} disabled={loading} />
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1.5 text-center">
            Answers are based on the indexed knowledge base. Verify critical information against original documents.
          </p>
        </div>
      </div>
    </div>
  );
}
