import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter as Router } from 'react-router-dom'
import { GoogleOAuthProvider } from '@react-oauth/google'
import App from './App.jsx'
import './App.css'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

// Global fetch interceptor to handle 401 Unauthorized errors (stale/expired tokens)
const originalFetch = window.fetch;
window.fetch = async (...args) => {
    try {
        const response = await originalFetch(...args);
        if (response.status === 401) {
            const url = typeof args[0] === 'string' ? args[0] : (args[0] instanceof URL ? args[0].href : '');
            // Only auto-logout if we're not trying to log in or register
            if (!url.includes('/auth/login') && !url.includes('/auth/register') && !url.includes('/auth/google') && !url.includes('/health')) {
                console.warn('Unauthorized request (401) detected. Cleaning session...');
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                // Redirect to login page
                window.location.href = '/login';
            }
        }
        return response;
    } catch (error) {
        throw error;
    }
};

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
            <Router>
                <App />
            </Router>
        </GoogleOAuthProvider>
    </React.StrictMode>,
)
