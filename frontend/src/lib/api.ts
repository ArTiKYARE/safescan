import axios, { AxiosInstance, AxiosError } from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

export const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor — add auth token
api.interceptors.request.use(
  (config) => {
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("access_token")
        : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor — handle 401 with token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (refreshToken) {
          const response = await api.post("/auth/refresh", {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data;
          localStorage.setItem("access_token", access_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  },
);

// ==================== Auth API ====================

export const authApi = {
  login: (data: { email: string; password: string; mfa_token?: string }) =>
    api.post("/auth/login", data),

  register: (data: {
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
  }) => api.post("/auth/register", data),

  refresh: (refresh_token: string) =>
    api.post("/auth/refresh", { refresh_token }),

  logout: () => api.post("/auth/logout"),

  verifyEmail: (token: string) =>
    api.get("/auth/verify-email", { params: { token } }),

  getMe: () => api.get("/users/me"),

  updateMe: (data: { first_name?: string; last_name?: string }) =>
    api.put("/users/me", data),

  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post("/users/change-password", data),

  setupMfa: () => api.post("/auth/mfa/setup"),

  verifyMfa: (totp_code: string) => api.post("/auth/mfa/verify", { totp_code }),

  disableMfa: (totp_code: string) =>
    api.post("/auth/mfa/disable", { totp_code }),
};

// ==================== Domains API ====================

export const domainsApi = {
  list: () => api.get("/domains/"),

  get: (domainId: string) => api.get(`/domains/${domainId}`),

  create: (data: { domain: string; verification_method: string }) =>
    api.post("/domains/", data),

  delete: (domainId: string) => api.delete(`/domains/${domainId}`),

  getVerificationStatus: (domainId: string) =>
    api.get(`/domains/${domainId}/verification-status`),

  verify: (domainId: string) => api.post(`/domains/${domainId}/verify`),

  checkDns: (domain: string) => api.get(`/verification/check-dns/${domain}`),

  checkFile: (domain: string) => api.get(`/verification/check-file/${domain}`),
};

// ==================== Scans API ====================

export const scansApi = {
  list: (params?: { status?: string; scan_type?: string }) =>
    api.get("/scans/", { params }),

  get: (scanId: string) => api.get(`/scans/${scanId}`),

  create: (data: {
    domain_id: string;
    scan_type: string;
    consent_acknowledged: boolean;
  }) => api.post("/scans/", data),

  getStatus: (scanId: string) => api.get(`/scans/${scanId}/status`),

  cancel: (scanId: string) => api.post(`/scans/${scanId}/cancel`),

  getLogs: (scanId: string, offset?: number, limit?: number) =>
    api.get(`/scans/${scanId}/logs`, { params: { offset, limit } }),
};

// ==================== Vulnerabilities API ====================

export const vulnsApi = {
  list: (params?: {
    scan_id?: string;
    severity?: string;
    module?: string;
    page?: number;
    page_size?: number;
  }) => api.get("/vulnerabilities/", { params }),

  get: (vulnId: string) => api.get(`/vulnerabilities/${vulnId}`),

  summary: () => api.get("/vulnerabilities/summary/overall"),

  markFalsePositive: (vulnId: string) =>
    api.post(`/vulnerabilities/${vulnId}/mark-false-positive`),

  resolve: (vulnId: string, note: string) =>
    api.post(`/vulnerabilities/${vulnId}/resolve`, null, { params: { note } }),
};

// ==================== Reports API ====================

export const reportsApi = {
  getJson: (scanId: string) => api.get(`/reports/${scanId}/json`),

  getPdf: (scanId: string) =>
    api.get(`/reports/${scanId}/pdf`, { responseType: "blob" }),

  getHtml: (scanId: string) => api.get(`/reports/${scanId}/html`),
};

// ==================== API Keys API ====================

export const apiKeysApi = {
  list: () => api.get("/api-keys/"),

  create: (data: { name: string; scopes: string; expires_in_days?: number }) =>
    api.post("/api-keys/", data),

  revoke: (keyId: string) => api.delete(`/api-keys/${keyId}`),
};

// ==================== Settings API ====================

export const settingsApi = {
  get: () => api.get("/settings/"),

  update: (data: any) => api.put("/settings/", data),
};

export default api;
