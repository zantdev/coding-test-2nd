import logging
import time
import os
import re
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models.schemas import ChatRequest, ChatResponse, DocumentsResponse, UploadResponse
from services.pdf_processor import PDFProcessor
from services.vector_store import VectorStoreService
from services.rag_pipeline import RAGPipeline
from config import settings


# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG-based Financial Statement Q&A System",
    description="AI-powered Q&A system for financial documents using RAG",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
# TODO: Initialize your services here
pdf_processor = None
vector_store = None
rag_pipeline = RAGPipeline()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # TODO: Initialize your services
    logger.info("Starting RAG Q&A System...")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "RAG-based Financial Statement Q&A System is running"}


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    # 1. Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    # 2. Save uploaded file
    document_id = str(uuid.uuid4())
    original_filename = file.filename
    sanitized_filename = re.sub(r"\s+", "-", original_filename)
    unique_filename = f"{uuid.uuid4()}_{sanitized_filename}"
    pdf_upload_path = getattr(settings, "pdf_upload_path")
    os.makedirs(pdf_upload_path, exist_ok=True)
    file_path = os.path.join(pdf_upload_path, unique_filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 3. Extract text from PDF
    pdf_processor = PDFProcessor()
    start_time = time.time()
    pages_content = pdf_processor.extract_text_from_pdf(file_path)

    # 4. Split text into chunks
    documents = pdf_processor.split_into_chunks(pages_content, document_id)
    processing_time = time.time() - start_time

    # 5. (Optional) Store documents in vector database (not implemented here)
    vector_store = VectorStoreService()
    vector_store.add_documents(documents)

    # 6. Return response
    return UploadResponse(
        message="Upload and processing successful.",
        filename=unique_filename,
        chunks_count=len(documents),
        processing_time=processing_time,
        document_id=document_id
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process chat request and return AI response using RAG pipeline.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = rag_pipeline.generate_answer(
            question=request.question,
            chat_history=request.chat_history or [],
            document_id=request.document_id 
        )
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            processing_time=result["processing_time"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")


@app.get("/api/documents", response_model=DocumentsResponse)
async def get_documents():
    """Get list of processed documents"""
    vector_store = VectorStoreService()
    collection = vector_store.vector_store._collection
    metadatas = collection.get(include=["metadatas"]).get("metadatas", [])
    all_metadatas = [m for sublist in metadatas for m in (sublist if isinstance(sublist, list) else [sublist]) if m]
    doc_info = {}
    for meta in all_metadatas:
        doc_id = meta.get("document_id")
        if not doc_id:
            continue
        if doc_id not in doc_info:
            doc_info[doc_id] = {
                "document_id": doc_id,
                "filename": meta.get("filename", ""),
                "num_chunks": 0,
                "uploaded_at": meta.get("uploaded_at", None)
            }
        doc_info[doc_id]["num_chunks"] += 1

    documents = list(doc_info.values())
    return DocumentsResponse(documents=documents)


@app.get("/api/chunks")
async def get_chunks():
    """Get document chunks (optional endpoint)"""
    # TODO: Implement chunk listing
    # - Return document chunks with metadata
    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port, reload=settings.debug) 