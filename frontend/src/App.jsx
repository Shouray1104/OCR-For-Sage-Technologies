import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import UploadZone from './components/UploadZone';
import ProcessingStatus from './components/ProcessingStatus';
import ExtractedTable from './components/ExtractedTable';
import './App.css';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'https://ocr-for-sage-technologies.onrender.com';

function App() {
  // State management
  const [state, setState] = useState('upload'); // 'upload', 'processing', 'results'
  const [jobId, setJobId] = useState(null);
  const [error, setError] = useState(null);
  const [extractedData, setExtractedData] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [processingStep, setProcessingStep] = useState(0);
  const [filename, setFilename] = useState(null);

  // Polling interval reference
  const pollingIntervalRef = useRef(null);
  const pollAttempsRef = useRef(0);
  const maxPollAttemptsRef = useRef(60); // Max 60 attempts = 2 minutes with 2-second interval

  /**
   * Handle file upload
   */
  const handleUpload = async (file) => {
    setError(null);
    setIsUploading(true);
    setProcessingStep(1);

    try {
      // Create FormData with file
      const formData = new FormData();
      formData.append('file', file);

      console.log('Uploading file:', file.name);

      // Send to backend
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const { job_id } = response.data;
      
      console.log('Upload successful, job_id:', job_id);

      setJobId(job_id);
      setFilename(file.name);
      setIsUploading(false);

      // Transition to processing state
      setState('processing');
      setProcessingStep(2);

      // Start polling for results
      startPolling(job_id);
    } catch (err) {
      console.error('Upload error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Upload failed';
      setError(errorMessage);
      setIsUploading(false);
      setState('upload');
    }
  };

  /**
   * Start polling for results
   */
  const startPolling = (id) => {
    console.log('Starting polling for job_id:', id);
    
    pollAttempsRef.current = 0;
    setProcessingStep(2);

    // Poll every 2 seconds
    pollingIntervalRef.current = setInterval(() => {
      pollForResults(id);
    }, 2000);
  };

  /**
   * Poll for results
   */
  const pollForResults = async (id) => {
    pollAttempsRef.current += 1;

    if (pollAttempsRef.current > maxPollAttemptsRef.current) {
      // Stop polling - timeout
      stopPolling();
      setError('Processing timeout. Please try again.');
      setState('upload');
      console.error('Polling timeout');
      return;
    }

    try {
      const response = await axios.get(`${API_BASE_URL}/results/${id}`);
      const { status, items, total_amount, item_count } = response.data;

      console.log(`Poll attempt ${pollAttempsRef.current}: status=${status}`);

      if (status === 'success' && items && items.length > 0) {
        // Results are ready
        console.log('Results received:', items.length, 'items');
        
        setProcessingStep(4);
        setExtractedData({
          items,
          total_amount,
          item_count,
        });

        stopPolling();
        setState('results');
      } else if (status === 'processing') {
        // Still processing
        setProcessingStep(3);
      }
    } catch (err) {
      if (err.response?.status === 404) {
        // Job not found yet, continue polling
        console.log('Results not ready yet, continuing to poll...');
      } else {
        console.error('Polling error:', err);
        // Continue polling on error
      }
    }
  };

  /**
   * Stop polling
   */
  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
      console.log('Polling stopped');
    }
  };

  /**
   * Reset to upload state
   */
  const handleReset = () => {
    console.log('Resetting application');
    
    stopPolling();
    setState('upload');
    setJobId(null);
    setError(null);
    setExtractedData(null);
    setIsUploading(false);
    setProcessingStep(0);
    setFilename(null);
    pollAttempsRef.current = 0;
  };

  /**
   * Dismiss error
   */
  const handleDismissError = () => {
    setError(null);
  };

  // Cleanup polling on component unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, []);

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1>ERP OCR Portal</h1>
          <p>Intelligent Invoice Processing & Data Extraction</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="app-main">
        <div className="content-wrapper">
          {/* Error Banner */}
          {error && (
            <div className="error-banner">
              <div className="error-content">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" />
                </svg>
                <div>
                  <h3>Error</h3>
                  <p>{error}</p>
                </div>
              </div>
              <button onClick={handleDismissError} className="dismiss-error">
                ✕
              </button>
            </div>
          )}

          {/* Upload State */}
          {state === 'upload' && (
            <div className="upload-section">
              <UploadZone onUpload={handleUpload} isProcessing={isUploading} />
            </div>
          )}

          {/* Processing State */}
          {state === 'processing' && (
            <div className="processing-section">
              <ProcessingStatus status="processing" currentStep={processingStep} />
              <div className="processing-info">
                <p>Processing file: <strong>{filename}</strong></p>
                <p>Job ID: <code>{jobId}</code></p>
              </div>
            </div>
          )}

          {/* Results State */}
          {state === 'results' && extractedData && (
            <div className="success-section">
              <div className="success-banner">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
                </svg>
                <h2>Processing Complete!</h2>
                <p>Successfully extracted {extractedData.item_count} line items</p>
              </div>
              <ExtractedTable data={extractedData} loading={false} />
              <div className="action-buttons">
                <button onClick={handleReset} className="btn-primary">
                  Upload Another Invoice
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>&copy; 2026 ERP OCR Portal. Design and Developed by Shouray Soni.</p>
      </footer>
    </div>
  );
}

export default App;
