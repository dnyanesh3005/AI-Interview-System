import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';

// Scroll-triggered Animation Wrapper
function FadeIn({ children, delay = 0 }) {
    const [isVisible, setIsVisible] = useState(false);
    const domRef = useRef();

    useEffect(() => {
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setIsVisible(true);
                    observer.unobserve(domRef.current);
                }
            });
        }, { threshold: 0.1 });

        const currentRef = domRef.current;
        if (currentRef) {
            observer.observe(currentRef);
        }

        return () => {
            if (currentRef) {
                observer.unobserve(currentRef);
            }
        };
    }, []);

    return (
        <div
            className={`fade-in-section ${isVisible ? 'is-visible' : ''}`}
            style={{ transitionDelay: `${delay}ms` }}
            ref={domRef}
        >
            {children}
        </div>
    );
}

// Live Interactive AI Interview Simulator
function InteractiveMockup() {
    const [phase, setPhase] = useState(0); // 0: scanning, 1: speaking, 2: coding, 3: report
    const [transcriptionText, setTranscriptionText] = useState('');
    const [codeLines, setCodeLines] = useState([]);

    // Cycle through phases
    useEffect(() => {
        const intervals = [
            5000,  // Phase 0: Scanning (5s)
            8000,  // Phase 1: Speaking/Speech transcription (8s)
            8000,  // Phase 2: Coding demonstration (8s)
            6000   // Phase 3: AI report feedback (6s)
        ];

        let timer;
        const runPhase = (currentPhase) => {
            setPhase(currentPhase);
            timer = setTimeout(() => {
                runPhase((currentPhase + 1) % 4);
            }, intervals[currentPhase]);
        };

        runPhase(0);
        return () => clearTimeout(timer);
    }, []);

    // Handle text generation for speech and coding
    useEffect(() => {
        if (phase === 0) {
            setTranscriptionText('');
            setCodeLines([]);
        } else if (phase === 1) {
            const fullText = "To optimize the lookup time from O(N) to O(1), I will use a Hash Map. This will allow us to store elements as keys and check for existence in constant time, which scales efficiently for large datasets...";
            let currentText = '';
            let charIndex = 0;
            const textInterval = setInterval(() => {
                if (charIndex < fullText.length) {
                    currentText += fullText[charIndex];
                    setTranscriptionText(currentText);
                    charIndex += 2; // type 2 characters at once for smooth speed
                } else {
                    clearInterval(textInterval);
                }
            }, 30);
            return () => clearInterval(textInterval);
        } else if (phase === 2) {
            const lines = [
                "function findTwoSum(nums, target) {",
                "  const map = new Map();",
                "  for (let i = 0; i < nums.length; i++) {",
                "    const complement = target - nums[i];",
                "    if (map.has(complement)) {",
                "      return [map.get(complement), i];",
                "    }",
                "    map.set(nums[i], i);",
                "  }",
                "  return [];",
                "}"
            ];
            let current = [];
            let lineIndex = 0;
            const codeInterval = setInterval(() => {
                if (lineIndex < lines.length) {
                    current.push(lines[lineIndex]);
                    setCodeLines([...current]);
                    lineIndex++;
                } else {
                    clearInterval(codeInterval);
                }
            }, 500);
            return () => clearInterval(codeInterval);
        }
    }, [phase]);

    return (
        <div className="system-mockup">
            {/* MacOS-style Window Chrome */}
            <div className="mockup-header">
                <div className="window-dots">
                    <span className="dot red"></span>
                    <span className="dot yellow"></span>
                    <span className="dot green"></span>
                </div>
                <div className="window-address">
                    <span className="address-icon">🔒</span>
                    ai-interview-system.com/session/live-mock
                </div>
                <div className="session-badge">
                    <span className={`status-dot ${phase === 0 ? 'pulse-blue' : phase === 1 ? 'pulse-red' : phase === 2 ? 'pulse-cyan' : 'pulse-green'}`}></span>
                    {phase === 0 ? 'SYSTEM INITIALIZING' : phase === 1 ? 'CANDIDATE RESPONDING' : phase === 2 ? 'CODING TEST ACTIVE' : 'EVALUATION COMPLETE'}
                </div>
            </div>

            {/* Main Mockup Workspace */}
            <div className="mockup-body">
                {/* Left Side: Video Feed & Speech Wave */}
                <div className="mockup-left">
                    <div className="webcam-box">
                        {/* Scanning Overlay (Phase 0 & 1) */}
                        {phase <= 1 && (
                            <div className="scanner-line"></div>
                        )}

                        {/* Facial detection reticle */}
                        {phase === 0 && (
                            <div className="face-reticle-box">
                                <div className="corner top-left"></div>
                                <div className="corner top-right"></div>
                                <div className="corner bottom-left"></div>
                                <div className="corner bottom-right"></div>
                                <span className="face-scan-text">SCANNING FACIAL MARKERS...</span>
                            </div>
                        )}

                        {/* Live Avatar Vector Drawing */}
                        <div className="avatar-graphic">
                            <svg viewBox="0 0 100 100" className="avatar-svg">
                                <circle cx="50" cy="35" r="20" className="avatar-head" />
                                <path d="M20 85 C20 60, 80 60, 80 85" className="avatar-shoulders" />
                                {/* Face Scan Nodes */}
                                {phase === 0 && (
                                    <>
                                        <circle cx="50" cy="35" r="1.5" className="node active" />
                                        <circle cx="43" cy="30" r="1" className="node" />
                                        <circle cx="57" cy="30" r="1" className="node" />
                                        <circle cx="45" cy="42" r="1" className="node" />
                                        <circle cx="55" cy="42" r="1" className="node" />
                                        <circle cx="50" cy="48" r="1" className="node" />
                                        <line x1="43" y1="30" x2="50" y2="35" className="node-line" />
                                        <line x1="57" y1="30" x2="50" y2="35" className="node-line" />
                                        <line x1="43" y1="30" x2="45" y2="42" className="node-line" />
                                        <line x1="57" y1="30" x2="55" y2="42" className="node-line" />
                                        <line x1="45" y1="42" x2="50" y2="48" className="node-line" />
                                        <line x1="55" y1="42" x2="50" y2="48" className="node-line" />
                                    </>
                                )}
                            </svg>
                        </div>

                        {/* Webcam HUD Stats */}
                        <div className="webcam-hud">
                            <span className="hud-metric">FPS: 60</span>
                            <span className="hud-metric">
                                {phase === 0 && "EYE TRACKING: CALIBRATING"}
                                {phase === 1 && "EYE TRACKING: STABLE (98%)"}
                                {phase === 2 && "FOCUS LOCK: HIGH"}
                                {phase === 3 && "REPORT GENERATED"}
                            </span>
                        </div>

                        {/* Rec blinking indicator */}
                        <div className="rec-indicator">
                            <span className="rec-dot"></span>
                            REC 00:02:{phase === 0 ? '12' : phase === 1 ? '18' : phase === 2 ? '25' : '30'}
                        </div>
                    </div>

                    {/* Speech Wave / Transcriber Area */}
                    <div className="transcription-panel">
                        <div className="audio-wave-container">
                            <span className="wave-label">Mic Input</span>
                            <div className="audio-wave">
                                <span className={`wave-bar bar-1 ${phase === 1 ? 'speaking' : ''}`}></span>
                                <span className={`wave-bar bar-2 ${phase === 1 ? 'speaking' : ''}`}></span>
                                <span className={`wave-bar bar-3 ${phase === 1 ? 'speaking' : ''}`}></span>
                                <span className={`wave-bar bar-4 ${phase === 1 ? 'speaking' : ''}`}></span>
                                <span className={`wave-bar bar-5 ${phase === 1 ? 'speaking' : ''}`}></span>
                                <span className={`wave-bar bar-6 ${phase === 1 ? 'speaking' : ''}`}></span>
                                <span className={`wave-bar bar-7 ${phase === 1 ? 'speaking' : ''}`}></span>
                            </div>
                        </div>
                        <div className="transcription-box">
                            {phase === 0 && <p className="placeholder-text">Awaiting microphone signal...</p>}
                            {phase === 1 && (
                                <p className="speech-text">
                                    {transcriptionText}
                                    <span className="caret"></span>
                                </p>
                            )}
                            {phase >= 2 && (
                                <p className="speech-text done">
                                    To optimize the lookup time from O(N) to O(1), I will use a Hash Map. This will allow us to store elements as keys and check for existence in constant time, which scales efficiently for large datasets...
                                </p>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Side: Coding Screen OR AI Feedback Panel */}
                <div className="mockup-right">
                    {/* Render Code Editor on Phase 2 */}
                    {phase === 2 && (
                        <div className="editor-panel">
                            <div className="editor-tab-bar">
                                <span className="tab-item active">solution.js</span>
                                <span className="tab-item">scratchpad.md</span>
                            </div>
                            <div className="code-editor-mock">
                                <div className="line-numbers">
                                    {Array.from({ length: 12 }, (_, i) => (
                                        <div key={i} className="line-no">{i + 1}</div>
                                    ))}
                                </div>
                                <pre className="code-content">
                                    {codeLines.map((line, idx) => (
                                        <div key={idx} className="code-line">
                                            {line}
                                            {idx === codeLines.length - 1 && <span className="editor-caret"></span>}
                                        </div>
                                    ))}
                                    {codeLines.length === 0 && <span className="editor-caret"></span>}
                                </pre>
                            </div>
                        </div>
                    )}

                    {/* Render AI Feedback Report on Phase 3 */}
                    {phase === 3 && (
                        <div className="ai-report-panel animate-fade-in">
                            <h4>Real-time AI Feedback</h4>
                            <div className="metrics-summary">
                                <div className="metric-row">
                                    <div className="metric-info">
                                        <span>Technical Accuracy</span>
                                        <span className="metric-val text-cyan">94%</span>
                                    </div>
                                    <div className="progress-track">
                                        <div className="progress-bar bg-cyan" style={{ width: '94%' }}></div>
                                    </div>
                                </div>
                                <div className="metric-row">
                                    <div className="metric-info">
                                        <span>STAR Structuring</span>
                                        <span className="metric-val text-violet">90%</span>
                                    </div>
                                    <div className="progress-track">
                                        <div className="progress-bar bg-violet" style={{ width: '90%' }}></div>
                                    </div>
                                </div>
                                <div className="metric-row">
                                    <div className="metric-info">
                                        <span>Communication Clarity</span>
                                        <span className="metric-val text-pink">88%</span>
                                    </div>
                                    <div className="progress-track">
                                        <div className="progress-bar bg-pink" style={{ width: '88%' }}></div>
                                    </div>
                                </div>
                            </div>

                            <div className="detected-signals">
                                <h5>Identified Core Concepts</h5>
                                <div className="signal-tags">
                                    <span className="tag glow-cyan">Hash Map</span>
                                    <span className="tag glow-violet">O(1) Search</span>
                                    <span className="tag glow-pink">STAR Method</span>
                                    <span className="tag glow-cyan">Optimal Space</span>
                                </div>
                            </div>

                            <div className="actionable-tips">
                                <h5>AI Coaching Tip</h5>
                                <p>Excellent job addressing time complexity constraints immediately. Next response, try to outline edge cases (e.g. empty input arrays) before starting the implementation.</p>
                            </div>
                        </div>
                    )}

                    {/* Default Dashboard placeholder during Phase 0 & 1 */}
                    {(phase === 0 || phase === 1) && (
                        <div className="dashboard-hud-placeholder">
                            <div className="hud-logo">
                                <span className="logo-sparkle">✨</span>
                                <span>AI SCREENING MODULE</span>
                            </div>
                            <div className="hud-status-grid">
                                <div className="hud-status-card">
                                    <span className="hud-label">VOICE ANALYSIS</span>
                                    <span className="hud-val pulse-text-blue">{phase === 0 ? 'STANDBY' : 'ANALYZING SPEECH'}</span>
                                </div>
                                <div className="hud-status-card">
                                    <span className="hud-label">SENTIMENT SCORE</span>
                                    <span className="hud-val">{phase === 0 ? '--' : 'CONFIDENT (96%)'}</span>
                                </div>
                                <div className="hud-status-card">
                                    <span className="hud-label">PACE ESTIMATOR</span>
                                    <span className="hud-val">{phase === 0 ? '--' : '135 WPM (OPTIMAL)'}</span>
                                </div>
                                <div className="hud-status-card">
                                    <span className="hud-label">COGNITIVE LOAD</span>
                                    <span className="hud-val">{phase === 0 ? '--' : 'BALANCED'}</span>
                                </div>
                            </div>
                            <div className="hud-graphic-container">
                                <div className="grid-radar">
                                    <div className="radar-sweep"></div>
                                    <div className="radar-circle circle-1"></div>
                                    <div className="radar-circle circle-2"></div>
                                    <div className="radar-circle circle-3"></div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function LandingPage() {
    const navigate = useNavigate();

    return (
        <div className="landing-page">
            {/* Drifting Ambient Background Glow Orbs */}
            <div className="ambient-orbs">
                <div className="orb orb-1"></div>
                <div className="orb orb-2"></div>
                <div className="orb orb-3"></div>
            </div>

            {/* Header / Navbar */}
            <header className="landing-header-nav">
                <div className="nav-left">
                    <div className="logo" onClick={() => navigate('/')}>
                        <div className="logo-icon-wrapper">
                            <span className="logo-icon">🤖</span>
                            <span className="logo-glow"></span>
                        </div>
                        <span className="logo-text">AI Interview System</span>
                    </div>
                </div>
                <nav className="nav-center">
                    <a href="#hero" className="nav-link">Home</a>
                    <a href="#how-it-works" className="nav-link">How It Works</a>
                    <a href="#features" className="nav-link">Key Features</a>
                </nav>
                <div className="nav-right">
                    <button className="nav-btn outline-btn" onClick={() => navigate('/login')}>Log In</button>
                    <button className="nav-btn filled-btn" onClick={() => navigate('/signup')}>Sign Up</button>
                </div>
            </header>

            {/* Hero Section */}
            <section id="hero" className="hero-section">
                <div className="hero-content">
                    <div className="announcement-tag animate-fade-in-down">
                        <span className="tag-sparkle">✨</span>
                        <span className="tag-text">Next-Generation AI Interviewer </span>
                    </div>
                    <h1 className="animate-fade-in">Prepare Smarter. Interview Better.</h1>
                    <p className="hero-subtitle animate-fade-in-up">
                        Practice personalized AI-driven interviews based on your resume and target role, receive instant performance analysis, and build confidence for your dream career.
                    </p>
                    <div className="hero-cta-group animate-fade-in-up">
                        <button className="get-started-btn" onClick={() => navigate('/signup')}>
                            Get Started Free
                            <span className="arrow-icon">→</span>
                        </button>
                        <a href="#how-it-works" className="watch-demo-link">
                            <span className="play-icon">▶</span> How it works
                        </a>
                    </div>


                </div>

                {/* Hero Dashboard Simulator Mockup */}
                <div className="hero-image-container animate-fade-in">
                    <InteractiveMockup />
                </div>
            </section>

            {/* How It Works Section */}
            <section id="how-it-works" className="how-works-section">
                <div className="section-container">
                    <FadeIn>
                        <h2>How the Platform Works</h2>
                        <p className="section-subtitle">A seamless three-step pipeline designed to simulate a professional technical screening.</p>
                    </FadeIn>
                    <div className="works-grid">
                        <FadeIn delay={100}>
                            <div className="works-card">
                                <div className="card-icon-container">
                                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon-svg">
                                        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                                        <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
                                        <line x1="12" y1="19" x2="12" y2="22" />
                                    </svg>
                                </div>
                                <h3>1. Parse Resume & Choose Role</h3>
                                <p>Upload your resume to extract key engineering competencies and select a target career path tailored to your goals.</p>
                            </div>
                        </FadeIn>

                        <FadeIn delay={200}>
                            <div className="works-card">
                                <div className="card-icon-container">
                                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon-svg">
                                        <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
                                        <line x1="8" y1="21" x2="16" y2="21" />
                                        <line x1="12" y1="17" x2="12" y2="21" />
                                    </svg>
                                </div>
                                <h3>2. Live Assessment Simulation</h3>
                                <p>Face dynamic, generative coding challenges and behavioral questions. Answer through voice-to-text transcription or code compiler inputs.</p>
                            </div>
                        </FadeIn>

                        <FadeIn delay={300}>
                            <div className="works-card">
                                <div className="card-icon-container">
                                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon-svg">
                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                        <polyline points="14 2 14 8 20 8" />
                                        <line x1="16" y1="13" x2="8" y2="13" />
                                        <line x1="16" y1="17" x2="8" y2="17" />
                                        <polyline points="10 9 9 9 8 9" />
                                    </svg>
                                </div>
                                <h3>3. Instant Diagnostic Feedback</h3>
                                <p>Get a comprehensive scorecard evaluating your technical performance, communications pace, and structured delivery improvements.</p>
                            </div>
                        </FadeIn>
                    </div>
                </div>
            </section>

            {/* Key Features Section */}
            <section id="features" className="features-section">
                <div className="section-container">
                    <FadeIn>
                        <h2>Key Platform Features</h2>
                    </FadeIn>
                    <div className="features-grid">
                        <FadeIn delay={100}>
                            <div className="feature-column">
                                <div className="feature-header">
                                    <span className="feature-icon">📹</span>
                                    <h3>Speech & Video Analysis</h3>
                                </div>
                                <p>Analyze presentation pace, confidence level, eye contact metrics, and filler word frequency to polish your delivery delivery.</p>
                            </div>
                        </FadeIn>

                        <FadeIn delay={200}>
                            <div className="feature-column">
                                <div className="feature-header">
                                    <span className="feature-icon">💻</span>
                                    <h3>Interactive Coding Sandbox</h3>
                                </div>
                                <p>Type code solution in an interactive IDE. Get feedback on algorithmic complexity, optimal space complexity, and critical edge cases.</p>
                            </div>
                        </FadeIn>

                        <FadeIn delay={300}>
                            <div className="feature-column">
                                <div className="feature-header">
                                    <span className="feature-icon">📊</span>
                                    <h3>Personalized Performance Hub</h3>
                                </div>
                                <p>Track history of past sessions, analyze career growth metrics over time, and compare scores across multiple target roles.</p>
                            </div>
                        </FadeIn>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default LandingPage;
