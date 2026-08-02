import asyncio
import os
import uuid
from typing import Dict, List, Any, Optional
import chromadb
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class SearchService:
    """Service for vector search using ChromaDB"""

    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id
        self.base_path = os.getenv("CHROMADB_PATH", "./data/chromadb")
        self.client = chromadb.PersistentClient(
            path=self._get_user_chromadb_path()
        )
        self.collection = self._get_or_create_collection()

    def _get_user_chromadb_path(self) -> str:
        """Get user-specific ChromaDB path"""
        if not self.user_id:
            return os.path.join(self.base_path, "default")
        return os.path.join(self.base_path, self.user_id)

    def _get_or_create_collection(self):
        """Get or create the memories collection"""
        try:
            collection_name = "memories"
            if self.user_id:
                collection_name = f"memories_{self.user_id}"
            
            return self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            raise

    async def store_memory(
        self,
        content: str,
        extracted_data: Dict[str, Any],
        filename: str
    ) -> str:
        """
        Store a memory in the vector database
        
        Args:
            content: Full transcript text
            extracted_data: Extracted structured data
            filename: Original filename
            
        Returns:
            Memory ID
        """
        try:
            memory_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()

            # Prepare metadata
            metadata = {
                "filename": filename,
                "timestamp": timestamp,
                "summary": extracted_data.get("summary", ""),
                "sentiment": extracted_data.get("sentiment", "neutral"),
                "topics": json.dumps(extracted_data.get("topics", [])),
                "tags": json.dumps(extracted_data.get("tags", [])),
                "people": json.dumps(extracted_data.get("people", [])),
                "tasks": json.dumps(extracted_data.get("tasks", [])),
                "action_items": json.dumps(extracted_data.get("action_items", []))
            }

            # Store in ChromaDB
            await asyncio.to_thread(
                self.collection.add,
                ids=[memory_id],
                documents=[content],
                metadatas=[metadata]
            )

            logger.info(f"Stored memory: {memory_id}")
            return memory_id

        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            raise

    async def search(
        self,
        query: str,
        threshold: float = 0.5,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search memories using semantic search
        
        Args:
            query: Search query
            threshold: Similarity threshold (0-1)
            n_results: Number of results to return
            
        Returns:
            List of search results
        """
        try:
            # Query ChromaDB
            results = await asyncio.to_thread(
                self.collection.query,
                query_texts=[query],
                n_results=n_results
            )

            # Format results
            formatted_results = []
            if results and results['ids'] and results['ids'][0]:
                for i, memory_id in enumerate(results['ids'][0]):
                    similarity = results['distances'][0][i] if results['distances'] else 0
                    
                    # Convert similarity to 0-1 range (cosine distance)
                    similarity_score = 1 - similarity

                    if similarity_score >= threshold:
                        metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                        
                        formatted_results.append({
                            "id": memory_id,
                            "date": metadata.get("timestamp", "").split("T")[0],
                            "similarity": similarity_score,
                            "content": results['documents'][0][i] if results['documents'] else "",
                            "tags": json.loads(metadata.get("tags", "[]")),
                            "summary": metadata.get("summary", ""),
                            "sentiment": metadata.get("sentiment", "")
                        })

            logger.info(f"Search for '{query}' returned {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise

    async def list_memories(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all memories with pagination
        """
        try:
            # Get all memories (ChromaDB doesn't have native pagination)
            all_results = await asyncio.to_thread(
                self.collection.get,
                limit=limit + offset
            )

            memories = []
            if all_results and all_results['ids']:
                for i, memory_id in enumerate(all_results['ids'][offset:offset+limit]):
                    metadata = all_results['metadatas'][i + offset] if all_results['metadatas'] else {}
                    
                    memories.append({
                        "id": memory_id,
                        "date": metadata.get("timestamp", "").split("T")[0],
                        "timestamp": metadata.get("timestamp", ""),
                        "content": all_results['documents'][i + offset] if all_results['documents'] else "",
                        "tags": json.loads(metadata.get("tags", "[]")),
                        "summary": metadata.get("summary", "")
                    })

            return memories

        except Exception as e:
            logger.error(f"Error listing memories: {str(e)}")
            raise

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory
        """
        try:
            await asyncio.to_thread(
                self.collection.delete,
                ids=[memory_id]
            )
            logger.info(f"Deleted memory: {memory_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}")
            raise

    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a memory
        """
        try:
            update_kwargs = {"ids": [memory_id]}
            
            if content:
                update_kwargs["documents"] = [content]
            if metadata:
                update_kwargs["metadatas"] = [metadata]

            await asyncio.to_thread(
                self.collection.update,
                **update_kwargs
            )
            logger.info(f"Updated memory: {memory_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating memory: {str(e)}")
            raise
