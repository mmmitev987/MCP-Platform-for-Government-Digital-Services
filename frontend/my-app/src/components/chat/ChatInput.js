import { useState, useRef } from "react";

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState("");
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    const text = value.trim();
    if (!text || disabled) return;
    onSend(text);
    setValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  const handleChange = (e) => {
    setValue(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2 sm:gap-3 p-3 sm:p-4 border-t border-gray-800 bg-gray-900">
      <textarea
        ref={textareaRef}
        rows={1}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder="Ask about government services…"
        className="flex-1 resize-none bg-gray-800 text-white placeholder-gray-500 border border-gray-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-indigo-500 transition-colors disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={!value.trim() || disabled}
        className="px-4 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl text-sm font-medium transition-colors flex-shrink-0"
      >
        {disabled ? "…" : "Send"}
      </button>
    </form>
  );
}
