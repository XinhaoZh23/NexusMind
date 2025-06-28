from typing import List
import numpy as np
import faiss

from core.nexusmind.storage.vector_store_base import VectorStoreBase
from core.nexusmind.processor.splitter import Chunk
from core.nexusmind.llm.llm_endpoint import LLMEndpoint


class FaissVectorStore(VectorStoreBase):
    """
    An in-memory vector store using FAISS.
    """

    def __init__(self, llm_endpoint: LLMEndpoint):
        self.llm_endpoint = llm_endpoint
        self.index = None
        # Mapping from FAISS index ID to Chunk object
        self.index_to_chunk: List[Chunk] = []

    def add_documents(self, chunks: List[Chunk]) -> None:
        if not chunks:
            return

        embeddings = [self.llm_endpoint.get_embedding(chunk.content) for chunk in chunks]
        
        # Ensure all embeddings are valid
        valid_embeddings = [emb for emb in embeddings if emb]
        if not valid_embeddings:
            print("Warning: No valid embeddings were generated for the provided chunks.")
            return
            
        dimension = len(valid_embeddings[0])
        vectors = np.array(valid_embeddings).astype("float32")

        if self.index is None:
            self.index = faiss.IndexFlatL2(dimension)

        self.index.add(vectors)
        self.index_to_chunk.extend(chunks)

    def similarity_search(self, query: str, k: int = 5) -> List[Chunk]:
        if self.index is None:
            return []

        query_embedding = self.llm_endpoint.get_embedding(query)
        if not query_embedding:
            return []

        query_vector = np.array([query_embedding]).astype("float32")
        
        # k might be larger than the number of vectors in the index
        k = min(k, self.index.ntotal)

        distances, indices = self.index.search(query_vector, k)

        # The indices returned are 2D, so we flatten them
        return [self.index_to_chunk[i] for i in indices[0]] 