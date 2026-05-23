import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import './App.css';
import ResumeUpload from '../components/ResumeUpload.jsx';
import RoleSelection from '../components/RoleSelection.jsx';
import InterviewFlow from '../components/InterviewFlow.jsx';
import InterviewSummary from '../components/InterviewSummary.jsx';
import SessionsList from '../components/SessionsList.jsx';
import Navigation from '../components/Navigation.jsx';
import Login from '../components/Login.jsx';
import LandingPage from '../components/LandingPage.jsx';

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
    const [totalQuestions, setTotalQuestions] = useState(5);
    const [currentStep, setCurrentStep] = useState('resume-upload');
    const [loading, setLoading] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState('Processing...');
    const [error, setError] = useState(null);
    const [toast, setToast] = useState(null); // { message: '', type: 'success' | 'error' }

    const navigate = useNavigate();
    const location = useLocation();
    const [showGuide, setShowGuide] = useState(() => {
        const stored = localStorage.getItem('showGuide');
        return stored !== 'false';
    });

    const toggleGuide = () => {
        setShowGuide(prev => {
            const next = !prev;
            localStorage.setItem('showGuide', String(next));
            return next;
        });
    };
    const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
    const HEALTH_URL = '/health';

    const showToast = (message, type = 'success') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 4000);
    };

    // Poll backend health until it's ready (handles slow startup)
    const waitForBackend = async (maxWaitMs = 30000) => {
        const start = Date.now();
        while (Date.now() - start < maxWaitMs) {
            try {
                const res = await fetch(HEALTH_URL);
                if (res.ok) return true;
            } catch (_) {}
            await new Promise(r => setTimeout(r, 1500));
        }
        return false;
    };

    useEffect(() => {
        if (token) {
            fetch(HEALTH_URL).catch(() => {
                console.warn('Backend not available yet.');
            });
        }
    }, [token]);

    const handleResumeUpload = async (file) => {
        setLoading(true);
        setLoadingMessage('Connecting to backend...');
        setError(null);

        const messageIntervals = [];

        try {
            // Wait for backend to be ready (handles cold-start delay)
            const ready = await waitForBackend(20000);
            if (!ready) {
                throw new Error('Backend is not responding. Make sure python main.py is running.');
            }

            setLoadingMessage('Uploading your resume...');
            messageIntervals.push(
                setTimeout(() => setLoadingMessage('Extracting sections and parsing text...'), 600),
                setTimeout(() => setLoadingMessage('Analyzing candidate skills using AI models...'), 1400),
                setTimeout(() => setLoadingMessage('Structuring candidate profile...'), 2400)
            );

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

            setLoadingMessage('Success! Loading role selection...');
            await new Promise(resolve => setTimeout(resolve, 600));

            setResumeData(data.data);
            setCurrentStep('role-selection');
            showToast('Resume parsed successfully!', 'success');
        } catch (err) {
            const msg = err.message || 'Error uploading resume. Make sure backend is running.';
            setError(msg);
            showToast(msg, 'error');
            console.error('Resume upload error:', err);
        } finally {
            messageIntervals.forEach(clearTimeout);
            setLoading(false);
        }
    };

    const handleRoleSelection = async (role, totalQuestions) => {
        setTotalQuestions(totalQuestions);
        setLoading(true);
        setLoadingMessage('Selecting target role...');
        setError(null); // clear any stale errors from previous step

        let intervals = [];

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
            
            setLoadingMessage('Initializing AI interviewer...');
            intervals = [
                setTimeout(() => setLoadingMessage('Generating personalized questions...'), 700),
                setTimeout(() => setLoadingMessage('Preparing voice and video modules...'), 1700),
            ];
            
            await startInterview(role, totalQuestions);
        } catch (err) {
            setError(err.message || 'Error selecting role');
            showToast(err.message || 'Error selecting role', 'error');
            console.error('Role selection error:', err);
        } finally {
            intervals.forEach(clearTimeout);
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
            setTotalQuestions(data.total_questions || totalQuestions);
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
        setTotalQuestions(5);
        setCurrentStep('resume-upload');
        navigate(`/summary/${finalSessionId}`);
    };

    const handleNewSession = () => {
        setSessionId(null);
        setResumeData(null);
        setSelectedRole(null);
        setFirstQuestion(null);
        setTotalQuestions(5);
        setCurrentStep('resume-upload');
        setError(null);
        navigate('/');
    };

    const handleResumeSession = (sessionData) => {
        setSessionId(sessionData.session_id);
        setResumeData(sessionData.resume_data);
        setSelectedRole(sessionData.role);
        setFirstQuestion(sessionData.question);
        setTotalQuestions(sessionData.total_questions);
        setCurrentStep('interview');
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

    const isAuthPage = location.pathname === '/login' || location.pathname === '/signup';
    const isFullBleedPage = isAuthPage || (!user && location.pathname === '/');

    return (
        <div className={`App ${isFullBleedPage ? 'auth-page' : ''}`}>
            {user && !isAuthPage && (
                <Navigation 
                    onNewSession={handleNewSession} 
                    currentStep={currentStep} 
                    user={user} 
                    onLogout={handleLogout} 
                    showGuide={showGuide}
                    onToggleGuide={toggleGuide}
                />
            )}

            <main className={`app-main ${isFullBleedPage ? 'auth-main' : ''}`}>
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
                        <p>{loadingMessage}</p>
                    </div>
                )}

                {user ? (
                    <div className={`app-layout-container ${showGuide ? 'with-sidebar' : 'without-sidebar'}`}>
                        <div className="app-route-content">
                            <Routes>
                                <Route 
                                    path="/login" 
                                    element={<Navigate to="/" replace />} 
                                />
                                <Route 
                                    path="/signup" 
                                    element={<Navigate to="/" replace />} 
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
                                                        totalQuestions={totalQuestions}
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
                                            <SessionsList token={token} showToast={showToast} onResumeSession={handleResumeSession} />
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
                        </div>

                        <aside className={`info-sidebar ${showGuide ? 'open' : 'collapsed'}`}>
                            <div className="info-section">
                                <div className="info-header">
                                    <h3>What happens next?</h3>
                                    <button className="close-guide-btn" onClick={toggleGuide} title="Hide Guide">✕</button>
                                </div>
                                <ul>
                                    <li className={`step-item ${currentStep === 'resume-upload' && location.pathname === '/' ? 'step-active' : ''} ${currentStep !== 'resume-upload' || location.pathname !== '/' ? 'step-done' : ''}`}>
                                        <span className="step-status-icon"></span>
                                        <div className="step-content">
                                            <span className="step-title">Upload Resume</span>
                                            <p className="step-subtext">AI parses your resume to instantly extract key skills, work experience, and educational background.</p>
                                        </div>
                                    </li>
                                    <li className={`step-item ${currentStep === 'role-selection' && location.pathname === '/' ? 'step-active' : ''} ${(currentStep !== 'resume-upload' && currentStep !== 'role-selection') || location.pathname !== '/' ? 'step-done' : ''}`}>
                                        <span className="step-status-icon"></span>
                                        <div className="step-content">
                                            <span className="step-title">Choose Target Role</span>
                                            <p className="step-subtext">Select your target engineering or analyst position to align interview questions with role-specific expectations.</p>
                                        </div>
                                    </li>
                                    <li className={`step-item ${currentStep === 'role-selection' && location.pathname === '/' ? 'step-active' : ''} ${(currentStep !== 'resume-upload' && currentStep !== 'role-selection') || location.pathname !== '/' ? 'step-done' : ''}`}>
                                        <span className="step-status-icon"></span>
                                        <div className="step-content">
                                            <span className="step-title">Generate AI Questions</span>
                                            <p className="step-subtext">Dynamic, personalized technical questions are generated specifically based on your resume and target path.</p>
                                        </div>
                                    </li>
                                    <li className={`step-item ${currentStep === 'interview' && location.pathname === '/' ? 'step-active' : ''} ${location.pathname.startsWith('/summary/') ? 'step-done' : ''}`}>
                                        <span className="step-status-icon"></span>
                                        <div className="step-content">
                                            <span className="step-title">Conduct Live Interview</span>
                                            <p className="step-subtext">Answer questions in real-time. Use optional camera and automatic voice transcription for seamless input.</p>
                                        </div>
                                    </li>
                                    <li className={`step-item ${location.pathname.startsWith('/summary/') ? 'step-active' : ''}`}>
                                        <span className="step-status-icon"></span>
                                        <div className="step-content">
                                            <span className="step-title">Detailed Summary Report</span>
                                            <p className="step-subtext">Get granular feedback, strengths and weaknesses, skill scores, and actionable feedback metrics.</p>
                                        </div>
                                    </li>
                                </ul>
                            </div>
                        </aside>
                    </div>
                ) : (
                    <Routes>
                        <Route 
                            path="/" 
                            element={<LandingPage />} 
                        />
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
                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                )}
            </main>
        </div>
    );
}
export default App;