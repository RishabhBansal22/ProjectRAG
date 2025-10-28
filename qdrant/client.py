"""Qdrant vector database client wrapper."""
import logging
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

logger = logging.getLogger(__name__)


class QdrantClientWrapper:
    """Wrapper for Qdrant client with enhanced functionality."""
    
    def __init__(self, api_key: str, url: str):
        """
        Initialize Qdrant client.
        
        Args:
            api_key: Qdrant API key
            url: Qdrant server URL
        """
        if not api_key or not url:
            raise ValueError("Both api_key and url are required for Qdrant client")
            
        try:
            self.client = QdrantClient(api_key=api_key, url=url)
            logger.info("Successfully connected to Qdrant")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise

    def create_collection(
        self, 
        collection_name: str, 
        vector_size: int,
        distance: Distance = Distance.COSINE,
        force_recreate: bool = False
    ) -> None:
        """
        Create a collection if it doesn't exist.
        
        Args:
            collection_name: Name of the collection
            vector_size: Dimension of the vectors
            distance: Distance metric to use
            force_recreate: If True, delete and recreate existing collection
        """
        try:
            exists = self.client.collection_exists(collection_name=collection_name)
            
            if exists and force_recreate:
                logger.info(f"Deleting existing collection: {collection_name}")
                self.client.delete_collection(collection_name=collection_name)
                exists = False
            
            if not exists:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=distance
                    )
                )
                logger.info(f"Created collection: {collection_name}")
            else:
                logger.info(f"Collection already exists: {collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise

    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection if it exists."""
        try:
            if self.client.collection_exists(collection_name=collection_name):
                self.client.delete_collection(collection_name=collection_name)
                logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            raise

    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        try:
            return self.client.collection_exists(collection_name=collection_name)
        except Exception as e:
            logger.error(f"Failed to check collection existence: {e}")
            raise
