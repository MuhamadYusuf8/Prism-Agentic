import { useState, useEffect } from "react";
import axios from "axios";
import {
  Settings,
  Mail,
  Linkedin,
  Bell,
  Globe,
  Save,
  RefreshCw,
  Eye,
  EyeOff,
} from "lucide-react";

/* ─── Section Component ─────────────────────────────────────── */

function SettingsSection({ title, icon: Icon, children }) {
  return (
    <div className="bg-white rounded-xl border p-5 space-y-4">
      <div className="flex items-center gap-2 border-b pb-3">
        <Icon size={18} className="text-blue-600" />
        <h2 className="font-semibold text-gray-800">{title}</h2>
      </div>
      {children}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════ */

export default function SettingsPage() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null);
  const [showPasswords, setShowPasswords] = useState({});

  useEffect(() => {
    axios
      .get("/api/settings")
      .then((r) => setSettings(r.data))
      .catch(() => setMsg("Failed to load settings"))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    if (!settings) return;
    setSaving(true);
    setMsg(null);
    try {
      await axios.put("/api/settings", settings);
      setMsg("Settings saved successfully");
    } catch {
      setMsg("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const update = (section, field, value) => {
    if (!settings) return;
    setSettings({
      ...settings,
      [section]: { ...settings[section], [field]: value },
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        <RefreshCw className="animate-spin mr-2" size={18} />
        Loading settings...
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="text-center py-12 text-gray-400">
        Could not load settings.
      </div>
    );
  }

  const toggleShow = (key) =>
    setShowPasswords((prev) => ({ ...prev, [key]: !prev[key] }));

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Settings size={22} className="text-blue-600" />
            Settings
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Configure email, scraping, monitoring, and general preferences
          </p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm font-medium transition-colors"
        >
          <Save size={16} />
          {saving ? "Saving..." : "Save All"}
        </button>
      </div>

      {msg && (
        <div
          className={`px-4 py-3 rounded-lg text-sm ${
            msg.includes("success")
              ? "bg-green-50 text-green-700 border border-green-200"
              : "bg-red-50 text-red-700 border border-red-200"
          }`}
        >
          {msg}
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-5">
        {/* ── Email Configuration ── */}
        <SettingsSection title="Email Configuration" icon={Mail}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                SMTP Host
              </label>
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={settings.email.smtp_host}
                onChange={(e) => update("email", "smtp_host", e.target.value)}
                placeholder="smtp.gmail.com"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                SMTP Port
              </label>
              <input
                type="number"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={settings.email.smtp_port}
                onChange={(e) =>
                  update("email", "smtp_port", parseInt(e.target.value) || 587)
                }
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                SMTP User
              </label>
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={settings.email.smtp_user}
                onChange={(e) => update("email", "smtp_user", e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                SMTP Password
              </label>
              <div className="relative">
                <input
                  type={showPasswords["smtp"] ? "text" : "password"}
                  className="w-full border rounded-lg px-3 py-2 text-sm pr-10 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  value={settings.email.smtp_pass}
                  onChange={(e) => update("email", "smtp_pass", e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => toggleShow("smtp")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPasswords["smtp"] ? (
                    <EyeOff size={16} />
                  ) : (
                    <Eye size={16} />
                  )}
                </button>
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                From Name
              </label>
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={settings.email.from_name}
                onChange={(e) => update("email", "from_name", e.target.value)}
                placeholder="Admissions Team"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                From Email
              </label>
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={settings.email.from_email}
                onChange={(e) => update("email", "from_email", e.target.value)}
                placeholder="admissions@president.ac.id"
              />
            </div>
          </div>
        </SettingsSection>

        {/* ── LinkedIn Scraper ── */}
        <SettingsSection title="LinkedIn Scraper" icon={Linkedin}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                LinkedIn Email
              </label>
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={settings.linkedin.email}
                onChange={(e) => update("linkedin", "email", e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                LinkedIn Password
              </label>
              <div className="relative">
                <input
                  type={showPasswords["linkedin"] ? "text" : "password"}
                  className="w-full border rounded-lg px-3 py-2 text-sm pr-10 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  value={settings.linkedin.password}
                  onChange={(e) =>
                    update("linkedin", "password", e.target.value)
                  }
                />
                <button
                  type="button"
                  onClick={() => toggleShow("linkedin")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPasswords["linkedin"] ? (
                    <EyeOff size={16} />
                  ) : (
                    <Eye size={16} />
                  )}
                </button>
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Max Requests per Session
              </label>
              <input
                type="number"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={settings.linkedin.max_requests}
                onChange={(e) =>
                  update(
                    "linkedin",
                    "max_requests",
                    parseInt(e.target.value) || 50,
                  )
                }
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-xs font-medium text-gray-600 mb-1">
                LinkedIn Session Cookie (li_at)
              </label>
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={settings.linkedin.li_at || ""}
                onChange={(e) => update("linkedin", "li_at", e.target.value)}
                placeholder="Paste your li_at cookie value here..."
              />
              <p className="text-xs text-gray-400 mt-1">
                How to get it: Log into linkedin.com → DevTools (F12) → Application → Cookies → linkedin.com → Copy "li_at" value. Enables Phase 2 detail scraping (skills, education, experience).
              </p>
            </div>
          </div>
        </SettingsSection>

        {/* ── Email Monitoring ── */}
        <SettingsSection title="Email Monitoring" icon={Bell}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Check Interval (minutes)
              </label>
              <input
                type="number"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={settings.monitoring.check_interval_minutes}
                onChange={(e) =>
                  update(
                    "monitoring",
                    "check_interval_minutes",
                    parseInt(e.target.value) || 5,
                  )
                }
              />
            </div>
            <div className="flex items-center gap-3 pt-5">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  checked={settings.monitoring.auto_follow_up}
                  onChange={(e) =>
                    update("monitoring", "auto_follow_up", e.target.checked)
                  }
                />
                <span className="text-sm text-gray-700">Auto Follow-up</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  checked={settings.monitoring.notify_on_reply}
                  onChange={(e) =>
                    update("monitoring", "notify_on_reply", e.target.checked)
                  }
                />
                <span className="text-sm text-gray-700">Notify on Reply</span>
              </label>
            </div>
          </div>
        </SettingsSection>

        {/* ── General Settings ── */}
        <SettingsSection title="General Settings" icon={Globe}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Institution Name
              </label>
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={settings.general.institution_name}
                onChange={(e) =>
                  update("general", "institution_name", e.target.value)
                }
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Program URL
              </label>
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={settings.general.program_url}
                onChange={(e) =>
                  update("general", "program_url", e.target.value)
                }
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Reply-to Email
              </label>
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={settings.general.reply_to_email}
                onChange={(e) =>
                  update("general", "reply_to_email", e.target.value)
                }
              />
            </div>
          </div>
        </SettingsSection>
      </form>
    </div>
  );
}
