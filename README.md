# RAG-Based LangChain Agent

A production-ready Retrieval-Augmented Generation (RAG) system built with LangChain, Google Gemini, and Qdrant vector database. This agent can index local documents (PDF and TXT files) and answer questions by retrieving relevant context from the indexed knowledge base.

## ✨ Key Features

- � **Document Indexing**: Load and index PDF and TXT documents into a vector database
- 🤖 **Intelligent Agent**: LangChain agent with RAG capabilities using Google Gemini
- 🔍 **Semantic Search**: Efficient similarity search using Qdrant vector database
- 📁 **Directory Support**: Index entire directories of documents at once
- ⚙️ **Configurable**: Centralized configuration management
- 📝 **Comprehensive Logging**: Detailed logging for debugging and monitoring
- 🛡️ **Error Handling**: Robust error handling throughout the application
- 🎯 **Type Hints**: Full type annotations for better code quality

## 🏗️ Architecture

```
rag-project/
├── documents/            # Place your documents here
│   └── sample.txt       # Sample text file
├── agent/
│   ├── document.py      # Document loading (PDF, TXT) and text splitting
│   ├── index_docs.py    # Document indexing pipeline
│   └── main.py         # Main RAG agent application
├── lang_comps/
│   └── components.py    # LangChain components (chat, embeddings, vector store)
├── qdrant/
│   └── client.py       # Qdrant client wrapper
├── tools/
│   └── retrival.py     # Retrieval tool for the agent
├── config.py           # Centralized configuration
└── DOCUMENT_SYSTEM.md  # Detailed documentation for document system
```

## 📋 Prerequisites

- Python 3.10+
- Google API key (for Gemini models)
- Qdrant cloud account or local instance

## 🚀 Installation

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

## 📚 Usage

### 1. Prepare Your Documents

Place your PDF or TXT files in the `documents/` directory:

```bash
documents/
├── sample.txt
├── research_paper.pdf
└── notes.txt
```

### 2. Index Documents

**Index a single file**:
```bash
# Index a text file
uv run agent/index_docs.py documents/sample.txt

# Index a PDF file
uv run agent/index_docs.py documents/research_paper.pdf
```

**Index all documents in a directory**:
```bash
uv run agent/index_docs.py documents/ --directory
```

**List all indexed documents**:
```bash
uv run agent/index_docs.py --list
```

### 3. Run the RAG Agent

Once documents are indexed, run the agent:

```bash
uv run agent/main.py
```

The agent will:
- Initialize with the configured Gemini model
- Use the retrieval tool to search indexed documents
- Answer queries based on retrieved context

### 4. Test Retrieval

Test document retrieval with sample queries:

```bash
uv run test_retrieval.py
```

## 📖 Supported File Types

- **PDF files** (.pdf) - Using LangChain's PyPDFLoader
- **Text files** (.txt) - Using LangChain's TextLoader

## ⚙️ Configuration

All configuration is managed in `config.py`. You can customize:

- **Model Settings**: Chat and embedding models
- **Vector Store**: Collection name, distance metric
- **Document Processing**: Chunk size and overlap
  - `CHUNK_SIZE = 1000` (characters per chunk)
  - `CHUNK_OVERLAP = 200` (overlap between chunks)
- **Retrieval**: Number of results to retrieve (top-k)
- **Batch Size**: Documents processed per batch during indexing

Environment variables in `.env` override defaults in `config.py`.

## 🔧 Project Components

### Document Processing (`agent/document.py`)
- `load_document()`: Loads single PDF or TXT files
- `load_documents_from_directory()`: Loads all supported files from a directory
- `split_documents()`: Splits documents into chunks for indexing

### Indexing Pipeline (`agent/index_docs.py`)
- `initialize_components()`: Sets up embeddings, vector store, and database
- `index_documents()`: Indexes documents from files or directories
- Supports batch processing for better performance
- Multi-threaded directory loading

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

## 🐛 Troubleshooting

### "0 documents indexed" Issue
**Cause**: Document content is empty or not being loaded correctly

**Solutions**:
1. **Check file content**: Ensure PDF files contain text (not just images)
2. **Check file encoding**: For TXT files, ensure UTF-8 encoding
3. **Use directory mode**: `uv run agent/index_docs.py documents/ --directory`

### Collection Not Found Error
```
ValueError: Collection 'rag_documents' not found
```
**Solution**: Run `uv run agent/index_docs.py documents/sample.txt` to create and populate the collection.

### API Key Errors
```
ValueError: Missing required environment variables: GOOGLE_API_KEY
```
**Solution**: Ensure your `.env` file has all required keys set.

### File Not Found
```
ValueError: File not found: documents/myfile.pdf
```
**Solution**: Check the file path and ensure the file exists.

## 📊 Performance Optimization

- **Batch Processing**: Documents are indexed in configurable batches (default: 10)
- **Multi-threading**: Directory loading uses multiple threads
- **Progress Indicators**: Real-time feedback during directory indexing
- **Retry Logic**: Automatic retry with exponential backoff for failed batches

## 🎯 Best Practices

1. **Always index documents before running the agent**
2. **Keep your API keys secure** - never commit `.env` files
3. **Monitor token usage** - embedding and chat API calls consume tokens
4. **Adjust chunk size** based on your document type and use case
5. **Use appropriate top-k values** - balance between context and relevance
6. **Organize documents** - Use descriptive filenames and directory structure

## 🔄 Migration from Web-Based System

The system has been updated from web-based to document-based:

| Feature | Old (Web) | New (Documents) |
|---------|-----------|-----------------|
| Input | URLs | File paths |
| Supported | HTML | PDF, TXT |
| Loader | WebBaseLoader | PyPDFLoader, TextLoader |
| Filtering | BeautifulSoup | Direct content |
| Issues | Anti-bot protection | Local file access |

## 📚 Documentation

- **[DOCUMENT_SYSTEM.md](DOCUMENT_SYSTEM.md)** - Comprehensive guide to the document system
- **[SIMPLE_WORKFLOW.md](SIMPLE_WORKFLOW.md)** - Quick start workflow

## 🚧 Future Enhancements

- [ ] Support for more document formats (DOCX, Markdown, CSV)
- [ ] OCR support for scanned PDFs
- [ ] Conversation memory
- [ ] Multiple vector store backends
- [ ] Web interface
- [ ] API endpoints
- [ ] Advanced query preprocessing
- [ ] Result caching

## 📄 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]

## 💬 Support

For issues and questions, please open an issue in the repository.

---

**Note**: For detailed information about the document loading system, see [DOCUMENT_SYSTEM.md](DOCUMENT_SYSTEM.md).
