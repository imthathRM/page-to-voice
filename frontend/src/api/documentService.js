import axiosInstance from './axiosClient';

export const documentService = {
  /**
   * Upload a document using Axios and FormData with upload progress tracking
   * @param {File} file
   * @param {Function} [onProgress] - Callback (progressPercent: number)
   * @returns {Promise<Object>}
   */
  async uploadDocument(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axiosInstance.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentCompleted);
        }
      },
    });
    return response.data;
  },

  /**
   * Get all documents for the current user
   */
  async getDocuments() {
    const response = await axiosInstance.get('/api/documents');
    return response.data;
  },

  /**
   * Get document details and its chapters
   */
  async getDocument(documentId) {
    const response = await axiosInstance.get(`/api/documents/${documentId}`);
    return response.data;
  },

  /**
   * Trigger document extraction and chapter detection
   */
  async processDocument(documentId) {
    const response = await axiosInstance.post(`/api/documents/${documentId}/process`);
    return response.data;
  },

  /**
   * Clean text for voice narration using Gemini AI
   */
  async cleanText({ text, language = 'en', chapterId }) {
    const response = await axiosInstance.post('/api/ai/clean-text', {
      text,
      language,
      chapter_id: chapterId,
    });
    return response.data;
  },

  /**
   * Generate chapter summary using Gemini AI
   */
  async summarizeText({ text, language = 'en', chapterId }) {
    const response = await axiosInstance.post('/api/ai/summarize', {
      text,
      language,
      chapter_id: chapterId,
    });
    return response.data;
  },

  /**
   * Translate text between English, Tamil, and Sinhala
   */
  async translateText({ text, sourceLanguage = 'en', targetLanguage, chapterId }) {
    const response = await axiosInstance.post('/api/ai/translate', {
      text,
      source_language: sourceLanguage,
      target_language: targetLanguage,
      chapter_id: chapterId,
    });
    return response.data;
  },

  /**
   * Generate speech audio for a chapter (Azure TTS / Gemini / gTTS)
   */
  async generateTTS({ chapterId, text, language = 'en', voiceName }) {
    const response = await axiosInstance.post('/api/tts/generate', {
      chapter_id: chapterId,
      text,
      language,
      voice_name: voiceName,
    });
    return response.data;
  },

  /**
   * Start background audiobook generation with Chapter 1 Priority
   */
  async generateAudiobook(documentId, { voiceName, language, forceRegenerate = false } = {}) {
    const response = await axiosInstance.post(`/api/documents/${documentId}/generate-audio`, {
      voice_name: voiceName,
      language,
      force_regenerate: forceRegenerate,
    });
    return response.data;
  },

  /**
   * Poll live chapter-level generation progress for an audiobook
   */
  async getAudiobookProgress(documentId) {
    const response = await axiosInstance.get(`/api/documents/${documentId}/audio-progress`);
    return response.data;
  },

  /**
   * Retry generating audio for a specific failed chapter
   */
  async retryChapterAudio(chapterId) {
    const response = await axiosInstance.post(`/api/chapters/${chapterId}/retry-audio`);
    return response.data;
  },

  /**
   * Fetch available voices for selected language and active provider
   */
  async getAvailableVoices(language = 'en') {
    const response = await axiosInstance.get(`/api/tts/voices`, {
      params: { language },
    });
    return response.data;
  },

  /**
   * Prioritize a specific chapter in the background generation queue
   */
  async prioritizeChapter(chapterId) {
    const response = await axiosInstance.post(`/api/chapters/${chapterId}/prioritize`);
    return response.data;
  },

  /**
   * Returns stream URL for real-time instant playback
   */
  getChapterStreamUrl(chapterId) {
    return `/api/chapters/${chapterId}/stream`;
  },
};

export default documentService;



