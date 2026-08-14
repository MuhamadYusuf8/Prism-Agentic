import { useEffect, useState } from "react";
import axios from "axios";
import {
  TrendingUp,
  Users,
  Award,
  Target,
  MessageSquare,
  GraduationCap,
  BarChart2,
} from "lucide-react";

function scoreColor(score) {
  if (score == null) return "text-gray-400";
  if (score >= 80) return "text-green-600";
  if (score >= 60) return "text-yellow-600";
  return "text-red-600";
}

function scoreBg(score) {
  if (score == null) return "bg-gray-100";
  if (score >= 80) return "bg-green-100";
  if (score >= 60) return "bg-yellow-100";
  return "bg-red-100";
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState(null);
  const [funnel, setFunnel] = useState({});
  const [byEducation, setByEducation] = useState({});
  const [byProgram, setByProgram] = useState({});
  const [profileDist, setProfileDist] = useState({});
  const [topProspects, setTopProspects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      axios.get("/api/analytics/summary"),
      axios.get("/api/analytics/funnel"),
      axios.get("/api/analytics/by-education"),
      axios.get("/api/analytics/by-program"),
      axios.get("/api/analytics/profile-distribution"),
      axios.get("/api/analytics/top-prospects"),
    ])
      .then(([sRes, fRes, eduRes, progRes, distRes, topRes]) => {
        setSummary(sRes.data);
        setFunnel(fRes.data);
        setByEducation(eduRes.data?.by_level ?? {});
        setByProgram(
          Object.fromEntries(
            progRes.data.map((item) => [
              item.program,
              item.count,
            ])
          )
        );
        setProfileDist(
          Array.isArray(distRes.data)
            ? Object.fromEntries(distRes.data.map((d) => [d.range, d.count]))
            : (distRes.data ?? {})
        );
        setTopProspects(topRes.data?.data ?? []);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-center py-12 text-gray-400">Loading...</div>;
  }

  const funnelEntries = Object.entries(funnel);
  const openRate =
    summary?.email_stats?.total_sent
      ? (
          (summary.email_stats.total_opened / summary.email_stats.total_sent) *
          100
        ).toFixed(1)
      : "0";
  const replyRate =
    summary?.email_stats?.total_sent
      ? (
          (summary.email_stats.total_replied / summary.email_stats.total_sent) *
          100
        ).toFixed(1)
      : "0";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Detailed recruitment analytics & insights
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-1">
            <Users size={16} className="text-blue-500" />
            <span className="text-xs text-gray-500">Total Leads</span>
          </div>
          <div className="text-2xl font-bold">{summary?.total_leads ?? 0}</div>
        </div>
        <div className="bg-white rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp size={16} className="text-green-500" />
            <span className="text-xs text-gray-500">Active Leads</span>
          </div>
          <div className="text-2xl font-bold">{summary?.active_leads ?? 0}</div>
        </div>
        <div className="bg-white rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-1">
            <Award size={16} className="text-purple-500" />
            <span className="text-xs text-gray-500">Avg Profile Score</span>
          </div>
          <div className="text-2xl font-bold">
            {summary?.avg_profile_score?.toFixed(1) ?? "0"}
          </div>
        </div>
        <div className="bg-white rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-1">
            <Target size={16} className="text-orange-500" />
            <span className="text-xs text-gray-500">Avg Priority Score</span>
          </div>
          <div className="text-2xl font-bold">
            {summary?.avg_priority_score?.toFixed(1) ?? "0"}
          </div>
        </div>
      </div>

      {/* Funnel & Email */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border p-5">
          <h2 className="font-semibold text-sm mb-3">Recruitment Funnel</h2>
          <div className="space-y-2">
            {funnelEntries.map(([stage, count], i) => {
              const colors = [
                "bg-blue-500",
                "bg-indigo-500",
                "bg-purple-500",
                "bg-pink-500",
                "bg-orange-500",
                "bg-emerald-500",
              ];
              const maxCount = Math.max(...funnelEntries.map(([, c]) => c), 1);
              return (
                <div key={stage} className="flex items-center gap-3">
                  <span className="text-xs w-24 text-gray-600 capitalize">
                    {stage}
                  </span>
                  <div className="flex-1 bg-gray-100 rounded-full h-5">
                    <div
                      className={`h-5 rounded-full ${colors[i % colors.length]} transition-all`}
                      style={{ width: `${(count / maxCount) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-semibold w-8 text-right">
                    {count}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-white rounded-xl border p-5">
          <h2 className="font-semibold text-sm mb-3">Email Performance</h2>
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="text-center p-3 bg-blue-50 rounded-xl">
              <div className="text-xl font-bold text-blue-700">
                {summary?.email_stats?.total_sent ?? 0}
              </div>
              <div className="text-xs text-blue-600">Sent</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-xl">
              <div className="text-xl font-bold text-green-700">
                {summary?.email_stats?.total_opened ?? 0}
              </div>
              <div className="text-xs text-green-600">Opened ({openRate}%)</div>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-xl">
              <div className="text-xl font-bold text-purple-700">
                {summary?.email_stats?.total_replied ?? 0}
              </div>
              <div className="text-xs text-purple-600">
                Replied ({replyRate}%)
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <MessageSquare size={14} />
            <span>
              {summary?.total_campaigns ?? 0} campaigns (
              {summary?.active_campaigns ?? 0} active)
            </span>
          </div>
        </div>
      </div>

      {/* Profile Distribution & Education */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border p-5">
          <h2 className="font-semibold text-sm mb-3">Profile Distribution</h2>
          <div className="space-y-2">
            {Object.entries(profileDist).map(([type, count]) => {
              const colors = {
                master: "bg-blue-100 text-blue-700",
              };
              const c = colors[type] ?? "bg-gray-100 text-gray-700";
              return (
                <div key={type} className="flex items-center justify-between">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${c}`}>
                    {type}
                  </span>
                  <span className="text-sm font-semibold">{count}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-white rounded-xl border p-5">
          <h2 className="font-semibold text-sm mb-3">Education Breakdown</h2>
          <div className="space-y-2">
            {Object.entries(byEducation).map(([level, count]) => (
              <div key={level} className="flex items-center justify-between">
                <span className="text-xs text-gray-600">{level}</span>
                <span className="text-sm font-semibold">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Program Matching */}
      <div className="bg-white rounded-xl border p-5">
        <h2 className="font-semibold text-sm mb-3">Program Matching</h2>
        {Object.keys(byProgram).length === 0 ? (
          <p className="text-xs text-gray-400">No program data yet.</p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(byProgram)
              .sort(([, a], [, b]) => b - a)
              .map(([program, count]) => (
                <div
                  key={program}
                  className="bg-gray-50 rounded-lg p-3 text-center"
                >
                  <div className="text-lg font-bold">{count}</div>
                  <div className="text-xs text-gray-500">{program}</div>
                </div>
              ))}
          </div>
        )}
      </div>

      {/* Top Prospects */}
      <div className="bg-white rounded-xl border p-5">
        <h2 className="font-semibold text-sm mb-3">Top Prospects</h2>
        {topProspects.length === 0 ? (
          <p className="text-xs text-gray-400">No prospects yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  {["#", "Name", "Type", "CS", "Score", "Source"].map((h) => (
                    <th
                      key={h}
                      className="text-left px-4 py-3 font-medium text-gray-600"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y">
                {topProspects.map((p, i) => (
                  <tr key={p.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-xs text-gray-400">{i + 1}</td>
                    <td className="px-4 py-3 font-medium">{p.name}</td>
                    <td className="px-4 py-3 text-xs capitalize">
                      {p.profile_type || "—"}
                    </td>
                    <td className="px-4 py-3">
                      {p.is_computer_science_related !== null ? (
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full ${
                            p.is_computer_science_related
                              ? "bg-green-100 text-green-700"
                              : "bg-red-100 text-red-700"
                          }`}
                        >
                          {p.is_computer_science_related ? "Yes" : "No"}
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {p.priority_score != null ? (
                        <span
                          className={`text-xs font-semibold px-2 py-0.5 rounded-full ${scoreBg(p.priority_score)} ${scoreColor(p.priority_score)}`}
                        >
                          {p.priority_score}
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs capitalize">
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
  );
}
