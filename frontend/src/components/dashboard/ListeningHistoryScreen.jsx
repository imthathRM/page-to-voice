import React from 'react';
import './Dashboard.css';

/**
 * Listening History Screen
 * Shows user listening sessions, resume controls, and empty state.
 */
export function ListeningHistoryScreen({ onNavigateToLibrary }) {
  return (
    <div className="dashboard-view-container">
      <div className="dash-panel">
        <div className="dash-panel-header">
          <h3 className="dash-panel-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            <span>Your Listening History</span>
          </h3>
        </div>

        <div className="empty-state-card">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <div className="empty-state-title">No listening history recorded yet</div>
          <p className="empty-state-desc">
            As you listen to audiobooks and chapters, your playback timestamps and progress will be saved automatically so you can resume anytime.
          </p>
          <button
            type="button"
            className="welcome-cta-btn"
            onClick={onNavigateToLibrary}
          >
            Browse Library to Listen
          </button>
        </div>
      </div>
    </div>
  );
}

export default ListeningHistoryScreen;
