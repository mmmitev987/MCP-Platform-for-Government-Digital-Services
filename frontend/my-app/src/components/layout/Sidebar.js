import { useEffect, useState, useRef } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../contexts/AuthContext";
import { getSessions, renameSession, deleteSession } from "../../api/chat";

export default function Sidebar({ onClose }) {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [search, setSearch] = useState("");

  const links = [
    { to: "/dashboard", label: t("nav.dashboard"), icon: "⊞" },
    { to: "/assistant", label: t("nav.assistant"), icon: "◈" },
    { to: "/services", label: t("nav.services"), icon: "⊙" },
    { to: "/activity", label: t("nav.activity"), icon: "≡" },
    { to: "/settings", label: t("nav.settings"), icon: "⚙" },
  ];

  const fetchSessions = () => getSessions().then(setSessions).catch(() => {});

  useEffect(() => {
    fetchSessions();
    window.addEventListener("chat:session-created", fetchSessions);
    return () => window.removeEventListener("chat:session-created", fetchSessions);
  }, []);

  const handleRename = (id, newTitle) => {
    setSessions((prev) => prev.map((s) => s.id === id ? { ...s, title: newTitle } : s));
  };

  const handleDelete = (id) => {
    setSessions((prev) => prev.filter((s) => s.id !== id));
  };

  const filtered = search.trim()
    ? sessions.filter((s) =>
        (s.title || "Untitled").toLowerCase().includes(search.trim().toLowerCase())
      )
    : sessions;

  return (
    <aside className="w-64 h-screen bg-gray-900 border-r border-gray-800 flex flex-col">
      {/* Header — includes close button on mobile */}
      <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
        <div>
          <h1 className="text-white font-bold text-lg tracking-tight">Gov<span className="text-indigo-400">MCP</span></h1>
          <p className="text-gray-500 text-xs mt-0.5">Digital Services</p>
        </div>
        {/* Close button — visible only on mobile */}
        <button
          onClick={onClose}
          className="lg:hidden p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          aria-label="Close menu"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <nav className="px-3 py-4 space-y-1">
        {links.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-indigo-600 text-white"
                  : "text-gray-400 hover:bg-gray-800 hover:text-white"
              }`
            }
          >
            <span className="text-base">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      {sessions.length > 0 && (
        <div className="px-3 py-2 flex-1 min-h-0 flex flex-col">
          <p className="text-gray-600 text-xs font-semibold uppercase tracking-wider px-2 mb-2">
            {t("sidebar.recentChats")}
          </p>

          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t("sidebar.searchChats")}
            className="w-full bg-gray-800 border border-gray-700 text-white text-xs rounded-lg px-2.5 py-1.5 outline-none focus:border-indigo-500 placeholder-gray-600 mb-2 transition-colors"
          />

          <div className="flex-1 min-h-0 overflow-y-auto">
            {filtered.slice(0, 20).map((s) => (
              <ChatItem
                key={s.id}
                session={s}
                onRename={handleRename}
                onDelete={handleDelete}
                t={t}
              />
            ))}
            {filtered.length === 0 && (
              <p className="text-gray-600 text-xs px-2 py-1">{t("sidebar.noMatches")}</p>
            )}
          </div>
        </div>
      )}

      <div className="px-3 py-4 border-t border-gray-800">
        <button
          onClick={() => navigate("/settings")}
          className="w-full flex items-center gap-3 px-3 py-2 mb-2 rounded-lg hover:bg-gray-800 transition-colors text-left"
        >
          <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white text-sm font-bold shrink-0">
            {user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-white text-sm font-medium truncate">{user?.full_name || "User"}</p>
            <p className="text-gray-500 text-xs truncate">{user?.email}</p>
          </div>
        </button>
        <button
          onClick={logout}
          className="w-full text-left px-3 py-2 text-sm text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
        >
          {t("sidebar.signOut")}
        </button>
      </div>
    </aside>
  );
}

function ChatItem({ session, onRename, onDelete, t }) {
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(session.title || "Untitled");
  const [menuOpen, setMenuOpen] = useState(false);
  const inputRef = useRef(null);
  const menuRef = useRef(null);

  useEffect(() => {
    if (editing) inputRef.current?.focus();
  }, [editing]);

  useEffect(() => {
    if (!menuOpen) return;
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [menuOpen]);

  const commit = async () => {
    setEditing(false);
    if (value.trim() && value.trim() !== session.title) {
      await renameSession(session.id, value.trim());
      onRename(session.id, value.trim());
    }
  };

  const handleDelete = async () => {
    setMenuOpen(false);
    await deleteSession(session.id);
    onDelete(session.id);
  };

  const handleRename = () => {
    setMenuOpen(false);
    setEditing(true);
  };

  return (
    <div className="group flex items-center gap-1 px-2 py-1.5 rounded-lg hover:bg-gray-800 cursor-pointer">
      {editing ? (
        <input
          ref={inputRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => { if (e.key === "Enter") commit(); if (e.key === "Escape") setEditing(false); }}
          className="flex-1 bg-gray-700 text-white text-xs px-1.5 py-0.5 rounded outline-none min-w-0"
        />
      ) : (
        <span
          onClick={() => navigate(`/assistant?session=${session.id}`)}
          className="flex-1 text-gray-400 text-xs truncate"
        >
          {value}
        </span>
      )}

      <div className="relative" ref={menuRef}>
        <button
          onClick={(e) => { e.stopPropagation(); setMenuOpen((o) => !o); }}
          className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-white text-xs px-1 transition-opacity leading-none"
          title="Options"
        >
          ···
        </button>

        {menuOpen && (
          <div className="absolute right-0 top-5 z-50 bg-gray-800 border border-gray-700 rounded-lg shadow-lg py-1 min-w-[110px]">
            <button
              onClick={handleRename}
              className="w-full text-left px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
            >
              {t("sidebar.rename")}
            </button>
            <button
              onClick={handleDelete}
              className="w-full text-left px-3 py-1.5 text-xs text-red-400 hover:bg-gray-700 hover:text-red-300 transition-colors"
            >
              {t("sidebar.delete")}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
