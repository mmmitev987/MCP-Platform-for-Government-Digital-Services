import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getActivity } from "../api/activity";

const LOAD_TIMEOUT_MS = 9000;

function withTimeout(promise, ms) {
  const timeout = new Promise((_, reject) =>
    setTimeout(() => reject(new Error("timeout")), ms)
  );
  return Promise.race([promise, timeout]);
}

const STATUS_KEYS = ["all", "completed", "pending", "failed"];

function Badge({ status }) {
  const colors = {
    completed: "text-green-400 bg-green-950 border-green-900",
    pending: "text-yellow-400 bg-yellow-950 border-yellow-900",
    failed: "text-red-400 bg-red-950 border-red-900",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize ${colors[status] || colors.pending}`}>
      {status}
    </span>
  );
}

export default function Activity() {
  const { t } = useTranslation();
  const [data, setData] = useState({ items: [], total: 0 });
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(1);
  const [loadError, setLoadError] = useState(null);
  const limit = 15;

  useEffect(() => {
    setLoadError(null);
    const params = { page, limit };
    if (status !== "all") params.status = status;
    withTimeout(getActivity(params), LOAD_TIMEOUT_MS)
      .then(setData)
      .catch((err) => {
        if (err.message === "timeout") {
          setLoadError("activity_timeout");
        } else {
          setLoadError("activity_error");
        }
      });
  }, [status, page]);

  const totalPages = Math.ceil(data.total / limit);

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-6 lg:mb-8">
        <h2 className="text-2xl font-bold text-white">{t("activity.title")}</h2>
        <p className="text-gray-400 mt-1">{t("activity.subtitle")}</p>
      </div>

      {loadError && (
        <div className="mb-4 px-4 py-3 bg-red-950 border border-red-800 rounded-lg text-red-400 text-sm">
          {loadError === "activity_timeout"
            ? "⏱️ Activity took too long to load. Please try again."
            : "Failed to load activity. Please try again."}
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {STATUS_KEYS.map((s) => (
          <button
            key={s}
            onClick={() => { setStatus(s); setPage(1); }}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              status === s
                ? "bg-indigo-600 text-white"
                : "bg-gray-800 text-gray-400 hover:text-white border border-gray-700"
            }`}
          >
            {t(`activity.statuses.${s}`)}
          </button>
        ))}
        <span className="ml-auto text-sm text-gray-500 self-center">
          {data.total} {t("activity.total")}
        </span>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        {data.items.length === 0 ? (
          <div className="px-6 py-16 text-center text-gray-500 text-sm">
            {t("activity.noActivity")}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[540px]">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left px-4 sm:px-6 py-3 text-xs text-gray-500 font-medium">{t("activity.service")}</th>
                  <th className="text-left px-4 sm:px-6 py-3 text-xs text-gray-500 font-medium hidden sm:table-cell">{t("activity.action")}</th>
                  <th className="text-left px-4 sm:px-6 py-3 text-xs text-gray-500 font-medium">{t("activity.status")}</th>
                  <th className="text-left px-4 sm:px-6 py-3 text-xs text-gray-500 font-medium hidden md:table-cell">{t("activity.description")}</th>
                  <th className="text-left px-4 sm:px-6 py-3 text-xs text-gray-500 font-medium">{t("activity.date")}</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((a) => (
                  <tr key={a.id} className="border-b border-gray-800 last:border-0 hover:bg-gray-800/50">
                    <td className="px-4 sm:px-6 py-3 text-sm text-white font-medium capitalize">{a.service}</td>
                    <td className="px-4 sm:px-6 py-3 text-xs text-gray-400 font-mono hidden sm:table-cell">{a.action}</td>
                    <td className="px-4 sm:px-6 py-3"><Badge status={a.status} /></td>
                    <td className="px-4 sm:px-6 py-3 text-xs text-gray-500 max-w-xs truncate hidden md:table-cell">{a.description || "—"}</td>
                    <td className="px-4 sm:px-6 py-3 text-xs text-gray-500 whitespace-nowrap">
                      {new Date(a.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <button
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
            className="px-3 py-1.5 text-sm text-gray-400 border border-gray-700 rounded-lg disabled:opacity-40 hover:text-white hover:border-gray-600 transition-colors"
          >
            {t("activity.previous")}
          </button>
          <span className="text-sm text-gray-400">
            {t("activity.page", { page, total: totalPages })}
          </span>
          <button
            disabled={page === totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="px-3 py-1.5 text-sm text-gray-400 border border-gray-700 rounded-lg disabled:opacity-40 hover:text-white hover:border-gray-600 transition-colors"
          >
            {t("activity.next")}
          </button>
        </div>
      )}
    </div>
  );
}
