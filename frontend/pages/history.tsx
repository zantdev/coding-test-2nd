import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Swal from 'sweetalert2';
import { useAppContext } from '@/context/AppContext';

interface DocumentInfo {
  document_id: string;
  filename: string;
  chunks_count: number;
  upload_date?: string | null;
}

export default function History() {
  const { state, setState } = useAppContext();
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
        const res = await fetch(`${backendUrl}/api/documents`);
        const data = await res.json();
        setDocuments(data.documents || []);
      } catch (err) {
        setDocuments([]);
      } finally {
        setLoading(false);
      }
    };
    fetchDocuments();
  }, []);

  const handleView = (docId: string) => {
    // Navigate to detail page or open modal (implement as needed)
    window.location.href = `/document/${docId}`;
  };

  const handleDelete = async (docId: string) => {
    const result = await Swal.fire({
      title: 'Are you sure?',
      text: 'Do you want to delete this document?',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      cancelButtonColor: '#3085d6',
      confirmButtonText: 'Yes, delete it!',
      cancelButtonText: 'Cancel'
    });
    if (!result.isConfirmed) return;
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
      await fetch(`${backendUrl}/api/documents/${docId}`, { method: 'DELETE' });
      setDocuments(docs => docs.filter(doc => doc.document_id !== docId));
      Swal.fire('Deleted!', 'The document has been deleted.', 'success');
    } catch (err) {
      Swal.fire('Error', 'Failed to delete document.', 'error');
    }
  };

  const getBack = () => {
    // Reset state and navigate back to home
    setState({
      ...state,
      isUploaded: false,
      documentId: '',
      documentName: '',
      file: null
    });
    router.back();
  }

  return (
    <div>
      <Head>
        <title>History - RAG-based Financial Q&A System</title>
        <meta name="description" content="History" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main>
        <h1 className="title">Document history</h1>
        {loading ? (
          <div>Loading...</div>
        ) : documents.length === 0 ? (
          <div>No documents found.</div>
        ) : (
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '1.5rem',
            marginTop: '2rem',
            paddingLeft: '20px',
            paddingRight: '20px'
          }}>
            {documents.map(doc => (
              <div
                key={doc.document_id}
                style={{
                  border: '1px solid #eaeaea',
                  borderRadius: '10px',
                  padding: '1.5rem',
                  width: '300px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  background: '#fff',
                  position: 'relative',
                  paddingLeft: '20px',
                  paddingRight: '20px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                  <img src="/icons/pdf.png" alt="PDF" style={{ width: 32, height: 32, marginRight: 10 }} />
                  <span style={{ fontWeight: 600 }}>{doc.filename || 'Untitled'}</span>
                </div>
                <div style={{ fontSize: 14, color: '#666', marginBottom: 8 }}>
                  Uploaded: {doc.upload_date ? new Date(doc.upload_date).toLocaleString() : 'Unknown'}
                </div>
                <div style={{ fontSize: 14, color: '#888', marginBottom: 16 }}>
                  Chunks: {doc.chunks_count}
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                  <button
                    onClick={() => handleView(doc.document_id)}
                    style={{
                      background: '#0070f3',
                      color: '#fff',
                      border: 'none',
                      borderRadius: 4,
                      padding: '6px 14px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                  >
                    <img src='/icons/view.png' alt='View Icon' style={{ width: 16, height: 16, marginRight: 4 }} />  
                    View 
                  </button>
                  <button
                    onClick={() => handleDelete(doc.document_id)}
                    style={{
                      background: '#ffffff',
                      // color: '#fff',
                      // border: 'none',
                      borderRadius: 4,
                      padding: '6px 14px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      border: '1px solid red',
                    }}
                  >
                    <img src='/icons/trash.png' alt='View Icon' style={{ width: 16, height: 16, marginRight: 4 }} />
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
        <button className="btn-history" onClick={() => getBack()} style={{ marginTop: '40px'}}>
          Back to Home
         </button>
      </main>
    </div>
  );
}