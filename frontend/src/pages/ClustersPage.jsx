import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { Layers, Users, MapPin, Code, Briefcase, GraduationCap, Target } from "lucide-react";

const TYPE_CONFIG = {
  master: {
    icon: GraduationCap,
    color: "text-blue-700",
    bg: "bg-blue-50",
    border: "border-blue-200",
  },
  unknown: {
    icon: Users,
    color: "text-gray-700",
    bg: "bg-gray-50",
    border: "border-gray-200",
  },
};

function ClusterCard({ cluster }) {
  const cfg = TYPE_CONFIG[cluster.type] ?? TYPE_CONFIG.unknown;
  const Icon = cfg.icon;

  return (
    <div className={`rounded-xl border ${cfg.border} ${cfg.bg} p-5 space-y-4`}>
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${cfg.bg} ${cfg.color}`}>
          <Icon size={20} />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">{cluster.name}</h3>
          <p className="text-xs text-gray-500">
            {cluster.lead_count} leads · {cluster.type}
          </p>
        </div>
      </div>

      <p className="text-xs text-gray-600">{cluster.description}</p>

      {cluster.characteristics && (
        <>
          <div>
            <div className="flex items-center gap-1 text-xs font-medium text-gray-500 mb-1.5">
              <Code size={12} />
              <span>Common Skills</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {cluster.characteristics.common_skills.slice(0, 5).map((skill) => (
                <span
                  key={skill}
                  className="bg-white px-2 py-0.5 rounded text-xs border"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center gap-1 text-xs font-medium text-gray-500 mb-1.5">
              <MapPin size={12} />
              <span>Top Locations</span>
            </div>
            <div className="space-y-0.5">
              {cluster.characteristics.top_locations.slice(0, 3).map((loc) => (
                <div key={loc.location} className="text-xs text-gray-600">
                  {loc.location} ({loc.count})
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="bg-white rounded-lg p-2 border">
              <div className="font-semibold">
                {cluster.characteristics.avg_experience?.toFixed(1) ?? "—"}y
              </div>
              <div className="text-gray-400">Exp</div>
            </div>
            <div className="bg-white rounded-lg p-2 border">
              <div className="font-semibold">
                {cluster.characteristics.avg_profile_score?.toFixed(1) ?? "—"}
              </div>
              <div className="text-gray-400">Profile</div>
            </div>
            <div className="bg-white rounded-lg p-2 border">
              <div className="font-semibold">
                {cluster.characteristics.avg_priority_score?.toFixed(1) ?? "—"}
              </div>
              <div className="text-gray-400">Priority</div>
            </div>
          </div>
        </>
      )}

      <Link
        to={`/email?targetCluster=${cluster.id}&type=${cluster.type}`}
        className="block text-center text-xs font-medium text-blue-600 hover:text-blue-800 border border-blue-200 rounded-lg py-1.5 hover:bg-blue-50 transition"
      >
        <Target size={12} className="inline mr-1" />
        Create Campaign for this Cluster
      </Link>
    </div>
  );
}

export default function ClustersPage() {
  const [clusters, setClusters] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [cRes, sRes] = await Promise.all([
          axios.get("/api/clusters"),
          axios.get("/api/clusters/stats"),
        ]);
        setClusters(cRes.data);
        setStats(sRes.data);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return <div className="text-center py-12 text-gray-400">Loading...</div>;
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Clusters</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {stats?.total_leads ?? 0} leads grouped into {clusters.length} clusters
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Layers size={16} />
          <span>{clusters.length} clusters</span>
        </div>
      </div>

      {clusters.length === 0 ? (
        <div className="bg-white rounded-xl border p-8 text-center">
          <Layers size={40} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500 mb-3">No clusters found.</p>
          <Link
            to="/linkedin"
            className="text-blue-600 hover:underline text-sm font-medium"
          >
            Import leads to generate clusters
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {clusters.map((c) => (
            <ClusterCard key={c.id} cluster={c} />
          ))}
        </div>
      )}
    </div>
  );
}
