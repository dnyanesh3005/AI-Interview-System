import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './SessionsList.css';

function SessionsList({ token, showToast, onResumeSession }) {
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [resuming, setResuming] = useState(false);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

    useEffect(() => {
        if (token) {
            fetchSessions();
        }
    }, [token]);

    const fetchSessions = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/sessions`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 401) {
                // Token is stale (backend restarted) — force re-login
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '/login';
                return;
            }

            if (!response.ok) {
                throw new Error('Failed to fetch sessions');
            }

            const data = await response.json();
            setSessions(data.sessions || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const viewSummary = (sessionId) => {
        navigate(`/summary/${sessionId}`);
    };

    const handleDeleteSession = async (sessionId, e) => {
        e.stopPropagation();
        if (!window.confirm("Are you sure you want to delete this session permanently?")) return;

        try {
            const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Failed to delete session');
            }

            showToast('Session deleted successfully', 'success');
            fetchSessions();
        } catch (err) {
            showToast(err.message || 'Error deleting session', 'error');
        }
    };

    const handleResume = async (sessionId, e) => {
        e.stopPropagation();
        setResuming(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/resume-interview/${sessionId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Failed to resume session');
            }

            const data = await response.json();
            if (data.success) {
                if (data.interview_complete) {
                    showToast(data.message || 'Interview already completed!', 'success');
                    fetchSessions();
                } else if (onResumeSession) {
                    showToast('Interview session restored!', 'success');
                    onResumeSession(data);
                }
            } else {
                throw new Error('Could not resume session');
            }
        } catch (err) {
            showToast(err.message || 'Error resuming session', 'error');
        } finally {
            setResuming(false);
        }
    };

    return (
        <div className="sessions-container">
            {resuming && (
                <div className="loading-overlay">
                    <div className="spinner"></div>
                    <p>Rebuilding AI context & restoring session...</p>
                </div>
            )}
            <div className="sessions-header">
                <h1>Interview Sessions</h1>
                <button className="refresh-btn" onClick={fetchSessions}>
                    🔄 Refresh
                </button>
            </div>

            {loading && <div className="loading">Loading sessions...</div>}

            {error && (
                <div className="error-message">
                    <p>{error}</p>
                    <button onClick={fetchSessions}>Retry</button>
                </div>
            )}

            {!loading && !error && (
                <>
                    {sessions.length === 0 ? (
                        <div className="empty-state">
                            <p>No interview sessions yet</p>
                            <button onClick={() => navigate('/')}>Start New Interview</button>
                        </div>
                    ) : (
                        <div className="sessions-table">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Candidate Name</th>
                                        <th>Role</th>
                                        <th>Session ID</th>
                                        <th>Date</th>
                                        <th>Status</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {sessions.map(session => (
                                        <tr key={session.session_id}>
                                            <td>{session.candidate_name}</td>
                                            <td>{session.role}</td>
                                            <td className="session-id">
                                                <code>{session.session_id.substring(0, 8)}...</code>
                                            </td>
                                            <td>{new Date(session.created_at).toLocaleDateString()}</td>
                                            <td>
                                                <span className={`status-badge ${session.status}`}>
                                                    {session.status === 'in_progress' ? '⏳ In Progress' : '✅ Completed'}
                                                </span>
                                            </td>
                                            <td>
                                                <div className="actions-cell">
                                                    {session.status === 'in_progress' ? (
                                                        <button
                                                            className="resume-btn"
                                                            onClick={(e) => handleResume(session.session_id, e)}
                                                            disabled={resuming}
                                                        >
                                                            ⚡ Resume
                                                        </button>
                                                    ) : (
                                                        <button
                                                            className="view-btn"
                                                            onClick={() => viewSummary(session.session_id)}
                                                            disabled={resuming}
                                                        >
                                                            View
                                                        </button>
                                                    )}
                                                    <button
                                                        className="delete-btn"
                                                        onClick={(e) => handleDeleteSession(session.session_id, e)}
                                                        disabled={resuming}
                                                    >
                                                        🗑️ Delete
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

export default SessionsList;