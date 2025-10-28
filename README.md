# RAG-Based LangChain Agent

A production-ready Retrieval-Augmented Generation (RAG) system built with LangChain, Google Gemini, and Qdrant vector database. This agent can index web documents and answer questions by retrieving relevant context from the indexed knowledge base.

## Features

- 🚀 **Document Indexing**: Load and index web documents into a vector database
- 🤖 **Intelligent Agent**: LangChain agent with RAG capabilities using Google Gemini
- 🔍 **Semantic Search**: Efficient similarity search using Qdrant vector database
- ⚙️ **Configurable**: Centralized configuration management
- 📝 **Comprehensive Logging**: Detailed logging for debugging and monitoring
- 🛡️ **Error Handling**: Robust error handling throughout the application
- 🎯 **Type Hints**: Full type annotations for better code quality

## Architecture

```
rag-project/
├── agent/
│   ├── document.py       # Document loading and text splitting
│   ├── index_docs.py     # Document indexing pipeline
│   └── main.py          # Main RAG agent application
├── lang_comps/
│   └── components.py     # LangChain components (chat, embeddings, vector store)
├── qdrant/
│   └── client.py        # Qdrant client wrapper
├── tools/
│   ├── __init__.py
│   └── retrival.py      # Retrieval tool for the agent
├── config.py            # Centralized configuration
├── pyproject.toml       # Project dependencies
├── .env.example         # Example environment variables
└── README.md           # This file
```

## Prerequisites

- Python 3.10+
- Google API key (for Gemini models)
- Qdrant cloud account or local instance

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd rag-project
   ```

2. **Install dependencies** (using uv or pip):
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -e .
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```env
   GOOGLE_API_KEY=your_google_api_key
   QDRANT_API_KEY=your_qdrant_api_key
   QDRANT_URL=your_qdrant_url
   ```

## Usage

### 1. Index Documents

First, index documents into the vector database:

```bash
uv run agent/index_docs.py
```

This will:
- Load a web document (default: LLM Agent blog post)
- Split it into chunks
- Create embeddings
- Store in Qdrant vector database

To index custom URLs, modify the `url` variable in `agent/index_docs.py` or extend the `main()` function.

### 2. Run the RAG Agent

Once documents are indexed, run the agent:

```bash
uv run agent/main.py
```

The agent will:
- Initialize with the configured Gemini model
- Use the retrieval tool to search indexed documents
- Answer queries based on retrieved context

### 3. Customize Queries

Edit `agent/main.py` to modify the query:

```python
query = "Your custom question here"
run_agent_query(agent, query)
```

## Configuration

All configuration is managed in `config.py`. You can customize:

- **Model Settings**: Chat and embedding models
- **Vector Store**: Collection name, distance metric
- **Document Processing**: Chunk size and overlap
- **Retrieval**: Number of results to retrieve (top-k)

Environment variables in `.env` override defaults in `config.py`.

## Project Components

### Document Processing (`agent/document.py`)
- `load_web_document()`: Loads web pages and extracts content
- `split_documents()`: Splits documents into chunks for indexing

### Indexing Pipeline (`agent/index_docs.py`)
- `initialize_components()`: Sets up embeddings, vector store, and database
- `index_documents()`: Indexes documents from URLs
- `main()`: Entry point for indexing

### RAG Agent (`agent/main.py`)
- `create_rag_agent()`: Creates the LangChain agent with tools
- `run_agent_query()`: Executes queries through the agent
- `main()`: Entry point for the agent

### LangChain Components (`lang_comps/components.py`)
- `ChatGemini`: Wrapper for Google Gemini chat model
- `GoogleEmbedding`: Wrapper for Google embedding model
- `VectorStore`: Wrapper for Qdrant vector store

### Retrieval Tool (`tools/retrival.py`)
- `RetrievalService`: Singleton service for managing retrieval
- `retrieve_context()`: LangChain tool for document retrieval

### Qdrant Client (`qdrant/client.py`)
- `QdrantClientWrapper`: Enhanced Qdrant client with collection management

## Error Handling

The project includes comprehensive error handling:
- Configuration validation
- API key validation
- Database connection errors
- Document loading failures
- Retrieval errors

All errors are logged with detailed messages for debugging.

## Logging

Logging is configured at the INFO level by default. Logs include:
- Component initialization
- Document processing progress
- Query execution
- Error details

To change log level, modify the `logging.basicConfig()` calls in the main scripts.

## Development

### Adding New Document Sources

Extend `agent/document.py` with new loaders:

```python
def load_pdf_document(file_path: str) -> List[Document]:
    """Load PDF documents."""
    # Implementation
    pass
```

### Adding New Tools

Create new tools in `tools/`:

```python
from langchain.tools import tool

@tool
def your_custom_tool(input: str) -> str:
    """Tool description."""
    # Implementation
    pass
```

Register in `agent/main.py`:

```python
tools = [retrieve_context, your_custom_tool]
```

### Customizing the Agent

Modify the system prompt in `agent/main.py` to change agent behavior:

```python
prompt = "Your custom system prompt here"
```

## Best Practices

1. **Always index documents before running the agent**
2. **Keep your API keys secure** - never commit `.env` files
3. **Monitor token usage** - embedding and chat API calls consume tokens
4. **Adjust chunk size** based on your document type and use case
5. **Use appropriate top-k values** - balance between context and relevance

## Troubleshooting

### Collection Not Found Error
```
ValueError: Collection 'rag_documents' not found
```
**Solution**: Run `uv run agent/index_docs.py` to create and populate the collection.

### API Key Errors
```
ValueError: Missing required environment variables: GOOGLE_API_KEY
```
**Solution**: Ensure your `.env` file has all required keys set.

### Import Errors
```
ModuleNotFoundError: No module named 'langchain'
```
**Solution**: Install dependencies with `uv sync` or `pip install -e .`

## Performance Optimization

- **Batch Indexing**: Index multiple documents in batches
- **Caching**: Implement embedding caching for frequently used queries
- **Async Operations**: Use async methods for concurrent operations
- **Collection Management**: Regularly optimize vector collections

## Future Enhancements

- [ ] Support for multiple document formats (PDF, DOCX, etc.)
- [ ] Batch document indexing
- [ ] Conversation memory
- [ ] Multiple vector store backends
- [ ] Web interface
- [ ] API endpoints
- [ ] Advanced query preprocessing
- [ ] Result caching

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues and questions, please open an issue in the repository.
