import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import i18n from "../i18n";
import { getInstitutions, connectInstitution, disconnectInstitution } from "../api/services";
import InstitutionModal from "../components/services/InstitutionModal";

const CARD_STYLE = {
  background: "#ffffff",
  border: "1px solid rgba(99,102,241,0.12)",
  boxShadow: "0 2px 16px rgba(99,102,241,0.08)",
};

const INST_ICONS = {
  uslugi: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
    </svg>
  ),
  mojtermin: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <rect x="3" y="4" width="18" height="18" rx="2" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="16" y1="2" x2="16" y2="6" strokeLinecap="round"/>
      <line x1="8" y1="2" x2="8" y2="6" strokeLinecap="round"/>
      <line x1="3" y1="10" x2="21" y2="10" strokeLinecap="round"/>
    </svg>
  ),
  crm: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>
  ),
  mon: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 14l9-5-9-5-9 5 9 5z"/>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z"/>
    </svg>
  ),
  katastar: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
    </svg>
  ),
  agencijaZaVrabotuvanje: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
    </svg>
  ),
};

function DefaultIcon() {
  return (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.1-1.1m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
    </svg>
  );
}

const INST_ACTIONS_MK = {
  mojtermin:               ["Закажи лекар", "Откажи термин", "Преглед на термини"],
  uslugi:                  ["Обнова на пасош", "Лична карта", "Возачка дозвола"],
  crm:                     ["Регистрација на фирма", "Тековна состојба", "Брисање од регистар"],
  mon:                     ["Нострификација", "Државна матура", "Упис во училиште"],
  katastar:                ["Имотен лист", "Пребарај парцела", "Преглед на згради"],
  agencijaZaVrabotuvanje:  ["Огласи за работа", "Управување со CV", "Поднеси пријава"],
};

const INST_ACTIONS_EN = {
  mojtermin:               ["Book doctor", "Cancel appointment", "View appointments"],
  uslugi:                  ["Passport renewal", "ID card", "Driver's license"],
  crm:                     ["Register company", "Current status", "Deregister company"],
  mon:                     ["Nostrification", "State exam", "School enrollment"],
  katastar:                ["Property certificate", "Search parcel", "View buildings"],
  agencijaZaVrabotuvanje:  ["Job listings", "Manage CV", "Submit application"],
};

const INST_META_MK = {
  uslugi:                  { name: "uslugi.gov.mk",               description: "Главен портал за административни постапки — пасоши, лични карти, возачки дозволи и повеќе." },
  mojtermin:               { name: "Мој Термин",                  description: "Систем за закажување медицински прегледи — пронајдете лекари, проверете слободни термини и закажете посета." },
  crm:                     { name: "Централен регистар",           description: "Централен регистар на Северна Македонија — регистрација на компании и деловни услуги." },
  mon:                     { name: "Министерство за образование",  description: "Портал за образовни услуги — пријавување документи, барања и услуги за ученици и студенти." },
  katastar:                { name: "Катастар",                    description: "Електронски услуги на Агенција за катастар на недвижности — имотни листови, парцели и згради." },
  agencijaZaVrabotuvanje:  { name: "Агенција за вработување",     description: "Портал за пребарување огласи за работа, управување со CV и поднесување пријави." },
};

const INST_META_EN = {
  uslugi:                  { name: "uslugi.gov.mk",               description: "Main portal for administrative procedures — passports, ID cards, driver's licenses and more." },
  mojtermin:               { name: "Moj Termin",                  description: "Medical appointment scheduling system — find doctors, check available slots and book visits." },
  crm:                     { name: "Central Registry",            description: "Central Registry of North Macedonia — company registration and business services." },
  mon:                     { name: "Ministry of Education",       description: "Educational services portal — submit documents, requests and services for students and pupils." },
  katastar:                { name: "Cadastre",                    description: "Electronic services of the Real Estate Cadastre Agency — property certificates, parcels and buildings." },
  agencijaZaVrabotuvanje:  { name: "Employment Agency",           description: "Portal for job listings, CV management and submitting job applications — av.gov.mk." },
};

