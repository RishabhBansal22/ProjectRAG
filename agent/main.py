"""Main RAG agent application."""
import logging
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain.agents import create_agent
from tools.retrival import retrieve_context, retrieval_service
from lang_comps.components import ChatGemini
from config import config
from url_mapper import URLCollectionMapper
from agent.index_docs import initialize_components, index_documents

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_rag_agent():
    """
    Create and configure the RAG agent with retrieval tools.
    
    Returns:
        Configured agent instance
    """
    try:
        # Validate configuration
        config.validate()
        
        # Initialize chat model
        chat_client = ChatGemini(
            api_key=config.GOOGLE_API_KEY,
            model=config.CHAT_MODEL
        )
        model = chat_client.get_client()
        
        # Set up tools
        tools = [retrieve_context]
        
        # Define system prompt
        prompt = (
            "You are a helpful AI assistant with access to a document retrieval tool. "
            "Use the tool to retrieve relevant context from indexed documents to help answer user queries. "
            "Always cite the sources you use and provide accurate, contextual answers based on the retrieved information. "
            "If you cannot find relevant information, acknowledge this to the user."
        )
        
        # Create agent
        agent = create_agent(model, tools, system_prompt=prompt)
        
        logger.info("Successfully created RAG agent")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise


def run_agent_query(agent, query: str, collection_name: str):
    """
    Run a query through the RAG agent.
    
    Args:
        agent: The agent instance
        query: User query string
        collection_name: Collection to search in
    """
    try:
        logger.info(f"Processing query in collection '{collection_name}': {query}")
        
        # Set the collection for this query
        retrieval_service.set_active_collection(collection_name)
        
        # Stream agent responses
        for event in agent.stream(
            {"messages": [{"role": "user", "content": query}]},
            stream_mode="values",
        ):
            event["messages"][-1].pretty_print()
            
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise


def ensure_collection_ready(file_path: str) -> str:
    """
    Ensure collection exists for file/directory, indexing if necessary.
    
    Args:
        file_path: Path to file or directory to index/retrieve
        
    Returns:
        Collection name to use
    """
    mapper = URLCollectionMapper()
    collection_name, is_existing = mapper.get_collection_name(file_path)
    
    if is_existing:
        logger.info(f"✅ Found existing collection for path: {collection_name}")
        print(f"\n✅ Using existing collection: {collection_name}")
        
        # Get document count
        mapping_info = mapper.mappings.get(file_path, {})
        doc_count = mapping_info.get('document_count', 'unknown')
        last_indexed = mapping_info.get('last_indexed', 'unknown')
        print(f"   Documents: {doc_count}")
        print(f"   Last indexed: {last_indexed}")
        
        return collection_name
    
    # Need to index this path
    logger.info(f"📥 Collection not found. Indexing path: {file_path}")
    print(f"\n📥 This path hasn't been indexed yet. Indexing now...")
    print(f"   Collection: {collection_name}")
    
    try:
        # Validate path exists
        from pathlib import Path
        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"Path does not exist: {file_path}")
        
        is_directory = path.is_dir()
        
        # Initialize components
        _, _, vector_store = initialize_components(collection_name)
        
        # Index documents
        doc_ids = index_documents(
            file_path, 
            vector_store,
            batch_size=config.BATCH_SIZE,
            is_directory=is_directory
        )
        
        # Update mapper
        mapper.update_indexing_info(file_path, len(doc_ids))
        
        print(f"\n✅ Indexing completed! {len(doc_ids)} documents indexed.")
        logger.info(f"Successfully indexed {len(doc_ids)} documents")
        
        return collection_name
        
    except Exception as e:
        logger.error(f"Failed to index path: {e}")
        print(f"\n❌ Failed to index path: {e}")
        raise


def main():
    """Main function to run the RAG agent."""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='RAG Agent - Chat with your indexed documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start chat session with a document
  python agent/main.py documents/sample.txt
  
  # Start chat with a PDF
  python agent/main.py documents/research.pdf
  
  # Direct query
  python agent/main.py documents/sample.txt --query "What is this about?"
  
  # Chat with all documents in a directory
  python agent/main.py documents/ --query "Summarize the content"
        """
    )
    parser.add_argument(
        'path',
        help='Path to the document file or directory to chat about'
    )
    parser.add_argument(
        '--query',
        '-q',
        type=str,
        help='Single query to ask (otherwise starts interactive session)'
    )
    
    args = parser.parse_args()
    file_path = args.path
    
    try:
        print("=" * 80)
        print("🤖 RAG Agent - Document Q&A System")
        print("=" * 80)
        print(f"\n📄 Document: {file_path}")
        
        # Validate configuration
        config.validate()
        
        # Validate path exists
        from pathlib import Path
        path = Path(file_path)
        if not path.exists():
            print(f"\n❌ Error: Path does not exist: {file_path}")
            print("Please provide a valid file or directory path.")
            sys.exit(1)
        
        # Ensure collection is ready (index if needed)
        collection_name = ensure_collection_ready(file_path)
        
        # Create agent
        print("\n🔧 Initializing agent...")
        agent = create_rag_agent()
        
        # Single query mode
        if args.query:
            query = args.query
            print(f"\n❓ Query: {query}")
            print("-" * 80)
            run_agent_query(agent, query, collection_name)
            return
        
        # Interactive mode
        print("\n" + "=" * 80)
        print("💬 Interactive Chat Mode")
        print("=" * 80)
        print("Type your questions below. Type 'quit', 'exit', or 'q' to stop.")
        print("-" * 80)
        
        while True:
            try:
                query = input("\n❓ You: ").strip()
                
                if not query:
                    continue
                    
                if query.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                print("\n🤖 Agent:")
                print("-" * 80)
                run_agent_query(agent, query, collection_name)
                print("-" * 80)
                
            except KeyboardInterrupt:
                print("\n\n� Chat session ended.")
                break
        
    except KeyboardInterrupt:
        print("\n\n👋 Agent stopped by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application failed: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
