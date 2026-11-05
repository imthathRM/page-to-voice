import { useState } from 'react';
import { AuthContext } from './AuthContext';
import authService from '../api/authService';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [authError, setAuthError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

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
    isLoading,
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
