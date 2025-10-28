"""URL and file path to collection mapping manager.

Note: This module is named url_mapper for backward compatibility,
but it now handles both URLs and file paths for the document-based system.
"""
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class URLCollectionMapper:
    """Manages mapping between file paths/URLs and their collection names."""
    
    def __init__(self, mapping_file: str = "url_collections.json"):
        """
        Initialize the path-collection mapper.
        
        Args:
            mapping_file: Path to the JSON file storing path-collection mappings
        """
        self.mapping_file = Path(mapping_file)
        self.mappings: Dict[str, dict] = self._load_mappings()
    
    def _load_mappings(self) -> Dict[str, dict]:
        """Load existing mappings from file."""
        if self.mapping_file.exists():
            try:
                with open(self.mapping_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load mappings from {self.mapping_file}: {e}")
                return {}
        return {}
    
    def _save_mappings(self) -> None:
        """Save mappings to file."""
        try:
            with open(self.mapping_file, 'w') as f:
                json.dump(self.mappings, f, indent=2)
            logger.info(f"Saved mappings to {self.mapping_file}")
        except Exception as e:
            logger.error(f"Failed to save mappings: {e}")
    
    def _generate_collection_name(self, path_or_url: str) -> str:
        """
        Generate a unique, valid collection name from file path or URL.
        
        Args:
            path_or_url: The file path or URL to generate a collection name for
            
        Returns:
            A valid Qdrant collection name
        """
        # Create a hash of the path/URL for uniqueness
        path_hash = hashlib.md5(path_or_url.encode()).hexdigest()[:8]
        
        # Try to extract a meaningful name from the path
        try:
            from pathlib import Path
            # Handle as file path
            path_obj = Path(path_or_url)
            # Get directory name or file stem for readability
            if path_obj.is_dir() or not path_obj.suffix:
                name_part = path_obj.name or "docs"
            else:
                name_part = path_obj.stem
            # Clean the name: replace special chars with underscores
            name_part = name_part.replace('.', '_').replace('-', '_').replace(' ', '_')
            # Limit length for readability
            name_part = name_part[:50]
        except Exception:
            # Fallback: use hash only if path parsing fails
            name_part = "document"
        
        # Add timestamp for better tracking (optional, but helps identify when indexed)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create collection name with format: rag_{filename}_{timestamp}_{hash}
        collection_name = f"rag_{name_part}_{timestamp}_{path_hash}"
        
        # Ensure it's valid (max 255 chars, only allowed characters)
        collection_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in collection_name)
        collection_name = collection_name[:255]  # Qdrant max length
        
        return collection_name
    
    def get_collection_name(self, path_or_url: str) -> tuple[str, bool]:
        """
        Get the collection name for a path/URL, creating a new one if needed.
        
        Args:
            path_or_url: The file path or URL to get/create a collection for
            
        Returns:
            Tuple of (collection_name, is_existing)
            - collection_name: The collection name to use
            - is_existing: True if collection already exists for this path/URL
        """
        if path_or_url in self.mappings:
            collection_name = self.mappings[path_or_url]['collection_name']
            logger.info(f"Found existing collection for path: {collection_name}")
            return collection_name, True
        
        # Generate new collection name
        collection_name = self._generate_collection_name(path_or_url)
        
        # Store mapping
        self.mappings[path_or_url] = {
            'collection_name': collection_name,
            'created_at': datetime.now().isoformat(),
            'last_indexed': None,
            'document_count': 0
        }
        self._save_mappings()
        
        logger.info(f"Created new collection mapping: {path_or_url} -> {collection_name}")
        return collection_name, False
    
    def update_indexing_info(self, path_or_url: str, document_count: int) -> None:
        """
        Update indexing information for a path/URL.
        
        Args:
            path_or_url: The path/URL that was indexed
            document_count: Number of documents indexed
        """
        if path_or_url in self.mappings:
            self.mappings[path_or_url]['last_indexed'] = datetime.now().isoformat()
            self.mappings[path_or_url]['document_count'] = document_count
            self._save_mappings()
    
    def list_all_mappings(self) -> Dict[str, dict]:
        """Get all path/URL-collection mappings."""
        return self.mappings.copy()
    
    def get_path_by_collection(self, collection_name: str) -> Optional[str]:
        """
        Get the path/URL associated with a collection name.
        
        Args:
            collection_name: The collection name to search for
            
        Returns:
            Path/URL if found, None otherwise
        """
        for path_or_url, info in self.mappings.items():
            if info['collection_name'] == collection_name:
                return path_or_url
        return None
    
    def delete_mapping(self, path_or_url: str) -> bool:
        """
        Delete a path/URL-collection mapping.
        
        Args:
            path_or_url: The path/URL to remove
            
        Returns:
            True if deleted, False if not found
        """
        if path_or_url in self.mappings:
            del self.mappings[path_or_url]
            self._save_mappings()
            logger.info(f"Deleted mapping for path: {path_or_url}")
            return True
        return False
