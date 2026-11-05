import React from 'react';
import './Header.css';

/**
 * Top Header Component for the Dashboard
 */
export function Header({
  activeView,
  user,
  onNavigate,
  onToggleMobileMenu,
  onLogoutClick,
}) {
  const getViewTitle = (view) => {
    switch (view) {
      case 'dashboard':
        return { title: 'Dashboard Overview', subtitle: 'Monitor your document processing and audiobook generation' };
      case 'upload':
        return { title: 'Upload & Process Document', subtitle: 'Upload PDF, DOCX, TXT, PPTX, EPUB, or RTF documents' };
      case 'results':
        return { title: 'Document Reader & Results', subtitle: 'Inspect extracted text, chapters, and metadata' };
      case 'library':
        return { title: 'My Document Library', subtitle: 'Manage and read all your processed documents' };
      case 'audiobooks':
        return { title: 'Audiobook Shelf', subtitle: 'Listen to generated audiobooks with interactive playback' };
      case 'history':
        return { title: 'Listening History', subtitle: 'Resume your audiobooks where you left off' };
      case 'favourites':
        return { title: 'Saved Favourites', subtitle: 'Quick access to your bookmarked documents' };
      case 'settings':
        return { title: 'Account & Settings', subtitle: 'Manage your profile and playback preferences' };
      case 'help':
        return { title: 'Help & Documentation', subtitle: 'Format guides, multilingual support, and FAQs' };
      default:
        return { title: 'Page to Voice', subtitle: 'Intelligent Audiobook Generation Platform' };
    }
  };

  const { title, subtitle } = getViewTitle(activeView);
  const userInitials = (user?.username || user?.name || user?.email || 'U').slice(0, 2).toUpperCase();

  return (
    <header className="dashboard-header">
      <div className="header-left">
        <button
          type="button"
          className="header-mobile-toggle"
          onClick={onToggleMobileMenu}
          aria-label="Toggle navigation menu"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        <div className="header-titles">
          <div className="header-breadcrumbs">
            <span className="breadcrumb-root" onClick={() => onNavigate('dashboard')}>Platform</span>
            <span className="breadcrumb-separator">/</span>
            <span className="breadcrumb-current">{title}</span>
          </div>
          <h1 className="header-page-title">{title}</h1>
          <p className="header-page-subtitle">{subtitle}</p>
        </div>
      </div>

      <div className="header-actions">
        {activeView !== 'upload' && (
          <button
            type="button"
            className="header-quick-upload-btn"
            onClick={() => onNavigate('upload')}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <span>Upload Document</span>
          </button>
        )}

        <div
          className="header-user-profile-badge"
          onClick={() => onNavigate('settings')}
          title="Go to Account Settings"
          role="button"
          tabIndex={0}
        >
          <div className="header-user-avatar">{userInitials}</div>
          <div className="header-user-text">
            <span className="header-user-name">{user?.username || user?.name || 'User'}</span>
            <span className="header-user-role">{user?.role || 'Member'}</span>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
