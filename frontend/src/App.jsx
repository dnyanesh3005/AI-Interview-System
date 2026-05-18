import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import ResumeUpload from '../components/ResumeUpload.jsx';
import RoleSelection from '../components/RoleSelection.jsx';
import InterviewFlow from '../components/InterviewFlow.jsx';
import InterviewSummary from '../components/InterviewSummary.jsx';
import SessionsList from '../components/SessionsList.jsx';
import Navigation from '../components/Navigation.jsx';

function App() {
    const [sessionId, setSessionId] = useState(null);
    const [resumeData, setResumeData] = useState(null);
    const [selectedRole, setSelectedRole] = useState(null);
    const [currentStep, setCurrentStep] = useState('resume-upload');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

    useEffect(() => {
        // Check if API is available
        fetch(`${API_BASE_URL.replace('/api', '')}/health`)
            .catch(err => {
                console.warn('Backend not available yet. Will retry on action.');
            });
    }, []);

    const handleResumeUpload = async (file) => {
        setLoading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${API_BASE_URL}/upload-resume`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to upload resume');
            }

            const data = await response.json();
            if (!data.success) {
                throw new Error('Upload failed');
            }

            setResumeData(data.data);
            setCurrentStep('role-selection');
        } catch (err) {
            setError(err.message || 'Error uploading resume. Make sure backend is running.');
            console.error('Resume upload error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleRoleSelection = async (role) => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/select-role`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to select role');
            }

            const data = await response.json();
            if (!data.success) {
                throw new Error('Role selection failed');
            }

            setSelectedRole(role);
            await startInterview(role);
        } catch (err) {
            setError(err.message || 'Error selecting role');
            console.error('Role selection error:', err);
        } finally {
            setLoading(false);
        }
    };

    const startInterview = async (role) => {
        try {
            const response = await fetch(`${API_BASE_URL}/start-interview`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...resumeData,
                    role,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to start interview');
            }

            const data = await response.json();
            if (!data.success) {
                throw new Error('Interview initialization failed');
            }

            setSessionId(data.session_id);
            setCurrentStep('interview');
        } catch (err) {
            setError(err.message || 'Error starting interview');
            console.error('Interview start error:', err);
        }
    };

    const handleInterviewComplete = () => {
        setCurrentStep('summary');
    };

    const handleNewSession = () => {
        setSessionId(null);
        setResumeData(null);
        setSelectedRole(null);
        setCurrentStep('resume-upload');
        setError(null);
    };

    return (
        <Router>
            <div className="App">
                <Navigation onNewSession={handleNewSession} currentStep={currentStep} />

                <main className="app-main">
                    {error && (
                        <div className="error-banner">
                            <p>❌ {error}</p>
                            <button onClick={() => setError(null)}>✕ Dismiss</button>
                        </div>
                    )}

                    {loading && (
                        <div className="loading-overlay">
                            <div className="spinner"></div>
                            <p>Processing...</p>
                        </div>
                    )}

                    <Routes>
                        <Route path="/" element={
                            <>
                                {currentStep === 'resume-upload' && (
                                    <ResumeUpload onUpload={handleResumeUpload} loading={loading} />
                                )}
                                {currentStep === 'role-selection' && resumeData && (
                                    <RoleSelection onSelect={handleRoleSelection} loading={loading} />
                                )}
                                {currentStep === 'interview' && sessionId && (
                                    <InterviewFlow
                                        sessionId={sessionId}
                                        resumeData={resumeData}
                                        role={selectedRole}
                                        onComplete={handleInterviewComplete}
                                    />
                                )}
                                {currentStep === 'summary' && sessionId && (
                                    <InterviewSummary
                                        sessionId={sessionId}
                                        onNewSession={handleNewSession}
                                    />
                                )}
                            </>
                        } />
                        <Route path="/sessions" element={<SessionsList />} />
                    </Routes>
                </main>
            </div>
        </Router>
    );
}

export default App;