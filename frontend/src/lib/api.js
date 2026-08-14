import axios from "axios";

/**
 * Configured axios instance with interceptors for:
 * - Automatically attaching JWT Bearer token
 * - Redirecting to /login on 401 Unauthorized
 * - Toast error notification on 500 Server Error
 */

export const api = axios.create({ baseURL: "" });

// ── Request interceptor: attach JWT ───────────────────────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("prism_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response interceptor: handle 401 + 500 globally ──────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;

    if (status === 401) {
      // Token expired or invalid — clean up and redirect to login
      localStorage.removeItem("prism_token");
      localStorage.removeItem("prism_user");
      // Only redirect if not already on login page
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
      return Promise.reject(error);
    }

    if (status === 403) {
      // Show toast via custom event — ToastProvider will listen
      window.dispatchEvent(
        new CustomEvent("prism:toast", {
          detail: {
            type: "warning",
            title: "Akses Ditolak",
            message: error.response?.data?.detail || "Anda tidak memiliki izin untuk aksi ini.",
          },
        })
      );
      return Promise.reject(error);
    }

    if (status >= 500) {
      window.dispatchEvent(
        new CustomEvent("prism:toast", {
          detail: {
            type: "error",
            title: "Server Error",
            message:
              error.response?.data?.detail ||
              "Terjadi kesalahan pada server. Silakan coba lagi.",
          },
        })
      );
      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

/* ─── Auth API ─────────────────────────────────────────────────── */
export const authAPI = {
  login: (email, password) => api.post("/api/auth/login", { email, password }),
  register: (name, email, password) =>
    api.post("/api/auth/register", { name, email, password }),
  getProfile: () => api.get("/api/auth/me"),
};

/* ─── Leads API ────────────────────────────────────────────────── */
export const leadsAPI = {
  list: (params) => api.get("/api/leads", { params }),
  getById: (id) => api.get(`/api/leads/${id}`),
  create: (data) => api.post("/api/leads", data),
  update: (id, data) => api.patch(`/api/leads/${id}`, data),
  delete: (id) => api.delete(`/api/leads/${id}`),
  profile: (id) => api.post(`/api/leads/${id}/profile`),
  profileBatch: (ids) => api.post("/api/leads/profile/batch", { lead_ids: ids }),
  cluster: (ids) => api.post("/api/leads/cluster", ids ? { lead_ids: ids } : {}),
  profilingStats: () => api.get("/api/leads/stats/profiling"),
  clusterStats: () => api.get("/api/leads/stats/clusters"),
  importAlumni: (formData) =>
    api.post("/api/leads/import/alumni", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
};

/* ─── Campaigns API ────────────────────────────────────────────── */
export const campaignsAPI = {
  list: (params) => api.get("/api/campaigns", { params }),
  getById: (id) => api.get(`/api/campaigns/${id}`),
  create: (data) => api.post("/api/campaigns", data),
  update: (id, data) => api.put(`/api/campaigns/${id}`, data),
  delete: (id) => api.delete(`/api/campaigns/${id}`),
  activate: (id) => api.post(`/api/campaigns/${id}/activate`),
  pause: (id) => api.post(`/api/campaigns/${id}/pause`),
  sendTest: (id, email) => api.post(`/api/campaigns/${id}/send-test`, { email }),
  sendFollowUps: (id) => api.post(`/api/campaigns/${id}/send-follow-ups`),
  getStats: (id) => api.get(`/api/campaigns/${id}/stats`),
  getLogs: (id, params) => api.get(`/api/campaigns/${id}/logs`, { params }),
  getReplies: (id) => api.get(`/api/campaigns/${id}/replies`),
  send: (id, body) => api.post(`/api/campaigns/${id}/send`, body),
};

/* ─── Email Monitoring API ────────────────────────────────────── */
export const emailMonitoringAPI = {
  overview: () => api.get("/api/email/monitoring/overview"),
  conversations: (params) => api.get("/api/email/monitoring/conversations", { params }),
  conversation: (key) =>
    api.get(`/api/email/monitoring/conversations/${encodeURIComponent(key)}`),
  syncInbox: () => api.post("/api/email/monitoring/sync-inbox"),
  replies: (params) => api.get("/api/email/monitoring/replies", { params }),
  processReply: (data) => api.post("/api/email/monitoring/process-reply", data),
  triggerFollowUps: (campaignId) =>
    api.post("/api/email/monitoring/trigger-follow-ups", campaignId ? { campaign_id: campaignId } : {}),
};

/* ─── Analytics API ────────────────────────────────────────────── */
export const analyticsAPI = {
  summary: () => api.get("/api/analytics/summary"),
  funnel: () => api.get("/api/analytics/funnel"),
  trends: () => api.get("/api/analytics/trends"),
  byEducation: () => api.get("/api/analytics/by-education"),
  byProgram: () => api.get("/api/analytics/by-program"),
  profileDistribution: () => api.get("/api/analytics/profile-distribution"),
  topProspects: (limit = 10) => api.get("/api/analytics/top-prospects", { params: { limit } }),
  emailPerformance: () => api.get("/api/analytics/email-performance"),
};

/* ─── Users API ─────────────────────────────────────────────────── */
export const usersAPI = {
  list: (params) => api.get("/api/users/", { params }),
  create: (data) => api.post("/api/users/", data),
  update: (id, data) => api.patch(`/api/users/${id}`, data),
  delete: (id) => api.delete(`/api/users/${id}`),
  me: () => api.get("/api/users/me"),
  updatePassword: (data) => api.patch("/api/users/me/password", data),
  auditLogs: (params) => api.get("/api/users/audit-logs", { params }),
};

/* ─── Documents API ────────────────────────────────────────────── */
export const documentsAPI = {
  list: () => api.get("/api/documents"),
  upload: (formData) =>
    api.post("/api/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  delete: (sourceFile) => api.delete(`/api/documents/${sourceFile}`),
  seed: () => api.post("/api/documents/seed"),
};

/* ─── Scraper API ──────────────────────────────────────────────── */
export const scraperAPI = {
  linkedinStream: (body, token) =>
    fetch("/api/scraper/linkedin/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token || localStorage.getItem("prism_token")}`,
      },
      body,
    }),
  linkedinStatus: () => api.get("/api/scraper/linkedin/status"),
  cikarang: () => api.post("/api/scraper/cikarang"),
};

/* ─── Export API ───────────────────────────────────────────────── */
export const exportAPI = {
  csv: (source) => (source ? `/api/export/csv?source=${source}` : "/api/export/csv"),
  excel: (source) => (source ? `/api/export/excel?source=${source}` : "/api/export/excel"),
};
