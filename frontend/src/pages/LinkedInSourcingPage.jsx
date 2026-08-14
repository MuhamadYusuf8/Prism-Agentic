import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import axios from "axios";
import {
  Linkedin,
  Search,
  X,
  Download,
  ExternalLink,
  Sparkles,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { FIELDS, getField, computeRelevance } from "../scraping";
import IconSelect from "../components/ui/IconSelect";

export default function LinkedInSourcingPage() {
  const [searchParams] = useSearchParams();
  const initialField = getField(searchParams.get("field"));
  const [activeFieldKey, setActiveFieldKey] = useState(initialField.key);
  const activeField = getField(activeFieldKey);

  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("all");
  const [showModal, setShowModal] = useState(false);
  const [customQuery, setCustomQuery] = useState("");
  const [scraping, setScraping] = useState(false);
  const [scrapedProfiles, setScrapedProfiles] = useState([]);
  const [scrapeLog, setScrapeLog] = useState([]);
  const [activePreset, setActivePreset] = useState(null);
  const [selectedSubField, setSelectedSubField] = useState(null);
  const [scrapeError, setScrapeError] = useState(null);
  const [scrapeCount, setScrapeCount] = useState(0);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 50;
  const abortRef = useRef(null);

  const fetchLeads = async (pageNum = page) => {
    try {
      const r = await axios.get("/api/leads", {
        params: { source: "linkedin", page: pageNum, page_size: pageSize },
      });
      const data = r.data?.data ?? r.data?.leads ?? [];
      setLeads(data);
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

  const openModal = () => {
    setCustomQuery("");
    setScrapedProfiles([]);
    setScrapeLog([]);
    setScrapeError(null);
    setActivePreset(null);
    setSelectedSubField(null);
    setScrapeCount(0);
    setShowModal(true);
  };

  const switchField = (key) => {
    if (key === activeFieldKey || scraping) return;
    setActiveFieldKey(key);
    setActivePreset(null);
    setSelectedSubField(null);
    setCustomQuery("");
    setScrapedProfiles([]);
    setScrapeLog([]);
    setScrapeError(null);
    setScrapeCount(0);
  };

  const startScrape = async (presetQueries) => {
    const queries = presetQueries || (customQuery.trim() ? [customQuery.trim()] : null);
    if (!queries || queries.length === 0) return;

    setScraping(true);
    setScrapedProfiles([]);
    setScrapeLog([]);
    setScrapeError(null);
    setScrapeCount(0);
    abortRef.current = new AbortController();

    try {
      const body = JSON.stringify({
        search_queries: queries,
        max_profiles: 50,
        field: activeField.key,
      });
      const r = await fetch("/api/scraper/linkedin/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
        signal: abortRef.current.signal,
      });

      if (!r.ok) {
        const errText = await r.text().catch(() => "");
        throw new Error(`Server error ${r.status}: ${errText || r.statusText}`);
      }

      const reader = r.body?.getReader();
      if (!reader) throw new Error("ReadableStream not supported");

      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n").filter(Boolean);
        for (const line of lines) {
          try {
            const ev = JSON.parse(line.replace(/^data: /, ""));
            handleEvent(ev);
          } catch {
            // ignore parse errors
          }
        }
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        setScrapeError(err.message);
        setScrapeLog((prev) => [...prev, `❌ Error: ${err.message}`]);
      }
    } finally {
      setScraping(false);
      abortRef.current = null;
      fetchLeads();
    }
  };

  const handleEvent = (e) => {
    switch (e.type) {
      case "start":
        setScrapeLog((prev) => [...prev, `🔍 Starting ${activeField.label} profile search...`]);
        break;
      case "query":
        setScrapeLog((prev) => [...prev, `📄 Searching: ${e.query}`]);
        break;
      case "phase":
        setScrapeLog((prev) => [...prev, `⚙️ ${e.phase}`]);
        break;
      case "profile":
        if (e.profile) {
          setScrapedProfiles((prev) => [...prev, e.profile]);
          setScrapeCount((prev) => prev + 1);
          const rel = computeRelevance(e.profile.skills, activeField);
          setScrapeLog((prev) => [
            ...prev,
            `👤 ${e.profile.name} — ${e.profile.headline || e.profile.job_title || ""} ${rel.level !== "unknown" ? `[${rel.label} ${activeField.shortLabel}]` : ""}`,
          ]);
        }
        break;
      case "query_done":
        setScrapeLog((prev) => [...prev, `📊 ${e.new_profiles} new profiles found (${e.total_so_far} total)`]);
        break;
      case "saved":
        if (e.inserted != null) {
          const parts = [`💾 ${e.inserted} new saved`];
          if (e.updated > 0) parts.push(`${e.updated} already existed (updated)`);
          if (e.failed > 0) parts.push(`${e.failed} failed`);
          setScrapeLog((prev) => [...prev, parts.join(", ")]);
        } else {
          setScrapeLog((prev) => [...prev, `💾 ${e.count} profiles saved to DB`]);
        }
        break;

      // ── Phase 1 events ──────────────────────────────────────────
      case "phase_1_start":
        setScrapeLog((prev) => [...prev, `🔍 Phase 1: Discovering profiles from Google...`]);
        break;
      case "phase_1_done":
        setScrapeLog((prev) => [...prev,
          `✅ Phase 1 done — ${e.profiles_found} found, ${e.inserted ?? 0} new, ${e.updated ?? 0} duplicate${(e.updated ?? 0) === 1 ? "" : "s"} updated`
        ]);
        break;

      // ── Phase 2: Email Discovery events ─────────────────────────
      case "phase_2_start":
        setScrapeLog((prev) => [...prev, `📧 Phase 2: Finding emails for ${e.total_profiles} profiles...`]);
        break;
      case "email_found":
        setScrapeLog((prev) => [...prev,
          `📧 ${e.email} — ${e.name}${e.source ? ` (via ${e.source})` : ""}`
        ]);
        break;
      case "email_skip":
        setScrapeLog((prev) => [...prev, `📧 No email found for ${e.name}`]);
        break;
      case "phase_2_done":
        setScrapeLog((prev) => [...prev,
          `✅ Phase 2 done — ${e.found} emails found, ${e.failed} no email`
        ]);
        break;

      // ── Syllabus matching ───────────────────────────────────────
      case "syllabus_matched":
        setScrapeLog((prev) => [...prev, `📊 Syllabus matched for ${e.total} leads`]);
        break;

      case "done":
        setScrapeLog((prev) => [...prev, `✅ All done! ${e.total_saved || e.total} profiles`]);
        break;
      case "error":
        setScrapeError(e.message);
        setScrapeLog((prev) => [...prev, `❌ ${e.message}`]);
        break;
    }
  };

  const stopScrape = () => {
    abortRef.current?.abort();
    setScraping(false);
  };

  const handlePresetClick = (preset) => {
    setActivePreset(preset.label);
    setSelectedSubField(preset.label);
    setCustomQuery("");
    // Open modal to show progress
    setShowModal(true);
    setScrapedProfiles([]);
    setScrapeLog([]);
    setScrapeError(null);
    setScrapeCount(0);
    // Start scraping after a tick so modal renders first
    setTimeout(() => startScrape(preset.queries), 50);
  };

  // Filter leads by status
  const filteredLeads = leads.filter((l) => {
    if (statusFilter !== "all" && l.status !== statusFilter) return false;
    return true;
  });

  return (
    <div className="space-y-5">
      {/* ═══ HEADER ═══ */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Linkedin size={24} className={activeField.accent.text} />
            LinkedIn {activeField.label} Sourcing
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">{activeField.description}</p>
        </div>
        <button
          onClick={openModal}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
        >
          <Search size={16} />
          New Search
        </button>
      </div>

      {/* ═══ SCRAPE CONFIGURATION (dropdown layout) ═══ */}
      <div className="bg-white rounded-xl shadow-sm border p-4 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Field dropdown */}
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
              Scraping Field
            </label>
            <IconSelect
              options={FIELDS.map((f) => ({ value: f.key, label: f.label, icon: f.icon }))}
              value={activeFieldKey}
              onChange={switchField}
              accent={activeField.accent}
              placeholder="Select a field..."
              disabled={scraping}
            />
            <p className="text-xs text-gray-400 mt-2">
              Target: <span className="font-medium text-gray-600">{activeField.degree}</span>
            </p>
          </div>

          {/* Sub-field dropdown */}
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
              {activeField.shortLabel} Sub-Field
            </label>
            <div className="flex gap-2">
              <div className="flex-1">
                <IconSelect
                  options={activeField.presets.map((p) => ({
                    value: p.label,
                    label: p.label,
                    icon: p.icon,
                  }))}
                  value={selectedSubField || ""}
                  onChange={setSelectedSubField}
                  accent={activeField.accent}
                  placeholder={`Pick a ${activeField.shortLabel} sub-field...`}
                  disabled={scraping}
                />
              </div>
              <button
                onClick={() => {
                  const preset = activeField.presets.find((p) => p.label === selectedSubField);
                  if (preset) handlePresetClick(preset);
                }}
                disabled={!selectedSubField || scraping}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium text-white transition disabled:opacity-40 ${activeField.accent.activeButton}`}
              >
                <Search size={15} /> Run
              </button>
            </div>
          </div>
        </div>

        {/* Quick-start chips */}
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Quick Start — {activeField.shortLabel} Sub-Fields
          </p>
          <div className="flex flex-wrap gap-2">
            {activeField.presets.map((preset) => {
              const Icon = preset.icon;
              const isActive = activePreset === preset.label && scraping;
              return (
                <button
                  key={preset.label}
                  onClick={() => handlePresetClick(preset)}
                  disabled={scraping && !isActive}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border transition ${
                    isActive
                      ? activeField.accent.activeButton
                      : `bg-white text-gray-700 border-gray-200 ${activeField.accent.hover}`
                  }`}
                >
                  {isActive ? (
                    <RefreshCw size={14} className="animate-spin" />
                  ) : (
                    <Icon size={14} className={activeField.accent.icon} />
                  )}
                  {preset.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* ═══ INLINE SCRAPE STATUS (when modal is closed) ═══ */}
      {scraping && !showModal && (
        <div className={`${activeField.accent.softBg} border rounded-xl p-4`}>
          <div className="flex items-center gap-3">
            <RefreshCw size={18} className={`animate-spin ${activeField.accent.spinner} shrink-0`} />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800">
                {activePreset ? `${activePreset} · ` : ""}{activeField.label} Profile Search
              </p>
              <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1">
                <span className={`text-xs ${activeField.accent.text} flex items-center gap-1`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${activeField.accent.dot} inline-block`} />
                  Phase 1: {scrapeCount} profiles discovered
                </span>
                <span className={`text-xs ${activeField.accent.text} flex items-center gap-1`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${activeField.accent.dot} inline-block animate-pulse`} />
                  Phase 2: Enriching details...
                </span>
              </div>
            </div>
            <button
              onClick={stopScrape}
              className="text-xs bg-red-600 text-white px-3 py-1.5 rounded-lg hover:bg-red-700 shrink-0"
            >
              Stop
            </button>
          </div>
        </div>
      )}

      {/* ═══ INLINE ERROR ═══ */}
      {scrapeError && !showModal && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
          <AlertCircle size={18} className="text-red-500 mt-0.5 shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800">Scrape failed</p>
            <p className="text-xs text-red-600 mt-0.5">{scrapeError}</p>
          </div>
          <button
            onClick={() => setScrapeError(null)}
            className="text-xs text-red-600 hover:text-red-800"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* ═══ FILTERS ═══ */}
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
        <span className="text-xs text-gray-400">
          {total} leads
          {totalPages > 1 && ` · Page ${page} of ${totalPages}`}
        </span>
        <div className="flex gap-2 ml-auto">
          <a
            href="/api/export/csv?source=linkedin"
            className="flex items-center gap-1 text-xs text-blue-600 hover:underline"
          >
            <Download size={14} /> CSV
          </a>
          <a
            href="/api/export/excel?source=linkedin"
            className="flex items-center gap-1 text-xs text-blue-600 hover:underline"
          >
            <Download size={14} /> Excel
          </a>
        </div>
      </div>

      {/* ═══ LEADS TABLE ═══ */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : leads.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-8 text-center text-gray-400">
          <Linkedin size={40} className="mx-auto text-gray-300 mb-3" />
          <p>
            No LinkedIn leads yet. Click a {activeField.shortLabel} sub-field button above to
            start scraping.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">LinkedIn</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Headline</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Company / Location</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Skills</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Syllabus Match</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Education</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Score</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filteredLeads.map((lead) => {
                  return (
                    <tr key={lead.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <Link
                          to={`/leads/${lead.id}`}
                          className="font-medium text-blue-600 hover:text-blue-800"
                        >
                          {lead.name}
                        </Link>
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
                            <span className="truncate max-w-[120px] inline-block">
                              {lead.linkedin_url.split("/in/")[1]?.split("/")[0] || "Profile"}
                            </span>
                            <ExternalLink size={10} />
                          </a>
                        ) : (
                          <span className="text-xs text-gray-400">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-600 max-w-[180px] truncate" title={lead.headline || lead.job_title || ""}>
                        {lead.headline || lead.job_title || "—"}
                      </td>
                      <td className="px-4 py-3 min-w-[150px]">
                        <div className="text-xs text-gray-700">
                          {lead.company && <div className="font-medium">{lead.company}</div>}
                          {lead.location && <div className="text-gray-400">{lead.location}</div>}
                          {lead.industry && !lead.company && !lead.location && (
                            <div className="text-gray-400">{lead.industry}</div>
                          )}
                          {!lead.company && !lead.location && !lead.industry && (
                            <span className="text-gray-400">—</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {lead.skills && lead.skills.length > 0 ? (
                          <div className="flex flex-wrap gap-1 max-w-[180px]">
                            {lead.skills.slice(0, 4).map((s, i) => (
                              <span
                                key={i}
                                className="text-xs px-1.5 py-0.5 rounded bg-blue-100 text-blue-700"
                              >
                                {s}
                              </span>
                            ))}
                            {lead.skills.length > 4 && (
                              <span className="text-xs text-gray-400">+{lead.skills.length - 4}</span>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 min-w-[140px]">
                        {lead.syllabus_confidence != null && lead.syllabus_confidence > 0 ? (
                          <div className="flex items-center gap-2">
                            <div className="relative w-8 h-8">
                              <svg className="w-8 h-8 -rotate-90" viewBox="0 0 36 36">
                                <circle cx="18" cy="18" r="15.5" fill="none" stroke="#e5e7eb" strokeWidth="3" />
                                <circle
                                  cx="18" cy="18" r="15.5" fill="none"
                                  stroke={lead.syllabus_confidence >= 50 ? "#7c3aed" : lead.syllabus_confidence >= 20 ? "#f59e0b" : "#ef4444"}
                                  strokeWidth="3"
                                  strokeDasharray={`${Math.min(lead.syllabus_confidence, 100) * 0.973} 97.3`}
                                  strokeLinecap="round"
                                />
                              </svg>
                              <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-gray-700">
                                {Math.round(lead.syllabus_confidence)}%
                              </span>
                            </div>
                            <div className="flex flex-col min-w-0">
                              <span className="text-xs font-medium text-gray-700 truncate max-w-[100px]" title={lead.syllabus_top_match || ""}>
                                {lead.syllabus_top_match || "General"}
                              </span>
                              {lead.syllabus_matched_subjects && lead.syllabus_matched_subjects.length > 1 && (
                                <span className="text-[10px] text-gray-400 truncate max-w-[100px]">
                                  +{lead.syllabus_matched_subjects.length - 1} more
                                </span>
                              )}
                            </div>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">—</span>
                        )}
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
                                    Score = average of all {lead.syllabus_matched_subjects?.length || 0} matched subject scores (max 100)
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
                      <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">
                        {lead.created_at ? new Date(lead.created_at).toLocaleDateString() : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ═══ PAGINATION ═══ */}
      {!loading && totalPages > 1 && (
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

      {/* ═══ SCRAPE MODAL ═══ */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-5 border-b">
              <div className="flex items-center gap-2">
                <Linkedin size={20} className={activeField.accent.text} />
                <h2 className="text-lg font-bold">{activeField.label} Profile Search</h2>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-5 space-y-4 flex-1 overflow-y-auto">
              {/* Custom query input */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customQuery}
                  onChange={(e) => setCustomQuery(e.target.value)}
                  placeholder='e.g. site:linkedin.com/in "software engineer" Indonesia'
                  className="flex-1 border rounded-lg px-3 py-2 text-sm font-mono"
                  disabled={scraping}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && customQuery.trim() && !scraping) {
                      startScrape();
                    }
                  }}
                />
                {!scraping ? (
                  <button
                    onClick={() => startScrape()}
                    disabled={!customQuery.trim()}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                  >
                    Search
                  </button>
                ) : (
                  <button
                    onClick={stopScrape}
                    className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-700 flex items-center gap-1"
                  >
                    <X size={14} /> Stop
                  </button>
                )}
              </div>

              {/* Sub-field preset dropdown inside modal */}
              <div>
                <p className="text-xs font-semibold text-gray-500 mb-2">
                  Or pick a {activeField.shortLabel} preset:
                </p>
                <div className="flex gap-2">
                  <div className="flex-1">
                    <IconSelect
                      options={activeField.presets.map((p) => ({
                        value: p.label,
                        label: p.label,
                        icon: p.icon,
                      }))}
                      value={selectedSubField || ""}
                      onChange={setSelectedSubField}
                      accent={activeField.accent}
                      placeholder={`Pick a ${activeField.shortLabel} sub-field...`}
                      disabled={scraping}
                    />
                  </div>
                  <button
                    onClick={() => {
                      const preset = activeField.presets.find((p) => p.label === selectedSubField);
                      if (preset) {
                        setActivePreset(preset.label);
                        setCustomQuery("");
                        startScrape(preset.queries);
                      }
                    }}
                    disabled={!selectedSubField || scraping}
                    className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium text-white transition disabled:opacity-40 ${activeField.accent.activeButton}`}
                  >
                    <Search size={15} /> Scrape
                  </button>
                </div>
              </div>

              {/* Scrape log */}
              {scrapeLog.length > 0 && (
                <div className="bg-gray-50 rounded-xl border max-h-40 overflow-y-auto">
                  <div className="p-3 space-y-1">
                    {scrapeLog.map((log, i) => (
                      <div key={i} className="text-xs text-gray-600 font-mono">
                        {log}
                      </div>
                    ))}
                    {scraping && (
                      <div className={`flex items-center gap-1.5 text-xs ${activeField.accent.text}`}>
                        <RefreshCw size={12} className="animate-spin" />
                        Scraping in progress...
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Scraped profiles table */}
              {scrapedProfiles.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold mb-2 flex items-center gap-1.5">
                    <Sparkles size={14} className={activeField.accent.text} />
                    Scraped Profiles ({scrapedProfiles.length})
                  </h3>
                  <div className="max-h-60 overflow-y-auto border rounded-xl">
                    <table className="w-full text-xs">
                      <thead className="bg-gray-50 sticky top-0 border-b">
                        <tr>
                          <th className="text-left px-3 py-2 font-medium">#</th>
                          <th className="text-left px-3 py-2 font-medium">Name</th>
                          <th className="text-left px-3 py-2 font-medium">Title</th>
                          <th className="text-left px-3 py-2 font-medium">Company</th>
                          <th className="text-left px-3 py-2 font-medium">Location</th>
                          <th className="text-left px-3 py-2 font-medium">{activeField.shortLabel} Skills</th>
                          <th className="text-left px-3 py-2 font-medium">Relevance</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {scrapedProfiles.map((p, i) => {
                          const rel = computeRelevance(p.skills, activeField);
                          return (
                            <tr
                              key={i}
                              className={`hover:bg-blue-50/30 ${
                                i === scrapedProfiles.length - 1 && scraping
                                  ? "bg-blue-50 animate-pulse"
                                  : ""
                              }`}
                            >
                              <td className="px-3 py-2.5 text-gray-400">{i + 1}</td>
                              <td className="px-3 py-2.5 min-w-[140px]">
                                <div className="font-semibold text-gray-900">{p.name}</div>
                                {p.linkedin_url && (
                                  <a
                                    href={p.linkedin_url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="text-blue-500 hover:underline flex items-center gap-0.5 mt-0.5"
                                  >
                                    <Linkedin size={10} /> <span>Profile</span>
                                  </a>
                                )}
                              </td>
                              <td className="px-3 py-2.5 text-gray-700 min-w-[130px]">
                                {p.job_title || <span className="text-gray-300">&mdash;</span>}
                              </td>
                              <td className="px-3 py-2.5 text-gray-700 min-w-[120px]">
                                {p.company || <span className="text-gray-300">&mdash;</span>}
                              </td>
                              <td className="px-3 py-2.5 min-w-[130px]">
                                {p.location ? (
                                  <div>
                                    <div className="text-gray-700">{p.location}</div>
                                    {p.area && p.area !== p.location && (
                                      <div className="text-gray-400">{p.area}</div>
                                    )}
                                  </div>
                                ) : (
                                  <span className="text-gray-300">&mdash;</span>
                                )}
                              </td>
                              <td className="px-3 py-2.5 min-w-[130px]">
                                {p.skills?.length > 0 ? (
                                  <div className="flex flex-wrap gap-1">
                                    {p.skills.slice(0, 3).map((s, si) => (
                                      <span
                                        key={si}
                                        className={`px-1.5 py-0.5 rounded text-xs ${
                                          activeField.skills.some((fs) =>
                                            s.toLowerCase().includes(fs.toLowerCase())
                                          )
                                            ? "bg-blue-100 text-blue-700"
                                            : "bg-gray-100 text-gray-600"
                                        }`}
                                      >
                                        {s}
                                      </span>
                                    ))}
                                    {p.skills.length > 3 && (
                                      <span className="text-gray-400">+{p.skills.length - 3}</span>
                                    )}
                                  </div>
                                ) : (
                                  <span className="text-gray-300">&mdash;</span>
                                )}
                              </td>
                              <td className="px-3 py-2.5">
                                <span
                                  className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${rel.color}`}
                                >
                                  {rel.label}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Error display */}
              {scrapeError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2">
                  <AlertCircle size={16} className="text-red-500 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-red-800">Scrape Error</p>
                    <p className="text-xs text-red-600 mt-0.5">{scrapeError}</p>
                  </div>
                </div>
              )}

              {/* Footer */}
              {!scraping && scrapedProfiles.length > 0 && (
                <div className="flex justify-end pt-2">
                  <button
                    onClick={() => {
                      setShowModal(false);
                      fetchLeads();
                    }}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
                  >
                    Close & View Leads
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
