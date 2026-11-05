import React, { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import AudioPlayerBar from '../dashboard/AudioPlayerBar';
import DashboardOverview from '../dashboard/DashboardOverview';
import UploadScreen from '../dashboard/UploadScreen';
import DocumentResultScreen from '../dashboard/DocumentResultScreen';
import LibraryScreen from '../dashboard/LibraryScreen';
import AudiobooksScreen from '../dashboard/AudiobooksScreen';
import ListeningHistoryScreen from '../dashboard/ListeningHistoryScreen';
import FavouritesScreen from '../dashboard/FavouritesScreen';
import SettingsScreen from '../dashboard/SettingsScreen';
import HelpSupportScreen from '../dashboard/HelpSupportScreen';
import Modal from '../common/Modal/Modal';
import Button from '../common/Button/Button';
import documentService from '../../api/documentService';
import './DashboardLayout.css';

/**
 * Main Authenticated User Dashboard Layout
 */
export function DashboardLayout({ user, onLogout }) {
  // Restore last visited screen from sessionStorage or default to 'dashboard'
  const [activeView, setActiveView] = useState(() => {
    return sessionStorage.getItem('p2v_active_view') || 'dashboard';
  });

  const [isOpenOnMobile, setIsOpenOnMobile] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [currentDocument, setCurrentDocument] = useState(null);
  const [currentTrack, setCurrentTrack] = useState(null);
  const [documentCount, setDocumentCount] = useState(0);

  // Sync active view with sessionStorage so refreshing browser keeps current screen
  useEffect(() => {
    sessionStorage.setItem('p2v_active_view', activeView);
  }, [activeView]);

  // Fetch document count for sidebar badge
  const refreshStats = async () => {
    try {
      const stats = await documentService.getDashboardStats();
      if (stats?.total_documents !== undefined) {
        setDocumentCount(stats.total_documents);
      }
    } catch {
      // Ignore count fetch errors
    }
  };

  useEffect(() => {
    refreshStats();
  }, [activeView]);

  const handleNavigate = (viewId) => {
    if (viewId === 'logout') {
      setShowLogoutModal(true);
      return;
    }
    setActiveView(viewId);
    setIsOpenOnMobile(false);
  };

  const handleOpenDocument = async (documentId) => {
    try {
      const doc = await documentService.getDocument(documentId);
      setCurrentDocument(doc);
      setActiveView('results');
    } catch (err) {
      alert(`Could not load document: ${err.message || 'Unknown error'}`);
    }
  };

  const handleUploadSuccess = (uploadedDoc) => {
    setCurrentDocument(uploadedDoc);
    setActiveView('results');
    refreshStats();
  };

  const handlePlayDocument = (doc) => {
    setCurrentTrack({
      title: doc.title,
      chapterTitle: 'Chapter 1: Audio Playback',
      docType: (doc.file_format || doc.file_type || 'PDF').toUpperCase(),
      audioUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
    });
  };

  const handlePlaySample = () => {
    setCurrentTrack({
      title: 'Page to Voice Audiobook Sample',
      chapterTitle: 'Chapter 1: Platform Overview',
      docType: 'AUDIOBOOK',
      audioUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
    });
  };

  const handleConfirmLogout = () => {
    sessionStorage.removeItem('p2v_active_view');
    setShowLogoutModal(false);
    onLogout();
  };

  return (
    <div className="dashboard-layout">
      {/* Mobile Backdrop */}
      {isOpenOnMobile && (
        <div
          className="dashboard-backdrop"
          onClick={() => setIsOpenOnMobile(false)}
        />
      )}

      {/* Responsive Sidebar */}
      <Sidebar
        activeView={activeView}
        onNavigate={handleNavigate}
        onLogoutClick={() => setShowLogoutModal(true)}
        user={user}
        isOpenOnMobile={isOpenOnMobile}
        onCloseMobile={() => setIsOpenOnMobile(false)}
        documentCount={documentCount}
      />

      {/* Main Content Area */}
      <div className="dashboard-content-wrapper">
        <Header
          activeView={activeView}
          user={user}
          onNavigate={handleNavigate}
          onToggleMobileMenu={() => setIsOpenOnMobile(!isOpenOnMobile)}
          onLogoutClick={() => setShowLogoutModal(true)}
        />

        <main className="dashboard-main-view">
          {activeView === 'dashboard' && (
            <DashboardOverview
              user={user}
              onNavigate={handleNavigate}
              onOpenDocument={handleOpenDocument}
            />
          )}

          {activeView === 'upload' && (
            <UploadScreen
              onUploadSuccess={handleUploadSuccess}
              onNavigateToLibrary={() => handleNavigate('library')}
            />
          )}

          {activeView === 'results' && (
            <DocumentResultScreen
              documentData={currentDocument}
              onNavigateToLibrary={() => handleNavigate('library')}
              onPlayChapter={(track) => setCurrentTrack(track)}
            />
          )}

          {activeView === 'library' && (
            <LibraryScreen
              onNavigateToUpload={() => handleNavigate('upload')}
              onOpenDocument={handleOpenDocument}
              onPlayDocument={handlePlayDocument}
            />
          )}

          {activeView === 'audiobooks' && (
            <AudiobooksScreen
              onPlayTrack={(track) => setCurrentTrack(track)}
              onNavigateToUpload={() => handleNavigate('upload')}
            />
          )}

          {activeView === 'history' && (
            <ListeningHistoryScreen
              onNavigateToLibrary={() => handleNavigate('library')}
            />
          )}

          {activeView === 'favourites' && (
            <FavouritesScreen
              onNavigateToLibrary={() => handleNavigate('library')}
            />
          )}

          {activeView === 'settings' && (
            <SettingsScreen
              user={user}
              onLogoutClick={() => setShowLogoutModal(true)}
            />
          )}

          {activeView === 'help' && (
            <HelpSupportScreen />
          )}
        </main>
      </div>

      {/* Persistent Audio Player Bar */}
      <AudioPlayerBar
        currentTrack={currentTrack}
        onPlaySample={handlePlaySample}
        onCloseTrack={() => setCurrentTrack(null)}
      />

      {/* Logout Confirmation Modal */}
      {showLogoutModal && (
        <Modal
          isOpen={showLogoutModal}
          onClose={() => setShowLogoutModal(false)}
          title="Sign Out"
          footer={
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <Button
                variant="outline"
                onClick={() => setShowLogoutModal(false)}
              >
                Stay Signed In
              </Button>
              <Button
                variant="danger"
                onClick={handleConfirmLogout}
              >
                Sign Out
              </Button>
            </div>
          }
        >
          <p style={{ margin: 0, fontSize: '14px', lineHeight: 1.5 }}>
            Are you sure you want to sign out of <strong>Page to Voice</strong>?
            Your active session will be ended.
          </p>
        </Modal>
      )}
    </div>
  );
}

export default DashboardLayout;
