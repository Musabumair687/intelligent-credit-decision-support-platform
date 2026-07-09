print("Running semantic_retriever.py")

"""
semantic_retriever.py

Purpose
-------
This module provides semantic search functionality
using the Chroma Vector Database.

Workflow
--------
1. Load embedding model
2. Load existing Chroma Vector Database
3. Perform semantic search
4. Return relevant document chunks

Author
------
Intelligent Credit Decision Support Platform
"""

# ---------------------------------------------------------
# Import VectorStoreManager
# Used to load the Chroma database
# ---------------------------------------------------------

from rag.vector_store.vector_store import VectorStoreManager

# ---------------------------------------------------------
# Import EmbeddingModel
# Used to create the embedding model
# ---------------------------------------------------------

from rag.embeddings.embedding import EmbeddingModel

# ---------------------------------------------------------
# Import configuration variables
# ---------------------------------------------------------

from rag.config import (
    VECTOR_DB_PATH,
    COLLECTION_NAME,
)


class SemanticRetriever:
    """
    Performs semantic search on the Chroma Vector Database.
    """

    def __init__(self):
        """
        Initialize the semantic retriever.

        Steps
        -----
        1. Load embedding model
        2. Load vector database
        """

        # Create embedding model
        self.embedding_model = EmbeddingModel().get_embedding_model()

        # Create vector store manager
        self.vector_store_manager = VectorStoreManager(
            persist_directory=VECTOR_DB_PATH,
            collection_name=COLLECTION_NAME,
            embedding_model=self.embedding_model,
        )

        # Load existing Chroma database
        self.vector_store = self.vector_store_manager.load_vector_store()

    # -----------------------------------------------------

    def similarity_search(
        self,
        query: str,
        k: int = 30,
    ):
        """
        Perform semantic similarity search.

        Parameters
        ----------
        query : str
            User question.

        k : int
            Number of documents to retrieve.

        Returns
        -------
        list[Document]
        """

        return self.vector_store.similarity_search(
            query=query,
            k=k,
        )

    # -----------------------------------------------------

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 30,
    ):
        """
        Perform semantic search with similarity score.

        Returns
        -------
        List of

        (Document, Score)
        """

        return self.vector_store.similarity_search_with_score(
            query=query,
            k=k,
        )

    # -----------------------------------------------------

    def mmr_search(
        self,
        query: str,
        k: int = 30,
        fetch_k: int = 20,
    ):
        """
        Perform Maximum Marginal Relevance search.

        MMR retrieves diverse documents
        while maintaining relevance.
        """

        return self.vector_store.max_marginal_relevance_search(
            query=query,
            k=k,
            fetch_k=fetch_k,
        )

    # -----------------------------------------------------

    def as_retriever(
        self,
        search_type="similarity",
        k: int = 30,
    ):
        """
        Return LangChain Retriever object.

        Useful for RetrievalQA chains.
        """

        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs={
                "k": k,
            },
        )


# ------------------------------------------------------------------
# Testing
# ------------------------------------------------------------------

if __name__ == "__main__":

    retriever = SemanticRetriever()

    query = "What is model Transperancy?"

    # ============================================
    # Test 1
    # ============================================

    print("=" * 60)
    print("SIMILARITY SEARCH")
    print("=" * 60)

    documents = retriever.similarity_search(query)

    for i, doc in enumerate(documents, start=1):
        print(f"\nDocument {i}")
        print(doc.page_content[:300])
        print(doc.metadata)
    print("\nFinished Test 1")

    # ============================================
    # Test 2
    # ============================================

    print("\n" + "=" * 60)
    print("SIMILARITY SEARCH WITH SCORE")
    print("=" * 60)

    results = retriever.similarity_search_with_score(query)

    for i, (doc, score) in enumerate(results, start=1):
        print(f"\nDocument {i}")
        print(f"Score : {score}")
        print(doc.page_content[:300])
        print(doc.metadata)
    print("\nFinished Test 2")

    # ============================================
    # Test 3
    # ============================================

    print("\n" + "=" * 60)
    print("MMR SEARCH")
    print("=" * 60)

    documents = retriever.mmr_search(query)

    for i, doc in enumerate(documents, start=1):
        print(f"\nDocument {i}")
        print(doc.page_content[:300])
        print(doc.metadata)
    print("\nFinished Test 3")

    # ============================================
    # Test 4
    # ============================================

    print("\n" + "=" * 60)
    print("AS RETRIEVER")
    print("=" * 60)

    lc_retriever = retriever.as_retriever()

    documents = lc_retriever.invoke(query)

    for i, doc in enumerate(documents, start=1):
        print(f"\nDocument {i}")
        print(doc.page_content[:300])
        print(doc.metadata)
    print("\nFinished Test 4")


        