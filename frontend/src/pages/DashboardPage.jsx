import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { StatCard } from "../components/ui/StatCard";
import { FunnelChart } from "../components/ui/FunnelChart";
import { TrendsChart } from "../components/ui/TrendsChart";
import {
  Linkedin,
  Briefcase,
  TrendingUp,
  Mail,
  Target,
} from "lucide-react";
import IconSelect from "../components/ui/IconSelect";
import { FIELDS, getField } from "../scraping";

const defaultSummary = {
  total_leads: 0,
  active_leads: 0,
  cs_related: 0,
  avg_profile_score: 0,
  avg_priority_score: 0,
  by_status: {},
  by_source: {},
  by_type: {},
  by_field: {},
  by_data_quality: {},
  master_track: 0,
  total_campaigns: 0,
  active_campaigns: 0,
  email_stats: { total_sent: 0, total_opened: 0, total_replied: 0 },
  clusters: [],
};

function SourceCard({
  icon: Icon,
  label,
  count,
  sub,
  color,
}) {
  return (
    <div className={`rounded-xl p-4 border flex items-center gap-3 ${color}`}>
      <div className="p-2.5 bg-white/60 rounded-lg">
        <Icon size={20} />
      </div>
      <div>
        <div className="text-2xl font-bold leading-none">{count}</div>
        <div className="text-sm font-medium mt-0.5">{label}</div>
        <div className="text-xs text-gray-500">{sub}</div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(defaultSummary);
  const [activeFieldKey, setActiveFieldKey] = useState(FIELDS[0].key);
  const activeField = getField(activeFieldKey);

  useEffect(() => {
    axios.get("/api/analytics/summary").then((r) => setSummary(r.data));
  }, []);

  const linkedinCount = summary.by_source?.linkedin ?? 0;
  const openRate =
    summary.email_stats?.total_sent > 0
      ? (
          (summary.email_stats.total_opened / summary.email_stats.total_sent) *
          100
        ).toFixed(1)
      : "0";
  const replyRate =
    summary.email_stats?.total_sent > 0
      ? (
          (summary.email_stats.total_replied / summary.email_stats.total_sent) *
          100
        ).toFixed(1)
      : "0";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Recruitment pipeline overview — President University
        </p>
      </div>

      {/* ── Field selector ───────────────────────────────────── */}
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

      {/* ── Row 1: Top KPIs ──────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Leads" value={summary.total_leads ?? 0} />
        <StatCard label="Active Leads" value={summary.active_leads ?? 0} />
        <StatCard label="CS Related" value={summary.cs_related ?? 0} />
        <StatCard
          label="Avg Profile Score"
          value={summary.avg_profile_score?.toFixed(1) ?? "0"}
        />
      </div>

      {/* ── Row 2: Source & Study Field breakdown ───────────── */}
      <div>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          By Source & Study Field
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <SourceCard
            icon={Linkedin}
            label="LinkedIn Leads"
            count={linkedinCount}
            sub="CS / MM / LAW professionals"
            color="border-blue-200 bg-blue-50 text-blue-800"
          />
          {FIELDS.map((field) => {
            const Icon = field.icon;
            return (
              <SourceCard
                key={field.key}
                icon={Icon}
                label={field.shortLabel}
                count={summary.by_field?.[field.key] ?? 0}
                sub={field.degree}
                color={`${field.accent.softBg} ${field.accent.softActive}`}
              />
            );
          })}
        </div>
      </div>

      {/* ── Row 3: Pipeline status ───────────────────────────── */}
      <div>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Pipeline Status
        </h2>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
          {[
            { key: "new", label: "New", color: "bg-blue-100 text-blue-700" },
            {
              key: "contacted",
              label: "Contacted",
              color: "bg-yellow-100 text-yellow-700",
            },
            {
              key: "replied",
              label: "Replied",
              color: "bg-purple-100 text-purple-700",
            },
            {
              key: "interested",
              label: "Interested",
              color: "bg-orange-100 text-orange-700",
            },
            {
              key: "enrolled",
              label: "Enrolled",
              color: "bg-emerald-100 text-emerald-700",
            },
            {
              key: "rejected",
              label: "Rejected",
              color: "bg-red-100 text-red-700",
            },
          ].map(({ key, label, color }) => (
            <div key={key} className={`rounded-xl p-3 text-center ${color}`}>
              <div className="text-xl font-bold">
                {summary.by_status?.[key] ?? 0}
              </div>
              <div className="text-xs font-medium mt-0.5">{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Row 4: Campaign & Email Performance ─────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-3">
            <Mail size={16} className="text-blue-500" />
            <h2 className="font-semibold text-sm">Email Performance</h2>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center">
              <div className="text-xl font-bold text-gray-800">
                {summary.email_stats?.total_sent ?? 0}
              </div>
              <div className="text-xs text-gray-500">Sent</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-green-600">
                {summary.email_stats?.total_opened ?? 0}
              </div>
              <div className="text-xs text-gray-500">Opened ({openRate}%)</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-purple-600">
                {summary.email_stats?.total_replied ?? 0}
              </div>
              <div className="text-xs text-gray-500">
                Replied ({replyRate}%)
              </div>
            </div>
          </div>
          <div className="mt-3 w-full bg-gray-100 rounded-full h-2">
            <div
              className="h-2 rounded-full bg-green-400 transition-all"
              style={{ width: `${Math.min(parseFloat(openRate), 100)}%` }}
            />
          </div>
          <div className="mt-3">
            <Link
              to="/email"
              className="text-xs font-medium text-blue-600 hover:text-blue-800"
            >
              View all campaigns →
            </Link>
          </div>
        </div>

        <div className="bg-white rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-3">
            <Target size={16} className="text-orange-500" />
            <h2 className="font-semibold text-sm">Campaigns Overview</h2>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center">
              <div className="text-xl font-bold text-gray-800">
                {summary.total_campaigns ?? 0}
              </div>
              <div className="text-xs text-gray-500">Total Campaigns</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-emerald-600">
                {summary.active_campaigns ?? 0}
              </div>
              <div className="text-xs text-gray-500">Active</div>
            </div>
          </div>
          <div className="mt-3">
            <Link
              to="/email"
              className="text-xs font-medium text-blue-600 hover:text-blue-800"
            >
              Manage campaigns →
            </Link>
          </div>
        </div>
      </div>

      {/* ── Row 5: Charts ───────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={16} className="text-gray-400" />
            <h2 className="font-semibold">Lead Funnel</h2>
          </div>
          <FunnelChart />
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={16} className="text-gray-400" />
            <h2 className="font-semibold">Weekly New Leads</h2>
          </div>
          <TrendsChart />
        </div>
      </div>

      {/* ── Row 6: Study Field Breakdown ────────────────────── */}
      <div>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Study Field Breakdown (CS / MM / LAW)
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {FIELDS.map((field) => {
            const Icon = field.icon;
            return (
              <div
                key={field.key}
                className={`rounded-xl p-3 text-center border ${field.accent.softBg} ${field.accent.softActive}`}
              >
                <Icon
                  size={18}
                  className={`mx-auto mb-1 ${field.accent.icon}`}
                />
                <div className={`text-xl font-bold ${field.accent.text}`}>
                  {summary.by_field?.[field.key] ?? 0}
                </div>
                <div className="text-xs font-medium mt-0.5">
                  {field.shortLabel}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Row 7: Data Quality ─────────────────────────────── */}
      {summary.by_data_quality &&
        Object.keys(summary.by_data_quality).length > 0 && (
          <div>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Data Quality
            </h2>
            <div className="grid grid-cols-3 gap-4">
              {[
                {
                  key: "complete",
                  label: "Complete",
                  color: "bg-emerald-100 text-emerald-700",
                },
                {
                  key: "partial",
                  label: "Partial",
                  color: "bg-yellow-100 text-yellow-700",
                },
                {
                  key: "minimal",
                  label: "Minimal",
                  color: "bg-red-100 text-red-700",
                },
              ].map(({ key, label, color }) => (
                <div
                  key={key}
                  className={`rounded-xl p-3 text-center ${color}`}
                >
                  <div className="text-xl font-bold">
                    {summary.by_data_quality?.[key] ?? 0}
                  </div>
                  <div className="text-xs font-medium mt-0.5">{label}</div>
                </div>
              ))}
            </div>
          </div>
        )}
    </div>
  );
}
