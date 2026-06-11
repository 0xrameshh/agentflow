import Sidebar from "./Sidebar";

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-full min-h-0 bg-slate-50 dark:bg-slate-950">
      <Sidebar />
      <main className="flex flex-1 flex-col min-w-0 min-h-0">{children}</main>
    </div>
  );
}
