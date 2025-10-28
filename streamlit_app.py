"""Streamlit frontend interface for RAG Agent."""
import streamlit as st
import logging
import sys
from pathlib import Path
from typing import Optional
import tempfile
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agent.main import create_rag_agent, ensure_collection_ready
from agent.index_docs import initialize_components, index_documents
from tools.retrival import retrieval_service
from url_mapper import URLCollectionMapper
from config import config

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose logging from httpx and other libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("tools.retrival").setLevel(logging.WARNING)
logging.getLogger("agent").setLevel(logging.WARNING)

# Page configuration
st.set_page_config(
    page_title="RAG Agent - Document Q&A",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .collection-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)


def get_friendly_collection_name(collection_name: str) -> str:
    """
    Extract a friendly display name from collection name.
    
    Args:
        collection_name: The full collection name (e.g., rag_myfile_20250128_143000_abc123)
        
    Returns:
        A user-friendly display name
    """
    mapper = URLCollectionMapper()
    
    # Try to find the original path/filename
    original_path = mapper.get_path_by_collection(collection_name)
    if original_path:
        return Path(original_path).name
    
    # Fallback: try to extract filename from collection name
    # Format is typically: rag_{filename}_{timestamp}_{hash}
    parts = collection_name.split('_')
    if len(parts) >= 2 and parts[0] == 'rag':
        # Extract the filename part (between 'rag' and timestamp/hash)
        # Assuming timestamp is 8 digits + 6 digits pattern
        filename_parts = []
        for i, part in enumerate(parts[1:], 1):
            # Stop if we hit what looks like a timestamp (8 digits)
            if part.isdigit() and len(part) == 8:
                break
            filename_parts.append(part)
        
        if filename_parts:
            return '_'.join(filename_parts)
    
    # Ultimate fallback: return the collection name as-is
    return collection_name


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "active_collection" not in st.session_state:
        st.session_state.active_collection = None
    if "indexed_paths" not in st.session_state:
        st.session_state.indexed_paths = {}
    if "messages" not in st.session_state:
        st.session_state.messages = []


def get_or_create_agent():
    """Get or create the RAG agent (cached in session state)."""
    if st.session_state.agent is None:
        try:
            with st.spinner("Initializing RAG agent..."):
                st.session_state.agent = create_rag_agent()
                logger.info("RAG agent initialized successfully")
        except Exception as e:
            st.error(f"❌ Failed to initialize agent: {str(e)}")
            logger.error(f"Agent initialization failed: {e}")
            raise
    return st.session_state.agent


def index_uploaded_file(uploaded_file, file_path: str) -> Optional[str]:
    """
    Index an uploaded file and return the collection name.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        file_path: Path where file is temporarily saved
        
    Returns:
        Collection name if successful, None otherwise
    """
    try:
        # Get or create collection name
        mapper = URLCollectionMapper()
        collection_name, is_existing = mapper.get_collection_name(file_path)
        
        if is_existing:
            st.info(f"📚 File already indexed in collection: **{collection_name}**")
            mapping_info = mapper.mappings.get(file_path, {})
            doc_count = mapping_info.get('document_count', 'unknown')
            st.write(f"- Documents: {doc_count}")
            st.write(f"- Last indexed: {mapping_info.get('last_indexed', 'unknown')}")
            return collection_name
        
        # Initialize components
        with st.spinner(f"Indexing {uploaded_file.name}..."):
            _, _, vector_store = initialize_components(collection_name)
            
            # Index the document
            doc_ids = index_documents(
                file_path,
                vector_store,
                batch_size=config.BATCH_SIZE,
                is_directory=False
            )
            
            # Update mapper
            mapper.update_indexing_info(file_path, len(doc_ids))
            
            st.success(f"✅ Successfully indexed {len(doc_ids)} document chunks!")
            logger.info(f"Indexed {uploaded_file.name}: {len(doc_ids)} chunks in {collection_name}")
            
        return collection_name
        
    except Exception as e:
        st.error(f"❌ Failed to index file: {str(e)}")
        logger.error(f"File indexing failed: {e}")
        return None


