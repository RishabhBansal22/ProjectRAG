"""Configuration management for RAG project."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration class for all project settings."""
    
    # API Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    
    # Model Settings
    CHAT_MODEL: str = os.getenv("CHAT_MODEL", "gemini-2.0-flash")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
    
    # Vector Store Settings
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "rag_documents")
    VECTOR_DISTANCE: str = os.getenv("VECTOR_DISTANCE", "COSINE")
    
    # Document Processing Settings
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # Indexing Settings
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "10"))  # Number of docs to index per batch
    
    # Retrieval Settings
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "3"))
    
    @classmethod
    def validate(cls) -> None:
        """Validate that required environment variables are set."""
        missing_keys = []
        
        if not cls.GOOGLE_API_KEY:
            missing_keys.append("GOOGLE_API_KEY")
        if not cls.QDRANT_API_KEY:
            missing_keys.append("QDRANT_API_KEY")
        if not cls.QDRANT_URL:
            missing_keys.append("QDRANT_URL")
            
        if missing_keys:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_keys)}"
            )


# Create a singleton instance
config = Config()
