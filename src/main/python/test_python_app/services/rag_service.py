import logging
import re
from typing import List, Dict

from sqlalchemy.orm import Session

from ..models.domain.entities import Document, DocumentChunk

logger = logging.getLogger(__name__)


class RAGService:
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(f"RAG Service initialized (chunk_size={chunk_size}, overlap={chunk_overlap})")
    
    def chunk_document(self, content: str) -> List[Dict[str, any]]:
        if not content:
            return []
        
        paragraphs = re.split(r'\n\s*\n', content)
        
        chunks = []
        current_chunk = ""
        start_char = 0
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                end_char = start_char + len(current_chunk)
                chunks.append({
                    "content": current_chunk,
                    "start_char": start_char,
                    "end_char": end_char,
                    "chunk_index": chunk_index
                })
                
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                current_chunk = overlap_text + " " + paragraph
                start_char = end_char - len(overlap_text)
                chunk_index += 1
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        if current_chunk:
            chunks.append({
                "content": current_chunk,
                "start_char": start_char,
                "end_char": start_char + len(current_chunk),
                "chunk_index": chunk_index
            })
        
        logger.info(f"Document chunked into {len(chunks)} chunks")
        return chunks
    
    def process_document(self, db: Session, document: Document) -> int:
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()
        
        chunks = self.chunk_document(document.content)
        
        for chunk_data in chunks:
            chunk = DocumentChunk(
                document_id=document.id,
                content=chunk_data["content"],
                chunk_index=chunk_data["chunk_index"],
                start_char=chunk_data["start_char"],
                end_char=chunk_data["end_char"]
            )
            db.add(chunk)
        
        db.commit()
        logger.info(f"Created {len(chunks)} chunks for document {document.id}")
        return len(chunks)
    
    def keyword_search(self, query: str, chunks: List[DocumentChunk], top_k: int = 3) -> List[DocumentChunk]:
        if not chunks:
            return []
        
        query_keywords = set(re.findall(r'\b\w+\b', query.lower()))
        
        stop_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        query_keywords = query_keywords - stop_words
        
        scored_chunks = []
        for chunk in chunks:
            chunk_text = chunk.content.lower()
            chunk_keywords = set(re.findall(r'\b\w+\b', chunk_text))
            
            overlap = len(query_keywords & chunk_keywords)
            
            phrase_matches = sum(1 for keyword in query_keywords if keyword in chunk_text)
            
            score = overlap + (phrase_matches * 0.5)
            
            if score > 0:
                scored_chunks.append((score, chunk))
        
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [chunk for score, chunk in scored_chunks[:top_k]]
        
        logger.info(f"Retrieved {len(top_chunks)} chunks for query: '{query[:50]}...'")
        return top_chunks
    
    def retrieve_context(self, db: Session, document_ids: List[str], query: str, top_k: int = 3) -> str:
        if not document_ids:
            return ""
        
        chunks = db.query(DocumentChunk).join(Document).filter(
            Document.id.in_(document_ids)
        ).all()
        
        if not chunks:
            logger.warning(f"No chunks found for documents: {document_ids}")
            return ""
        
        top_chunks = self.keyword_search(query, chunks, top_k=top_k)
        
        if not top_chunks:
            return ""
        
        context_parts = []
        for i, chunk in enumerate(top_chunks, 1):
            context_parts.append(f"[Context {i}]\n{chunk.content}")
        
        context = "\n\n".join(context_parts)
        logger.info(f"Retrieved {len(top_chunks)} chunks ({len(context)} chars) for query")
        return context
