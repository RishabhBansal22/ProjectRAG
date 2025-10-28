"""Document loading and processing utilities."""
import logging
from typing import List
import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def load_web_document(url: str) -> List[Document]:
    """
    Load a web document and extract relevant content.
    
    Args:
        url: URL of the web page to load
        
    Returns:
        List of Document objects
        
    Raises:
        ValueError: If URL is invalid
        Exception: If loading fails
    """
    if not url:
        raise ValueError("URL cannot be empty")
    
    try:
        # Only keep post title, headers, and content from the full HTML
        bs4_strainer = bs4.SoupStrainer(
            class_=("post-title", "post-header", "post-content")
        )
        loader = WebBaseLoader(
            web_paths=(url,),
            bs_kwargs={"parse_only": bs4_strainer},
        )
        docs = loader.load()
        logger.info(f"Successfully loaded document from {url}")
        return docs
    except Exception as e:
        logger.error(f"Failed to load document from {url}: {e}")
        raise


def split_documents(
    docs: List[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Document]:
    """
    Split documents into smaller chunks.
    
    Args:
        docs: List of documents to split
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        
    Returns:
        List of split Document objects
        
    Raises:
        ValueError: If parameters are invalid
    """
    if not docs:
        raise ValueError("Documents list cannot be empty")
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")
    if chunk_overlap < 0:
        raise ValueError("Chunk overlap cannot be negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("Chunk overlap must be less than chunk size")
    
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True,  # Track index in original document
        )
        all_splits = text_splitter.split_documents(docs)
        logger.info(f"Split {len(docs)} documents into {len(all_splits)} chunks")
        return all_splits
    except Exception as e:
        logger.error(f"Failed to split documents: {e}")
        raise
