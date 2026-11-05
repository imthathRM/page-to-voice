import React, { useState, useRef, useEffect } from 'react';
import './AudioPlayerBar.css';

/**
 * Persistent Audio Player Bar
 * Supports HTML5 audio playback, seekbar, speed adjustments (0.75x - 2x), volume, and sample preview.
 */
export function AudioPlayerBar({
  currentTrack,
  onPlaySample,
  onCloseTrack,
}) {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [volume, setVolume] = useState(0.85);
  const [isMuted, setIsMuted] = useState(false);
  const [isSpeedMenuOpen, setIsSpeedMenuOpen] = useState(false);

  const speedOptions = [0.75, 1.0, 1.25, 1.5, 2.0];

  useEffect(() => {
    if (audioRef.current && currentTrack?.audioUrl) {
      audioRef.current.src = currentTrack.audioUrl;
      audioRef.current.playbackRate = playbackRate;
      audioRef.current.volume = isMuted ? 0 : volume;
      audioRef.current.play().then(() => {
        setIsPlaying(true);
      }).catch(() => {
        setIsPlaying(false);
      });
    } else {
      setIsPlaying(false);
      setCurrentTime(0);
      setDuration(0);
    }
  }, [currentTrack]);

  const togglePlayPause = () => {
    if (!audioRef.current || !currentTrack?.audioUrl) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().then(() => {
        setIsPlaying(true);
      }).catch(() => {
        setIsPlaying(false);
      });
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
      if (audioRef.current.duration && !isNaN(audioRef.current.duration)) {
        setDuration(audioRef.current.duration);
      }
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current && !isNaN(audioRef.current.duration)) {
      setDuration(audioRef.current.duration);
    }
  };

  const handleSeek = (e) => {
    const newTime = parseFloat(e.target.value);
    setCurrentTime(newTime);
    if (audioRef.current) {
      audioRef.current.currentTime = newTime;
    }
  };

  const skipSeconds = (seconds) => {
    if (audioRef.current) {
      const targetTime = Math.max(0, Math.min(duration || 100, audioRef.current.currentTime + seconds));
      audioRef.current.currentTime = targetTime;
      setCurrentTime(targetTime);
    }
  };

  const handleSpeedChange = (speed) => {
    setPlaybackRate(speed);
    if (audioRef.current) {
      audioRef.current.playbackRate = speed;
    }
    setIsSpeedMenuOpen(false);
  };

  const handleVolumeChange = (e) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    setIsMuted(val === 0);
    if (audioRef.current) {
      audioRef.current.volume = val;
    }
  };

  const toggleMute = () => {
    if (audioRef.current) {
      if (isMuted) {
        audioRef.current.volume = volume || 0.8;
        setIsMuted(false);
      } else {
        audioRef.current.volume = 0;
        setIsMuted(true);
      }
    }
  };

  const formatTime = (timeInSeconds) => {
    if (isNaN(timeInSeconds) || timeInSeconds <= 0) return '00:00';
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = Math.floor(timeInSeconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  const hasTrack = Boolean(currentTrack?.title);

  return (
    <div className={`audio-player-bar ${hasTrack ? 'active' : 'idle'}`}>
      <audio
        ref={audioRef}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={() => setIsPlaying(false)}
      />

      <div className="player-inner">
        {/* Track Metadata */}
        <div className="player-track-info">
          <div className="player-art">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 18V5l12-2v13" />
              <circle cx="6" cy="18" r="3" />
              <circle cx="18" cy="16" r="3" />
            </svg>
          </div>
          <div className="player-text">
            {hasTrack ? (
              <>
                <div className="player-title" title={currentTrack.title}>
                  {currentTrack.title}
                </div>
                <div className="player-subtitle">
                  {currentTrack.chapterTitle || 'Standard Chapter'} • {currentTrack.docType || 'Audiobook'}
                </div>
              </>
            ) : (
              <>
                <div className="player-title-idle">No audiobook playing</div>
                <div className="player-subtitle-idle">
                  Select a document from your library or{' '}
                  <button type="button" className="sample-btn-link" onClick={onPlaySample}>
                    Play Demo Audio
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Center Controls & Scrubber */}
        <div className="player-controls-center">
          <div className="player-buttons">
            {/* Skip Back 10s */}
            <button
              type="button"
              className="player-btn"
              onClick={() => skipSeconds(-10)}
              disabled={!hasTrack}
              title="Rewind 10 seconds"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M1 4v6h6" />
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
              </svg>
              <span className="btn-label-tiny">10</span>
            </button>

            {/* Play / Pause Primary */}
            <button
              type="button"
              className={`player-btn-main ${isPlaying ? 'playing' : ''}`}
              onClick={hasTrack ? togglePlayPause : onPlaySample}
              title={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="6" y="4" width="4" height="16" rx="1" />
                  <rect x="14" y="4" width="4" height="16" rx="1" />
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="5 3 19 12 5 21 5 3" />
                </svg>
              )}
            </button>

            {/* Skip Forward 10s */}
            <button
              type="button"
              className="player-btn"
              onClick={() => skipSeconds(10)}
              disabled={!hasTrack}
              title="Fast forward 10 seconds"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M23 4v6h-6" />
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
              </svg>
              <span className="btn-label-tiny">10</span>
            </button>
          </div>

          <div className="player-timeline">
            <span className="timeline-time">{formatTime(currentTime)}</span>
            <input
              type="range"
              min="0"
              max={duration || 100}
              step="0.1"
              value={currentTime}
              onChange={handleSeek}
              disabled={!hasTrack}
              className="timeline-slider"
              aria-label="Audio scrubber"
            />
            <span className="timeline-time">{formatTime(duration)}</span>
          </div>
        </div>

        {/* Right Tools: Speed & Volume */}
        <div className="player-tools-right">
          {/* Speed Selector */}
          <div className="speed-dropdown-wrapper">
            <button
              type="button"
              className="player-tool-btn speed-btn"
              onClick={() => setIsSpeedMenuOpen(!isSpeedMenuOpen)}
              title="Playback speed"
            >
              <span>{playbackRate}x</span>
            </button>

            {isSpeedMenuOpen && (
              <div className="speed-menu">
                <div className="speed-menu-title">Speed</div>
                {speedOptions.map((s) => (
                  <button
                    key={s}
                    type="button"
                    className={`speed-option ${playbackRate === s ? 'selected' : ''}`}
                    onClick={() => handleSpeedChange(s)}
                  >
                    {s}x {playbackRate === s && '✓'}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Volume Control */}
          <div className="player-volume-group">
            <button
              type="button"
              className="player-tool-btn"
              onClick={toggleMute}
              title={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted || volume === 0 ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="1" y1="1" x2="23" y2="23" />
                  <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6" />
                  <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23" />
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
                </svg>
              )}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              className="volume-slider"
              aria-label="Volume slider"
            />
          </div>

          {hasTrack && onCloseTrack && (
            <button
              type="button"
              className="player-close-track-btn"
              onClick={onCloseTrack}
              title="Close Player"
            >
              &times;
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default AudioPlayerBar;
