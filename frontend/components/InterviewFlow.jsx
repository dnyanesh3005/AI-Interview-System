import React, { useState, useEffect, useRef } from 'react';
import './InterviewFlow.css';

function InterviewFlow({ sessionId, resumeData, role, initialQuestion, onComplete, token, showToast }) {
    const [currentQuestion, setCurrentQuestion] = useState(initialQuestion || null);
    const [questionNumber, setQuestionNumber] = useState(1);
    const [totalQuestions, setTotalQuestions] = useState(5);
    const [answer, setAnswer] = useState('');
    const [isAnswering, setIsAnswering] = useState(false);
    const [isSkipping, setIsSkipping] = useState(false);
    const [loading, setLoading] = useState(!initialQuestion);
    const [error, setError] = useState(null);
    const [answeredQuestions, setAnsweredQuestions] = useState([]);
    const [answerStartTime, setAnswerStartTime] = useState(null);
    const [recordingDuration, setRecordingDuration] = useState(0);

    // Video/Audio Recording States
    const [isRecording, setIsRecording] = useState(false);
    const [mediaStream, setMediaStream] = useState(null);
    const videoRef = useRef(null);
    const recognitionRef = useRef(null);
    const timerRef = useRef(null);

    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

    useEffect(() => {
        // If we received an initialQuestion from parent, use it directly
        if (initialQuestion) {
            setCurrentQuestion(initialQuestion);
            setLoading(false);
        }
    }, [initialQuestion]);

    useEffect(() => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            
            recognition.onresult = (event) => {
                let finalTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript + ' ';
                    }
                }
                if (finalTranscript) {
                    setAnswer((prev) => prev + finalTranscript);
                }
            };
            
            recognition.onerror = (event) => {
                console.error("Speech recognition error", event.error);
            };
            
            recognitionRef.current = recognition;
        }

        return () => {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
            }
        };
    }, []);

    // Cleanup media tracks when component unmounts
    useEffect(() => {
        return () => {
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
            }
            if (timerRef.current) clearInterval(timerRef.current);
        };
    }, [mediaStream]);

    useEffect(() => {
        if (videoRef.current && mediaStream) {
            videoRef.current.srcObject = mediaStream;
        }
    }, [mediaStream, isRecording]);

    const toggleRecording = async () => {
        if (isRecording) {
            // Stop recording
            setIsRecording(false);
            if (recognitionRef.current) {
                recognitionRef.current.stop();
            }
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                setMediaStream(null);
            }
            if (timerRef.current) {
                clearInterval(timerRef.current);
                timerRef.current = null;
            }
        } else {
            // Start recording
            try {
                if (!answerStartTime) {
                    setAnswerStartTime(Date.now());
                }
                setRecordingDuration(0);
                timerRef.current = setInterval(() => {
                    setRecordingDuration(prev => prev + 1);
                }, 1000);
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                setMediaStream(stream);
                setIsRecording(true);

                if (recognitionRef.current) {
                    recognitionRef.current.start();
                }
            } catch (err) {
                setError("Could not access camera/microphone. Please allow permissions.");
                console.error("Media access error:", err);
            }
        }
    };

    const handleSkipQuestion = async () => {
        if (!currentQuestion) return;
        setIsSkipping(true);
        setError(null);

        // Stop any active recording first
        if (isRecording) {
            setIsRecording(false);
            if (recognitionRef.current) recognitionRef.current.stop();
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                setMediaStream(null);
            }
            if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
        }

        try {
            const response = await fetch(`${API_BASE_URL}/skip-question`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    question_id: currentQuestion.question_id,
                }),
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Failed to skip question');
            }

            const data = await response.json();

            setAnsweredQuestions(prev => [
                ...prev,
                {
                    question: currentQuestion.question_text,
                    answer: null,
                    questionNumber,
                    skipped: true,
                }
            ]);

            if (data.interview_complete) {
                onComplete(sessionId);
            } else {
                setCurrentQuestion(data.question);
                setQuestionNumber(prev => prev + 1);
                if (data.total_questions) setTotalQuestions(data.total_questions);
                setAnswer('');
                setAnswerStartTime(null);
                setRecordingDuration(0);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setIsSkipping(false);
        }
    };

    const handleAnswerSubmit = async () => {
        if (!answer.trim()) {
            alert('Please record your answer before submitting. Use the Start Video Response button.');
            return;
        }

        if (!currentQuestion) {
            setError('No question loaded. Please refresh the page.');
            return;
        }

        setIsAnswering(true);
        setError(null);

        try {
            const duration = answerStartTime ? Math.round((Date.now() - answerStartTime) / 1000) : 0;

            const response = await fetch(`${API_BASE_URL}/submit-answer`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    question_id: currentQuestion.question_id,
                    answer: answer,
                    duration_seconds: duration,
                }),
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Failed to submit answer');
            }

            const data = await response.json();

            // Store answered question
            setAnsweredQuestions(prev => [
                ...prev,
                {
                    question: currentQuestion.question_text,
                    answer: answer,
                    questionNumber: questionNumber,
                }
            ]);

            // Check if interview is complete
            if (data.interview_complete) {
                onComplete(sessionId);
            } else {
                // Move to next question
                setCurrentQuestion(data.question);
                setQuestionNumber(prev => prev + 1);
                if (data.total_questions) setTotalQuestions(data.total_questions);
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

    const formatDuration = (secs) => {
        const m = Math.floor(secs / 60).toString().padStart(2, '0');
        const s = (secs % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    };

    if (loading) {
        return (
            <div className="interview-container">
                <div className="loading">Loading question...</div>
            </div>
        );
    }

    if (error && !currentQuestion) {
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
                    <p>Role: <strong>{role}</strong> | Candidate: <strong>{resumeData?.candidate_name || 'Candidate'}</strong></p>
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
                {currentQuestion ? (
                    <div className="question-section">
                        <div className="question-metadata">
                            <span className="question-type">{currentQuestion.question_type}</span>
                            <span className="difficulty-badge">{currentQuestion.difficulty}</span>
                            <span className="category-badge">{currentQuestion.category}</span>
                        </div>

                        <h2 className="question-text">{currentQuestion.question_text}</h2>

                        {currentQuestion.expected_depth && (
                            <div className="question-hints">
                                <p className="hint-label">Expected answer depth:</p>
                                <p className="hint-text">{currentQuestion.expected_depth}</p>
                            </div>
                        )}

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
                ) : (
                    <div className="question-section">
                        <p className="loading">Preparing your question...</p>
                    </div>
                )}

                    <div className="answer-section">
                        {error && (
                            <div className="error-notification-bar">
                                <div className="error-content">
                                    <span className="error-icon">⚠️</span>
                                    <span className="error-text">Failed to submit: {error}</span>
                                </div>
                                <button 
                                    className="retry-submission-btn"
                                    onClick={handleAnswerSubmit}
                                    disabled={isAnswering || isSkipping}
                                >
                                    🔄 Retry Submission
                                </button>
                            </div>
                        )}

                        <label>Your Response:</label>
                        <div className="recording-controls">
                            <button
                                id="toggle-recording-btn"
                                className={`record-button ${isRecording ? 'recording' : ''}`}
                                onClick={toggleRecording}
                                disabled={isAnswering || isSkipping}
                            >
                                {isRecording ? '⏹ Stop Recording' : '⏺ Start Video Response'}
                            </button>
                            {isRecording && (
                                <span className="recording-indicator">
                                    🔴 Recording — {formatDuration(recordingDuration)}
                                </span>
                            )}
                        </div>

                        {isRecording && (
                            <div className="video-preview-container">
                                <video
                                    ref={videoRef}
                                    autoPlay
                                    muted
                                    playsInline
                                    style={{ width: '100%', maxHeight: '300px', objectFit: 'cover', display: 'block' }}
                                />
                            </div>
                        )}

                        {answer && (
                            <div className="transcript-preview">
                                <p className="transcript-label">📝 Transcription:</p>
                                <p className="transcript-text">{answer}</p>
                            </div>
                        )}

                        <div className="answer-actions">
                            <button
                                id="skip-question-btn"
                                className="skip-button"
                                onClick={handleSkipQuestion}
                                disabled={isAnswering || isSkipping || isRecording}
                            >
                                {isSkipping ? 'Skipping...' : '⏭ Skip Question'}
                            </button>
                            <button
                                id="submit-answer-btn"
                                className="submit-button"
                                onClick={handleAnswerSubmit}
                                disabled={isAnswering || isSkipping || !answer.trim() || !currentQuestion}
                            >
                                {isAnswering ? 'Submitting...' : 'Submit Answer'}
                            </button>
                        </div>
                    </div>
            </div>

            {answeredQuestions.length > 0 && (
                <div className="previous-answers">
                    <h3>Previous Answers</h3>
                    <div className="qa-summary">
                        {answeredQuestions.map((qa, idx) => (
                            <div key={idx} className={`qa-item ${qa.skipped ? 'qa-skipped' : ''}`}>
                                <p className="qa-question"><strong>Q{idx + 1}:</strong> {qa.question}</p>
                                {qa.skipped
                                    ? <p className="qa-skipped-label">⏭ Skipped</p>
                                    : <p className="qa-answer"><strong>Your Answer:</strong> {qa.answer.substring(0, 100)}...</p>
                                }
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {isAnswering && (
                <div className="submitting-overlay">
                    <div className="submitting-card">
                        <div className="submitting-spinner"></div>
                        <h3>Uploading Response</h3>
                        <p>Uploading and analyzing transcript...</p>
                    </div>
                </div>
            )}
        </div>
    );
}

export default InterviewFlow;