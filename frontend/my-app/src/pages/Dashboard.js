import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../contexts/AuthContext";
import { getActivity } from "../api/activity";
import { getInstitutions } from "../api/services";

const ACTION_LABELS_MK = {
  "search services":                    "Пребарување услуги",
  "get group contents":                 "Преглед на група услуги",
  "list all services":                  "Листа на сите услуги",
  "get service requirements":           "Услови за услуга",
  "login":                              "Најава",
  "logout":                             "Одјава",
  "check session":                      "Проверка на сесија",
  "search companies":                   "Пребарување компании",
  "get company details":                "Детали за компанија",
  "get founders and directors":         "Основачи и директори",
  "get annual reports":                 "Годишни извештаи",
  "get locations":                      "Листа на локации",
  "get location by name":               "Пребарување локација",
  "get specialties":                    "Специјалности",
  "get doctors":                        "Листа на лекари",
  "get doctors by city":                "Лекари по град",
  "get available appointments by name": "Слободни термини",
  "check session mon":                  "Проверка на сесија (МОН)",
  "login mon":                          "Најава (МОН)",
  "logout mon":                         "Одјава (МОН)",
  "list mon services":                  "Услуги на МОН",
  "get mon service requirements":       "Услови за услуга (МОН)",
  "list mon document types":            "Типови документи (МОН)",
  "get mon document requirements":      "Услови за документ (МОН)",
};

const ACTION_LABELS_EN = {
  "search services":                    "Search services",
  "get group contents":                 "View service group",
  "list all services":                  "List all services",
  "get service requirements":           "Service requirements",
  "login":                              "Login",
  "logout":                             "Logout",
  "check session":                      "Check session",
  "search companies":                   "Search companies",
  "get company details":                "Company details",
  "get founders and directors":         "Founders & directors",
  "get annual reports":                 "Annual reports",
  "get locations":                      "List locations",
  "get location by name":               "Search location",
  "get specialties":                    "Specialties",
  "get doctors":                        "List doctors",
  "get doctors by city":                "Doctors by city",
  "get available appointments by name": "Available appointments",
  "check session mon":                  "Check session (MOE)",
  "login mon":                          "Login (MOE)",
  "logout mon":                         "Logout (MOE)",
  "list mon services":                  "MOE services",
  "get mon service requirements":       "Service requirements (MOE)",
  "list mon document types":            "Document types (MOE)",
  "get mon document requirements":      "Document requirements (MOE)",
};

const INST_NAMES_MK = {
  uslugi:                 "uslugi.gov.mk",
  mojtermin:              "Мој Термин",
  crm:                    "Централен регистар",
  mon:                    "Министерство за образование",
  katastar:               "Катастар",
  agencijaZaVrabotuvanje: "Агенција за вработување",
};

const INST_NAMES_EN = {
  uslugi:                 "uslugi.gov.mk",
  mojtermin:              "Moj Termin",
  crm:                    "Central Registry",
  mon:                    "Ministry of Education",
  katastar:               "Cadastre",
  agencijaZaVrabotuvanje: "Employment Agency",
};

const INST_DESC_MK = {
  uslugi:                 "Главен портал за административни постапки — пасоши, лични карти, возачки дозволи и повеќе.",
  mojtermin:              "Систем за закажување медицински прегледи — пронајдете лекари и закажете посета.",
  crm:                    "Централен регистар на Северна Македонија — регистрација на компании и деловни услуги.",
  mon:                    "Портал за образовни услуги — пријавување документи, барања и услуги за ученици и студенти.",
  katastar:               "Електронски услуги на Агенција за катастар на недвижности — имотни листови, парцели и згради.",
  agencijaZaVrabotuvanje: "Портал за пребарување огласи за работа, управување со CV и поднесување пријави.",
};

const INST_DESC_EN = {
  uslugi:                 "Main portal for administrative procedures — passports, ID cards, driver's licenses and more.",
  mojtermin:              "Medical appointment scheduling — find doctors and book visits.",
  crm:                    "Central Registry of North Macedonia — company registration and business services.",
  mon:                    "Educational services portal — documents, requests and services for students and pupils.",
  katastar:               "Electronic services of the Real Estate Cadastre Agency — property certificates, parcels and buildings.",
  agencijaZaVrabotuvanje: "Portal for job listings, CV management and submitting job applications.",
};

