import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Only keep post title, headers, and content from the full HTML.
def web_doc_loader(url:str):
    bs4_strainer = bs4.SoupStrainer(class_=("post-title", "post-header", "post-content"))
    loader = WebBaseLoader(
        web_paths=(url,),
        bs_kwargs={"parse_only": bs4_strainer},
    )
    docs = loader.load()
    return docs

def text_splitter(docs):
    text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # chunk size (characters)
    chunk_overlap=200,  # chunk overlap (characters)
    add_start_index=True,  # track index in original document
)
    all_splits = text_splitter.split_documents(docs)
    return all_splits

# docs = web_doc_loader(url=r"https://lilianweng.github.io/posts/2023-06-23-agent/")
# splits = text_splitter(docs=docs)
# print(f"Split blog post into {len(splits)} sub-documents.")
# print(splits[0])
