import { useState } from 'react';
import AuthProvider from './context/AuthProvider';
import useAuth from './context/useAuth';
import Navbar from './components/layout/Navbar';
import DashboardLayout from './components/layout/DashboardLayout';
import LoginScreen from './components/screens/LoginScreen';
import RegisterScreen from './components/screens/RegisterScreen';
import LoadingSpinner from './components/common/LoadingSpinner/LoadingSpinner';
import Alert from './components/common/Alert/Alert';
import { getBaseUrl } from './api/apiClient';
import './App.css';

const CURRENT_YEAR = new Date().getFullYear();

function AppContent() {
  const {
    user,
    isLoading,
    isInitializing,
    authError,
    successMessage,
    login,
    register,
    logout,
    clearError,
    clearSuccess,
  } = useAuth();

  const [authScreen, setAuthScreen] = useState('login'); // 'login' | 'register'
  const baseUrl = getBaseUrl() || 'http://localhost:8000';

  const handleNavigateAuth = (screen) => {
    clearError();
    clearSuccess();
    setAuthScreen(screen);
  };

  const handleLoginSubmit = async (credentials) => {
    await login(credentials);
  };

  const handleRegisterSubmit = async (userData) => {
    await register(userData);
  };

  const handleLogoutSubmit = async () => {
    await logout();
    setAuthScreen('login');
  };

  // 1. Session Initialization Gate: Avoids login screen flash on refresh
  if (isInitializing) {
    return (
      <div style={{
        minHeight: '100vh',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg)',
        gap: '16px',
      }}>
        <div style={{
          width: '48px',
          height: '48px',
          borderRadius: '12px',
          background: 'var(--accent)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
        }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M12 2v20M17 5v14M7 8v8M22 10v4M2 10v4" />
          </svg>
        </div>
        <LoadingSpinner size="lg" text="Restoring secure session..." />
      </div>
    );
  }

  // 2. Authenticated Experience: Render Full Dashboard Layout
  if (user) {
    return (
      <DashboardLayout
        user={user}
        onLogout={handleLogoutSubmit}
      />
    );
  }

  // 3. Unauthenticated Experience: Sign In / Create Account
  return (
    <div className="app-wrapper">
      <Navbar
        activeScreen={authScreen}
        onNavigate={handleNavigateAuth}
        user={null}
      />

      <main className="main-content">
        {successMessage && (
          <div className="notification-container">
            <Alert
              type="success"
              title="Success"
              onClose={clearSuccess}
            >
              {successMessage}
            </Alert>
          </div>
        )}

        {authScreen === 'login' && (
          <LoginScreen
            onLogin={handleLoginSubmit}
            onNavigateToRegister={() => handleNavigateAuth('register')}
            isLoading={isLoading}
            authError={authError}
            onClearError={clearError}
          />
        )}

        {authScreen === 'register' && (
          <RegisterScreen
            onRegister={handleRegisterSubmit}
            onNavigateToLogin={() => handleNavigateAuth('login')}
            isLoading={isLoading}
            authError={authError}
            onClearError={clearError}
          />
        )}
      </main>

      <footer className="app-footer">
        <div>
          <span>&copy; {CURRENT_YEAR} Page to Voice. All rights reserved.</span>
        </div>
        <div className="footer-contract-pill">
          Backend API: Connected ({baseUrl})
        </div>
      </footer>
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
