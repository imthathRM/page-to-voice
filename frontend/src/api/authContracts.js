/**
 * Page to Voice - Authentication API Contracts & Configuration
 *
 * NOTE: Official backend API contracts are pending confirmation from the backend teammate.
 * To avoid inventing backend contracts (Instruction 5 & 6), these endpoint paths, payload
 * formats, and response mappings are isolated here in a configurable structure.
 *
 * MISSING BACKEND CONTRACT INFORMATION REQUIRED:
 * 1. Base URL prefix (e.g. "/api", "/api/v1", or root "/")
 * 2. Login Endpoint:
 *    - Route path and HTTP method (e.g., POST /auth/login vs POST /api/v1/auth/login)
 *    - Request payload keys: { email, password } vs { username, password } vs { identifier, password }
 *    - Response schema: { token, user: { id, email, name, status } } vs { accessToken, refreshToken } vs Set-Cookie (HttpOnly)
 * 3. Registration Endpoint:
 *    - Route path and HTTP method (e.g., POST /auth/register vs POST /auth/signup)
 *    - Required/optional fields: { name, email, password, confirmPassword } or separate { firstName, lastName }
 *    - Response schema: immediate token response vs verification email dispatch status
 * 4. Authentication Strategy:
 *    - Bearer JWT token in Authorization header vs Session Cookies / CSRF tokens
 * 5. Account Details & Status Endpoint:
 *    - Route path and HTTP method for fetching current user profile (e.g., GET /auth/me or GET /user/profile)
 *    - Exact status enum/strings (e.g., "active", "verified", "pending_verification", "suspended")
 * 6. Error Response Schema:
 *    - Standardized field for error messages: e.g., { message: string } vs { error: string } vs { errors: string[] }
 */

export const AUTH_ENDPOINTS = {
  // Configurable route paths (placeholders pending backend confirmation)
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  PROFILE: '/auth/me',
  LOGOUT: '/auth/logout',
};

/**
 * Adapter helpers to build request payloads according to confirmed contracts
 */
export const buildLoginPayload = ({ email, password }) => ({
  email,
  password,
});

export const buildRegisterPayload = ({ name, email, password }) => ({
  name,
  email,
  password,
});

/**
 * Adapter helper to normalize account/user data from backend response
 */
export const normalizeAuthResponse = (data) => {
  if (!data || typeof data !== 'object') {
    return null;
  }
  return {
    token: data.token || data.accessToken || null,
    user: data.user || {
      id: data.id || null,
      name: data.name || data.username || '',
      email: data.email || '',
      status: data.status || 'Active (Unverified Contract)',
    },
  };
};
