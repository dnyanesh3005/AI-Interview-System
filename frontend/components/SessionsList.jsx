import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './SessionsList.css';

function SessionsList() {
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

    useEffect(() => {
        fetchSessions();
    }, []);

    const fetchSessions = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/sessions`);

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
        // This would ideally navigate to summary view
        window.location.href = `/#/summary/${sessionId}`;
    };

    return (
        <div className="sessions-container">
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
                                                <button
                                                    className="view-btn"
                                                    onClick={() => viewSummary(session.session_id)}
                                                >
                                                    View Summary
                                                </button>
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