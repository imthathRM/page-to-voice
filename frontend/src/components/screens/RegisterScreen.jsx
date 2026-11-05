import { useState } from 'react';
import TextInput from '../common/Input/TextInput';
import PasswordInput from '../common/Input/PasswordInput';
import Button from '../common/Button/Button';
import Alert from '../common/Alert/Alert';
import './Screens.css';

/**
 * Page to Voice - Registration Screen Component
 *
 * Integrated with FastAPI /auth/register endpoint:
 * requires username, email, and strong password.
 *
 * @param {Object} props
 * @param {Function} props.onRegister - Async handler to submit registration
 * @param {Function} props.onNavigateToLogin - Navigation callback
 * @param {boolean} props.isLoading - Loading state from auth controller
 * @param {string|null} props.authError - Global auth error message
 * @param {Function} props.onClearError - Clear error callback
 */
export function RegisterScreen({
  onRegister,
  onNavigateToLogin,
  isLoading = false,
  authError = null,
  onClearError,
}) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  const [fieldErrors, setFieldErrors] = useState({});

  const validate = () => {
    const errors = {};
    const usernameTrimmed = formData.username.trim();
    const emailTrimmed = formData.email.trim();
    const pwd = formData.password;

    if (!usernameTrimmed) {
      errors.username = 'Username is required.';
    } else if (usernameTrimmed.length < 3 || usernameTrimmed.length > 50) {
      errors.username = 'Username must be between 3 and 50 characters.';
    } else if (!/^[a-zA-Z0-9_-]+$/.test(usernameTrimmed)) {
      errors.username = 'Username can only contain letters, numbers, underscores, and hyphens.';
    }

    if (!emailTrimmed) {
      errors.email = 'Email address is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailTrimmed)) {
      errors.email = 'Please enter a valid email address.';
    }

    if (!pwd) {
      errors.password = 'Password is required.';
    } else if (pwd.length < 8) {
      errors.password = 'Password must be at least 8 characters long.';
    } else if (!/\d/.test(pwd)) {
      errors.password = 'Password must contain at least one digit.';
    } else if (!/[a-zA-Z]/.test(pwd)) {
      errors.password = 'Password must contain at least one letter.';
    } else if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(pwd)) {
      errors.password = 'Password must contain at least one special character (!@#$%^&*).';
    } else if (/\s/.test(pwd)) {
      errors.password = 'Password must not contain spaces.';
    }

    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Confirming your password is required.';
    } else if (pwd !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match.';
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
      await onRegister({
        username: formData.username.trim(),
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
          <h1 className="auth-card-title">Create an Account</h1>
          <p className="auth-card-subtitle">
            Get started with Page to Voice today
          </p>
        </div>

        {authError && (
          <Alert
            type="error"
            title="Registration Error"
            onClose={onClearError}
          >
            {authError}
          </Alert>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <TextInput
            id="username"
            label="Username"
            placeholder="e.g. alex_reader"
            value={formData.username}
            onChange={handleChange}
            error={fieldErrors.username}
            helperText="3-50 characters (alphanumeric, underscores, hyphens)"
            required
            disabled={isLoading}
            autoComplete="username"
          />

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
            placeholder="Create a strong password"
            value={formData.password}
            onChange={handleChange}
            error={fieldErrors.password}
            helperText="At least 8 characters with letters, numbers, and special characters (!@#$%^&*)."
            required
            disabled={isLoading}
            autoComplete="new-password"
          />

          <PasswordInput
            id="confirmPassword"
            label="Confirm Password"
            placeholder="Re-enter your password"
            value={formData.confirmPassword}
            onChange={handleChange}
            error={fieldErrors.confirmPassword}
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
            {isLoading ? 'Creating Account...' : 'Create Account'}
          </Button>
        </form>

        <div className="auth-card-footer">
          <span>Already have an account? </span>
          <button
            type="button"
            className="auth-link-btn"
            onClick={onNavigateToLogin}
            disabled={isLoading}
          >
            Sign in
          </button>
        </div>
      </div>
    </div>
  );
}

export default RegisterScreen;
