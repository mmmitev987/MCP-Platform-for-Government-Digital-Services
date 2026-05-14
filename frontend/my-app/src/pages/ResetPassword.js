import { useState } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { resetPassword } from "../api/auth";

const PAGE_BG = {
  background: "linear-gradient(180deg, #e8eeff 0%, #f0f4ff 40%, #ffffff 100%)",
  minHeight: "100vh",
};

const CARD_STYLE = {
  background: "#ffffff",
  border: "1px solid rgba(99,102,241,0.15)",
  boxShadow: "0 0 0 1px rgba(99,102,241,0.06), 0 24px 48px rgba(99,102,241,0.12)",
};

const INPUT_STYLE = {
  background: "#f5f7ff",
  border: "1px solid rgba(99,102,241,0.2)",
  width: "100%",
  borderRadius: "0.5rem",
  padding: "0.75rem 1rem",
  color: "#1e293b",
  fontSize: "0.875rem",
  outline: "none",
  transition: "box-shadow 0.15s",
};

const BTN_STYLE = {
  background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
  boxShadow: "0 4px 16px rgba(99,102,241,0.4)",
  width: "100%",
  padding: "0.75rem",
  borderRadius: "0.5rem",
  color: "white",
  fontWeight: "500",
  fontSize: "0.9rem",
  cursor: "pointer",
  border: "none",
  transition: "opacity 0.15s, box-shadow 0.15s",
};

function ShieldIcon() {
  return (
    <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  );
}

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const navigate = useNavigate();

  const [form, setForm] = useState({ new_password: "", confirm: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.new_password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await resetPassword(token, form.new_password);
      setDone(true);
      setTimeout(() => navigate("/signin"), 2500);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const focusInput = (e) => {
    e.target.style.boxShadow = "0 0 0 2px rgba(99,102,241,0.45)";
    e.target.style.borderColor = "rgba(99,102,241,0.6)";
  };
  const blurInput = (e) => {
    e.target.style.boxShadow = "none";
    e.target.style.borderColor = "rgba(99,102,241,0.2)";
  };

  return (
    <div style={PAGE_BG} className="flex items-center justify-center px-4">
      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2.5 mb-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}>
              <ShieldIcon />
            </div>
            <h1 className="text-4xl font-bold tracking-tight" style={{ color: "#1e293b" }}>
              Gov<span style={{ color: "#6366f1" }}>MCP</span>
            </h1>
          </div>
          <p className="text-slate-500 text-sm">Digital Government Services</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl p-8" style={CARD_STYLE}>
          <h2 className="font-semibold text-lg mb-1" style={{ color: "#1e293b" }}>Set a new password</h2>
          <p className="text-slate-500 text-sm mb-6">Choose a strong password for your account.</p>

          {!token && (
            <div className="flex items-start gap-2 rounded-lg px-3 py-2.5 mb-4"
              style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.25)" }}>
              <svg className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-red-500 text-sm">Invalid reset link. Please request a new one.</p>
            </div>
          )}

          {done ? (
            <div className="space-y-4">
              <div className="flex items-start gap-3 rounded-xl px-4 py-3"
                style={{ background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.25)" }}>
                <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-green-600 text-sm">Password updated! Redirecting to Sign In…</p>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-slate-600 mb-1.5">New password</label>
                <input
                  type="password"
                  required
                  disabled={!token}
                  value={form.new_password}
                  onChange={(e) => setForm((f) => ({ ...f, new_password: e.target.value }))}
                  placeholder="••••••••"
                  style={!token ? { ...INPUT_STYLE, opacity: 0.5 } : INPUT_STYLE}
                  onFocus={focusInput}
                  onBlur={blurInput}
                />
              </div>
              <div>
                <label className="block text-sm text-slate-600 mb-1.5">Confirm new password</label>
                <input
                  type="password"
                  required
                  disabled={!token}
                  value={form.confirm}
                  onChange={(e) => setForm((f) => ({ ...f, confirm: e.target.value }))}
                  placeholder="••••••••"
                  style={!token ? { ...INPUT_STYLE, opacity: 0.5 } : INPUT_STYLE}
                  onFocus={focusInput}
                  onBlur={blurInput}
                />
              </div>

              {error && (
                <div className="flex items-start gap-2 rounded-lg px-3 py-2.5"
                  style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.25)" }}>
                  <svg className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-red-500 text-sm">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={loading || !token}
                style={loading || !token ? { ...BTN_STYLE, opacity: 0.5, cursor: "not-allowed", boxShadow: "none" } : BTN_STYLE}
                onMouseEnter={e => { if (!loading && token) e.target.style.boxShadow = "0 6px 20px rgba(99,102,241,0.55)"; }}
                onMouseLeave={e => { if (!loading && token) e.target.style.boxShadow = "0 4px 16px rgba(99,102,241,0.4)"; }}
              >
                {loading ? "Updating…" : "Update Password"}
              </button>

              <Link
                to="/signin"
                className="block text-center text-sm transition-colors"
                style={{ color: "#94a3b8" }}
                onMouseEnter={e => e.target.style.color = "#6366f1"}
                onMouseLeave={e => e.target.style.color = "#94a3b8"}
              >
                ← Back to Sign In
              </Link>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
