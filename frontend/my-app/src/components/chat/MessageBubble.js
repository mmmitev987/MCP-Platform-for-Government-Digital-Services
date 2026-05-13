import { useTranslation } from "react-i18next";
import ReactMarkdown from "react-markdown";

const PORTAL_NAMES = {
  uslugi:    "uslugi.gov.mk",
  mojtermin: "mojtermin.mk",
  crm:       "crm.com.mk",
  mon:       "e-uslugi.mon.gov.mk",
};

function AIAvatar() {
  return (
    <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
      style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", boxShadow: "0 2px 8px rgba(99,102,241,0.4)" }}>
      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
      </svg>
    </div>
  );
}

const markdownComponents = {
  h1: ({ children }) => (
    <h1 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.5rem", marginTop: "0.75rem" }}>{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "#1e293b", marginBottom: "0.4rem", marginTop: "0.75rem" }}>{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 style={{ fontSize: "0.9rem", fontWeight: 600, color: "#334155", marginBottom: "0.3rem", marginTop: "0.5rem" }}>{children}</h3>
  ),
  p: ({ children }) => (
    <p style={{ marginBottom: "0.4rem", lineHeight: "1.6" }}>{children}</p>
  ),
  ul: ({ children }) => (
    <ul style={{ paddingLeft: "1.25rem", marginBottom: "0.5rem", listStyleType: "disc" }}>{children}</ul>
  ),
  ol: ({ children }) => (
    <ol style={{ paddingLeft: "1.25rem", marginBottom: "0.5rem", listStyleType: "decimal" }}>{children}</ol>
  ),
  li: ({ children }) => (
    <li style={{ marginBottom: "0.2rem", lineHeight: "1.5" }}>{children}</li>
  ),
  strong: ({ children }) => (
    <strong style={{ fontWeight: 600, color: "#1e293b" }}>{children}</strong>
  ),
  em: ({ children }) => (
    <em style={{ color: "#64748b" }}>{children}</em>
  ),
  hr: () => (
    <hr style={{ border: "none", borderTop: "1px solid rgba(99,102,241,0.15)", margin: "0.75rem 0" }} />
  ),
  blockquote: ({ children }) => (
    <blockquote style={{
      borderLeft: "3px solid #6366f1",
      paddingLeft: "0.75rem",
      margin: "0.5rem 0",
      color: "#64748b",
      fontStyle: "italic",
    }}>{children}</blockquote>
  ),
  code: ({ inline, children }) =>
    inline ? (
      <code style={{
        background: "rgba(99,102,241,0.1)",
        color: "#6366f1",
        borderRadius: "4px",
        padding: "0.1rem 0.35rem",
        fontSize: "0.8rem",
        fontFamily: "monospace",
      }}>{children}</code>
    ) : (
      <pre style={{
        background: "rgba(99,102,241,0.06)",
        border: "1px solid rgba(99,102,241,0.15)",
        borderRadius: "8px",
        padding: "0.75rem",
        overflowX: "auto",
        fontSize: "0.8rem",
        fontFamily: "monospace",
        margin: "0.5rem 0",
      }}><code>{children}</code></pre>
    ),
};

export default function MessageBubble({ role, content, portalErrors = [] }) {
  const { t } = useTranslation();
  const isUser = role === "user";
  const hasPortalError = !isUser && portalErrors.length > 0;
  const portalNames = portalErrors.map((s) => PORTAL_NAMES[s] || s);

  // Guard: content must always be a string for ReactMarkdown / plain render
  const safeContent =
    typeof content === "string"
      ? content
      : content == null
      ? ""
      : JSON.stringify(content, null, 2);

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}
      style={{ animation: "fadeSlideIn 0.25s ease-out" }}>
      {!isUser && (
        <div className="mr-2 mt-0.5">
          <AIAvatar />
        </div>
      )}
      <div className="max-w-[78%] flex flex-col gap-1">
        <div
          className="px-4 py-3 rounded-2xl text-sm"
          style={isUser ? {
            background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
            color: "#ffffff",
            borderBottomRightRadius: "4px",
            boxShadow: "0 2px 12px rgba(99,102,241,0.3)",
            lineHeight: "1.6",
            whiteSpace: "pre-wrap",
          } : {
            background: "#ffffff",
            color: "#1e293b",
            border: "1px solid rgba(99,102,241,0.15)",
            boxShadow: "0 2px 8px rgba(99,102,241,0.07)",
            borderBottomLeftRadius: "4px",
          }}
        >
          {isUser ? (
            safeContent
          ) : (
            <ReactMarkdown components={markdownComponents}>
              {safeContent}
            </ReactMarkdown>
          )}
        </div>

        {hasPortalError && (
          <div className="flex items-center gap-1.5 px-1 text-xs" style={{ color: "#ca8a04" }}>
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
