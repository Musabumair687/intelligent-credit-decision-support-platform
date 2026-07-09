print("Running keyword_retriever.py")
"""
keyword_retriever.py

Purpose
-------
This module provides keyword-based retrieval using the
BM25 ranking algorithm.

Unlike semantic search, BM25 retrieves documents based
on exact keyword matching.

Workflow
--------
1. Load PDF documents
2. Split documents into chunks
3. Build BM25 index
4. Perform keyword search
5. Return relevant document chunks

Author
------
Intelligent Credit Decision Support Platform
"""

# ---------------------------------------------------------
# Imports
# ---------------------------------------------------------

from langchain_community.retrievers import BM25Retriever

from rag.documents.document_loader import DocumentLoader
from rag.documents.text_splitter import DocumentSplitter

from rag.config import (
    DOCUMENT_PATH,
)


class KeywordRetriever:
    """
    Performs keyword-based retrieval using BM25.
    """

    def __init__(self):
        """
        Initialize the BM25 Retriever.

        Steps
        -----
        1. Load documents
        2. Split into chunks
        3. Build BM25 index
        """

        # ---------------------------------------------
        # Load PDF documents
        # ---------------------------------------------

        loader = DocumentLoader(DOCUMENT_PATH)

        documents = loader.load_all_pdfs()

        # ---------------------------------------------
        # Split documents
        # ---------------------------------------------

        splitter = DocumentSplitter()

        chunks = splitter.split_documents(documents)

        # Save chunks (optional but useful later)
        self.documents = chunks

        # ---------------------------------------------
        # Build BM25 Retriever
        # ---------------------------------------------

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
        Perform keyword search.

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

    print("=" * 60)
    print("BM25 KEYWORD SEARCH")
    print("=" * 60)

    for i, doc in enumerate(documents, start=1):

        print(f"\nDocument {i}")
        print("-" * 60)

        print(doc.page_content[:400])

        print("\nMetadata")

        print(doc.metadata)