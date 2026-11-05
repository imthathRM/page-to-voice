import axios from 'axios';
import { getAuthToken, getBaseUrl } from './apiClient';

const baseUrl = getBaseUrl() || '';

export const axiosInstance = axios.create({
  baseURL: baseUrl,
  headers: {
    Accept: 'application/json',
  },
});

// Request interceptor to automatically attach JWT token
axiosInstance.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to format error messages
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = 'An unexpected error occurred.';
    if (error.response?.data) {
      const data = error.response.data;
      if (Array.isArray(data.detail)) {
        message = data.detail.map((d) => d.msg || JSON.stringify(d)).join('. ');
      } else if (typeof data.detail === 'string') {
        message = data.detail;
      } else if (data.message) {
        message = data.message;
      }
    } else if (error.message) {
      message = error.message;
    }
    const err = new Error(message);
    err.status = error.response?.status || 0;
    err.data = error.response?.data || null;
    return Promise.reject(err);
  }
);

export default axiosInstance;

