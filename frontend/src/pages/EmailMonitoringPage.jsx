import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import {
  Mail,
  Send,
  Eye,
  MousePointerClick,
  MessageSquare,
  AlertTriangle,
  RefreshCw,
  Inbox,
  ArrowLeft,
  Bot,
  User,
  Search,
  CheckCircle2,
  Clock,
} from "lucide-react";

// ── Status metadata ───────────────────────────────────────────────────────────

const STATUS_META = {
  replied: { label: "Replied", color: "bg-emerald-100 text-emerald-700 border-emerald-200" },
  clicked: { label: "Clicked", color: "bg-purple-100 text-purple-700 border-purple-200" },
  opened: { label: "Opened", color: "bg-blue-100 text-blue-700 border-blue-200" },
  bounced: { label: "Bounced", color: "bg-red-100 text-red-700 border-red-200" },
  failed: { label: "Failed", color: "bg-red-100 text-red-700 border-red-200" },
  sent: { label: "Sent", color: "bg-green-100 text-green-700 border-green-200" },
  delivered: { label: "Delivered", color: "bg-green-100 text-green-700 border-green-200" },
  logged: { label: "Logged", color: "bg-yellow-100 text-yellow-700 border-yellow-200" },
  pending: { label: "Pending", color: "bg-yellow-100 text-yellow-700 border-yellow-200" },
  no_activity: { label: "No Activity", color: "bg-gray-100 text-gray-600 border-gray-200" },
};

const statusBadge = (status) => {
  const meta = STATUS_META[status] || { label: status, color: "bg-gray-100 text-gray-600 border-gray-200" };
  return (
    <span className={`text-[11px] px-2 py-0.5 rounded-full border font-medium ${meta.color}`}>
      {meta.label}
    </span>
  );
};

const stripHtml = (html) => {
  if (!html) return "";
  const div = document.createElement("div");
  div.innerHTML = html;
  return (div.textContent || div.innerText || "").trim();
};

const formatDate = (d) => (d ? new Date(d).toLocaleString() : "—");
const formatDay = (d) => (d ? new Date(d).toLocaleDateString() : "");

// ── Small components ──────────────────────────────────────────────────────────

