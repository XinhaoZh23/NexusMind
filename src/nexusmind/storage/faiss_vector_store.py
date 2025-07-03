import logging
import os
import pickle
import json
from pathlib import Path
from typing import List, Optional

import faiss
import numpy as np
from pydantic import Field

from ..llm.llm_endpoint import LLMEndpoint
from ..processor.splitter import Chunk
from .vector_store_base import VectorStoreBase

logger = logging.getLogger(__name__)


class FaissVectorStore(VectorStoreBase):
    """
    An in-memory vector store using FAISS that can be persisted to disk.
    """

    def __init__(self, llm_endpoint: LLMEndpoint, store_path: Optional[str] = None):
        self.llm_endpoint = llm_endpoint
        self.store_path = store_path
        self.index = None
        # Mapping from FAISS index ID to Chunk object
        self.index_to_chunk: List[Chunk] = []

        if self.store_path and Path(self.store_path).exists():
            self._load_from_disk()

    def _get_chunk_path(self) -> Path:
        """Helper to get the path for the chunk mapping file."""
        if not self.store_path:
            raise ValueError("store_path must be set to save or load chunks.")
        return Path(self.store_path).with_suffix(".json")

    def add_documents(self, chunks: List[Chunk]) -> None:
        if not chunks:
            return

        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = [
            self.llm_endpoint.get_embedding(chunk.content) for chunk in chunks
        ]

        # Ensure all embeddings are valid
        valid_embeddings = [emb for emb in embeddings if emb]
        if not valid_embeddings:
            logger.warning(
                "No valid embeddings were generated for the provided chunks. "
                "Index will not be updated."
            )
            return

        logger.info(f"Successfully generated {len(valid_embeddings)} valid embeddings.")
        dimension = len(valid_embeddings[0])
        vectors = np.array(valid_embeddings).astype("float32")

        if self.index is None:
            logger.info(f"Creating new FAISS index with dimension {dimension}.")
            self.index = faiss.IndexFlatL2(dimension)

        self.index.add(vectors)
        self.index_to_chunk.extend(chunks)

        if self.store_path:
            self.save_to_disk()

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

    def save_to_disk(self):
        """Saves the FAISS index and the chunk mapping to disk."""
        if not self.store_path:
            logger.error("store_path must be set to save the index.")
            raise ValueError("store_path must be set to save the index.")
        if self.index is None:
            logger.warning("Index is empty, nothing to save.")
            return

        # Ensure directory exists
        Path(self.store_path).parent.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        logger.info(f"Saving FAISS index to {self.store_path}")
        faiss.write_index(self.index, self.store_path)

        # Save chunk mapping
        chunk_path = self._get_chunk_path()
        with open(chunk_path, "w") as f:
            # Explicitly dump each chunk to its JSON string representation.
            # This is more robust than dumping dicts with a default handler.
            chunk_json_list = [
                chunk.model_dump_json() for chunk in self.index_to_chunk
            ]
            json.dump(chunk_json_list, f, indent=4)

        logger.info(f"Saved {len(self.index_to_chunk)} chunk metadata to {chunk_path}")

    def _load_from_disk(self):
        """Loads the FAISS index and chunk mapping from disk."""
        if not self.store_path or not Path(self.store_path).exists():
            return

        # Load FAISS index
        logger.info(f"Loading FAISS index from {self.store_path}")
        self.index = faiss.read_index(self.store_path)

        # Load chunk mapping
        chunk_path = self._get_chunk_path()
        if chunk_path.exists():
            with open(chunk_path, "r") as f:
                chunk_json_list = json.load(f)
                # Each item in the list is a JSON string, so we need to parse it
                # back into a Chunk object using Pydantic's validator.
                self.index_to_chunk = [
                    Chunk.model_validate_json(data_str)
                    for data_str in chunk_json_list
                ]
