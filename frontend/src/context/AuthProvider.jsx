import { useState, useEffect } from 'react';
import { AuthContext } from './AuthContext';
import authService from '../api/authService';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [authError, setAuthError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Restore authenticated session on initial load
  useEffect(() => {
    let isMounted = true;
    const restoreSession = async () => {
      try {
        const profile = await authService.getProfile();
        if (isMounted && profile) {
          setUser(profile);
        }
      } catch {
        // Session restoration failed silently (e.g. expired token)
      } finally {
        if (isMounted) {
          setIsInitializing(false);
        }
      }
    };

    restoreSession();
    return () => {
      isMounted = false;
    };
  }, []);

  const clearError = () => {
    setAuthError(null);
  };

  const clearSuccess = () => {
    setSuccessMessage(null);
  };

  const login = async (credentials) => {
    setIsLoading(true);
    setAuthError(null);
    setSuccessMessage(null);
    try {
      const result = await authService.login(credentials);
      setUser(result.user);
      return result;
    } catch (err) {
      const message = err.message || 'Failed to sign in. Please check your credentials.';
      setAuthError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData) => {
    setIsLoading(true);
    setAuthError(null);
    setSuccessMessage(null);
    try {
      const result = await authService.register(userData);
      setUser(result.user);
      setSuccessMessage('Account created successfully! Welcome to Page to Voice.');
      return result;
    } catch (err) {
      const message = err.message || 'Failed to create account. Please try again.';
      setAuthError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await authService.logout();
      setUser(null);
      setSuccessMessage('You have been signed out successfully.');
    } finally {
      setIsLoading(false);
    }
  };

  const value = {
    user,
    isLoading: isLoading || isInitializing,
    isInitializing,
    authError,
    successMessage,
    login,
    register,
    logout,
    clearError,
    clearSuccess,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export default AuthProvider;
