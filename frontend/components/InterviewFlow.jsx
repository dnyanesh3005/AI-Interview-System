import React, { useState, useEffect, useRef } from 'react';
import './InterviewFlow.css';

function InterviewFlow({ sessionId, resumeData, role, initialQuestion, totalQuestions: propTotalQuestions = 5, onComplete, token, showToast }) {
    const [currentQuestion, setCurrentQuestion] = useState(initialQuestion || null);
    const [questionNumber, setQuestionNumber] = useState(1);
    const [totalQuestions, setTotalQuestions] = useState(propTotalQuestions);
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
    const [videoBlob, setVideoBlob] = useState(null);
    const videoRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);
    const recognitionRef = useRef(null);

    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

    useEffect(() => {
        if (propTotalQuestions) {
            setTotalQuestions(propTotalQuestions);
        }
    }, [propTotalQuestions]);

    useEffect(() => {
        // If we received an initialQuestion from parent, use it directly
        if (initialQuestion) {
            setCurrentQuestion(initialQuestion);
            if (initialQuestion.question_number) {
                setQuestionNumber(initialQuestion.question_number);
            }
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

    // Live timer linked to isRecording state
    useEffect(() => {
        let timer = null;
        if (isRecording) {
            timer = setInterval(() => {
                setRecordingDuration(prev => prev + 1);
            }, 1000);
        } else {
            if (timer) clearInterval(timer);
        }
        return () => {
            if (timer) clearInterval(timer);
        };
    }, [isRecording]);

    // Cleanup media tracks when component unmounts
    useEffect(() => {
        return () => {
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
            }
        };
    }, [mediaStream]);

    useEffect(() => {
        if (videoRef.current) {
            videoRef.current.srcObject = mediaStream;
        }
    }, [mediaStream]);

    const toggleRecording = async () => {
        if (isRecording) {
            // Stop MediaRecorder
            if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
                mediaRecorderRef.current.stop();
            }
            
            // Stop speech recognition
            if (recognitionRef.current) {
                recognitionRef.current.stop();
            }
            
            // Turn off camera and mic lights
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                setMediaStream(null);
            }
            
            setIsRecording(false);
        } else {
            // Start recording
            try {
                setError(null);
                setVideoBlob(null);
                setRecordingDuration(0);
                if (!answerStartTime) {
                    setAnswerStartTime(Date.now());
                }
                
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                setMediaStream(stream);
                
                // Initialize MediaRecorder
                chunksRef.current = [];
                let options = { mimeType: 'video/webm;codecs=vp9,opus' };
                if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                    options = { mimeType: 'video/webm;codecs=vp8,opus' };
                }
                if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                    options = { mimeType: 'video/webm' };
                }
                if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                    options = { mimeType: '' };
                }
                
                const mediaRecorder = new MediaRecorder(stream, options);
                mediaRecorderRef.current = mediaRecorder;
                
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data && event.data.size > 0) {
                        chunksRef.current.push(event.data);
                    }
                };
                
                mediaRecorder.onstop = () => {
                    const blob = new Blob(chunksRef.current, { type: 'video/webm' });
                    setVideoBlob(blob);
                    if (showToast) {
                        showToast('Video response captured! Ready to submit.', 'success');
                    }
                };
                
                mediaRecorder.start(1000);
                setIsRecording(true);

                if (recognitionRef.current) {
                    recognitionRef.current.start();
                }
            } catch (err) {
                let userFriendlyMsg = "Could not access camera/microphone. Please allow camera and microphone permissions in your browser settings.";
                if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                    userFriendlyMsg = "Camera and Microphone permissions were denied. Please enable them in your browser's address bar settings to record your video response.";
                } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
                    userFriendlyMsg = "No camera or microphone device was found. Please connect a webcam/microphone to continue.";
                }
                setError(userFriendlyMsg);
                if (showToast) {
                    showToast(userFriendlyMsg, 'error');
                }
                console.error("Media access error:", err);
            }
        }
    };

    const handleSkipQuestion = async () => {
        if (!currentQuestion || isSkipping || isAnswering) return;
        setIsSkipping(true);
        setError(null);

        // Stop any active recording first
        if (isRecording) {
            if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
                mediaRecorderRef.current.stop();
            }
            setIsRecording(false);
            if (recognitionRef.current) recognitionRef.current.stop();
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                setMediaStream(null);
            }
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
                setVideoBlob(null);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setIsSkipping(false);
        }
    };

    const handleAnswerSubmit = async () => {
        if (isAnswering || isSkipping) return;
        if (!videoBlob) {
            alert('Please record your answer video before submitting. Use the Start Video Response button.');
            return;
        }

        if (!currentQuestion) {
            setError('No question loaded. Please refresh the page.');
            return;
        }

        setIsAnswering(true);
        setError(null);

        try {
            const duration = recordingDuration || (answerStartTime ? Math.round((Date.now() - answerStartTime) / 1000) : 0);

            const formData = new FormData();
            formData.append('session_id', sessionId);
            formData.append('question_id', currentQuestion.question_id);
            formData.append('answer', answer.trim() || '[Video response recorded]');
            formData.append('duration_seconds', String(duration));
            
            if (videoBlob) {
                formData.append('video', videoBlob, `response_${sessionId}_${currentQuestion.question_id}.webm`);
            }

            const response = await fetch(`${API_BASE_URL}/submit-answer`, {
                method: 'POST',
                headers: { 
                    'Authorization': `Bearer ${token}`
                },
                body: formData,
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
                    answer: answer.trim() || '[Video Response]',
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
                setRecordingDuration(0);
                setVideoBlob(null);
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

                        <label className="answer-label">Your Response:</label>
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
                            <div className="video-preview-container animate-fade-in">
                                <div className="webcam-badge">
                                    <span className="dot"></span>
                                    <span>LIVE</span>
                                </div>
                                <video
                                    ref={videoRef}
                                    autoPlay
                                    muted
                                    playsInline
                                    style={{ width: '100%', maxHeight: '340px', objectFit: 'cover', display: 'block' }}
                                />
                            </div>
                        )}

                        {!isRecording && videoBlob && (
                            <div className="recording-status-box animate-fade-in">
                                <div className="status-icon">✓</div>
                                <div className="status-details">
                                    <p className="status-title">Video Response Captured</p>
                                    <p className="status-subtitle">Duration: {formatDuration(recordingDuration)} | Ready to submit</p>
                                </div>
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
                                disabled={isAnswering || isSkipping || isRecording || !videoBlob || !currentQuestion}
                            >
                                {isAnswering ? 'Uploading Response...' : 'Submit Answer'}
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