import { useState, useEffect, useRef } from 'react';
import Button from '../common/Button/Button';
import LoadingSpinner from '../common/LoadingSpinner/LoadingSpinner';
import Alert from '../common/Alert/Alert';
import Modal from '../common/Modal/Modal';
import documentService from '../../api/documentService';
import './Screens.css';

export function DocumentDetailScreen({ documentId, onNavigate, onPlayAudio }) {
  const [doc, setDoc] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Active AI action states
  const [activeActionChapter, setActiveActionChapter] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [summaryModal, setSummaryModal] = useState({ open: false, title: '', content: '' });
  const [translateModal, setTranslateModal] = useState({ open: false, chapter: null, targetLang: 'ta' });
  const [viewModes, setViewModes] = useState({}); // { [chapterId]: 'processed' | 'original' }

  // Audiobook Batch Generation & Voice states
  const [audiobookProgress, setAudiobookProgress] = useState(null);
  const [isGeneratingAudiobook, setIsGeneratingAudiobook] = useState(false);
  const [voiceModalOpen, setVoiceModalOpen] = useState(false);
  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState('');
  const [voiceProvider, setVoiceProvider] = useState('azure');
  const pollTimerRef = useRef(null);
  const autoPlayPendingRef = useRef(false);


  const fetchDocument = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await documentService.getDocument(documentId);
      setDoc(data);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to load document details.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    if (documentId) {
      documentService
        .getDocument(documentId)
        .then((data) => {
          if (isMounted) setDoc(data);
        })
        .catch((err) => {
          if (isMounted) setErrorMsg(err.message || 'Failed to load document details.');
        })
        .finally(() => {
          if (isMounted) setIsLoading(false);
        });
    }
    return () => {
      isMounted = false;
    };
  }, [documentId]);

  // Load available voices when document is loaded
  useEffect(() => {
    if (doc?.source_language) {
      documentService
        .getAvailableVoices(doc.source_language)
        .then((res) => {
          setAvailableVoices(res.voices || []);
          setVoiceProvider(res.provider || 'azure');
          if (res.voices && res.voices.length > 0) {
            setSelectedVoice(res.voices[0].name);
          }
        })
        .catch((err) => {
          console.warn('Could not load voices:', err);
        });
    }
  }, [doc?.source_language]);

  // Audiobook progress polling effect
  useEffect(() => {
    if (!isGeneratingAudiobook || !documentId) {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
      return;
    }

    const pollProgress = async () => {
      try {
        const progressData = await documentService.getAudiobookProgress(documentId);
        setAudiobookProgress(progressData);

        // Update local document chapter audio states as they complete
        if (progressData?.chapters) {
          setDoc((prev) => {
            if (!prev) return prev;
            const updatedChaps = prev.chapters.map((ch) => {
              const matched = progressData.chapters.find((p) => p.chapter_id === ch.id);
              if (matched && matched.audio_url && matched.audio_url !== ch.audio_file_url) {
                return {
                  ...ch,
                  audio_file_url: matched.audio_url,
                  duration_seconds: matched.duration_seconds,
                };
              }
              return ch;
            });
            return { ...prev, chapters: updatedChaps };
          });
        }

        // Auto-play Chapter 1 when ready if user just launched generation
        if (autoPlayPendingRef.current && progressData?.chapters) {
          const chap1 = progressData.chapters.find((p) => p.chapter_number === 1);
          if (chap1 && chap1.audio_url && onPlayAudio) {
            autoPlayPendingRef.current = false;
            onPlayAudio({
              title: chap1.title || 'Chapter 1',
              chapter_number: 1,
              audio_url: chap1.audio_url,
              duration_seconds: chap1.duration_seconds,
              documentTitle: doc?.title,
              text: doc?.chapters?.[0]?.processed_text || doc?.chapters?.[0]?.original_text,
              playlist: doc?.chapters || [],
              currentIndex: 0,
            });
            setSuccessMsg('Chapter 1 is ready! Immediate playback started.');
          }
        }

        if (progressData.status === 'completed' || progressData.overall_progress_percent === 100) {
          setIsGeneratingAudiobook(false);
          setSuccessMsg('Audiobook generation completed! All chapters are ready to listen.');
          if (pollTimerRef.current) clearInterval(pollTimerRef.current);
        }

      } catch (err) {
        console.warn('Progress polling error:', err);
      }
    };

    pollProgress();
    pollTimerRef.current = setInterval(pollProgress, 2500);

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [isGeneratingAudiobook, documentId]);

  const handleProcessDocument = async () => {
    setIsProcessing(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const result = await documentService.processDocument(documentId);
      setSuccessMsg(result.message);
      await fetchDocument();
    } catch (err) {
      setErrorMsg(err.message || 'Processing failed.');
    } finally {
      setIsProcessing(false);
    }
  };

  const toggleViewMode = (chapterId) => {
    setViewModes((prev) => ({
      ...prev,
      [chapterId]: prev[chapterId] === 'original' ? 'processed' : 'original',
    }));
  };

  const handleCleanText = async (chapter) => {
    setActionLoading(true);
    setActiveActionChapter(chapter.id);
    setErrorMsg(null);
    try {
      const sourceText = chapter.processed_text || chapter.original_text;
      const res = await documentService.cleanText({
        text: sourceText,
        language: doc.source_language || 'en',
        chapterId: chapter.id,
      });
      setDoc((prev) => ({
        ...prev,
        chapters: prev.chapters.map((c) =>
          c.id === chapter.id ? { ...c, processed_text: res.cleaned_text } : c
        ),
      }));
      setSuccessMsg(`Chapter ${chapter.chapter_number} narration text cleaned by Gemini AI.`);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to clean text.');
    } finally {
      setActionLoading(false);
      setActiveActionChapter(null);
    }
  };

  const handleSummarize = async (chapter) => {
    setActionLoading(true);
    setActiveActionChapter(chapter.id);
    setErrorMsg(null);
    try {
      const sourceText = chapter.processed_text || chapter.original_text;
      const res = await documentService.summarizeText({
        text: sourceText,
        language: doc.source_language || 'en',
        chapterId: chapter.id,
      });
      setSummaryModal({
        open: true,
        title: `Summary - ${chapter.title || `Chapter ${chapter.chapter_number}`}`,
        content: res.summary,
      });
    } catch (err) {
      setErrorMsg(err.message || 'Summarization failed.');
    } finally {
      setActionLoading(false);
      setActiveActionChapter(null);
    }
  };

  const handleOpenTranslate = (chapter) => {
    const defaultTarget = doc.source_language === 'en' ? 'ta' : 'en';
    setTranslateModal({
      open: true,
      chapter,
      targetLang: defaultTarget,
    });
  };

  const handleExecuteTranslate = async () => {
    const chapter = translateModal.chapter;
    if (!chapter) return;

    setActionLoading(true);
    setErrorMsg(null);
    try {
      const sourceText = chapter.processed_text || chapter.original_text;
      const res = await documentService.translateText({
        text: sourceText,
        sourceLanguage: doc.source_language || 'en',
        targetLanguage: translateModal.targetLang,
        chapterId: chapter.id,
      });
      setDoc((prev) => ({
        ...prev,
        chapters: prev.chapters.map((c) =>
          c.id === chapter.id ? { ...c, processed_text: res.translated_text } : c
        ),
      }));
      setTranslateModal({ open: false, chapter: null, targetLang: 'ta' });
      setSuccessMsg(
        `Chapter ${chapter.chapter_number} translated to ${translateModal.targetLang.toUpperCase()} successfully!`
      );
    } catch (err) {
      setErrorMsg(err.message || 'Translation failed.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleGenerateSingleTTS = async (chapter) => {
    setActionLoading(true);
    setActiveActionChapter(chapter.id);
    setErrorMsg(null);
    try {
      const res = await documentService.generateTTS({
        chapterId: chapter.id,
        text: chapter.processed_text || chapter.original_text,
        language: doc.source_language || 'en',
        voiceName: selectedVoice || undefined,
      });
      setDoc((prev) => ({
        ...prev,
        chapters: prev.chapters.map((c) =>
          c.id === chapter.id
            ? { ...c, audio_file_url: res.audio_url, duration_seconds: res.duration_seconds }
            : c
        ),
      }));
      setSuccessMsg(`Audio generated for Chapter ${chapter.chapter_number} (${res.provider}, ${res.duration_seconds}s)!`);

      if (onPlayAudio) {
        const cIndex = doc.chapters.findIndex((c) => c.id === chapter.id);
        onPlayAudio({
          title: chapter.title,
          chapter_number: chapter.chapter_number,
          audio_url: res.audio_url,
          duration_seconds: res.duration_seconds,
          documentTitle: doc.title,
          text: chapter.processed_text || chapter.original_text,
          playlist: doc.chapters,
          currentIndex: cIndex >= 0 ? cIndex : 0,
        });
      }
    } catch (err) {
      setErrorMsg(err.message || 'TTS generation failed.');
    } finally {
      setActionLoading(false);
      setActiveActionChapter(null);
    }
  };

  const handleStartAudiobookGeneration = async () => {
    setVoiceModalOpen(false);
    setIsGeneratingAudiobook(true);
    autoPlayPendingRef.current = true;
    setErrorMsg(null);
    setSuccessMsg('Audiobook synthesis started. Chapter 1 is prioritized and will auto-play as soon as ready!');
    try {
      await documentService.generateAudiobook(documentId, {
        voiceName: selectedVoice || undefined,
        language: doc.source_language || 'en',
      });
    } catch (err) {
      setIsGeneratingAudiobook(false);
      autoPlayPendingRef.current = false;
      setErrorMsg(err.message || 'Failed to start audiobook generation.');
    }
  };

  const handleRetryChapter = async (chapter) => {
    setActionLoading(true);
    setActiveActionChapter(chapter.id);
    setErrorMsg(null);
    try {
      const res = await documentService.retryChapterAudio(chapter.id);
      setDoc((prev) => ({
        ...prev,
        chapters: prev.chapters.map((c) =>
          c.id === chapter.id
            ? { ...c, audio_file_url: res.audio_url, duration_seconds: res.duration_seconds }
            : c
        ),
      }));
      setSuccessMsg(`Chapter ${chapter.chapter_number} audio re-generated successfully!`);
    } catch (err) {
      setErrorMsg(err.message || 'Retry generation failed.');
    } finally {
      setActionLoading(false);
      setActiveActionChapter(null);
    }
  };

  const handlePlayChapterAudio = (chap) => {
    if (!onPlayAudio || !chap.audio_file_url) return;
    const currentIndex = doc.chapters.findIndex((c) => c.id === chap.id);
    onPlayAudio({
      title: chap.title,
      chapter_number: chap.chapter_number,
      audio_url: chap.audio_file_url,
      duration_seconds: chap.duration_seconds,
      documentTitle: doc.title,
      text: chap.processed_text || chap.original_text,
      playlist: doc.chapters,
      currentIndex: currentIndex >= 0 ? currentIndex : 0,
    });
  };

  const handleStreamChapterAudio = async (chap) => {
    if (!onPlayAudio) return;
    try {
      await documentService.prioritizeChapter(chap.id);
    } catch (e) {
      // non-fatal
    }
    const currentIndex = doc.chapters.findIndex((c) => c.id === chap.id);
    const streamUrl = documentService.getChapterStreamUrl(chap.id);
    onPlayAudio({
      title: chap.title,
      chapter_number: chap.chapter_number,
      audio_url: streamUrl,
      duration_seconds: chap.duration_seconds || 60,
      documentTitle: doc.title,
      text: chap.processed_text || chap.original_text,
      playlist: doc.chapters,
      currentIndex: currentIndex >= 0 ? currentIndex : 0,
      isStreaming: true,
    });
  };

  const handlePrioritizeChapter = async (chap) => {
    try {
      await documentService.prioritizeChapter(chap.id);
      setSuccessMsg(`Chapter #${chap.chapter_number} prioritized in background generation!`);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to prioritize chapter.');
    }
  };


  // Helper to determine chapter badge
  const getChapterProgressStatus = (chap) => {
    if (chap.audio_file_url) return { status: 'completed', label: 'Audio Ready' };
    if (audiobookProgress?.chapters) {
      const p = audiobookProgress.chapters.find((item) => item.chapter_id === chap.id);
      if (p) {
        if (p.status === 'processing') return { status: 'processing', label: 'Synthesizing...' };
        if (p.status === 'failed') return { status: 'failed', label: 'Failed' };
        if (p.status === 'completed') return { status: 'completed', label: 'Audio Ready' };
      }
    }
    if (isGeneratingAudiobook) return { status: 'pending', label: 'Queued' };
    return { status: 'pending', label: 'No Audio' };
  };

  if (isLoading) {
    return (
      <div className="screen-container">
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <LoadingSpinner size="lg" />
          <p style={{ marginTop: '16px', color: '#64748b' }}>Loading document...</p>
        </div>
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="screen-container">
        <Alert type="error" title="Not Found">
          Document could not be located.
          <Button style={{ marginTop: '12px' }} onClick={() => onNavigate('dashboard')}>
            Back to Dashboard
          </Button>
        </Alert>
      </div>
    );
  }

  const completedCount = doc.chapters?.filter((c) => c.audio_file_url).length || 0;
  const totalCount = doc.chapters?.length || 0;
  const overallPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return (
    <div className="screen-container">
      <div className="detail-view-wrap">
        {/* Navigation Breadcrumb */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Button variant="outline" size="sm" onClick={() => onNavigate('dashboard')}>
            &larr; Back to Dashboard
          </Button>
          <div className="doc-badge-group">
            <span className="file-type-pill">{doc.file_type}</span>
            <span className={`status-badge ${doc.status}`}>{doc.status}</span>
          </div>
        </div>

        {errorMsg && (
          <Alert type="error" title="Error" onClose={() => setErrorMsg(null)}>
            {errorMsg}
          </Alert>
        )}

        {successMsg && (
          <Alert type="success" title="Success" onClose={() => setSuccessMsg(null)}>
            {successMsg}
          </Alert>
        )}

        {/* Document Header Card */}
        <div className="detail-view-header">
          <div>
            <h1 className="auth-card-title" style={{ fontSize: '24px', margin: 0 }}>
              {doc.title}
            </h1>
            <div style={{ display: 'flex', gap: '16px', marginTop: '8px', fontSize: '13px', color: '#64748b' }}>
              <span>Uploaded: {new Date(doc.created_at).toLocaleDateString()}</span>
              <span>Chapters: {totalCount}</span>
              <span>Language: <strong>{doc.source_language?.toUpperCase()}</strong></span>
              <span>Audio: <strong>{completedCount} / {totalCount} ready</strong></span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <Button
              variant="outline"
              onClick={handleProcessDocument}
              loading={isProcessing}
              disabled={isProcessing || isGeneratingAudiobook}
            >
              {totalCount > 0 ? 'Re-Detect Chapters' : 'Detect Chapters'}
            </Button>

            {totalCount > 0 && (
              <Button
                variant="primary"
                onClick={() => setVoiceModalOpen(true)}
                loading={isGeneratingAudiobook}
                disabled={isGeneratingAudiobook || totalCount === 0}
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '6px' }}>
                  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
                </svg>
                {completedCount === totalCount ? 'Regenerate Full Audiobook' : 'Generate Full Audiobook'}
              </Button>
            )}
          </div>
        </div>

        {/* Live Audiobook Generation Banner */}
        {(isGeneratingAudiobook || (audiobookProgress && audiobookProgress.status === 'processing')) && (
          <div className="audiobook-banner" role="status" aria-live="polite">
            <div className="audiobook-banner-header">
              <div className="audiobook-banner-title">
                <span className="pulse-indicator" />
                <span>
                  Synthesizing Audiobook with Microsoft Azure AI Speech (Chapter 1 Priority)
                </span>
              </div>
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#0369a1' }}>
                {audiobookProgress?.completed_chapters ?? completedCount} of {totalCount} Chapters Complete ({audiobookProgress?.overall_progress_percent ?? overallPercent}%)
              </span>
            </div>

            <div className="progress-bar-bg" style={{ height: '10px' }}>
              <div
                className="progress-bar-fill"
                style={{ width: `${audiobookProgress?.overall_progress_percent ?? overallPercent}%` }}
              />
            </div>

            <div style={{ fontSize: '12px', color: '#0284c7', display: 'flex', justifyContent: 'space-between' }}>
              <span>
                First chapter is prioritized so you can listen while remaining chapters generate in the background.
              </span>
              <span>Provider: <strong>{voiceProvider.toUpperCase()}</strong></span>
            </div>
          </div>
        )}

        {/* Chapters Section */}
        <div>
          <div className="section-header">
            <h2 className="section-title">Chapters ({totalCount})</h2>
            {totalCount === 0 && !isProcessing && (
              <span style={{ fontSize: '13px', color: '#94a3b8' }}>
                Click &apos;Detect Chapters&apos; to extract document text.
              </span>
            )}
          </div>

          {totalCount === 0 ? (
            <div className="account-card" style={{ textAlign: 'center', padding: '36px' }}>
              <p style={{ color: '#64748b', margin: '0 0 16px' }}>
                This document has not been parsed into chapters yet.
              </p>
              <Button variant="primary" onClick={handleProcessDocument} loading={isProcessing}>
                Start Text Extraction
              </Button>
            </div>
          ) : (
            doc.chapters.map((chap) => {
              const currentMode = viewModes[chap.id] || 'processed';
              const displayText =
                currentMode === 'original' ? chap.original_text : (chap.processed_text || chap.original_text);
              const isWorking = actionLoading && activeActionChapter === chap.id;
              const statusInfo = getChapterProgressStatus(chap);

              return (
                <div key={chap.id} className="chapter-card">
                  <div className="chapter-card-header">
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                        <h3 style={{ margin: 0, fontSize: '15px', color: '#0f172a' }}>
                          {chap.title || `Chapter ${chap.chapter_number}`}
                        </h3>
                        <span className={`chapter-status-pill ${statusInfo.status}`}>
                          {statusInfo.status === 'processing' && <span className="pulse-indicator" style={{ width: '6px', height: '6px' }} />}
                          {statusInfo.label}
                        </span>
                      </div>
                      <span style={{ fontSize: '12px', color: '#64748b' }}>
                        Chapter #{chap.chapter_number} &bull;{' '}
                        {chap.duration_seconds > 0
                          ? `Audio: ${Math.round(chap.duration_seconds)}s duration`
                          : 'No audio generated yet'}
                      </span>
                    </div>

                    <div className="chapter-toolbar">
                      {/* Play Button if audio available */}
                      {chap.audio_file_url ? (
                        <button
                          type="button"
                          className="btn-tool primary"
                          onClick={() => handlePlayChapterAudio(chap)}
                          title="Play Chapter Audio"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M5 3l14 9-14 9V3z" />
                          </svg>
                          <span>Play Audio</span>
                        </button>
                      ) : (
                        /* Live Streaming Audio Option */
                        <button
                          type="button"
                          className="btn-tool primary"
                          onClick={() => handleStreamChapterAudio(chap)}
                          title="Stream audio instantly without waiting for completion"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                            <polygon points="5 3 19 12 5 21 5 3" />
                          </svg>
                          <span>Stream & Listen Now</span>
                        </button>
                      )}

                      {/* Prioritize button if chapter is queued */}
                      {!chap.audio_file_url && isGeneratingAudiobook && statusInfo.status === 'pending' && (
                        <button
                          type="button"
                          className="btn-tool"
                          onClick={() => handlePrioritizeChapter(chap)}
                          title="Move this chapter to top of the synthesis queue"
                        >
                          ⚡ Prioritize
                        </button>
                      )}


                      {/* Retry Button if chapter generation failed */}
                      {statusInfo.status === 'failed' && (
                        <button
                          type="button"
                          className="btn-tool"
                          style={{ borderColor: '#ef4444', color: '#b91c1c' }}
                          onClick={() => handleRetryChapter(chap)}
                          disabled={isWorking}
                        >
                          &#x21bb; Retry Chapter
                        </button>
                      )}

                      {/* Generate Speech TTS */}
                      <button
                        type="button"
                        className="btn-tool"
                        onClick={() => handleGenerateSingleTTS(chap)}
                        disabled={isWorking || isGeneratingAudiobook}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                          <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
                        </svg>
                        <span>{chap.audio_file_url ? 'Regenerate Audio' : 'Generate Audio (TTS)'}</span>
                      </button>

                      {/* Clean for Narration */}
                      <button
                        type="button"
                        className="btn-tool"
                        onClick={() => handleCleanText(chap)}
                        disabled={isWorking}
                      >
                        ✨ Clean with AI
                      </button>

                      {/* Summarize */}
                      <button
                        type="button"
                        className="btn-tool"
                        onClick={() => handleSummarize(chap)}
                        disabled={isWorking}
                      >
                        📝 Summarize
                      </button>

                      {/* Translate */}
                      <button
                        type="button"
                        className="btn-tool"
                        onClick={() => handleOpenTranslate(chap)}
                        disabled={isWorking}
                      >
                        🌐 Translate
                      </button>

                      {/* View Mode Toggle */}
                      <button
                        type="button"
                        className="btn-tool"
                        onClick={() => toggleViewMode(chap.id)}
                      >
                        {currentMode === 'original' ? 'Show Cleaned Text' : 'Show Original Text'}
                      </button>
                    </div>
                  </div>

                  <div className="chapter-card-body">
                    {isWorking && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', color: '#4f46e5', fontSize: '13px' }}>
                        <LoadingSpinner size="sm" />
                        <span>Processing AI request...</span>
                      </div>
                    )}
                    <div className="chapter-text-content">
                      {displayText || 'No text extracted for this chapter.'}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Voice Selection & Audiobook Launch Modal */}
      <Modal
        isOpen={voiceModalOpen}
        onClose={() => setVoiceModalOpen(false)}
        title="Generate Full Audiobook"
        footer={
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <Button variant="secondary" onClick={() => setVoiceModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleStartAudiobookGeneration}>
              Start Generation (Chapter 1 Priority)
            </Button>
          </div>
        }
      >
        <div>
          <p style={{ margin: '0 0 16px', fontSize: '14px', color: '#475569' }}>
            Generate high-fidelity audio for all <strong>{totalCount}</strong> chapters using{' '}
            <strong>Microsoft Azure AI Speech</strong>. The first chapter is synthesized first so you can begin listening immediately.
          </p>

          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '14px' }}>
            Select Narration Voice ({doc.source_language?.toUpperCase()}):
          </label>
          <select
            value={selectedVoice}
            onChange={(e) => setSelectedVoice(e.target.value)}
            style={{
              width: '100%',
              padding: '10px',
              borderRadius: '8px',
              border: '1px solid #cbd5e1',
              fontSize: '14px',
              background: '#ffffff',
            }}
          >
            {availableVoices.length > 0 ? (
              availableVoices.map((v) => (
                <option key={v.name} value={v.name}>
                  {v.label} ({v.gender})
                </option>
              ))
            ) : (
              <option value="en-US-JennyNeural">Jenny (en-US Neural Default)</option>
            )}
          </select>

          <div style={{ marginTop: '16px', padding: '12px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px', color: '#64748b' }}>
            <p style={{ margin: '0 0 6px' }}><strong>Narration Engine:</strong> Microsoft Azure AI Speech (Primary) with Google Gemini / gTTS fallback.</p>
            <p style={{ margin: 0 }}><strong>Format:</strong> Studio-quality MP3 (24kHz 160kbps mono) compatible with all modern browsers.</p>
          </div>
        </div>
      </Modal>

      {/* Chapter Summary Modal */}
      <Modal
        isOpen={summaryModal.open}
        onClose={() => setSummaryModal({ open: false, title: '', content: '' })}
        title={summaryModal.title}
      >
        <div style={{ fontSize: '14px', lineHeight: 1.6, color: '#334155', whiteSpace: 'pre-wrap' }}>
          {summaryModal.content}
        </div>
      </Modal>

      {/* Translation Modal */}
      <Modal
        isOpen={translateModal.open}
        onClose={() => setTranslateModal({ open: false, chapter: null, targetLang: 'ta' })}
        title={`Translate Chapter #${translateModal.chapter?.chapter_number}`}
        footer={
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <Button
              variant="secondary"
              onClick={() => setTranslateModal({ open: false, chapter: null, targetLang: 'ta' })}
              disabled={actionLoading}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleExecuteTranslate}
              loading={actionLoading}
              disabled={actionLoading}
            >
              Translate Chapter
            </Button>
          </div>
        }
      >
        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '14px' }}>
            Select Target Language:
          </label>
          <select
            value={translateModal.targetLang}
            onChange={(e) =>
              setTranslateModal((prev) => ({ ...prev, targetLang: e.target.value }))
            }
            style={{
              width: '100%',
              padding: '10px',
              borderRadius: '8px',
              border: '1px solid #cbd5e1',
              fontSize: '14px',
              background: '#ffffff',
            }}
          >
            <option value="en">English (English)</option>
            <option value="ta">Tamil (தமிழ்)</option>
            <option value="si">Sinhala (සිංහල)</option>
          </select>
          <p style={{ marginTop: '12px', fontSize: '12px', color: '#64748b' }}>
            Translation is powered by Google Gemini AI with high preservation of linguistic nuance and natural audiobook phrasing.
          </p>
        </div>
      </Modal>
    </div>
  );
}

export default DocumentDetailScreen;
