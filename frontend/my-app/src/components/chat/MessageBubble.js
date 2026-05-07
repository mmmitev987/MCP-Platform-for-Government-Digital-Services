import { useTranslation } from "react-i18next";

// Human-readable display names for institution slugs
const PORTAL_NAMES = {
  uslugi:    "uslugi.gov.mk",
  mojtermin: "mojtermin.mk",
  crm:       "crm.com.mk",
  mon:       "e-uslugi.mon.gov.mk",
};

export default function MessageBubble({ role, content, portalErrors = [] }) {
  const { t } = useTranslation();
  const isUser = role === "user";
  const hasPortalError = !isUser && portalErrors.length > 0;

  const portalNames = portalErrors.map((s) => PORTAL_NAMES[s] || s);

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs font-bold mr-2 flex-shrink-0 mt-0.5">
          AI
        </div>
      )}
      <div className="max-w-[75%] flex flex-col gap-1">
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? "bg-indigo-600 text-white rounded-br-md"
              : "bg-gray-800 text-gray-100 rounded-bl-md border border-gray-700"
          }`}
        >
          {content}
        </div>

        {/* Portal unavailability indicator — shown below the bubble */}
        {hasPortalError && (
          <div className="flex items-center gap-1.5 px-1 text-xs text-amber-500">
            <span>⚠</span>
            <span>
              {portalNames.length === 1
                ? t("assistant.portalWarning_one",   { portal: portalNames[0] })
                : t("assistant.portalWarning_other", { portals: portalNames.join(", ") })}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
