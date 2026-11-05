import './Alert.css';

/**
 * Reusable Alert component for notifications, errors, warnings, and confirmations
 *
 * @param {Object} props
 * @param {'error'|'success'|'warning'|'info'} [props.type='info']
 * @param {string} [props.title]
 * @param {React.ReactNode} props.children
 * @param {Function} [props.onClose] - If provided, renders close button
 * @param {string} [props.className='']
 */
export function Alert({
  type = 'info',
  title,
  children,
  onClose,
  className = '',
}) {
  const isError = type === 'error';
  const role = isError ? 'alert' : 'status';
  const ariaLive = isError ? 'assertive' : 'polite';

  const renderIcon = () => {
    switch (type) {
      case 'error':
        return (
          <svg className="alert-icon" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        );
      case 'success':
        return (
          <svg className="alert-icon" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'warning':
        return (
          <svg className="alert-icon" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        );
      case 'info':
      default:
        return (
          <svg className="alert-icon" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
        );
    }
  };

  return (
    <div
      role={role}
      aria-live={ariaLive}
      className={`alert alert-${type} ${className}`}
    >
      <div className="alert-icon-wrapper">{renderIcon()}</div>
      <div className="alert-content">
        {title && <div className="alert-title">{title}</div>}
        <div>{children}</div>
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="alert-close-btn"
          aria-label="Dismiss alert"
        >
          &times;
        </button>
      )}
    </div>
  );
}

export default Alert;
