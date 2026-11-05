import './Input.css';

/**
 * Reusable accessible TextInput component
 *
 * @param {Object} props
 * @param {string} props.id - HTML ID
 * @param {string} props.label - Field label
 * @param {string} [props.type='text'] - Input type
 * @param {string} props.value - Input value
 * @param {Function} props.onChange - Change handler
 * @param {string} [props.placeholder=''] - Placeholder text
 * @param {string} [props.error=''] - Error message to display
 * @param {string} [props.helperText=''] - Helper guidance text
 * @param {boolean} [props.required=false] - Required indicator
 * @param {boolean} [props.disabled=false] - Disabled state
 * @param {string} [props.autoComplete] - Autocomplete attribute
 * @param {string} [props.className='']
 */
export function TextInput({
  id,
  label,
  type = 'text',
  value,
  onChange,
  placeholder = '',
  error = '',
  helperText = '',
  required = false,
  disabled = false,
  autoComplete,
  className = '',
  ...rest
}) {
  const errorId = error ? `${id}-error` : undefined;
  const helperId = helperText ? `${id}-helper` : undefined;
  const describedBy = [errorId, helperId].filter(Boolean).join(' ') || undefined;

  return (
    <div className={`form-group ${className}`}>
      {label && (
        <label htmlFor={id} className="form-label">
          {label}
          {required && <span className="form-required" aria-hidden="true">*</span>}
        </label>
      )}
      <div className="input-wrapper">
        <input
          id={id}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          autoComplete={autoComplete}
          aria-invalid={Boolean(error)}
          aria-describedby={describedBy}
          className={`form-input ${error ? 'form-input-error' : ''}`}
          {...rest}
        />
      </div>
      {error && (
        <span id={errorId} className="form-error-msg" role="alert">
          {error}
        </span>
      )}
      {!error && helperText && (
        <span id={helperId} className="form-helper">
          {helperText}
        </span>
      )}
    </div>
  );
}

export default TextInput;
