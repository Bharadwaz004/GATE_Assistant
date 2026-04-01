/**
 * Axios API client with token interceptor and error handling.
 */
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
});

// ── Request interceptor: attach JWT ─────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: handle 401 ────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_id');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ── Auth ────────────────────────────────────────────────────
export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => api.post('/auth/login', data),
};

// ── User ────────────────────────────────────────────────────
export const userAPI = {
  onboarding: (data) => api.post('/user/onboarding', data),
  getProfile: () => api.get('/user/profile'),
};

// ── Study Plan ──────────────────────────────────────────────
export const planAPI = {
  generate: (data) => api.post('/plan/generate', data),
  getDaily: (date) => api.get('/plan/daily', { params: date ? { target_date: date } : {} }),
  updateTask: (data) => api.post('/plan/task', data),
  getStreak: () => api.get('/plan/streak'),
  getProgress: () => api.get('/plan/progress'),
};

// ── Matching ────────────────────────────────────────────────
export const matchAPI = {
  getMatches: (topN = 10) => api.get('/match', { params: { top_n: topN } }),
};

export default api;
