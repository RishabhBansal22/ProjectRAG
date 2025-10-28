"""Document loading and processing utilities."""
import logging
from typing import List
from pathlib import Path
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    DirectoryLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def load_document(file_path: str) -> List[Document]:
    """
    Load a document from a file (PDF or TXT).
    
    Args:
        file_path: Path to the document file (PDF or TXT)
        
    Returns:
        List of Document objects
        
    Raises:
        ValueError: If file path is invalid or file type not supported
        Exception: If loading fails
    """
    if not file_path:
        raise ValueError("File path cannot be empty")
    
    path = Path(file_path)
    if not path.exists():
        raise ValueError(f"File not found: {file_path}")
    
    file_extension = path.suffix.lower()
    
    try:
        if file_extension == '.pdf':
            logger.info(f"Loading PDF file: {file_path}")
            loader = PyPDFLoader(str(path))
        elif file_extension == '.txt':
            logger.info(f"Loading TXT file: {file_path}")
            loader = TextLoader(str(path))
        else:
            raise ValueError(
                f"Unsupported file type: {file_extension}. "
                "Supported types: .pdf, .txt"
            )
        
        docs = loader.load()
        logger.info(f"Successfully loaded {len(docs)} document(s) from {file_path}")
        return docs
    except Exception as e:
        logger.error(f"Failed to load document from {file_path}: {e}")
        raise


def load_documents_from_directory(
    directory_path: str,
    glob_pattern: str = "**/*",
    file_types: List[str] = None
) -> List[Document]:
    """
    Load multiple documents from a directory.
    
    Args:
        directory_path: Path to the directory containing documents
        glob_pattern: Glob pattern to match files (default: "**/*" for all files)
        file_types: List of file extensions to load (e.g., ['.pdf', '.txt'])
                   If None, loads both .pdf and .txt files
        
    Returns:
        List of Document objects
        
    Raises:
        ValueError: If directory path is invalid
        Exception: If loading fails
    """
    if not directory_path:
        raise ValueError("Directory path cannot be empty")
    
    path = Path(directory_path)
    if not path.exists():
        raise ValueError(f"Directory not found: {directory_path}")
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {directory_path}")
    
    if file_types is None:
        file_types = ['.pdf', '.txt']
    
    all_docs = []
    
    try:
        # Load each file type separately
        for file_type in file_types:
            if file_type == '.pdf':
                logger.info(f"Loading PDF files from {directory_path}")
                loader = DirectoryLoader(
                    str(path),
                    glob=f"{glob_pattern}.pdf",
                    loader_cls=PyPDFLoader,
                    show_progress=True,
                    use_multithreading=True
                )
            elif file_type == '.txt':
                logger.info(f"Loading TXT files from {directory_path}")
                loader = DirectoryLoader(
                    str(path),
                    glob=f"{glob_pattern}.txt",
                    loader_cls=TextLoader,
                    show_progress=True,
                    use_multithreading=True
                )
            else:
                logger.warning(f"Unsupported file type: {file_type}")
                continue
            
            docs = loader.load()
            all_docs.extend(docs)
            logger.info(f"Loaded {len(docs)} document(s) with extension {file_type}")
        
        logger.info(
            f"Successfully loaded {len(all_docs)} total document(s) "
            f"from {directory_path}"
        )
        return all_docs
    except Exception as e:
        logger.error(f"Failed to load documents from {directory_path}: {e}")
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
