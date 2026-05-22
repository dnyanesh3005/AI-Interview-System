import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './InterviewSummary.css';

/* ─── Score ring (SVG circle) ─────────────────────────────────────────────── */
function ScoreRing({ score, size = 96, stroke = 8, label, color }) {
    const radius = (size - stroke) / 2;
    const circ   = 2 * Math.PI * radius;
    const fill   = circ * (1 - score / 100);

    return (
        <div className="score-ring-wrap">
            <svg width={size} height={size} className="score-ring-svg">
                <circle cx={size/2} cy={size/2} r={radius}
                    fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={stroke} />
                <circle cx={size/2} cy={size/2} r={radius}
                    fill="none" stroke={color} strokeWidth={stroke}
                    strokeDasharray={circ} strokeDashoffset={fill}
                    strokeLinecap="round"
                    style={{ transform:'rotate(-90deg)', transformOrigin:'50% 50%', transition:'stroke-dashoffset 1.2s ease' }}
                />
                <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle"
                    fill="#fff" fontSize={size * 0.22} fontWeight="700">
                    {score}
                </text>
            </svg>
            <span className="score-ring-label">{label}</span>
        </div>
    );
}

/* ─── Skill bar ───────────────────────────────────────────────────────────── */
function SkillBar({ name, score }) {
    const color =
        score >= 80 ? '#22c55e' :
        score >= 60 ? '#3b82f6' :
        score >= 40 ? '#f59e0b' : '#ef4444';

    return (
        <div className="skill-bar-row">
            <span className="skill-bar-name">{name}</span>
            <div className="skill-bar-track">
                <div className="skill-bar-fill"
                    style={{ width: `${score}%`, background: color }} />
            </div>
            <span className="skill-bar-score" style={{ color }}>{score}</span>
        </div>
    );
}

/* ─── Readiness Badge ─────────────────────────────────────────────────────── */
function ReadinessBadge({ readiness, score }) {
    const config = {
        'Strong':            { cls: 'badge-strong',    icon: '🏆', bg: '#16a34a' },
        'Moderate':          { cls: 'badge-moderate',  icon: '⚡', bg: '#d97706' },
        'Needs Preparation': { cls: 'badge-weak',      icon: '📚', bg: '#dc2626' },
    };
    const c = config[readiness] || config['Moderate'];
    return (
        <div className={`readiness-badge ${c.cls}`} style={{ background: c.bg }}>
            <span className="badge-icon">{c.icon}</span>
            <div className="badge-text">
                <span className="badge-title">Interview Readiness</span>
                <span className="badge-value">{readiness}</span>
            </div>
            <span className="badge-score">{score}/100</span>
        </div>
    );
}

