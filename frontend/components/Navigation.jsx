import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navigation.css';

function Navigation({ onNewSession, currentStep, user, onLogout }) {
    const location = useLocation();
    const isDashboard = location.pathname === '/';
    const isSessions = location.pathname === '/sessions';
    const isSummary = location.pathname.startsWith('/summary/');

    const stepLabels = {
        'resume-upload': 'Upload Resume',
        'role-selection': 'Select Role',
        'interview': 'Active Interview'
    };

    return (
        <nav className="navigation">
            <div className="nav-left">
                <Link to="/" className="logo" onClick={onNewSession}>
                    <span className="logo-icon">🤖</span>
                    <span className="logo-text">AI Interview System</span>
                </Link>
            </div>

            <div className="nav-center">
                {isDashboard && user && (
                    <div className="breadcrumb">
                        {Object.entries(stepLabels).map(([step, label]) => (
                            <div key={step} className={`breadcrumb-item ${step === currentStep ? 'active' : ''}`}>
                                <span>{label}</span>
                            </div>
                        ))}
                    </div>
                )}
                {isSessions && user && (
                    <div className="breadcrumb">
                        <div className="breadcrumb-item active">
                            <span>📋 All Sessions</span>
                        </div>
                    </div>
                )}
                {isSummary && user && (
                    <div className="breadcrumb">
                        <div className="breadcrumb-item active">
                            <span>📊 Interview Summary</span>
                        </div>
                    </div>
                )}
            </div>

            {user && (
                <div className="nav-right">
                    <Link to="/sessions" className="sessions-link">
                        📋 All Sessions
                    </Link>
                    <button className="new-session-btn" onClick={onNewSession}>
                        ➕ New Interview
                    </button>
                    <div className="user-profile">
                        <span className="username" title={user.email}>👤 {user.username}</span>
                        <button className="logout-btn" onClick={onLogout}>
                            🚪 Logout
                        </button>
                    </div>
                </div>
            )}
        </nav>
    );
}

export default Navigation;