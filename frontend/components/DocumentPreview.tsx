import { useAppContext } from '@/context/AppContext';

export default function DocumentPreview() {
  const {state, setState} = useAppContext();

  const handleClose = () => {
    setState({...state, isUploaded: false, documentId: '', documentName: '', file: null});
  }

  return (
    <div className="document-container">
      <div className="document-wrapper">
        <img src="/icons/pdf.png" alt="PDF Icon" className="document-icon" />
        <div className="document-placeholder">{ state.file?.name}</div>
      </div>
      <a href="javascript:void(0);" onClick={handleClose} className="document-close">
        <img className="close-icon" src="/icons/close.png" alt="Close Icon" />
      </a>
    </div>
  );
}