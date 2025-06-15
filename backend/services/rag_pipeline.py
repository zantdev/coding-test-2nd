import logging
import time
import os

import cohere
from typing import List, Dict, Any, Tuple, Optional
from langchain.schema import Document
from services.vector_store import VectorStoreService
from config import settings

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self):
        # Load config from .env via settings or os.environ
        self.llm_model = getattr(settings, "llm_model", os.getenv("llm_model", "command"))
        self.max_tokens = int(getattr(settings, "max_tokens", os.getenv("MAX_TOKENS", 512)))
        self.retrieval_k = int(getattr(settings, "retrieval_k", os.getenv("RETRIEVAL_K", 5)))
        self.similarity_threshold = float(getattr(settings, "similarity_threshold", os.getenv("SIMILARITY_THRESHOLD", 0.0)))
        self.cohere_api_key = getattr(settings, "cohere_api_key", os.getenv("COHERE_API_KEY"))
        self.cohere_client = cohere.Client(self.cohere_api_key)

        self.vector_store = VectorStoreService()

    def generate_answer(self, question: str, chat_history: List[Dict[str, str]] = None, document_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate answer using RAG pipeline"""
        start_time = time.time()
        # 1. Retrieve relevant documents
        retrieved_docs = self._retrieve_documents(question, document_id=document_id)
        # 2. Generate context from retrieved documents
        context = self._generate_context(retrieved_docs)
        # 3. Generate answer using Cohere LLM
        answer = self._generate_llm_response(question, context, chat_history)
        # 4. Return answer with sources and processing time
        processing_time = time.time() - start_time
        sources = [
            {
                "content": doc.page_content,
                "page": doc.metadata.get("page_num", -1),
                "score": score,
                "metadata": doc.metadata,
            }
            for doc, score in retrieved_docs
        ]
        return {
            "answer": answer,
            "sources": sources,
            "processing_time": processing_time,
        }

    def _retrieve_documents(self, query: str, document_id: Optional[str] = None) -> List[Tuple[Document, float]]:
        """Retrieve relevant documents for the query"""
        results = self.vector_store.similarity_search(query, k=self.retrieval_k, document_id=document_id)
        filtered = [
            (doc, score)
            for doc, score in results
            if score >= self.similarity_threshold
        ]
        logger.info(f"Retrieved {len(filtered)} documents above similarity threshold.")
        return filtered

    def _generate_context(self, documents: List[Tuple[Document, float]]) -> str:
        """Generate context string from retrieved documents"""
        context_chunks = []
        total_chars = 0
        for doc, score in documents:
            chunk = doc.page_content
            if total_chars + len(chunk) > 3000 * 4:  # rough estimate: 1 token ≈ 4 chars
                break
            context_chunks.append(chunk)
            total_chars += len(chunk)
        return "\n\n".join(context_chunks)

    def _generate_llm_response(self, question: str, context: str, chat_history: List[Dict[str, str]] = None) -> str:
        """Generate response using Cohere LLM"""
        prompt = self._build_prompt(question, context, chat_history)
        try:
            response = self.cohere_client.chat(
                message=prompt,
                model=self.llm_model,
                max_tokens=self.max_tokens,
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "Sorry, I couldn't generate an answer at this time."

    def _build_prompt(self, question: str, context: str, chat_history: List[Dict[str, str]] = None) -> str:
        """Build prompt for Cohere LLM with context and chat history"""
        messages = []
        if chat_history:
            for chat in chat_history:
                messages.append(f"User: {chat.get('question', '')}")
                messages.append(f"Assistant: {chat.get('answer', '')}")
        system_prompt = (
            "You are a helpful assistant for answering questions about financial documents. "
            "Use the provided context to answer the user's question as accurately as possible."
        )
        prompt_parts = [system_prompt]
        if context:
            prompt_parts.append(f"Context:\n{context}")
        prompt_parts.extend(messages)
        prompt_parts.append(f"User: {question}")
        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)
