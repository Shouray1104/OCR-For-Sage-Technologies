import React from 'react';

const ProcessingStatus = ({ status, currentStep }) => {
  const steps = [
    { id: 1, label: 'Uploaded', description: 'File received' },
    { id: 2, label: 'OCR Scanning', description: 'AWS Textract processing' },
    { id: 3, label: 'Parsing', description: 'Extracting line items' },
    { id: 4, label: 'Ready', description: 'Done' },
  ];

  const getStepStatus = (stepId) => {
    if (currentStep > stepId) return 'completed';
    if (currentStep === stepId) return 'processing';
    return 'pending';
  };

  const progressPercent = Math.min((currentStep / steps.length) * 100, 100);

  if (status !== 'processing') return null;

  return (
    <div className="processing-status">
      {/* Progress Bar */}
      <div className="progress-bar-container">
        <div className="progress-bar" style={{ width: `${progressPercent}%` }}></div>
      </div>

      {/* Steps Container */}
      <div className="progress-container">
        {steps.map((step, index) => (
          <React.Fragment key={step.id}>
            <div className={`step ${getStepStatus(step.id)}`}>
              <div className="step-circle">
                {getStepStatus(step.id) === 'completed' ? (
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
                  </svg>
                ) : getStepStatus(step.id) === 'processing' ? (
                  <div className="spinner"></div>
                ) : (
                  <span>{step.id}</span>
                )}
              </div>
              <div className="step-info">
                <p className="step-label">{step.label}</p>
                <p className="step-description">{step.description}</p>
              </div>
            </div>
            {index < steps.length - 1 && <div className="step-connector"></div>}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default ProcessingStatus;
