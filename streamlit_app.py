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
    /* Main header */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Chat message styling */
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.8rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Chat input styling */
    .stChatInputContainer {
        border-top: 2px solid #e0e0e0;
        padding-top: 1rem;
        margin-top: 1rem;
    }
    
    /* Collection card */
    .collection-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
    }
    
    /* Button hover effects */
    .stButton button {
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 500;
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
        # Use original filename as the key, not the temp path
        original_filename = uploaded_file.name
        
        # Get or create collection name using original filename
        mapper = URLCollectionMapper()
        collection_name, is_existing = mapper.get_collection_name(original_filename)
        
        if is_existing:
            st.info(f"📚 File already indexed: **{original_filename}**")
            mapping_info = mapper.mappings.get(original_filename, {})
            doc_count = mapping_info.get('document_count', 'unknown')
            st.write(f"- Chunks: {doc_count}")
            st.write(f"- Last indexed: {mapping_info.get('last_indexed', 'unknown')}")
            return collection_name
        
        # Initialize components
        with st.spinner(f"Indexing {original_filename}..."):
            _, _, vector_store = initialize_components(collection_name)
            
            # Index the document using the temp file path
            doc_ids = index_documents(
                file_path,
                vector_store,
                batch_size=config.BATCH_SIZE,
                is_directory=False
            )
            
            # Update mapper with original filename
            mapper.update_indexing_info(original_filename, len(doc_ids))
            
            st.success(f"✅ Successfully indexed {len(doc_ids)} document chunks!")
            logger.info(f"Indexed {original_filename}: {len(doc_ids)} chunks in {collection_name}")
            
        return collection_name
        
    except Exception as e:
        st.error(f"❌ Failed to index file: {str(e)}")
        logger.error(f"File indexing failed: {e}")
        return None


def display_collections_sidebar():
    """Display indexed collections in the sidebar."""
    st.sidebar.header("📚 My Documents")
    
    mapper = URLCollectionMapper()
    mappings = mapper.list_all_mappings()
    
    if not mappings:
        st.sidebar.info("📝 No documents yet.\n\nUpload one to get started!")
        return
    
    st.sidebar.caption(f"Total: {len(mappings)} document(s)")
    
    for idx, (path, info) in enumerate(mappings.items()):
        collection_name = info['collection_name']
        doc_count = info['document_count']
        
        # Extract a clean filename for display
        filename = Path(path).name
        file_stem = Path(path).stem  # filename without extension
        
        # Check if this is the active collection
        is_active = st.session_state.active_collection == collection_name
        
        # Display collection info with clear filename
        with st.sidebar.expander(f"{'✅ ' if is_active else '📄 '}{filename}", expanded=is_active):
            st.markdown(f"**📄 File:** {filename}")
            st.markdown(f"**🔢 Chunks:** {doc_count}")
            st.markdown(f"**📅 Indexed:** {info.get('last_indexed', 'N/A')[:10]}")
            
            # Button to activate collection
            if not is_active:
                if st.button("📂 Chat with this", key=f"use_{idx}", type="primary", use_container_width=True):
                    st.session_state.active_collection = collection_name
                    retrieval_service.set_active_collection(collection_name)
                    st.rerun()
            else:
                st.success("Currently active")
    
    st.sidebar.divider()
    
    # Display active collection status
    if st.session_state.active_collection:
        active_friendly_name = get_friendly_collection_name(st.session_state.active_collection)
        st.sidebar.success(f"💬 Active: **{active_friendly_name}**")
    else:
        st.sidebar.info("💡 Select a document to start chatting")


def handle_file_upload():
    """Handle file upload section."""
    # Styled header
    st.markdown("""
    <div style="background-color: #f0f7ff; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
        <h3 style="margin: 0; color: #1f77b4;">📁 Upload Document</h3>
        <p style="margin: 0.5rem 0 0 0; color: #555;">Upload a PDF or TXT file to index and chat with it</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'txt'],
        help="Upload a document to index it into the vector database",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        # Display file info in a nice card
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #1f77b4; margin-bottom: 1rem;">
            <h4 style="margin: 0 0 0.5rem 0;">📄 {uploaded_file.name}</h4>
            <p style="margin: 0; color: #666;">Size: {uploaded_file.size / 1024:.2f} KB</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Center the button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📥 Index Document", type="primary", use_container_width=True):
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
    else:
        # Show instructions when no file is uploaded
        st.info("👆 Choose a file to get started")
        st.markdown("""
        ### 📋 Instructions
        1. Click the **Browse files** button above
        2. Select a PDF or TXT document
        3. Click **Index Document** to process it
        4. Start chatting in the **Chat** tab!
        """)


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
    # Check if a collection is active
    if not st.session_state.active_collection:
        st.info("👆 Please upload a document or select a document from the sidebar to start chatting.")
        st.markdown("### 🚀 Getting Started")
        st.markdown("""
        1. **Upload a document** in the 📁 Upload tab, or
        2. **Select an indexed document** from the sidebar
        3. Start asking questions about your documents!
        """)
        return
    
    # Display friendly name instead of collection name
    friendly_name = get_friendly_collection_name(st.session_state.active_collection)
    
    # Header with document info
    st.markdown(f"""
    <div style="background-color: #e8f4f8; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
        <h3 style="margin: 0; color: #1f77b4;">💬 Chat with Your Documents</h3>
        <p style="margin: 0.5rem 0 0 0; color: #555;">📄 Currently chatting with: <strong>{friendly_name}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat input at the top for better UX
    user_query = st.chat_input("Ask a question about your documents...", key="chat_input_top")
    
    # Container for chat messages
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        if not st.session_state.conversation_history:
            st.info("👋 Start a conversation! Ask me anything about the document.")
        else:
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
    
    # Process user query if submitted
    if user_query:
        run_chat_query(user_query)


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
