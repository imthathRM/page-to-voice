/**
 * Page to Voice - Authentication Service
 *
 * Provides isolated authentication actions for login, registration,
 * profile retrieval, and logout using the centralized API client and
 * configurable contract mappings.
 */

import { apiClient, setAuthToken, clearAuthToken, getBaseUrl, ApiError } from './apiClient';
import {
  AUTH_ENDPOINTS,
  buildLoginPayload,
  buildRegisterPayload,
  normalizeAuthResponse,
} from './authContracts';

/**
 * Check whether mock authentication preview is permitted.
 * - Allowed ONLY in local development (import.meta.env.DEV === true && PROD === false).
 * - Requires explicit opt-in via VITE_ENABLE_AUTH_PREVIEW === 'true'.
 * - In production builds, this is strictly blocked (always false).
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
   * @param {Object} credentials - { email, password }
   * @returns {Promise<Object>} { user, token }
   */
  async login(credentials) {
    const payload = buildLoginPayload(credentials);
    const baseUrl = getBaseUrl();

    // When backend URL is not configured:
    if (!baseUrl) {
      if (isAuthPreviewAllowed()) {
        clearAuthToken();
        return {
          user: {
            id: null,
            name: credentials.email.split('@')[0] || 'Preview User',
            email: credentials.email,
            status: 'Development Preview (Not Authenticated)',
            role: 'Development Preview',
            isLocalPreview: true,
            sessionType: 'Local Development Simulation',
          },
          token: null,
          isLocalPreview: true,
        };
      }

      throw new ApiError(
        'Backend API URL is not configured (VITE_API_BASE_URL). Real authentication requires a configured backend service. To test UI states during local development, set VITE_ENABLE_AUTH_PREVIEW=true in your .env file.',
        0
      );
    }

    const response = await apiClient.post(AUTH_ENDPOINTS.LOGIN, payload);
    const normalized = normalizeAuthResponse(response);
    if (normalized?.token) {
      setAuthToken(normalized.token);
    }
    return normalized;
  },

  /**
   * Submit user registration request
   * @param {Object} userData - { name, email, password }
   * @returns {Promise<Object>} { user, token }
   */
  async register(userData) {
    const payload = buildRegisterPayload(userData);
    const baseUrl = getBaseUrl();

    if (!baseUrl) {
      if (isAuthPreviewAllowed()) {
        clearAuthToken();
        return {
          user: {
            id: null,
            name: userData.name,
            email: userData.email,
            status: 'Development Preview (Not Authenticated)',
            role: 'Development Preview',
            isLocalPreview: true,
            sessionType: 'Local Development Simulation',
          },
          token: null,
          isLocalPreview: true,
        };
      }

      throw new ApiError(
        'Backend API URL is not configured (VITE_API_BASE_URL). Real authentication requires a configured backend service. To test UI states during local development, set VITE_ENABLE_AUTH_PREVIEW=true in your .env file.',
        0
      );
    }

    const response = await apiClient.post(AUTH_ENDPOINTS.REGISTER, payload);
    const normalized = normalizeAuthResponse(response);
    if (normalized?.token) {
      setAuthToken(normalized.token);
    }
    return normalized;
  },

  /**
   * Fetch current authenticated user's account details
   * @returns {Promise<Object>} Account profile data
   */
  async getProfile() {
    const baseUrl = getBaseUrl();
    if (!baseUrl) {
      return null;
    }
    const response = await apiClient.get(AUTH_ENDPOINTS.PROFILE);
    return normalizeAuthResponse(response)?.user || response;
  },

  /**
   * Terminate current session
   */
  async logout() {
    const baseUrl = getBaseUrl();
    if (baseUrl) {
      try {
        await apiClient.post(AUTH_ENDPOINTS.LOGOUT, {});
      } catch {
        // Continue clearing local token even if remote logout fails
      }
    }
    clearAuthToken();
    return true;
  },
};

export default authService;
