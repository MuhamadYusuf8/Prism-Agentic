import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import {
  Mail,
  Plus,
  Play,
  Pause,
  Send,
  X,
  Loader2,
  Eye,
  MousePointerClick,
  MessageSquare,
  Clock,
} from "lucide-react";

export default function EmailPage() {
  const [tab, setTab] = useState("campaigns");
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    name: "",
    subject: "",
    type: "master",
    target_cluster_id: "",
    target_cluster_type: "master",
    email_body: "",
    follow_up_body: "",
    schedule_date: "",
    schedule_time: "",
  });
  const [logs, setLogs] = useState([]);
  const [logsTotal, setLogsTotal] = useState(0);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logStatus, setLogStatus] = useState("all");
  const [logPage, setLogPage] = useState(1);
  const logPageSize = 20;

  const fetchLogs = async (pageNum = logPage, status = logStatus) => {
    setLogsLoading(true);
    try {
      const params = { page: pageNum, page_size: logPageSize };
      if (status !== "all") params.status = status;
      const r = await axios.get("/api/email/logs", { params });
      setLogs(r.data?.data ?? []);
      setLogsTotal(r.data?.total ?? 0);
      if (pageNum !== logPage) setLogPage(pageNum);
    } finally {
      setLogsLoading(false);
    }
  };

  const logTotalPages = Math.max(1, Math.ceil(logsTotal / logPageSize));

  const fetchCampaigns = async () => {
    try {
      const r = await axios.get("/api/campaigns");
      setCampaigns(r.data?.data ?? r.data?.campaigns ?? []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        ...form,
        schedule: form.schedule_date
          ? `${form.schedule_date}T${form.schedule_time || "09:00"}`
          : null,
      };
      await axios.post("/api/campaigns", payload);
      setShowModal(false);
      fetchCampaigns();
    } finally {
      setSaving(false);
    }
  };

  const handleActivate = async (id) => {
    await axios.post(`/api/campaigns/${id}/activate`);
    fetchCampaigns();
  };

  const handlePause = async (id) => {
    await axios.post(`/api/campaigns/${id}/pause`);
    fetchCampaigns();
  };

  const handleSendFollowUps = async (id) => {
    await axios.post(`/api/campaigns/${id}/send-follow-ups`);
    fetchCampaigns();
  };

  const handleSendAll = async (id, name) => {
    if (!window.confirm(`Send this campaign to ALL leads with registered emails?\n\n"${name}"`)) return;
    try {
      await axios.post(`/api/campaigns/${id}/send-all`);
      fetchCampaigns();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to send campaign");
    }
  };

  const handleMarkReplied = async (logId) => {
    const content = window.prompt("Reply content (optional):", "");
    if (content === null) return;
    try {
      await axios.post(`/api/email/logs/${logId}/reply`, {
        reply_content: content || null,
      });
      fetchLogs(logPage);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to mark as replied");
    }
  };

  const STATUS_COLORS = {
    draft: "bg-gray-100 text-gray-700",
    active: "bg-green-100 text-green-700",
    paused: "bg-yellow-100 text-yellow-700",
    completed: "bg-blue-100 text-blue-700",
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Email Campaigns</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Manage and send email campaigns to leads
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
        >
          <Plus size={16} />
          New Campaign
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-white rounded-xl shadow-sm p-1 w-fit">
        <button
          onClick={() => setTab("campaigns")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            tab === "campaigns"
              ? "bg-blue-600 text-white"
              : "text-gray-600 hover:bg-gray-100"
          }`}
        >
          Campaigns
        </button>
        <button
          onClick={() => {
            setTab("records");
            fetchLogs(1);
          }}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            tab === "records"
              ? "bg-blue-600 text-white"
              : "text-gray-600 hover:bg-gray-100"
          }`}
        >
          Email Records
          {logsTotal > 0 && (
            <span
              className={`ml-1.5 text-[10px] px-1.5 py-0.5 rounded-full ${
                tab === "records" ? "bg-white/20" : "bg-gray-200"
              }`}
            >
              {logsTotal}
            </span>
          )}
        </button>
      </div>

      {tab === "campaigns" ? (
        loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : campaigns.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-8 text-center text-gray-400">
          <Mail size={40} className="mx-auto text-gray-300 mb-3" />
          <p>No campaigns yet. Create your first campaign.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {campaigns.map((c) => (
            <div
              key={c.id}
              className="bg-white rounded-xl border p-5 hover:shadow-sm transition"
            >
              <div className="flex items-start justify-between">
                <div>
                  <Link
                    to={`/email/${c.id}`}
                    className="font-semibold text-gray-900 hover:text-blue-600"
                  >
                    {c.name}
                  </Link>
                  <p className="text-sm text-gray-500 mt-0.5">{c.subject}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[c.status] ?? "bg-gray-100 text-gray-700"}`}
                    >
                      {c.status}
                    </span>
                    <span className="text-xs text-gray-400">{c.type}</span>
                    {c.target_clusters && c.target_clusters.length > 0 && (
                      <span className="text-xs text-gray-400">
                        {c.target_clusters.map((tc) => tc.name).join(", ")}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {c.status === "draft" && (
                    <button
                      onClick={() => handleActivate(c.id)}
                      className="flex items-center gap-1 text-xs border rounded-lg px-2.5 py-1.5 hover:bg-green-50 text-green-700 border-green-200"
                    >
                      <Play size={12} /> Activate
                    </button>
                  )}
                  {c.status === "active" && (
                    <button
                      onClick={() => handlePause(c.id)}
                      className="flex items-center gap-1 text-xs border rounded-lg px-2.5 py-1.5 hover:bg-yellow-50 text-yellow-700 border-yellow-200"
                    >
                      <Pause size={12} /> Pause
                    </button>
                  )}
                  {c.status === "paused" && (
                    <button
                      onClick={() => handleActivate(c.id)}
                      className="flex items-center gap-1 text-xs border rounded-lg px-2.5 py-1.5 hover:bg-green-50 text-green-700 border-green-200"
                    >
                      <Play size={12} /> Resume
                    </button>
                  )}
                  <button
                    onClick={() => handleSendFollowUps(c.id)}
                    className="flex items-center gap-1 text-xs border rounded-lg px-2.5 py-1.5 hover:bg-blue-50 text-blue-700 border-blue-200"
                  >
                    <Send size={12} /> Follow-ups
                  </button>
                  <button
                    onClick={() => handleSendAll(c.id, c.name)}
                    className="flex items-center gap-1 text-xs border rounded-lg px-2.5 py-1.5 hover:bg-emerald-50 text-emerald-700 border-emerald-200"
                  >
                    <Send size={12} /> Send to All Emails
                  </button>
                </div>
              </div>
              {c.stats && (
                <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                  <span>Sent: {c.stats.total_sent}</span>
                  <span>Opened: {c.stats.total_opened}</span>
                  <span>Replied: {c.stats.total_replied}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )) : (
        /* ── Email Records / Traffic view ── */
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">Email Traffic & Records</h2>
              <p className="text-xs text-gray-500 mt-0.5">
                {logsTotal} total emails · Page {logPage} of {logTotalPages}
              </p>
            </div>
            <select
              value={logStatus}
              onChange={(e) => {
                setLogStatus(e.target.value);
                fetchLogs(1, e.target.value);
              }}
              className="border rounded-lg px-3 py-2 text-sm"
            >
              <option value="all">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="sent">Sent</option>
              <option value="delivered">Delivered</option>
              <option value="bounced">Bounced</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          {logsLoading ? (
            <div className="text-center py-12 text-gray-400">Loading...</div>
          ) : logs.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm p-8 text-center text-gray-400">
              <Mail size={40} className="mx-auto text-gray-300 mb-3" />
              <p>No email records yet. Send a campaign to see traffic here.</p>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Lead</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-600">To</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Subject</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Campaign</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Opened</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Clicked</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Replied</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Sent At</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {logs.map((log) => (
                      <tr key={log.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap">
                          {log.lead_id ? (
                            <Link
                              to={`/leads/${log.lead_id}`}
                              className="font-medium text-blue-600 hover:text-blue-800"
                            >
                              {log.lead_name || log.recipient_name || "—"}
                            </Link>
                          ) : (
                            <span>{log.recipient_name || "—"}</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-gray-600">{log.recipient_email}</td>
                        <td className="px-4 py-3 max-w-[200px] truncate" title={log.subject}>
                          {log.subject}
                        </td>
                        <td className="px-4 py-3 text-xs">
                          {log.campaign_id ? (
                            <Link
                              to={`/email/${log.campaign_id}`}
                              className="text-blue-600 hover:underline"
                            >
                              {log.campaign_name || "Campaign"}
                            </Link>
                          ) : (
                            <span className="text-gray-400">Direct</span>
                          )}
                          {log.is_follow_up && (
                            <span className="ml-1 text-[10px] bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded-full">
                              FU{log.follow_up_number || ""}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full ${
                              log.status === "sent" || log.status === "delivered"
                                ? "bg-green-100 text-green-700"
                                : log.status === "bounced" || log.status === "failed"
                                  ? "bg-red-100 text-red-700"
                                  : "bg-yellow-100 text-yellow-700"
                            }`}
                          >
                            {log.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-600">
                          {log.opened_at ? (
                            <span className="flex items-center gap-1">
                              <Eye size={12} className="text-blue-500" />
                              {log.opened_count || 1}
                            </span>
                          ) : (
                            <span className="text-gray-300">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-600">
                          {log.clicked_at ? (
                            <span className="flex items-center gap-1">
                              <MousePointerClick size={12} className="text-purple-500" />
                              {log.clicked_count || 1}
                            </span>
                          ) : (
                            <span className="text-gray-300">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-600">
                          {log.replied_at ? (
                            <span className="flex items-center gap-1">
                              <MessageSquare size={12} className="text-emerald-500" />
                              Yes
                            </span>
                          ) : (
                            <button
                              onClick={() => handleMarkReplied(log.id)}
                              className="text-[11px] text-blue-600 hover:underline border border-blue-200 rounded px-1.5 py-0.5 hover:bg-blue-50"
                            >
                              Mark Replied
                            </button>
                          )}
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">
                          <span className="flex items-center gap-1">
                            <Clock size={12} />
                            {log.sent_at
                              ? new Date(log.sent_at).toLocaleString()
                              : new Date(log.created_at).toLocaleDateString()}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {logTotalPages > 1 && (
                <div className="flex items-center justify-end gap-1 px-4 py-3 border-t">
                  <button
                    onClick={() => fetchLogs(logPage - 1)}
                    disabled={logPage <= 1}
                    className="px-3 py-1.5 text-xs rounded-lg border hover:bg-gray-50 disabled:opacity-40"
                  >
                    Prev
                  </button>
                  <span className="text-xs text-gray-500 px-2">
                    {logPage} / {logTotalPages}
                  </span>
                  <button
                    onClick={() => fetchLogs(logPage + 1)}
                    disabled={logPage >= logTotalPages}
                    className="px-3 py-1.5 text-xs rounded-lg border hover:bg-gray-50 disabled:opacity-40"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Create Campaign Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-5 border-b">
              <div className="flex items-center gap-2">
                <Mail size={20} className="text-blue-600" />
                <h2 className="text-lg font-bold">New Campaign</h2>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreate} className="p-5 space-y-4 overflow-y-auto">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Campaign Name
                </label>
                <input
                  type="text"
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  placeholder="e.g. S2 CS Outreach Q1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Subject
                </label>
                <input
                  type="text"
                  required
                  value={form.subject}
                  onChange={(e) => setForm({ ...form, subject: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  placeholder="e.g. Graduate Program Opportunity"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Type
                </label>
                <select
                  value={form.type}
                  onChange={(e) => setForm({ ...form, type: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                >
                  <option value="master">S2</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Body
                </label>
                <textarea
                  rows={5}
                  value={form.email_body}
                  onChange={(e) =>
                    setForm({ ...form, email_body: e.target.value })
                  }
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  placeholder="Write your email content here..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Follow-up Body (optional)
                </label>
                <textarea
                  rows={3}
                  value={form.follow_up_body}
                  onChange={(e) =>
                    setForm({ ...form, follow_up_body: e.target.value })
                  }
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  placeholder="Follow-up message..."
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Schedule Date
                  </label>
                  <input
                    type="date"
                    value={form.schedule_date}
                    onChange={(e) =>
                      setForm({ ...form, schedule_date: e.target.value })
                    }
                    className="w-full border rounded-lg px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Schedule Time
                  </label>
                  <input
                    type="time"
                    value={form.schedule_time}
                    onChange={(e) =>
                      setForm({ ...form, schedule_time: e.target.value })
                    }
                    className="w-full border rounded-lg px-3 py-2 text-sm"
                  />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="sendNow"
                  className="rounded"
                />
                <label htmlFor="sendNow" className="text-sm text-gray-600">
                  Send immediately
                </label>
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <Send size={16} />
                  )}
                  {saving ? "Creating..." : "Create Campaign"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
