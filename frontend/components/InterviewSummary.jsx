import React, { useState, useEffect } from 'react';
import './InterviewSummary.css';

function InterviewSummary({ sessionId, onNewSession }) {
    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [expandedQA, setExpandedQA] = useState(null);

    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

    useEffect(() => {
        fetchSummary();
    }, []);

    const fetchSummary = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/interview-summary/${sessionId}`);

            if (!response.ok) {
                throw new Error('Failed to fetch summary');
            }

            const data = await response.json();
            setSummary(data.summary);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const downloadSummary = () => {
        const summaryText = generateSummaryText();
        const element = document.createElement('a');
        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(summaryText));
        element.setAttribute('download', `interview_summary_${sessionId}.txt`);
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    };

    const generateSummaryText = () => {
        if (!summary) return '';

        let text = `INTERVIEW SUMMARY\n`;
        text += `${'='.repeat(60)}\n\n`;
        text += `Session ID: ${summary.session_id}\n`;
        text += `Candidate: ${summary.candidate_name}\n`;
        text += `Role: ${summary.role}\n`;
        text += `Date: ${new Date(summary.timestamp).toLocaleString()}\n`;
        text += `Total Questions: ${summary.total_questions}\n\n`;

        text += `Q&A PAIRS\n`;
        text += `${'-'.repeat(60)}\n`;
        summary.qa_pairs.forEach((pair, idx) => {
            text += `\nQuestion ${idx + 1}:\n`;
            text += `Type: ${pair.question_type}\n`;
            text += `Difficulty: ${pair.difficulty}\n`;
            text += `${pair.question}\n\n`;
            text += `Answer:\n`;
            text += `${pair.answer || 'No answer provided'}\n`;
            text += `${'-'.repeat(60)}\n`;
        });

        if (summary.analysis) {
            text += `\nANALYSIS\n`;
            text += `${'-'.repeat(60)}\n`;
            text += `Knowledge Depth: ${summary.analysis.depth_of_knowledge}\n`;
            text += `Technical Accuracy: ${(summary.analysis.technical_accuracy * 100).toFixed(1)}%\n`;
            text += `Communication: ${summary.analysis.communication_clarity}\n`;
            text += `Domain Relevance: ${summary.analysis.domain_relevance}\n\n`;

            if (summary.analysis.recommendations) {
                text += `Recommendations:\n`;
                summary.analysis.recommendations.forEach(rec => {
                    text += `- ${rec}\n`;
                });
            }
        }

        return text;
    };

    if (loading) {
        return (
            <div className="summary-container">
                <div className="loading">Loading interview summary...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="summary-container">
                <div className="error-message">
                    <p>Error: {error}</p>
                    <button onClick={fetchSummary}>Retry</button>
                </div>
            </div>
        );
    }

    return (
        <div className="summary-container">
            <div className="summary-header">
                <h1>Interview Summary</h1>
                <p className="session-info">
                    Session ID: <code>{sessionId}</code>
                </p>
            </div>

            {summary && (
                <>
                    <div className="summary-overview">
                        <div className="overview-card">
                            <h3>Candidate Information</h3>
                            <div className="info-item">
                                <label>Name:</label>
                                <span>{summary.candidate_name}</span>
                            </div>
                            <div className="info-item">
                                <label>Target Role:</label>
                                <span>{summary.role}</span>
                            </div>
                            <div className="info-item">
                                <label>Interview Date:</label>
                                <span>{new Date(summary.timestamp).toLocaleString()}</span>
                            </div>
                            <div className="info-item">
                                <label>Questions Completed:</label>
                                <span>{summary.total_questions}</span>
                            </div>
                        </div>

                        {summary.analysis && (
                            <div className="overview-card">
                                <h3>Performance Analysis</h3>
                                <div className="metric">
                                    <label>Knowledge Depth:</label>
                                    <span className="metric-value">{summary.analysis.depth_of_knowledge}</span>
                                </div>
                                <div className="metric">
                                    <label>Technical Accuracy:</label>
                                    <div className="accuracy-bar">
                                        <div
                                            className="accuracy-fill"
                                            style={{ width: `${summary.analysis.technical_accuracy * 100}%` }}
                                        ></div>
                                    </div>
                                    <span>{(summary.analysis.technical_accuracy * 100).toFixed(1)}%</span>
                                </div>
                                <div className="metric">
                                    <label>Communication:</label>
                                    <span className="metric-value">{summary.analysis.communication_clarity}</span>
                                </div>
                                <div className="metric">
                                    <label>Domain Relevance:</label>
                                    <span className="metric-value">{summary.analysis.domain_relevance}</span>
                                </div>
                            </div>
                        )}
                    </div>

                    {summary.analysis && summary.analysis.recommendations && (
                        <div className="recommendations-section">
                            <h3>Recommendations</h3>
                            <ul className="recommendations-list">
                                {summary.analysis.recommendations.map((rec, idx) => (
                                    <li key={idx}>{rec}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <div className="qa-section">
                        <h2>Q&A Pairs</h2>
                        <div className="qa-list">
                            {summary.qa_pairs.map((pair, idx) => (
                                <div key={idx} className="qa-card">
                                    <div
                                        className="qa-header"
                                        onClick={() => setExpandedQA(expandedQA === idx ? null : idx)}
                                    >
                                        <div className="qa-title">
                                            <span className="qa-number">Q{idx + 1}</span>
                                            <span className="qa-question">{pair.question}</span>
                                        </div>
                                        <div className="qa-metadata">
                                            <span className="type-badge">{pair.question_type}</span>
                                            <span className="difficulty-badge">{pair.difficulty}</span>
                                            <span className="expand-icon">
                                                {expandedQA === idx ? '▼' : '▶'}
                                            </span>
                                        </div>
                                    </div>

                                    {expandedQA === idx && (
                                        <div className="qa-content">
                                            <div className="question-box">
                                                <h4>Question</h4>
                                                <p>{pair.question}</p>
                                            </div>

                                            <div className="answer-box">
                                                <h4>Your Answer</h4>
                                                <p>{pair.answer || 'No answer provided'}</p>
                                            </div>

                                            <div className="qa-stats">
                                                <span>Category: {pair.category || 'N/A'}</span>
                                                <span>Answered: {pair.answered_at ? new Date(pair.answered_at).toLocaleString() : 'N/A'}</span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="summary-actions">
                        <button className="download-btn" onClick={downloadSummary}>
                            📥 Download Summary
                        </button>
                        <button className="new-session-btn" onClick={onNewSession}>
                            🔄 Start New Interview
                        </button>
                    </div>
                </>
            )}
        </div>
    );
}

export default InterviewSummary;