import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import {
  ArrowLeft,
  Mail,
  Send,
  Pause,
  Play,
  Trash2,
  MessageSquare,
  Users,
  Target,
  Clock,
} from "lucide-react";

function formatDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString();
}

function StatCard({
  label,
  value,
  color,
}) {
  return (
    <div className="bg-white rounded-xl border p-4 text-center">
      <div className={`text-xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-0.5">{label}</div>
    </div>
  );
}

export default function CampaignDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [campaign, setCampaign] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      axios.get(`/api/campaigns/${id}`),
      axios.get(`/api/campaigns/${id}/stats`),
    ])
      .then(([cRes, sRes]) => {
        setCampaign(cRes.data);
        setStats(sRes.data);
      })
      .finally(() => setLoading(false));
  }, [id]);

  const handleAction = async (action) => {
    if (!id) return;
    await axios.post(`/api/campaigns/${id}/${action}`);
    const r = await axios.get(`/api/campaigns/${id}`);
    setCampaign(r.data);
  };

  if (loading) {
    return <div className="text-center py-12 text-gray-400">Loading...</div>;
  }

  if (!campaign) {
    return (
      <div className="text-center py-12 text-gray-400">Campaign not found.</div>
    );
  }

  return (
    <div className="space-y-5">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800"
      >
        <ArrowLeft size={16} /> Back
      </button>

      {/* Header */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold">{campaign.name}</h1>
            <p className="text-sm text-gray-500 mt-0.5">{campaign.subject}</p>
            <div className="flex items-center gap-2 mt-2">
              <span
                className={`text-xs px-2 py-0.5 rounded-full ${
                  campaign.status === "active"
                    ? "bg-green-100 text-green-700"
                    : campaign.status === "paused"
                      ? "bg-yellow-100 text-yellow-700"
                      : campaign.status === "completed"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-gray-100 text-gray-700"
                }`}
              >
                {campaign.status}
              </span>
              <span className="text-xs text-gray-400">{campaign.type}</span>
              <span className="text-xs text-gray-400">
                Created {formatDate(campaign.created_at)}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {campaign.status === "draft" && (
              <button
                onClick={() => handleAction("activate")}
                className="flex items-center gap-1 text-xs border rounded-lg px-3 py-1.5 hover:bg-green-50 text-green-700 border-green-200"
              >
                <Play size={14} /> Activate
              </button>
            )}
            {campaign.status === "active" && (
              <button
                onClick={() => handleAction("pause")}
                className="flex items-center gap-1 text-xs border rounded-lg px-3 py-1.5 hover:bg-yellow-50 text-yellow-700 border-yellow-200"
              >
                <Pause size={14} /> Pause
              </button>
            )}
            {campaign.status === "paused" && (
              <button
                onClick={() => handleAction("activate")}
                className="flex items-center gap-1 text-xs border rounded-lg px-3 py-1.5 hover:bg-green-50 text-green-700 border-green-200"
              >
                <Play size={14} /> Resume
              </button>
            )}
            <button
              onClick={() => handleAction("send-follow-ups")}
              className="flex items-center gap-1 text-xs border rounded-lg px-3 py-1.5 hover:bg-blue-50 text-blue-700 border-blue-200"
            >
              <Send size={14} /> Send Follow-ups
            </button>
            <button
              onClick={() => handleAction("delete")}
              className="flex items-center gap-1 text-xs border rounded-lg px-3 py-1.5 hover:bg-red-50 text-red-700 border-red-200"
            >
              <Trash2 size={14} /> Delete
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          label="Total Leads"
          value={stats?.total_leads ?? 0}
          color="text-gray-800"
        />
        <StatCard
          label="Sent"
          value={stats?.sent ?? 0}
          color="text-blue-600"
        />
        <StatCard
          label="Opened"
          value={stats?.opened ?? 0}
          color="text-green-600"
        />
        <StatCard
          label="Replied"
          value={stats?.replied ?? 0}
          color="text-purple-600"
        />
      </div>

      {/* Email Template */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-center gap-2 mb-3">
          <Mail size={16} className="text-gray-400" />
          <h2 className="font-semibold text-sm">Email Template</h2>
        </div>
        {campaign.email_template ? (
          <div className="bg-gray-50 rounded-lg p-4 text-sm whitespace-pre-wrap">
            {campaign.email_template.body}
          </div>
        ) : (
          <p className="text-xs text-gray-400">No template defined.</p>
        )}
      </div>

      {/* Follow-up */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-center gap-2 mb-3">
          <MessageSquare size={16} className="text-gray-400" />
          <h2 className="font-semibold text-sm">Follow-up</h2>
        </div>
        {campaign.follow_up ? (
          <div>
            <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
              <Clock size={12} />
              <span>Delay: {campaign.follow_up.delay_days} days</span>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 text-sm whitespace-pre-wrap">
              {campaign.follow_up.body}
            </div>
          </div>
        ) : (
          <p className="text-xs text-gray-400">No follow-up configured.</p>
        )}
      </div>

      {/* Target Clusters */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-center gap-2 mb-3">
          <Target size={16} className="text-gray-400" />
          <h2 className="font-semibold text-sm">Target Clusters</h2>
        </div>
        {campaign.target_clusters && campaign.target_clusters.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {campaign.target_clusters.map((c) => (
              <span
                key={c.id}
                className="bg-blue-50 text-blue-700 text-xs px-2.5 py-1 rounded-full"
              >
                {c.name}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xs text-gray-400">No specific clusters targeted.</p>
        )}
      </div>

      {/* Schedule */}
      {campaign.schedule && (
        <div className="bg-white rounded-xl border p-5">
          <div className="flex items-center gap-2 mb-3">
            <Clock size={16} className="text-gray-400" />
            <h2 className="font-semibold text-sm">Schedule</h2>
          </div>
          <p className="text-sm text-gray-700">
            {new Date(campaign.schedule).toLocaleString()}
          </p>
        </div>
      )}
    </div>
  );
}
