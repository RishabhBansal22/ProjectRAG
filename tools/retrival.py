from langchain.tools import tool
from lang_comps.components import VectorStore, GoogleEmbedding
from qdrant.client import Qdrant

# Initialize components
embeddings = GoogleEmbedding()
embed = embeddings.Client()
qrant = Qdrant()
collection_name = "test"

# Create vector store instance
Vectorstore = VectorStore(
    client=qrant.client,
    collection_name=collection_name,
    embeddings=embed
)
vector_store = Vectorstore.vector_store()

@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    retrieved_docs = vector_store.similarity_search(query, k=1)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs