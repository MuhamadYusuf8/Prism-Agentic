import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../lib/auth-context";
import {
  Users, UserPlus, Shield, User,
  CheckCircle, XCircle, Trash2,
  AlertCircle, ChevronLeft, ChevronRight,
  Clock, Activity
} from "lucide-react";

const ROLE_CONFIG = {
  admin:     { label: "Admin",     color: "bg-purple-100 text-purple-700 border-purple-200" },
  recruiter: { label: "Recruiter", color: "bg-blue-100 text-blue-700 border-blue-200" },
  viewer:    { label: "Viewer",    color: "bg-gray-100 text-gray-700 border-gray-200" },
};

export default function UserManagementPage() {
  const { user: currentUser } = useAuth();
  const navigate = useNavigate();

  const [users, setUsers]       = useState([]);
  const [total, setTotal]       = useState(0);
  const [page, setPage]         = useState(1);
  const PAGE_SIZE               = 20;

  const [activeTab, setActiveTab] = useState("users"); // "users" | "audit"
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditTotal, setAuditTotal] = useState(0);
  const [auditPage, setAuditPage]   = useState(1);

  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({ name: "", email: "", password: "", role: "viewer" });

  // ── Role Guard ─────────────────────────────────────────────────────────────
  useEffect(() => {
    if (currentUser && currentUser.role !== "admin") {
      navigate("/dashboard", { replace: true });
    }
  }, [currentUser, navigate]);

  // ── Fetch Users ────────────────────────────────────────────────────────────
  const fetchUsers = async (p = page) => {
    setLoading(true);
    try {
      const { data } = await axios.get(`/api/users/?page=${p}&page_size=${PAGE_SIZE}`);
      setUsers(data.data);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || "Gagal memuat pengguna.");
    } finally {
      setLoading(false);
    }
  };

  // ── Fetch Audit Logs ───────────────────────────────────────────────────────
  const fetchAuditLogs = async (p = auditPage) => {
    setLoading(true);
    try {
      const { data } = await axios.get(`/api/users/audit-logs?page=${p}&page_size=30`);
      setAuditLogs(data.data);
      setAuditTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || "Gagal memuat audit log.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "users") fetchUsers(page);
    else fetchAuditLogs(auditPage);
  }, [activeTab, page, auditPage]);

  // ── Actions ────────────────────────────────────────────────────────────────
  const handleAddUser = async (e) => {
    e.preventDefault();
    try {
      await axios.post("/api/users/", formData);
      setFormData({ name: "", email: "", password: "", role: "viewer" });
      setShowAddForm(false);
      fetchUsers();
    } catch (err) {
      alert(err.response?.data?.detail || "Gagal menambah pengguna.");
    }
  };

  const toggleStatus = async (user) => {
    try {
      await axios.patch(`/api/users/${user.id}`, { is_active: !user.is_active });
      fetchUsers();
    } catch (err) {
      alert(err.response?.data?.detail || "Gagal mengubah status.");
    }
  };

  const changeRole = async (user, newRole) => {
    try {
      await axios.patch(`/api/users/${user.id}`, { role: newRole });
      fetchUsers();
    } catch (err) {
      alert(err.response?.data?.detail || "Gagal mengubah role.");
    }
  };

  const deleteUser = async (user) => {
    if (!window.confirm(`Hapus akun ${user.name} (${user.email})? Tindakan ini tidak dapat dibatalkan.`)) return;
    try {
      await axios.delete(`/api/users/${user.id}`);
      fetchUsers();
    } catch (err) {
      alert(err.response?.data?.detail || "Gagal menghapus pengguna.");
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Shield size={22} className="text-purple-600" />
            Manajemen Pengguna
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            RBAC — Kelola akun, peran, dan rekam jejak aktivitas sistem PRISM.
          </p>
        </div>
        {activeTab === "users" && (
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors shadow-sm text-sm"
          >
            {showAddForm ? <XCircle size={16} /> : <UserPlus size={16} />}
            {showAddForm ? "Batal" : "Tambah Pengguna"}
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {[
          { id: "users", label: "Daftar Pengguna", icon: Users },
          { id: "audit", label: "Audit Log", icon: Activity },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px
              ${activeTab === id
                ? "border-purple-600 text-purple-700"
                : "border-transparent text-gray-500 hover:text-gray-700"}`}
          >
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-xl flex items-start gap-3 border border-red-100">
          <AlertCircle size={20} className="shrink-0 mt-0.5" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* ── TAB: Users ──────────────────────────────────────────────────────── */}
      {activeTab === "users" && (
        <>
          {showAddForm && (
            <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
              <h2 className="text-base font-semibold mb-4 border-b pb-3">Buat Pengguna Baru</h2>
              <form onSubmit={handleAddUser} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Nama Lengkap</label>
                  <input
                    required type="text"
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-500"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Alamat Email</label>
                  <input
                    required type="email"
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-500"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Password <span className="text-gray-400 font-normal">(min. 8 karakter)</span>
                  </label>
                  <input
                    required type="password" minLength={8}
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-500"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Peran (Role)</label>
                  <select
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-500"
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  >
                    <option value="viewer">Viewer (Read-only)</option>
                    <option value="recruiter">Recruiter</option>
                    <option value="admin">Administrator</option>
                  </select>
                </div>
                <div className="md:col-span-2 pt-2 border-t flex justify-end">
                  <button type="submit" className="px-6 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition">
                    Simpan Pengguna
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Summary Stats */}
          <div className="text-sm text-gray-500">
            Total <span className="font-semibold text-gray-700">{total}</span> pengguna
          </div>

          <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-gray-400">Memuat pengguna...</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm whitespace-nowrap">
                  <thead className="bg-gray-50 border-b text-gray-600 text-xs uppercase tracking-wider">
                    <tr>
                      <th className="px-5 py-3 font-semibold">Pengguna</th>
                      <th className="px-5 py-3 font-semibold">Role</th>
                      <th className="px-5 py-3 font-semibold">Status</th>
                      <th className="px-5 py-3 font-semibold">Last Login</th>
                      <th className="px-5 py-3 font-semibold text-right">Aksi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {users.map((user) => (
                      <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-5 py-3.5">
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
                              ${user.role === "admin" ? "bg-purple-100 text-purple-700" :
                                user.role === "recruiter" ? "bg-blue-100 text-blue-700" :
                                "bg-gray-100 text-gray-600"}`}>
                              {user.name?.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <div className="font-medium text-gray-800">
                                {user.name}
                                {String(user.id) === String(currentUser?.id) && (
                                  <span className="ml-2 text-xs bg-yellow-50 text-yellow-700 px-1.5 py-0.5 rounded border border-yellow-200">Saya</span>
                                )}
                              </div>
                              <div className="text-xs text-gray-500">{user.email}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-3.5">
                          <select
                            value={user.role}
                            disabled={String(user.id) === String(currentUser?.id)}
                            onChange={(e) => changeRole(user, e.target.value)}
                            className={`text-xs px-2.5 py-1 border rounded-lg font-medium cursor-pointer focus:outline-none focus:ring-1 focus:ring-purple-500 disabled:opacity-60 disabled:cursor-not-allowed
                              ${ROLE_CONFIG[user.role]?.color || "bg-gray-100 text-gray-700"}`}
                          >
                            <option value="admin">Admin</option>
                            <option value="recruiter">Recruiter</option>
                            <option value="viewer">Viewer</option>
                          </select>
                        </td>
                        <td className="px-5 py-3.5">
                          <button
                            onClick={() => toggleStatus(user)}
                            disabled={String(user.id) === String(currentUser?.id)}
                            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors disabled:opacity-60 disabled:cursor-not-allowed
                              ${user.is_active
                                ? "bg-green-100 text-green-700 hover:bg-green-200"
                                : "bg-red-100 text-red-700 hover:bg-red-200"}`}
                          >
                            {user.is_active ? <CheckCircle size={12} /> : <XCircle size={12} />}
                            {user.is_active ? "Aktif" : "Nonaktif"}
                          </button>
                        </td>
                        <td className="px-5 py-3.5 text-xs text-gray-500">
                          {user.last_login
                            ? new Date(user.last_login).toLocaleString("id-ID", { dateStyle: "medium", timeStyle: "short" })
                            : <span className="italic text-gray-400">Belum pernah</span>}
                        </td>
                        <td className="px-5 py-3.5 text-right">
                          <button
                            title="Hapus Pengguna"
                            disabled={String(user.id) === String(currentUser?.id)}
                            onClick={() => deleteUser(user)}
                            className="p-1.5 text-red-500 bg-red-50 rounded hover:bg-red-100 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                          >
                            <Trash2 size={15} />
                          </button>
                        </td>
                      </tr>
                    ))}
                    {users.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-5 py-10 text-center text-gray-400">
                          Tidak ada pengguna.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Halaman {page} dari {totalPages}</span>
              <div className="flex gap-2">
                <button
                  disabled={page === 1}
                  onClick={() => setPage(p => p - 1)}
                  className="p-2 border rounded-lg disabled:opacity-40 hover:bg-gray-50 transition"
                >
                  <ChevronLeft size={16} />
                </button>
                <button
                  disabled={page === totalPages}
                  onClick={() => setPage(p => p + 1)}
                  className="p-2 border rounded-lg disabled:opacity-40 hover:bg-gray-50 transition"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* ── TAB: Audit Log ──────────────────────────────────────────────────── */}
      {activeTab === "audit" && (
        <>
          <div className="text-sm text-gray-500">
            Total <span className="font-semibold text-gray-700">{auditTotal}</span> entri log
          </div>
          <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-gray-400">Memuat audit log...</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm whitespace-nowrap">
                  <thead className="bg-gray-50 border-b text-gray-600 text-xs uppercase tracking-wider">
                    <tr>
                      <th className="px-5 py-3 font-semibold">Waktu</th>
                      <th className="px-5 py-3 font-semibold">Pelaku</th>
                      <th className="px-5 py-3 font-semibold">Aksi</th>
                      <th className="px-5 py-3 font-semibold">Resource</th>
                      <th className="px-5 py-3 font-semibold">IP</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {auditLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-5 py-3 text-xs text-gray-500">
                          <div className="flex items-center gap-1.5">
                            <Clock size={12} />
                            {log.created_at
                              ? new Date(log.created_at).toLocaleString("id-ID", { dateStyle: "short", timeStyle: "medium" })
                              : "-"}
                          </div>
                        </td>
                        <td className="px-5 py-3">
                          <div className="font-medium text-gray-800 text-xs">{log.actor_name || "-"}</div>
                          <div className="text-xs text-gray-400">{log.actor_email || "-"}</div>
                        </td>
                        <td className="px-5 py-3">
                          <span className={`text-xs px-2 py-0.5 rounded font-mono font-medium
                            ${log.action?.startsWith("delete") ? "bg-red-50 text-red-700" :
                              log.action?.startsWith("create") ? "bg-green-50 text-green-700" :
                              "bg-blue-50 text-blue-700"}`}>
                            {log.action}
                          </span>
                        </td>
                        <td className="px-5 py-3 text-xs text-gray-600">
                          <span className="font-medium">{log.resource_type}</span>
                          {log.resource_id && <span className="text-gray-400 ml-1">#{log.resource_id.slice(0, 8)}</span>}
                        </td>
                        <td className="px-5 py-3 text-xs text-gray-400 font-mono">
                          {log.ip_address || "-"}
                        </td>
                      </tr>
                    ))}
                    {auditLogs.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-5 py-10 text-center text-gray-400">Tidak ada log audit.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Audit Pagination */}
          {Math.ceil(auditTotal / 30) > 1 && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Halaman {auditPage} dari {Math.ceil(auditTotal / 30)}</span>
              <div className="flex gap-2">
                <button disabled={auditPage === 1} onClick={() => setAuditPage(p => p - 1)} className="p-2 border rounded-lg disabled:opacity-40 hover:bg-gray-50">
                  <ChevronLeft size={16} />
                </button>
                <button disabled={auditPage >= Math.ceil(auditTotal / 30)} onClick={() => setAuditPage(p => p + 1)} className="p-2 border rounded-lg disabled:opacity-40 hover:bg-gray-50">
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
