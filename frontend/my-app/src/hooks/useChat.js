import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { sendMessage, getSession } from "../api/chat";

const SESSION_LOAD_TIMEOUT_MS = 6000;

function withTimeout(promise, ms) {
  const timeout = new Promise((_, reject) =>
    setTimeout(() => reject(new Error("timeout")), ms)
  );
  return Promise.race([promise, timeout]);
}

/** Map an Axios error to a specific i18n key for the assistant.errors namespace. */
function errorKey(err) {
  if (!err.response) return "networkDown";          // no response — network down
  const s = err.response.status;
  if (s === 502 || s === 503 || s === 504) return "serverUnavailable";
  if (s === 408) return "timeout";
  return "serverError";
}

export function useChat() {
  const { t } = useTranslation();
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [sessionTitle, setSessionTitle] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const clearError = useCallback(() => setError(null), []);

  const send = useCallback(
    async (text) => {
      setLoading(true);
      setError(null);
      setMessages((prev) => [...prev, { role: "user", content: text }]);
      try {
        const { reply, session_id, portal_errors, geometry } = await sendMessage(text, sessionId);
        if (!sessionId) window.dispatchEvent(new Event("chat:session-created"));
        setSessionId(session_id);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: reply,
            // portal_errors: e.g. ["uslugi", "crm"] — portals that failed
            portalErrors: portal_errors ?? [],
            // katastar parcel geometry for mini-map (null if not a katastar response)
            geometry: geometry ?? null,
          },
        ]);
      } catch (err) {
        setError(t(`assistant.errors.${errorKey(err)}`));
      } finally {
        setLoading(false);
      }
    },
    [sessionId, t]
  );

  const loadSession = useCallback(async (id) => {
    setLoading(true);
    setError(null);
    try {
      const session = await withTimeout(getSession(id), SESSION_LOAD_TIMEOUT_MS);
      setSessionId(session.id);
      setSessionTitle(session.title);
      setMessages(
        session.messages.map((m) => ({
          role: m.role,
          content: m.content,
          portalErrors: [],   // historical messages don't carry live error state
        }))
      );
    } catch (err) {
      if (err.message === "timeout") {
        setError(t("assistant.errors.timeout"));
      } else {
        setError(t(`assistant.errors.${errorKey(err)}`));
      }
    } finally {
      setLoading(false);
    }
  }, [t]);

  const reset = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setSessionTitle(null);
    setError(null);
  }, []);

  return {
    messages, loading, error, clearError,
    send, reset, loadSession,
    sessionId, sessionTitle, setSessionTitle,
  };
}
