import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import {
  Users, Mail, FileText, MessageSquare, Award, GraduationCap,
  RefreshCw, ChevronRight, Search, Filter,
} from "lucide-react";

// ── Pipeline Stage Definitions ────────────────────────────────────────────────

const STAGES = [
  {
    key: "new",
    label: "New Leads",
    icon: Users,
    color: "bg-gray-100",
    headerColor: "bg-gray-200",
    textColor: "text-gray-700",
    borderColor: "border-gray-200",
  },
  {
    key: "contacted",
    label: "Contacted",
    icon: Mail,
    color: "bg-blue-50",
    headerColor: "bg-blue-100",
    textColor: "text-blue-700",
    borderColor: "border-blue-200",
  },
  {
    key: "interested",
    label: "Interested",
    icon: MessageSquare,
    color: "bg-yellow-50",
    headerColor: "bg-yellow-100",
    textColor: "text-yellow-700",
    borderColor: "border-yellow-200",
  },
  {
    key: "applied",
    label: "Applied",
    icon: FileText,
    color: "bg-purple-50",
    headerColor: "bg-purple-100",
    textColor: "text-purple-700",
    borderColor: "border-purple-200",
  },
  {
    key: "enrolled",
    label: "Enrolled",
    icon: GraduationCap,
    color: "bg-green-50",
    headerColor: "bg-green-100",
    textColor: "text-green-700",
    borderColor: "border-green-200",
  },
];

const STATUS_TO_STAGE = {
  new: "new",
  contacted: "contacted",
  replied: "contacted",
  interested: "interested",
  applied: "applied",
  enrolled: "enrolled",
  not_interested: null,
  unsubscribed: null,
};

// ── Lead Card ─────────────────────────────────────────────────────────────────

function LeadCard({ lead, onClick }) {
  const score = lead.priority_score ?? lead.cs_relevance_score;
  const scoreColor =
    score >= 80 ? "bg-green-100 text-green-700" :
    score >= 60 ? "bg-yellow-100 text-yellow-700" :
    score != null ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-500";

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg border border-gray-100 p-3 shadow-sm hover:shadow-md
        hover:border-blue-200 transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-gray-800 truncate group-hover:text-blue-600 transition-colors">
            {lead.name || "Unknown"}
          </p>
          <p className="text-xs text-gray-500 truncate mt-0.5">
            {lead.headline || lead.job_title || "—"}
          </p>
        </div>
        {score != null && (
          <span className={`shrink-0 text-[10px] font-bold px-1.5 py-0.5 rounded ${scoreColor}`}>
            {score}
          </span>
        )}
      </div>

      {lead.recommended_program && (
        <p className="text-[10px] text-indigo-600 bg-indigo-50 rounded px-1.5 py-0.5 mt-2 truncate">
          {lead.recommended_program}
        </p>
      )}

      <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-50">
        <div className="flex items-center gap-1 flex-wrap">
          {lead.email && (
            <span className="text-[10px] text-green-600 bg-green-50 px-1.5 py-0.5 rounded">
              ✉ Email
            </span>
          )}
          {lead.source && (
            <span className="text-[10px] text-gray-500 bg-gray-50 px-1.5 py-0.5 rounded capitalize">
              {lead.source}
            </span>
          )}
        </div>
        <ChevronRight size={12} className="text-gray-300 group-hover:text-blue-400 transition-colors" />
      </div>
    </div>
  );
}

// ── Kanban Column ─────────────────────────────────────────────────────────────

function KanbanColumn({ stage, leads, onLeadClick }) {
  const Icon = stage.icon;
  return (
    <div className={`rounded-xl border ${stage.borderColor} flex flex-col min-h-[500px] min-w-[220px] w-full`}>
      {/* Column Header */}
      <div className={`${stage.headerColor} rounded-t-xl px-3 py-2.5 flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <Icon size={14} className={stage.textColor} />
          <span className={`text-xs font-semibold ${stage.textColor}`}>{stage.label}</span>
        </div>
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full bg-white ${stage.textColor}`}>
          {leads.length}
        </span>
      </div>

      {/* Cards */}
      <div className={`${stage.color} flex-1 p-2 rounded-b-xl space-y-2 overflow-y-auto max-h-[600px]`}>
        {leads.length === 0 ? (
          <div className="flex items-center justify-center h-24 text-xs text-gray-400">
            No leads
          </div>
        ) : (
          leads.map((lead) => (
            <LeadCard key={lead.id} lead={lead} onClick={() => onLeadClick(lead.id)} />
          ))
        )}
      </div>
    </div>
  );
}

