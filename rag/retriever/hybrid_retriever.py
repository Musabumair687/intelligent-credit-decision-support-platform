"""
hybrid_retriever.py

Purpose
-------
Combines Semantic Search and BM25 Keyword Search
to retrieve more relevant documents.
"""

from rag.retriever.semantic_retriever import SemanticRetriever
from rag.retriever.keyword_retriever import KeywordRetriever


class HybridRetriever:
    """
    Combines semantic and keyword retrieval.
    """

    def __init__(self):

        self.semantic = SemanticRetriever()

        self.keyword = KeywordRetriever()

    def search(
        self,
        query: str,
        semantic_k: int = 30,
        keyword_k: int = 30,
    ):
        """
        Perform hybrid retrieval.

        Returns
        -------
        List[Document]
        """

        semantic_docs = self.semantic.similarity_search(
            query=query,
            k=semantic_k,
        )

        keyword_docs = self.keyword.search(
            query=query,
            k=keyword_k,
        )

        unique_docs = {}

        for doc in semantic_docs + keyword_docs:
            unique_docs[doc.page_content] = doc

        return list(unique_docs.values())


if __name__ == "__main__":

    retriever = HybridRetriever()

    query = "Who is eligible for premium loan?"

    docs = retriever.search(query)

    print("=" * 60)
    print("HYBRID SEARCH")
    print("=" * 60)

    for i, doc in enumerate(docs, start=1):

        print(f"\nDocument {i}")
        print("-" * 60)

        print(doc.page_content[:400])

        print("\nMetadata")

        print(doc.metadata)


        