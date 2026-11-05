import { useState, useRef, useEffect } from 'react';
import './AudioPlayer.css';

/**
 * Global audio player component for listening to generated chapter audio.
 *
 * @param {Object} props
 * @param {Object} props.audio - { title, audio_url, chapter_number, text, duration_seconds }
 * @param {Function} props.onClose - Callback to close player
 */
export function AudioPlayer({ audio, onClose, onNextTrack, onPrevTrack, hasNext = false, hasPrev = false }) {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(audio.duration_seconds || 0);
  const [isTextOpen, setIsTextOpen] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    if (audioRef.current && audio?.audio_url) {
      setCurrentTime(0);
      setErrorMsg(null);
      audioRef.current.load();
      audioRef.current
        .play()
        .then(() => setIsPlaying(true))
        .catch(() => setIsPlaying(false));
    }
  }, [audio?.audio_url]);

  const handleEnded = () => {
    setIsPlaying(false);
    if (onNextTrack && hasNext) {
      onNextTrack();
    }
  };


  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current
        .play()
        .then(() => setIsPlaying(true))
        .catch(() => {
          setErrorMsg('Failed to play audio. Please check network connectivity.');
          setIsPlaying(false);
        });
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration || audio.duration_seconds || 0);
    }
  };

  const handleSeek = (e) => {
    const targetTime = parseFloat(e.target.value);
    setCurrentTime(targetTime);
    if (audioRef.current) {
      audioRef.current.currentTime = targetTime;
    }
  };

  const handleRateChange = () => {
    const nextRate = playbackRate === 1 ? 1.25 : playbackRate === 1.25 ? 1.5 : playbackRate === 1.5 ? 2 : 1;
    setPlaybackRate(nextRate);
    if (audioRef.current) {
      audioRef.current.playbackRate = nextRate;
    }
  };

  const formatTime = (secs) => {
    if (!secs || isNaN(secs)) return '00:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (!audio || !audio.audio_url) return null;

  return (
    <div className="audio-player-bar" role="region" aria-label="Audiobook Player">
      <audio
        ref={audioRef}
        src={audio.audio_url}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={handleEnded}
        onError={() => setErrorMsg('Error loading audio stream.')}
      />

      <div className="audio-player-top">
        <div className="audio-track-info">
          <div className="audio-track-icon" aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 18V5l12-2v13" />
              <circle cx="6" cy="18" r="3" />
              <circle cx="18" cy="16" r="3" />
            </svg>
          </div>
          <div className="audio-track-text">
            <h4 title={audio.title || `Chapter ${audio.chapter_number}`}>
              {audio.title || `Chapter ${audio.chapter_number}`}
            </h4>
            <p>{audio.documentTitle || 'Audiobook Playback'}</p>
          </div>
        </div>

        <div className="audio-controls-main">
          {/* Previous Track Button */}
          <button
            type="button"
            className="skip-track-btn"
            onClick={onPrevTrack}
            disabled={!hasPrev}
            aria-label="Previous Chapter"
            title="Previous Chapter"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z" />
            </svg>
          </button>

          <button
            type="button"
            className="play-pause-btn"
            onClick={togglePlay}
            aria-label={isPlaying ? 'Pause audio' : 'Play audio'}
          >
            {isPlaying ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="4" width="4" height="16" rx="1" />
                <rect x="14" y="4" width="4" height="16" rx="1" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M5 3l14 9-14 9V3z" />
              </svg>
            )}
          </button>

          {/* Next Track Button */}
          <button
            type="button"
            className="skip-track-btn"
            onClick={onNextTrack}
            disabled={!hasNext}
            aria-label="Next Chapter"
            title="Next Chapter"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z" />
            </svg>
          </button>


          <div className="audio-timeline-wrap">
            <span className="audio-time">{formatTime(currentTime)}</span>
            <input
              type="range"
              min="0"
              max={duration || 100}
              step="0.1"
              value={currentTime}
              onChange={handleSeek}
              className="audio-progress-slider"
              aria-label="Seek track position"
            />
            <span className="audio-time">{formatTime(duration)}</span>
          </div>
        </div>

        <div className="audio-actions-extra">
          <button
            type="button"
            className="text-toggle-btn"
            onClick={handleRateChange}
            title="Change Playback Speed"
          >
            {playbackRate}x
          </button>

          {audio.text && (
            <button
              type="button"
              className="text-toggle-btn"
              onClick={() => setIsTextOpen((prev) => !prev)}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
              </svg>
              <span>{isTextOpen ? 'Hide Text' : 'View Text'}</span>
            </button>
          )}

          <button
            type="button"
            className="close-player-btn"
            onClick={onClose}
            aria-label="Close audio player"
            title="Close"
          >
            &times;
          </button>
        </div>
      </div>

      {errorMsg && (
        <div style={{ color: '#ef4444', fontSize: '12px', textAlign: 'center' }}>
          {errorMsg}
        </div>
      )}

      {isTextOpen && audio.text && (
        <div className="audio-text-drawer">
          <div className="audio-text-drawer-header">
            <span>Narration Script / Chapter Text</span>
            <span style={{ fontSize: '11px', color: '#64748b' }}>
              Word Count: {audio.text.split(/\s+/).length}
            </span>
          </div>
          <div>{audio.text}</div>
        </div>
      )}
    </div>
  );
}

export default AudioPlayer;
