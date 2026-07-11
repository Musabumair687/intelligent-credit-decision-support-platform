"""
keyword_retriever.py

Purpose
-------
Performs keyword-based retrieval using the BM25 algorithm.

Instead of loading and chunking PDF documents every time,
this module loads the pre-built chunk store (chunks.pkl).

Workflow
--------
Load chunks.pkl
      │
      ▼
Build BM25 Index
      │
      ▼
Keyword Search
      │
      ▼
Return Relevant Chunks

Author
------
Intelligent Credit Decision Support Platform
"""

# ---------------------------------------------------------
# Imports
# ---------------------------------------------------------

import pickle
from pathlib import Path

from langchain_community.retrievers import BM25Retriever


class KeywordRetriever:
    """
    Performs keyword-based retrieval using BM25.
    """

    def __init__(self):
        """
        Initialize the BM25 Retriever.

        Steps
        -----
        1. Load chunk store
        2. Build BM25 Index
        """

        # -------------------------------------------------
        # Locate chunk file
        # -------------------------------------------------

        BASE_DIR = Path(__file__).resolve().parents[2]

        chunk_file = (
            BASE_DIR
            / "docs"
            / "chunks"
            / "chunks.pkl"
        )

        # -------------------------------------------------
        # Load chunks
        # -------------------------------------------------

        with open(chunk_file, "rb") as file:

            self.documents = pickle.load(file)

        print(f"Loaded {len(self.documents)} chunks.")

        # -------------------------------------------------
        # Build BM25 Retriever
        # -------------------------------------------------

        self.retriever = BM25Retriever.from_documents(
            self.documents
        )

    # -------------------------------------------------

    def search(
        self,
        query: str,
        k: int = 30,
    ):
        """
        Perform BM25 keyword search.

        Parameters
        ----------
        query : str
            User question.

        k : int
            Number of documents to retrieve.

        Returns
        -------
        List[Document]
        """

        self.retriever.k = k

        return self.retriever.invoke(query)


# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------

if __name__ == "__main__":

    retriever = KeywordRetriever()

    query = "premium loan interest rate"

    documents = retriever.search(
        query=query,
        k=30,
    )

    print("=" * 70)
    print("BM25 KEYWORD SEARCH")
    print("=" * 70)

    for i, doc in enumerate(documents, start=1):

        print(f"\nDocument {i}")
        print("-" * 70)

        print(doc.page_content[:500])

        print("\nMetadata")

        print(doc.metadata)