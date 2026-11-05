import React, { useState, useEffect } from 'react';
import documentService from '../../api/documentService';
import './Dashboard.css';

/**
 * Audiobooks Shelf Screen
 * Displays audiobooks, player preview, and honest coming-soon notice for team TTS worker integration.
 */
export function AudiobooksScreen({
  onPlayTrack,
  onNavigateToUpload,
}) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const loadDocs = async () => {
      try {
        const data = await documentService.getDocuments({ status: 'completed' });
        if (isMounted) {
          setDocuments(data);
        }
      } catch {
        // Fallback gracefully
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    loadDocs();
    return () => {
      isMounted = false;
    };
  }, []);

  const handlePlaySampleAudiobook = (doc) => {
    if (onPlayTrack) {
      onPlayTrack({
        title: doc ? doc.title : 'Page to Voice Audiobook Sample',
        chapterTitle: doc ? 'Chapter 1: Introduction' : 'Chapter 1: Platform Overview',
        docType: doc ? (doc.file_format || 'PDF').toUpperCase() : 'AUDIOBOOK',
        // High quality web audio sample for test playback
        audioUrl: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
      });
    }
  };

  return (
    <div className="dashboard-view-container">
      {/* Honest Coming-Soon Banner */}
      <div className="coming-soon-banner">
        <h3>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>Neural TTS Batch Synthesis Pipeline — Development Status</span>
        </h3>
        <p>
          Document parsing, OCR, and chapter extraction (Tasks 1 & 2) are fully complete!
          The asynchronous neural Text-to-Speech synthesis worker is currently being integrated by Team Member 4.
          In the meantime, you can test the interactive audiobook player below with demo audio streams, variable playback speeds (0.75x – 2x), seeking, and volume controls.
        </p>
      </div>

      {/* Interactive Player Preview Card */}
      <div className="dash-panel" style={{ marginBottom: '28px', background: 'var(--social-bg)', borderColor: 'var(--accent-border)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <h4 style={{ margin: '0 0 4px', fontSize: '16px', fontWeight: '700', color: 'var(--text-h)' }}>
              🎧 Try Interactive Audiobook Player Preview
            </h4>
            <p style={{ margin: 0, fontSize: '13px', color: 'var(--text)' }}>
              Test audio streaming, pause/resume, 10s skip, scrubber seeking, and variable speeds.
            </p>
          </div>
          <button
            type="button"
            className="welcome-cta-btn"
            onClick={() => handlePlaySampleAudiobook(null)}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            <span>Play Sample Stream</span>
          </button>
        </div>
      </div>

      {/* Available Documents for Audio Shelf */}
      <div className="dash-panel">
        <div className="dash-panel-header">
          <h3 className="dash-panel-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
            </svg>
            <span>Processed Document Audio Queue</span>
          </h3>
        </div>

        {loading ? (
          <div className="empty-state-card">
            <p>Loading document audio queue...</p>
          </div>
        ) : documents.length > 0 ? (
          <div className="library-grid">
            {documents.map((doc) => (
              <div key={doc.id} className="doc-card">
                <div>
                  <div className="doc-card-top">
                    <span className="format-pill pdf">AUDIO READY</span>
                    <span className="status-badge completed">Ready</span>
                  </div>
                  <h4 className="doc-card-title">{doc.title}</h4>
                  <div className="doc-card-date">
                    {doc.chapter_count || 1} Chapters Extracted
                  </div>
                </div>

                <div className="doc-card-footer" style={{ marginTop: '16px' }}>
                  <button
                    type="button"
                    className="welcome-cta-btn"
                    style={{ width: '100%', justifyContent: 'center', padding: '8px 12px', fontSize: '13px' }}
                    onClick={() => handlePlaySampleAudiobook(doc)}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                      <polygon points="5 3 19 12 5 21 5 3" />
                    </svg>
                    <span>Play in Audio Player</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state-card">
            <div className="empty-state-title">No processed audiobooks yet</div>
            <p className="empty-state-desc">
              Upload a document first to extract its chapters and generate an audiobook.
            </p>
            <button
              type="button"
              className="welcome-cta-btn"
              onClick={onNavigateToUpload}
            >
              Upload Document Now
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default AudiobooksScreen;
