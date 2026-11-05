/**
 * Page to Voice - Authentication Service
 *
 * Implements authentication flows integrated with FastAPI backend endpoints:
 * - /auth/login
 * - /auth/register
 * - /users/me
 * - /health
 */

import {
  apiClient,
  setAuthToken,
  clearAuthToken,
  getAuthToken,
  getBaseUrl,
  ApiError,
} from './apiClient';
import {
  AUTH_ENDPOINTS,
  buildLoginPayload,
  buildRegisterPayload,
  normalizeUser,
} from './authContracts';

/**
 * Check whether mock authentication preview is permitted.
 */
export const isAuthPreviewAllowed = () => {
  if (import.meta.env.PROD || !import.meta.env.DEV) {
    return false;
  }
  return import.meta.env.VITE_ENABLE_AUTH_PREVIEW === 'true';
};

export const authService = {
  /**
   * Submit user login request
   * @param {Object} credentials - { email, username, password }
   * @returns {Promise<Object>} { user, token }
   */
  async login(credentials) {
    const payload = buildLoginPayload(credentials);
    const baseUrl = getBaseUrl();

    // If base URL not configured and mock preview enabled
    if (!baseUrl && isAuthPreviewAllowed()) {
      clearAuthToken();
      return {
        user: {
          id: null,
          name: credentials.username || (credentials.email ? credentials.email.split('@')[0] : 'Preview User'),
          username: credentials.username || 'preview_user',
          email: credentials.email || 'preview@example.com',
          status: 'Development Preview',
          role: 'user',
          isLocalPreview: true,
        },
        token: null,
      };
    }

    // Call FastAPI /auth/login
    const tokenResponse = await apiClient.post(AUTH_ENDPOINTS.LOGIN, payload);
    const token = tokenResponse.access_token || tokenResponse.token;

    if (!token) {
      throw new ApiError('No access token received from authentication server.', 500);
    }

    // Save token in memory and localStorage
    setAuthToken(token);

    // Retrieve active authenticated user profile from /users/me
    const userProfile = await apiClient.get(AUTH_ENDPOINTS.PROFILE);
    const normalizedUser = normalizeUser(userProfile);

    return {
      token,
      user: normalizedUser,
    };
  },

  /**
   * Submit user registration request
   * @param {Object} userData - { username, name, email, password }
   * @returns {Promise<Object>} { user, token }
   */
  async register(userData) {
    const payload = buildRegisterPayload(userData);
    const baseUrl = getBaseUrl();

    if (!baseUrl && isAuthPreviewAllowed()) {
      clearAuthToken();
      return {
        user: {
          id: null,
          name: userData.username || userData.name,
          username: payload.username,
          email: userData.email,
          status: 'Development Preview',
          role: 'user',
          isLocalPreview: true,
        },
        token: null,
      };
    }

    // Call FastAPI /auth/register
    await apiClient.post(AUTH_ENDPOINTS.REGISTER, payload);

    // Automatically authenticate with created credentials
    return await this.login({
      email: userData.email,
      password: userData.password,
    });
  },

  /**
   * Fetch current authenticated user's account details from /users/me
   * @returns {Promise<Object|null>} Account profile data
   */
  async getProfile() {
    const token = getAuthToken();
    if (!token) {
      return null;
    }

    try {
      const response = await apiClient.get(AUTH_ENDPOINTS.PROFILE);
      return normalizeUser(response);
    } catch (err) {
      // If unauthorized/expired token, clear and return null
      if (err.status === 401 || err.status === 403) {
        clearAuthToken();
        return null;
      }
      throw err;
    }
  },

  /**
   * Check backend server and database health
   */
  async checkHealth() {
    return await apiClient.get(AUTH_ENDPOINTS.HEALTH);
  },

  /**
   * Terminate current session
   */
  async logout() {
    clearAuthToken();
    return true;
  },
};

export default authService;
