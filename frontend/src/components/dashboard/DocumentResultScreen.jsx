import React, { useState } from 'react';
import './Dashboard.css';

/**
 * Document Processing Results & Reader Screen
 * Displays document metadata, chapter navigation, comfortable text reading,
 * font sizing, text export, and playback integration.
 */
export function DocumentResultScreen({
  documentData,
  onNavigateToLibrary,
  onPlayChapter,
}) {
  const [activeChapterIndex, setActiveChapterIndex] = useState(0);
  const [fontSize, setFontSize] = useState('md'); // 'sm', 'md', 'lg'
  const [copyFeedback, setCopyFeedback] = useState(false);

  if (!documentData) {
    return (
      <div className="dashboard-view-container">
        <div className="empty-state-card">
          <div className="empty-state-title">No Document Loaded</div>
          <p className="empty-state-desc">Select a document from your library to view results.</p>
          <button type="button" className="welcome-cta-btn" onClick={onNavigateToLibrary}>
            Return to Library
          </button>
        </div>
      </div>
    );
  }

  const {
    title = 'Untitled Document',
    file_format = 'txt',
    processing_status = 'completed',
    chapters = [],
    extracted_text = '',
    created_at,
  } = documentData;

  // Use chapters if available, otherwise fallback to extracted_text as single section
  const sectionList = chapters.length > 0
    ? chapters
    : [{ title: 'Full Document Text', content: extracted_text || 'No text extracted.' }];

  const currentChapter = sectionList[activeChapterIndex] || sectionList[0];
  const currentText = currentChapter?.content || extracted_text || 'No text extracted.';

  // Word count estimate
  const wordCount = currentText.trim().split(/\s+/).filter(Boolean).length;
  const totalDocWords = sectionList.reduce((acc, chap) => {
    return acc + (chap.content || '').trim().split(/\s+/).filter(Boolean).length;
  }, 0) || wordCount;

  const handleCopyText = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(currentText);
      setCopyFeedback(true);
      setTimeout(() => setCopyFeedback(false), 2000);
    }
  };

  const handleDownloadText = () => {
    const blob = new Blob([currentText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${title.replace(/\.[^/.]+$/, '')}_chapter_${activeChapterIndex + 1}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handlePlayCurrentChapter = () => {
    if (onPlayChapter) {
      onPlayChapter({
        title: title,
        chapterTitle: currentChapter.title || `Chapter ${activeChapterIndex + 1}`,
        docType: file_format.toUpperCase(),
        audioUrl: currentChapter.audio_url || null, // Will use sample if null
      });
    }
  };

  return (
    <div className="dashboard-view-container">
      {/* Top Navigation & Actions Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <button
          type="button"
          onClick={onNavigateToLibrary}
          style={{
            background: 'transparent',
            border: '1px solid var(--border)',
            padding: '8px 14px',
            borderRadius: '8px',
            color: 'var(--text-h)',
            fontSize: '13px',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          &larr; Back to Library
        </button>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            type="button"
            className="welcome-cta-btn"
            style={{ padding: '8px 16px', fontSize: '13px' }}
            onClick={handlePlayCurrentChapter}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            <span>Listen with Player</span>
          </button>
        </div>
      </div>

      {/* Main Two-Pane Reader */}
      <div className="reader-container">
        {/* Left Pane: Chapters & Structure */}
        <div className="reader-sidebar">
          <div className="reader-sidebar-title">
            Document Sections ({sectionList.length})
          </div>
          <ul className="reader-chapter-list">
            {sectionList.map((chap, idx) => {
              const chapWords = (chap.content || '').trim().split(/\s+/).filter(Boolean).length;
              return (
                <li key={idx}>
                  <button
                    type="button"
                    className={`reader-chapter-btn ${activeChapterIndex === idx ? 'active' : ''}`}
                    onClick={() => setActiveChapterIndex(idx)}
                  >
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {chap.title || `Section ${idx + 1}`}
                    </span>
                    <span style={{ fontSize: '11px', opacity: 0.8, marginLeft: '6px' }}>
                      {chapWords}w
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>

          <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid var(--border)', fontSize: '12px', color: 'var(--text)' }}>
            <div><strong>Format:</strong> {file_format.toUpperCase()}</div>
            <div><strong>Status:</strong> {processing_status}</div>
            <div><strong>Total Words:</strong> ~{totalDocWords}</div>
          </div>
        </div>

        {/* Right Pane: Comfortable Text Reader */}
        <div className="reader-content-area">
          {/* Reader Toolbar */}
          <div className="reader-toolbar">
            <div className="reader-meta-group">
              <span className={`format-pill ${file_format.toLowerCase()}`}>
                {file_format.toUpperCase()}
              </span>
              <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '700', color: 'var(--text-h)' }}>
                {currentChapter.title || `Chapter ${activeChapterIndex + 1}`}
              </h3>
              <span className={`status-badge ${processing_status}`}>
                {processing_status}
              </span>
            </div>

            <div className="reader-tool-actions">
              {/* Font Size Adjusters */}
              <div style={{ display: 'inline-flex', border: '1px solid var(--border)', borderRadius: '6px', overflow: 'hidden' }}>
                <button
                  type="button"
                  onClick={() => setFontSize('sm')}
                  style={{
                    background: fontSize === 'sm' ? 'var(--accent-bg)' : 'transparent',
                    border: 'none',
                    padding: '4px 8px',
                    fontSize: '11px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    color: fontSize === 'sm' ? 'var(--accent)' : 'var(--text)',
                  }}
                  title="Small text"
                >
                  A-
                </button>
                <button
                  type="button"
                  onClick={() => setFontSize('md')}
                  style={{
                    background: fontSize === 'md' ? 'var(--accent-bg)' : 'transparent',
                    border: 'none',
                    padding: '4px 8px',
                    fontSize: '13px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    color: fontSize === 'md' ? 'var(--accent)' : 'var(--text)',
                  }}
                  title="Medium text"
                >
                  A
                </button>
                <button
                  type="button"
                  onClick={() => setFontSize('lg')}
                  style={{
                    background: fontSize === 'lg' ? 'var(--accent-bg)' : 'transparent',
                    border: 'none',
                    padding: '4px 8px',
                    fontSize: '15px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    color: fontSize === 'lg' ? 'var(--accent)' : 'var(--text)',
                  }}
                  title="Large text"
                >
                  A+
                </button>
              </div>

              {/* Copy Button */}
              <button
                type="button"
                className="reader-tool-btn"
                onClick={handleCopyText}
                title="Copy section text to clipboard"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                </svg>
                <span>{copyFeedback ? 'Copied!' : 'Copy'}</span>
              </button>

              {/* Download Button */}
              <button
                type="button"
                className="reader-tool-btn"
                onClick={handleDownloadText}
                title="Download text file"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                <span>Download</span>
              </button>
            </div>
          </div>

          {/* Text Content */}
          <div className={`reader-text-body font-${fontSize}`}>
            {currentText}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DocumentResultScreen;
