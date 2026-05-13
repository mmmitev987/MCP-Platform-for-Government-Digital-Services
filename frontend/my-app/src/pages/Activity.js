import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import i18n from "../i18n";
import { getActivity } from "../api/activity";

const LOAD_TIMEOUT_MS = 9000;

function withTimeout(promise, ms) {
  const timeout = new Promise((_, reject) =>
    setTimeout(() => reject(new Error("timeout")), ms)
  );
  return Promise.race([promise, timeout]);
}

const STATUS_KEYS = ["all", "completed", "pending"];

function Badge({ status, t }) {
  const styles = {
    completed: { background: "rgba(34,197,94,0.1)", color: "#16a34a", border: "1px solid rgba(34,197,94,0.2)" },
    pending:   { background: "rgba(234,179,8,0.1)",  color: "#ca8a04", border: "1px solid rgba(234,179,8,0.2)" },
    failed:    { background: "rgba(239,68,68,0.1)",  color: "#dc2626", border: "1px solid rgba(239,68,68,0.2)" },
  };
  const s = styles[status] || styles.pending;
  return (
    <span className="text-xs px-2.5 py-0.5 rounded-full font-medium" style={s}>
      {t(`activity.statuses.${status}`) || status}
    </span>
  );
}

const ACTION_LABELS_MK = {
  uslugi__get_service_requirements: "Барање на услуга",
  uslugi__search_services:          "Пребарување услуги",
  uslugi__list_all_services:        "Листа на услуги",
  mojtermin__get_doctors_by_city:   "Пребарување лекари",
  mojtermin__book_appointment:      "Закажување термин",
  mojtermin__cancel_appointment:    "Откажување термин",
  crm__search_company:              "Пребарување компанија",
  crm__get_company_details:         "Детали за компанија",
  mon__get_info:                    "Информации за образование",
};

const ACTION_LABELS_EN = {
  uslugi__get_service_requirements: "Service request",
  uslugi__search_services:          "Search services",
  uslugi__list_all_services:        "List all services",
  mojtermin__get_doctors_by_city:   "Search doctors",
  mojtermin__book_appointment:      "Book appointment",
  mojtermin__cancel_appointment:    "Cancel appointment",
  crm__search_company:              "Search company",
  crm__get_company_details:         "Company details",
  mon__get_info:                    "Education info",
};

