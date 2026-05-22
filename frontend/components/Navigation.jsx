import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navigation.css';

function Navigation({ onNewSession, currentStep, user, onLogout, showGuide, onToggleGuide }) {
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
                    <div className="stepper">
                        {Object.entries(stepLabels).map(([step, label], idx) => {
                            const steps = Object.keys(stepLabels);
                            const currentIdx = steps.indexOf(currentStep);
                            const stepIdx = steps.indexOf(step);
                            const isActive = step === currentStep;
                            const isCompleted = stepIdx < currentIdx;

                            return (
                                <React.Fragment key={step}>
                                    <div className={`step-node ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}>
                                        <div className="step-circle">
                                            {isCompleted ? '✓' : idx + 1}
                                        </div>
                                        <span className="step-label">{label}</span>
                                    </div>
                                    {idx < steps.length - 1 && (
                                        <div className={`step-line ${stepIdx < currentIdx ? 'active' : ''}`}></div>
                                    )}
                                </React.Fragment>
                            );
                        })}
                    </div>
                )}
                {isSessions && user && (
                    <div className="nav-page-badge sessions-badge">
                        <span className="badge-icon">📋</span>
                        <span className="badge-text">All Sessions</span>
                    </div>
                )}
                {isSummary && user && (
                    <div className="nav-page-badge summary-badge">
                        <span className="badge-icon">📊</span>
                        <span className="badge-text">Interview Summary</span>
                    </div>
                )}
            </div>

            {user && (
                <div className="nav-right">
                    <button 
                        className={`toggle-guide-btn ${showGuide ? 'active' : ''}`} 
                        onClick={onToggleGuide}
                        title={showGuide ? "Hide process guide" : "Show process guide"}
                    >
                        {showGuide ? 'ℹ️ Hide Guide' : 'ℹ️ Show Guide'}
                    </button>
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