// ── Main Pipeline Page ────────────────────────────────────────────────────────

export default function PipelinePage() {
  const navigate = useNavigate();
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("all");
  const [overview, setOverview] = useState(null);

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page_size: 200 };
      if (source !== "all") params.source = source;
      const [leadsRes, overviewRes] = await Promise.allSettled([
        axios.get("/api/leads", { params }),
        axios.get("/api/analytics/summary"),
      ]);
      if (leadsRes.status === "fulfilled") {
        setLeads(leadsRes.value.data?.data ?? leadsRes.value.data?.leads ?? []);
      }
      if (overviewRes.status === "fulfilled") {
        setOverview(overviewRes.value.data);
      }
    } finally {
      setLoading(false);
    }
  }, [source]);

  useEffect(() => { fetchLeads(); }, [fetchLeads]);

  // Distribute leads into pipeline stages
  const grouped = STAGES.reduce((acc, stage) => {
    acc[stage.key] = [];
    return acc;
  }, {});

  const searchLower = search.toLowerCase();
  const filtered = search
    ? leads.filter(
        (l) =>
          (l.name || "").toLowerCase().includes(searchLower) ||
          (l.headline || "").toLowerCase().includes(searchLower) ||
          (l.email || "").toLowerCase().includes(searchLower)
      )
    : leads;

  for (const lead of filtered) {
    const stageKey = STATUS_TO_STAGE[lead.status];
    if (stageKey && grouped[stageKey]) {
      grouped[stageKey].push(lead);
    }
  }

  // Sort each column by priority score (desc)
  for (const key in grouped) {
    grouped[key].sort((a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0));
  }

  const totalActive = filtered.filter((l) => STATUS_TO_STAGE[l.status] !== null).length;
  const totalExcluded = filtered.filter((l) => STATUS_TO_STAGE[l.status] === null).length;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Recruitment Pipeline</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Visualisasi alur kandidat dari New → Enrolled
          </p>
        </div>
        <button
          onClick={fetchLeads}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-2 text-sm border rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {/* Stats Bar */}
      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {STAGES.map((stage) => {
            const Icon = stage.icon;
            return (
              <div key={stage.key} className={`${stage.color} border ${stage.borderColor} rounded-xl p-3 flex items-center gap-2`}>
                <Icon size={16} className={stage.textColor} />
                <div>
                  <div className={`text-lg font-bold ${stage.textColor}`}>
                    {grouped[stage.key]?.length ?? 0}
                  </div>
                  <div className="text-[10px] text-gray-500">{stage.label}</div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Cari nama, headline, email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter size={14} className="text-gray-400" />
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="text-sm border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">Semua Sumber</option>
            <option value="linkedin">LinkedIn</option>
            <option value="alumni">Alumni</option>
            <option value="manual">Manual</option>
          </select>
        </div>
        <p className="text-xs text-gray-400">
          {totalActive} kandidat aktif · {totalExcluded} di-exclude
        </p>
      </div>

      {/* Kanban Board */}
      {loading ? (
        <div className="flex items-center justify-center py-16 text-gray-400">
          <RefreshCw size={20} className="animate-spin mr-2" /> Loading pipeline...
        </div>
      ) : (
        <div className="overflow-x-auto pb-4">
          <div className="flex gap-4 min-w-max">
            {STAGES.map((stage) => (
              <div key={stage.key} className="w-56">
                <KanbanColumn
                  stage={stage}
                  leads={grouped[stage.key] || []}
                  onLeadClick={(id) => navigate(`/leads/${id}`)}
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
