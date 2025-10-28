"""LangChain components for chat models, embeddings, and vector stores."""
import logging
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)


class ChatGemini:
    """Wrapper for Google Gemini chat model."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        """
        Initialize Gemini chat model.
        
        Args:
            api_key: Google API key
            model: Model name to use
        """
        if not api_key:
            raise ValueError("Google API key is required")
            
        self.api_key = api_key
        self.model = model

    def get_client(self) -> ChatGoogleGenerativeAI:
        """
        Get the chat model client.
        
        Returns:
            ChatGoogleGenerativeAI instance
        """
        try:
            client = ChatGoogleGenerativeAI(
                google_api_key=self.api_key,
                model=self.model
            )
            logger.info(f"Initialized chat model: {self.model}")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize chat model: {e}")
            raise


class GoogleEmbedding:
    """Wrapper for Google embedding model."""
    
    def __init__(self, api_key: str, model: str = "models/gemini-embedding-001"):
        """
        Initialize Google embedding model.
        
        Args:
            api_key: Google API key
            model: Embedding model name
        """
        if not api_key:
            raise ValueError("Google API key is required")
            
        self.api_key = api_key
        self.model = model
    
    def get_client(self) -> GoogleGenerativeAIEmbeddings:
        """
        Get the embedding client.
        
        Returns:
            GoogleGenerativeAIEmbeddings instance
        """
        try:
            client = GoogleGenerativeAIEmbeddings(
                google_api_key=self.api_key,
                model=self.model
            )
            logger.info(f"Initialized embedding model: {self.model}")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise


class VectorStore:
    """Wrapper for Qdrant vector store."""
    
    def __init__(
        self, 
        client: QdrantClient, 
        collection_name: str, 
        embeddings: GoogleGenerativeAIEmbeddings
    ):
        """
        Initialize vector store.
        
        Args:
            client: Qdrant client instance
            collection_name: Name of the collection
            embeddings: Embedding model instance
        """
        if not client:
            raise ValueError("Qdrant client is required")
        if not collection_name:
            raise ValueError("Collection name is required")
        if not embeddings:
            raise ValueError("Embeddings model is required")
            
        self.client = client
        self.collection_name = collection_name
        self.embeddings = embeddings

    def get_vector_store(self) -> QdrantVectorStore:
        """
        Get the vector store instance.
        
        Returns:
            QdrantVectorStore instance
        """
        try:
            vector_store = QdrantVectorStore(
                client=self.client,
                collection_name=self.collection_name,
                embedding=self.embeddings
            )
            logger.info(f"Initialized vector store for collection: {self.collection_name}")
            return vector_store
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
