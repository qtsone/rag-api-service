# services/api/app/document_processor.py
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from typing import Dict, Any, List
import os

class DocumentProcessor:
    def __init__(self):
        self.model = SentenceTransformer('all-mpnet-base-v2')
        self.qdrant = QdrantClient(
            host=os.getenv("QDRANT_HOST"),
            port=int(os.getenv("QDRANT_PORT"))
        )

    async def process_document(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a document by generating embeddings and storing in Qdrant
        """
        # Generate embedding
        embedding = self.model.encode(content)

        # Store in Qdrant
        self.qdrant.upsert(
            collection_name="knowledge_base",
            points=[{
                "id": str(metadata.get('id')),
                "vector": embedding.tolist(),
                "payload": {
                    "content": content,
                    "metadata": metadata
                }
            }]
        )

        return {
            "status": "success",
            "document_id": metadata.get('id')
        }

    async def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents using the query
        """
        query_vector = self.model.encode(query)
        
        results = self.qdrant.search(
            collection_name="knowledge_base",
            query_vector=query_vector.tolist(),
            limit=top_k
        )
        
        return [{
            "content": hit.payload["content"],
            "metadata": hit.payload["metadata"],
            "score": hit.score
        } for hit in results]
