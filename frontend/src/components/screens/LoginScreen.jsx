import { useState } from 'react';
import TextInput from '../common/Input/TextInput';
import PasswordInput from '../common/Input/PasswordInput';
import Button from '../common/Button/Button';
import Alert from '../common/Alert/Alert';
import './Screens.css';

/**
 * Page to Voice - Login Screen Component
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
    email: '',
    password: '',
  });

  const [fieldErrors, setFieldErrors] = useState({});

  const validate = () => {
    const errors = {};
    const emailTrimmed = formData.email.trim();

    if (!emailTrimmed) {
      errors.email = 'Email address is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailTrimmed)) {
      errors.email = 'Please enter a valid email address.';
    }

    if (!formData.password) {
      errors.password = 'Password is required.';
    } else if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters.';
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
        email: formData.email.trim(),
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

        <form onSubmit={handleSubmit} noValidate>
          <TextInput
            id="email"
            type="email"
            label="Email Address"
            placeholder="name@example.com"
            value={formData.email}
            onChange={handleChange}
            error={fieldErrors.email}
            required
            disabled={isLoading}
            autoComplete="email"
          />

          <PasswordInput
            id="password"
            label="Password"
            placeholder="Enter your password"
            value={formData.password}
            onChange={handleChange}
            error={fieldErrors.password}
            required
            disabled={isLoading}
            autoComplete="current-password"
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
