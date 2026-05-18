import React, { useState, useEffect } from 'react';
import './InterviewFlow.css';

function InterviewFlow({ sessionId, resumeData, role, onComplete }) {
    const [currentQuestion, setCurrentQuestion] = useState(null);
    const [questionNumber, setQuestionNumber] = useState(1);
    const [totalQuestions] = useState(5);
    const [answer, setAnswer] = useState('');
    const [isAnswering, setIsAnswering] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [answeredQuestions, setAnsweredQuestions] = useState([]);
    const [answerStartTime, setAnswerStartTime] = useState(null);

    const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

    useEffect(() => {
        // Fetch initial question
        if (questionNumber === 1) {
            fetchCurrentQuestion();
        }
    }, []);

    const fetchCurrentQuestion = async () => {
        setLoading(true);
        setError(null);

        try {
            // In a real implementation, this would be a separate endpoint
            // For now, we've already got the first question from start-interview
            // This is a placeholder for fetching subsequent questions
            setLoading(false);
        } catch (err) {
            setError(err.message);
            setLoading(false);
        }
    };

    const handleAnswerSubmit = async () => {
        if (!answer.trim()) {
            alert('Please provide an answer before submitting');
            return;
        }

        setIsAnswering(true);
        setError(null);

        try {
            const duration = answerStartTime ? Math.round((Date.now() - answerStartTime) / 1000) : 0;

            const response = await fetch(`${API_BASE_URL}/submit-answer`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    question_id: currentQuestion.question_id,
                    answer: answer,
                    duration_seconds: duration,
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to submit answer');
            }

            const data = await response.json();

            // Store answered question
            setAnsweredQuestions([
                ...answeredQuestions,
                {
                    question: currentQuestion.question_text,
                    answer: answer,
                    questionNumber: questionNumber,
                }
            ]);

            // Check if interview is complete
            if (data.interview_complete) {
                onComplete();
            } else {
                // Move to next question
                setCurrentQuestion(data.question);
                setQuestionNumber(questionNumber + 1);
                setAnswer('');
                setAnswerStartTime(null);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setIsAnswering(false);
        }
    };

    const handleAnswerChange = (e) => {
        if (!answerStartTime) {
            setAnswerStartTime(Date.now());
        }
        setAnswer(e.target.value);
    };

    if (loading) {
        return (
            <div className="interview-container">
                <div className="loading">Loading question...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="interview-container">
                <div className="error-message">
                    <p>Error: {error}</p>
                    <button onClick={() => window.location.reload()}>Retry</button>
                </div>
            </div>
        );
    }

    return (
        <div className="interview-container">
            <div className="interview-header">
                <div className="interview-title">
                    <h1>Technical Interview</h1>
                    <p>Role: <strong>{role}</strong> | Candidate: <strong>{resumeData.candidate_name}</strong></p>
                </div>

                <div className="progress-section">
                    <div className="progress-bar">
                        <div
                            className="progress-fill"
                            style={{ width: `${(questionNumber / totalQuestions) * 100}%` }}
                        ></div>
                    </div>
                    <p className="progress-text">Question {questionNumber} of {totalQuestions}</p>
                </div>
            </div>

            <div className="interview-content">
                {currentQuestion && (
                    <div className="question-section">
                        <div className="question-metadata">
                            <span className="question-type">{currentQuestion.question_type}</span>
                            <span className="difficulty-badge">{currentQuestion.difficulty}</span>
                            <span className="category-badge">{currentQuestion.category}</span>
                        </div>

                        <h2 className="question-text">{currentQuestion.question_text}</h2>

                        <div className="question-hints">
                            <p className="hint-label">Expected answer depth:</p>
                            <p className="hint-text">{currentQuestion.expected_depth}</p>
                        </div>

                        {currentQuestion.context_used && currentQuestion.context_used.length > 0 && (
                            <details className="context-details">
                                <summary>View context used for this question</summary>
                                <div className="context-content">
                                    {currentQuestion.context_used.map((ctx, idx) => (
                                        <p key={idx}>{ctx}...</p>
                                    ))}
                                </div>
                            </details>
                        )}
                    </div>
                )}

                <div className="answer-section">
                    <label htmlFor="answer">Your Answer:</label>
                    <textarea
                        id="answer"
                        className="answer-input"
                        placeholder="Type your detailed answer here. Take your time to provide a thoughtful response."
                        value={answer}
                        onChange={handleAnswerChange}
                        disabled={isAnswering}
                        rows={10}
                    />

                    <div className="answer-info">
                        <span className="char-count">{answer.length} characters</span>
                        <span className="timer">
                            {answerStartTime && (
                                <>Time: {Math.round((Date.now() - answerStartTime) / 1000)}s</>
                            )}
                        </span>
                    </div>

                    <button
                        className="submit-button"
                        onClick={handleAnswerSubmit}
                        disabled={isAnswering || !answer.trim()}
                    >
                        {isAnswering ? 'Submitting...' : 'Submit Answer'}
                    </button>
                </div>
            </div>

            {answeredQuestions.length > 0 && (
                <div className="previous-answers">
                    <h3>Previous Answers</h3>
                    <div className="qa-summary">
                        {answeredQuestions.map((qa, idx) => (
                            <div key={idx} className="qa-item">
                                <p className="qa-question"><strong>Q{idx + 1}:</strong> {qa.question}</p>
                                <p className="qa-answer"><strong>Your Answer:</strong> {qa.answer.substring(0, 100)}...</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

export default InterviewFlow;