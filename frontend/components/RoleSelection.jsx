import React, { useState } from 'react';
import './RoleSelection.css';

function RoleSelection({ onSelect, loading }) {
    const [selectedRole, setSelectedRole] = useState(null);

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
            id: 'datascience',
            name: 'Data Scientist',
            description: 'Data analysis, statistical modeling, insights generation',
            icon: '📊',
            skills: ['Python', 'SQL', 'Statistics', 'Pandas', 'Visualization']
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
        onSelect(roleName);
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

                {selectedRole && (
                    <div className="role-info-box">
                        <p>You selected <strong>{selectedRole}</strong></p>
                        <p className="text-muted">Customized questions will be generated based on this role and your resume</p>
                    </div>
                )}

                <button
                    className="continue-button"
                    disabled={!selectedRole || loading}
                    onClick={() => selectedRole && handleRoleSelect(selectedRole)}
                >
                    {loading ? 'Starting Interview...' : 'Start Interview'}
                </button>
            </div>
        </div>
    );
}

export default RoleSelection;