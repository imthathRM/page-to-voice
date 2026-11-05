import React, { useState, useEffect } from 'react';
import documentService from '../../api/documentService';
import Modal from '../common/Modal/Modal';
import Button from '../common/Button/Button';
import './Dashboard.css';

/**
 * My Library Screen
 * Full document management: search, format filter pills, sorting, card/table view,
 * reading view trigger, audio player loading, and delete confirmation modal.
 */
export function LibraryScreen({
  onNavigateToUpload,
  onOpenDocument,
  onPlayDocument,
}) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [formatFilter, setFormatFilter] = useState('all');
  const [sortBy, setSortBy] = useState('newest'); // 'newest', 'oldest', 'alpha'
  const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'table'

  // Delete modal state
  const [documentToDelete, setDocumentToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const formatPills = ['all', 'pdf', 'docx', 'txt', 'pptx', 'epub', 'rtf'];

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const params = {};
      if (searchQuery.trim()) params.search = searchQuery.trim();
      if (formatFilter !== 'all') params.file_format = formatFilter;
      const data = await documentService.getDocuments(params);
      setDocuments(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load documents.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchDocuments();
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery, formatFilter]);

  const sortedDocuments = [...documents].sort((a, b) => {
    if (sortBy === 'newest') {
      return new Date(b.created_at || 0) - new Date(a.created_at || 0);
    }
    if (sortBy === 'oldest') {
      return new Date(a.created_at || 0) - new Date(b.created_at || 0);
    }
    if (sortBy === 'alpha') {
      return (a.title || '').localeCompare(b.title || '');
    }
    return 0;
  });

  const handleDeleteConfirm = async () => {
    if (!documentToDelete) return;
    setIsDeleting(true);
    try {
      await documentService.deleteDocument(documentToDelete.id);
      setDocumentToDelete(null);
      await fetchDocuments();
    } catch (err) {
      alert(`Delete failed: ${err.message || 'Unable to delete document'}`);
    } finally {
      setIsDeleting(false);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'Just now';
    try {
      return new Date(isoString).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="dashboard-view-container">
      {/* Controls: Search, Format Pills, Sort, View Mode */}
      <div className="library-controls">
        {/* Search */}
        <div className="library-search-box">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            className="library-search-input"
            placeholder="Search documents by title..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery('')}
              style={{ background: 'none', border: 'none', color: 'var(--text)', cursor: 'pointer', fontSize: '16px' }}
            >
              &times;
            </button>
          )}
        </div>

        {/* Format Pills */}
        <div className="library-filter-pills">
          {formatPills.map((fmt) => (
            <button
              key={fmt}
              type="button"
              className={`filter-pill-btn ${formatFilter === fmt ? 'active' : ''}`}
              onClick={() => setFormatFilter(fmt)}
            >
              {fmt.toUpperCase()}
            </button>
          ))}
        </div>

        {/* Sort & View Mode */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            style={{
              padding: '6px 10px',
              borderRadius: '6px',
              border: '1px solid var(--border)',
              background: 'var(--bg)',
              color: 'var(--text-h)',
              fontSize: '12px',
            }}
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="alpha">Alphabetical (A-Z)</option>
          </select>

          <div style={{ display: 'inline-flex', border: '1px solid var(--border)', borderRadius: '6px', overflow: 'hidden' }}>
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              style={{
                background: viewMode === 'grid' ? 'var(--accent-bg)' : 'transparent',
                border: 'none',
                padding: '6px 10px',
                color: viewMode === 'grid' ? 'var(--accent)' : 'var(--text)',
                cursor: 'pointer',
              }}
              title="Grid View"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="7" height="7" />
                <rect x="14" y="3" width="7" height="7" />
                <rect x="14" y="14" width="7" height="7" />
                <rect x="3" y="14" width="7" height="7" />
              </svg>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('table')}
              style={{
                background: viewMode === 'table' ? 'var(--accent-bg)' : 'transparent',
                border: 'none',
                padding: '6px 10px',
                color: viewMode === 'table' ? 'var(--accent)' : 'var(--text)',
                cursor: 'pointer',
              }}
              title="Table View"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="8" y1="6" x2="21" y2="6" />
                <line x1="8" y1="12" x2="21" y2="12" />
                <line x1="8" y1="18" x2="21" y2="18" />
                <line x1="3" y1="6" x2="3.01" y2="6" />
                <line x1="3" y1="12" x2="3.01" y2="12" />
                <line x1="3" y1="18" x2="3.01" y2="18" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Error Notice */}
      {error && (
        <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.1)', color: '#dc2626', borderRadius: '8px', marginBottom: '16px' }}>
          {error}
        </div>
      )}

      {/* Documents List */}
      {loading ? (
        <div className="empty-state-card">
          <p>Loading documents from your library...</p>
        </div>
      ) : sortedDocuments.length > 0 ? (
        viewMode === 'grid' ? (
          <div className="library-grid">
            {sortedDocuments.map((doc) => {
              const ext = (doc.file_format || doc.file_type || 'txt').toLowerCase();
              return (
                <div key={doc.id} className="doc-card">
                  <div>
                    <div className="doc-card-top">
                      <span className={`format-pill ${ext}`}>{ext.toUpperCase()}</span>
                      <span className={`status-badge ${doc.processing_status || 'completed'}`}>
                        {doc.processing_status || 'completed'}
                      </span>
                    </div>

                    <h4 className="doc-card-title" title={doc.title}>
                      {doc.title}
                    </h4>
                    <div className="doc-card-date">
                      Uploaded on {formatDate(doc.created_at)}
                    </div>

                    <div className="doc-card-stats">
                      <span>📖 {doc.chapter_count || 1} {doc.chapter_count === 1 ? 'chapter' : 'chapters'}</span>
                      <span>🌐 {doc.language ? doc.language.toUpperCase() : 'EN'}</span>
                    </div>
                  </div>

                  <div className="doc-card-footer">
                    <button
                      type="button"
                      className="doc-card-btn primary"
                      onClick={() => onOpenDocument(doc.id)}
                    >
                      Read Text
                    </button>
                    <button
                      type="button"
                      className="doc-card-btn primary"
                      onClick={() => onPlayDocument(doc)}
                      title="Play Audiobook"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                        <polygon points="5 3 19 12 5 21 5 3" />
                      </svg>
                      <span>Listen</span>
                    </button>
                    <button
                      type="button"
                      className="doc-card-btn danger"
                      onClick={() => setDocumentToDelete(doc)}
                      title="Delete document"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="dash-panel" style={{ padding: 0 }}>
            <div className="docs-table-wrapper">
              <table className="docs-table">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Format</th>
                    <th>Chapters</th>
                    <th>Status</th>
                    <th>Uploaded Date</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedDocuments.map((doc) => {
                    const ext = (doc.file_format || doc.file_type || 'txt').toLowerCase();
                    return (
                      <tr key={doc.id}>
                        <td>
                          <div className="doc-name-cell">
                            <span>{doc.title}</span>
                          </div>
                        </td>
                        <td>
                          <span className={`format-pill ${ext}`}>{ext.toUpperCase()}</span>
                        </td>
                        <td>{doc.chapter_count || 1}</td>
                        <td>
                          <span className={`status-badge ${doc.processing_status || 'completed'}`}>
                            {doc.processing_status || 'completed'}
                          </span>
                        </td>
                        <td>{formatDate(doc.created_at)}</td>
                        <td>
                          <div style={{ display: 'flex', gap: '6px' }}>
                            <button
                              type="button"
                              className="table-action-btn"
                              onClick={() => onOpenDocument(doc.id)}
                            >
                              Read
                            </button>
                            <button
                              type="button"
                              className="table-action-btn"
                              onClick={() => onPlayDocument(doc)}
                            >
                              Listen
                            </button>
                            <button
                              type="button"
                              className="table-action-btn"
                              style={{ color: '#ef4444' }}
                              onClick={() => setDocumentToDelete(doc)}
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )
      ) : (
        <div className="empty-state-card" style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '12px' }}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
          <div className="empty-state-title">No documents found</div>
          <p className="empty-state-desc">
            {searchQuery || formatFilter !== 'all'
              ? 'No documents matched your filters. Try clearing the search or filter.'
              : 'Your library is currently empty. Upload your first document to get started.'}
          </p>
          <button
            type="button"
            className="welcome-cta-btn"
            onClick={onNavigateToUpload}
          >
            Upload Document
          </button>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {documentToDelete && (
        <Modal
          isOpen={Boolean(documentToDelete)}
          onClose={() => setDocumentToDelete(null)}
          title="Delete Document"
          footer={
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <Button
                variant="outline"
                onClick={() => setDocumentToDelete(null)}
                disabled={isDeleting}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={handleDeleteConfirm}
                loading={isDeleting}
              >
                Delete Permanently
              </Button>
            </div>
          }
        >
          <p style={{ margin: 0, fontSize: '14px', lineHeight: 1.5 }}>
            Are you sure you want to delete <strong>{documentToDelete.title}</strong>?
            This will permanently remove the document, its extracted chapters, and any generated audiobooks. This action cannot be undone.
          </p>
        </Modal>
      )}
    </div>
  );
}

export default LibraryScreen;