function Badge({ status, t }) {
  const styles = {
    completed: { background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.25)", color: "#16a34a" },
    pending:   { background: "rgba(234,179,8,0.1)",  border: "1px solid rgba(234,179,8,0.25)",  color: "#ca8a04" },
    failed:    { background: "rgba(239,68,68,0.1)",  border: "1px solid rgba(239,68,68,0.25)",  color: "#dc2626" },
  };
  const s = styles[status] || styles.pending;
  return (
    <span className="text-xs px-2.5 py-0.5 rounded-full font-medium" style={s}>
      {t(`activity.statuses.${status}`) || status}
    </span>
  );
}

const CARD_STYLE = {
  background: "#ffffff",
  border: "1px solid rgba(99,102,241,0.12)",
  boxShadow: "0 2px 12px rgba(99,102,241,0.07)",
};

/* ─── Quick action icons ─── */
function CalendarIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="16" y1="2" x2="16" y2="6" strokeLinecap="round"/>
      <line x1="8" y1="2" x2="8" y2="6" strokeLinecap="round"/>
      <line x1="3" y1="10" x2="21" y2="10" strokeLinecap="round"/>
    </svg>
  );
}
function DocumentIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
    </svg>
  );
}
function ChatIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
    </svg>
  );
}
function ActivityIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
    </svg>
  );
}

/* ─── Institution icons by slug ─── */
const INST_META = {
  "mojtermin":   {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
        <rect x="3" y="4" width="18" height="18" rx="2" strokeLinecap="round" strokeLinejoin="round"/>
        <line x1="16" y1="2" x2="16" y2="6" strokeLinecap="round"/>
        <line x1="8" y1="2" x2="8" y2="6" strokeLinecap="round"/>
        <line x1="3" y1="10" x2="21" y2="10" strokeLinecap="round"/>
      </svg>
    ),
    type: "API",
  },
  "kataster": {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"/>
      </svg>
    ),
    type: "Automation",
  },
  "uslugi": {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
      </svg>
    ),
    type: "API",
  },
  "crm": {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
    ),
    type: "API",
  },
};

function getInstMeta(slug = "") {
  const key = Object.keys(INST_META).find((k) => slug.toLowerCase().includes(k));
  return INST_META[key] || {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
      </svg>
    ),
    type: "API",
  };
}

