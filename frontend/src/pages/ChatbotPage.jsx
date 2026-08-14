import { useState, useRef, useEffect, useCallback } from "react";
import axios from "axios";
import {
  Send, Bot, User2, Trash2, GraduationCap, Loader2,
  Upload, CheckCircle, AlertCircle,
} from "lucide-react";

// ── Helpers ───────────────────────────────────────────────────────────────────

function generateId() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function formatTime(d) {
  return new Date(d).toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" });
}

function getOrCreateSessionId() {
  let id = sessionStorage.getItem("prism_chat_session");
  if (!id) {
    id = generateId();
    sessionStorage.setItem("prism_chat_session", id);
  }
  return id;
}

// ── Quick Reply Chips ─────────────────────────────────────────────────────────

const QUICK_REPLIES = [
  "Program S2 apa saja yang tersedia?",
  "Berapa biaya kuliah S2?",
  "Persyaratan pendaftaran S2?",
  "Silabus S2 Ilmu Komputer?",
  "Jadwal kelas untuk profesional?",
];

// ── Markdown-lite renderer ────────────────────────────────────────────────────
// Simple renderer for **bold**, *italic*, lists, and line breaks

function renderMarkdown(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    // Bold
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    // Italic
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    // Inline code
    .replace(/`(.+?)`/g, '<code class="bg-gray-100 px-1 rounded text-sm">$1</code>')
    // Bullet list items
    .replace(/^[-•]\s+(.+)/gm, "<li class=\"ml-4 list-disc\">$1</li>")
    // Numbered list
    .replace(/^\d+\.\s+(.+)/gm, "<li class=\"ml-4 list-decimal\">$1</li>")
    // Line breaks
    .replace(/\n/g, "<br/>");
}

// ── Message Bubble ────────────────────────────────────────────────────────────

function MessageBubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex items-end gap-2 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      {/* Avatar */}
      <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white text-sm
        ${isUser ? "bg-blue-600" : "bg-gradient-to-br from-indigo-500 to-purple-600"}`}>
        {isUser ? <User2 size={14} /> : <Bot size={14} />}
      </div>

      {/* Bubble */}
      <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm
        ${isUser
          ? "bg-blue-600 text-white rounded-br-sm"
          : "bg-white border border-gray-100 text-gray-800 rounded-bl-sm"
        }`}>
        {isUser ? (
          <p>{msg.content}</p>
        ) : (
          <div
            dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
            className="prose-sm"
          />
        )}
        <p className={`text-[10px] mt-1 ${isUser ? "text-blue-200 text-right" : "text-gray-400"}`}>
          {formatTime(msg.timestamp)}
        </p>
      </div>
    </div>
  );
}

// ── Typing Indicator ──────────────────────────────────────────────────────────

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
        <Bot size={14} className="text-white" />
      </div>
      <div className="bg-white border border-gray-100 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
        <div className="flex gap-1 items-center">
          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
        </div>
      </div>
    </div>
  );
}

// ── Document Upload Panel ─────────────────────────────────────────────────────

