import { useState } from 'react';
import TextInput from '../common/Input/TextInput';
import PasswordInput from '../common/Input/PasswordInput';
import Button from '../common/Button/Button';
import Alert from '../common/Alert/Alert';
import './Screens.css';

/**
 * Page to Voice - Registration Screen Component
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
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  const [fieldErrors, setFieldErrors] = useState({});

  const validate = () => {
    const errors = {};
    const nameTrimmed = formData.name.trim();
    const emailTrimmed = formData.email.trim();

    if (!nameTrimmed) {
      errors.name = 'Full name is required.';
    } else if (nameTrimmed.length < 2) {
      errors.name = 'Name must be at least 2 characters.';
    }

    if (!emailTrimmed) {
      errors.email = 'Email address is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailTrimmed)) {
      errors.email = 'Please enter a valid email address.';
    }

    if (!formData.password) {
      errors.password = 'Password is required.';
    } else if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters.';
    }

    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Confirming your password is required.';
    } else if (formData.password !== formData.confirmPassword) {
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
        name: formData.name.trim(),
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
            id="name"
            label="Full Name"
            placeholder="e.g. Jane Doe"
            value={formData.name}
            onChange={handleChange}
            error={fieldErrors.name}
            required
            disabled={isLoading}
            autoComplete="name"
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
            helperText="Must be at least 8 characters long."
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
