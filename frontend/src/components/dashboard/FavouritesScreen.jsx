import React from 'react';
import './Dashboard.css';

/**
 * Favourites Screen
 * Manages bookmarked audiobooks and starred documents.
 */
export function FavouritesScreen({ onNavigateToLibrary }) {
  return (
    <div className="dashboard-view-container">
      <div className="dash-panel">
        <div className="dash-panel-header">
          <h3 className="dash-panel-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
            <span>Saved Favourites</span>
          </h3>
        </div>

        <div className="empty-state-card">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
          <div className="empty-state-title">No favourites bookmarked yet</div>
          <p className="empty-state-desc">
            You can bookmark your most important documents and audiobooks for one-click access here.
          </p>
          <button
            type="button"
            className="welcome-cta-btn"
            onClick={onNavigateToLibrary}
          >
            Explore Document Library
          </button>
        </div>
      </div>
    </div>
  );
}

export default FavouritesScreen;
