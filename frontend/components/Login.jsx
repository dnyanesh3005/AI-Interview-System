import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './Login.css';

function Login({ setToken, setUser, showToast, initialMode = 'login' }) {
    const [mode, setMode] = useState(initialMode); // 'login' or 'signup'
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [companyName, setCompanyName] = useState('');
    const [loading, setLoading] = useState(false);

    const navigate = useNavigate();
    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        // Basic Validations
        if (username.trim().length < 3) {
            showToast(mode === 'signup' ? 'Full Name must be at least 3 characters long' : 'Username must be at least 3 characters long', 'error');
            return;
        }
        if (password.length < 6) {
            showToast('Password must be at least 6 characters long', 'error');
            return;
        }
        
        if (mode === 'signup') {
            if (!email.includes('@') || !email.includes('.')) {
                showToast('Please enter a valid email address', 'error');
                return;
            }
            if (password !== confirmPassword) {
                showToast('Passwords do not match', 'error');
                return;
            }
            
            setLoading(true);
            try {
                const response = await fetch(`${API_BASE_URL}/auth/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password }),
                });
                
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.detail || 'Registration failed');
                }
                
                showToast('Registration successful! Please log in.', 'success');
                setMode('login');
                setPassword('');
                setConfirmPassword('');
                setCompanyName('');
            } catch (err) {
                showToast(err.message, 'error');
            } finally {
                setLoading(false);
            }
        } else {
            setLoading(true);
            try {
                const response = await fetch(`${API_BASE_URL}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password }),
                });
                
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.detail || 'Login failed');
                }
                
                localStorage.setItem('token', data.token);
                localStorage.setItem('user', JSON.stringify(data.user));
                
                setToken(data.token);
                setUser(data.user);
                
                showToast(`Welcome back, ${data.user.username}!`, 'success');
                navigate('/');
            } catch (err) {
                showToast(err.message, 'error');
            } finally {
                setLoading(false);
            }
        }
    };

    return (
        <div className="login-container">
            <div className="login-glass-card">
                <div className="login-header">
                    <h2>{mode === 'login' ? 'Welcome Back' : 'Create Account'}</h2>
                    <p>{mode === 'login' ? 'Sign in to access your interview dashboard' : 'Sign up to start candidate screenings'}</p>
                </div>
                
                <form onSubmit={handleSubmit} className="login-form">
                    <div className="input-group">
                        <label htmlFor="username">{mode === 'signup' ? 'Full Name' : 'Email Address or Username'}</label>
                        <input
                            type="text"
                            id="username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder={mode === 'signup' ? "First and Last Name" : "Enter email or username"}
                            required
                            disabled={loading}
                        />
                    </div>

                    {mode === 'signup' && (
                        <div className="input-group">
                            <label htmlFor="email">Email Address</label>
                            <input
                                type="email"
                                id="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="name@example.com"
                                required={mode === 'signup'}
                                disabled={loading}
                            />
                        </div>
                    )}

                    <div className="input-group">
                        <label htmlFor="password">Password</label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                            disabled={loading}
                        />
                    </div>

                    {mode === 'signup' && (
                        <div className="input-group">
                            <label htmlFor="confirmPassword">Confirm Password</label>
                            <input
                                type="password"
                                id="confirmPassword"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="••••••••"
                                required={mode === 'signup'}
                                disabled={loading}
                            />
                        </div>
                    )}

                    {mode === 'signup' && (
                        <div className="input-group">
                            <label htmlFor="companyName">Company Name</label>
                            <input
                                type="text"
                                id="companyName"
                                value={companyName}
                                onChange={(e) => setCompanyName(e.target.value)}
                                placeholder="Acme Corporation"
                                disabled={loading}
                            />
                        </div>
                    )}

                    {mode === 'login' && (
                        <div className="forgot-password-container">
                            <button
                                type="button"
                                className="forgot-password-link"
                                onClick={() => showToast('Password reset is not configured. Please contact the administrator.', 'error')}
                            >
                                Forgot Password?
                            </button>
                        </div>
                    )}

                    <button type="submit" className="login-btn" disabled={loading}>
                        {loading ? (
                            <span className="spinner-small"></span>
                        ) : (
                            mode === 'login' ? 'Sign In' : 'Sign Up'
                        )}
                    </button>
                </form>

                {mode === 'login' && (
                    <div className="social-login-container">
                        <div className="divider">
                            <span>or</span>
                        </div>
                        <div className="social-buttons">
                            <button
                                type="button"
                                className="social-btn google-btn"
                                onClick={() => showToast('Google authentication placeholder', 'success')}
                            >
                                <span className="social-icon">🌐</span>
                                Sign in with Google
                            </button>
                            <button
                                type="button"
                                className="social-btn linkedin-btn"
                                onClick={() => showToast('LinkedIn authentication placeholder', 'success')}
                            >
                                <span className="social-icon">🔗</span>
                                Sign in with LinkedIn
                            </button>
                        </div>
                    </div>
                )}

                <div className="login-footer">
                    {mode === 'login' ? (
                        <p>
                            Don't have an account?{' '}
                            <button className="toggle-mode-btn" onClick={() => setMode('signup')} disabled={loading}>
                                Sign Up
                            </button>
                        </p>
                    ) : (
                        <p>
                            Already have an account?{' '}
                            <button className="toggle-mode-btn" onClick={() => setMode('login')} disabled={loading}>
                                Sign In
                            </button>
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
}

export default Login;
