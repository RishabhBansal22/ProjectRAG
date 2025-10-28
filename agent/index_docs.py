"""Document indexing pipeline for RAG system."""
import logging
import time
import sys
import argparse
from pathlib import Path
from typing import List
from langchain_core.documents import Document

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.document import load_web_document, split_documents
from qdrant.client import QdrantClientWrapper
from lang_comps.components import VectorStore, GoogleEmbedding
from config import config
from url_mapper import URLCollectionMapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_components(collection_name: str):
    """
    Initialize all required components for document indexing.
    
    Args:
        collection_name: Name of the collection to use
    
    Returns:
        Tuple of (embeddings_client, qdrant_client, vector_store)
    """
    try:
        # Validate configuration
        config.validate()
        
        # Initialize embedding model
        embeddings = GoogleEmbedding(
            api_key=config.GOOGLE_API_KEY,
            model=config.EMBEDDING_MODEL
        )
        embed_client = embeddings.get_client()
        
        # Initialize Qdrant client
        qdrant = QdrantClientWrapper(
            api_key=config.QDRANT_API_KEY,
            url=config.QDRANT_URL
        )
        
        # Create collection with proper vector size
        sample_embedding = embed_client.embed_query("sample text")
        vector_size = len(sample_embedding)
        qdrant.create_collection(
            collection_name=collection_name,
            vector_size=vector_size
        )
        
        # Initialize vector store
        store = VectorStore(
            client=qdrant.client,
            collection_name=collection_name,
            embeddings=embed_client
        )
        vector_store = store.get_vector_store()
        
        logger.info("Successfully initialized all components")
        return embed_client, qdrant, vector_store
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise


def index_documents(url: str, vector_store, batch_size: int = 10) -> List[str]:
    """
    Index documents from a URL into the vector store with batching.
    
    Args:
        url: URL of the document to index
        vector_store: Vector store instance
        batch_size: Number of documents to index per batch (default: 10)
        
    Returns:
        List of document IDs
        
    Raises:
        Exception: If indexing fails
    """
    try:
        logger.info(f"Starting document indexing from {url}")
        
        # Load and split documents
        docs = load_web_document(url)
        splits = split_documents(
            docs,
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP
        )
        
        logger.info(f"Processing {len(splits)} document chunks in batches of {batch_size}")
        
        # Index documents in batches to avoid timeouts
        all_doc_ids = []
        total_batches = (len(splits) + batch_size - 1) // batch_size
        
        for i in range(0, len(splits), batch_size):
            batch = splits[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"Indexing batch {batch_num}/{total_batches} ({len(batch)} documents)")
            
            # Retry logic for each batch
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    doc_ids = vector_store.add_documents(documents=batch)
                    all_doc_ids.extend(doc_ids)
                    logger.info(f"Successfully indexed batch {batch_num}/{total_batches}")
                    break
                    
                except Exception as batch_error:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                        logger.warning(
                            f"Batch {batch_num} failed (attempt {attempt + 1}/{max_retries}): {batch_error}. "
                            f"Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Batch {batch_num} failed after {max_retries} attempts: {batch_error}")
                        raise
            
            # Small delay between batches to avoid overwhelming the server
            if i + batch_size < len(splits):
                time.sleep(0.5)
        
        logger.info(f"Successfully indexed {len(all_doc_ids)} document chunks across {total_batches} batches")
        return all_doc_ids
        
    except Exception as e:
        logger.error(f"Failed to index documents: {e}")
        raise


def main():
    """Main function to run document indexing."""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Index web documents into Qdrant vector database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index a single URL
  python agent/index_docs.py https://example.com/article
  
  # Index with custom batch size
  python agent/index_docs.py https://example.com/article --batch-size 5
  
  # List all indexed URLs
  python agent/index_docs.py --list
        """
    )
    parser.add_argument(
        'url',
        nargs='?',
        help='URL of the web page to index'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=config.BATCH_SIZE,
        help=f'Number of documents to index per batch (default: {config.BATCH_SIZE})'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all indexed URLs and their collections'
    )
    parser.add_argument(
        '--reindex',
        action='store_true',
        help='Force reindexing even if URL was previously indexed'
    )
    
    args = parser.parse_args()
    
    # Initialize URL mapper
    mapper = URLCollectionMapper()
    
    # Handle list command
    if args.list:
        mappings = mapper.list_all_mappings()
        if not mappings:
            print("No URLs have been indexed yet.")
            return
        
        print("\n📚 Indexed URLs and Collections:")
        print("=" * 80)
        for url, info in mappings.items():
            print(f"\nURL: {url}")
            print(f"  Collection: {info['collection_name']}")
            print(f"  Documents: {info['document_count']}")
            print(f"  Created: {info['created_at']}")
            print(f"  Last Indexed: {info['last_indexed'] or 'Never'}")
        print("=" * 80)
        return
    
    # Require URL if not listing
    if not args.url:
        parser.print_help()
        sys.exit(1)
    
    url = args.url
    
    try:
        # Get or create collection for this URL
        collection_name, is_existing = mapper.get_collection_name(url)
        
        if is_existing and not args.reindex:
            logger.info(f"URL '{url}' was previously indexed in collection '{collection_name}'")
            response = input("Do you want to reindex? This will add new documents. (y/N): ")
            if response.lower() != 'y':
                logger.info("Indexing cancelled.")
                return
        
        logger.info(f"Using collection: {collection_name}")
        
        # Initialize components with the collection name
        _, _, vector_store = initialize_components(collection_name)
        
        # Index documents from URL
        doc_ids = index_documents(
            url, 
            vector_store,
            batch_size=args.batch_size
        )
        
        # Update mapper with indexing info
        mapper.update_indexing_info(url, len(doc_ids))
        
        logger.info(f"✅ Indexing completed successfully!")
        logger.info(f"   URL: {url}")
        logger.info(f"   Collection: {collection_name}")
        logger.info(f"   Total documents: {len(doc_ids)}")
        
    except KeyboardInterrupt:
        logger.info("\nIndexing cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        raise


if __name__ == "__main__":
    main()