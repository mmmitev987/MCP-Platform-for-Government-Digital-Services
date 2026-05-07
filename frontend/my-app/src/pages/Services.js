import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getInstitutions, connectInstitution, disconnectInstitution } from "../api/services";
import InstitutionModal from "../components/services/InstitutionModal";

const INSTITUTION_ICONS = {
  "uslugi.gov.mk": "🏛️",
  "mojtermin.mk": "🏥",
  "crm.com.mk": "📋",
};

export default function Services() {
  const { t } = useTranslation();
  const [institutions, setInstitutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(null);
  const [detailInstitution, setDetailInstitution] = useState(null);

  useEffect(() => {
    getInstitutions()
      .then(setInstitutions)
      .finally(() => setLoading(false));
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
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white">{t("services.title")}</h2>
        <p className="text-gray-400 mt-1">{t("services.subtitle")}</p>
      </div>

      {loading ? (
        <div className="text-gray-500 text-sm">{t("services.loading")}</div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {institutions.map((inst) => (
            <div
              key={inst.slug}
              className={`bg-gray-900 border rounded-xl overflow-hidden transition-colors ${
                inst.connected ? "border-gray-800" : "border-gray-700 opacity-60"
              }`}
            >
              {/* Header */}
              <div className="px-5 py-4 border-b border-gray-800 flex items-center gap-3">
                <span className="text-2xl">{INSTITUTION_ICONS[inst.name] || "🔗"}</span>
                <div className="flex-1 min-w-0">
                  <h3 className="text-white font-semibold">{inst.name}</h3>
                  <a
                    href={inst.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-indigo-400 hover:underline truncate"
                  >
                    {inst.url}
                  </a>
                </div>
                <span
                  className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full ${
                    inst.connected
                      ? "bg-green-900/40 text-green-400"
                      : "bg-gray-800 text-gray-500"
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${inst.connected ? "bg-green-400" : "bg-gray-500"}`} />
                  {inst.connected ? t("services.connected") : t("services.disconnected")}
                </span>
              </div>

              {/* Body */}
              <div className="px-5 py-4">
                <p className="text-gray-400 text-sm">{inst.description}</p>
              </div>

              {/* Footer */}
              <div className="px-5 py-3 border-t border-gray-800 flex items-center gap-3">
                <button
                  onClick={() => toggle(inst)}
                  disabled={toggling === inst.slug}
                  className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors disabled:opacity-50 ${
                    inst.connected
                      ? "border border-red-800 text-red-400 hover:bg-red-900/20"
                      : "border border-green-800 text-green-400 hover:bg-green-900/20"
                  }`}
                >
                  {toggling === inst.slug
                    ? "..."
                    : inst.connected
                    ? t("services.disconnect")
                    : t("services.connect")}
                </button>
                <button
                  onClick={() => setDetailInstitution(inst)}
                  className="text-xs px-3 py-1.5 rounded-lg font-medium border border-gray-700 text-gray-400 hover:text-white hover:border-gray-600 transition-colors"
                >
                  {t("services.moreDetails")}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {detailInstitution && (
        <InstitutionModal
          institution={detailInstitution}
          onClose={() => setDetailInstitution(null)}
        />
      )}
    </div>
  );
}
