import { useState } from 'react';
import AuthProvider from './context/AuthProvider';
import useAuth from './context/useAuth';
import Navbar from './components/layout/Navbar';
import LoginScreen from './components/screens/LoginScreen';
import RegisterScreen from './components/screens/RegisterScreen';
import AccountScreen from './components/screens/AccountScreen';
import DashboardScreen from './components/screens/DashboardScreen';
import UploadScreen from './components/screens/UploadScreen';
import DocumentDetailScreen from './components/screens/DocumentDetailScreen';
import AudioPlayer from './components/audio/AudioPlayer';
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

  const [navScreen, setNavScreen] = useState(null);
  const [navParams, setNavParams] = useState({});
  const [activeAudio, setActiveAudio] = useState(null);

  const baseUrl = getBaseUrl() || 'http://localhost:8000';

  // Determine active screen based on explicit navigation or user authentication status
  const activeScreen = navScreen ?? (user ? 'dashboard' : 'login');

  const handleNavigate = (screen, params = {}) => {
    clearError();
    clearSuccess();
    setNavScreen(screen);
    setNavParams(params);
  };

  const handleLoginSubmit = async (credentials) => {
    await login(credentials);
    setNavScreen('dashboard');
  };

  const handleRegisterSubmit = async (userData) => {
    await register(userData);
    setNavScreen('dashboard');
  };

  const handleLogoutSubmit = async () => {
    await logout();
    setActiveAudio(null);
    setNavScreen('login');
  };

  const handlePlayAudio = (audioData) => {
    setActiveAudio(audioData);
  };

  const handleNextTrack = () => {
    if (!activeAudio || !activeAudio.playlist) return;
    const nextIdx = activeAudio.currentIndex + 1;
    if (nextIdx < activeAudio.playlist.length) {
      const nextChap = activeAudio.playlist[nextIdx];
      if (nextChap.audio_file_url) {
        setActiveAudio({
          title: nextChap.title,
          chapter_number: nextChap.chapter_number,
          audio_url: nextChap.audio_file_url,
          duration_seconds: nextChap.duration_seconds,
          documentTitle: activeAudio.documentTitle,
          text: nextChap.processed_text || nextChap.original_text,
          playlist: activeAudio.playlist,
          currentIndex: nextIdx,
        });
      }
    }
  };

  const handlePrevTrack = () => {
    if (!activeAudio || !activeAudio.playlist) return;
    const prevIdx = activeAudio.currentIndex - 1;
    if (prevIdx >= 0) {
      const prevChap = activeAudio.playlist[prevIdx];
      if (prevChap.audio_file_url) {
        setActiveAudio({
          title: prevChap.title,
          chapter_number: prevChap.chapter_number,
          audio_url: prevChap.audio_file_url,
          duration_seconds: prevChap.duration_seconds,
          documentTitle: activeAudio.documentTitle,
          text: prevChap.processed_text || prevChap.original_text,
          playlist: activeAudio.playlist,
          currentIndex: prevIdx,
        });
      }
    }
  };

  const hasNextChapter = Boolean(
    activeAudio?.playlist &&
    activeAudio.currentIndex < activeAudio.playlist.length - 1 &&
    activeAudio.playlist[activeAudio.currentIndex + 1]?.audio_file_url
  );

  const hasPrevChapter = Boolean(
    activeAudio?.playlist &&
    activeAudio.currentIndex > 0 &&
    activeAudio.playlist[activeAudio.currentIndex - 1]?.audio_file_url
  );


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

        {/* Public Screens */}
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

        {/* Authenticated Screens */}
        {activeScreen === 'dashboard' && (
          <DashboardScreen
            user={user}
            onNavigate={handleNavigate}
          />
        )}

        {activeScreen === 'upload' && (
          <UploadScreen
            onNavigate={handleNavigate}
            onUploadSuccess={(doc) => handleNavigate('document-detail', { documentId: doc.id })}
          />
        )}

        {activeScreen === 'document-detail' && (
          <DocumentDetailScreen
            documentId={navParams.documentId}
            onNavigate={handleNavigate}
            onPlayAudio={handlePlayAudio}
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

      {/* Global Audio Player Bar */}
      {activeAudio && (
        <AudioPlayer
          audio={activeAudio}
          onClose={() => setActiveAudio(null)}
          onNextTrack={handleNextTrack}
          onPrevTrack={handlePrevTrack}
          hasNext={hasNextChapter}
          hasPrev={hasPrevChapter}
        />
      )}

      <footer className="app-footer">
        <div>
          <span>&copy; {CURRENT_YEAR} Page to Voice. All rights reserved.</span>
        </div>
        <div className="footer-contract-pill">
          Azure AI Speech & Gemini TTS: Connected ({baseUrl})
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
