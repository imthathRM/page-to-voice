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
  const backendBaseUrl = getBaseUrl() || 'http://localhost:8000';

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

  const userInitials = (user.username || user.name || user.email || 'U')
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
            This session is a local development simulation (VITE_ENABLE_AUTH_PREVIEW=true).
          </Alert>
        )}

        <div className="account-header">
          <div className="account-user-info">
            <div className="account-avatar" aria-hidden="true">
              {userInitials}
            </div>
            <div>
              <h1 className="auth-card-title" style={{ fontSize: '20px' }}>
                {user.username || user.name || 'Account User'}
              </h1>
              <p className="auth-card-subtitle">{user.email}</p>
            </div>
          </div>

          <div className={`account-status-badge ${isPreview ? 'account-status-badge-preview' : ''}`}>
            <span className="status-indicator" aria-hidden="true" />
            <span>{isPreview ? 'Preview Mode' : (user.status || 'Active')}</span>
          </div>
        </div>

        {/* Backend Integration Status Note */}
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
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            <span>Backend Integration Status</span>
          </div>
          <p style={{ margin: 0 }}>
            {`Connected to Page to Voice FastAPI service at ${backendBaseUrl}. Authenticated via JWT Bearer token.`}
          </p>
        </div>

        <div className="account-details-list">
          <div className="detail-item">
            <span className="detail-label">Account Identifier (ID)</span>
            <span className="detail-value">
              {user.id !== null && user.id !== undefined ? `#${user.id}` : 'None'}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Username</span>
            <span className="detail-value">{user.username || user.name || 'N/A'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Email Address</span>
            <span className="detail-value">{user.email}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Account Role</span>
            <span className="detail-value" style={{ textTransform: 'capitalize' }}>
              {user.role || 'user'}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Session Type</span>
            <span className="detail-value">
              {isPreview ? 'Local Simulation' : 'Authenticated JWT Session'}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Backend Service</span>
            <span className="detail-value">{backendBaseUrl}</span>
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
