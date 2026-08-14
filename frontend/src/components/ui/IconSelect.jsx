import { useEffect, useRef, useState } from "react";
import { ChevronDown, Check } from "lucide-react";

/**
 * Reusable dropdown with icons + per-field accent color.
 *
 * @param {Array} options    [{ value, label, icon }]
 * @param {string} value     Currently selected option value
 * @param {Function} onChange Called with the selected value
 * @param {object} accent    Field accent classes { text, softActive }
 * @param {string} placeholder
 * @param {boolean} disabled
 */
export default function IconSelect({
  options,
  value,
  onChange,
  accent,
  placeholder,
  disabled,
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const selected = options.find((o) => o.value === value);

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        disabled={disabled}
        className={`w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg border bg-white text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed ${
          selected ? accent.text : "text-gray-600"
        } border-gray-200 hover:border-gray-300`}
      >
        <span className="flex items-center gap-2 min-w-0">
          {selected ? (
            <>
              <selected.icon size={16} className="shrink-0" />
              <span className="truncate">{selected.label}</span>
            </>
          ) : (
            <span className="text-gray-400 truncate">{placeholder}</span>
          )}
        </span>
        <ChevronDown
          size={16}
          className={`shrink-0 transition-transform ${open ? "rotate-180" : ""} ${accent.text}`}
        />
      </button>
      {open && (
        <div className="absolute z-30 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg py-1 max-h-72 overflow-y-auto">
          {options.map((opt) => {
            const isActive = opt.value === value;
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => {
                  onChange(opt.value);
                  setOpen(false);
                }}
                className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-left transition ${
                  isActive ? accent.softActive : "text-gray-700 hover:bg-gray-50"
                }`}
              >
                <opt.icon size={15} className={isActive ? accent.text : "text-gray-400"} />
                <span className="truncate">{opt.label}</span>
                {isActive && <Check size={14} className={`ml-auto shrink-0 ${accent.text}`} />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
