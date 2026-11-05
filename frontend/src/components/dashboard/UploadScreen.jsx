import React, { useState, useRef } from 'react';
import documentService from '../../api/documentService';
import './Dashboard.css';

const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25 MB
const ALLOWED_EXTENSIONS = ['pdf', 'docx', 'txt', 'pptx', 'epub', 'rtf'];

/**
 * Upload Document Screen
 * Supports drag-and-drop, format validation, size checks, mode/language selection,
 * real FastAPI backend processing, and immediate transition to results reader.
 */
export function UploadScreen({
  onUploadSuccess,
  onNavigateToLibrary,
}) {
  const [file, setFile] = useState(null);
  const [mode, setMode] = useState('document');
  const [targetLanguage, setTargetLanguage] = useState('en');
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [progressStage, setProgressStage] = useState('');
  const [errorMessage, setErrorMessage] = useState(null);
  const fileInputRef = useRef(null);

  const getFileExtension = (filename) => {
    return filename.split('.').pop().toLowerCase();
  };

  const validateFile = (selectedFile) => {
    if (!selectedFile) return false;

    const ext = getFileExtension(selectedFile.name);
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setErrorMessage(`Unsupported format .${ext}. Please upload PDF, DOCX, TXT, PPTX, EPUB, or RTF.`);
      return false;
    }

    if (selectedFile.size > MAX_FILE_SIZE) {
      setErrorMessage(`File exceeds 25 MB limit (${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB). Please select a smaller file.`);
      return false;
    }

    setErrorMessage(null);
    return true;
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && validateFile(selectedFile)) {
      setFile(selectedFile);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile && validateFile(droppedFile)) {
      setFile(droppedFile);
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
    setErrorMessage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const handleUploadAndProcess = async () => {
    if (!file) return;

    setIsUploading(true);
    setErrorMessage(null);
    setUploadProgress(15);
    setProgressStage('Uploading file securely to server...');

    try {
      // Advance stage animation
      const stageTimer1 = setTimeout(() => {
        setUploadProgress(45);
        setProgressStage('Parsing document structure & detecting chapters...');
      }, 500);

      const stageTimer2 = setTimeout(() => {
        setUploadProgress(75);
        setProgressStage('Extracting Unicode text (English, Tamil, Sinhala)...');
      }, 1000);

      const result = await documentService.uploadDocument(file, mode, targetLanguage);

      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      setUploadProgress(100);
      setProgressStage('Extraction complete! Loading reader...');

      // Transition to results screen
      setTimeout(() => {
        onUploadSuccess(result);
      }, 500);
    } catch (err) {
      setErrorMessage(err.message || 'Document processing failed. Please check the file and try again.');
      setIsUploading(false);
      setUploadProgress(0);
      setProgressStage('');
    }
  };

  return (
    <div className="dashboard-view-container">
      <div className="upload-container">
        <div className="upload-card">
          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <h2 style={{ fontSize: '22px', fontWeight: '700', color: 'var(--text-h)', margin: '0 0 6px' }}>
              Upload Document for Audiobook Generation
            </h2>
            <p style={{ fontSize: '14px', color: 'var(--text)', margin: 0 }}>
              Upload any document to extract text, detect chapters, and prepare your audiobook.
            </p>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#dc2626',
              borderRadius: '8px',
              padding: '12px 16px',
              fontSize: '13.5px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}>
              <span>{errorMessage}</span>
              <button
                type="button"
                onClick={() => setErrorMessage(null)}
                style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', fontWeight: 'bold' }}
              >
                &times;
              </button>
            </div>
          )}

          {/* Drag & Drop Area */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt,.pptx,.epub,.rtf"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />

          {!file ? (
            <div
              className={`upload-dropzone ${isDragging ? 'dragging' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="upload-icon-large">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </div>
              <div className="dropzone-title">Drag & drop your document here</div>
              <div className="dropzone-subtitle">or choose a file from your computer</div>
              <button type="button" className="dropzone-browse-btn">
                Browse Files
              </button>

              <div className="upload-format-chips">
                <span className="format-chip">PDF</span>
                <span className="format-chip">DOCX</span>
                <span className="format-chip">TXT</span>
                <span className="format-chip">PPTX</span>
                <span className="format-chip">EPUB</span>
                <span className="format-chip">RTF</span>
                <span className="format-chip" style={{ color: 'var(--accent)', borderColor: 'var(--accent-border)' }}>
                  Max 25 MB
                </span>
              </div>
            </div>
          ) : (
            <div className="upload-file-preview">
              <div className="file-preview-info">
                <span className={`format-pill ${getFileExtension(file.name)}`}>
                  {getFileExtension(file.name).toUpperCase()}
                </span>
                <div>
                  <div className="file-preview-name">{file.name}</div>
                  <div className="file-preview-size">{formatFileSize(file.size)}</div>
                </div>
              </div>
              {!isUploading && (
                <button
                  type="button"
                  className="file-remove-btn"
                  onClick={handleRemoveFile}
                  title="Remove file"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              )}
            </div>
          )}

          {/* Options Row */}
          <div className="upload-options-row">
            <div className="upload-field-group">
              <label htmlFor="processing-mode" className="upload-field-label">
                Processing Mode
              </label>
              <select
                id="processing-mode"
                className="upload-select"
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                disabled={isUploading}
              >
                <option value="document">Standard Document Parser (Fast & Structured)</option>
                <option value="ocr">OCR Enhanced (For scanned pages & images)</option>
              </select>
            </div>

            <div className="upload-field-group">
              <label htmlFor="target-lang" className="upload-field-label">
                Document Language
              </label>
              <select
                id="target-lang"
                className="upload-select"
                value={targetLanguage}
                onChange={(e) => setTargetLanguage(e.target.value)}
                disabled={isUploading}
              >
                <option value="en">English</option>
                <option value="ta">Tamil (தமிழ்)</option>
                <option value="si">Sinhala (සිංහල)</option>
                <option value="auto">Auto-detect Language</option>
              </select>
            </div>
          </div>

          {/* Progress Indicator */}
          {isUploading && (
            <div className="upload-progress-container">
              <div className="upload-progress-bar">
                <div className="upload-progress-fill" style={{ width: `${uploadProgress}%` }} />
              </div>
              <div className="upload-progress-status">
                <span>{progressStage}</span>
                <span>{uploadProgress}%</span>
              </div>
            </div>
          )}

          {/* Upload Button */}
          <button
            type="button"
            className="upload-submit-btn"
            onClick={handleUploadAndProcess}
            disabled={!file || isUploading}
          >
            {isUploading ? (
              <>
                <span className="btn-spinner" aria-hidden="true" />
                <span>Processing Document...</span>
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                <span>Upload & Process Document</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default UploadScreen;
