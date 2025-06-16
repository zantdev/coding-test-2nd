import logging
import time
import os
import re
import uuid
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
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
    documents = pdf_processor.split_into_chunks(pages_content, document_id, unique_filename)
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
            # Try to parse or fallback to now
            uploaded_at = meta.get("uploaded_at")
            if uploaded_at is None:
                upload_date = datetime.utcnow()
            elif isinstance(uploaded_at, datetime):
                upload_date = uploaded_at
            else:
                try:
                    upload_date = datetime.fromisoformat(uploaded_at)
                except Exception:
                    upload_date = datetime.utcnow()
            doc_info[doc_id] = {
                "document_id": doc_id,
                "filename": meta.get("filename", ""),
                "upload_date": upload_date,
                "chunks_count": 0,
                "status": meta.get("status", "processed"),
            }
        doc_info[doc_id]["chunks_count"] += 1

    documents = list(doc_info.values())
    return DocumentsResponse(documents=documents)


@app.get("/api/document/{document_id}")
async def get_document_pdf(document_id: str):
    """
    Serve the PDF file for a given document_id.
    """
    vector_store = VectorStoreService()
    collection = vector_store.vector_store._collection
    metadatas = collection.get(include=["metadatas"]).get("metadatas", [])
    all_metadatas = [m for sublist in metadatas for m in (sublist if isinstance(sublist, list) else [sublist]) if m]
    # Find the first chunk with this document_id to get the filename
    for meta in all_metadatas:
        if meta.get("document_id") == document_id:
            filename = meta.get("filename")
            break
    else:
        raise HTTPException(status_code=404, detail="Document not found")
    pdf_upload_path = getattr(settings, "pdf_upload_path", "uploaded_files")
    file_path = os.path.join(pdf_upload_path, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    headers = {
        "Content-Disposition": f'inline; filename="{filename}"',
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        # Optionally, restrict framing or scripts:
        # "Content-Security-Policy": "frame-ancestors 'self';"
    }
    return FileResponse(file_path, media_type="application/pdf", filename=filename, headers=headers)


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str = Path(..., description="The document_id to delete")):
    vector_store = VectorStoreService()
    collection = vector_store.vector_store._collection
    result = collection.get(include=["metadatas"])
    ids = result.get("ids", [])
    metadatas = result.get("metadatas", [])
    ids_to_delete = []
    filename = None
    for idx, meta in enumerate(metadatas):
        if meta and meta.get("document_id") == document_id:
            ids_to_delete.append(ids[idx])
            if not filename:
                filename = meta.get("filename")
    if not ids_to_delete:
        raise HTTPException(status_code=404, detail="Document not found")

    vector_store.delete_documents(ids_to_delete)

    pdf_upload_path = getattr(settings, "pdf_upload_path", "uploaded_files")
    if filename:
        file_path = os.path.join(pdf_upload_path, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    return {"message": f"Document {document_id} and its chunks deleted successfully."}


@app.get("/api/chunks")
async def get_chunks():
    """Get document chunks (optional endpoint)"""
    # TODO: Implement chunk listing
    # - Return document chunks with metadata
    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port, reload=settings.debug) 