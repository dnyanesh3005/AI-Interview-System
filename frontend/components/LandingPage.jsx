import React from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';
import heroImage from '../src/assets/hero_interview.png';

function LandingPage() {
    const navigate = useNavigate();

    return (
        <div className="landing-page">
            {/* Header / Navbar */}
            <header className="landing-header-nav">
                <div className="nav-left">
                    <div className="logo">
                        <span className="logo-icon">🤖</span>
                        <span className="logo-text">AI Interview System</span>
                    </div>
                </div>
                <nav className="nav-center">
                    <a href="#hero" className="nav-link">Home</a>
                    <a href="#features" className="nav-link">About Us</a>
                    <a href="#how-it-works" className="nav-link">How It Works</a>
                    <a href="#features" className="nav-link">Pricing</a>
                </nav>
                <div className="nav-right">
                    <button className="nav-btn outline-btn" onClick={() => navigate('/login')}>Log In</button>
                    <button className="nav-btn filled-btn" onClick={() => navigate('/signup')}>Sign Up</button>
                </div>
            </header>

            {/* Hero Section */}
            <section id="hero" className="hero-section">
                <div className="hero-content">
                    <h1>Unlock Your Potential. Excel in Every Interview.</h1>
                    <p className="hero-subtitle">
                        Practice mock interviews, receive instant AI feedback, and land your dream internship or job.
                    </p>
                    <button className="get-started-btn" onClick={() => navigate('/signup')}>
                        Get Started
                    </button>
                </div>
                <div className="hero-image-container">
                    <img src={heroImage} alt="Mock Interview Collaboration" className="hero-image" />
                </div>
            </section>

            {/* How It Works Section */}
            <section id="how-it-works" className="how-works-section">
                <div className="section-container">
                    <h2>How AI Interview System Works</h2>
                    <div className="works-grid">
                        <div className="works-card">
                            <div className="card-icon-container">
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon-svg">
                                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                                    <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
                                    <line x1="12" y1="19" x2="12" y2="22" />
                                </svg>
                            </div>
                            <h3>1. Record Interview</h3>
                            <p>Record your answers to personalized technical and behavioral questions using audio and video.</p>
                        </div>
                        <div className="works-card">
                            <div className="card-icon-container">
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon-svg">
                                    <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.44 2.5 2.5 0 0 1 0-3.12 3 3 0 0 1 0-3.88 2.5 2.5 0 0 1 0-3.12 2.5 2.5 0 0 1 2.46-4.94ZM14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.44 2.5 2.5 0 0 0 0-3.12 3 3 0 0 0 0-3.88 2.5 2.5 0 0 0 0-3.12 2.5 2.5 0 0 0-2.46-4.94Z" />
                                </svg>
                            </div>
                            <h3>2. AI Assessment</h3>
                            <p>Our advanced models evaluate your responses for technical accuracy, structure, and communication.</p>
                        </div>
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
                            <h3>3. Feedback Report</h3>
                            <p>Receive a detailed evaluation report with performance metrics, model answers, and areas of improvement.</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Key Features Section */}
            <section id="features" className="features-section">
                <div className="section-container">
                    <h2>Key Features</h2>
                    <div className="features-grid">
                        <div className="feature-column">
                            <h3>Video Interviews</h3>
                            <p>Conduct realistic mock sessions with video recordings and automated transcription feedback.</p>
                        </div>
                        <div className="feature-column">
                            <h3>Coding Challenges</h3>
                            <p>Role-specific technical questions designed to test your core engineering and logic capabilities.</p>
                        </div>
                        <div className="feature-column">
                            <h3>Communication Analysis</h3>
                            <p>Understand your speech clarity, grammar, confidence levels, and structure of delivery.</p>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default LandingPage;
