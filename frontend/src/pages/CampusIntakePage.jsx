import { useEffect, useState } from "react";
import axios from "axios";
import { Upload, Download, GraduationCap } from "lucide-react";

function getTrack(level) {
  if (!level) return "unknown";
  const l = level.toLowerCase();
  if (l.includes("master") || l.includes("s2") || l.includes("s3")) return "master";
  return "unknown";
}

function LeadTable({ leads, loading }) {
  if (loading) return <div className="text-center py-8 text-gray-400">Loading...</div>;
  if (leads.length === 0)
    return <div className="text-center py-8 text-gray-400">No campus leads yet.</div>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b">
          <tr>
            <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
            <th className="text-left px-4 py-3 font-medium text-gray-600">Email</th>
            <th className="text-left px-4 py-3 font-medium text-gray-600">Education</th>
            <th className="text-left px-4 py-3 font-medium text-gray-600">Score</th>
            <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
            <th className="text-left px-4 py-3 font-medium text-gray-600">Date</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {leads.map((lead) => (
            <tr key={lead.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 font-medium">{lead.name}</td>
              <td className="px-4 py-3 text-gray-600">{lead.email}</td>
              <td className="px-4 py-3">
                {lead.education_level ? (
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                    {lead.education_level}
                  </span>
                ) : (
                  <span className="text-xs text-gray-400">—</span>
                )}
              </td>
              <td className="px-4 py-3">
                {lead.priority_score != null ? (
                  <span className="text-xs font-semibold">{lead.priority_score}</span>
                ) : (
                  <span className="text-xs text-gray-400">—</span>
                )}
              </td>
              <td className="px-4 py-3 text-xs">
                <span className="capitalize">{lead.status}</span>
              </td>
              <td className="px-4 py-3 text-xs text-gray-400">
                {new Date(lead.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SectionHeader({
  title,
  count,
  icon: Icon,
}) {
  return (
    <div className="flex items-center gap-2 mb-2">
      <Icon size={18} className="text-blue-500" />
      <h2 className="font-semibold text-gray-800">
        {title}{" "}
        <span className="text-gray-400 font-normal">({count})</span>
      </h2>
    </div>
  );
}

export default function CampusIntakePage() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("all");

  const fetchLeads = async () => {
    try {
      const r = await axios.get("/api/leads", { params: { source: "alumni" } });
      setLeads(r.data?.data ?? r.data?.leads ?? []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, []);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    await axios.post("/api/leads/import/alumni", formData);
    fetchLeads();
  };

  const masterLeads = leads.filter(
    (l) => getTrack(l.education_level) === "master"
  );
  const unknownLeads = leads.filter(
    (l) => getTrack(l.education_level) === "unknown"
  );
  const filteredMaster =
    statusFilter === "all"
      ? masterLeads
      : masterLeads.filter((l) => l.status === statusFilter);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Campus Intake</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Alumni & internal student data import
          </p>
        </div>
        <label className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition cursor-pointer">
          <Upload size={16} />
          Upload CSV
          <input
            type="file"
            accept=".csv"
            onChange={handleUpload}
            className="hidden"
          />
        </label>
      </div>

      <div className="flex gap-3 flex-wrap items-center">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="all">All Status</option>
          <option value="new">New</option>
          <option value="contacted">Contacted</option>
          <option value="replied">Replied</option>
          <option value="interested">Interested</option>
          <option value="enrolled">Enrolled</option>
        </select>
        <div className="flex gap-2">
          <a
            href="/api/export/csv?source=alumni"
            className="flex items-center gap-1 text-xs text-blue-600 hover:underline"
          >
            <Download size={14} /> CSV
          </a>
          <a
            href="/api/export/excel?source=alumni"
            className="flex items-center gap-1 text-xs text-blue-600 hover:underline"
          >
            <Download size={14} /> Excel
          </a>
        </div>
      </div>

      <div className="space-y-2">
        <SectionHeader
          title="S2 Track Candidates"
          count={filteredMaster.length}
          icon={GraduationCap}
        />
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <LeadTable leads={filteredMaster} loading={loading} />
        </div>
      </div>

      {!loading && unknownLeads.length > 0 && (
        <details className="bg-gray-50 border rounded-xl p-4">
          <summary className="text-sm font-medium text-gray-600 cursor-pointer">
            Unknown Track ({unknownLeads.length})
          </summary>
          <div className="mt-3">
            <LeadTable leads={unknownLeads} loading={false} />
          </div>
        </details>
      )}
    </div>
  );
}
