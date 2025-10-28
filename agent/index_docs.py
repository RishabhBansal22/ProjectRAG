from agent.document import web_doc_loader, text_splitter
from qdrant.client import Qdrant
from lang_comps.components import VectorStore, GoogleEmbedding

embeddings = GoogleEmbedding()
embed = embeddings.Client()

qrant = Qdrant()
collection_name = "test"
qrant.create_collection(collection_name, size=len(embed.embed_query("sample_txt")))

def index_documents(url:str):

    docs = web_doc_loader(url)
    splits = text_splitter(docs)
    store = VectorStore(
        client=qrant.client,
        collection_name=collection_name,
        embeddings=embed
    )
    vector_store = store.vector_store()
    doc_ids = vector_store.add_documents(documents=splits)
    return doc_ids

# doc_ids = index_documents(url=r"https://lilianweng.github.io/posts/2023-06-23-agent/")
# print(doc_ids)