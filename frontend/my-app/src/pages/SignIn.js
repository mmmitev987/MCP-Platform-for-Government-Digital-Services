import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { login, register } from "../api/auth";
import { useAuth } from "../contexts/AuthContext";

export default function SignIn() {
  const { t } = useTranslation();
  const { login: authLogin } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "", password: "", full_name: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const fn = mode === "login" ? login : register;
      const { access_token } = await fn(form);
      await authLogin(access_token);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">Gov<span className="text-indigo-400">MCP</span></h1>
          <p className="text-gray-400 mt-2 text-sm">{t("auth.subtitle")}</p>
        </div>

        <div className="bg-gray-900 rounded-2xl border border-gray-800 p-8">
          <div className="flex rounded-lg bg-gray-800 p-1 mb-6">
            {["login", "register"].map((m) => (
              <button
                key={m}
                onClick={() => { setMode(m); setError(""); }}
                className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                  mode === m ? "bg-indigo-600 text-white" : "text-gray-400 hover:text-white"
                }`}
              >
                {m === "login" ? t("auth.signIn") : t("auth.register")}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "register" && (
              <div>
                <label className="block text-sm text-gray-400 mb-1">{t("auth.fullName")}</label>
                <input
                  type="text"
                  value={form.full_name}
                  onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
                  placeholder="Jane Doe"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>
            )}
            <div>
              <label className="block text-sm text-gray-400 mb-1">{t("auth.email")}</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                placeholder="you@example.com"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">{t("auth.password")}</label>
              <input
                type="password"
                required
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                placeholder="••••••••"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>

            {error && (
              <p className="text-red-400 text-sm bg-red-950 border border-red-900 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium py-3 rounded-lg transition-colors"
            >
              {loading ? t("auth.pleaseWait") : mode === "login" ? t("auth.signIn") : t("auth.createAccount")}
            </button>

            {mode === "login" && (
              <Link
                to="/forgot-password"
                className="block text-center text-gray-500 hover:text-gray-300 text-sm transition-colors"
              >
                {t("auth.forgotPassword")}
              </Link>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
