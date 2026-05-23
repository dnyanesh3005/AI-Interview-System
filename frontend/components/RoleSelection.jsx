import React, { useState } from 'react';
import './RoleSelection.css';

function RoleSelection({ onSelect, loading }) {
    const [selectedRole, setSelectedRole] = useState(null);
    const [questionCount, setQuestionCount] = useState(5);

    const roles = [
        {
            id: 'backend',
            name: 'Backend Engineer',
            description: 'Server-side development, APIs, databases, system design',
            icon: '⚙️',
            skills: ['Python', 'Java', 'APIs', 'Databases', 'System Design']
        },
        {
            id: 'aiml',
            name: 'AI/ML Engineer',
            description: 'Machine learning, data science, neural networks, AI models',
            icon: '🤖',
            skills: ['Python', 'TensorFlow', 'PyTorch', 'Data Science', 'ML']
        },
        {
            id: 'fullstack',
            name: 'Full Stack Engineer',
            description: 'Frontend and backend development, complete application building',
            icon: '🌐',
            skills: ['React', 'Node.js', 'Databases', 'APIs', 'DevOps']
        },
        {
            id: 'frontend',
            name: 'Frontend Developer',
            description: 'UI/UX development, component structure, state, and web performance',
            icon: '🎨',
            skills: ['HTML5/CSS3', 'JavaScript ES6+', 'React', 'Vite', 'Performance']
        },
        {
            id: 'datascience',
            name: 'Data Scientist',
            description: 'Data analysis, statistical modeling, insights generation',
            icon: '📊',
            skills: ['Python', 'SQL', 'Statistics', 'Pandas', 'Visualization']
        },
        {
            id: 'dataanalyst',
            name: 'Data Analyst',
            description: 'SQL queries, metrics dashboards, A/B tests, and business analysis',
            icon: '📈',
            skills: ['SQL', 'Excel/Sheets', 'Tableau/PowerBI', 'Pandas', 'KPIs']
        },
        {
            id: 'devops',
            name: 'DevOps Engineer',
            description: 'Infrastructure, deployment, CI/CD, cloud platforms',
            icon: '🚀',
            skills: ['Docker', 'Kubernetes', 'AWS/GCP', 'CI/CD', 'Terraform']
        }
    ];

    const handleRoleSelect = (roleName) => {
        setSelectedRole(roleName);
    };

    const handleStartInterview = () => {
        if (selectedRole && !loading) {
            onSelect(selectedRole, questionCount);
        }
    };

    return (
        <div className="role-selection-container">
            <div className="role-content">
                <h1>Select Your Target Role</h1>
                <p className="subtitle">Choose the position you're interviewing for</p>

                <div className="roles-grid">
                    {roles.map(role => (
                        <div
                            key={role.id}
                            className={`role-card ${selectedRole === role.name ? 'selected' : ''}`}
                            onClick={() => handleRoleSelect(role.name)}
                        >
                            <div className="role-icon">{role.icon}</div>
                            <h3>{role.name}</h3>
                            <p className="role-description">{role.description}</p>

                            <div className="role-skills">
                                {role.skills.map((skill, idx) => (
                                    <span key={idx} className="skill-tag">{skill}</span>
                                ))}
                            </div>

                            {selectedRole === role.name && (
                                <div className="selected-indicator">✓ Selected</div>
                            )}
                        </div>
                    ))}
                </div>

                <div className="question-count-section">
                    <h3>Number of Questions</h3>
                    <div className="count-options">
                        {[5, 10, 15].map(count => (
                            <button
                                key={count}
                                type="button"
                                className={`count-btn ${questionCount === count ? 'active' : ''}`}
                                onClick={() => setQuestionCount(count)}
                            >
                                {count} Questions
                            </button>
                        ))}
                    </div>
                </div>

                {selectedRole && (
                    <div className="role-info-box">
                        <p>You selected <strong>{selectedRole}</strong> with <strong>{questionCount} questions</strong></p>
                        <p className="text-muted">Customized questions will be generated based on this role and your resume</p>
                    </div>
                )}

                <button
                    className="continue-button"
                    disabled={!selectedRole || loading}
                    onClick={handleStartInterview}
                >
                    {loading ? 'Starting Interview...' : 'Start Interview'}
                </button>
            </div>
        </div>
    );
}

export default RoleSelection;