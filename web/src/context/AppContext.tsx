"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { getHealth, getKbArticles, type HealthResponse } from "@/lib/api";

interface AppContextValue {
  health: HealthResponse | null;
  online: boolean;
  kbCount: number | null;
  kbArticles: string[];
  refresh: () => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [online, setOnline] = useState(false);
  const [kbCount, setKbCount] = useState<number | null>(null);
  const [kbArticles, setKbArticles] = useState<string[]>([]);

  const refresh = useCallback(() => {
    getHealth()
      .then((data) => {
        setHealth(data);
        setOnline(data.status === "ok");
      })
      .catch(() => {
        setHealth(null);
        setOnline(false);
      });

    getKbArticles()
      .then((data) => {
        setKbCount(data.count);
        setKbArticles(data.articles);
      })
      .catch(() => {
        setKbCount(0);
        setKbArticles([]);
      });
  }, []);

  useEffect(() => {
    refresh();
    const id = window.setInterval(refresh, 30_000);
    return () => window.clearInterval(id);
  }, [refresh]);

  return (
    <AppContext.Provider value={{ health, online, kbCount, kbArticles, refresh }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
