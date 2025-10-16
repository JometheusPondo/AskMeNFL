import React, { useState } from 'react';
import { useAuth } from '../contexts/authContext';
import './auth.css';

export const Login = ({ onSwitchToRegister, onClose }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    const result = await login(username, password);

    if (result.success) {
      onClose();
    } else {
      setError(result.error);
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-modal-overlay" onClick={onClose}>
      <div className="auth-modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="auth-close-btn" onClick={onClose}>✕</button>

        <div className="auth-header">
          <h2>Login</h2>
          <p>Welcome back! Enter your credentials to continue.</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
              disabled={isLoading}
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              disabled={isLoading}
            />
          </div>

          {error && (
            <div className="auth-error">
              ⚠️ {error}
              { error === "Invalid credentials" && (
                <div className="forgot-password-hint">
                  <p>Forgot your password?
                  <button className="forgot-password-link"
                  onClick={() => alert("Password reset feature coming soon! Please contact support")}>
                  Reset Password
                </button>
                </p>
              </div>
            )}
            </div>
          )}

          <button
            type="submit"
            className="auth-submit-btn"
            disabled={isLoading || !username || !password}
          >
            {isLoading ? '🔄 Logging in...' : '🚀 Login'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Don't have an account?{' '}
            <button
              className="auth-switch-btn"
              onClick={onSwitchToRegister}
              disabled={isLoading}
            >
              Register here
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;