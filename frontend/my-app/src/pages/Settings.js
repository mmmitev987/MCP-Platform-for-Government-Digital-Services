import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useAuth } from "../contexts/AuthContext";
import { getSettings, updateSettings, changeEmail, changePassword, deleteAccount } from "../api/settings";
import i18n from "../i18n";
import { LANGUAGES } from "../locales/index";

const inputCls =
  "w-full bg-gray-800 border border-gray-700 text-white text-sm rounded-lg px-4 py-3 outline-none focus:border-indigo-500 transition-colors placeholder-gray-500";

function StatusMsg({ status }) {
  if (!status) return null;
  return (
    <p className={`text-xs mt-1 ${status.type === "error" ? "text-red-400" : "text-green-400"}`}>
      {status.msg}
    </p>
  );
}

export default function Settings() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();

  // Profile form
  const [form, setForm] = useState({ full_name: "", language: "en", notifications: true });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Change email form
  const [emailForm, setEmailForm] = useState({ current_password: "", new_email: "" });
  const [emailStatus, setEmailStatus] = useState(null);
  const [emailLoading, setEmailLoading] = useState(false);

  // Change password form
  const [pwForm, setPwForm] = useState({ current_password: "", new_password: "", confirm: "" });
  const [pwStatus, setPwStatus] = useState(null);
  const [pwLoading, setPwLoading] = useState(false);

  // Delete account
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
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    setEmailLoading(true);
    setEmailStatus(null);
    try {
      await changeEmail(emailForm.current_password, emailForm.new_email);
      setEmailStatus({ type: "ok", msg: t("settings.emailUpdated") });
      setEmailForm({ current_password: "", new_email: "" });
      setTimeout(() => logout(), 1500);
    } catch (err) {
      setEmailStatus({ type: "error", msg: err?.response?.data?.detail || t("settings.emailFailed") });
    } finally {
      setEmailLoading(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (pwForm.new_password !== pwForm.confirm) {
      setPwStatus({ type: "error", msg: t("settings.passwordMismatch") });
      return;
    }
    setPwLoading(true);
    setPwStatus(null);
    try {
      await changePassword(pwForm.current_password, pwForm.new_password);
      setPwStatus({ type: "ok", msg: t("settings.passwordUpdated") });
      setPwForm({ current_password: "", new_password: "", confirm: "" });
    } catch (err) {
      setPwStatus({ type: "error", msg: err?.response?.data?.detail || t("settings.passwordFailed") });
    } finally {
      setPwLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    setDeleteLoading(true);
    setDeleteStatus(null);
    try {
      await deleteAccount(deletePassword);
      logout();
    } catch (err) {
      setDeleteStatus({ type: "error", msg: err?.response?.data?.detail || t("settings.deleteFailed") });
      setDeleteLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-2xl space-y-6">
      <div className="mb-2">
        <h2 className="text-2xl font-bold text-white">{t("settings.title")}</h2>
        <p className="text-gray-400 mt-1">{t("settings.subtitle")}</p>
      </div>

      {/* ── Avatar + identity ── */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 flex items-center gap-4">
        <div className="w-14 h-14 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xl font-bold shrink-0">
          {user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || "U"}
        </div>
        <div className="min-w-0">
          <p className="text-white font-semibold truncate">{user?.full_name || "—"}</p>
          <p className="text-gray-400 text-sm truncate">{user?.email}</p>
        </div>
      </div>

      {/* ── Profile (name + language + notifications) ── */}
      <form onSubmit={handleSave} className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-5">
        <h3 className="text-white font-semibold">{t("settings.profile")}</h3>

        <div>
          <label className="block text-sm text-gray-400 mb-1">{t("settings.fullName")}</label>
          <input
            type="text"
            value={form.full_name}
            onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
            className={inputCls}
          />
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-2">{t("settings.language")}</label>
          <div className="flex gap-3">
            {LANGUAGES.map(({ code, label }) => (
              <button
                type="button"
                key={code}
                onClick={() => setForm((f) => ({ ...f, language: code }))}
                className={`flex-1 py-2.5 rounded-lg border text-sm font-medium transition-colors ${
                  form.language === code
                    ? "bg-indigo-600 border-indigo-600 text-white"
                    : "border-gray-700 text-gray-400 hover:text-white hover:border-gray-600"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between py-1">
          <div>
            <p className="text-sm text-white">{t("settings.notifications")}</p>
            <p className="text-xs text-gray-500">{t("settings.notificationsDesc")}</p>
          </div>
          <button
            type="button"
            onClick={() => setForm((f) => ({ ...f, notifications: !f.notifications }))}
            className={`relative w-11 h-6 rounded-full transition-colors ${
              form.notifications ? "bg-indigo-600" : "bg-gray-700"
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                form.notifications ? "translate-x-5" : "translate-x-0"
              }`}
            />
          </button>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium py-3 rounded-xl transition-colors"
        >
          {saving ? t("settings.saving") : saved ? t("settings.saved") : t("settings.saveChanges")}
        </button>
      </form>

      {/* ── Change Email ── */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-white font-semibold mb-4">{t("settings.changeEmail")}</h3>
        <form onSubmit={handleEmailSubmit} className="space-y-3">
          <div>
            <label className="block text-sm text-gray-400 mb-1">{t("settings.currentPassword")}</label>
            <input
              required
              type="password"
              placeholder={t("settings.enterCurrentPassword")}
              value={emailForm.current_password}
              onChange={(e) => setEmailForm((f) => ({ ...f, current_password: e.target.value }))}
              className={inputCls}
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">{t("settings.newEmail")}</label>
            <input
              required
              type="email"
              placeholder={t("settings.enterNewEmail")}
              value={emailForm.new_email}
              onChange={(e) => setEmailForm((f) => ({ ...f, new_email: e.target.value }))}
              className={inputCls}
            />
          </div>
          <StatusMsg status={emailStatus} />
          <button
            type="submit"
            disabled={emailLoading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-3 rounded-xl transition-colors disabled:opacity-50"
          >
            {emailLoading ? t("settings.updating") : t("settings.updateEmail")}
          </button>
        </form>
      </div>

      {/* ── Change Password ── */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-white font-semibold mb-4">{t("settings.changePassword")}</h3>
        <form onSubmit={handlePasswordSubmit} className="space-y-3">
          <div>
            <label className="block text-sm text-gray-400 mb-1">{t("settings.currentPassword")}</label>
            <input
              required
              type="password"
              placeholder={t("settings.enterCurrentPassword")}
              value={pwForm.current_password}
              onChange={(e) => setPwForm((f) => ({ ...f, current_password: e.target.value }))}
              className={inputCls}
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">{t("settings.newPassword")}</label>
            <input
              required
              type="password"
              placeholder={t("settings.enterNewPassword")}
              value={pwForm.new_password}
              onChange={(e) => setPwForm((f) => ({ ...f, new_password: e.target.value }))}
              className={inputCls}
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">{t("settings.confirmPassword")}</label>
            <input
              required
              type="password"
              placeholder={t("settings.repeatNewPassword")}
              value={pwForm.confirm}
              onChange={(e) => setPwForm((f) => ({ ...f, confirm: e.target.value }))}
              className={inputCls}
            />
          </div>
          <StatusMsg status={pwStatus} />
          <button
            type="submit"
            disabled={pwLoading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-3 rounded-xl transition-colors disabled:opacity-50"
          >
            {pwLoading ? t("settings.updating") : t("settings.updatePassword")}
          </button>
        </form>
      </div>

      {/* ── Delete Account ── */}
      <div className="bg-gray-900 border border-red-900/50 rounded-xl p-6">
        <h3 className="text-red-400 font-semibold mb-1">{t("settings.deleteAccount")}</h3>
        <p className="text-gray-500 text-sm mb-4">{t("settings.deleteAccountDesc")}</p>
        {!confirmDelete ? (
          <button
            onClick={() => setConfirmDelete(true)}
            className="w-full border border-red-800 text-red-400 hover:bg-red-900/20 font-medium py-3 rounded-xl transition-colors"
          >
            {t("settings.deleteMyAccount")}
          </button>
        ) : (
          <div className="space-y-3">
            <div>
              <label className="block text-sm text-gray-400 mb-1">{t("settings.enterPasswordToConfirm")}</label>
              <input
                type="password"
                placeholder={t("settings.yourPassword")}
                value={deletePassword}
                onChange={(e) => setDeletePassword(e.target.value)}
                className={inputCls}
              />
            </div>
            <StatusMsg status={deleteStatus} />
            <div className="flex gap-3">
              <button
                onClick={() => { setConfirmDelete(false); setDeletePassword(""); setDeleteStatus(null); }}
                className="flex-1 border border-gray-700 text-gray-400 hover:text-white font-medium py-3 rounded-xl transition-colors"
              >
                {t("settings.cancel")}
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deleteLoading || !deletePassword}
                className="flex-1 bg-red-700 hover:bg-red-600 text-white font-medium py-3 rounded-xl transition-colors disabled:opacity-50"
              >
                {deleteLoading ? t("settings.deleting") : t("settings.confirmDelete")}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
