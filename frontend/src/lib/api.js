import axios from 'axios';
import { toast } from 'sonner';

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api';

const TOKEN_KEY = 'seolab.token';

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY) || null,
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

export const api = axios.create({
  baseURL,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const t = tokenStore.get();
  if (t) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${t}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => {
    const data = response?.data;
    if (data && typeof data === 'object' && 'success' in data) {
      if (data.success === false) {
        const msg = data.error || 'Request failed';
        toast.error(msg);
        return Promise.reject(new Error(msg));
      }
      return { ...response, data: data.data };
    }
    return response;
  },
  (error) => {
    const status = error.response?.status;
    const detail = error.response?.data?.detail || error.response?.data?.error || error.message;

    if (status === 401) {
      // Token expired or missing — drop it and bounce to /login (unless we're
      // already there or the request was the login itself).
      tokenStore.clear();
      const path = window.location.pathname;
      if (path !== '/login' && !error.config?.url?.endsWith('/auth/login')) {
        window.location.href = '/login';
        return Promise.reject(error);
      }
    }

    if (status && status !== 401) {
      toast.error(typeof detail === 'string' ? detail : 'Request failed');
    }
    return Promise.reject(error);
  }
);

export const get = (url, params) => api.get(url, { params }).then((r) => r.data);
export const post = (url, body) => api.post(url, body).then((r) => r.data);
export const patch = (url, body) => api.patch(url, body).then((r) => r.data);
export const del = (url) => api.delete(url).then((r) => r.data);
