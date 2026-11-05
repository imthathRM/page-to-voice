import React, { useState } from 'react';
import Button from '../common/Button/Button';
import './Dashboard.css';

/**
 * Settings & Profile Screen
 */
export function SettingsScreen({
  user,
  onLogoutClick,
}) {
  const [defaultSpeed, setDefaultSpeed] = useState('1.0');
  const [autoPlayNext, setAutoPlayNext] = useState(true);
  const [ocrFallback, setOcrFallback] = useState(true);
  const [defaultLanguage, setDefaultLanguage] = useState('en');
  const [savedNotice, setSavedNotice] = useState(false);

  const handleSavePreferences = (e) => {
    e.preventDefault();
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 2500);
  };

  const userInitials = (user?.username || user?.name || user?.email || 'U').slice(0, 2).toUpperCase();

  return (
    <div className="dashboard-view-container">
      {savedNotice && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          color: '#059669',
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '20px',
          fontSize: '13.5px',
          fontWeight: '600',
        }}>
          Preferences saved successfully!
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
        {/* User Profile Card */}
        <div className="dash-panel">
          <h3 className="dash-panel-title" style={{ marginBottom: '20px' }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            <span>User Profile Information</span>
          </h3>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
            <div style={{
              width: '60px',
              height: '60px',
              borderRadius: '50%',
              background: 'var(--accent-bg)',
              color: 'var(--accent)',
              border: '2px solid var(--accent-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '22px',
              fontWeight: '700',
            }}>
              {userInitials}
            </div>
            <div>
              <h4 style={{ margin: '0 0 4px', fontSize: '17px', color: 'var(--text-h)' }}>
                {user?.username || user?.name || 'Registered User'}
              </h4>
              <span className="status-badge completed" style={{ textTransform: 'capitalize' }}>
                {user?.role || 'Active Member'}
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13.5px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: 'var(--code-bg)', borderRadius: '8px' }}>
              <span style={{ color: 'var(--text)' }}>User ID</span>
              <strong style={{ color: 'var(--text-h)' }}>#{user?.id || '—'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: 'var(--code-bg)', borderRadius: '8px' }}>
              <span style={{ color: 'var(--text)' }}>Email Address</span>
              <strong style={{ color: 'var(--text-h)' }}>{user?.email || '—'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: 'var(--code-bg)', borderRadius: '8px' }}>
              <span style={{ color: 'var(--text)' }}>Username</span>
              <strong style={{ color: 'var(--text-h)' }}>{user?.username || '—'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: 'var(--code-bg)', borderRadius: '8px' }}>
              <span style={{ color: 'var(--text)' }}>Session Validity</span>
              <strong style={{ color: '#059669' }}>Active (JWT 30m)</strong>
            </div>
          </div>

          <div style={{ marginTop: '28px', paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
            <Button
              variant="danger"
              fullWidth
              onClick={onLogoutClick}
            >
              Sign Out of Account
            </Button>
          </div>
        </div>

        {/* Audio & Parsing Preferences */}
        <div className="dash-panel">
          <h3 className="dash-panel-title" style={{ marginBottom: '20px' }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
            <span>Preferences</span>
          </h3>

          <form onSubmit={handleSavePreferences} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="upload-field-group">
              <label htmlFor="pref-speed" className="upload-field-label">
                Default Playback Speed
              </label>
              <select
                id="pref-speed"
                className="upload-select"
                value={defaultSpeed}
                onChange={(e) => setDefaultSpeed(e.target.value)}
              >
                <option value="0.75">0.75x (Slower)</option>
                <option value="1.0">1.0x (Normal)</option>
                <option value="1.25">1.25x</option>
                <option value="1.5">1.5x (Fast)</option>
                <option value="2.0">2.0x (Double)</option>
              </select>
            </div>

            <div className="upload-field-group">
              <label htmlFor="pref-lang" className="upload-field-label">
                Default Document Language
              </label>
              <select
                id="pref-lang"
                className="upload-select"
                value={defaultLanguage}
                onChange={(e) => setDefaultLanguage(e.target.value)}
              >
                <option value="en">English</option>
                <option value="ta">Tamil (தமிழ்)</option>
                <option value="si">Sinhala (සිංහල)</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0' }}>
              <div>
                <div style={{ fontSize: '13.5px', fontWeight: '600', color: 'var(--text-h)' }}>
                  Continuous Chapter Playback
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text)' }}>
                  Automatically start next chapter when current one finishes
                </div>
              </div>
              <input
                type="checkbox"
                checked={autoPlayNext}
                onChange={(e) => setAutoPlayNext(e.target.checked)}
                style={{ width: '18px', height: '18px', cursor: 'pointer' }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0' }}>
              <div>
                <div style={{ fontSize: '13.5px', fontWeight: '600', color: 'var(--text-h)' }}>
                  Automatic OCR Fallback
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text)' }}>
                  Trigger OCR when standard parser detects scanned image pages
                </div>
              </div>
              <input
                type="checkbox"
                checked={ocrFallback}
                onChange={(e) => setOcrFallback(e.target.checked)}
                style={{ width: '18px', height: '18px', cursor: 'pointer' }}
              />
            </div>

            <Button type="submit" variant="primary" style={{ marginTop: '12px' }}>
              Save Preferences
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default SettingsScreen;
