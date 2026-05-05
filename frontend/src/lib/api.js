import axios from 'axios';
import { toast } from 'sonner';

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api';

export const api = axios.create({
  baseURL,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
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
