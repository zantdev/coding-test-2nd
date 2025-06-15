import React, { createContext, useContext, useState, ReactNode } from 'react';

type StoreState = {
  isUploaded: boolean;
  userName: string;
  documentId: string;
  file: File | null;
  isUploading: boolean;
  uploadProgress: number;
};

type StoreContextType = {
  state: StoreState;
  setState: React.Dispatch<React.SetStateAction<StoreState>>;
};

const initialState: StoreState = {
  isUploaded: false,
  userName: '',
  documentId: '',
  file: null,
  isUploading: false,
  uploadProgress: 0
};

const AppContext = createContext<StoreContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [state, setState] = useState<StoreState>(initialState);

  return (
    <AppContext.Provider value={{ state, setState }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useAppContext must be used within AppProvider');
  return context;
};