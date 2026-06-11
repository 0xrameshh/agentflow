"use client";

import { AppProvider } from "@/context/AppContext";
import Sidebar from "./Sidebar";

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <AppProvider>
      <div className="flex h-full min-h-0 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.08),transparent_40%),linear-gradient(to_bottom,#f8fafc,#f1f5f9)] dark:bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.08),transparent_35%),linear-gradient(to_bottom,#020617,#0f172a)]">
        <Sidebar />
        <main className="flex flex-1 flex-col min-w-0 min-h-0">{children}</main>
      </div>
    </AppProvider>
  );
}
