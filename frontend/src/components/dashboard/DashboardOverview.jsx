import React, { useState, useEffect } from 'react';
import documentService from '../../api/documentService';
import './Dashboard.css';

/**
 * Dashboard Overview Screen
 * Displays welcome banner, real aggregated metrics, getting started guide, recent documents, and activities.
 */
export function DashboardOverview({
  user,
  onNavigate,
  onOpenDocument,
}) {
  const [stats, setStats] = useState({
    total_documents: 0,
    processed_documents: 0,
    audiobooks_generated: 0,
    processing_documents: 0,
    recent_documents: [],
    recent_activities: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const fetchStats = async () => {
      try {
        setLoading(true);
        const data = await documentService.getDashboardStats();
        if (isMounted) {
          setStats(data);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Failed to load dashboard metrics.');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchStats();
    return () => {
      isMounted = false;
    };
  }, []);

  const formatDate = (isoString) => {
    if (!isoString) return 'Just now';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return isoString;
    }
  };

  const userName = user?.username || user?.name || user?.email?.split('@')[0] || 'Member';

  return (
    <div className="dashboard-view-container">
      {/* Welcome Banner */}
      <div className="dashboard-welcome-banner">
        <div className="welcome-text">
          <h2>Welcome back, {userName}! 👋</h2>
          <p>
            Transform your documents into high-quality audiobooks. Upload a PDF, DOCX, TXT, PPTX, EPUB, or RTF document to get started.
          </p>
        </div>
        <button
          type="button"
          className="welcome-cta-btn"
          onClick={() => onNavigate('upload')}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <span>Upload New Document</span>
        </button>
      </div>

      {/* 4 Metric Stats Cards */}
      <div className="dashboard-stats-grid">
        {/* Card 1: Total Documents */}
        <div className="stat-card">
          <div className="stat-info">
            <span className="stat-label">Total Documents</span>
            <span className="stat-value">{loading ? '...' : stats.total_documents}</span>
            <span className="stat-subtext">Across 6 supported formats</span>
          </div>
          <div className="stat-icon purple">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </div>
        </div>

        {/* Card 2: Processed Successfully */}
        <div className="stat-card">
          <div className="stat-info">
            <span className="stat-label">Processed Successfully</span>
            <span className="stat-value">{loading ? '...' : stats.processed_documents}</span>
            <span className="stat-subtext">Extracted text & chapters</span>
          </div>
          <div className="stat-icon green">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          </div>
        </div>

        {/* Card 3: Audiobooks Generated */}
        <div className="stat-card">
          <div className="stat-info">
            <span className="stat-label">Audiobooks Generated</span>
            <span className="stat-value">{loading ? '...' : stats.audiobooks_generated}</span>
            <span className="stat-subtext">Ready for playback</span>
          </div>
          <div className="stat-icon blue">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
            </svg>
          </div>
        </div>

        {/* Card 4: In Processing */}
        <div className="stat-card">
          <div className="stat-info">
            <span className="stat-label">Processing / Queued</span>
            <span className="stat-value">{loading ? '...' : stats.processing_documents}</span>
            <span className="stat-subtext">Active extraction jobs</span>
          </div>
          <div className="stat-icon amber">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
          </div>
        </div>
      </div>

      {/* Getting Started Guide */}
      <div className="getting-started-banner">
        <h3>🚀 How Page to Voice Works</h3>
        <div className="getting-started-steps">
          <div className="step-card">
            <div className="step-number">1</div>
            <div className="step-text">
              <h4>Upload Your Document</h4>
              <p>Drag and drop PDF, DOCX, TXT, PPTX, EPUB, or RTF files up to 25MB.</p>
            </div>
          </div>
          <div className="step-card">
            <div className="step-number">2</div>
            <div className="step-text">
              <h4>Automated Parsing & OCR</h4>
              <p>Text is extracted, chapters are detected, and Unicode (English, Tamil, Sinhala) is preserved.</p>
            </div>
          </div>
          <div className="step-card">
            <div className="step-number">3</div>
            <div className="step-text">
              <h4>Listen & Read</h4>
              <p>Read formatted text comfortably or listen via the persistent audiobook player.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Recent Documents & Activity Feed */}
      <div className="dashboard-main-grid">
        {/* Left: Recent Documents */}
        <div className="dash-panel">
          <div className="dash-panel-header">
            <h3 className="dash-panel-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              <span>Recent Documents</span>
            </h3>
            <button
              type="button"
              className="dash-panel-link"
              onClick={() => onNavigate('library')}
            >
              View All in Library &rarr;
            </button>
          </div>

          {loading ? (
            <div className="empty-state-card">
              <p>Loading your documents...</p>
            </div>
          ) : stats.recent_documents?.length > 0 ? (
            <div className="docs-table-wrapper">
              <table className="docs-table">
                <thead>
                  <tr>
                    <th>Document</th>
                    <th>Format</th>
                    <th>Status</th>
                    <th>Uploaded</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.recent_documents.map((doc) => {
                    const ext = doc.file_format || doc.file_type || 'txt';
                    return (
                      <tr key={doc.id}>
                        <td>
                          <div className="doc-name-cell">
                            <span title={doc.title}>{doc.title}</span>
                          </div>
                        </td>
                        <td>
                          <span className={`format-pill ${ext.toLowerCase()}`}>
                            {ext.toUpperCase()}
                          </span>
                        </td>
                        <td>
                          <span className={`status-badge ${doc.processing_status || 'completed'}`}>
                            {doc.processing_status || 'Completed'}
                          </span>
                        </td>
                        <td>{formatDate(doc.created_at)}</td>
                        <td>
                          <button
                            type="button"
                            className="table-action-btn"
                            onClick={() => onOpenDocument(doc.id)}
                          >
                            Read Text
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state-card">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              <div className="empty-state-title">No documents uploaded yet</div>
              <p className="empty-state-desc">
                Upload your first document to extract chapters and generate an audiobook.
              </p>
              <button
                type="button"
                className="welcome-cta-btn"
                onClick={() => onNavigate('upload')}
              >
                Upload First Document
              </button>
            </div>
          )}
        </div>

        {/* Right: Recent Activities */}
        <div className="dash-panel">
          <div className="dash-panel-header">
            <h3 className="dash-panel-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
              </svg>
              <span>Recent Activity</span>
            </h3>
          </div>

          {stats.recent_activities?.length > 0 ? (
            <ul className="activity-feed">
              {stats.recent_activities.map((act, idx) => (
                <li key={idx} className="activity-item">
                  <span className="activity-dot" />
                  <div className="activity-body">
                    <span className="activity-action">{act.action}</span>
                    <span className="activity-detail">{act.detail}</span>
                    <span className="activity-time">{formatDate(act.timestamp)}</span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="empty-state-card">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
              <div className="empty-state-title">No recent activity</div>
              <p className="empty-state-desc">
                Your recent uploads, text extractions, and listening sessions will appear here.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DashboardOverview;
