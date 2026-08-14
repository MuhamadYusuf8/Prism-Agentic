import { createContext, useContext, useState, useCallback, useRef, useEffect } from "react";
import { CheckCircle, XCircle, AlertTriangle, Info, X } from "lucide-react";

const ToastContext = createContext(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

const ICONS = {
  success: CheckCircle,
  error:   XCircle,
  warning: AlertTriangle,
  info:    Info,
};

const COLORS = {
  success: "bg-white border-green-400 text-green-800",
  error:   "bg-white border-red-400 text-red-800",
  warning: "bg-white border-yellow-400 text-yellow-800",
  info:    "bg-white border-blue-400 text-blue-800",
};

const ICON_COLORS = {
  success: "text-green-500",
  error:   "text-red-500",
  warning: "text-yellow-500",
  info:    "text-blue-500",
};

function ToastItem({ toast, onRemove }) {
  const Icon = ICONS[toast.type] || Info;
  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 rounded-xl border-l-4 shadow-lg w-80 max-w-sm
        ${COLORS[toast.type]}`}
    >
      <Icon size={18} className={`shrink-0 mt-0.5 ${ICON_COLORS[toast.type]}`} />
      <div className="flex-1 min-w-0">
        {toast.title && <p className="text-sm font-semibold leading-tight">{toast.title}</p>}
        {toast.message && <p className="text-xs text-gray-600 mt-0.5 leading-snug">{toast.message}</p>}
      </div>
      <button
        onClick={() => onRemove(toast.id)}
        className="shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
      >
        <X size={14} />
      </button>
    </div>
  );
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const counterRef = useRef(0);

  const remove = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(({ type = "info", title, message, duration = 4000 }) => {
    const id = ++counterRef.current;
    setToasts((prev) => [...prev, { id, type, title, message }]);
    if (duration > 0) setTimeout(() => remove(id), duration);
    return id;
  }, [remove]);

  // Shortcuts
  toast.success = (msg, title = "Berhasil")      => toast({ type: "success", title, message: msg });
  toast.error   = (msg, title = "Terjadi Error") => toast({ type: "error",   title, message: msg });
  toast.warning = (msg, title = "Peringatan")    => toast({ type: "warning", title, message: msg });
  toast.info    = (msg, title = "Info")          => toast({ type: "info",    title, message: msg });

  // Listen to events from axios interceptor (fires on 403/500 errors)
  useEffect(() => {
    const handler = (e) => toast(e.detail);
    window.addEventListener("prism:toast", handler);
    return () => window.removeEventListener("prism:toast", handler);
  }, [toast]);

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="fixed bottom-5 right-5 z-[9999] flex flex-col gap-2.5 pointer-events-none">
        {toasts.map((t) => (
          <div key={t.id} className="pointer-events-auto">
            <ToastItem toast={t} onRemove={remove} />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
