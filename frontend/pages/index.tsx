import React, { useState, createContext, useContext } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Swal from 'sweetalert2'
import FileUpload from '@/components/FileUpload';
import ChatInterface from '@/components/ChatInterface';
import { useAppContext } from '@/context/AppContext';

export default function Home() {
  const {state, setState} = useAppContext();
  const router = useRouter();

  const handleFileUploadError = (err: string) => {
    Swal.fire({
      icon: 'error',
      title: 'Upload Error',
      text: err,
      confirmButtonText: 'OK'
    });
  }

  const goToHistory = () => {
    setState({...state, isUploaded: false, documentId: '', documentName: '', file: null});
    router.push('/history')
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
        <p className="subtitle">Upload a document PDF and start asking questions.</p>
        <FileUpload onUploadError={handleFileUploadError} />
        {
          state.isUploaded && !state.isUploading ? <ChatInterface documentId={state.documentId} /> : null
        }
        {/* this is only shown if user does not upload yet */}
        {
          !state.isUploaded && !state.isUploading ? <><p className="subtitle">Or</p>
         <button className="btn-history" onClick={() => goToHistory()}>
          View document history
         </button></> : null
        }
      </main>
    </div>
  );
} 