const INST_NAMES = {
  uslugi:    "uslugi.gov.mk",
  mojtermin: "Мој Термин",
  crm:       "Централен регистар",
  mon:       "МОН",
};

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
        setLoadError(err.message === "timeout" ? "timeout" : "error");
      });
  }, [status, page]);

  const totalPages = Math.ceil(data.total / limit);

  const getInstName = (service) => {
    const key = Object.keys(INST_NAMES).find(k => service?.toLowerCase().includes(k));
    return key ? INST_NAMES[key] : service;
  };

  const getActionLabel = (action) => {
    const lang = i18n.language || "mk";
    const labels = lang === "en" ? ACTION_LABELS_EN : ACTION_LABELS_MK;
    return labels[action] || action;
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold" style={{ color: "#1e293b" }}>{t("activity.title")}</h2>
        <p className="mt-1 text-sm" style={{ color: "#94a3b8" }}>{t("activity.subtitle")}</p>
      </div>

      {/* Error */}
      {loadError && (
        <div className="mb-4 px-4 py-3 rounded-xl text-sm"
          style={{ background: "rgba(239,68,68,0.07)", border: "1px solid rgba(239,68,68,0.2)", color: "#dc2626" }}>
          {loadError === "timeout"
            ? "Активноста одзеде премногу долго. Обидете се повторно."
            : "Неуспешно вчитување. Обидете се повторно."}
        </div>
      )}

      {/* Filter tabs + total */}
      <div className="flex flex-wrap items-center gap-2 mb-6">
        {STATUS_KEYS.map((s) => (
          <button
            key={s}
            onClick={() => { setStatus(s); setPage(1); }}
            className="px-4 py-1.5 rounded-xl text-sm font-medium transition-all"
            style={status === s
              ? { background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#ffffff", boxShadow: "0 2px 10px rgba(99,102,241,0.3)" }
              : { background: "#ffffff", color: "#64748b", border: "1px solid rgba(99,102,241,0.15)" }}
          >
            {t(`activity.statuses.${s}`)}
          </button>
        ))}
        <span className="ml-auto text-sm font-medium" style={{ color: "#94a3b8" }}>
          <span style={{ color: "#6366f1", fontWeight: 800, fontSize: "1.25rem" }}>{data.total}</span> {t("activity.total")}
        </span>
      </div>

      {/* Table */}
      <div className="rounded-2xl overflow-hidden"
        style={{ background: "#ffffff", border: "1px solid rgba(99,102,241,0.12)", boxShadow: "0 2px 16px rgba(99,102,241,0.07)" }}>
        {data.items.length === 0 ? (
          <div className="px-6 py-20 text-center text-sm" style={{ color: "#94a3b8" }}>
            {t("activity.noActivity")}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[540px]">
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(99,102,241,0.08)" }}>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold uppercase tracking-wide" style={{ color: "#94a3b8" }}>{t("activity.service")}</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold uppercase tracking-wide hidden sm:table-cell" style={{ color: "#94a3b8" }}>{t("activity.action")}</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold uppercase tracking-wide" style={{ color: "#94a3b8" }}>{t("activity.status")}</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold uppercase tracking-wide hidden md:table-cell" style={{ color: "#94a3b8" }}>{t("activity.description")}</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold uppercase tracking-wide" style={{ color: "#94a3b8" }}>{t("activity.date")}</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((a, idx) => (
                  <tr key={a.id}
                    style={{ borderBottom: idx < data.items.length - 1 ? "1px solid rgba(99,102,241,0.06)" : "none" }}
                    onMouseEnter={e => e.currentTarget.style.background = "rgba(99,102,241,0.03)"}
                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                  >
                    <td className="px-5 py-3.5 text-sm font-semibold" style={{ color: "#1e293b" }}>
                      {getInstName(a.service)}
                    </td>
                    <td className="px-5 py-3.5 text-sm hidden sm:table-cell" style={{ color: "#64748b" }}>
                      {getActionLabel(a.action)}
                    </td>
                    <td className="px-5 py-3.5">
                      <Badge status={a.status} t={t} />
                    </td>
                    <td className="px-5 py-3.5 text-xs max-w-xs truncate hidden md:table-cell" style={{ color: "#94a3b8" }}>
                      {(() => {
                        const raw = a.description;
                        if (!raw) return "—";
                        try {
                          const parsed = JSON.parse(raw);
                          if (parsed.doctor) return `Д-р ${parsed.doctor}${parsed.clinic ? `, ${parsed.clinic}` : ""}`;
                          if (parsed.municipality?.name) return parsed.municipality.name;
                          const first = parsed.name || parsed.title || Object.values(parsed)[0];
                          return typeof first === "string" ? first : "—";
                        } catch {
                          const m = raw.match(/"name"\s*:\s*"([^"]+)"/);
                          if (m) return m[1];
                          const d = raw.match(/"doctor"\s*:\s*"([^"]+)"/);
                          const c = raw.match(/"clinic"\s*:\s*"([^"]+)"/);
                          if (d) return `Д-р ${d[1]}${c ? `, ${c[1]}` : ""}`;
                          const plain = raw.replace(/^\d+\s*[—-]+\s*/, "");
                          return plain || "—";
                        }
                      })()}
                    </td>
                    <td className="px-5 py-3.5 text-xs whitespace-nowrap" style={{ color: "#94a3b8" }}>
                      {new Date(a.created_at).toLocaleString("mk-MK")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 mt-6">
          <button
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
            className="px-4 py-1.5 text-sm rounded-xl font-medium transition-all disabled:opacity-40"
            style={{ background: "#ffffff", border: "1px solid rgba(99,102,241,0.2)", color: "#6366f1" }}
            onMouseEnter={e => { if (!e.currentTarget.disabled) e.currentTarget.style.background = "rgba(99,102,241,0.07)"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "#ffffff"; }}
          >
            {t("activity.previous")}
          </button>
          <span className="text-sm" style={{ color: "#94a3b8" }}>
            {t("activity.page", { page, total: totalPages })}
          </span>
          <button
            disabled={page === totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="px-4 py-1.5 text-sm rounded-xl font-medium transition-all disabled:opacity-40"
            style={{ background: "#ffffff", border: "1px solid rgba(99,102,241,0.2)", color: "#6366f1" }}
            onMouseEnter={e => { if (!e.currentTarget.disabled) e.currentTarget.style.background = "rgba(99,102,241,0.07)"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "#ffffff"; }}
          >
            {t("activity.next")}
          </button>
        </div>
      )}
    </div>
  );
}
