import React from 'react';
import { Link } from 'react-router-dom';
import './Navigation.css';

function Navigation({ onNewSession, currentStep }) {
    const stepLabels = {
        'resume-upload': 'Resume Upload',
        'role-selection': 'Role Selection',
        'interview': 'Interview',
        'summary': 'Summary'
    };

    return (
        <nav className="navigation">
            <div className="nav-left">
                <Link to="/" className="logo">
                    <span className="logo-icon">🤖</span>
                    <span className="logo-text">AI Interview System</span>
                </Link>
            </div>

            <div className="nav-center">
                <div className="breadcrumb">
                    {Object.entries(stepLabels).map(([step, label]) => (
                        <div key={step} className={`breadcrumb-item ${step === currentStep ? 'active' : ''}`}>
                            <span>{label}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className="nav-right">
                <Link to="/sessions" className="sessions-link">
                    📋 All Sessions
                </Link>
                <button className="new-session-btn" onClick={onNewSession}>
                    ➕ New Interview
                </button>
            </div>
        </nav>
    );
}

export default Navigation;