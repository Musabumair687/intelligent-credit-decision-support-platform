"""
vector_store.py

Purpose:
--------
This module is responsible for creating, loading, and managing
the Chroma Vector Database used in the RAG pipeline.

It stores document embeddings generated from document chunks
and provides persistent storage for semantic search.

Author:
--------
Intelligent Credit Decision Support Platform
"""

import time
from pathlib import Path

from langchain_chroma import Chroma


class VectorStoreManager:
    """
    Creates and manages the Chroma Vector Database.
    """

    def __init__(
        self,
        persist_directory: str,
        collection_name: str,
        embedding_model,
    ):
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.embedding_model = embedding_model

    def create_vector_store(self, documents, batch_size: int = 30, delay_seconds: float = 25.0):
        """
        Create (or resume) a Chroma vector database from document chunks.

        If the collection already has documents (from a previous run that
        was interrupted, e.g. by a quota error), this skips already-embedded
        chunks and continues from where it left off, avoiding duplicates.
        """

        vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_model,
            persist_directory=str(self.persist_directory),
        )

        already_done = vector_store._collection.count()
        total = len(documents)

        if already_done > 0:
            print(f"Found {already_done} documents already embedded. Resuming from there.")

        remaining = documents[already_done:]

        if not remaining:
            print("All documents already embedded. Nothing to do.")
            return vector_store

        for i in range(0, len(remaining), batch_size):
            batch = remaining[i : i + batch_size]

            start_num = already_done + i + 1
            end_num = already_done + i + len(batch)

            print(f"Embedding batch ({start_num}-{end_num} of {total})...")

            vector_store.add_documents(batch)

            if i + batch_size < len(remaining):
                time.sleep(delay_seconds)

        print("All batches embedded and stored.")

        return vector_store

    def load_vector_store(self):
        """
        Load an existing Chroma vector database.
        """

        vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_model,
            persist_directory=str(self.persist_directory),
        )

        return vector_store

    def delete_vector_store(self):
        """
        Delete the existing vector database.
        """

        if self.persist_directory.exists():
            for item in self.persist_directory.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    import shutil
                    shutil.rmtree(item)
            print("Vector database deleted successfully.")
        else:
            print("Vector database does not exist.")