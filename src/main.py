# services/api/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
import asyncio
import logging
from typing import List, Dict, Any
from document_processor import DocumentProcessor
from postgresql_listener import PostgresListener

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG API Service")

class Query(BaseModel):
    text: str
    top_k: int = 5

class SearchResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

# Initialize the document processor and PostgreSQL listener
doc_processor = DocumentProcessor()
pg_listener = PostgresListener()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        await pg_listener.connect()
        await pg_listener.setup_trigger()
        pg_listener.register_callback(doc_processor.process_document)
        asyncio.create_task(pg_listener.start_listening())
        logger.info("Successfully initialized background tasks")
    except Exception as e:
        logger.error(f"Failed to initialize background tasks: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await pg_listener.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "qdrant": "connected",
            "postgresql": "connected" if pg_listener.conn else "disconnected",
            "ollama": "connected"  # You might want to add actual health check
        }
    }

@app.post("/search", response_model=SearchResponse)
async def search(query: Query):
    """
    Search endpoint that combines RAG with LLM response
    """
    try:
        # Get similar documents
        search_results = await doc_processor.search_similar(
            query.text, 
            query.top_k
        )
        
        # Prepare context from search results
        context = "\n".join([result["content"] for result in search_results])
        
        # Get LLM response using Ollama
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{os.getenv('OLLAMA_API_URL')}/api/generate",
                json={
                    "model": "llama2",
                    "prompt": f"Context: {context}\n\nQuestion: {query.text}\n\nAnswer:",
                    "stream": False
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500, 
                    detail="LLM processing failed"
                )
                
            llm_response = response.json()
        
        return SearchResponse(
            answer=llm_response["response"],
            sources=search_results
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search operation failed: {str(e)}"
        )

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        # You might want to implement actual stats collection
        return {
            "total_documents": 0,  # Implement actual count
            "last_indexed": None,  # Implement actual timestamp
            "system_status": "operational"
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve statistics"
        )
