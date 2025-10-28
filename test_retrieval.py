"""Test script to query indexed documents."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from tools.retrival import retrieve_context, retrieval_service
from url_mapper import URLCollectionMapper
from config import config

def main():
    """Test document retrieval."""
    # Get the collection name for our sample document
    mapper = URLCollectionMapper()
    mappings = mapper.list_all_mappings()
    
    if not mappings:
        print("❌ No documents have been indexed yet.")
        print("Please run: uv run agent/index_docs.py documents/sample.txt")
        return
    
    # Use the first indexed document's collection
    path, info = next(iter(mappings.items()))
    collection_name = info['collection_name']
    
    print(f"📚 Testing retrieval from collection: {collection_name}")
    print(f"   Source: {path}")
    print("=" * 80)
    
    # Test queries
    test_queries = [
        "What is machine learning?",
        "Tell me about vector databases",
        "What is natural language processing?",
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 80)
        
        try:
            # Set active collection
            retrieval_service.set_active_collection(collection_name)
            
            # Retrieve relevant documents using the tool directly
            result = retrieve_context.invoke({"query": query})
            
            # Handle the result - it could be a tuple or just text
            if isinstance(result, tuple):
                results_text, results_docs = result
            else:
                results_text = result
                results_docs = []
            
            if results_docs:
                print(f"\nFound {len(results_docs)} relevant documents:")
                for i, doc in enumerate(results_docs, 1):
                    print(f"\nResult {i}:")
                    print(f"Content: {doc.page_content[:200]}...")
                    print(f"Source: {doc.metadata.get('source', 'N/A')}")
            else:
                print(f"\nResponse: {results_text[:500]}...")
        except Exception as e:
            print(f"Error during retrieval: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 80)

if __name__ == "__main__":
    main()
