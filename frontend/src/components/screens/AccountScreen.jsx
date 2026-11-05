import { useState } from 'react';
import Button from '../common/Button/Button';
import Modal from '../common/Modal/Modal';
import Alert from '../common/Alert/Alert';
import { getBaseUrl } from '../../api/apiClient';
import './Screens.css';

/**
 * Page to Voice - Account State UI Component
 *
 * @param {Object} props
 * @param {Object|null} props.user - Active authenticated user object
 * @param {Function} props.onLogout - Logout handler callback
 * @param {Function} props.onNavigateToLogin - Navigation callback
 * @param {Function} props.onNavigateToRegister - Navigation callback
 * @param {boolean} props.isLoading - Action loading state
 */
export function AccountScreen({
  user,
  onLogout,
  onNavigateToLogin,
  onNavigateToRegister,
  isLoading = false,
}) {
  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);
  const backendBaseUrl = getBaseUrl();

  const handleConfirmLogout = async () => {
    setIsLogoutModalOpen(false);
    await onLogout();
  };

  if (!user) {
    return (
      <div className="screen-container">
        <div className="account-card" style={{ textAlign: 'center' }}>
          <Alert type="warning" title="No Active Session">
            You are not currently signed in. Please sign in or create an account to view your account state.
          </Alert>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', marginTop: '20px' }}>
            <Button variant="primary" onClick={onNavigateToLogin}>
              Sign In
            </Button>
            <Button variant="outline" onClick={onNavigateToRegister}>
              Create Account
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const userInitials = (user.name || user.email || 'U')
    .slice(0, 2)
    .toUpperCase();

  const isPreview = Boolean(user.isLocalPreview);

  return (
    <div className="screen-container">
      <div className="account-card">
        {isPreview && (
          <Alert
            type="warning"
            title="Local Development Preview"
          >
            This session is a local development simulation (VITE_ENABLE_AUTH_PREVIEW=true). No real account exists on a backend server, and no real authentication token was issued.
          </Alert>
        )}

        <div className="account-header">
          <div className="account-user-info">
            <div className="account-avatar" aria-hidden="true">
              {userInitials}
            </div>
            <div>
              <h1 className="auth-card-title" style={{ fontSize: '20px' }}>
                {user.name || 'Account User'}
              </h1>
              <p className="auth-card-subtitle">{user.email}</p>
            </div>
          </div>

          <div className={`account-status-badge ${isPreview ? 'account-status-badge-preview' : ''}`}>
            <span className="status-indicator" aria-hidden="true" />
            <span>{isPreview ? 'Local Development Preview' : (user.status || 'Active')}</span>
          </div>
        </div>

        {/* Backend API Contract Status Note */}
        <div className="contract-note-box">
          <div className="contract-note-title">
            <svg
              width="16"
              height="16"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="16" x2="12" y2="12" />
              <line x1="12" y1="8" x2="12.01" y2="8" />
            </svg>
            <span>Backend Integration Status</span>
          </div>
          <p style={{ margin: 0 }}>
            {backendBaseUrl
              ? `Connected to configured backend at: ${backendBaseUrl}. Contract synchronization pending backend teammate confirmation.`
              : isPreview
              ? 'Active session is a simulated preview for local UI evaluation. When backend contracts are ready, configure VITE_API_BASE_URL to connect to the real API.'
              : 'Backend API contracts (endpoints, payload schemas, and auth token strategy) are isolated in authContracts.js pending confirmation.'}
          </p>
        </div>

        <div className="account-details-list">
          <div className="detail-item">
            <span className="detail-label">Account Identifier</span>
            <span className="detail-value">
              {isPreview ? 'None (Local Preview Simulation)' : (user.id || 'Pending Backend Assignment')}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Email Address</span>
            <span className="detail-value">{user.email}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Account Role</span>
            <span className="detail-value">
              {isPreview ? 'Development Simulation' : (user.role || 'Standard User')}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Session Type</span>
            <span className="detail-value">
              {isPreview ? 'Local Development Preview (Simulated)' : 'Authenticated Backend Session'}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Backend URL</span>
            <span className="detail-value">{backendBaseUrl || 'Not configured (VITE_API_BASE_URL)'}</span>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <Button
            variant="danger"
            onClick={() => setIsLogoutModalOpen(true)}
            disabled={isLoading}
          >
            Sign Out
          </Button>
        </div>
      </div>

      {/* Logout Confirmation Modal */}
      <Modal
        isOpen={isLogoutModalOpen}
        onClose={() => setIsLogoutModalOpen(false)}
        title="Confirm Sign Out"
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => setIsLogoutModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleConfirmLogout}
              loading={isLoading}
            >
              Sign Out
            </Button>
          </>
        }
      >
        <p style={{ margin: 0 }}>
          Are you sure you want to sign out of your Page to Voice account? You will need to sign back in to access your account profile.
        </p>
      </Modal>
    </div>
  );
}

export default AccountScreen;