def display_collections_sidebar():
    """Display indexed collections in the sidebar."""
    st.sidebar.header("📚 Indexed Collections")
    
    mapper = URLCollectionMapper()
    mappings = mapper.list_all_mappings()
    
    if not mappings:
        st.sidebar.info("No documents indexed yet. Upload a file to get started!")
        return
    
    for idx, (path, info) in enumerate(mappings.items()):
        collection_name = info['collection_name']
        doc_count = info['document_count']
        
        # Extract a clean filename for display
        filename = Path(path).name
        file_stem = Path(path).stem  # filename without extension
        
        # Display collection info with clear filename
        with st.sidebar.expander(f"📄 {filename}", expanded=False):
            st.write(f"**File:** {filename}")
            st.write(f"**Chunks:** {doc_count}")
            st.write(f"**Indexed:** {info.get('last_indexed', 'N/A')[:10]}")
            
            # Button to activate collection
            if st.button(f"📂 Select Document", key=f"use_{idx}", type="primary"):
                st.session_state.active_collection = collection_name
                retrieval_service.set_active_collection(collection_name)
                st.success(f"✅ Now chatting with: **{filename}**")
                st.rerun()
    
    # Display active collection with friendly name
    if st.session_state.active_collection:
        active_friendly_name = get_friendly_collection_name(st.session_state.active_collection)
        st.sidebar.success(f"✅ Active: **{active_friendly_name}**")
    else:
        st.sidebar.warning("⚠️ No document selected")