function DocumentPanel({ onClose }) {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [docs, setDocs] = useState([]);
  const fileRef = useRef();

  const fetchDocs = async () => {
    try {
      const r = await axios.get("/api/documents/");
      setDocs(r.data?.documents ?? []);
    } catch (e) { /* ignore */ }
  };

  useEffect(() => { fetchDocs(); }, []);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await axios.post("/api/documents/upload", fd);
      setResult({ ok: true, msg: res.data?.message });
      fetchDocs();
    } catch (err) {
      setResult({ ok: false, msg: err?.response?.data?.detail || "Upload failed" });
    } finally {
      setUploading(false);
    }
  };

  const handleSeed = async () => {
    setUploading(true);
    setResult(null);
    try {
      const res = await axios.post("/api/documents/seed");
      setResult({ ok: true, msg: res.data?.message });
      fetchDocs();
    } catch (err) {
      setResult({ ok: false, msg: err?.response?.data?.detail || "Seed failed" });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white border-l p-4 w-72 shrink-0 overflow-y-auto">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-sm text-gray-800">📚 Knowledge Base</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xs">Tutup</button>
      </div>

      {result && (
        <div className={`mb-3 p-2.5 rounded-lg text-xs flex gap-1.5 items-start
          ${result.ok ? "bg-green-50 text-green-700" : "bg-red-50 text-red-600"}`}>
          {result.ok ? <CheckCircle size={12} className="mt-0.5 shrink-0" /> : <AlertCircle size={12} className="mt-0.5 shrink-0" />}
          {result.msg}
        </div>
      )}

      <div className="space-y-2 mb-4">
        <label className={`w-full flex items-center gap-2 justify-center px-3 py-2 border-2 border-dashed 
          border-blue-200 rounded-lg text-xs text-blue-600 cursor-pointer hover:bg-blue-50 transition-colors
          ${uploading ? "opacity-50 pointer-events-none" : ""}`}>
          {uploading ? <Loader2 size={13} className="animate-spin" /> : <Upload size={13} />}
          Upload Dokumen (PDF/TXT)
          <input ref={fileRef} type="file" className="hidden" accept=".txt,.pdf,.md,.csv" onChange={handleUpload} />
        </label>

        <button onClick={handleSeed} disabled={uploading}
          className="w-full flex items-center gap-2 justify-center px-3 py-2 border rounded-lg text-xs 
          text-indigo-600 border-indigo-200 hover:bg-indigo-50 transition-colors disabled:opacity-50">
          {uploading ? <Loader2 size={13} className="animate-spin" /> : <GraduationCap size={13} />}
          Seed Data Kampus Bawaan
        </button>
      </div>

      <div>
        <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">Dokumen Aktif ({docs.length})</p>
        {docs.length === 0 ? (
          <p className="text-xs text-gray-400">Belum ada dokumen.</p>
        ) : (
          <ul className="space-y-1">
            {docs.map((d) => (
              <li key={d.source_file} className="text-xs text-gray-600 bg-gray-50 rounded p-2 flex justify-between">
                <span className="truncate mr-2">{d.source_file}</span>
                <span className="text-gray-400 shrink-0">{d.chunk_count} chunks</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

// ── Main Chat Page ────────────────────────────────────────────────────────────

const WELCOME_MESSAGE = {
  id: "welcome",
  role: "assistant",
  content: "Halo! 👋 Saya adalah asisten penerimaan mahasiswa **President University**.\n\nSaya siap membantu Anda mendapatkan informasi tentang program S2 kami: Ilmu Komputer, Manajemen, Teknik Industri, dan MBA Eksekutif.\n\nAda yang bisa saya bantu?",
  timestamp: new Date().toISOString(),
};

export default function ChatbotPage() {
  const sessionId = useRef(getOrCreateSessionId());
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showDocs, setShowDocs] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, scrollToBottom]);

  const sendMessage = async (text) => {
    const userText = text || input.trim();
    if (!userText || loading) return;

    setInput("");
    setMessages((prev) => [
      ...prev,
      { id: Date.now(), role: "user", content: userText, timestamp: new Date().toISOString() },
    ]);
    setLoading(true);

    const assistantId = Date.now() + 1;
    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: "assistant", content: "", timestamp: new Date().toISOString(), streaming: true },
    ]);

    try {
      const response = await fetch("/api/chatbot/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId.current, message: userText }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") break;
            try {
              const parsed = JSON.parse(data);
              if (parsed.text) {
                accumulated += parsed.text;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId ? { ...m, content: accumulated } : m
                  )
                );
              }
            } catch (_) { /* ignore parse errors */ }
          }
        }
      }

      // Mark streaming complete
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, streaming: false } : m))
      );
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: "Maaf, terjadi kesalahan koneksi. Silakan coba lagi.", streaming: false }
            : m
        )
      );
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const clearConversation = async () => {
    try {
      await axios.delete(`/api/chatbot/history/${sessionId.current}`);
    } catch (_) { /* ignore */ }
    sessionStorage.removeItem("prism_chat_session");
    sessionId.current = generateId();
    sessionStorage.setItem("prism_chat_session", sessionId.current);
    setMessages([WELCOME_MESSAGE]);
    setInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-[calc(100vh-80px)] bg-gray-50 rounded-xl overflow-hidden border shadow-sm">

      {/* Chat Area */}
      <div className="flex flex-col flex-1 min-w-0">

        {/* Header */}
        <div className="bg-white border-b px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Bot size={18} className="text-white" />
            </div>
            <div>
              <h2 className="font-semibold text-sm text-gray-800">Asisten Admisi President University</h2>
              <div className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                <span className="text-xs text-green-600">Online • RAG Aktif</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setShowDocs(!showDocs)}
              className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-lg border border-indigo-200 text-indigo-600 hover:bg-indigo-50 transition-colors">
              <GraduationCap size={13} /> Dokumen
            </button>
            <button onClick={clearConversation}
              className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-lg border text-gray-500 hover:bg-gray-50 transition-colors">
              <Trash2 size={13} /> Bersihkan
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} msg={msg} />
          ))}
          {loading && messages[messages.length - 1]?.content === "" && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        {/* Quick replies (show only at start) */}
        {messages.length <= 2 && !loading && (
          <div className="px-4 pb-2 flex flex-wrap gap-2">
            {QUICK_REPLIES.map((q) => (
              <button key={q} onClick={() => sendMessage(q)}
                className="text-xs px-3 py-1.5 bg-white border border-gray-200 rounded-full text-gray-600 
                hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50 transition-all">
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="bg-white border-t px-4 py-3">
          <div className="flex items-end gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Tanyakan tentang program S2 President University..."
              rows={1}
              disabled={loading}
              className="flex-1 resize-none rounded-xl border border-gray-200 px-3.5 py-2.5 text-sm
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                disabled:opacity-50 max-h-28 overflow-y-auto"
              style={{ minHeight: "42px" }}
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              className="shrink-0 w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center
                hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </div>
          <p className="text-[10px] text-gray-400 mt-1.5 text-center">
            Tekan Enter untuk kirim • Shift+Enter untuk baris baru
          </p>
        </div>
      </div>

      {/* Document Panel */}
      {showDocs && <DocumentPanel onClose={() => setShowDocs(false)} />}
    </div>
  );
}
