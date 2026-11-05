import './LoadingSpinner.css';

/**
 * Reusable LoadingSpinner component
 *
 * @param {Object} props
 * @param {string} [props.label='Loading...'] - Accessible label
 * @param {boolean} [props.showLabel=true]
 * @param {string} [props.className='']
 */
export function LoadingSpinner({
  label = 'Loading...',
  showLabel = true,
  className = '',
}) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={`spinner-container ${className}`}
    >
      <div className="spinner-circle" aria-hidden="true" />
      {showLabel && <span className="spinner-text">{label}</span>}
      <span className="sr-only" style={{ position: 'absolute', width: 1, height: 1, padding: 0, margin: -1, overflow: 'hidden', clip: 'rect(0,0,0,0)', border: 0 }}>
        {label}
      </span>
    </div>
  );
}

export default LoadingSpinner;
