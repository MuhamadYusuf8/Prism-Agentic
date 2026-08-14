import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import {
  ArrowLeft,
  Mail,
  ExternalLink,
  Award,
  Code,
  GraduationCap,
  Briefcase,
  MapPin,
  Building,
  Globe,
  User,
  Target,
  Star,
  CheckCircle,
  AlertCircle,
  Linkedin,
  UserPlus,
  MessageSquare,
  Eye,
  RefreshCw,
  Send,
} from "lucide-react";

function scoreColor(s) {
  if (s == null) return "text-gray-400";
  if (s >= 80) return "text-green-600";
  if (s >= 60) return "text-yellow-600";
  return "text-red-600";
}

function scoreBg(s) {
  if (s == null) return "bg-gray-100";
  if (s >= 80) return "bg-green-100";
  if (s >= 60) return "bg-yellow-100";
  return "bg-red-100";
}

function formatDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString();
}

function InfoRow({
  label,
  value,
  href,
  icon: Icon,
}) {
  return (
    <div className="flex items-start gap-2 py-1.5">
      {Icon && <Icon size={14} className="text-gray-400 mt-0.5 shrink-0" />}
      <span className="text-xs text-gray-500 min-w-[100px]">{label}</span>
      <span className="text-xs font-medium text-gray-800">
        {href ? (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline flex items-center gap-1"
          >
            {value} <ExternalLink size={10} />
          </a>
        ) : (
          value ?? "—"
        )}
      </span>
    </div>
  );
}

