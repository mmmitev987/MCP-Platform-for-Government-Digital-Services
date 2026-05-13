import { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useChat } from "../hooks/useChat";
import MessageBubble from "../components/chat/MessageBubble";
import ChatInput from "../components/chat/ChatInput";
import SuggestedQuestions from "../components/chat/SuggestedQuestions";
import KatastarMap from "../components/chat/KatastarMap";

export default function Assistant() {
  const { t } = useTranslation();
  const { messages, loading, error, clearError, send, reset, loadSession, sessionTitle } = useChat();
  const bottomRef = useRef(null);
  const initialSentRef = useRef(false);
  const location = useLocation();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const sessionParam = params.get("session");
    if (sessionParam) {
      loadSession(Number(sessionParam));
      return;
    }
    const initial = location.state?.initialMessage;
    if (initial && !initialSentRef.current) {
      initialSentRef.current = true;
      send(initial);
      window.history.replaceState({}, "");
    }
  }, [location.search]); // eslint-disable-line

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col" style={{ height: "100vh", background: "#f0f4ff" }}>

      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 shrink-0"
        style={{ background: "#ffffff", borderBottom: "1px solid rgba(99,102,241,0.12)", boxShadow: "0 1px 8px rgba(99,102,241,0.07)" }}>
        <div className="flex items-center gap-3">
          {/* Icon */}
          <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
            style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", boxShadow: "0 2px 10px rgba(99,102,241,0.35)" }}>
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
            </svg>
          </div>
          <div>
            <h2 className="font-bold text-base" style={{ color: "#1e293b" }}>
              {sessionTitle || t("assistant.title")}
            </h2>
            <p className="text-xs mt-0.5" style={{ color: "#94a3b8" }}>{t("assistant.subtitle")}</p>
          </div>
        </div>
        {!isEmpty && (
          <button
            onClick={reset}
            className="flex items-center gap-2 text-sm font-semibold px-4 py-2 rounded-xl transition-all text-white"
            style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", boxShadow: "0 2px 10px rgba(99,102,241,0.35)" }}
            onMouseEnter={e => { e.currentTarget.style.boxShadow = "0 4px 16px rgba(99,102,241,0.5)"; e.currentTarget.style.transform = "translateY(-1px)"; }}
            onMouseLeave={e => { e.currentTarget.style.boxShadow = "0 2px 10px rgba(99,102,241,0.35)"; e.currentTarget.style.transform = "translateY(0)"; }}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4"/>
            </svg>
            {t("assistant.newChat")}
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6">
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-full text-center gap-6">
            <div>
              <div className="w-14 h-14 rounded-2xl mx-auto mb-4 flex items-center justify-center"
                style={{ background: "rgba(99,102,241,0.08)", color: "#6366f1" }}>
                <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
                </svg>
              </div>
              <h3 className="text-lg font-bold mb-2" style={{ color: "#1e293b" }}>{t("assistant.emptyHeading")}</h3>
              <p className="text-sm max-w-md" style={{ color: "#64748b" }}>{t("assistant.emptySubtitle")}</p>
            </div>
            <SuggestedQuestions onSelect={send} />
          </div>
        ) : (
          <div className="max-w-3xl mx-auto">
            {messages.map((m, i) => (
              <div key={i}>
                <MessageBubble role={m.role} content={m.content} portalErrors={m.portalErrors} />
                {m.role === "assistant" && m.geometry && (
                  <div className="max-w-xl ml-10 mb-4">
                    <KatastarMap geometry={m.geometry} />
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex justify-start mb-4" style={{ animation: "fadeSlideIn 0.25s ease-out" }}>
                <div className="w-8 h-8 rounded-full flex items-center justify-center mr-2 mt-0.5 shrink-0"
                  style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", boxShadow: "0 2px 8px rgba(99,102,241,0.4)" }}>
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
                  </svg>
                </div>
                <div className="px-5 py-3.5 rounded-2xl rounded-bl-sm flex items-center gap-1.5"
                  style={{ background: "#ffffff", border: "1px solid rgba(99,102,241,0.15)", boxShadow: "0 2px 8px rgba(99,102,241,0.07)" }}>
                  <span className="w-2 h-2 rounded-full" style={{ background: "#818cf8", animation: "typingBounce 1.2s ease-in-out infinite", animationDelay: "0ms" }} />
                  <span className="w-2 h-2 rounded-full" style={{ background: "#818cf8", animation: "typingBounce 1.2s ease-in-out infinite", animationDelay: "200ms" }} />
                  <span className="w-2 h-2 rounded-full" style={{ background: "#818cf8", animation: "typingBounce 1.2s ease-in-out infinite", animationDelay: "400ms" }} />
                </div>
              </div>
            )}
            {error && (
              <div className="flex items-start gap-3 px-4 py-3 mb-2 rounded-xl text-sm"
                style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)" }}>
                <span style={{ color: "#ef4444" }} className="flex-shrink-0">⚠</span>
                <p className="flex-1" style={{ color: "#dc2626" }}>{error}</p>
                <button onClick={clearError} className="flex-shrink-0 leading-none" style={{ color: "#ef4444" }}>✕</button>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="max-w-3xl w-full mx-auto px-2 sm:px-0 shrink-0">
        <ChatInput onSend={send} disabled={loading} />
      </div>
    </div>
  );
}
