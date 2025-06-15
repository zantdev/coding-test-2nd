import React, { useState, useRef, useEffect } from 'react';
import { useAppContext } from '@/context/AppContext';
import axios from 'axios';

interface FileUploadProps {
  onUploadComplete?: (result: any) => void;
  onUploadError?: (error: string) => void;
}

export default function FileUpload({ onUploadComplete, onUploadError }: FileUploadProps) {
  const {state, setState} = useAppContext();
  const fileInputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (state.file) {
      handleUpload();
    }
  }, [state.file]);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    // 1. Validate file type (PDF only)
    // 2. Validate file size (e.g., max 10MB)
    // 3. Set selected file
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    if (selectedFile.type !== 'application/pdf') {
      onUploadError?.('Only PDF files are allowed.');
      return;
    }
    if (selectedFile.size > 10 * 1024 * 1024) {
      onUploadError?.('File size must be less than 10MB.');
      return;
    }
    setState({...state, file: selectedFile, isUploaded: true});
    
  };

  const handleUpload = async () => {
    if (!state.file) return;
    setState({ ...state, isUploading: true, uploadProgress: 0 });

    const formData = new FormData();
    formData.append('file', state.file);

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
      const response = await axios.post(`${backendUrl}/api/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setState(s => ({ ...s, uploadProgress: percent }));
          }
        },
      });

      if (response.status === 200) {
        const result = response.data;
        setState({
          ...state,
          isUploading: false,
          uploadProgress: 100,
          isUploaded: true,
          documentId: result.document_id,
        });
        onUploadComplete?.(result);
      } else {
        setState({ ...state, isUploading: false });
        onUploadError?.('Upload failed.');
      }
    } catch (error: any) {
      setState({ ...state, isUploading: false });
      onUploadError?.(error.message || 'Unknown error');
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    // Prevent default to allow drop
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    // Prevent default and handle file drop
    e.preventDefault();
    e.stopPropagation();
    const droppedFile = e.dataTransfer.files?.[0];
    if (!droppedFile) return;

    if (droppedFile.type !== 'application/pdf') {
      onUploadError?.('Only PDF files are allowed.');
      return;
    }
    if (droppedFile.size > 10 * 1024 * 1024) {
      onUploadError?.('File size must be less than 10MB.');
      return;
    }
    setState({...state, file: droppedFile, isUploaded: true});
    handleUpload();
  };

  return (
    <div className="file-upload">
      {/* Drag & Drop area */}
      <div 
        className="upload-area"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        {/* Drag & drop UI */}
        {state.file ? (
          <span>{state.file.name}</span>
        ) : (
          <span>Drag & drop a PDF file here, or click to select</span>
        )}
      </div>

      {/* File input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />

      {/* Progress bar */}
      {state.isUploading && (
        <div className="progress-bar" >
          <div
            style={{
              width: `${state.uploadProgress}%`,
              height: '100%',
              background: '#0070f3',
              borderRadius: '4px',
              transition: 'width 0.2s'
            }}
          />
        </div>
      )}
    </div>
  );
}