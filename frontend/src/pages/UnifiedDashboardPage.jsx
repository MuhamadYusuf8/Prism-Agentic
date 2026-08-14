import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import {
  LayoutDashboard,
  Users,
  Linkedin,
  BookOpen,
  Briefcase,
  TrendingUp,
  Mail,
  Target,
  Award,
  Eye,
  MessageSquare,
  CheckCircle,
  Play,
  Pause,
  Send,
  Plus,
  X,
  Loader2,
  RefreshCw,
  BarChart2,
  Search,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Bot,
  Download,
  GraduationCap,
  School,
} from "lucide-react";
import IconSelect from "../components/ui/IconSelect";
import { FIELDS, getField } from "../scraping";

/* ═══════════════════════════════════════════════════════════════
   HELPERS
   ═══════════════════════════════════════════════════════════════ */
const STATUS_COLORS = {
  draft: "bg-gray-100 text-gray-700",
  active: "bg-green-100 text-green-700",
  paused: "bg-yellow-100 text-yellow-700",
  completed: "bg-blue-100 text-blue-700",
  cancelled: "bg-red-100 text-red-700",
};

const FUNNEL_COLORS = [
  "#3b82f6",
  "#8b5cf6",
  "#f59e0b",
  "#10b981",
  "#059669",
  "#6366f1",
  "#ec4899",
  "#14b8a6",
  "#f97316",
  "#84cc16",
];

const TYPE_CONFIG = {
  master: {
    color: "text-blue-600",
    bg: "bg-blue-50",
    border: "border-blue-200",
  },
};

function scoreColor(s) {
  if (s == null) return "text-gray-400";
  if (s >= 70) return "text-green-600";
  if (s >= 40) return "text-yellow-600";
  return "text-red-500";
}
function scoreBg(s) {
  if (s == null) return "bg-gray-100";
  if (s >= 70) return "bg-green-100";
  if (s >= 40) return "bg-yellow-100";
  return "bg-red-100";
}

/* ── KPI Card ── */
function KpiCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div className="bg-white rounded-xl border p-4 flex items-center gap-3">
      <div className={`p-2.5 rounded-lg ${color}`}>
        <Icon size={20} className="text-white" />
      </div>
      <div>
        <div className="text-2xl font-bold leading-none">{value}</div>
        <div className="text-sm font-medium mt-0.5">{label}</div>
        {sub && <div className="text-xs text-gray-500">{sub}</div>}
      </div>
    </div>
  );
}

