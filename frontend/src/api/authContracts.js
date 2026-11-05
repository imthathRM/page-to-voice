/**
 * Page to Voice - Authentication API Contracts & Configuration
 *
 * Mapped to FastAPI Backend:
 * - POST /auth/login -> { access_token, token_type, expires_in }
 * - POST /auth/register -> UserResponse { id, email, username, role, is_active, created_at }
 * - GET /users/me -> UserResponse { id, email, username, role, is_active, created_at }
 * - GET /health -> { status, database, service }
 */

export const AUTH_ENDPOINTS = {
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  PROFILE: '/users/me',
  HEALTH: '/health',
  LOGOUT: '/auth/logout',
};

/**
 * Adapter helper to build login payload supporting dual identifier (email or username)
 */
export const buildLoginPayload = ({ email, username, password }) => {
  const identifier = (email || username || '').trim();
  if (identifier.includes('@')) {
    return {
      email: identifier,
      password,
    };
  }
  return {
    username: identifier,
    password,
  };
};

/**
 * Adapter helper to build register payload matching FastAPI UserCreate schema:
 * { email: EmailStr, username: str (3-50 chars), password: str }
 */
export const buildRegisterPayload = ({ username, name, email, password }) => {
  // Use provided username or derive clean username from name or email prefix
  let candidateUsername = (username || name || email.split('@')[0])
    .trim()
    .replace(/[^a-zA-Z0-9_-]/g, '_')
    .slice(0, 50);

  if (candidateUsername.length < 3) {
    candidateUsername = `${candidateUsername}_user`.slice(0, 50);
  }

  return {
    username: candidateUsername,
    email: email.trim(),
    password,
  };
};

/**
 * Adapter helper to normalize user profile from backend UserResponse
 */
export const normalizeUser = (data) => {
  if (!data || typeof data !== 'object') {
    return null;
  }

  const roleValue = typeof data.role === 'object' && data.role !== null
    ? data.role.value || String(data.role)
    : String(data.role || 'user');

  return {
    id: data.id ?? null,
    name: data.username || data.name || data.email?.split('@')[0] || 'User',
    username: data.username || '',
    email: data.email || '',
    role: roleValue,
    status: data.is_active ? 'Active' : 'Inactive',
    isActive: Boolean(data.is_active),
    createdAt: data.created_at || null,
  };
};