function Badge({
  children,
  color,
}) {
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${color}`}>
      {children}
    </span>
  );
}

export default function LeadDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [lead, setLead] = useState(null);
  const [loading, setLoading] = useState(true);
  const [interactions, setInteractions] = useState([]);
  const [conversation, setConversation] = useState(null);
  const [convLoading, setConvLoading] = useState(false);
  const [interactionType, setInteractionType] = useState("connection_request");
  const [interactionNotes, setInteractionNotes] = useState("");
  const [logging, setLogging] = useState(false);
  const [showLogForm, setShowLogForm] = useState(false);
  const [findingEmail, setFindingEmail] = useState(false);
  const [emailResult, setEmailResult] = useState(null);

  const loadLead = async () => {
    if (!id) return;
    const r = await axios.get(`/api/leads/${id}`);
    setLead(r.data);
    return r.data;
  };

  const loadInteractions = async () => {
    if (!id) return;
    try {
      const r = await axios.get(`/api/leads/${id}/interactions`);
      setInteractions(r.data?.interactions ?? []);
    } catch {
      setInteractions([]);
    }
  };

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    loadLead().finally(() => setLoading(false));
    loadInteractions();
  }, [id]);

  const loadConversation = async (leadId) => {
    setConvLoading(true);
    try {
      const r = await axios.get(`/api/email/monitoring/conversations/${leadId}`);
      setConversation(r.data);
    } catch {
      setConversation(null);
    } finally {
      setConvLoading(false);
    }
  };

  useEffect(() => {
    if (id) loadConversation(id);
  }, [id]);

  const handleProfile = async () => {
    if (!id) return;
    await axios.post(`/api/leads/${id}/reprofile`);
    await loadLead();
  };

  const handleLogInteraction = async () => {
    if (!id || logging) return;
    setLogging(true);
    try {
      await axios.post(`/api/leads/${id}/interactions`, {
        interaction_type: interactionType,
        notes: interactionNotes || null,
        content: interactionNotes || null,
      });
      setInteractionNotes("");
      setShowLogForm(false);
      await Promise.all([loadLead(), loadInteractions()]);
    } finally {
      setLogging(false);
    }
  };

  const handleFindEmail = async () => {
    if (!id || findingEmail) return;
    setFindingEmail(true);
    setEmailResult(null);
    try {
      const r = await axios.post(`/api/leads/${id}/find-email`);
      setEmailResult(r.data);
      await loadLead();
    } catch {
      setEmailResult({ email: null, confidence: 0, source: "error" });
    } finally {
      setFindingEmail(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12 text-gray-400">Loading...</div>;
  }

  if (!lead) {
    return (
      <div className="text-center py-12 text-gray-400">Lead not found.</div>
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
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-lg">
              {lead.name?.charAt(0) ?? "?"}
            </div>
            <div>
              <h1 className="text-xl font-bold">{lead.name}</h1>
              <p className="text-sm text-gray-500">{lead.headline}</p>
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                <Badge color="bg-blue-100 text-blue-700">
                  {lead.profile_type || "Unknown"}
                </Badge>
                <Badge
                  color={
                    lead.status === "enrolled"
                      ? "bg-green-100 text-green-700"
                      : "bg-gray-100 text-gray-700"
                  }
                >
                  {lead.status}
                </Badge>
                <Badge color="bg-purple-100 text-purple-700">
                  {lead.source}
                </Badge>
                {lead.is_computer_science_related !== null && (
                  <Badge
                    color={
                      lead.is_computer_science_related
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-red-100 text-red-700"
                    }
                  >
                    {lead.is_computer_science_related ? "CS Related" : "Non-CS"}
                  </Badge>
                )}
                {lead.data_quality && (
                  <Badge
                    color={
                      lead.data_quality === "complete"
                        ? "bg-green-100 text-green-700"
                        : lead.data_quality === "partial"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-red-100 text-red-700"
                    }
                  >
                    {lead.data_quality}
                  </Badge>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleProfile}
              className="text-xs border rounded-lg px-3 py-1.5 hover:bg-gray-50"
            >
              Re-profile
            </button>
          </div>
        </div>
      </div>

      {/* Scores */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          {
            label: "Priority Score",
            value: lead.priority_score,
            icon: Star,
          },
          {
            label: "Profile Score",
            value: lead.profile_score,
            icon: Award,
          },
          {
            label: "Email Opens",
            value: lead.communication?.email_opens ?? 0,
            icon: Mail,
          },
          {
            label: "Email Replies",
            value: lead.communication?.email_replies ?? 0,
            icon: CheckCircle,
          },
        ].map(({ label, value, icon: Icon }) => (
          <div
            key={label}
            className="bg-white rounded-xl border p-4 text-center"
          >
            <Icon size={18} className="mx-auto text-gray-400 mb-1" />
            <div className={`text-xl font-bold ${scoreColor(value)}`}>
              {value ?? "—"}
            </div>
            <div className="text-xs text-gray-500">{label}</div>
          </div>
        ))}
      </div>

      {/* Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border p-5 space-y-1">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-800">
              Contact Information
            </h3>
            {!lead.email && (
              <button
                onClick={handleFindEmail}
                disabled={findingEmail}
                className="text-xs bg-emerald-600 text-white px-3 py-1.5 rounded-lg hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-1"
              >
                {findingEmail ? (
                  <RefreshCw size={12} className="animate-spin" />
                ) : (
                  <Mail size={12} />
                )}
                {findingEmail ? "Searching..." : "Find Email"}
              </button>
            )}
          </div>

          {lead.email ? (
            <InfoRow label="Email" value={lead.email} icon={Mail} />
          ) : emailResult?.source === "error" ? (
            <div className="text-xs text-red-600 py-1.5">
              Failed to search for email. Try again later.
            </div>
          ) : emailResult?.email ? (
            <div className="py-1.5">
              <div className="text-xs font-medium text-emerald-700 flex items-center gap-1">
                <Mail size={14} /> {emailResult.email}
              </div>
              <div className="text-[10px] text-gray-400 mt-0.5">
                Confidence: {emailResult.confidence}% · Source: {emailResult.source}
              </div>
            </div>
          ) : emailResult ? (
            <div className="text-xs text-gray-400 py-1.5">
              No email found. Try adding a company website to improve results.
            </div>
          ) : (
            <InfoRow label="Email" value={null} icon={Mail} />
          )}
          <InfoRow label="Phone" value={lead.phone} icon={User} />
          <InfoRow label="Location" value={lead.location} icon={MapPin} />
          <InfoRow
            label="LinkedIn"
            value={lead.profile_url ? "View Profile" : "—"}
            href={lead.profile_url ?? undefined}
            icon={ExternalLink}
          />
          <InfoRow
            label="Education Level"
            value={lead.education_level}
            icon={GraduationCap}
          />
          <InfoRow
            label="Created"
            value={formatDate(lead.created_at)}
            icon={Globe}
          />
        </div>

        <div className="bg-white rounded-xl border p-5">
          <h3 className="text-sm font-semibold text-gray-800 mb-3">
            Matched Programs
          </h3>
          {lead.matched_programs && lead.matched_programs.length > 0 ? (
            <div className="space-y-2">
              {lead.matched_programs.map((p, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-gray-700">{p.program}</span>
                  <span
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full ${scoreBg(p.score)} ${scoreColor(p.score)}`}
                  >
                    {p.score}%
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-400">No program matches yet.</p>
          )}
        </div>
      </div>

      {/* Skills */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-center gap-2 mb-3">
          <Code size={16} className="text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-800">Skills</h3>
        </div>
        {lead.skills && lead.skills.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {lead.skills.map((skill) => (
              <span
                key={skill}
                className="bg-gray-100 px-2.5 py-1 rounded-lg text-xs"
              >
                {skill}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xs text-gray-400">No skills listed.</p>
        )}
      </div>

      {/* Education */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-center gap-2 mb-3">
          <GraduationCap size={16} className="text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-800">Education</h3>
        </div>
        {lead.education && lead.education.length > 0 ? (
          <div className="space-y-3">
            {lead.education.map((edu, i) => (
              <div key={i} className="border-b pb-2 last:border-0 last:pb-0">
                <div className="text-sm font-medium">{edu.institution}</div>
                <div className="text-xs text-gray-500">
                  {edu.degree} in {edu.field}
                </div>
                <div className="text-xs text-gray-400">
                  {edu.start_year} – {edu.end_year || "Present"}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-gray-400">No education data.</p>
        )}
      </div>

      {/* Experience */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-center gap-2 mb-3">
          <Briefcase size={16} className="text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-800">Experience</h3>
        </div>
        {lead.experience && lead.experience.length > 0 ? (
          <div className="space-y-3">
            {lead.experience.map((exp, i) => (
              <div key={i} className="border-b pb-2 last:border-0 last:pb-0">
                <div className="text-sm font-medium">{exp.title}</div>
                <div className="text-xs text-gray-500">{exp.company}</div>
                <div className="text-xs text-gray-400">
                  {exp.start_date} – {exp.end_date || "Present"}
                </div>
                {exp.description && (
                  <p className="text-xs text-gray-600 mt-1">{exp.description}</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-gray-400">No experience data.</p>
        )}
      </div>

      {/* LinkedIn Interaction Monitoring */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Linkedin size={16} className="text-blue-600" />
            <h3 className="text-sm font-semibold text-gray-800">
              LinkedIn Interaction Monitoring
            </h3>
          </div>
          <div className="flex items-center gap-2">
            {lead.linkedin_url && (
              <a
                href={lead.linkedin_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-600 hover:underline flex items-center gap-1"
              >
                Open LinkedIn <ExternalLink size={10} />
              </a>
            )}
            <button
              onClick={() => setShowLogForm((v) => !v)}
              className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 flex items-center gap-1"
            >
              <Send size={12} /> Log Interaction
            </button>
          </div>
        </div>

        {/* Log interaction form */}
        {showLogForm && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 space-y-2">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              <select
                value={interactionType}
                onChange={(e) => setInteractionType(e.target.value)}
                className="border rounded-lg px-2 py-1.5 text-xs"
              >
                <option value="profile_view">Profile Viewed</option>
                <option value="connection_request">Connection Request Sent</option>
                <option value="connection_accepted">Connection Accepted</option>
                <option value="message_sent">Message / InMail Sent</option>
                <option value="reply_received">Reply Received</option>
                <option value="follow_up_sent">Follow-up Sent</option>
                <option value="note">Note</option>
              </select>
              <input
                type="text"
                value={interactionNotes}
                onChange={(e) => setInteractionNotes(e.target.value)}
                placeholder="Notes or reply content..."
                className="md:col-span-2 border rounded-lg px-2 py-1.5 text-xs"
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowLogForm(false)}
                className="text-xs px-3 py-1.5 rounded-lg border hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleLogInteraction}
                disabled={logging}
                className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
              >
                {logging && <RefreshCw size={12} className="animate-spin" />}
                Save Interaction
              </button>
            </div>
          </div>
        )}

        {/* Interaction timeline */}
        {interactions.length > 0 ? (
          <div className="space-y-0">
            {interactions.map((interaction, i) => {
              const typeMeta = {
                profile_view: { icon: Eye, color: "bg-gray-100 text-gray-600", label: "Profile Viewed" },
                connection_request: { icon: UserPlus, color: "bg-blue-100 text-blue-700", label: "Connection Request Sent" },
                connection_accepted: { icon: CheckCircle, color: "bg-green-100 text-green-700", label: "Connection Accepted" },
                message_sent: { icon: MessageSquare, color: "bg-purple-100 text-purple-700", label: "Message / InMail Sent" },
                reply_received: { icon: Send, color: "bg-emerald-100 text-emerald-700", label: "Reply Received" },
                follow_up_sent: { icon: RefreshCw, color: "bg-yellow-100 text-yellow-700", label: "Follow-up Sent" },
                note: { icon: Star, color: "bg-gray-100 text-gray-600", label: "Note" },
              }[interaction.type] || {
                icon: Star,
                color: "bg-gray-100 text-gray-600",
                label: interaction.type,
              };
              const Icon = typeMeta.icon;
              return (
                <div key={interaction.id || i} className="flex gap-3 py-2.5">
                  <div className="flex flex-col items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${typeMeta.color} shrink-0`}>
                      <Icon size={14} />
                    </div>
                    {i < interactions.length - 1 && (
                      <div className="w-px flex-1 bg-gray-200 my-1" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1 pb-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-gray-800">
                        {typeMeta.label}
                      </span>
                      <span className="text-[10px] text-gray-400">
                        {new Date(interaction.at).toLocaleString()}
                      </span>
                    </div>
                    {interaction.notes && (
                      <p className="text-xs text-gray-600 mt-0.5">
                        {interaction.notes}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-6 text-gray-400">
            <Linkedin size={28} className="mx-auto text-gray-300 mb-2" />
            <p className="text-sm">
              No LinkedIn interactions logged yet. Click "Log Interaction" to
              start tracking outreach for this profile.
            </p>
          </div>
        )}
      </div>

      {/* Email Conversation Thread */}
      <div className="bg-white rounded-xl border p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Mail size={16} className="text-gray-400" />
            <h2 className="font-semibold text-sm">Email Conversation Thread</h2>
            {conversation && (
              <span className={`text-xs px-2 py-0.5 rounded-full border font-medium
                ${{ replied: "bg-emerald-100 text-emerald-700 border-emerald-200",
                    clicked: "bg-purple-100 text-purple-700 border-purple-200",
                    opened: "bg-blue-100 text-blue-700 border-blue-200",
                    sent: "bg-green-100 text-green-700 border-green-200",
                    bounced: "bg-red-100 text-red-700 border-red-200",
                    no_activity: "bg-gray-100 text-gray-500 border-gray-200",
                  }[conversation.status] || "bg-gray-100 text-gray-500 border-gray-200"}`}>
                {conversation.status?.replace("_", " ")}
              </span>
            )}
          </div>
          <button
            onClick={() => loadConversation(id)}
            disabled={convLoading}
            className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
          >
            <RefreshCw size={12} className={convLoading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>

        {convLoading ? (
          <div className="flex items-center justify-center py-8 text-gray-400">
            <RefreshCw size={16} className="animate-spin mr-2" /> Loading thread...
          </div>
        ) : !conversation || conversation.messages_count === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <Mail size={28} className="mx-auto text-gray-300 mb-2" />
            <p className="text-sm">No email activity yet for this lead.</p>
            <p className="text-xs text-gray-400 mt-1">Send a campaign to start the conversation.</p>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-xs text-gray-400">{conversation.messages_count} messages</p>
            {conversation.messages.map((msg) => (
              <div
                key={msg.id}
                className={`rounded-lg border p-3.5 ${
                  msg.direction === "outgoing"
                    ? "bg-blue-50 border-blue-100 ml-4"
                    : msg.type === "auto_response"
                    ? "bg-indigo-50 border-indigo-100 ml-4"
                    : "bg-gray-50 border-gray-100 mr-4"
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded
                      ${ msg.direction === "outgoing" ? "bg-blue-200 text-blue-700" : "bg-gray-200 text-gray-600" }`}>
                      {msg.type === "auto_response" ? "Auto Reply" : msg.direction === "outgoing" ? "Sent" : "Reply"}
                    </span>
                    {msg.intent && (
                      <span className="text-[10px] px-1.5 py-0.5 bg-green-100 text-green-700 rounded font-medium">
                        {msg.intent.replace("_", " ")}
                      </span>
                    )}
                    {msg.opened_at && (
                      <span className="flex items-center gap-0.5 text-[10px] text-green-600">
                        <Eye size={9} /> Dibuka {msg.opened_count}x
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] text-gray-400 shrink-0">
                    {msg.sent_at || msg.received_at
                      ? new Date(msg.sent_at || msg.received_at).toLocaleString("id-ID")
                      : "—"}
                  </span>
                </div>
                <p className="text-xs font-medium text-gray-700 mb-1">{msg.subject || "(no subject)"}</p>
                {(msg.body_text || msg.body) && (
                  <p className="text-xs text-gray-600 line-clamp-3">
                    {msg.body_text ||
                      (msg.body
                        ? msg.body.replace(/<[^>]+>/g, " ").trim().slice(0, 200)
                        : "")}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
