import React, { useRef, useState } from 'react';
import './ResumeUpload.css';

function ResumeUpload({ onUpload, loading }) {
    const fileInputRef = useRef(null);
    const [dragActive, setDragActive] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];
            validateAndSetFile(file);
        }
    };

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            validateAndSetFile(e.target.files[0]);
        }
    };

    const validateAndSetFile = (file) => {
        const validTypes = ['.pdf', '.txt', '.docx'];
        const isValid = validTypes.some(type => file.name.endsWith(type));

        if (!isValid) {
            alert('Please upload a PDF, TXT, or DOCX file');
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            alert('File size must be less than 10MB');
            return;
        }

        setSelectedFile(file);
    };

    const handleUpload = () => {
        if (selectedFile) {
            onUpload(selectedFile);
        }
    };

    return (
        <div className="resume-upload-container">
            <div className="upload-content">
                <h1>AI-Powered Candidate Screening System</h1>
                <p className="subtitle">Upload your resume to get started with the technical interview</p>

                <div
                    className={`upload-area ${dragActive ? 'active' : ''}`}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                >
                    <div className="upload-icon">📄</div>
                    <h2>Drag and drop your resume</h2>
                    <p>or click to browse</p>
                    <p className="file-types">Supported formats: PDF, TXT, DOCX (Max 10MB)</p>

                    <input
                        ref={fileInputRef}
                        type="file"
                        onChange={handleFileChange}
                        accept=".pdf,.txt,.docx"
                        style={{ display: 'none' }}
                    />
                </div>

                {selectedFile && (
                    <div className="selected-file">
                        <p>✓ Selected: <strong>{selectedFile.name}</strong></p>
                        <p className="file-size">Size: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                )}

                <button
                    className="upload-button"
                    onClick={handleUpload}
                    disabled={!selectedFile || loading}
                >
                    {loading ? 'Processing...' : 'Upload Resume'}
                </button>

                <div className="info-section">
                    <h3>What happens next?</h3>
                    <ul>
                        <li>Your resume will be analyzed to extract key skills and experience</li>
                        <li>You'll select a target role for the interview</li>
                        <li>Dynamic questions will be generated based on your background and the role</li>
                        <li>You'll answer 5-10 interview questions in real-time</li>
                        <li>A comprehensive summary will be generated at the end</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}

export default ResumeUpload;