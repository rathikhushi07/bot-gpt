from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from ....core.database import get_db_manager
from ....models.domain.entities import Document, User
from ....models.schemas.request_schemas import UploadDocumentRequest, DocumentResponse
from ....services.rag_service import RAGService

router = APIRouter(prefix="/documents", tags=["Documents"])

# Service instances
rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    if rag_service is None:
        raise HTTPException(status_code=500, detail="RAG service not initialized")
    return rag_service


def init_rag_service(service: RAGService):
    global rag_service
    rag_service = service


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=201,
    summary="Upload document",
    description="Upload a document for RAG mode conversations"
)
def upload_document(
    request: UploadDocumentRequest,
    service: RAGService = Depends(get_rag_service)
):
    db_manager = get_db_manager()
    
    try:
        with db_manager.get_session() as db:
            # Verify user exists
            user = db.query(User).filter(User.id == request.user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Create document
            document = Document(
                user_id=request.user_id,
                filename=request.filename,
                content=request.content,
                file_size=len(request.content),
                mime_type=request.mime_type
            )
            db.add(document)
            db.flush()
            
            # Process document and create chunks
            chunk_count = service.process_document(db, document)
            
            return DocumentResponse(
                id=document.id,
                user_id=document.user_id,
                filename=document.filename,
                file_size=document.file_size,
                mime_type=document.mime_type,
                chunk_count=chunk_count,
                created_at=document.created_at
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@router.get(
    "",
    response_model=List[DocumentResponse],
    summary="List documents",
    description="Get list of documents for a user"
)
def list_documents(
    user_id: str,
    service: RAGService = Depends(get_rag_service)
):
    db_manager = get_db_manager()
    
    try:
        with db_manager.get_session() as db:
            documents = db.query(Document).filter(
                Document.user_id == user_id
            ).order_by(Document.created_at.desc()).all()
            
            return [
                DocumentResponse(
                    id=doc.id,
                    user_id=doc.user_id,
                    filename=doc.filename,
                    file_size=doc.file_size,
                    mime_type=doc.mime_type,
                    chunk_count=len(doc.chunks),
                    created_at=doc.created_at
                )
                for doc in documents
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document",
    description="Get document details"
)
def get_document(document_id: str):
    db_manager = get_db_manager()
    
    try:
        with db_manager.get_session() as db:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            return DocumentResponse(
                id=document.id,
                user_id=document.user_id,
                filename=document.filename,
                file_size=document.file_size,
                mime_type=document.mime_type,
                chunk_count=len(document.chunks),
                created_at=document.created_at
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.delete(
    "/{document_id}",
    status_code=204,
    summary="Delete document",
    description="Delete a document and its chunks"
)
def delete_document(document_id: str):
    db_manager = get_db_manager()
    
    try:
        with db_manager.get_session() as db:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            db.delete(document)
            db.commit()
            return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

