import { useState } from 'react';
import TextInput from '../common/Input/TextInput';
import PasswordInput from '../common/Input/PasswordInput';
import Button from '../common/Button/Button';
import Alert from '../common/Alert/Alert';
import './Screens.css';

/**
 * Page to Voice - Login Screen Component
 *
 * Supports login by either Email or Username, integrated with FastAPI /auth/login.
 *
 * @param {Object} props
 * @param {Function} props.onLogin - Async handler to submit login
 * @param {Function} props.onNavigateToRegister - Navigation callback
 * @param {boolean} props.isLoading - Loading state from auth controller
 * @param {string|null} props.authError - Global auth error message
 * @param {Function} props.onClearError - Clear error callback
 */
export function LoginScreen({
  onLogin,
  onNavigateToRegister,
  isLoading = false,
  authError = null,
  onClearError,
}) {
  const [formData, setFormData] = useState({
    identifier: '',
    password: '',
  });

  const [fieldErrors, setFieldErrors] = useState({});

  const validate = () => {
    const errors = {};
    const trimmed = formData.identifier.trim();

    if (!trimmed) {
      errors.identifier = 'Email or username is required.';
    } else if (trimmed.includes('@')) {
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
        errors.identifier = 'Please enter a valid email address.';
      }
    } else if (trimmed.length < 3) {
      errors.identifier = 'Username must be at least 3 characters.';
    }

    if (!formData.password) {
      errors.password = 'Password is required.';
    } else if (formData.password.length < 4) {
      errors.password = 'Password must be at least 4 characters.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleChange = (e) => {
    const { id, value } = e.target;
    setFormData((prev) => ({ ...prev, [id]: value }));

    if (fieldErrors[id]) {
      setFieldErrors((prev) => ({ ...prev, [id]: '' }));
    }
    if (authError && onClearError) {
      onClearError();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    try {
      await onLogin({
        email: formData.identifier.trim(),
        password: formData.password,
      });
    } catch {
      // Errors handled by parent auth state
    }
  };

  return (
    <div className="screen-container">
      <div className="auth-card">
        <div className="auth-card-header">
          <h1 className="auth-card-title">Welcome back</h1>
          <p className="auth-card-subtitle">
            Sign in to your Page to Voice account
          </p>
        </div>

        {authError && (
          <Alert
            type="error"
            title="Authentication Error"
            onClose={onClearError}
          >
            {authError}
          </Alert>
        )}

        <form onSubmit={handleSubmit} noValidate autoComplete="off">
          {/* Hidden inputs to absorb aggressive browser credential autofill */}
          <input
            type="text"
            name="prevent_autofill_username"
            tabIndex={-1}
            aria-hidden="true"
            style={{ position: 'absolute', opacity: 0, height: 0, width: 0, pointerEvents: 'none' }}
            autoComplete="off"
          />
          <input
            type="password"
            name="prevent_autofill_password"
            tabIndex={-1}
            aria-hidden="true"
            style={{ position: 'absolute', opacity: 0, height: 0, width: 0, pointerEvents: 'none' }}
            autoComplete="off"
          />

          <TextInput
            id="identifier"
            name="login_account_identifier"
            type="text"
            label="Email or Username"
            placeholder="Enter your email or username"
            value={formData.identifier}
            onChange={handleChange}
            error={fieldErrors.identifier}
            required
            disabled={isLoading}
            autoComplete="off"
          />

          <PasswordInput
            id="password"
            name="login_account_secret"
            label="Password"
            placeholder="Enter your password"
            value={formData.password}
            onChange={handleChange}
            error={fieldErrors.password}
            required
            disabled={isLoading}
            autoComplete="new-password"
          />

          <Button
            type="submit"
            variant="primary"
            size="lg"
            fullWidth
            loading={isLoading}
            disabled={isLoading}
            style={{ marginTop: '8px' }}
          >
            {isLoading ? 'Signing In...' : 'Sign In'}
          </Button>
        </form>

        <div className="auth-card-footer">
          <span>Don&apos;t have an account? </span>
          <button
            type="button"
            className="auth-link-btn"
            onClick={onNavigateToRegister}
            disabled={isLoading}
          >
            Create an account
          </button>
        </div>
      </div>
    </div>
  );
}

export default LoginScreen;
