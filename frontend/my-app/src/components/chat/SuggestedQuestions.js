import { useTranslation } from "react-i18next";

export default function SuggestedQuestions({ onSelect }) {
  const { t } = useTranslation();

  const SUGGESTIONS = [
    t("assistant.suggestions.passport"),
    t("assistant.suggestions.idCard"),
    t("assistant.suggestions.doctors"),
    t("assistant.suggestions.driverLicense"),
    t("assistant.suggestions.vehicle"),
    t("assistant.suggestions.citizenship"),
  ];

  return (
    <div className="flex flex-wrap gap-2 justify-center">
      {SUGGESTIONS.map((q) => (
        <button
          key={q}
          onClick={() => onSelect(q)}
          className="px-3 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 hover:text-white text-xs rounded-lg transition-colors"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
