import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import './App.css';
import ResumeUpload from '../components/ResumeUpload.jsx';
import RoleSelection from '../components/RoleSelection.jsx';
import InterviewFlow from '../components/InterviewFlow.jsx';
import InterviewSummary from '../components/InterviewSummary.jsx';
import SessionsList from '../components/SessionsList.jsx';
import Navigation from '../components/Navigation.jsx';
import Login from '../components/Login.jsx';

function PrivateRoute({ token, children }) {
    return token ? children : <Navigate to="/login" replace />;
}

function App() {
    const [token, setToken] = useState(localStorage.getItem('token') || null);
    const [user, setUser] = useState(() => {
        try {
            const stored = localStorage.getItem('user');
            return stored ? JSON.parse(stored) : null;
        } catch (e) {
            return null;
        }
    });

    const [sessionId, setSessionId] = useState(null);
    const [resumeData, setResumeData] = useState(null);
    const [selectedRole, setSelectedRole] = useState(null);
    const [firstQuestion, setFirstQuestion] = useState(null);
    const [currentStep, setCurrentStep] = useState('resume-upload');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [toast, setToast] = useState(null); // { message: '', type: 'success' | 'error' }

    const navigate = useNavigate();
    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

    const showToast = (message, type = 'success') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 4000);
    };

    useEffect(() => {
        if (token) {
            // Check if API is available
            fetch(`${API_BASE_URL.replace('/api', '')}/health`)
                .catch(err => {
                    console.warn('Backend not available yet.');
                });
        }
    }, [token]);

    const handleResumeUpload = async (file) => {
        setLoading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${API_BASE_URL}/upload-resume`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
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
            showToast('Resume parsed successfully!', 'success');
        } catch (err) {
            setError(err.message || 'Error uploading resume. Make sure backend is running.');
            showToast(err.message || 'Error uploading resume', 'error');
            console.error('Resume upload error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleRoleSelection = async (role, totalQuestions) => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/select-role`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
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
            await startInterview(role, totalQuestions);
        } catch (err) {
            setError(err.message || 'Error selecting role');
            showToast(err.message || 'Error selecting role', 'error');
            console.error('Role selection error:', err);
        } finally {
            setLoading(false);
        }
    };

    const startInterview = async (role, totalQuestions) => {
        try {
            const response = await fetch(`${API_BASE_URL}/start-interview`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    ...resumeData,
                    role,
                    total_questions: totalQuestions
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
            setFirstQuestion(data.question || null);
            setCurrentStep('interview');
            showToast('Interview session initialized!', 'success');
        } catch (err) {
            setError(err.message || 'Error starting interview');
            showToast(err.message || 'Error starting interview', 'error');
            console.error('Interview start error:', err);
        }
    };

    const handleInterviewComplete = (finalSessionId) => {
        showToast('Interview completed successfully!', 'success');
        setSessionId(null);
        setResumeData(null);
        setSelectedRole(null);
        setFirstQuestion(null);
        setCurrentStep('resume-upload');
        navigate(`/summary/${finalSessionId}`);
    };

    const handleNewSession = () => {
        setSessionId(null);
        setResumeData(null);
        setSelectedRole(null);
        setFirstQuestion(null);
        setCurrentStep('resume-upload');
        setError(null);
        navigate('/');
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setToken(null);
        setUser(null);
        handleNewSession();
        showToast('Logged out successfully', 'success');
    };

    return (
        <div className="App">
            <Navigation 
                onNewSession={handleNewSession} 
                currentStep={currentStep} 
                user={user} 
                onLogout={handleLogout} 
            />

            <main className="app-main">
                {toast && (
                    <div className={`toast toast-${toast.type}`}>
                        <span>{toast.type === 'success' ? '✓' : '✗'} {toast.message}</span>
                    </div>
                )}

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
                    <Route 
                        path="/login" 
                        element={
                            token ? <Navigate to="/" replace /> : 
                            <Login setToken={setToken} setUser={setUser} showToast={showToast} initialMode="login" />
                        } 
                    />
                    <Route 
                        path="/signup" 
                        element={
                            token ? <Navigate to="/" replace /> : 
                            <Login setToken={setToken} setUser={setUser} showToast={showToast} initialMode="signup" />
                        } 
                    />
                    <Route 
                        path="/" 
                        element={
                            <PrivateRoute token={token}>
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
                                            initialQuestion={firstQuestion}
                                            onComplete={handleInterviewComplete}
                                            token={token}
                                            showToast={showToast}
                                        />
                                    )}
                                </>
                            </PrivateRoute>
                        } 
                    />
                    <Route 
                        path="/sessions" 
                        element={
                            <PrivateRoute token={token}>
                                <SessionsList token={token} showToast={showToast} />
                            </PrivateRoute>
                        } 
                    />
                    <Route 
                        path="/summary/:sessionId" 
                        element={
                            <PrivateRoute token={token}>
                                <InterviewSummary token={token} showToast={showToast} onNewSession={handleNewSession} />
                            </PrivateRoute>
                        } 
                    />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </main>
        </div>
    );
}
export default App;