"""Retrieval tool for RAG agent."""
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain.tools import tool
from langchain_core.documents import Document
from lang_comps.components import VectorStore, GoogleEmbedding
from qdrant.client import QdrantClientWrapper
from config import config
from url_mapper import URLCollectionMapper

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service for managing document retrieval operations."""
    
    _instance = None
    _vector_stores = {}  # Cache of collection_name -> vector_store
    _embeddings = None
    _qdrant = None
    _active_collection = None  # Current collection being used
    
    def __new__(cls):
        """Singleton pattern to ensure single instance."""
        if cls._instance is None:
            cls._instance = super(RetrievalService, cls).__new__(cls)
        return cls._instance
    
    def set_active_collection(self, collection_name: str):
        """
        Set the active collection for queries.
        
        Args:
            collection_name: Name of the collection to use
        """
        self._active_collection = collection_name
        logger.info(f"Active collection set to: {collection_name}")
    
    def get_active_collection(self) -> Optional[str]:
        """Get the currently active collection name."""
        return self._active_collection
    
    def _initialize_clients(self):
        """Initialize embedding and Qdrant clients (only once)."""
        if self._embeddings is None:
            embeddings = GoogleEmbedding(
                api_key=config.GOOGLE_API_KEY,
                model=config.EMBEDDING_MODEL
            )
            self._embeddings = embeddings.get_client()
            
        if self._qdrant is None:
            self._qdrant = QdrantClientWrapper(
                api_key=config.QDRANT_API_KEY,
                url=config.QDRANT_URL
            )
    
    def get_vector_store(self, collection_name: Optional[str] = None):
        """
        Get vector store for a specific collection or default.
        
        Args:
            collection_name: Name of the collection, or None for default
            
        Returns:
            Vector store instance
        """
        # Use default collection if none specified
        if collection_name is None:
            collection_name = config.COLLECTION_NAME
        
        # Return cached vector store if available
        if collection_name in self._vector_stores:
            return self._vector_stores[collection_name]
        
        try:
            # Initialize clients
            self._initialize_clients()
            
            # Check if collection exists
            if not self._qdrant.collection_exists(collection_name):
                logger.warning(
                    f"Collection '{collection_name}' does not exist. "
                    "Please run index_docs.py first."
                )
                raise ValueError(f"Collection '{collection_name}' not found")
            
            # Initialize vector store
            store = VectorStore(
                client=self._qdrant.client,
                collection_name=collection_name,
                embeddings=self._embeddings
            )
            vector_store = store.get_vector_store()
            
            # Cache it
            self._vector_stores[collection_name] = vector_store
            
            logger.info(f"Successfully initialized retrieval service for collection: {collection_name}")
            return vector_store
            
        except Exception as e:
            logger.error(f"Failed to initialize retrieval service: {e}")
            raise
    
    def get_all_collections(self) -> List[str]:
        """Get list of all available collections."""
        mapper = URLCollectionMapper()
        mappings = mapper.list_all_mappings()
        return [info['collection_name'] for info in mappings.values()]


# Initialize the retrieval service
retrieval_service = RetrievalService()


@tool(response_format="content_and_artifact")
def retrieve_context(query: str) -> Tuple[str, List[Document]]:
    """
    Retrieve relevant context from the document store to help answer a query.
    
    This tool searches the vector database for documents similar to the query
    and returns the most relevant results.
    
    Args:
        query: The search query or question
        
    Returns:
        Tuple of (formatted_string, list_of_documents)
        - formatted_string: Concatenated results with source metadata
        - list_of_documents: List of retrieved Document objects
    """
    try:
        # Get the active collection (set by the main agent)
        collection_name = retrieval_service.get_active_collection()
        
        if not collection_name:
            logger.warning("No active collection set")
            return "No collection is currently active. Please specify a URL.", []
        
        # Get vector store for the collection
        vector_store = retrieval_service.get_vector_store(collection_name)
        
        # Retrieve similar documents
        retrieved_docs = vector_store.similarity_search(
            query, 
            k=config.TOP_K_RESULTS
        )
        
        if not retrieved_docs:
            logger.warning(f"No documents found for query: {query}")
            return "No relevant documents found.", []
        
        # Format results
        serialized = "\n\n".join(
            f"Source: {doc.metadata}\nContent: {doc.page_content}"
            for doc in retrieved_docs
        )
        
        logger.info(f"Retrieved {len(retrieved_docs)} documents from collection '{collection_name}'")
        return serialized, retrieved_docs
        
    except Exception as e:
        logger.error(f"Failed to retrieve context: {e}")
        error_msg = f"Error retrieving context: {str(e)}"
        return error_msg, []
