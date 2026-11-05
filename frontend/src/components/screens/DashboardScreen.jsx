import { useState, useEffect } from 'react';
import Button from '../common/Button/Button';
import LoadingSpinner from '../common/LoadingSpinner/LoadingSpinner';
import Alert from '../common/Alert/Alert';
import documentService from '../../api/documentService';
import './Screens.css';

export function DashboardScreen({ user, onNavigate }) {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);

  const fetchDocuments = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await documentService.getDocuments();
      setDocuments(data);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to load documents.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    documentService
      .getDocuments()
      .then((data) => {
        if (isMounted) setDocuments(data);
      })
      .catch((err) => {
        if (isMounted) setErrorMsg(err.message || 'Failed to load documents.');
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const totalChapters = documents.reduce((acc, d) => acc + (d.chapter_count || 0), 0);
  const completedDocs = documents.filter((d) => d.status === 'completed').length;

  return (
    <div className="screen-container">
      <div className="dashboard-wrap">
        {/* Hero Banner */}
        <div className="dashboard-hero">
          <div className="dashboard-hero-content">
            <h1>Welcome back, {user?.name || user?.username || 'Reader'}!</h1>
            <p>
              Upload documents, books, or scripts in English, Tamil, or Sinhala. Convert them into structured chapters and narrated audiobooks powered by Gemini AI.
            </p>
          </div>
          <Button
            variant="primary"
            size="lg"
            onClick={() => onNavigate('upload')}
            style={{ background: '#ffffff', color: '#4f46e5', fontWeight: 700 }}
          >
            + Upload Document
          </Button>
        </div>

        {/* Stats Row */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <div>
              <div className="stat-value">{documents.length}</div>
              <div className="stat-label">Total Documents</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#ecfdf5', color: '#059669' }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
              </svg>
            </div>
            <div>
              <div className="stat-value">{totalChapters}</div>
              <div className="stat-label">Extracted Chapters</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: '#fdf4ff', color: '#c026d3' }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18V5l12-2v13" />
                <circle cx="6" cy="18" r="3" />
                <circle cx="18" cy="16" r="3" />
              </svg>
            </div>
            <div>
              <div className="stat-value">{completedDocs}</div>
              <div className="stat-label">Ready for Audio</div>
            </div>
          </div>
        </div>

        {/* Documents Section */}
        <div>
          <div className="section-header">
            <h2 className="section-title">Your Documents</h2>
            <Button variant="outline" size="sm" onClick={fetchDocuments} disabled={isLoading}>
              Refresh
            </Button>
          </div>

          {errorMsg && (
            <Alert type="error" title="Error" onClose={() => setErrorMsg(null)}>
              {errorMsg}
            </Alert>
          )}

          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <LoadingSpinner size="lg" />
              <p style={{ marginTop: '12px', color: '#64748b' }}>Loading your library...</p>
            </div>
          ) : documents.length === 0 ? (
            <div className="account-card" style={{ textAlign: 'center', padding: '48px 24px', margin: '0 auto' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📚</div>
              <h3 style={{ margin: '0 0 8px', color: '#0f172a' }}>No documents uploaded yet</h3>
              <p style={{ margin: '0 0 20px', color: '#64748b', fontSize: '14px' }}>
                Upload your first PDF, Word document, or text file to extract chapters and listen.
              </p>
              <Button variant="primary" onClick={() => onNavigate('upload')}>
                Upload a Document
              </Button>
            </div>
          ) : (
            <div className="docs-grid">
              {documents.map((doc) => (
                <div key={doc.id} className="doc-card">
                  <div>
                    <div className="doc-card-header">
                      <div className="doc-badge-group">
                        <span className="file-type-pill">{doc.file_type}</span>
                        <span className={`status-badge ${doc.status}`}>
                          {doc.status}
                        </span>
                      </div>
                      <span style={{ fontSize: '12px', color: '#64748b' }}>
                        Lang: {doc.source_language?.toUpperCase() || 'EN'}
                      </span>
                    </div>

                    <div className="doc-card-body" style={{ marginTop: '12px' }}>
                      <h3 title={doc.title}>{doc.title}</h3>
                      <div className="doc-meta-info">
                        <span>Chapters: {doc.chapter_count || 0}</span>
                        <span>
                          {new Date(doc.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="doc-card-actions">
                    <Button
                      variant="primary"
                      size="sm"
                      fullWidth
                      onClick={() => onNavigate('document-detail', { documentId: doc.id })}
                    >
                      {doc.status === 'completed' ? 'Open & Listen' : 'Process Chapters'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DashboardScreen;
