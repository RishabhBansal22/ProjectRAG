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

from agent.document import load_document, load_documents_from_directory, split_documents
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


def index_documents(file_path: str, vector_store, batch_size: int = 10, is_directory: bool = False) -> List[str]:
    """
    Index documents from a file or directory into the vector store with batching.
    
    Args:
        file_path: Path to the document file or directory
        vector_store: Vector store instance
        batch_size: Number of documents to index per batch (default: 10)
        is_directory: If True, load all supported files from directory
        
    Returns:
        List of document IDs
        
    Raises:
        Exception: If indexing fails
    """
    try:
        logger.info(f"Starting document indexing from {file_path}")
        
        # Load documents based on type
        if is_directory:
            docs = load_documents_from_directory(file_path)
        else:
            docs = load_document(file_path)
        
        # Split documents into chunks
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
        description='Index documents (PDF, TXT) into Qdrant vector database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index a single PDF file
  python agent/index_docs.py path/to/document.pdf
  
  # Index a single text file
  python agent/index_docs.py path/to/document.txt
  
  # Index all documents in a directory
  python agent/index_docs.py path/to/documents/ --directory
  
  # Index with custom batch size
  python agent/index_docs.py path/to/document.pdf --batch-size 5
  
  # List all indexed documents
  python agent/index_docs.py --list
        """
    )
    parser.add_argument(
        'path',
        nargs='?',
        help='Path to the document file or directory'
    )
    parser.add_argument(
        '--directory',
        action='store_true',
        help='Treat path as a directory and index all supported files (PDF, TXT)'
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
        help='List all indexed documents and their collections'
    )
    parser.add_argument(
        '--reindex',
        action='store_true',
        help='Force reindexing even if file was previously indexed'
    )
    
    args = parser.parse_args()
    
    # Initialize mapper
    mapper = URLCollectionMapper()
    
    # Handle list command
    if args.list:
        mappings = mapper.list_all_mappings()
        if not mappings:
            print("No documents have been indexed yet.")
            return
        
        print("\n📚 Indexed Documents and Collections:")
        print("=" * 80)
        for path, info in mappings.items():
            print(f"\nPath: {path}")
            print(f"  Collection: {info['collection_name']}")
            print(f"  Documents: {info['document_count']}")
            print(f"  Created: {info['created_at']}")
            print(f"  Last Indexed: {info['last_indexed'] or 'Never'}")
        print("=" * 80)
        return
    
    # Require path if not listing
    if not args.path:
        parser.print_help()
        sys.exit(1)
    
    file_path = args.path
    
    try:
        # Validate path exists
        path = Path(file_path)
        if not path.exists():
            logger.error(f"Path does not exist: {file_path}")
            sys.exit(1)
        
        # Check if it's a directory or file
        if args.directory and not path.is_dir():
            logger.error(f"--directory flag used but path is not a directory: {file_path}")
            sys.exit(1)
        
        if not args.directory and path.is_dir():
            logger.error(f"Path is a directory. Use --directory flag to index all files.")
            sys.exit(1)
        
        # Get or create collection for this path
        collection_name, is_existing = mapper.get_collection_name(file_path)
        
        if is_existing and not args.reindex:
            logger.info(f"Path '{file_path}' was previously indexed in collection '{collection_name}'")
            response = input("Do you want to reindex? This will add new documents. (y/N): ")
            if response.lower() != 'y':
                logger.info("Indexing cancelled.")
                return
        
        logger.info(f"Using collection: {collection_name}")
        
        # Initialize components with the collection name
        _, _, vector_store = initialize_components(collection_name)
        
        # Index documents from file or directory
        doc_ids = index_documents(
            file_path,
            vector_store,
            batch_size=args.batch_size,
            is_directory=args.directory
        )
        
        # Update mapper with indexing info
        mapper.update_indexing_info(file_path, len(doc_ids))
        
        logger.info(f"✅ Indexing completed successfully!")
        logger.info(f"   Path: {file_path}")
        logger.info(f"   Type: {'Directory' if args.directory else 'File'}")
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