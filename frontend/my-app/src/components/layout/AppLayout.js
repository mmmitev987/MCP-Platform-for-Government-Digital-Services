import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-gray-950">
      {/* ── Mobile top bar (hamburger) — hidden on lg+ ── */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-30 flex items-center gap-3 px-4 py-3 bg-gray-900 border-b border-gray-800">
        <button
          onClick={() => setSidebarOpen(true)}
          className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          aria-label="Open menu"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <h1 className="text-white font-bold text-base tracking-tight">
          Gov<span className="text-indigo-400">MCP</span>
        </h1>
      </div>

      {/* ── Backdrop overlay — mobile only ── */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Sidebar ──
           Mobile:  fixed drawer, slides in/out with translate-x
           Desktop: static, always visible                        ── */}
      <div
        className={`
          fixed inset-y-0 left-0 z-50 transition-transform duration-300 ease-in-out
          lg:static lg:translate-x-0 lg:z-auto lg:flex-shrink-0
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        <Sidebar onClose={() => setSidebarOpen(false)} />
      </div>

      {/* ── Main content ── */}
      <main className="flex-1 overflow-auto min-w-0 pt-12 lg:pt-0">
        <Outlet />
      </main>
    </div>
  );
}
