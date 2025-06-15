import React, { useState, createContext, useContext } from 'react';
import Head from 'next/head';
import Swal from 'sweetalert2'
import FileUpload from '@/components/FileUpload';
import ChatInterface from '@/components/ChatInterface';
import { useAppContext } from '@/context/AppContext';

export default function Home() {
  const {state, setState} = useAppContext();
  const handleFileUploadError = (err: string) => {
    Swal.fire({
      icon: 'error',
      title: 'Upload Error',
      text: err,
      confirmButtonText: 'OK'
    });
  }
  return (
    <div>
      <Head>
        <title>RAG-based Financial Q&A System</title>
        <meta name="description" content="AI-powered Q&A system for financial documents" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main>
        <h1 className="title">Welcome to the RAG-based Q&A System!</h1>
        <p className="subtitle">Upload a financial statement PDF and start asking questions.</p>
        {/* TODO: Implement your components here */}
        <FileUpload onUploadError={handleFileUploadError} />
        {
        /* 
          Suggested components to implement:
          - FileUpload component for PDF upload
          - ChatInterface component for Q&A
          - DocumentViewer component for document display
        */}
        {
          state.isUploaded && !state.isUploading ? <ChatInterface documentId={state.documentId} /> : null
        }
      </main>
    </div>
  );
} 