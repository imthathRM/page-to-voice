import { useState } from 'react';
import AuthProvider from './context/AuthProvider';
import useAuth from './context/useAuth';
import Navbar from './components/layout/Navbar';
import LoginScreen from './components/screens/LoginScreen';
import RegisterScreen from './components/screens/RegisterScreen';
import AccountScreen from './components/screens/AccountScreen';
import Alert from './components/common/Alert/Alert';
import { getBaseUrl } from './api/apiClient';
import './App.css';

const CURRENT_YEAR = new Date().getFullYear();

function AppContent() {
  const {
    user,
    isLoading,
    authError,
    successMessage,
    login,
    register,
    logout,
    clearError,
    clearSuccess,
  } = useAuth();

  const [activeScreen, setActiveScreen] = useState('login');
  const baseUrl = getBaseUrl();

  const handleNavigate = (screen) => {
    clearError();
    clearSuccess();
    setActiveScreen(screen);
  };

  const handleLoginSubmit = async (credentials) => {
    await login(credentials);
    setActiveScreen('account');
  };

  const handleRegisterSubmit = async (userData) => {
    await register(userData);
    setActiveScreen('account');
  };

  const handleLogoutSubmit = async () => {
    await logout();
    setActiveScreen('login');
  };

  return (
    <div className="app-wrapper">
      <Navbar
        activeScreen={activeScreen}
        onNavigate={handleNavigate}
        user={user}
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

        {activeScreen === 'login' && (
          <LoginScreen
            onLogin={handleLoginSubmit}
            onNavigateToRegister={() => handleNavigate('register')}
            isLoading={isLoading}
            authError={authError}
            onClearError={clearError}
          />
        )}

        {activeScreen === 'register' && (
          <RegisterScreen
            onRegister={handleRegisterSubmit}
            onNavigateToLogin={() => handleNavigate('login')}
            isLoading={isLoading}
            authError={authError}
            onClearError={clearError}
          />
        )}

        {activeScreen === 'account' && (
          <AccountScreen
            user={user}
            onLogout={handleLogoutSubmit}
            onNavigateToLogin={() => handleNavigate('login')}
            onNavigateToRegister={() => handleNavigate('register')}
            isLoading={isLoading}
          />
        )}
      </main>

      <footer className="app-footer">
        <div>
          <span>&copy; {CURRENT_YEAR} Page to Voice. All rights reserved.</span>
        </div>
        <div className="footer-contract-pill">
          API Endpoint Status: {baseUrl ? `Configured (${baseUrl})` : 'Contracts Pending Backend Confirmation'}
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
