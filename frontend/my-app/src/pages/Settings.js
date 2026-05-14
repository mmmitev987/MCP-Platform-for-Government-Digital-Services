import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useAuth } from "../contexts/AuthContext";
import { getSettings, updateSettings, changeEmail, changePassword, deleteAccount } from "../api/settings";
import i18n from "../i18n";
import { LANGUAGES } from "../locales/index";

const CARD = {
  background: "#ffffff",
  border: "1px solid rgba(99,102,241,0.12)",
  boxShadow: "0 2px 16px rgba(99,102,241,0.07)",
};

function LightInput({ type = "text", value, onChange, placeholder, required }) {
  return (
    <input
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      required={required}
      className="w-full text-sm rounded-xl px-4 py-2.5 outline-none transition-all"
      style={{ background: "#f8faff", border: "1px solid rgba(99,102,241,0.18)", color: "#1e293b" }}
      onFocus={e => { e.target.style.border = "1px solid rgba(99,102,241,0.5)"; e.target.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.08)"; }}
      onBlur={e => { e.target.style.border = "1px solid rgba(99,102,241,0.18)"; e.target.style.boxShadow = "none"; }}
    />
  );
}

function GradientBtn({ children, disabled, type = "button", onClick }) {
  return (
    <button type={type} disabled={disabled} onClick={onClick}
      className="w-full font-medium py-2.5 rounded-xl text-sm transition-all disabled:opacity-50"
      style={{ background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", boxShadow: "0 2px 10px rgba(99,102,241,0.3)" }}
      onMouseEnter={e => { if (!e.currentTarget.disabled) e.currentTarget.style.boxShadow = "0 4px 16px rgba(99,102,241,0.5)"; }}
      onMouseLeave={e => { e.currentTarget.style.boxShadow = "0 2px 10px rgba(99,102,241,0.3)"; }}>
      {children}
    </button>
  );
}

function StatusMsg({ status }) {
  if (!status) return null;
  return <p className="text-xs mt-1" style={{ color: status.type === "error" ? "#dc2626" : "#16a34a" }}>{status.msg}</p>;
}


export default function Settings() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState("profile");

  const [form, setForm] = useState({ full_name: "", language: "en", notifications: true });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const [emailForm, setEmailForm] = useState({ current_password: "", new_email: "" });
  const [emailStatus, setEmailStatus] = useState(null);
  const [emailLoading, setEmailLoading] = useState(false);

  const [pwForm, setPwForm] = useState({ current_password: "", new_password: "", confirm: "" });
  const [pwStatus, setPwStatus] = useState(null);
  const [pwLoading, setPwLoading] = useState(false);

  const [deletePassword, setDeletePassword] = useState("");
  const [deleteStatus, setDeleteStatus] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    getSettings().then((d) => {
      setForm({ full_name: d.full_name || "", language: d.language, notifications: d.notifications });
      setLoading(false);
    });
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    await updateSettings(form).catch(() => {});
    localStorage.setItem("language", form.language);
    i18n.changeLanguage(form.language);
    setSaving(false); setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleEmailSubmit = async (e) => {
    e.preventDefault(); setEmailLoading(true); setEmailStatus(null);
    try {
      await changeEmail(emailForm.current_password, emailForm.new_email);
      setEmailStatus({ type: "ok", msg: t("settings.emailUpdated") });
      setEmailForm({ current_password: "", new_email: "" });
      setTimeout(() => logout(), 1500);
    } catch (err) {
      setEmailStatus({ type: "error", msg: err?.response?.data?.detail || t("settings.emailFailed") });
    } finally { setEmailLoading(false); }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (pwForm.new_password !== pwForm.confirm) { setPwStatus({ type: "error", msg: t("settings.passwordMismatch") }); return; }
    setPwLoading(true); setPwStatus(null);
    try {
      await changePassword(pwForm.current_password, pwForm.new_password);
      setPwStatus({ type: "ok", msg: t("settings.passwordUpdated") });
      setPwForm({ current_password: "", new_password: "", confirm: "" });
    } catch (err) {
      setPwStatus({ type: "error", msg: err?.response?.data?.detail || t("settings.passwordFailed") });
    } finally { setPwLoading(false); }
  };

  const handleDeleteAccount = async () => {
    setDeleteLoading(true); setDeleteStatus(null);
    try { await deleteAccount(deletePassword); logout(); }
    catch (err) {
      setDeleteStatus({ type: "error", msg: err?.response?.data?.detail || t("settings.deleteFailed") });
      setDeleteLoading(false);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-full">
      <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: "#6366f1", borderTopColor: "transparent" }} />
    </div>
  );

  return (
    <div className="h-full flex items-start justify-center p-4 sm:p-6 lg:p-8 pt-6">
      <div className="w-full max-w-6xl">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold" style={{ color: "#1e293b" }}>{t("settings.title")}</h2>
          <p className="mt-1 text-sm" style={{ color: "#94a3b8" }}>{t("settings.subtitle")}</p>
        </div>

        <div className="rounded-2xl overflow-hidden flex" style={{ ...CARD, minHeight: "520px" }}>
          {/* Left panel */}
          <div className="w-72 shrink-0 flex flex-col" style={{ borderRight: "1px solid rgba(99,102,241,0.1)", background: "#fafbff" }}>
            {/* Avatar */}
            <div className="p-5 flex flex-col items-center text-center" style={{ borderBottom: "1px solid rgba(99,102,241,0.1)" }}>
              <div className="w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl font-bold mb-3"
                style={{ background: "linear-gradient(135deg,#6366f1,#8b5cf6)", boxShadow: "0 2px 12px rgba(99,102,241,0.4)" }}>
                {user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || "U"}
              </div>
              <p className="font-bold text-sm leading-tight" style={{ color: "#1e293b" }}>{user?.full_name || "—"}</p>
              <p className="text-xs mt-0.5 truncate w-full" style={{ color: "#94a3b8" }}>{user?.email}</p>
            </div>

            {/* Tab nav */}
            <nav className="p-3 space-y-1 flex-1">
              {[
                { key: "profile",  labelKey: "settings.profile",       path: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" },
                { key: "email",    labelKey: "settings.changeEmail",    path: "M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" },
                { key: "password", labelKey: "settings.changePassword", path: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" },
                { key: "delete",   labelKey: "settings.deleteAccount",  path: "M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" },
              ].map(({ key, labelKey, path }) => (
                <button key={key} onClick={() => setActiveTab(key)}
                  className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-all text-left"
                  style={activeTab === key
                    ? { background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", boxShadow: "0 2px 8px rgba(99,102,241,0.3)" }
                    : { color: key === "delete" ? "#dc2626" : "#64748b" }}
                  onMouseEnter={e => { if (activeTab !== key) e.currentTarget.style.background = key === "delete" ? "rgba(239,68,68,0.06)" : "rgba(99,102,241,0.07)"; }}
                  onMouseLeave={e => { if (activeTab !== key) e.currentTarget.style.background = "transparent"; }}
                >
                  <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d={path} />
                  </svg>
                  {t(labelKey)}
                </button>
              ))}
            </nav>
          </div>

          {/* Right panel */}
          <div className="flex-1 p-10">

            {/* PROFILE TAB */}
            {activeTab === "profile" && (
              <form onSubmit={handleSave} className="space-y-4 h-full flex flex-col">
                <h3 className="font-bold text-base" style={{ color: "#1e293b" }}>{t("settings.profile")}</h3>
                <div>
                  <label className="block text-sm font-medium mb-1.5" style={{ color: "#64748b" }}>{t("settings.fullName")}</label>
                  <LightInput value={form.full_name} onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: "#64748b" }}>{t("settings.language")}</label>
                  <div className="flex gap-3">
                    {LANGUAGES.map(({ code, label }) => (
                      <button type="button" key={code} onClick={() => setForm((f) => ({ ...f, language: code }))}
                        className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-all"
                        style={form.language === code
                          ? { background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", boxShadow: "0 2px 8px rgba(99,102,241,0.3)", border: "none" }
                          : { background: "#f8faff", border: "1px solid rgba(99,102,241,0.18)", color: "#64748b" }}>
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="mt-auto pt-2">
                  <GradientBtn type="submit" disabled={saving}>
                    {saving ? t("settings.saving") : saved ? t("settings.saved") : t("settings.saveChanges")}
                  </GradientBtn>
                </div>
              </form>
            )}

            {/* EMAIL TAB */}
            {activeTab === "email" && (
              <form onSubmit={handleEmailSubmit} className="space-y-4">
                <h3 className="font-bold text-base" style={{ color: "#1e293b" }}>{t("settings.changeEmail")}</h3>
                <div>
                  <label className="block text-sm font-medium mb-1.5" style={{ color: "#64748b" }}>{t("settings.currentPassword")}</label>
                  <LightInput type="password" required placeholder={t("settings.enterCurrentPassword")}
                    value={emailForm.current_password} onChange={(e) => setEmailForm((f) => ({ ...f, current_password: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5" style={{ color: "#64748b" }}>{t("settings.newEmail")}</label>
                  <LightInput type="email" required placeholder={t("settings.enterNewEmail")}
                    value={emailForm.new_email} onChange={(e) => setEmailForm((f) => ({ ...f, new_email: e.target.value }))} />
                </div>
                <StatusMsg status={emailStatus} />
                <GradientBtn type="submit" disabled={emailLoading}>
                  {emailLoading ? t("settings.updating") : t("settings.updateEmail")}
                </GradientBtn>
              </form>
            )}

            {/* PASSWORD TAB */}
            {activeTab === "password" && (
              <form onSubmit={handlePasswordSubmit} className="space-y-4">
                <h3 className="font-bold text-base" style={{ color: "#1e293b" }}>{t("settings.changePassword")}</h3>
                <div>
                  <label className="block text-sm font-medium mb-1.5" style={{ color: "#64748b" }}>{t("settings.currentPassword")}</label>
                  <LightInput type="password" required placeholder={t("settings.enterCurrentPassword")}
                    value={pwForm.current_password} onChange={(e) => setPwForm((f) => ({ ...f, current_password: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5" style={{ color: "#64748b" }}>{t("settings.newPassword")}</label>
                  <LightInput type="password" required placeholder={t("settings.enterNewPassword")}
                    value={pwForm.new_password} onChange={(e) => setPwForm((f) => ({ ...f, new_password: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5" style={{ color: "#64748b" }}>{t("settings.confirmPassword")}</label>
                  <LightInput type="password" required placeholder={t("settings.repeatNewPassword")}
                    value={pwForm.confirm} onChange={(e) => setPwForm((f) => ({ ...f, confirm: e.target.value }))} />
                </div>
                <StatusMsg status={pwStatus} />
                <GradientBtn type="submit" disabled={pwLoading}>
                  {pwLoading ? t("settings.updating") : t("settings.updatePassword")}
                </GradientBtn>
              </form>
            )}

            {/* DELETE TAB */}
            {activeTab === "delete" && (
              <div className="space-y-4">
                <h3 className="font-bold text-base" style={{ color: "#dc2626" }}>{t("settings.deleteAccount")}</h3>
                <p className="text-sm" style={{ color: "#94a3b8" }}>{t("settings.deleteAccountDesc")}</p>
                {!confirmDelete ? (
                  <button onClick={() => setConfirmDelete(true)}
                    className="w-full font-medium py-2.5 rounded-xl text-sm transition-all"
                    style={{ border: "1px solid rgba(239,68,68,0.3)", color: "#dc2626" }}
                    onMouseEnter={e => { e.currentTarget.style.background = "rgba(239,68,68,0.06)"; }}
                    onMouseLeave={e => { e.currentTarget.style.background = "transparent"; }}>
                    {t("settings.deleteMyAccount")}
                  </button>
                ) : (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium mb-1.5" style={{ color: "#64748b" }}>{t("settings.enterPasswordToConfirm")}</label>
                      <LightInput type="password" placeholder={t("settings.yourPassword")}
                        value={deletePassword} onChange={(e) => setDeletePassword(e.target.value)} />
                    </div>
                    <StatusMsg status={deleteStatus} />
                    <div className="flex gap-3">
                      <button onClick={() => { setConfirmDelete(false); setDeletePassword(""); setDeleteStatus(null); }}
                        className="flex-1 font-medium py-2.5 rounded-xl text-sm transition-all"
                        style={{ border: "1px solid rgba(99,102,241,0.2)", color: "#64748b" }}
                        onMouseEnter={e => { e.currentTarget.style.background = "rgba(99,102,241,0.06)"; }}
                        onMouseLeave={e => { e.currentTarget.style.background = "transparent"; }}>
                        {t("settings.cancel")}
                      </button>
                      <button onClick={handleDeleteAccount} disabled={deleteLoading || !deletePassword}
                        className="flex-1 font-medium py-2.5 rounded-xl text-sm text-white transition-all disabled:opacity-50"
                        style={{ background: "#dc2626" }}
                        onMouseEnter={e => { if (!e.currentTarget.disabled) e.currentTarget.style.background = "#b91c1c"; }}
                        onMouseLeave={e => { e.currentTarget.style.background = "#dc2626"; }}>
                        {deleteLoading ? t("settings.deleting") : t("settings.confirmDelete")}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}