function StatCard({ icon: Icon, label, value, sub, accent }) {
  return (
    <div className="bg-white rounded-xl border p-4 flex items-center gap-3">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${accent}`}>
        <Icon size={18} />
      </div>
      <div className="min-w-0">
        <div className="text-xl font-bold leading-tight">{value}</div>
        <div className="text-xs text-gray-500 truncate">{label}</div>
        {sub && <div className="text-[10px] text-gray-400">{sub}</div>}
      </div>
    </div>
  );
}

export default function EmailMonitoringPage() {
  const [tab, setTab] = useState("conversations"); // overview | conversations
  const [overview, setOverview] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [convTotal, setConvTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [convLoading, setConvLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [thread, setThread] = useState(null);
  const [threadLoading, setThreadLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState(null);
  const pageSize = 20;

  const fetchOverview = async () => {
    try {
      const r = await axios.get("/api/email/monitoring/overview");
      setOverview(r.data);
    } catch {
      setOverview(null);
    }
  };

  const fetchConversations = async (p = page, st = statusFilter, q = search) => {
    setConvLoading(true);
    try {
      const params = { page: p, page_size: pageSize };
      if (st && st !== "all") params.status = st;
      if (q) params.search = q;
      const r = await axios.get("/api/email/monitoring/conversations", { params });
      setConversations(r.data?.data ?? []);
      setConvTotal(r.data?.total ?? 0);
      if (p !== page) setPage(p);
    } finally {
      setConvLoading(false);
    }
  };

  const loadConversation = async (key) => {
    setThreadLoading(true);
    setThread(null);
    try {
      const r = await axios.get(`/api/email/monitoring/conversations/${encodeURIComponent(key)}`);
      setThread(r.data);
    } catch {
      setThread(null);
    } finally {
      setThreadLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    setSyncResult(null);
    try {
      const r = await axios.post("/api/email/monitoring/sync-inbox");
      setSyncResult(r.data);
      await Promise.all([fetchOverview(), fetchConversations()]);
    } catch (err) {
      setSyncResult({ success: false, message: err.response?.data?.detail || "Sync failed" });
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchOverview(), fetchConversations(1)]).finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totalPages = Math.max(1, Math.ceil(convTotal / pageSize));
  const rates = overview?.rates ?? {};

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Email Monitoring</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Track every outreach email — opened, clicked, replied — and read the
            full conversation between us ({overview?.sender_email || "Admissions"}) and each student.
          </p>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition disabled:opacity-50"
        >
          {syncing ? <RefreshCw size={16} className="animate-spin" /> : <Inbox size={16} />}
          {syncing ? "Syncing inbox..." : "Sync Inbox"}
        </button>
      </div>

      {syncResult && (
        <div
          className={`text-sm rounded-lg px-4 py-3 border ${
            syncResult.success
              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
              : "bg-yellow-50 text-yellow-800 border-yellow-200"
          }`}
        >
          <div className="font-medium">{syncResult.message || "Inbox synced."}</div>
          {syncResult.configured && (
            <div className="text-xs mt-1 text-gray-500">
              Fetched {syncResult.fetched} · Matched {syncResult.matched} · Processed{" "}
              {syncResult.processed} · Duplicates skipped {syncResult.skipped_duplicate}
              {syncResult.errors?.length > 0 && ` · Errors ${syncResult.errors.length}`}
            </div>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-white rounded-xl shadow-sm p-1 w-fit">
        <button
          onClick={() => {
            setTab("overview");
            fetchOverview();
          }}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            tab === "overview" ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100"
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => {
            setTab("conversations");
            fetchConversations(1);
          }}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            tab === "conversations" ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100"
          }`}
        >
          Conversations
          {convTotal > 0 && (
            <span
              className={`ml-1.5 text-[10px] px-1.5 py-0.5 rounded-full ${
                tab === "conversations" ? "bg-white/20" : "bg-gray-200"
              }`}
            >
              {convTotal}
            </span>
          )}
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : tab === "overview" ? (
        <div className="space-y-4">
          {/* Stat cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard icon={Send} label="Emails Sent" value={overview?.sent ?? 0} accent="bg-blue-100 text-blue-600" />
            <StatCard icon={Eye} label="Opened" value={overview?.opened ?? 0} sub={`${rates.open_rate ?? 0}% open rate`} accent="bg-blue-100 text-blue-600" />
            <StatCard icon={MousePointerClick} label="Clicked" value={overview?.clicked ?? 0} sub={`${rates.click_rate ?? 0}% click rate`} accent="bg-purple-100 text-purple-600" />
            <StatCard icon={MessageSquare} label="Replied" value={overview?.replied ?? 0} sub={`${rates.reply_rate ?? 0}% reply rate`} accent="bg-emerald-100 text-emerald-600" />
            <StatCard icon={Mail} label="Total Emails" value={overview?.total_emails ?? 0} accent="bg-gray-100 text-gray-600" />
            <StatCard icon={Inbox} label="Conversations" value={overview?.conversations ?? 0} accent="bg-cyan-100 text-cyan-600" />
            <StatCard icon={AlertTriangle} label="Bounced" value={overview?.bounced ?? 0} sub={`${rates.bounce_rate ?? 0}% bounce rate`} accent="bg-red-100 text-red-600" />
            <StatCard icon={AlertTriangle} label="Failed" value={overview?.failed ?? 0} accent="bg-red-100 text-red-600" />
          </div>

          {/* Funnel */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="text-sm font-semibold text-gray-800 mb-4">
              Engagement Funnel (from {overview?.sent ?? 0} sent)
            </h3>
            <div className="space-y-3">
              {[
                { label: "Opened", value: overview?.opened ?? 0, color: "bg-blue-500" },
                { label: "Clicked", value: overview?.clicked ?? 0, color: "bg-purple-500" },
                { label: "Replied", value: overview?.replied ?? 0, color: "bg-emerald-500" },
              ].map((row) => {
                const pct = overview?.sent ? Math.round((row.value / overview.sent) * 100) : 0;
                return (
                  <div key={row.label} className="flex items-center gap-3">
                    <span className="w-16 text-xs font-medium text-gray-600">{row.label}</span>
                    <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${row.color} rounded-full transition-all`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="w-24 text-right text-xs text-gray-500">
                      {row.value} ({pct}%)
                    </span>
                  </div>
                );
              })}
            </div>
            <p className="text-xs text-gray-400 mt-4">
              Sender: {overview?.sender_email || "—"} · Pending {overview?.pending ?? 0} · Replying leads{" "}
              {overview?.replying_leads ?? 0}
            </p>
          </div>
        </div>
      ) : thread ? (
        /* ── Conversation thread view ── */
        <div className="space-y-4">
          <button
            onClick={() => setThread(null)}
            className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800"
          >
            <ArrowLeft size={16} /> Back to conversations
          </button>

          <div className="bg-white rounded-xl border p-5">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">
                  {(thread.lead?.name || "?").charAt(0)}
                </div>
                <div>
                  <h2 className="font-semibold text-gray-900">{thread.lead?.name}</h2>
                  <p className="text-sm text-gray-500">{thread.lead?.email}</p>
                  {thread.lead?.headline && (
                    <p className="text-xs text-gray-400 mt-0.5">{thread.lead?.headline}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {statusBadge(thread.status)}
                <span className="text-xs text-gray-400">{thread.messages_count} messages</span>
              </div>
            </div>
            {thread.lead?.id && (
              <Link
                to={`/leads/${thread.lead.id}`}
                className="inline-flex items-center gap-1 mt-3 text-xs text-blue-600 hover:underline"
              >
                View lead profile →
              </Link>
            )}
          </div>

          <div className="bg-white rounded-xl border p-5 space-y-4 max-h-[70vh] overflow-y-auto">
            {thread.messages?.length === 0 && (
              <div className="text-center py-10 text-gray-400">
                No messages in this conversation yet.
              </div>
            )}
            {thread.messages?.map((msg, i) => {
              const outgoing = msg.direction === "outgoing";
              const isAuto = msg.type === "auto_response";
              const isReply = msg.type === "reply";
              const body = msg.type === "reply" ? msg.body_text || stripHtml(msg.body) : stripHtml(msg.body);
              const ts = msg.sent_at || msg.received_at;
              const showDate =
                i === 0 || formatDay(ts) !== formatDay(thread.messages[i - 1]?.sent_at || thread.messages[i - 1]?.received_at);
              return (
                <div key={msg.id || i}>
                  {showDate && (
                    <div className="text-center text-[10px] text-gray-400 my-2">
                      {formatDay(ts)}
                    </div>
                  )}
                  <div className={`flex ${outgoing ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
                        outgoing
                          ? "bg-blue-600 text-white rounded-br-sm"
                          : isAuto
                            ? "bg-gray-100 text-gray-700 rounded-bl-sm border border-gray-200"
                            : "bg-gray-100 text-gray-800 rounded-bl-sm"
                      }`}
                    >
                      <div className={`flex items-center gap-2 mb-1 ${outgoing ? "justify-end" : ""}`}>
                        <span className="flex items-center gap-1 text-[11px] font-medium opacity-90">
                          {outgoing ? <Bot size={12} /> : <User size={12} />}
                          {outgoing
                            ? isAuto
                              ? "Auto-reply"
                              : `Us (${thread.sender_email || "Admissions"})`
                            : thread.lead?.name || msg.from_email}
                        </span>
                        {isReply && msg.intent && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/80 text-gray-500">
                            {msg.intent}
                          </span>
                        )}
                      </div>
                      {msg.subject && (
                        <div className={`text-[11px] ${outgoing ? "text-blue-100" : "text-gray-500"} mb-1`}>
                          {msg.subject}
                        </div>
                      )}
                      {body ? (
                        <div className={outgoing ? "text-blue-50" : ""}>{body}</div>
                      ) : (
                        <div className={outgoing ? "text-blue-200 italic" : "text-gray-400 italic"}>
                          (no text content)
                        </div>
                      )}
                      <div
                        className={`flex items-center gap-2 mt-1.5 text-[10px] ${
                          outgoing ? "text-blue-200" : "text-gray-400"
                        }`}
                      >
                        <span className="flex items-center gap-1">
                          <Clock size={10} /> {formatDate(ts)}
                        </span>
                        {outgoing && msg.status && (
                          <span className="flex items-center gap-1">
                            ·
                            {msg.status === "opened" && (
                              <>
                                <Eye size={10} /> opened {msg.opened_count}x
                              </>
                            )}
                            {msg.status === "clicked" && (
                              <>
                                <MousePointerClick size={10} /> clicked {msg.clicked_count}x
                              </>
                            )}
                            {msg.status === "replied" && (
                              <>
                                <MessageSquare size={10} /> replied
                              </>
                            )}
                            {msg.status === "bounced" && (
                              <>
                                <AlertTriangle size={10} /> bounced
                              </>
                            )}
                            {["sent", "delivered", "logged", "pending", "failed"].includes(msg.status) && msg.status}
                          </span>
                        )}
                        {!outgoing && msg.sentiment && (
                          <span className="capitalize">· {msg.sentiment}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        /* ── Conversations list ── */
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-xs text-gray-500">
              {convTotal} conversations · Page {page} of {totalPages}
            </p>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && fetchConversations(1, statusFilter, search)}
                  placeholder="Search name / email / subject..."
                  className="border rounded-lg pl-8 pr-3 py-2 text-sm w-64"
                />
              </div>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  fetchConversations(1, e.target.value, search);
                }}
                className="border rounded-lg px-3 py-2 text-sm"
              >
                <option value="all">All Statuses</option>
                {Object.keys(STATUS_META).map((s) => (
                  <option key={s} value={s}>
                    {STATUS_META[s].label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {convLoading ? (
            <div className="text-center py-12 text-gray-400">Loading...</div>
          ) : conversations.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm p-10 text-center text-gray-400">
              <Mail size={40} className="mx-auto text-gray-300 mb-3" />
              <p>No conversations yet. Send an outreach email to see conversations here.</p>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Student</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Latest Subject</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                    <th className="text-center px-4 py-3 font-medium text-gray-600">Emails</th>
                    <th className="text-center px-4 py-3 font-medium text-gray-600">Replies</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Last Activity</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {conversations.map((c) => (
                    <tr
                      key={c.key}
                      onClick={() => loadConversation(c.lead_id || c.recipient_email)}
                      className="hover:bg-gray-50 cursor-pointer"
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-xs font-bold shrink-0">
                            {(c.lead_name || "?").charAt(0)}
                          </div>
                          <div className="min-w-0">
                            <div className="font-medium text-gray-800 truncate">{c.lead_name}</div>
                            <div className="text-xs text-gray-400 truncate">{c.recipient_email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 max-w-[220px] truncate text-gray-600" title={c.last_subject}>
                        {c.last_subject || "—"}
                      </td>
                      <td className="px-4 py-3">{statusBadge(c.status)}</td>
                      <td className="px-4 py-3 text-center text-gray-600">{c.emails_sent}</td>
                      <td className="px-4 py-3 text-center text-gray-600">{c.replies_count}</td>
                      <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">
                        {formatDate(c.last_activity_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {totalPages > 1 && (
                <div className="flex items-center justify-end gap-1 px-4 py-3 border-t">
                  <button
                    onClick={() => fetchConversations(page - 1)}
                    disabled={page <= 1}
                    className="px-3 py-1.5 text-xs rounded-lg border hover:bg-gray-50 disabled:opacity-40"
                  >
                    Prev
                  </button>
                  <span className="text-xs text-gray-500 px-2">
                    {page} / {totalPages}
                  </span>
                  <button
                    onClick={() => fetchConversations(page + 1)}
                    disabled={page >= totalPages}
                    className="px-3 py-1.5 text-xs rounded-lg border hover:bg-gray-50 disabled:opacity-40"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          )}

          {threadLoading && (
            <div className="text-center py-6 text-gray-400">
              <CheckCircle2 size={20} className="mx-auto animate-pulse mb-1" />
              Loading conversation...
            </div>
          )}
        </div>
      )}
    </div>
  );
}
