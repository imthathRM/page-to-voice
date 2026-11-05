/**
 * Page to Voice - Document Processing & Management Service
 *
 * Communicates with FastAPI backend endpoints:
 * - POST   /documents/upload    (multipart file upload and extraction)
 * - GET    /documents           (list user documents with filters)
 * - GET    /documents/:id       (detailed document view with chapters)
 * - DELETE /documents/:id       (delete document)
 * - GET    /dashboard/stats     (user aggregated statistics)
 */

import apiClient from './apiClient';

export const documentService = {
  /**
   * Upload and process a document file
   * @param {File} file - Document file (PDF, DOCX, TXT, PPTX, EPUB, RTF)
   * @param {Object} options - { mode, sourceLanguage, targetLanguage }
   * @returns {Promise<Object>} Processed DocumentDetailResponse
   */
  async uploadDocument(file, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', options.mode || 'document');
    formData.append('source_language', options.sourceLanguage || 'en');
    if (options.targetLanguage) {
      formData.append('target_language', options.targetLanguage);
    }

    return await apiClient.upload('/documents/upload', formData);
  },

  /**
   * Fetch all documents for current user
   * @param {Object} [filters={}] - { search, fileType, statusFilter }
   * @returns {Promise<Array>} List of DocumentListItem
   */
  async getDocuments(filters = {}) {
    const params = new URLSearchParams();
    if (filters.search) params.append('search', filters.search);
    if (filters.fileType && filters.fileType !== 'all') params.append('file_type', filters.fileType);
    if (filters.statusFilter && filters.statusFilter !== 'all') params.append('status_filter', filters.statusFilter);

    const queryStr = params.toString() ? `?${params.toString()}` : '';
    return await apiClient.get(`/documents${queryStr}`);
  },

  /**
   * Retrieve single document details including chapters and raw extracted text
   * @param {number|string} documentId
   * @returns {Promise<Object>} DocumentDetailResponse
   */
  async getDocumentById(documentId) {
    return await apiClient.get(`/documents/${documentId}`);
  },

  /**
   * Delete a document
   * @param {number|string} documentId
   * @returns {Promise<Object>} { status, message }
   */
  async deleteDocument(documentId) {
    return await apiClient.delete(`/documents/${documentId}`);
  },

  /**
   * Retrieve aggregated dashboard metrics and recent activity for the authenticated user
   * @returns {Promise<Object>} DashboardStatsResponse
   */
  async getDashboardStats() {
    return await apiClient.get('/dashboard/stats');
  },
};

export default documentService;