/* ── Section Wrapper ── */
function Section({ title, icon: Icon, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon size={16} className="text-gray-500" />
          <h2 className="font-semibold text-sm text-gray-700">{title}</h2>
        </div>
        {open ? (
          <ChevronUp size={16} className="text-gray-400" />
        ) : (
          <ChevronDown size={16} className="text-gray-400" />
        )}
      </button>
      {open && <div className="px-5 pb-5">{children}</div>}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════════════════════════ */
export default function UnifiedDashboardPage() {
  const [summary, setSummary] = useState(null);
  const [funnel, setFunnel] = useState({});
  const [byEducation, setByEducation] = useState({});
  const [byProgram, setByProgram] = useState({});
  const [profileDist, setProfileDist] = useState({});
  const [topProspects, setTopProspects] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateCampaign, setShowCreateCampaign] = useState(false);
  const [campaignForm, setCampaignForm] = useState({
    name: "",
    description: "",
    target_type: "master",
    email_template: { subject: "", body: "" },
    follow_up: { enabled: true, delay_days: 3, max_follow_ups: 2 },
  });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [leadSearch, setLeadSearch] = useState("");
  const [leadFilter, setLeadFilter] = useState("all");
  const [activeFieldKey, setActiveFieldKey] = useState(FIELDS[0].key);
  const activeField = getField(activeFieldKey);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [
        sRes,
        fRes,
        eduRes,
        progRes,
        distRes,
        topRes,
        campRes,
        leadsRes,
      ] = await Promise.allSettled([
        axios.get("/api/analytics/summary"),
        axios.get("/api/analytics/funnel"),
        axios.get("/api/analytics/by-education"),
        axios.get("/api/analytics/by-program"),
        axios.get("/api/analytics/profile-distribution"),
        axios.get("/api/analytics/top-prospects?limit=10"),
        axios.get("/api/campaigns"),
        axios.get("/api/leads"),
      ]);
      if (sRes.status === "fulfilled") setSummary(sRes.value.data);
      if (fRes.status === "fulfilled") setFunnel(fRes.value.data);
      if (eduRes.status === "fulfilled")
        setByEducation(eduRes.value.data?.by_level ?? {});
      if (progRes.status === "fulfilled") {
        const arr = progRes.value.data;
        setByProgram(
          Array.isArray(arr)
            ? Object.fromEntries(
                arr.map((item) => [
                  item.program,
                  item.count,
                ]),
              )
            : (arr ?? {}),
        );
      }
      if (distRes.status === "fulfilled") setProfileDist(distRes.value.data);
      if (topRes.status === "fulfilled")
        setTopProspects(topRes.value.data?.data ?? []);
      if (campRes.status === "fulfilled")
        setCampaigns(
          campRes.value.data.data || campRes.value.data.campaigns || [],
        );
      if (leadsRes.status === "fulfilled")
        setLeads(leadsRes.value.data?.data || leadsRes.value.data?.leads || []);
    } catch {
      /* ignore */
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchAll();
  }, []);

  const handleCreateCampaign = async (e) => {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      await axios.post("/api/campaigns", campaignForm);
      setMsg("✅ Campaign created");
      setShowCreateCampaign(false);
      setCampaignForm({
        name: "",
        description: "",
        target_type: "master",
        email_template: { subject: "", body: "" },
        follow_up: { enabled: true, delay_days: 3, max_follow_ups: 2 },
      });
      fetchAll();
    } catch (err) {
      setMsg(`❌ ${err.response?.data?.detail || "Failed"}`);
    }
    setBusy(false);
  };

  const handleActivate = async (id) => {
    try {
      await axios.post(`/api/campaigns/${id}/activate`);
      setMsg("✅ Activated");
      fetchAll();
    } catch (err) {
      setMsg(`❌ ${err.response?.data?.detail || "Failed"}`);
    }
  };
  const handlePause = async (id) => {
    try {
      await axios.post(`/api/campaigns/${id}/pause`);
      setMsg("⏸️ Paused");
      fetchAll();
    } catch (err) {
      setMsg(`❌ ${err.response?.data?.detail || "Failed"}`);
    }
  };
  const handleSendFollowUps = async (id) => {
    try {
      await axios.post(`/api/campaigns/${id}/send-follow-ups`);
      setMsg("✅ Follow-ups sent");
    } catch (err) {
      setMsg(`❌ ${err.response?.data?.detail || "Failed"}`);
    }
  };

  const openRate = summary?.email_stats?.total_sent
    ? (
        (summary.email_stats.total_opened / summary.email_stats.total_sent) *
        100
      ).toFixed(1)
    : "0";
  const replyRate = summary?.email_stats?.total_sent
    ? (
        (summary.email_stats.total_replied / summary.email_stats.total_sent) *
        100
      ).toFixed(1)
    : "0";
  const maxFunnel = Math.max(...Object.values(funnel), 1);
  const filteredLeads = leads.filter((l) => {
    if (leadFilter !== "all" && l.status !== leadFilter) return false;
    if (
      leadSearch &&
      !l.name?.toLowerCase().includes(leadSearch.toLowerCase()) &&
      !l.email?.toLowerCase().includes(leadSearch.toLowerCase())
    )
      return false;
    return true;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen text-gray-400">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-4" />
          <p>Loading unified dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5 pb-12">
      {/* ═══ HEADER ═══ */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bot size={24} className="text-blue-600" />
            PRISM Unified Command Center
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            President Recruitment Intelligence System & Matcher — All features
            consolidated
          </p>
        </div>
        <button
          onClick={fetchAll}
          className="flex items-center gap-1.5 px-3 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* ═══ FIELD SELECTOR ═══ */}
      <div className="flex flex-wrap items-center gap-3 bg-white rounded-xl border p-3">
        <div className="w-64">
          <IconSelect
            options={FIELDS.map((f) => ({ value: f.key, label: f.label, icon: f.icon }))}
            value={activeFieldKey}
            onChange={setActiveFieldKey}
            accent={activeField.accent}
            placeholder="Select field..."
          />
        </div>
        <span className="text-xs text-gray-400">
          Target: <span className="font-medium text-gray-600">{activeField.degree}</span>
        </span>
        <Link
          to={`/linkedin?field=${activeFieldKey}`}
          className={`flex items-center gap-1.5 ml-auto px-3 py-2 rounded-lg text-sm font-medium border transition ${activeField.accent.hover} border-gray-200 bg-white text-gray-700`}
        >
          <Linkedin size={15} className={activeField.accent.icon} />
          Open LinkedIn Sourcing
        </Link>
      </div>

      {msg && (
        <div className="bg-gray-50 border rounded-lg px-4 py-2 text-sm flex items-center justify-between">
          <span>{msg}</span>
          <button
            onClick={() => setMsg(null)}
            className="text-gray-400 hover:text-gray-600"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* ═══ SECTION 1: KPIs ═══ */}
      <Section title="Key Performance Indicators" icon={LayoutDashboard}>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <KpiCard
            icon={Users}
            label="Total Leads"
            value={summary?.total_leads ?? 0}
            color="bg-blue-600"
          />
          <KpiCard
            icon={CheckCircle}
            label="Active Leads"
            value={summary?.active_leads ?? 0}
            color="bg-emerald-600"
          />
          <KpiCard
            icon={Sparkles}
            label="Total Scraped Fields"
            value={Object.values(summary?.by_field ?? {}).reduce(
              (a, b) => a + b,
              0,
            )}
            sub={FIELDS.map((f) => f.shortLabel).join(" · ")}
            color="bg-purple-600"
          />
          <KpiCard
            icon={Award}
            label="Avg Profile Score"
            value={summary?.avg_profile_score?.toFixed(1) ?? "—"}
            color="bg-amber-600"
          />
          <KpiCard
            icon={Mail}
            label="Campaigns"
            value={summary?.total_campaigns ?? 0}
            sub={`${summary?.active_campaigns ?? 0} active`}
            color="bg-rose-600"
          />
        </div>
      </Section>

      {/* ═══ SECTION 2: PIPELINE & SOURCE ═══ */}
      <Section title="Pipeline Status & Source Breakdown" icon={TrendingUp}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Lead Stages
            </p>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
              {[
                { key: "new", label: "New", c: "bg-blue-100 text-blue-700" },
                {
                  key: "contacted",
                  label: "Contacted",
                  c: "bg-yellow-100 text-yellow-700",
                },
                {
                  key: "replied",
                  label: "Replied",
                  c: "bg-purple-100 text-purple-700",
                },
                {
                  key: "interested",
                  label: "Interested",
                  c: "bg-orange-100 text-orange-700",
                },
                {
                  key: "enrolled",
                  label: "Enrolled",
                  c: "bg-emerald-100 text-emerald-700",
                },
                {
                  key: "rejected",
                  label: "Rejected",
                  c: "bg-red-100 text-red-700",
                },
              ].map(({ key, label, c }) => (
                <div key={key} className={`rounded-lg p-2.5 text-center ${c}`}>
                  <div className="text-lg font-bold">
                    {summary?.by_status?.[key] ?? 0}
                  </div>
                  <div className="text-xs font-medium">{label}</div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              By Source
            </p>
            <div className="grid grid-cols-2 gap-3">
              {[
                {
                  key: "linkedin",
                  label: "LinkedIn",
                  icon: Linkedin,
                  c: "border-blue-200 bg-blue-50 text-blue-800",
                },
                {
                  key: "manual",
                  label: "Manual Entry",
                  icon: Users,
                  c: "border-gray-200 bg-gray-50 text-gray-700",
                },
              ].map(({ key, label, icon: Icon, c }) => (
                <div
                  key={key}
                  className={`rounded-lg p-3 border flex items-center gap-2.5 ${c}`}
                >
                  <Icon size={18} />
                  <div>
                    <div className="text-lg font-bold">
                      {summary?.by_source?.[key] ?? 0}
                    </div>
                    <div className="text-xs">{label}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Section>

      {/* ═══ SECTION 3: STUDY FIELDS & DATA QUALITY ═══ */}
      <Section title="Study Fields & Data Quality" icon={BarChart2}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              By Study Field
            </p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {FIELDS.map((field) => {
                const Icon = field.icon;
                const count = summary?.by_field?.[field.key] ?? 0;
                const total = Object.values(summary?.by_field ?? {}).reduce(
                  (a, b) => a + b,
                  0,
                );
                const pct = total > 0 ? Math.round((count / total) * 100) : 0;
                return (
                  <div
                    key={field.key}
                    className={`rounded-lg p-3 border ${field.accent.softBg} ${field.accent.softActive} text-center`}
                  >
                    <Icon size={20} className={`mx-auto mb-1 ${field.accent.icon}`} />
                    <div className={`text-lg font-bold ${field.accent.text}`}>
                      {count}
                      <span className="text-xs font-normal text-gray-400 ml-1">
                        ({pct}%)
                      </span>
                    </div>
                    <div className="text-xs font-medium">{field.shortLabel}</div>
                    <div className="text-[10px] text-gray-500 truncate">
                      {field.degree}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Data Quality
            </p>
            <div className="grid grid-cols-3 gap-3">
              {[
                {
                  key: "complete",
                  label: "Complete",
                  c: "bg-emerald-100 text-emerald-700",
                },
                {
                  key: "partial",
                  label: "Partial",
                  c: "bg-yellow-100 text-yellow-700",
                },
                {
                  key: "minimal",
                  label: "Minimal",
                  c: "bg-red-100 text-red-700",
                },
              ].map(({ key, label, c }) => (
                <div key={key} className={`rounded-lg p-3 text-center ${c}`}>
                  <div className="text-xl font-bold">
                    {summary?.by_data_quality?.[key] ?? 0}
                  </div>
                  <div className="text-xs font-medium">{label}</div>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-1 gap-3 mt-3">
              <div className="rounded-lg p-3 border border-purple-200 bg-purple-50 text-center">
                <GraduationCap size={18} className="mx-auto text-purple-600 mb-1" />
                <div className="text-lg font-bold text-purple-700">
                  {summary?.by_profile_type?.master ?? 0}
                </div>
                <div className="text-xs text-purple-600">S2 Candidates</div>
              </div>
            </div>
          </div>
        </div>
      </Section>

      {/* ═══ SECTION 4: FUNNEL & EMAIL ═══ */}
      <Section title="Recruitment Funnel & Email Performance" icon={TrendingUp}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Lead Funnel
            </p>
            <div className="space-y-1.5">
              {Object.entries(funnel).map(([stage, count], i) => {
                const pct = maxFunnel > 0 ? (count / maxFunnel) * 100 : 0;
                return (
                  <div key={stage} className="flex items-center gap-2">
                    <span className="text-xs text-gray-600 w-28 truncate capitalize">
                      {stage.replace(/_/g, " ")}
                    </span>
                    <div
                      className="flex-1 h-5 rounded relative"
                      style={{
                        backgroundColor: `${FUNNEL_COLORS[i % FUNNEL_COLORS.length]}20`,
                      }}
                    >
                      <div
                        className="h-full rounded flex items-center justify-end pr-1.5 transition-all"
                        style={{
                          width: `${pct}%`,
                          backgroundColor:
                            FUNNEL_COLORS[i % FUNNEL_COLORS.length],
                          opacity: 0.8,
                        }}
                      >
                        {pct > 12 && (
                          <span className="text-xs text-white font-medium">
                            {count}
                          </span>
                        )}
                      </div>
                    </div>
                    <span className="text-xs font-semibold w-8 text-right text-gray-600">
                      {count}
                    </span>
                  </div>
                );
              })}
              {Object.keys(funnel).length === 0 && (
                <p className="text-sm text-gray-400 text-center py-4">
                  No funnel data
                </p>
              )}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Email Performance
            </p>
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="text-center p-3 bg-blue-50 rounded-xl">
                <Mail size={18} className="mx-auto text-blue-500 mb-1" />
                <div className="text-xl font-bold text-blue-700">
                  {summary?.email_stats?.total_sent ?? 0}
                </div>
                <div className="text-xs text-blue-600">Sent</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded-xl">
                <Eye size={18} className="mx-auto text-purple-500 mb-1" />
                <div className="text-xl font-bold text-purple-700">
                  {summary?.email_stats?.total_opened ?? 0}
                </div>
                <div className="text-xs text-purple-600">
                  Opened ({openRate}%)
                </div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-xl">
                <MessageSquare
                  size={18}
                  className="mx-auto text-green-500 mb-1"
                />
                <div className="text-xl font-bold text-green-700">
                  {summary?.email_stats?.total_replied ?? 0}
                </div>
                <div className="text-xs text-green-600">
                  Replied ({replyRate}%)
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Open Rate</span>
                <span className="font-semibold">{openRate}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2">
                <div
                  className="bg-purple-500 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(parseFloat(openRate), 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </Section>

      {/* ═══ SECTION 5: SCORE DISTRIBUTION & EDUCATION ═══ */}
      <Section title="Profile Scores & Education Breakdown" icon={Award}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Profile Score Distribution
            </p>
            <div className="grid grid-cols-5 gap-2">
              {[
                { key: "0-20", label: "0–20", color: "bg-red-500" },
                { key: "20-40", label: "20–40", color: "bg-orange-500" },
                { key: "40-60", label: "40–60", color: "bg-yellow-500" },
                { key: "60-80", label: "60–80", color: "bg-blue-500" },
                { key: "80-100", label: "80–100", color: "bg-green-500" },
              ].map(({ key, label, color }) => {
                const count = profileDist[key] ?? 0;
                const total = Object.values(profileDist).reduce(
                  (a, b) => a + b,
                  0,
                );
                const pct = total > 0 ? (count / total) * 100 : 0;
                return (
                  <div
                    key={key}
                    className="text-center p-2 bg-gray-50 rounded-lg"
                  >
                    <div className="text-lg font-bold">{count}</div>
                    <div className="text-xs text-gray-500">{label}</div>
                    <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                      <div
                        className={`${color} h-1.5 rounded-full`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              By Education Level
            </p>
            <div className="space-y-1.5">
              {Object.entries(byEducation).map(([level, count]) => {
                const total = Object.values(byEducation).reduce(
                  (a, b) => a + b,
                  0,
                );
                const pct = total > 0 ? (count / total) * 100 : 0;
                const colors = {
                  S3: "bg-purple-500",
                  S2: "bg-blue-500",
                  S1: "bg-green-500",
                  D3: "bg-yellow-500",
                  SMA: "bg-orange-500",
                };
                return (
                  <div key={level} className="flex items-center gap-2">
                    <span className="text-sm font-medium w-10">{level}</span>
                    <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${colors[level] ?? "bg-gray-400"}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-sm font-semibold w-16 text-right">
                      {count}
                      <span className="text-gray-400 text-xs ml-1">
                        ({pct.toFixed(0)}%)
                      </span>
                    </span>
                  </div>
                );
              })}
              {Object.keys(byEducation).length === 0 && (
                <p className="text-sm text-gray-400 text-center py-4">
                  No data
                </p>
              )}
            </div>
          </div>
        </div>
      </Section>

      {/* ═══ SECTION 6: PROGRAMS & TOP PROSPECTS ═══ */}
      <Section title="Program Matching & Top Prospects" icon={Target}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Study Fields (CS / MM / LAW)
            </p>
            <div className="space-y-1.5">
              {FIELDS.map((field) => {
                const count = summary?.by_field?.[field.key] ?? 0;
                const total = Object.values(summary?.by_field ?? {}).reduce(
                  (a, b) => a + b,
                  0,
                );
                const pct = total > 0 ? (count / total) * 100 : 0;
                const Icon = field.icon;
                return (
                  <div key={field.key} className="flex items-center gap-2">
                    <span className="text-xs text-gray-700 w-36 truncate flex items-center gap-1.5">
                      <Icon size={13} className={field.accent.icon} />
                      {field.label}
                    </span>
                    <div className="flex-1 bg-gray-100 rounded-full h-4">
                      <div
                        className={`h-4 rounded-full ${field.accent.dot}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-xs font-semibold w-8 text-right">
                      {count}
                    </span>
                  </div>
                );
              })}
              {Object.keys(summary?.by_field ?? {}).length === 0 && (
                <p className="text-sm text-gray-400 text-center py-4">
                  No field data yet — scrape CS, MM, or LAW to populate
                </p>
              )}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Top Prospects (Top 10)
            </p>
            {topProspects.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-4">
                No profiled leads yet
              </p>
            ) : (
              <div className="overflow-x-auto max-h-64 overflow-y-auto">
                <table className="w-full text-xs">
                  <thead className="bg-gray-50 border-b sticky top-0">
                    <tr>
                      {["#", "Name", "Field", "Score", "Source"].map(
                        (h) => (
                          <th
                            key={h}
                            className="px-2 py-2 text-left font-medium text-gray-600"
                          >
                            {h}
                          </th>
                        ),
                      )}
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {topProspects.map((p, i) => (
                      <tr key={p.id} className="hover:bg-gray-50">
                        <td className="px-2 py-2 text-gray-400">{i + 1}</td>
                        <td className="px-2 py-2 font-medium">{p.name}</td>
                        <td className="px-2 py-2">
                          {p.field ? (
                            (() => {
                              const f = getField(p.field);
                              return (
                                <span
                                  className={`px-1.5 py-0.5 rounded-full font-medium ${f.accent.softBg} ${f.accent.softActive}`}
                                >
                                  {f.shortLabel}
                                </span>
                              );
                            })()
                          ) : (
                            <span className="bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full">
                              —
                            </span>
                          )}
                        </td>
                        <td className="px-2 py-2">
                          <span
                            className={`font-bold px-1.5 py-0.5 rounded ${scoreBg(p.profile_score)} ${scoreColor(p.profile_score)}`}
                          >
                            {p.profile_score ?? "—"}
                          </span>
                        </td>
                        <td className="px-2 py-2 capitalize text-gray-500">
                          {p.source}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </Section>

      {/* ═══ SECTION 8: CAMPAIGNS ═══ */}
      <Section title={`Email Campaigns (${campaigns.length})`} icon={Mail}>
        <div className="flex justify-end mb-3">
          <button
            onClick={() => setShowCreateCampaign(true)}
            className="flex items-center gap-1.5 bg-rose-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-rose-700"
          >
            <Plus size={14} /> New Campaign
          </button>
        </div>
        {campaigns.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">
            No campaigns yet. Create your first campaign.
          </p>
        ) : (
          <div className="space-y-3">
            {campaigns.map((c) => {
              const s = c.stats || {};
              const sent = s.emails_sent || 0;
              const opened = s.opened || 0;
              const replied = s.replied || 0;
              const openRate =
                sent > 0 ? ((opened / sent) * 100).toFixed(1) : "0.0";
              return (
                <div key={c.id} className="bg-gray-50 rounded-lg border p-4">
                  <div className="flex items-start justify-between flex-wrap gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-sm">{c.name}</h3>
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${STATUS_COLORS[c.status] ?? "bg-gray-100 text-gray-600"}`}
                        >
                          {c.status}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                        <span>
                          Target:{" "}
                          <span className="font-medium capitalize">
                            {c.target_type}
                          </span>
                        </span>
                        <span>
                          {new Date(c.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 text-center">
                      <div>
                        <div className="text-sm font-bold">{sent}</div>
                        <div className="text-xs text-gray-400">Sent</div>
                      </div>
                      <div>
                        <div className="text-sm font-bold text-purple-600">
                          {opened}
                        </div>
                        <div className="text-xs text-gray-400">{openRate}%</div>
                      </div>
                      <div>
                        <div className="text-sm font-bold text-green-600">
                          {replied}
                        </div>
                        <div className="text-xs text-gray-400">Replied</div>
                      </div>
                    </div>
                    <div className="flex gap-1.5">
                      {c.status === "draft" && (
                        <button
                          onClick={() => handleActivate(c.id)}
                          className="flex items-center gap-1 px-2.5 py-1.5 bg-green-600 text-white rounded text-xs font-medium hover:bg-green-700"
                        >
                          <Play size={10} /> Activate
                        </button>
                      )}
                      {c.status === "active" && (
                        <>
                          <button
                            onClick={() => handlePause(c.id)}
                            className="flex items-center gap-1 px-2.5 py-1.5 bg-yellow-500 text-white rounded text-xs font-medium hover:bg-yellow-600"
                          >
                            <Pause size={10} /> Pause
                          </button>
                          <button
                            onClick={() => handleSendFollowUps(c.id)}
                            className="flex items-center gap-1 px-2.5 py-1.5 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700"
                          >
                            <Send size={10} /> Follow-ups
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                  {sent > 0 && (
                    <div className="mt-2 flex gap-0.5 h-1.5">
                      <div
                        className="bg-blue-500 rounded-l h-full"
                        style={{ flex: sent }}
                      />
                      <div
                        className="bg-purple-500 h-full"
                        style={{ flex: opened }}
                      />
                      <div
                        className="bg-green-500 rounded-r h-full"
                        style={{ flex: replied }}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </Section>

      {/* ═══ SECTION 9: ALL LEADS (with search/filter) ═══ */}
      <Section title={`All Leads (${leads.length})`} icon={Users}>
        <div className="flex items-center gap-3 mb-4 flex-wrap">
          <div className="relative flex-1 max-w-xs">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />
            <input
              type="text"
              value={leadSearch}
              onChange={(e) => setLeadSearch(e.target.value)}
              placeholder="Search by name or email..."
              className="w-full pl-9 pr-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select
            value={leadFilter}
            onChange={(e) => setLeadFilter(e.target.value)}
            className="px-3 py-2 border rounded-lg text-sm"
          >
            <option value="all">All Status</option>
            <option value="new">New</option>
            <option value="contacted">Contacted</option>
            <option value="replied">Replied</option>
            <option value="interested">Interested</option>
            <option value="enrolled">Enrolled</option>
            <option value="rejected">Rejected</option>
          </select>
          <span className="text-xs text-gray-400">
            {filteredLeads.length} of {leads.length}
          </span>
        </div>
        {filteredLeads.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">
            No leads match your filters.
          </p>
        ) : (
          <div className="overflow-x-auto max-h-80 overflow-y-auto">
            <table className="w-full text-xs">
              <thead className="bg-gray-50 border-b sticky top-0">
                <tr>
                  {[
                    "Name",
                    "Email",
                    "Status",
                    "Type",
                    "Score",
                    "Source",
                    "Education",
                    "Created",
                  ].map((h) => (
                    <th
                      key={h}
                      className="px-3 py-2 text-left font-medium text-gray-600"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y">
                {filteredLeads.map((l) => (
                  <tr key={l.id} className="hover:bg-gray-50">
                    <td className="px-3 py-2 font-medium">{l.name}</td>
                    <td className="px-3 py-2 text-gray-500">
                      {l.email || "—"}
                    </td>
                    <td className="px-3 py-2">
                      <span
                        className={`capitalize ${l.status === "new" ? "text-blue-600" : l.status === "contacted" ? "text-yellow-600" : l.status === "interested" ? "text-orange-600" : l.status === "enrolled" ? "text-emerald-600" : "text-gray-500"}`}
                      >
                        {l.status}
                      </span>
                    </td>
                    <td className="px-3 py-2 capitalize">
                      {l.profile_type || "—"}
                    </td>
                    <td className="px-3 py-2">
                      <span
                        className={`font-bold px-1.5 py-0.5 rounded ${scoreBg(l.profile_score)} ${scoreColor(l.profile_score)}`}
                      >
                        {l.profile_score ?? "—"}
                      </span>
                    </td>
                    <td className="px-3 py-2 capitalize text-gray-500">
                      {l.source}
                    </td>
                    <td className="px-3 py-2 text-gray-500">
                      {l.education_level || "—"}
                    </td>
                    <td className="px-3 py-2 text-gray-400">
                      {l.created_at
                        ? new Date(l.created_at).toLocaleDateString()
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      {/* ═══ SECTION 10: FEATURE SUMMARY ═══ */}
      <Section
        title="Feature Summary — All Versions Consolidated"
        icon={Sparkles}
        defaultOpen={false}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <h3 className="font-semibold text-blue-800 mb-2 flex items-center gap-1.5">
              <Linkedin size={14} /> LinkedIn Scraping
            </h3>
            <ul className="space-y-1 text-blue-700 text-xs">
              <li>• Puppeteer-based LinkedIn profile scraping</li>
              <li>• Search by keywords, university, location</li>
              <li>• Auto-extract skills, education, experience</li>
              <li>• Real-time streaming scrape results</li>
              <li>• Source: intake-agent, recruit-Z</li>
            </ul>
          </div>
          <div className="bg-emerald-50 rounded-lg p-4 border border-emerald-200">
            <h3 className="font-semibold text-emerald-800 mb-2 flex items-center gap-1.5">
              <GraduationCap size={14} /> Profiling Engine
            </h3>
            <ul className="space-y-1 text-emerald-700 text-xs">
              <li>• CS relevance scoring (39 keywords, 0-100)</li>
              <li>
                • Weighted scoring: academic 35%, engagement 20%, program fit
                30%, completeness 15%
              </li>
              <li>• Education analysis & degree normalization</li>
              <li>• Interest extraction (14 patterns)</li>
              <li>• Program matching (10 target programs)</li>
              <li>• Source: intake-agent-2, recruit-Z</li>
            </ul>
          </div>
          <div className="bg-rose-50 rounded-lg p-4 border border-rose-200">
            <h3 className="font-semibold text-rose-800 mb-2 flex items-center gap-1.5">
              <Mail size={14} /> Email Campaigns
            </h3>
            <ul className="space-y-1 text-rose-700 text-xs">
              <li>• Campaign CRUD with target type selection</li>
              <li>• HTML email templates with personalization</li>
              <li>• Template variables: name, program, university, etc.</li>
              <li>• Campaign activate/pause/send-test</li>
              <li>• Source: intake-agent-2 campaignController</li>
            </ul>
          </div>
          <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
            <h3 className="font-semibold text-amber-800 mb-2 flex items-center gap-1.5">
              <MessageSquare size={14} /> Conversation Pipeline
            </h3>
            <ul className="space-y-1 text-amber-700 text-xs">
              <li>• 9-stage pipeline: Inquiry → LoA Issued → Follow-up</li>
              <li>• Intent analysis with 9 intent patterns</li>
              <li>• Stage progression logic</li>
              <li>• Escalating follow-up messages (5 levels)</li>
              <li>• Source: auto-reply-email-bot replyGenerator</li>
            </ul>
          </div>
          <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
            <h3 className="font-semibold text-indigo-800 mb-2 flex items-center gap-1.5">
              <Eye size={14} /> Email Tracking
            </h3>
            <ul className="space-y-1 text-indigo-700 text-xs">
              <li>• 1×1 transparent GIF open tracking pixel</li>
              <li>• Link click tracking with redirect</li>
              <li>• Per-campaign open/click/reply stats</li>
              <li>• Source: intake-agent-2 tracking routes</li>
            </ul>
          </div>
          <div className="bg-cyan-50 rounded-lg p-4 border border-cyan-200">
            <h3 className="font-semibold text-cyan-800 mb-2 flex items-center gap-1.5">
              <RefreshCw size={14} /> Reply Monitoring
            </h3>
            <ul className="space-y-1 text-cyan-700 text-xs">
              <li>• IMAP-based inbox monitoring</li>
              <li>• Sentiment analysis (positive/negative/neutral)</li>
              <li>• Intent classification (6 intents)</li>
              <li>• Auto-response templates per intent</li>
              <li>• Source: recruit-Z replyMonitor, autoResponder</li>
            </ul>
          </div>
          <div className="bg-teal-50 rounded-lg p-4 border border-teal-200">
            <h3 className="font-semibold text-teal-800 mb-2 flex items-center gap-1.5">
              <BarChart2 size={14} /> Analytics
            </h3>
            <ul className="space-y-1 text-teal-700 text-xs">
              <li>• Summary KPIs (total, active, CS-related, scores)</li>
              <li>• Recruitment funnel (10 stages)</li>
              <li>• Weekly trends (12 weeks)</li>
              <li>• Profile score distribution (5 buckets)</li>
              <li>• Education & program breakdown</li>
              <li>• Top prospects ranking</li>
              <li>• Source: recruit-Z Analytics, intake-agent stats</li>
            </ul>
          </div>
          <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
            <h3 className="font-semibold text-orange-800 mb-2 flex items-center gap-1.5">
              <Users size={14} /> Data Processing
            </h3>
            <ul className="space-y-1 text-orange-700 text-xs">
              <li>• Email validation & phone cleaning</li>
              <li>• Name normalization & location parsing</li>
              <li>• Degree normalization (30+ variants)</li>
              <li>• Deduplication by email & LinkedIn URL</li>
              <li>• Data quality assessment (complete/partial/minimal)</li>
              <li>• Source: recruit-Z dataProcessor</li>
            </ul>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-1.5">
              <School size={14} /> Campus Intake
            </h3>
            <ul className="space-y-1 text-gray-700 text-xs">
              <li>• CSV import for alumni/internal data</li>
              <li>• Manual candidate entry</li>
              <li>• Cikarang industrial area scraping</li>
              <li>• Source: recruit-Z internalDataScraper</li>
            </ul>
          </div>
          <div className="bg-sky-50 rounded-lg p-4 border border-sky-200">
            <h3 className="font-semibold text-sky-800 mb-2 flex items-center gap-1.5">
              <Bot size={14} /> Auth & User Management
            </h3>
            <ul className="space-y-1 text-sky-700 text-xs">
              <li>• JWT-based authentication</li>
              <li>• Role-based access (admin/recruiter/viewer)</li>
              <li>• bcrypt password hashing</li>
              <li>• User registration & profile</li>
              <li>• Source: intake-agent-2 authController</li>
            </ul>
          </div>
          <div className="bg-pink-50 rounded-lg p-4 border border-pink-200">
            <h3 className="font-semibold text-pink-800 mb-2 flex items-center gap-1.5">
              <Download size={14} /> Export
            </h3>
            <ul className="space-y-1 text-pink-700 text-xs">
              <li>• CSV export by source</li>
              <li>• Excel export by source</li>
              <li>• Source: PRISM export routes</li>
            </ul>
          </div>
        </div>
      </Section>

      {/* ═══ CREATE CAMPAIGN MODAL ═══ */}
      {showCreateCampaign && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Plus size={18} className="text-rose-600" /> New Campaign
              </h2>
              <button
                onClick={() => setShowCreateCampaign(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>
            <form
              onSubmit={handleCreateCampaign}
              className="flex-1 overflow-auto p-6 space-y-4"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Campaign Name
                </label>
                <input
                  type="text"
                  value={campaignForm.name}
                  onChange={(e) =>
                    setCampaignForm({ ...campaignForm, name: e.target.value })
                  }
                  required
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-rose-500"
                  placeholder="e.g., S2 Informatics Outreach Q1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={campaignForm.description}
                  onChange={(e) =>
                    setCampaignForm({
                      ...campaignForm,
                      description: e.target.value,
                    })
                  }
                  rows={2}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-rose-500"
                  placeholder="Optional description"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Target Program
                </label>
                <select
                  value={campaignForm.target_type}
                  onChange={(e) =>
                    setCampaignForm({
                      ...campaignForm,
                      target_type: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-rose-500"
                >
                  <option value="master">S2</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Subject
                </label>
                <input
                  type="text"
                  value={campaignForm.email_template.subject}
                  onChange={(e) =>
                    setCampaignForm({
                      ...campaignForm,
                      email_template: {
                        ...campaignForm.email_template,
                        subject: e.target.value,
                      },
                    })
                  }
                  required
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-rose-500"
                  placeholder="Use {{name}}, {{program}} for personalization"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Body (HTML)
                </label>
                <textarea
                  value={campaignForm.email_template.body}
                  onChange={(e) =>
                    setCampaignForm({
                      ...campaignForm,
                      email_template: {
                        ...campaignForm.email_template,
                        body: e.target.value,
                      },
                    })
                  }
                  rows={6}
                  required
                  className="w-full px-3 py-2 border rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-rose-500"
                  placeholder={`<h2>Hello {{name}},</h2>\n<p>We noticed your interest in {{program}}...</p>`}
                />
                <p className="text-xs text-gray-400 mt-1">
                  Available variables:{" "}
                  {`{{name}}, {{firstName}}, {{program}}, {{university}}, {{location}}, {{skills}}, {{headline}}`}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Follow-up Delay (days)
                  </label>
                  <input
                    type="number"
                    value={campaignForm.follow_up.delay_days}
                    onChange={(e) =>
                      setCampaignForm({
                        ...campaignForm,
                        follow_up: {
                          ...campaignForm.follow_up,
                          delay_days: parseInt(e.target.value) || 3,
                        },
                      })
                    }
                    min={1}
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-rose-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Follow-ups
                  </label>
                  <input
                    type="number"
                    value={campaignForm.follow_up.max_follow_ups}
                    onChange={(e) =>
                      setCampaignForm({
                        ...campaignForm,
                        follow_up: {
                          ...campaignForm.follow_up,
                          max_follow_ups: parseInt(e.target.value) || 2,
                        },
                      })
                    }
                    min={1}
                    max={5}
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-rose-500"
                  />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="followup_enabled"
                  checked={campaignForm.follow_up.enabled}
                  onChange={(e) =>
                    setCampaignForm({
                      ...campaignForm,
                      follow_up: {
                        ...campaignForm.follow_up,
                        enabled: e.target.checked,
                      },
                    })
                  }
                  className="rounded border-gray-300"
                />
                <label
                  htmlFor="followup_enabled"
                  className="text-sm text-gray-700"
                >
                  Enable automatic follow-ups
                </label>
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setShowCreateCampaign(false)}
                  className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={busy}
                  className="flex items-center gap-2 bg-rose-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-rose-700 disabled:opacity-50"
                >
                  {busy && <Loader2 size={14} className="animate-spin" />}{" "}
                  Create Campaign
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}