export default function Dashboard() {
  const { t, i18n } = useTranslation();
  const isMk = i18n.language === "mk";
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activity, setActivity] = useState([]);
  const [institutions, setInstitutions] = useState([]);

  const QUICK_ACTIONS = [
    { labelKey: "actions.bookAppointment", descKey: "actions.bookAppointmentDesc", Icon: CalendarIcon, path: "/assistant", q: isMk ? "Кога има слободни термини кај лекар?" : "When are there available appointment slots with a doctor?", accent: "#6366f1", accentBg: "rgba(99,102,241,0.08)" },
    { labelKey: "actions.checkDocuments",  descKey: "actions.checkDocumentsDesc",  Icon: DocumentIcon, path: "/assistant", q: isMk ? "Кои документи се потребни?" : "What documents are required?", accent: "#0ea5e9", accentBg: "rgba(14,165,233,0.08)" },
    { labelKey: "actions.chats",            descKey: "actions.chatsDesc",           Icon: ChatIcon,     path: "/chats",     q: null, accent: "#8b5cf6", accentBg: "rgba(139,92,246,0.08)" },
    { labelKey: "actions.myActivity",      descKey: "actions.myActivityDesc",      Icon: ActivityIcon, path: "/activity",  q: null, accent: "#10b981", accentBg: "rgba(16,185,129,0.08)" },
  ];

  useEffect(() => {
    getActivity({ limit: 5 }).then((d) => setActivity(d.items)).catch(() => {});
    getInstitutions().then(setInstitutions).catch(() => {});
  }, []);

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return t("dashboard.goodMorning");
    if (h < 18) return t("dashboard.goodAfternoon");
    return t("dashboard.goodEvening");
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">

      {/* Greeting */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold" style={{ color: "#1e293b" }}>
          {greeting()}, <span style={{ color: "#6366f1", fontWeight: 800 }}>{user?.full_name || user?.email?.split("@")[0]}</span>
        </h2>
        <p className="mt-1 text-sm" style={{ color: "#94a3b8" }}>{i18n.language === "en" ? "Your single portal for digital services" : "Ваш единствен портал за дигитални услуги"}</p>
      </div>

      {/* Quick Actions */}
      <section className="mb-8">
        <h3 className="text-xs font-semibold uppercase tracking-wider mb-4" style={{ color: "#94a3b8" }}>
          {t("dashboard.quickActions")}
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {QUICK_ACTIONS.map(({ labelKey, descKey, Icon, path, q, accent, accentBg }) => (
            <button
              key={labelKey}
              onClick={() => navigate(path, q ? { state: { initialMessage: q } } : {})}
              className="rounded-2xl p-5 text-left transition-all duration-200"
              style={CARD_STYLE}
              onMouseEnter={e => {
                e.currentTarget.style.boxShadow = "0 4px 20px rgba(99,102,241,0.18)";
                e.currentTarget.style.borderColor = "rgba(99,102,241,0.35)";
                e.currentTarget.style.transform = "translateY(-2px)";
              }}
              onMouseLeave={e => {
                e.currentTarget.style.boxShadow = "0 2px 12px rgba(99,102,241,0.07)";
                e.currentTarget.style.borderColor = "rgba(99,102,241,0.12)";
                e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4"
                style={{ background: accentBg, color: accent }}>
                <Icon />
              </div>
              <p className="font-semibold text-sm" style={{ color: "#1e293b" }}>
                {t(`dashboard.${labelKey}`)}
              </p>
              <p className="text-xs mt-1" style={{ color: "#94a3b8" }}>
                {t(`dashboard.${descKey}`)}
              </p>
            </button>
          ))}
        </div>
      </section>

      {/* Connected Services + Need Help */}
      <section className="mb-8">
        <div className="flex gap-6 items-stretch flex-col xl:flex-row">

          {/* Connected Services */}
          {institutions.length > 0 && (
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-semibold uppercase tracking-wider" style={{ color: "#94a3b8" }}>
                  {t("dashboard.connectedServices")}
                </h3>
                <button
                  onClick={() => navigate("/services")}
                  className="text-sm font-medium flex items-center gap-1 transition-colors"
                  style={{ color: "#6366f1" }}
                  onMouseEnter={e => e.currentTarget.style.color = "#4f46e5"}
                  onMouseLeave={e => e.currentTarget.style.color = "#6366f1"}
                >
                  {t("dashboard.viewAll")}
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7"/>
                  </svg>
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {institutions.slice(0, 4).map((inst) => {
                  const meta = getInstMeta(inst.slug || inst.name);
                  const slugKey = Object.keys(INST_NAMES_MK).find(k => inst.slug === k || inst.slug?.includes(k)) || "";
                  const instNames = i18n.language === "en" ? INST_NAMES_EN : INST_NAMES_MK;
                  const instDescs = i18n.language === "en" ? INST_DESC_EN : INST_DESC_MK;
                  return (
                    <div key={inst.slug} className="rounded-2xl p-5" style={{ ...CARD_STYLE, opacity: inst.connected ? 1 : 0.55 }}>
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                          style={{ background: "rgba(99,102,241,0.08)", color: "#6366f1" }}>
                          {meta.icon}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap mb-1">
                            <span className="font-semibold text-sm" style={{ color: "#1e293b" }}>{instNames[slugKey] || inst.name}</span>
                            <span className="flex items-center gap-1 text-xs font-medium"
                              style={{ color: inst.connected ? "#16a34a" : "#94a3b8" }}>
                              <span className="w-1.5 h-1.5 rounded-full"
                                style={{ background: inst.connected ? "#16a34a" : "#94a3b8" }} />
                              {inst.connected ? t("services.connected") : t("services.disconnected")}
                            </span>
                          </div>
                          <p className="text-sm" style={{ color: "#64748b" }}>{instDescs[slugKey] || inst.description}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Need Help Banner */}
          <div className="xl:w-80 shrink-0 flex flex-col">
            <h3 className="text-xs font-semibold uppercase tracking-wider mb-4" style={{ color: "#94a3b8" }}>
              &nbsp;
            </h3>
            <div className="flex-1 flex items-center justify-center" style={{ paddingTop: "4%" }}>
              <div className="rounded-2xl p-6 flex flex-col gap-4 w-full"
                style={{ background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)", boxShadow: "0 4px 24px rgba(99,102,241,0.35)" }}>
                <div>
                  <p className="font-bold text-xl text-white mb-1">{i18n.language === "en" ? "Need help?" : "Ви треба помош?"}</p>
                  <p className="text-sm leading-relaxed" style={{ color: "rgba(255,255,255,0.75)" }}>
                    {i18n.language === "en" ? "Ask our AI assistant." : "Прашајте го нашиот AI асистент."}
                  </p>
                </div>
                <button
                  onClick={() => navigate("/assistant")}
                  className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-sm transition-all duration-200"
                  style={{ background: "#ffffff", color: "#6366f1" }}
                  onMouseEnter={e => { e.currentTarget.style.background = "#f5f3ff"; e.currentTarget.style.transform = "translateY(-1px)"; }}
                  onMouseLeave={e => { e.currentTarget.style.background = "#ffffff"; e.currentTarget.style.transform = "translateY(0)"; }}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                  </svg>
                  {i18n.language === "en" ? "Open AI Assistant" : "Отвори AI Асистент"}
                </button>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* Recent Activity */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider" style={{ color: "#94a3b8" }}>
            {t("dashboard.recentActivity")}
          </h3>
          <button
            onClick={() => navigate("/activity")}
            className="text-sm font-medium flex items-center gap-1 transition-colors"
            style={{ color: "#6366f1" }}
            onMouseEnter={e => e.currentTarget.style.color = "#4f46e5"}
            onMouseLeave={e => e.currentTarget.style.color = "#6366f1"}
          >
            {t("dashboard.viewAll")}
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7"/>
            </svg>
          </button>
        </div>

        <div className="rounded-2xl overflow-hidden" style={CARD_STYLE}>
          {activity.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <div className="w-12 h-12 rounded-2xl mx-auto mb-3 flex items-center justify-center"
                style={{ background: "rgba(99,102,241,0.08)", color: "#6366f1" }}>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                </svg>
              </div>
              <p className="text-sm font-medium" style={{ color: "#1e293b" }}>{t("dashboard.noActivity")}</p>
              <p className="text-xs mt-1" style={{ color: "#94a3b8" }}>{t("dashboard.noActivityHint")}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[480px]">
                <thead>
                  <tr style={{ borderBottom: "1px solid rgba(99,102,241,0.1)" }}>
                    <th className="text-left px-6 py-3 text-xs font-semibold" style={{ color: "#94a3b8" }}>{t("activity.service")}</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold hidden sm:table-cell" style={{ color: "#94a3b8" }}>{t("activity.action")}</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold" style={{ color: "#94a3b8" }}>{t("dashboard.status")}</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold" style={{ color: "#94a3b8" }}>{t("dashboard.date")}</th>
                  </tr>
                </thead>
                <tbody>
                  {activity.map((a) => (
                    <tr key={a.id} className="transition-colors"
                      style={{ borderBottom: "1px solid rgba(99,102,241,0.07)" }}
                      onMouseEnter={e => e.currentTarget.style.background = "rgba(99,102,241,0.03)"}
                      onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                      <td className="px-6 py-3 text-sm font-medium" style={{ color: "#1e293b" }}>{(i18n.language === "en" ? INST_NAMES_EN : INST_NAMES_MK)[a.service] || a.service}</td>
                      <td className="px-6 py-3 text-sm hidden sm:table-cell" style={{ color: "#64748b" }}>{(() => {
                          const parts = a.action.split("__");
                          const action = parts[parts.length - 1].replace(/_/g, " ");
                          const labels = i18n.language === "en" ? ACTION_LABELS_EN : ACTION_LABELS_MK;
                          return labels[action] || (action.charAt(0).toUpperCase() + action.slice(1));
                        })()}</td>
                      <td className="px-6 py-3"><Badge status={a.status} t={t} /></td>
                      <td className="px-6 py-3 text-xs whitespace-nowrap" style={{ color: "#94a3b8" }}>{new Date(a.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