def handle_file_upload():
    """Handle file upload section."""
    st.header("📁 Upload Document")
    
    uploaded_file = st.file_uploader(
        "Choose a file (PDF or TXT)",
        type=['pdf', 'txt'],
        help="Upload a document to index it into the vector database"
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**Filename:** {uploaded_file.name}")
            st.write(f"**Size:** {uploaded_file.size / 1024:.2f} KB")
        
        with col2:
            if st.button("📥 Index Document", type="primary"):
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                try:
                    # Index the file
                    collection_name = index_uploaded_file(uploaded_file, tmp_path)
                    
                    if collection_name:
                        # Set as active collection
                        st.session_state.active_collection = collection_name
                        retrieval_service.set_active_collection(collection_name)
                        st.session_state.indexed_paths[tmp_path] = collection_name
                        st.rerun()
                        
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass


def run_chat_query(query: str):
    """
    Run a chat query through the RAG agent.
    
    Args:
        query: User's question
    """
    if not st.session_state.active_collection:
        st.error("⚠️ Please select or upload a document first!")
        return
    
    try:
        # Get agent
        agent = get_or_create_agent()
        
        # Set active collection
        retrieval_service.set_active_collection(st.session_state.active_collection)
        
        # Add user message to conversation history
        st.session_state.conversation_history.append({"role": "user", "content": query})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(query)
        
        # Display assistant response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            
            # Show a spinner while processing
            with st.spinner("🤔 Thinking..."):
                # Stream agent responses - only show AI messages, not tool calls
                for event in agent.stream(
                    {"messages": st.session_state.conversation_history},
                    stream_mode="values",
                ):
                    last_message = event["messages"][-1]
                    
                    # Only process AI messages, skip tool calls and other intermediate messages
                    if hasattr(last_message, 'type') and last_message.type == 'ai':
                        # Handle different message types
                        if hasattr(last_message, 'content'):
                            if isinstance(last_message.content, str):
                                full_response = last_message.content
                            elif isinstance(last_message.content, list):
                                # Handle content blocks
                                full_response = ""
                                for block in last_message.content:
                                    if isinstance(block, dict) and 'text' in block:
                                        full_response += block['text']
                                    elif isinstance(block, str):
                                        full_response += block
            
            # Display the final response after processing is complete
            if full_response:
                response_placeholder.markdown(full_response)
            
            # Add assistant response to conversation history
            # Convert LangChain message to dictionary format
            assistant_message = {
                "role": "assistant",
                "content": full_response
            }
            st.session_state.conversation_history.append(assistant_message)
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        logger.error(f"Query processing error: {e}")


def display_chat_interface():
    """Display the chat interface."""
    st.header("💬 Chat with Your Documents")
    
    # Check if a collection is active
    if not st.session_state.active_collection:
        st.info("👆 Please upload a document or select an indexed collection from the sidebar to start chatting.")
        return
    
    # Display friendly name instead of collection name
    friendly_name = get_friendly_collection_name(st.session_state.active_collection)
    st.success(f"🎯 Chatting with: **{friendly_name}**")
    
    # Display chat history
    for message in st.session_state.conversation_history:
        # Handle both dictionary and LangChain message objects
        if isinstance(message, dict):
            role = message.get("role", "assistant")
            content = message.get("content", "")
        else:
            # LangChain message object
            role = getattr(message, 'type', 'assistant')
            if role == 'ai':
                role = 'assistant'
            elif role == 'human':
                role = 'user'
            content = getattr(message, 'content', '')
        
        # Handle different content types
        if isinstance(content, str):
            display_content = content
        elif isinstance(content, list):
            # Handle content blocks
            display_content = ""
            for block in content:
                if isinstance(block, dict) and 'text' in block:
                    display_content += block['text']
                elif isinstance(block, str):
                    display_content += block
        else:
            display_content = str(content)
        
        with st.chat_message(role):
            st.markdown(display_content)
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        run_chat_query(prompt)


def display_url_collections_db():
    """Display the URL collections database in a dedicated section."""
    st.header("🗄️ Collections Database")
    
    mapper = URLCollectionMapper()
    mappings = mapper.list_all_mappings()
    
    if not mappings:
        st.info("No collections in database yet.")
        return
    
    # Create a table view
    st.write(f"**Total Collections:** {len(mappings)}")
    
    for path, info in mappings.items():
        with st.expander(f"📄 {Path(path).name}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Path:** `{path}`")
                st.write(f"**Collection:** `{info['collection_name']}`")
                st.write(f"**Documents:** {info['document_count']}")
                st.write(f"**Created:** {info['created_at'][:19]}")
                st.write(f"**Last Indexed:** {info.get('last_indexed', 'N/A')[:19]}")
            
            with col2:
                if st.button("🎯 Activate", key=f"activate_{info['collection_name']}"):
                    st.session_state.active_collection = info['collection_name']
                    retrieval_service.set_active_collection(info['collection_name'])
                    st.success("✅ Collection activated!")
                    st.rerun()
                
                if st.button("🗑️ Delete", key=f"delete_{info['collection_name']}"):
                    if mapper.delete_mapping(path):
                        st.success("✅ Collection mapping deleted!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete collection")


def main():
    """Main Streamlit application."""
    # Initialize session state
    initialize_session_state()
    
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        st.error(f"❌ Configuration Error: {str(e)}")
        st.info("Please ensure all required environment variables are set in your .env file.")
        st.stop()
    
    # Header
    st.markdown('<div class="main-header">🤖 RAG Agent - Document Q&A System</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("🎛️ Control Panel")
        
        # Clear conversation button
        if st.button("🔄 Clear Conversation", use_container_width=True):
            st.session_state.conversation_history = []
            st.session_state.messages = []
            st.success("✅ Conversation cleared!")
            st.rerun()
        
        st.divider()
        
        # Display collections
        display_collections_sidebar()
        
        st.divider()
        
        # Settings
        st.header("⚙️ Settings")
        st.write(f"**Model:** {config.CHAT_MODEL}")
        st.write(f"**Embedding:** {config.EMBEDDING_MODEL}")
        st.write(f"**Top K Results:** {config.TOP_K_RESULTS}")
    
    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "📁 Upload", "🗄️ Database"])
    
    with tab1:
        display_chat_interface()
    
    with tab2:
        handle_file_upload()
    
    with tab3:
        display_url_collections_db()


if __name__ == "__main__":
    main()
