/**
 * Page to Voice - Centralized Frontend API Client
 *
 * Provides a standardized HTTP client wrapping native fetch with:
 * - Environment-based backend URL configuration (VITE_API_BASE_URL)
 * - Standard headers and authentication header injection
 * - Unified response parsing and consistent error formatting
 * - Safe isolation to connect with backend endpoints once confirmed
 */

// Retrieve base URL from environment or fallback to empty string (relative to host)
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');

// In-memory token storage (can be swapped or connected to cookies/storage once backend strategy is confirmed)
let authToken = null;

export const setAuthToken = (token) => {
  authToken = token;
};

export const getAuthToken = () => {
  return authToken;
};

export const clearAuthToken = () => {
  authToken = null;
};

export const getBaseUrl = () => {
  return API_BASE_URL;
};

/**
 * Custom API Error class for consistent error handling across the application
 */
export class ApiError extends Error {
  constructor(message, status = 0, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Execute an HTTP request with standardized options, parsing, and error formatting
 *
 * @param {string} endpoint - API path (e.g., '/auth/login')
 * @param {RequestInit} [options={}] - Standard fetch RequestInit options
 * @returns {Promise<any>} Parsed response data
 */
export async function request(endpoint, options = {}) {
  const url = endpoint.startsWith('http://') || endpoint.startsWith('https://')
    ? endpoint
    : `${API_BASE_URL}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;

  const headers = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    ...(options.headers || {}),
  };

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);

    // Parse response body safely
    let responseData = null;
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      try {
        responseData = await response.json();
      } catch {
        responseData = null;
      }
    } else {
      try {
        responseData = await response.text();
      } catch {
        responseData = null;
      }
    }

    if (!response.ok) {
      // Extract error message from backend payload if available, without assuming a fixed schema
      let errorMessage = `Request failed with status ${response.status}`;
      if (responseData && typeof responseData === 'object') {
        errorMessage = responseData.message || responseData.error || responseData.detail || errorMessage;
      } else if (typeof responseData === 'string' && responseData.trim().length > 0) {
        errorMessage = responseData;
      }

      throw new ApiError(errorMessage, response.status, responseData);
    }

    return responseData;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    // Network or client-side fetch error (e.g., server offline, CORS, DNS)
    const isNetworkError = error.name === 'TypeError' || error.message.includes('fetch');
    const message = isNetworkError
      ? 'Unable to connect to the backend server. Please verify the server is running and VITE_API_BASE_URL is configured.'
      : error.message || 'An unexpected error occurred during the request.';

    throw new ApiError(message, 0, null);
  }
}

export const apiClient = {
  get: (endpoint, options = {}) => request(endpoint, { ...options, method: 'GET' }),
  post: (endpoint, data, options = {}) =>
    request(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),
  put: (endpoint, data, options = {}) =>
    request(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),
  delete: (endpoint, options = {}) => request(endpoint, { ...options, method: 'DELETE' }),
};

export default apiClient;
