import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { Search, Linkedin, ExternalLink, Mail, RefreshCw } from "lucide-react";

export default function AllLeadsPage() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [fieldFilter, setFieldFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [fetchingEmails, setFetchingEmails] = useState(false);
  const [emailResult, setEmailResult] = useState(null);
  const pageSize = 50;

  const fetchLeads = async (pageNum = page, overrides = {}) => {
    try {
      const status = overrides.status ?? statusFilter;
      const source = overrides.source ?? sourceFilter;
      const field = overrides.field ?? fieldFilter;
      const searchTerm = overrides.search ?? search;
      const params = { page: pageNum, page_size: pageSize };
      if (status !== "all") params.status = status;
      if (source !== "all") params.source = source;
      if (field !== "all") params.field = field;
      if (searchTerm.trim()) params.search = searchTerm.trim();
      const r = await axios.get("/api/leads", { params });
      setLeads(r.data?.data ?? r.data?.leads ?? []);
      setTotal(r.data?.total ?? 0);
      if (pageNum !== page) setPage(pageNum);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads(1);
  }, []);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const goToPage = (p) => {
    if (p < 1 || p > totalPages) return;
    setPage(p);
    setLoading(true);
    fetchLeads(p);
  };

  const handleSearchChange = (val) => {
    setSearch(val);
  };

  const handleSearchKeyDown = (e) => {
    if (e.key === "Enter") {
      setPage(1);
      setLoading(true);
      fetchLeads(1);
    }
  };

  const handleFilterChange = (setter, key) => (val) => {
    setter(val);
    setPage(1);
    setLoading(true);
    fetchLeads(1, { [key]: val });
  };

  const handleFetchEmails = async () => {
    if (fetchingEmails) return;
    setFetchingEmails(true);
    setEmailResult(null);
    try {
      // Process the currently visible leads without an email
      const ids = leads.filter((l) => !l.email).map((l) => l.id);
      const r = await axios.post("/api/leads/email-discovery/batch", { lead_ids: ids });
      setEmailResult(r.data);
      // Refresh to show newly found emails
      await fetchLeads(page);
    } catch (err) {
      setEmailResult({ total: 0, found: 0, error: err.message });
    } finally {
      setFetchingEmails(false);
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">All Leads</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          {total} total leads
          {totalPages > 1 && ` · Page ${page} of ${totalPages}`}
        </p>
      </div>

      <div className="flex gap-3 flex-wrap items-center">
        <div className="relative">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
          />
          <input
            type="text"
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            placeholder="Search leads... (press Enter)"
            className="border rounded-lg pl-9 pr-3 py-2 text-sm w-60"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => handleFilterChange(setStatusFilter, "status")(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="all">All Status</option>
          <option value="new">New</option>
          <option value="contacted">Contacted</option>
          <option value="replied">Replied</option>
          <option value="interested">Interested</option>
          <option value="enrolled">Enrolled</option>
          <option value="rejected">Rejected</option>
        </select>
        <select
          value={sourceFilter}
          onChange={(e) => handleFilterChange(setSourceFilter, "source")(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="all">All Sources</option>
          <option value="linkedin">LinkedIn</option>
          <option value="alumni">Campus</option>
        </select>
        <select
          value={fieldFilter}
          onChange={(e) => handleFilterChange(setFieldFilter, "field")(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="all">All Fields</option>
          <option value="computer_science">CS — Computer Science</option>
          <option value="management">MM — Management</option>
          <option value="law">MH — Law</option>
        </select>
        <button
          onClick={handleFetchEmails}
          disabled={fetchingEmails}
          className="ml-auto flex items-center gap-1.5 bg-emerald-600 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50"
          title="Search for emails of the visible leads without an email"
        >
          {fetchingEmails ? (
            <RefreshCw size={14} className="animate-spin" />
          ) : (
            <Mail size={14} />
          )}
          {fetchingEmails ? "Fetching emails..." : "Fetch Emails"}
        </button>
      </div>

      {/* Email fetch status */}
      {emailResult && !fetchingEmails && (
        <div
          className={`text-xs rounded-lg p-3 ${
            emailResult.error
              ? "bg-red-50 text-red-700 border border-red-200"
              : emailResult.found > 0
                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                : "bg-gray-50 text-gray-600 border border-gray-200"
          }`}
        >
          {emailResult.error
            ? `Error fetching emails: ${emailResult.error}`
            : emailResult.found > 0
              ? `✅ Found ${emailResult.found} of ${emailResult.total} emails`
              : `No emails found for the ${emailResult.total} leads checked.`}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : leads.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-8 text-center text-gray-400">
          No leads found.
        </div>
      ) : (
        <>
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Field</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">LinkedIn</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Email</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Headline / Company</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Location</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Education</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Type</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Score</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Source</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {leads.map((lead) => (
                    <tr key={lead.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <Link
                          to={`/leads/${lead.id}`}
                          className="font-medium text-blue-600 hover:text-blue-800"
                        >
                          {lead.name}
                        </Link>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {lead.field === "computer_science" && (
                          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">CS</span>
                        )}
                        {lead.field === "management" && (
                          <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">MM</span>
                        )}
                        {lead.field === "law" && (
                          <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">MH</span>
                        )}
                        {!lead.field && <span className="text-xs text-gray-400">—</span>}
                      </td>
                      <td className="px-4 py-3">
                        {lead.linkedin_url ? (
                          <a
                            href={lead.linkedin_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-500 hover:text-blue-700 flex items-center gap-1"
                            title={lead.linkedin_url}
                          >
                            <Linkedin size={12} />
                            <span className="truncate max-w-[110px] inline-block">
                              {lead.linkedin_url.split("/in/")[1]?.split("/")[0] || "Profile"}
                            </span>
                            <ExternalLink size={10} />
                          </a>
                        ) : (
                          <span className="text-xs text-gray-400">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-600 max-w-[160px] truncate" title={lead.email || ""}>
                        {lead.email || "—"}
                      </td>
                      <td className="px-4 py-3 max-w-[180px]">
                        <div className="text-xs">
                          {lead.headline && <div className="text-gray-700 truncate" title={lead.headline}>{lead.headline}</div>}
                          {lead.company && <div className="text-gray-400 truncate">{lead.company}</div>}
                          {!lead.headline && !lead.company && <span className="text-gray-400">—</span>}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-600 max-w-[130px] truncate" title={lead.location || ""}>
                        {lead.location || "—"}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {lead.education_level ? (
                          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                            {lead.education_level}
                          </span>
                        ) : (
                          <span className="text-xs text-gray-400">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs whitespace-nowrap">
                        <span className="capitalize">{lead.profile_type || "—"}</span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="relative group">
                          {lead.syllabus_confidence != null ? (
                            <>
                              <span className="text-xs font-semibold cursor-help">
                                {Math.round(lead.syllabus_confidence)}<span className="text-gray-400 font-normal">/100</span>
                              </span>
                              {/* Hover info panel */}
                              <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150">
                                <div className="bg-gray-900 text-white text-[11px] rounded-lg p-3 shadow-xl leading-relaxed">
                                  <p className="font-semibold mb-1.5">How this score is calculated</p>
                                  <div className="space-y-1 text-gray-300">
                                    <p><span className="text-blue-300">Skills match:</span> 50% weight</p>
                                    <p><span className="text-blue-300">Job title match:</span> 20% weight</p>
                                    <p><span className="text-blue-300">Headline match:</span> 15% weight</p>
                                    <p><span className="text-blue-300">Summary match:</span> 15% weight</p>
                                  </div>
                                  <hr className="border-gray-700 my-1.5" />
                                  <p className="text-gray-400">
                                    Score = avg of matched subject scores (max 100)
                                  </p>
                                  {lead.syllabus_top_match && (
                                    <p className="text-gray-400 mt-1">
                                      Top: <span className="text-green-300">{lead.syllabus_top_match}</span>
                                    </p>
                                  )}
                                  <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900" />
                                </div>
                              </div>
                            </>
                          ) : lead.priority_score != null ? (
                            <span className="text-xs font-semibold">{lead.priority_score}</span>
                          ) : (
                            <span className="text-xs text-gray-400">—</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-xs whitespace-nowrap">
                        <span className="capitalize">{lead.status}</span>
                      </td>
                      <td className="px-4 py-3 text-xs whitespace-nowrap">
                        <span className="capitalize">{lead.source}</span>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">
                        {new Date(lead.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* ═══ PAGINATION ═══ */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between bg-white rounded-xl shadow-sm px-4 py-3">
              <span className="text-xs text-gray-500">
                Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total} leads
              </span>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => goToPage(page - 1)}
                  disabled={page <= 1}
                  className="px-3 py-1.5 text-xs rounded-lg border hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Prev
                </button>
                {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 7) {
                    pageNum = i + 1;
                  } else if (page <= 4) {
                    pageNum = i + 1;
                  } else if (page >= totalPages - 3) {
                    pageNum = totalPages - 6 + i;
                  } else {
                    pageNum = page - 3 + i;
                  }
                  return (
                    <button
                      key={pageNum}
                      onClick={() => goToPage(pageNum)}
                      className={`px-3 py-1.5 text-xs rounded-lg border ${
                        pageNum === page
                          ? "bg-blue-600 text-white border-blue-600"
                          : "hover:bg-gray-50"
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
                <button
                  onClick={() => goToPage(page + 1)}
                  disabled={page >= totalPages}
                  className="px-3 py-1.5 text-xs rounded-lg border hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
