import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';

const UploadZone = ({ onUpload, isProcessing }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setSelectedFile(file);
    }
  }, []);

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
    },
    disabled: isProcessing,
    multiple: false,
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false),
  });

  const handleExtractClick = () => {
    if (selectedFile && onUpload) {
      onUpload(selectedFile);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className={`upload-zone ${isDragActive ? 'active' : ''} ${isProcessing ? 'disabled' : ''}`} {...getRootProps()}>
      <input {...getInputProps()} />

      {!selectedFile ? (
        <div className="upload-content">
          <svg className="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"
            />
          </svg>
          <h2>Upload Invoice Document</h2>
          {isDragActive ? (
            <p className="drag-active">Drop the file here...</p>
          ) : (
            <>
              <p>Drag and drop your invoice here, or click to select</p>
              <p className="hint">Supported formats: PDF, PNG, JPG (Max 10MB)</p>
            </>
          )}
        </div>
      ) : (
        <div className="file-selected-content">
          <svg className="file-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8zm-1 15H7v-2h6v2zm3-4H7v-2h9v2z" />
          </svg>
          <div className="file-info">
            <h3>{selectedFile.name}</h3>
            <p className="file-size">{formatFileSize(selectedFile.size)}</p>
          </div>
          <div className="file-actions">
            <button
              className="btn-extract"
              onClick={handleExtractClick}
              disabled={isProcessing}
              type="button"
            >
              {isProcessing ? (
                <>
                  <span className="spinner-small"></span>
                  Uploading...
                </>
              ) : (
                'Extract Data'
              )}
            </button>
            <button
              className="btn-clear"
              onClick={(e) => {
                e.stopPropagation();
                handleClear();
              }}
              disabled={isProcessing}
              type="button"
            >
              Clear
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadZone;
