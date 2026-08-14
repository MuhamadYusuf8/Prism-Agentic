import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import {
  ArrowLeft, Mail, Send, Pause, Play, Trash2, MessageSquare,
  Clock, CheckCircle, MousePointerClick, RefreshCw, AlertCircle,
  ChevronRight, TrendingUp, Users, Inbox, Eye,
} from "lucide-react";

// ── Utilities ─────────────────────────────────────────────────────────────────

function formatDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleString("id-ID", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function pct(num, total) {
  if (!total) return "0%";
  return `${Math.round((num / total) * 100)}%`;
}

// ── Sub-components ────────────────────────────────────────────────────────────

function StatusBadge({ status }) {
  const map = {
    active:    "bg-green-100 text-green-700 border-green-200",
    paused:    "bg-yellow-100 text-yellow-700 border-yellow-200",
    completed: "bg-blue-100 text-blue-700 border-blue-200",
    draft:     "bg-gray-100 text-gray-600 border-gray-200",
  };
  return (
    <span className={`text-xs px-2.5 py-0.5 rounded-full border font-medium ${map[status] || map.draft}`}>
      {status}
    </span>
  );
}

function StatCard({ label, value, sub, icon: Icon, color }) {
  return (
    <div className="bg-white rounded-xl border p-4 flex items-center gap-3">
      <div className={`p-2.5 rounded-lg ${color} bg-opacity-10`}>
        <Icon size={18} className={color.replace("bg-", "text-")} />
      </div>
      <div className="min-w-0">
        <div className="text-2xl font-bold text-gray-800">{value ?? 0}</div>
        <div className="text-xs text-gray-500 mt-0.5">{label}</div>
        {sub && <div className="text-xs font-semibold text-gray-400">{sub}</div>}
      </div>
    </div>
  );
}

function IntentBadge({ intent }) {
  const map = {
    interested:     "bg-green-100 text-green-700",
    request_info:   "bg-blue-100 text-blue-700",
    not_interested: "bg-red-100 text-red-700",
    unsubscribe:    "bg-red-100 text-red-700",
    out_of_office:  "bg-gray-100 text-gray-600",
    neutral:        "bg-gray-100 text-gray-600",
  };
  const label = {
    interested:     "Interested",
    request_info:   "Request Info",
    not_interested: "Not Interested",
    unsubscribe:    "Unsubscribe",
    out_of_office:  "Out of Office",
    neutral:        "Neutral",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${map[intent] || map.neutral}`}>
      {label[intent] || intent}
    </span>
  );
}

function EmailStatusDot({ status }) {
  const map = {
    sent:    "bg-blue-400",
    replied: "bg-purple-500",
    bounced: "bg-red-400",
    failed:  "bg-red-400",
    logged:  "bg-gray-300",
    pending: "bg-yellow-400",
  };
  return <span className={`inline-block w-2 h-2 rounded-full ${map[status] || "bg-gray-300"}`} />;
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function CampaignDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [campaign, setCampaign] = useState(null);
  const [stats, setStats]       = useState(null);
  const [logs, setLogs]         = useState([]);
  const [replies, setReplies]   = useState([]);
  const [logsTotal, setLogsTotal]   = useState(0);
  const [repliesTotal, setRepliesTotal] = useState(0);
  const [loading, setLoading]   = useState(true);
  const [activeTab, setActiveTab]   = useState("overview");
  const [sending, setSending]   = useState(false);
  const [sendMsg, setSendMsg]   = useState(null);

  const fetchAll = async () => {
    if (!id) return;
    const [cRes, sRes, lRes, rRes] = await Promise.allSettled([
      axios.get(`/api/campaigns/${id}`),
      axios.get(`/api/campaigns/${id}/stats`),
      axios.get(`/api/campaigns/${id}/logs?page_size=10`),
      axios.get(`/api/campaigns/${id}/replies?page_size=10`),
    ]);
    if (cRes.status === "fulfilled") setCampaign(cRes.value.data);
    if (sRes.status === "fulfilled") setStats(sRes.value.data?.stats);
    if (lRes.status === "fulfilled") {
      setLogs(lRes.value.data?.data ?? []);
      setLogsTotal(lRes.value.data?.total ?? 0);
    }
    if (rRes.status === "fulfilled") {
      setReplies(rRes.value.data?.data ?? []);
      setRepliesTotal(rRes.value.data?.total ?? 0);
    }
  };

  useEffect(() => {
    fetchAll().finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleAction = async (action) => {
    if (!id) return;
    try {
      await axios.post(`/api/campaigns/${id}/${action}`);
      await fetchAll();
    } catch (err) {
      console.error(action, err);
    }
  };

  const handleSendCampaign = async () => {
    setSending(true);
    setSendMsg(null);
    try {
      const res = await axios.post(`/api/campaigns/${id}/send`, {});
      setSendMsg({ ok: true, text: res.data?.message || "Emails queued in background!" });
      await fetchAll();
    } catch (err) {
      setSendMsg({ ok: false, text: err?.response?.data?.detail || "Failed to send." });
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-gray-400">
        <RefreshCw size={20} className="animate-spin mr-2" /> Loading campaign…
      </div>
    );
  }

  if (!campaign) {
    return <div className="text-center py-12 text-gray-400">Campaign not found.</div>;
  }

  const tabs = [
    { key: "overview", label: "Overview" },
    { key: "logs",     label: `Email Logs (${logsTotal})` },
    { key: "replies",  label: `Replies (${repliesTotal})` },
    { key: "template", label: "Template" },
  ];

  return (
    <div className="space-y-5 max-w-5xl mx-auto">
      {/* Back */}
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800 transition-colors">
        <ArrowLeft size={16} /> Back to Campaigns
      </button>

      {/* Header Card */}
      <div className="bg-white rounded-xl border p-5 shadow-sm">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="min-w-0">
            <h1 className="text-xl font-bold text-gray-800 truncate">{campaign.name}</h1>
            {campaign.description && (
              <p className="text-sm text-gray-500 mt-0.5">{campaign.description}</p>
            )}
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <StatusBadge status={campaign.status} />
              <span className="text-xs text-gray-400">Dibuat {formatDate(campaign.created_at)}</span>
              {campaign.launched_at && (
                <span className="text-xs text-gray-400">· Diluncurkan {formatDate(campaign.launched_at)}</span>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 flex-wrap">
            {(campaign.status === "draft" || campaign.status === "paused") && (
              <button onClick={() => handleAction("activate")}
                className="flex items-center gap-1 text-xs border rounded-lg px-3 py-1.5 hover:bg-green-50 text-green-700 border-green-200 transition-colors">
                <Play size={13} /> Aktifkan
              </button>
            )}
            {campaign.status === "active" && (
              <button onClick={() => handleAction("pause")}
                className="flex items-center gap-1 text-xs border rounded-lg px-3 py-1.5 hover:bg-yellow-50 text-yellow-700 border-yellow-200 transition-colors">
                <Pause size={13} /> Pause
              </button>
            )}
            <button onClick={handleSendCampaign} disabled={sending}
              className="flex items-center gap-1 text-xs border rounded-lg px-3 py-1.5 bg-blue-600 text-white border-blue-600 hover:bg-blue-700 disabled:opacity-50 transition-colors">
              {sending ? <RefreshCw size={13} className="animate-spin" /> : <Send size={13} />}
              {sending ? "Mengirim…" : "Kirim Campaign"}
            </button>
            <button onClick={() => handleAction("send-follow-ups")}
              className="flex items-center gap-1 text-xs border rounded-lg px-3 py-1.5 hover:bg-purple-50 text-purple-700 border-purple-200 transition-colors">
              <MessageSquare size={13} /> Follow-up
            </button>
          </div>
        </div>

        {/* Send status message */}
        {sendMsg && (
          <div className={`mt-3 p-3 rounded-lg text-sm flex items-center gap-2 ${sendMsg.ok ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
            {sendMsg.ok ? <CheckCircle size={15} /> : <AlertCircle size={15} />}
            {sendMsg.text}
          </div>
        )}
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Terkirim"    value={stats?.total_sent}    sub={null}                               icon={Send}             color="bg-blue-500" />
        <StatCard label="Dibuka"      value={stats?.total_opened}  sub={pct(stats?.total_opened,  stats?.total_sent)} icon={Eye}              color="bg-green-500" />
        <StatCard label="Diklik"      value={stats?.total_clicked} sub={pct(stats?.total_clicked, stats?.total_sent)} icon={MousePointerClick} color="bg-orange-500" />
        <StatCard label="Dibalas"     value={stats?.total_replied} sub={pct(stats?.total_replied, stats?.total_sent)} icon={MessageSquare}    color="bg-purple-500" />
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
        <div className="flex border-b">
          {tabs.map((t) => (
            <button key={t.key} onClick={() => setActiveTab(t.key)}
              className={`px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === t.key
                  ? "border-b-2 border-blue-600 text-blue-600"
                  : "text-gray-500 hover:text-gray-700"
              }`}>
              {t.label}
            </button>
          ))}
        </div>

        <div className="p-5">
          {/* OVERVIEW TAB */}
          {activeTab === "overview" && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Statistik Lengkap</h3>
                  <div className="space-y-2">
                    {[
                      { label: "Open Rate",   val: `${stats?.open_rate ?? 0}%` },
                      { label: "Click Rate",  val: `${stats?.click_rate ?? 0}%` },
                      { label: "Reply Rate",  val: `${stats?.reply_rate ?? 0}%` },
                      { label: "Bounced",     val: stats?.total_bounced ?? 0 },
                      { label: "Follow-ups Sent", val: stats?.total_follow_ups ?? 0 },
                    ].map(({ label, val }) => (
                      <div key={label} className="flex justify-between items-center py-1.5 border-b border-gray-50">
                        <span className="text-sm text-gray-600">{label}</span>
                        <span className="text-sm font-semibold text-gray-800">{val}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Konfigurasi Follow-up</h3>
                  {campaign.follow_up?.enabled ? (
                    <div className="space-y-2">
                      <div className="flex justify-between py-1.5 border-b border-gray-50">
                        <span className="text-sm text-gray-600">Status</span>
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Aktif</span>
                      </div>
                      <div className="flex justify-between py-1.5 border-b border-gray-50">
                        <span className="text-sm text-gray-600">Delay</span>
                        <span className="text-sm font-semibold">{campaign.follow_up?.delay_days} hari</span>
                      </div>
                      <div className="flex justify-between py-1.5 border-b border-gray-50">
                        <span className="text-sm text-gray-600">Maks. Follow-up</span>
                        <span className="text-sm font-semibold">{campaign.follow_up?.max_follow_ups}x</span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-400">Follow-up tidak dikonfigurasi.</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* LOGS TAB */}
          {activeTab === "logs" && (
            <div>
              {logs.length === 0 ? (
                <div className="text-center py-10 text-gray-400">
                  <Inbox size={32} className="mx-auto mb-2 opacity-40" />
                  <p>Belum ada email log untuk campaign ini.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-xs text-gray-400 border-b">
                        <th className="text-left pb-2 font-medium">Penerima</th>
                        <th className="text-left pb-2 font-medium">Status</th>
                        <th className="text-left pb-2 font-medium">Dibuka</th>
                        <th className="text-left pb-2 font-medium">Diklik</th>
                        <th className="text-left pb-2 font-medium">Dibalas</th>
                        <th className="text-left pb-2 font-medium">Terkirim</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {logs.map((log) => (
                        <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                          <td className="py-2.5 pr-4">
                            <div className="font-medium text-gray-800 truncate max-w-[150px]">{log.recipient_name || "—"}</div>
                            <div className="text-xs text-gray-400 truncate max-w-[150px]">{log.recipient_email}</div>
                          </td>
                          <td className="py-2.5 pr-4">
                            <div className="flex items-center gap-1.5">
                              <EmailStatusDot status={log.status} />
                              <span className="capitalize">{log.status}</span>
                              {log.is_follow_up && (
                                <span className="text-xs bg-purple-100 text-purple-600 px-1.5 rounded">FU#{log.follow_up_number}</span>
                              )}
                            </div>
                          </td>
                          <td className="py-2.5 pr-4 text-xs">
                            {log.opened_at ? (
                              <span className="text-green-600 flex items-center gap-1">
                                <Eye size={11} /> {log.opened_count}x
                              </span>
                            ) : <span className="text-gray-300">—</span>}
                          </td>
                          <td className="py-2.5 pr-4 text-xs">
                            {log.clicked_at ? (
                              <span className="text-orange-500 flex items-center gap-1">
                                <MousePointerClick size={11} /> {log.clicked_count}x
                              </span>
                            ) : <span className="text-gray-300">—</span>}
                          </td>
                          <td className="py-2.5 pr-4 text-xs">
                            {log.replied_at ? (
                              <span className="text-purple-600 flex items-center gap-1">
                                <MessageSquare size={11} /> Ya
                              </span>
                            ) : <span className="text-gray-300">—</span>}
                          </td>
                          <td className="py-2.5 text-xs text-gray-400">
                            {log.sent_at ? new Date(log.sent_at).toLocaleDateString("id-ID") : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {logsTotal > 10 && (
                    <p className="text-center text-xs text-gray-400 mt-3">
                      Menampilkan 10 dari {logsTotal} log
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* REPLIES TAB */}
          {activeTab === "replies" && (
            <div>
              {replies.length === 0 ? (
                <div className="text-center py-10 text-gray-400">
                  <MessageSquare size={32} className="mx-auto mb-2 opacity-40" />
                  <p>Belum ada balasan untuk campaign ini.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {replies.map((reply) => (
                    <div key={reply.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-medium text-sm text-gray-800 truncate">{reply.from_email}</span>
                            <IntentBadge intent={reply.intent} />
                            {reply.auto_response_sent && (
                              <span className="text-xs text-green-600 flex items-center gap-0.5">
                                <CheckCircle size={10} /> Auto-replied
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-500 mt-1 line-clamp-2">{reply.body_text}</p>
                        </div>
                        <div className="text-xs text-gray-400 whitespace-nowrap shrink-0">
                          {reply.received_at ? new Date(reply.received_at).toLocaleDateString("id-ID") : "—"}
                        </div>
                      </div>
                      <div className="mt-1.5 flex items-center gap-2 text-xs text-gray-400">
                        <span>Confidence: {((reply.confidence || 0) * 100).toFixed(0)}%</span>
                        <span>·</span>
                        <span className={reply.sentiment === "positive" ? "text-green-500" : reply.sentiment === "negative" ? "text-red-400" : "text-gray-400"}>
                          {reply.sentiment}
                        </span>
                      </div>
                    </div>
                  ))}
                  {repliesTotal > 10 && (
                    <p className="text-center text-xs text-gray-400">
                      Menampilkan 10 dari {repliesTotal} balasan
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* TEMPLATE TAB */}
          {activeTab === "template" && (
            <div className="space-y-4">
              {campaign.email_template ? (
                <>
                  <div>
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Subject</p>
                    <p className="text-sm font-medium text-gray-800 bg-gray-50 px-3 py-2 rounded-lg">
                      {campaign.email_template.subject || "—"}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Body (HTML Preview)</p>
                    <div
                      className="border rounded-lg p-4 bg-white text-sm max-h-96 overflow-y-auto"
                      dangerouslySetInnerHTML={{ __html: campaign.email_template.body || "<p>Kosong</p>" }}
                    />
                  </div>
                </>
              ) : (
                <div className="text-center py-10 text-gray-400">
                  <Mail size={32} className="mx-auto mb-2 opacity-40" />
                  <p>Belum ada template email.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
