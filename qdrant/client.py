from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from dotenv import load_dotenv
import os

load_dotenv()


class Qdrant:
    def __init__(self,api_key=os.getenv('QDRANT_API_KEY'),url=os.getenv("QDRANT_URL")):
        self.client = QdrantClient(
            api_key=api_key,
            url=url
        )

    def create_collection(self,collection_name,size):
        if not self.client.collection_exists(collection_name=collection_name):
            self.client.create_collection(
                collection_name,
                vectors_config=VectorParams(
                    size=size,
                    distance=Distance.COSINE
                )
            )

    
        

    
        

