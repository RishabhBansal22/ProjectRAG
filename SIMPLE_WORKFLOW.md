# 🚀 Simplified RAG Agent Workflow

## Overview

The RAG agent now has a **streamlined, URL-first workflow**. Every chat session starts with a URL, and the system automatically handles indexing if needed.

## How It Works

### Simple 3-Step Process

1. **Provide URL** → System checks if it's already indexed
2. **Auto-Index** → If new, automatically indexes the documents
3. **Start Chatting** → Ask questions about the content

No more separate indexing commands or collection management!

## Usage

### Quick Start

```bash
# Start chat with any URL
uv run agent/main.py "https://example.com/article"

# The system will:
# ✅ Check if URL is already indexed
# 📥 Index it automatically if needed
# 💬 Start interactive chat session
```

### Single Query Mode

```bash
# Ask a single question
uv run agent/main.py "https://example.com/article" --query "What is this about?"
```

### Using Quickstart Script

```bash
# Simplest way to get started
uv run quickstart.py

# You'll be prompted for:
# 1. URL to chat about
# 2. System handles rest automatically
```

## Examples

### Example 1: New URL (Auto-Index)

```bash
$ uv run agent/main.py "https://lilianweng.github.io/posts/2023-06-23-agent/"

================================================================================
🤖 RAG Agent - Document Q&A System
================================================================================

📄 URL: https://lilianweng.github.io/posts/2023-06-23-agent/

📥 This URL hasn't been indexed yet. Indexing now...
   Collection: rag_lilianweng_github_io_31d52fb4

[Indexing progress with batches...]

✅ Indexing completed! 63 documents indexed.

🔧 Initializing agent...

================================================================================
💬 Interactive Chat Mode
================================================================================
Type your questions below. Type 'quit', 'exit', or 'q' to stop.
--------------------------------------------------------------------------------

❓ You: What is Task Decomposition?

🤖 Agent:
--------------------------------------------------------------------------------
[Agent's response with retrieved context]
```

### Example 2: Previously Indexed URL

```bash
$ uv run agent/main.py "https://lilianweng.github.io/posts/2023-06-23-agent/"

================================================================================
🤖 RAG Agent - Document Q&A System
================================================================================

📄 URL: https://lilianweng.github.io/posts/2023-06-23-agent/

✅ Using existing collection: rag_lilianweng_github_io_31d52fb4
   Documents: 63
   Last indexed: 2025-10-28T11:53:11.624105

🔧 Initializing agent...

[Chat starts immediately - no indexing needed]
```

### Example 3: Direct Query

```bash
$ uv run agent/main.py "https://example.com" --query "Summarize this page"

================================================================================
🤖 RAG Agent - Document Q&A System
================================================================================

📄 URL: https://example.com

✅ Using existing collection: rag_example_com_abc12345
   Documents: 25
   Last indexed: 2025-10-28T10:00:00.123456

🔧 Initializing agent...

❓ Query: Summarize this page
--------------------------------------------------------------------------------
[Agent's response]
```

## Command Reference

### Main Agent Script

```bash
# Basic usage
uv run agent/main.py <URL>

# With query
uv run agent/main.py <URL> --query "Your question"
uv run agent/main.py <URL> -q "Your question"

# Help
uv run agent/main.py --help
uv run agent/main.py -h
```

### Quickstart Script

```bash
# Interactive mode
uv run quickstart.py

# Prompts for URL and starts chat
```

## Interactive Chat Mode

Once in chat mode, you can:

```
❓ You: What is the main topic?
🤖 Agent: [Response with citations]

❓ You: Tell me more about X
🤖 Agent: [Response with more details]

❓ You: quit
👋 Goodbye!
```

### Chat Commands

- Type any question to get an answer
- Type `quit`, `exit`, or `q` to end the session
- Press `Ctrl+C` to exit anytime

## Behind the Scenes

### What Happens When You Start

1. **URL Validation**: System accepts the URL
2. **Collection Check**: Looks up if URL was previously indexed
3. **Decision Point**:
   - **If indexed**: Uses existing collection
   - **If new**: Automatically indexes documents