/* ─── Main Component ──────────────────────────────────────────────────────── */
function InterviewSummary({ token, showToast, onNewSession }) {
    const { sessionId } = useParams();
    const navigate      = useNavigate();

    const [summary,    setSummary]    = useState(null);
    const [loading,    setLoading]    = useState(true);
    const [error,      setError]      = useState(null);
    const [expandedQA, setExpandedQA] = useState(null);
    const [activeTab,  setActiveTab]  = useState('evaluation'); // 'evaluation' | 'qa'

    const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

    useEffect(() => {
        if (token && sessionId) fetchSummary();
    }, [token, sessionId]);

    const fetchSummary = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/interview-summary/${sessionId}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) {
                let errMsg = `Server error ${res.status}`;
                try {
                    const errData = await res.json();
                    errMsg = errData.detail || errMsg;
                } catch (_) {}
                throw new Error(errMsg);
            }
            const data = await res.json();
            setSummary(data.summary);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!window.confirm('Delete this session permanently? This cannot be undone.')) return;
        try {
            const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
                method:  'DELETE',
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) {
                const e = await res.json();
                throw new Error(e.detail || 'Failed to delete');
            }
            showToast('Session deleted', 'success');
            navigate('/sessions');
        } catch (err) {
            showToast(err.message || 'Error deleting session', 'error');
        }
    };

    const downloadSummary = () => {
        if (!summary) return;
        const ev = summary.evaluation_report;
        let text = `AI INTERVIEW REPORT\n${'='.repeat(60)}\n\n`;
        text += `Candidate : ${summary.candidate_name}\n`;
        text += `Role      : ${summary.role}\n`;
        text += `Date      : ${new Date(summary.timestamp).toLocaleString()}\n`;
        text += `Questions : ${summary.total_questions}\n\n`;

        if (ev) {
            text += `EVALUATION REPORT\n${'-'.repeat(60)}\n`;
            text += `Final Score       : ${ev.final_score}/100\n`;
            text += `Interview Readiness: ${ev.interview_readiness}\n`;
            text += `Technical Score   : ${ev.technical_score}/100\n`;
            text += `Communication     : ${ev.communication_score}/100\n`;
            text += `Confidence        : ${ev.confidence_score}/100\n\n`;
            text += `Strengths:\n${(ev.strengths||[]).map(s=>`  - ${s}`).join('\n')}\n\n`;
            text += `Weak Areas:\n${(ev.weak_areas||[]).map(w=>`  - ${w}`).join('\n')}\n\n`;
            text += `Improvement Suggestions:\n${(ev.improvement_suggestions||[]).map(s=>`  - ${s}`).join('\n')}\n\n`;
            if (ev.skill_scores && Object.keys(ev.skill_scores).length) {
                text += `Skill Scores:\n`;
                Object.entries(ev.skill_scores).forEach(([k,v]) => { text += `  ${k}: ${v}/100\n`; });
            }
            text += '\n';
        }

        text += `Q&A PAIRS\n${'-'.repeat(60)}\n`;
        (summary.qa_pairs || []).forEach((p, i) => {
            text += `\nQ${i+1}: ${p.question}\nA: ${p.answer || '[Skipped]'}\n`;
        });

        const el = document.createElement('a');
        el.href     = 'data:text/plain;charset=utf-8,' + encodeURIComponent(text);
        el.download = `interview_report_${sessionId}.txt`;
        el.click();
    };

    /* ── Loading / Error states ───────────────────────────────────────────── */
    if (loading) return (
        <div className="summary-container">
            <div className="summary-loading">
                <div className="loading-spinner" />
                <p>Generating your evaluation report…</p>
            </div>
        </div>
    );
    if (error) return (
        <div className="summary-container">
            <div className="error-message">
                <p>Error: {error}</p>
                <button onClick={fetchSummary}>Retry</button>
            </div>
        </div>
    );
    if (!summary) return null;

    const ev = summary.evaluation_report;
    const skillEntries = ev?.skill_scores ? Object.entries(ev.skill_scores) : [];

    return (
        <div className="summary-container">

            {/* ── Header ───────────────────────────────────────────────────── */}
            <div className="summary-header">
                <div className="summary-header-left">
                    <h1>Interview Complete 🎉</h1>
                    <p className="summary-subtitle">
                        {summary.candidate_name} · {summary.role} ·{' '}
                        {new Date(summary.timestamp).toLocaleDateString()}
                    </p>
                </div>
                {ev && (
                    <ReadinessBadge
                        readiness={ev.interview_readiness}
                        score={ev.final_score}
                    />
                )}
            </div>

            {/* ── Score Rings ───────────────────────────────────────────────── */}
            {ev && (
                <div className="score-rings-row">
                    <ScoreRing score={ev.final_score}         label="Overall"       color="#6366f1" size={108} />
                    <ScoreRing score={ev.technical_score}     label="Technical"     color="#3b82f6" />
                    <ScoreRing score={ev.communication_score} label="Communication" color="#22c55e" />
                    <ScoreRing score={ev.confidence_score}    label="Confidence"    color="#f59e0b" />
                </div>
            )}

            {/* ── Stats row ────────────────────────────────────────────────── */}
            <div className="stats-row">
                <div className="stat-chip">
                    <span className="stat-num">{summary.total_questions}</span>
                    <span className="stat-lbl">Questions</span>
                </div>
                {ev && <>
                    <div className="stat-chip">
                        <span className="stat-num">{ev.questions_answered}</span>
                        <span className="stat-lbl">Answered</span>
                    </div>
                    <div className="stat-chip">
                        <span className="stat-num">{ev.questions_skipped}</span>
                        <span className="stat-lbl">Skipped</span>
                    </div>
                    <div className="stat-chip">
                        <span className="stat-num">{ev.avg_answer_length}</span>
                        <span className="stat-lbl">Avg chars</span>
                    </div>
                </>}
            </div>

            {/* ── Tabs ─────────────────────────────────────────────────────── */}
            <div className="summary-tabs">
                <button
                    className={`tab-btn ${activeTab === 'evaluation' ? 'active' : ''}`}
                    onClick={() => setActiveTab('evaluation')}
                    id="tab-evaluation"
                >
                    📊 Evaluation Report
                </button>
                <button
                    className={`tab-btn ${activeTab === 'qa' ? 'active' : ''}`}
                    onClick={() => setActiveTab('qa')}
                    id="tab-qa"
                >
                    💬 Q&amp;A Transcript ({(summary.qa_pairs || []).length})
                </button>
            </div>

            {/* ── Evaluation Tab ───────────────────────────────────────────── */}
            {activeTab === 'evaluation' && ev && (
                <div className="eval-tab">

                    {/* Strengths / Weak / Suggestions */}
                    <div className="eval-grid">
                        <div className="eval-card eval-strengths">
                            <h3>💪 Strengths</h3>
                            <ul>
                                {(ev.strengths || []).map((s, i) => (
                                    <li key={i}>{s}</li>
                                ))}
                            </ul>
                        </div>
                        <div className="eval-card eval-weaknesses">
                            <h3>🎯 Areas to Improve</h3>
                            <ul>
                                {(ev.weak_areas || []).map((w, i) => (
                                    <li key={i}>{w}</li>
                                ))}
                            </ul>
                        </div>
                        <div className="eval-card eval-suggestions">
                            <h3>💡 Suggestions</h3>
                            <ul>
                                {(ev.improvement_suggestions || []).map((s, i) => (
                                    <li key={i}>{s}</li>
                                ))}
                            </ul>
                        </div>
                    </div>

                    {/* Skill Scores */}
                    {skillEntries.length > 0 && (
                        <div className="skill-scores-section">
                            <h3>🛠 Skill Scores</h3>
                            <div className="skill-bars">
                                {skillEntries
                                    .sort((a, b) => b[1] - a[1])
                                    .map(([skill, score]) => (
                                        <SkillBar key={skill} name={skill} score={score} />
                                    ))}
                            </div>
                        </div>
                    )}

                    {/* Generation method note */}
                    <p className="eval-method-note">
                        {ev.generation_method === 'gemini'
                            ? '✨ Evaluation generated by Gemini AI'
                            : '📐 Evaluation generated using heuristic analysis'}
                    </p>
                </div>
            )}

            {/* No eval fallback */}
            {activeTab === 'evaluation' && !ev && (
                <div className="eval-tab">
                    <div className="eval-card" style={{ gridColumn: '1/-1' }}>
                        <h3>Performance Overview</h3>
                        {summary.analysis && (
                            <>
                                <div className="metric">
                                    <label>Knowledge Depth:</label>
                                    <span className="metric-value">{summary.analysis.depth_of_knowledge}</span>
                                </div>
                                <div className="metric">
                                    <label>Technical Accuracy:</label>
                                    <span className="metric-value">
                                        {(summary.analysis.technical_accuracy * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <div className="metric">
                                    <label>Communication:</label>
                                    <span className="metric-value">{summary.analysis.communication_clarity}</span>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}

            {/* ── Q&A Transcript Tab ────────────────────────────────────────── */}
            {activeTab === 'qa' && (
                <div className="qa-section">
                    <div className="qa-list">
                        {(summary.qa_pairs || []).map((pair, idx) => (
                            <div key={idx} className={`qa-card ${pair.answer === '[SKIPPED]' ? 'qa-skipped' : ''}`}>
                                <div
                                    className="qa-header"
                                    onClick={() => setExpandedQA(expandedQA === idx ? null : idx)}
                                >
                                    <div className="qa-title">
                                        <span className="qa-number">Q{idx + 1}</span>
                                        <span className="qa-question">{pair.question}</span>
                                    </div>
                                    <div className="qa-metadata">
                                        {pair.question_type && (
                                            <span className="type-badge">{pair.question_type}</span>
                                        )}
                                        {pair.difficulty && (
                                            <span className="difficulty-badge">{pair.difficulty}</span>
                                        )}
                                        {pair.answer === '[SKIPPED]' && (
                                            <span className="skipped-badge">Skipped</span>
                                        )}
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
                                        <div className={`answer-box ${pair.answer === '[SKIPPED]' ? 'answer-skipped' : ''}`}>
                                            <h4>Your Answer</h4>
                                            <p>{pair.answer === '[SKIPPED]'
                                                ? '— Question was skipped —'
                                                : (pair.answer || 'No answer provided')}</p>
                                        </div>
                                        <div className="qa-stats">
                                            <span>Category: {pair.category || pair.question_type || 'N/A'}</span>
                                            {pair.answered_at && (
                                                <span>At: {new Date(pair.answered_at).toLocaleTimeString()}</span>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* ── Actions ──────────────────────────────────────────────────── */}
            <div className="summary-actions">
                <button className="action-btn download-btn" onClick={downloadSummary} id="btn-download-summary">
                    📥 Download Report
                </button>
                <button className="action-btn new-session-btn" onClick={onNewSession} id="btn-new-interview">
                    🔄 New Interview
                </button>
                <button className="action-btn delete-summary-btn" onClick={handleDelete} id="btn-delete-session">
                    🗑️ Delete Session
                </button>
            </div>
        </div>
    );
}

export default InterviewSummary;