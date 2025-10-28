"""URL and collection mapping manager."""
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class URLCollectionMapper:
    """Manages mapping between URLs and their collection names."""
    
    def __init__(self, mapping_file: str = "url_collections.json"):
        """
        Initialize the URL-collection mapper.
        
        Args:
            mapping_file: Path to the JSON file storing URL-collection mappings
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
    
    def _generate_collection_name(self, url: str) -> str:
        """
        Generate a unique, valid collection name from URL.
        
        Args:
            url: The URL to generate a collection name for
            
        Returns:
            A valid Qdrant collection name
        """
        # Create a hash of the URL
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        
        # Extract domain or path segment for readability
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace('.', '_').replace('-', '_')
        
        # Create collection name: domain_hash
        # Qdrant collection names must start with letter, contain only letters, numbers, underscore
        collection_name = f"rag_{domain}_{url_hash}"
        
        # Ensure it's valid (max 255 chars, only allowed characters)
        collection_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in collection_name)
        collection_name = collection_name[:255]  # Qdrant max length
        
        return collection_name
    
    def get_collection_name(self, url: str) -> tuple[str, bool]:
        """
        Get the collection name for a URL, creating a new one if needed.
        
        Args:
            url: The URL to get/create a collection for
            
        Returns:
            Tuple of (collection_name, is_existing)
            - collection_name: The collection name to use
            - is_existing: True if collection already exists for this URL
        """
        if url in self.mappings:
            collection_name = self.mappings[url]['collection_name']
            logger.info(f"Found existing collection for URL: {collection_name}")
            return collection_name, True
        
        # Generate new collection name
        collection_name = self._generate_collection_name(url)
        
        # Store mapping
        self.mappings[url] = {
            'collection_name': collection_name,
            'created_at': datetime.now().isoformat(),
            'last_indexed': None,
            'document_count': 0
        }
        self._save_mappings()
        
        logger.info(f"Created new collection mapping: {url} -> {collection_name}")
        return collection_name, False
    
    def update_indexing_info(self, url: str, document_count: int) -> None:
        """
        Update indexing information for a URL.
        
        Args:
            url: The URL that was indexed
            document_count: Number of documents indexed
        """
        if url in self.mappings:
            self.mappings[url]['last_indexed'] = datetime.now().isoformat()
            self.mappings[url]['document_count'] = document_count
            self._save_mappings()
    
    def list_all_mappings(self) -> Dict[str, dict]:
        """Get all URL-collection mappings."""
        return self.mappings.copy()
    
    def get_url_by_collection(self, collection_name: str) -> Optional[str]:
        """
        Get the URL associated with a collection name.
        
        Args:
            collection_name: The collection name to search for
            
        Returns:
            URL if found, None otherwise
        """
        for url, info in self.mappings.items():
            if info['collection_name'] == collection_name:
                return url
        return None
    
    def delete_mapping(self, url: str) -> bool:
        """
        Delete a URL-collection mapping.
        
        Args:
            url: The URL to remove
            
        Returns:
            True if deleted, False if not found
        """
        if url in self.mappings:
            del self.mappings[url]
            self._save_mappings()
            logger.info(f"Deleted mapping for URL: {url}")
            return True
        return False
