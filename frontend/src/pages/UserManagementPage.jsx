import { useEffect, useState } from "react";
import axios from "axios";
import {
  Users, UserPlus, Shield, User,
  CheckCircle, XCircle, Trash2, Key,
  AlertCircle
} from "lucide-react";

export default function UserManagementPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({ name: "", email: "", password: "", role: "user" });

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get("/api/users");
      setUsers(data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || "Gagal memuat pengguna.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleAddUser = async (e) => {
    e.preventDefault();
    try {
      await axios.post("/api/users", formData);
      setFormData({ name: "", email: "", password: "", role: "user" });
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
      alert(err.response?.data?.detail || "Gagal mengubah status pengguna.");
    }
  };

  const changeRole = async (user, newRole) => {
    try {
      await axios.patch(`/api/users/${user.id}`, { role: newRole });
      fetchUsers();
    } catch (err) {
      alert(err.response?.data?.detail || "Gagal mengubah role pengguna.");
    }
  };

  const deleteUser = async (user) => {
    if (!window.confirm(`Yakin ingin menghapus ${user.name}?`)) return;
    try {
      await axios.delete(`/api/users/${user.id}`);
      fetchUsers();
    } catch (err) {
      alert(err.response?.data?.detail || "Gagal menghapus pengguna.");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Manajemen Pengguna</h1>
          <p className="text-sm text-gray-500 mt-1">Kelola akses, peran (RBAC), dan akun staf sistem PRISM.</p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm text-sm"
        >
          {showAddForm ? <XCircle size={16} /> : <UserPlus size={16} />}
          {showAddForm ? "Batal" : "Tambah Pengguna"}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-xl flex items-start gap-3 border border-red-100">
          <AlertCircle size={20} className="shrink-0 mt-0.5" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Add User Form */}
      {showAddForm && (
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm animate-in fade-in slide-in-from-top-4">
          <h2 className="text-lg font-semibold mb-4 border-b pb-3">Buat Pengguna Baru</h2>
          <form onSubmit={handleAddUser} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Nama Lengkap</label>
              <input
                required
                type="text"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Alamat Email</label>
              <input
                required
                type="email"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Password</label>
              <input
                required
                type="password"
                minLength={6}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Peran Akses (Role)</label>
              <select
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              >
                <option value="user">User Biasa</option>
                <option value="recruiter">Recruiter</option>
                <option value="admin">Administrator</option>
              </select>
            </div>
            <div className="md:col-span-2 pt-2 border-t mt-2 flex justify-end">
              <button
                type="submit"
                className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition"
              >
                Simpan Pengguna
              </button>
            </div>
          </form>
        </div>
      )}

      {/* User Table */}
      <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-400">Loading users...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-gray-50 border-b text-gray-600">
                <tr>
                  <th className="px-4 py-3 font-semibold">Pengguna</th>
                  <th className="px-4 py-3 font-semibold">Role</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold text-right">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
                          <User size={16} />
                        </div>
                        <div>
                          <div className="font-medium text-gray-800">{user.name}</div>
                          <div className="text-xs text-gray-500">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <select
                        value={user.role}
                        onChange={(e) => changeRole(user, e.target.value)}
                        className={`text-xs px-2 py-1 border rounded-lg font-medium cursor-pointer focus:outline-none focus:ring-1 focus:ring-blue-500
                          ${user.role === 'admin' ? 'bg-purple-50 text-purple-700 border-purple-200' : 
                            user.role === 'recruiter' ? 'bg-blue-50 text-blue-700 border-blue-200' : 
                            'bg-gray-50 text-gray-700 border-gray-200'}`}
                      >
                        <option value="admin">Admin</option>
                        <option value="recruiter">Recruiter</option>
                        <option value="user">User</option>
                      </select>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => toggleStatus(user)}
                        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors
                          ${user.is_active ? 'bg-green-100 text-green-700 hover:bg-green-200' : 'bg-red-100 text-red-700 hover:bg-red-200'}`}
                      >
                        {user.is_active ? <CheckCircle size={12} /> : <XCircle size={12} />}
                        {user.is_active ? 'Aktif' : 'Nonaktif'}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <button
                          title="Hapus Pengguna"
                          onClick={() => deleteUser(user)}
                          className="p-1.5 text-red-500 bg-red-50 rounded hover:bg-red-100 transition-colors"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                      Tidak ada pengguna ditemukan.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
