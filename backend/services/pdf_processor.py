import logging

from typing import List, Dict, Any, Optional
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

logger = logging.getLogger(__name__)


class PDFProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        # Initialize text splitter with chunk size and overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def extract_text_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from PDF and return page-wise content.
        Returns a list of dicts: [{"page_num": int, "text": str}]
        """
        pages_content = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages_content.append({
                    "page_num": i + 1,
                    "text": text
                })
        logger.info(f"Extracted text from {len(pages_content)} pages.")
        logger.info(pages_content)
        return pages_content

    def split_into_chunks(self, pages_content: List[Dict[str, Any]], document_id: Optional[str] = None) -> List[Document]:
        """
        Split page content into chunks.
        Returns a list of langchain.schema.Document objects.
        """
        documents = []
        for page in pages_content:
            chunks = self.text_splitter.split_text(page["text"])
            for idx, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "page_num": page["page_num"],
                        "chunk_idx": idx,
                        "document_id": document_id
                    }
                )
                documents.append(doc)
        logger.info(f"Split into {len(documents)} chunks.")
        return documents

    def process_pdf(self, file_path: str) -> List[Document]:
        """
        Complete PDF processing pipeline:
        1. Extract text from PDF.
        2. Split text into chunks.
        3. Return processed Document objects.
        """
        pages_content = self.extract_text_from_pdf(file_path)
        documents = self.split_into_chunks(pages_content)
        return documents
