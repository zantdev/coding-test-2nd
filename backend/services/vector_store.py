from typing import List, Tuple, Optional
from langchain.schema import Document
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings, CohereEmbeddings
from config import settings
import logging
import os

logger = logging.getLogger(__name__)


class VectorStoreService:
    def __init__(self):
        # Grab configuration from .env via settings or os.environ
        persist_dir = getattr(settings, "chroma_persist_dir", os.getenv("CHROMA_PERSIST_DIR", "chroma_db"))
        cohere_api_key = getattr(settings, "cohere_api_key", os.getenv("COHERE_API_KEY"))
        os.makedirs(persist_dir, exist_ok=True)
        self.embeddings = CohereEmbeddings(cohere_api_key=cohere_api_key)
        self.vector_store = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings
        )
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store"""
        if not documents:
            logger.warning("No documents to add to vector store.")
            return
        self.vector_store.add_documents(documents)
        self.vector_store.persist()
        logger.info(f"Added {len(documents)} documents to vector store.")

    def similarity_search(self, query: str, k: int = 5, document_id: Optional[str] = None) -> List[Tuple[Document, float]]:
        """Search for similar documents"""
        if not query:
            logger.warning("Empty query for similarity search.")
            return []
        if document_id:
            results = self.vector_store.similarity_search_with_score(query, k=k, filter={"document_id": document_id})
        else:
            results = self.vector_store.similarity_search_with_score(query, k=k)
        logger.info(f"Found {len(results)} similar documents for query.")
        return results

    def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from vector store"""
        if not document_ids:
            logger.warning("No document IDs provided for deletion.")
            return
        self.vector_store.delete(ids=document_ids)
        self.vector_store.persist()
        logger.info(f"Deleted {len(document_ids)} documents from vector store.")

    def get_document_count(self) -> int:
        """Get total number of documents in vector store"""
        count = self.vector_store._collection.count()
        logger.info(f"Vector store contains {count} documents.")
        return count