export default function Services() {
  const { t } = useTranslation();
  const [institutions, setInstitutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(null);
  const [detailInstitution, setDetailInstitution] = useState(null);

  useEffect(() => {
    getInstitutions().then(setInstitutions).finally(() => setLoading(false));
  }, []);

  const toggle = async (inst) => {
    setToggling(inst.slug);
    try {
      const updated = inst.connected
        ? await disconnectInstitution(inst.slug)
        : await connectInstitution(inst.slug);
      setInstitutions((prev) =>
        prev.map((i) => (i.slug === inst.slug ? { ...i, connected: updated.connected } : i))
      );
    } finally {
      setToggling(null);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold" style={{ color: "#1e293b" }}>{t("services.title")}</h2>
        <p className="mt-1 text-sm" style={{ color: "#94a3b8" }}>{t("services.subtitle")}</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="rounded-2xl animate-pulse" style={{ background: "rgba(99,102,241,0.06)", height: "360px" }} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5">
          {institutions.map((inst) => {
            const slugKey = Object.keys(INST_ICONS).find(k => inst.slug === k || inst.slug.includes(k)) || "";
            const icon = INST_ICONS[slugKey] || <DefaultIcon />;
            const INST_ACTIONS = i18n.language === "en" ? INST_ACTIONS_EN : INST_ACTIONS_MK;
            const actions = INST_ACTIONS[slugKey] || [];
            const INST_META = i18n.language === "en" ? INST_META_EN : INST_META_MK;
            const meta = INST_META[slugKey] || { name: inst.name, description: inst.description };

            return (
              <div
                key={inst.slug}
                className="rounded-2xl flex flex-col transition-all duration-200"
                style={{ ...CARD_STYLE, opacity: inst.connected ? 1 : 0.65, minHeight: "360px" }}
              >
                {/* Top: icon + arrow */}
                <div className="px-5 pt-5 flex items-start justify-between">
                  <div className="w-12 h-12 rounded-2xl flex items-center justify-center"
                    style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#ffffff" }}>
                    {icon}
                  </div>
                  <button
                    onClick={() => setDetailInstitution(inst)}
                    className="w-8 h-8 rounded-full flex items-center justify-center transition-all"
                    style={{ background: "rgba(99,102,241,0.07)", color: "#6366f1" }}
                    onMouseEnter={e => { e.currentTarget.style.background = "rgba(99,102,241,0.15)"; }}
                    onMouseLeave={e => { e.currentTarget.style.background = "rgba(99,102,241,0.07)"; }}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7"/>
                    </svg>
                  </button>
                </div>

                {/* Title + description */}
                <div className="px-5 pt-4 flex-1">
                  <h3 className="font-bold text-base mb-1" style={{ color: "#1e293b" }}>{meta.name}</h3>
                  <p className="text-sm leading-relaxed" style={{ color: "#64748b" }}>{meta.description}</p>
                </div>

                {/* Available actions */}
                {actions.length > 0 && (
                  <div className="px-5 pt-4">
                    <p className="text-xs font-medium mb-2" style={{ color: "#94a3b8" }}>{t("services.availableServices")}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {actions.map(action => (
                        <span key={action} className="text-xs px-2.5 py-1 rounded-lg"
                          style={{ background: "#f8faff", border: "1px solid rgba(99,102,241,0.15)", color: "#475569" }}>
                          {action}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Footer buttons */}
                <div className="px-5 py-4 mt-3 flex items-center gap-2"
                  style={{ borderTop: "1px solid rgba(99,102,241,0.08)" }}>
                  <button
                    onClick={() => toggle(inst)}
                    disabled={toggling === inst.slug}
                    className="text-xs px-3 py-1.5 rounded-lg font-medium transition-all disabled:opacity-50"
                    style={inst.connected
                      ? { border: "1px solid rgba(239,68,68,0.3)", color: "#ef4444" }
                      : { border: "1px solid rgba(34,197,94,0.3)", color: "#16a34a" }}
                    onMouseEnter={e => { e.currentTarget.style.background = inst.connected ? "rgba(239,68,68,0.07)" : "rgba(34,197,94,0.07)"; }}
                    onMouseLeave={e => { e.currentTarget.style.background = "transparent"; }}
                  >
                    {toggling === inst.slug ? "..." : inst.connected ? t("services.disconnect") : t("services.connect")}
                  </button>
                  <span className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full ml-auto"
                    style={inst.connected
                      ? { background: "rgba(34,197,94,0.1)", color: "#16a34a" }
                      : { background: "rgba(148,163,184,0.12)", color: "#94a3b8" }}>
                    <span className="w-1.5 h-1.5 rounded-full"
                      style={{ background: inst.connected ? "#16a34a" : "#94a3b8" }} />
                    {inst.connected ? t("services.connected") : t("services.disconnected")}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {detailInstitution && (
        <InstitutionModal institution={detailInstitution} onClose={() => setDetailInstitution(null)} />
      )}
    </div>
  );
}
