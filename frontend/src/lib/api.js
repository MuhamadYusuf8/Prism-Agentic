import axios from "axios";

// In React SPA, we use Vite proxy which forwards /api/* to http://localhost:8000/api/*
export const api = axios.create({
  baseURL: "",
});

/* ─── Auth API ─────────────────────────────────────────────────── */
export const authAPI = {
  login: (email, password) =>
    api.post("/api/auth/login", { email, password }),
  register: (name, email, password) =>
    api.post("/api/auth/register", { name, email, password }),
  getProfile: () => api.get("/api/auth/me"),
  listUsers: () => api.get("/api/auth/users"),
};

/* ─── Leads API ────────────────────────────────────────────────── */
export const leadsAPI = {
  list: (params) =>
    api.get("/api/leads", { params }),
  getById: (id) => api.get(`/api/leads/${id}`),
  create: (data) => api.post("/api/leads", data),
  update: (id, data) => api.patch(`/api/leads/${id}`, data),
  delete: (id) => api.delete(`/api/leads/${id}`),
  profile: (id) => api.post(`/api/leads/${id}/profile`),
  profileBatch: (ids) =>
    api.post("/api/leads/profile/batch", { lead_ids: ids }),
  cluster: (ids) =>
    api.post("/api/leads/cluster", ids ? { lead_ids: ids } : {}),
  profilingStats: () => api.get("/api/leads/stats/profiling"),
  clusterStats: () => api.get("/api/leads/stats/clusters"),
  importAlumni: (formData) =>
    api.post("/api/leads/import/alumni", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
};

/* ─── Campaigns API ────────────────────────────────────────────── */
export const campaignsAPI = {
  list: (params) =>
    api.get("/api/campaigns", { params }),
  getById: (id) => api.get(`/api/campaigns/${id}`),
  create: (data) => api.post("/api/campaigns", data),
  update: (id, data) => api.put(`/api/campaigns/${id}`, data),
  delete: (id) => api.delete(`/api/campaigns/${id}`),
  activate: (id) => api.post(`/api/campaigns/${id}/activate`),
  pause: (id) => api.post(`/api/campaigns/${id}/pause`),
  sendTest: (id, email) =>
    api.post(`/api/campaigns/${id}/send-test`, { email }),
  sendFollowUps: (id) =>
    api.post(`/api/campaigns/${id}/send-follow-ups`),
  getStats: (id) => api.get(`/api/campaigns/${id}/stats`),
};

/* ─── Email Monitoring API ────────────────────────────────────── */
export const emailMonitoringAPI = {
  overview: () => api.get("/api/email/monitoring/overview"),
  conversations: (params) =>
    api.get("/api/email/monitoring/conversations", { params }),
  conversation: (key) =>
    api.get(`/api/email/monitoring/conversations/${encodeURIComponent(key)}`),
  syncInbox: () => api.post("/api/email/monitoring/sync-inbox"),
};

/* ─── Analytics API ────────────────────────────────────────────── */
export const analyticsAPI = {
  summary: () => api.get("/api/analytics/summary"),
  funnel: () => api.get("/api/analytics/funnel"),
  trends: () => api.get("/api/analytics/trends"),
  byEducation: () => api.get("/api/analytics/by-education"),
  byProgram: () => api.get("/api/analytics/by-program"),
  profileDistribution: () => api.get("/api/analytics/profile-distribution"),
  topProspects: (limit = 10) =>
    api.get("/api/analytics/top-prospects", { params: { limit } }),
};

/* ─── Scraper API ──────────────────────────────────────────────── */
export const scraperAPI = {
  linkedinStream: (body) =>
    fetch("/api/scraper/linkedin/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    }),
  linkedinStatus: () => api.get("/api/scraper/linkedin/status"),
  cikarang: () => api.post("/api/scraper/cikarang"),
};

/* ─── Export API ───────────────────────────────────────────────── */
export const exportAPI = {
  csv: (source) =>
    source ? `/api/export/csv?source=${source}` : "/api/export/csv",
  excel: (source) =>
    source ? `/api/export/excel?source=${source}` : "/api/export/excel",
};
