import { useState, useRef } from 'react';
import Button from '../common/Button/Button';
import Alert from '../common/Alert/Alert';
import documentService from '../../api/documentService';
import './Screens.css';

const MAX_SIZE_BYTES = 50 * 1024 * 1024; // 50 MB
const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt'];

export function UploadScreen({ onNavigate, onUploadSuccess }) {
  const fileInputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successDoc, setSuccessDoc] = useState(null);

  const validateFile = (file) => {
    if (!file) return false;
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setErrorMsg(`Unsupported file type (${ext}). Please upload a PDF, DOCX, or TXT file.`);
      return false;
    }
    if (file.size > MAX_SIZE_BYTES) {
      setErrorMsg('File exceeds 50 MB limit.');
      return false;
    }
    setErrorMsg(null);
    return true;
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
      setSuccessDoc(null);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
      setSuccessDoc(null);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setUploadProgress(0);
    setErrorMsg(null);

    try {
      const result = await documentService.uploadDocument(selectedFile, (percent) => {
        setUploadProgress(percent);
      });
      setSuccessDoc(result);
      setSelectedFile(null);
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to upload document.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="screen-container">
      <div className="upload-card">
        <div className="auth-card-header">
          <h1 className="auth-card-title">Upload Document</h1>
          <p className="auth-card-subtitle">
            Upload your PDF, DOCX, or TXT file to generate narration chapters and audiobooks.
          </p>
        </div>

        {errorMsg && (
          <Alert type="error" title="Upload Failed" onClose={() => setErrorMsg(null)}>
            {errorMsg}
          </Alert>
        )}

        {successDoc && (
          <Alert type="success" title="Upload Complete">
            <strong>{successDoc.title}</strong> has been uploaded successfully!
            <div style={{ marginTop: '10px', display: 'flex', gap: '8px' }}>
              <Button
                variant="primary"
                size="sm"
                onClick={() => onNavigate('document-detail', { documentId: successDoc.id })}
              >
                Open & Process Chapters
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onNavigate('dashboard')}
              >
                View in Dashboard
              </Button>
            </div>
          </Alert>
        )}

        {/* Hidden native input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />

        {/* Drag and Drop Zone */}
        <div
          className={`dropzone ${dragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
        >
          <div className="dropzone-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <div>
            <p style={{ margin: '0 0 4px', fontWeight: 600, color: '#0f172a' }}>
              Click to browse or drag and drop your file here
            </p>
            <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>
              Maximum file size: 50 MB
            </p>
          </div>
          <div className="format-pills">
            <span className="format-pill">PDF Document (.pdf)</span>
            <span className="format-pill">Word (.docx)</span>
            <span className="format-pill">Plain Text (.txt)</span>
          </div>
        </div>

        {/* Selected file preview */}
        {selectedFile && (
          <div className="selected-file-box">
            <div className="selected-file-details">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4f46e5" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              <div>
                <div className="file-name">{selectedFile.name}</div>
                <div className="file-size">{formatFileSize(selectedFile.size)}</div>
              </div>
            </div>
            <button
              type="button"
              className="close-player-btn"
              onClick={() => setSelectedFile(null)}
              disabled={isUploading}
              title="Remove file"
            >
              &times;
            </button>
          </div>
        )}

        {/* Progress bar */}
        {isUploading && (
          <div className="progress-container">
            <div className="progress-bar-bg">
              <div className="progress-bar-fill" style={{ width: `${uploadProgress}%` }} />
            </div>
            <div className="progress-label">
              <span>Uploading to server...</span>
              <span>{uploadProgress}%</span>
            </div>
          </div>
        )}

        {/* Action button */}
        <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <Button variant="secondary" onClick={() => onNavigate('dashboard')} disabled={isUploading}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleUpload}
            loading={isUploading}
            disabled={!selectedFile || isUploading}
          >
            {isUploading ? `Uploading (${uploadProgress}%)` : 'Upload File'}
          </Button>
        </div>
      </div>
    </div>
  );
}

export default UploadScreen;

