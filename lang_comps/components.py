from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant.client import Qdrant
from dotenv import load_dotenv
import os

load_dotenv()
qdrant = Qdrant()

class ChatGemini:
    def __init__(self,api_key=os.getenv("GOOGLE_API_KEY"),model:str="gemini-2.0-flash"):
        self.api_key=api_key
        self.model=model

    def client(self):
        client = ChatGoogleGenerativeAI(
            google_api_key=self.api_key,
            model=self.model
        )
        return client
        

class GoogleEmbedding:
    def __init__(self, api_key: str = None, model: str = "models/gemini-embedding-001"):
        self.model = model
        if api_key is None:
            self.api_key = os.getenv("GOOGLE_API_KEY")
    
    def Client(self):
        client = GoogleGenerativeAIEmbeddings(
            google_api_key=self.api_key,
            model=self.model
        )
        return client

class VectorStore:
    def __init__(self,client,collection_name,embeddings):
        self.collection_name = collection_name
        self.embeddings = embeddings
        if client:
            self.client = client
        else:
            self.client = qdrant.client

    def vector_store(self):
        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name =  self.collection_name,
            embedding=self.embeddings

        )
        return vector_store
    
    
