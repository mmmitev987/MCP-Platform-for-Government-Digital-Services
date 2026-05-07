import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../contexts/AuthContext";
import { getActivity } from "../api/activity";

function Badge({ status }) {
  const colors = {
    completed: "text-green-400 bg-green-950 border-green-900",
    pending: "text-yellow-400 bg-yellow-950 border-yellow-900",
    failed: "text-red-400 bg-red-950 border-red-900",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${colors[status] || colors.pending}`}>
      {status}
    </span>
  );
}

export default function Dashboard() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activity, setActivity] = useState([]);

  const QUICK_ACTIONS = [
    { labelKey: "actions.bookAppointment", descKey: "actions.bookAppointmentDesc", icon: "📅", path: "/assistant", q: "I want to book a medical appointment" },
    { labelKey: "actions.checkDocuments", descKey: "actions.checkDocumentsDesc", icon: "📄", path: "/services", q: null },
    { labelKey: "actions.submitRequest", descKey: "actions.submitRequestDesc", icon: "📨", path: "/assistant", q: "What services can I apply for?" },
    { labelKey: "actions.checkTax", descKey: "actions.checkTaxDesc", icon: "💰", path: "/assistant", q: "Tell me about tax-related services" },
  ];

  useEffect(() => {
    getActivity({ limit: 5 }).then((d) => setActivity(d.items)).catch(() => {});
  }, []);

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return t("dashboard.goodMorning");
    if (h < 18) return t("dashboard.goodAfternoon");
    return t("dashboard.goodEvening");
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-6 lg:mb-8">
        <h2 className="text-2xl font-bold text-white">
          {greeting()}, {user?.full_name || user?.email?.split("@")[0]} 👋
        </h2>
        <p className="text-gray-400 mt-1">{t("dashboard.subtitle")}</p>
      </div>

      {/* Quick Actions */}
      <section className="mb-8">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
          {t("dashboard.quickActions")}
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {QUICK_ACTIONS.map(({ labelKey, descKey, icon, path, q }) => (
            <button
              key={labelKey}
              onClick={() => navigate(path, q ? { state: { initialMessage: q } } : {})}
              className="bg-gray-900 border border-gray-800 rounded-xl p-5 text-left hover:border-indigo-500 hover:bg-gray-800 transition-all group"
            >
              <div className="text-2xl mb-3">{icon}</div>
              <p className="text-white font-medium text-sm group-hover:text-indigo-400 transition-colors">
                {t(`dashboard.${labelKey}`)}
              </p>
              <p className="text-gray-500 text-xs mt-1">{t(`dashboard.${descKey}`)}</p>
            </button>
          ))}
        </div>
      </section>

      {/* Recent Activity */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
            {t("dashboard.recentActivity")}
          </h3>
          <button onClick={() => navigate("/activity")} className="text-indigo-400 text-sm hover:text-indigo-300">
            {t("dashboard.viewAll")}
          </button>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          {activity.length === 0 ? (
            <div className="px-6 py-10 text-center text-gray-500 text-sm">
              {t("dashboard.noActivity")}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[480px]">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="text-left px-4 sm:px-6 py-3 text-xs text-gray-500 font-medium">{t("dashboard.service")}</th>
                    <th className="text-left px-4 sm:px-6 py-3 text-xs text-gray-500 font-medium hidden sm:table-cell">{t("dashboard.action")}</th>
                    <th className="text-left px-4 sm:px-6 py-3 text-xs text-gray-500 font-medium">{t("dashboard.status")}</th>
                    <th className="text-left px-4 sm:px-6 py-3 text-xs text-gray-500 font-medium">{t("dashboard.date")}</th>
                  </tr>
                </thead>
                <tbody>
                  {activity.map((a) => (
                    <tr key={a.id} className="border-b border-gray-800 last:border-0 hover:bg-gray-800/50">
                      <td className="px-4 sm:px-6 py-3 text-sm text-gray-300 font-medium capitalize">{a.service}</td>
                      <td className="px-4 sm:px-6 py-3 text-sm text-gray-400 hidden sm:table-cell">{a.action.replace(/__/g, " › ").replace(/_/g, " ")}</td>
                      <td className="px-4 sm:px-6 py-3"><Badge status={a.status} /></td>
                      <td className="px-4 sm:px-6 py-3 text-xs text-gray-500 whitespace-nowrap">{new Date(a.created_at).toLocaleDateString()}</td>
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
