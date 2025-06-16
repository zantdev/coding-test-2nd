import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';

export default function DocumentPreview() {
  const router = useRouter();
  const { document_id } = router.query;
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  useEffect(() => {
    if (document_id) {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
      setPdfUrl(`${backendUrl}/api/document/${document_id}`);
    }
  }, [document_id]);

  if (!pdfUrl) return <div>Loading...</div>;

  return (
    <div style={{ width: '100%', height: '100vh', background: '#f9f9f9' }}>
      <h1 style={{ textAlign: 'center' }}>Document Preview</h1>
      <div style={{ width: '100vw', height: '100vh', margin: 0, padding: 0 }}>
        <iframe
          src={pdfUrl}
          width="100%"
          height="100%"
          style={{
            border: 'none',
            width: '100%',
            height: '100%',
            display: 'block',
          }}
          title="PDF Preview"
        />
      </div>
    </div>
  );
}