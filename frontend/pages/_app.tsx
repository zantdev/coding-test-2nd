import '../styles/main.scss'
import type { AppProps } from 'next/app'
import React, { createContext, useState } from 'react'
import { AppProvider } from '@/context/AppContext';


export default function App({ Component, pageProps }: AppProps) {
  const [isUploaded, setIsUploaded] = useState(false);
  const [documentId, setDocumentId] = useState<string | null>(null);

  return (
    <AppProvider>
      <Component {...pageProps} />
    </AppProvider>
  )
} 