4. **Agent Ready**: Starts chat session

### Automatic Indexing Process

When a new URL is provided:

```
📥 Indexing documents from URL...
   ├── Loading web page
   ├── Splitting into chunks (batch size: 10)
   ├── Creating embeddings
   ├── Storing in Qdrant
   └── Saving URL mapping
✅ Done! Ready to chat
```

### Collection Naming

Collections are automatically named based on URL:
- Format: `rag_<domain>_<hash>`
- Example: `rag_lilianweng_github_io_31d52fb4`
- Stored in: `url_collections.json`

## Features

### ✅ What's Included

- **Auto-indexing**: No separate indexing step needed
- **Smart caching**: Reuses existing collections
- **Batch processing**: Handles timeouts with retry logic
- **Progress feedback**: Clear status messages
- **Interactive mode**: Natural conversation flow
- **Single query mode**: Quick one-off questions
- **Persistent storage**: Remembers all indexed URLs

### 🎯 Benefits

- **Simpler workflow**: One command does everything
- **Faster start**: Existing URLs load instantly
- **No confusion**: Always know what you're chatting about
- **Reliable**: Automatic retry on failures
- **Transparent**: Shows what's happening at each step

## Configuration

### Environment Variables

Required in `.env`:
```env
GOOGLE_API_KEY=your_key
QDRANT_API_KEY=your_key
QDRANT_URL=your_url
```

Optional tuning:
```env
BATCH_SIZE=10          # Documents per batch
CHUNK_SIZE=1000        # Characters per chunk
CHUNK_OVERLAP=200      # Overlap between chunks
TOP_K_RESULTS=3        # Results per query
```

## Troubleshooting

### "Missing environment variables"
```bash
# Copy example file and edit
cp .env.example .env
# Add your API keys
```

### "Failed to load document"
- Check if URL is accessible
- Ensure URL uses http/https protocol
- Try a different URL

### "Indexing timeout"
```bash
# Reduce batch size
BATCH_SIZE=5 uv run agent/main.py "https://example.com"
```

### Want to reindex?
```bash
# Delete the URL from url_collections.json
# Or wait - we'll add a --reindex flag!
```

## Advanced Usage

### Programmatic Access

```python
from agent.main import ensure_collection_ready, create_rag_agent, run_agent_query

# Ensure collection is ready
collection_name = ensure_collection_ready("https://example.com")

# Create agent
agent = create_rag_agent()

# Run query
run_agent_query(agent, "What is this about?", collection_name)
```

### Check Indexed URLs

```python
from url_mapper import URLCollectionMapper

mapper = URLCollectionMapper()
mappings = mapper.list_all_mappings()

for url, info in mappings.items():
    print(f"{url}: {info['document_count']} docs")
```

## Comparison: Old vs New Workflow

### Old Workflow ❌
```bash
# Step 1: Index (separate command)
python agent/index_docs.py https://example.com

# Step 2: Chat (separate command)
python agent/main.py --query "question"

# Issues:
# - Two separate steps
# - Need to remember if indexed
# - Collection management manual
```

### New Workflow ✅
```bash
# One command does both!
python agent/main.py https://example.com

# Benefits:
# ✅ Single command
# ✅ Auto-detects if indexed
# ✅ Automatic collection management
# ✅ Clear feedback at each step
```

## Migration from Old Version

If you have existing indexed documents:

1. They're still in Qdrant
2. Run with the original URL - system will index again (new collection)
3. Or manually add mapping to `url_collections.json`

The old `index_docs.py` script still works if you need manual indexing:
```bash
uv run agent/index_docs.py "https://example.com"
uv run agent/index_docs.py --list
```

## What's Next?

Planned improvements:
- [ ] Reindex existing URLs (update content)
- [ ] Delete collections
- [ ] Multi-URL sessions (search across multiple sources)
- [ ] URL validation and sanitization
- [ ] Collection statistics in chat
- [ ] Export/import collections

---

**Now you can just provide a URL and start chatting - the system handles the rest!** 🎉
