"""
rrf_retriever.py

Purpose
-------
Implements Reciprocal Rank Fusion (RRF) by combining
Semantic Search and BM25 Keyword Search.

Instead of combining scores,
RRF combines document ranks.

Author
------
Intelligent Credit Decision Support Platform
"""

from rag.retriever.semantic_retriever import SemanticRetriever
from rag.retriever.keyword_retriever import KeywordRetriever


class RRFRetriever:
    """
    Reciprocal Rank Fusion Retriever.
    """

    def __init__(self):

        self.semantic = SemanticRetriever()

        self.keyword = KeywordRetriever()

    def search(
        self,
        query: str,
        semantic_k: int = 30,
        keyword_k: int = 30,
        final_k: int = 20,
        rrf_k: int = 60,
    ):
        """
        Perform Reciprocal Rank Fusion.

        Parameters
        ----------
        query : str

        semantic_k : int
            Number of semantic documents.

        keyword_k : int
            Number of BM25 documents.

        final_k : int
            Final documents returned.

        rrf_k : int
            Constant used in RRF formula.

        Returns
        -------
        List[(Document, Score)]
        """

        semantic_docs = self.semantic.similarity_search(
            query=query,
            k=semantic_k,
        )

        keyword_docs = self.keyword.search(
            query=query,
            k=keyword_k,
        )

        scores = {}

        # -----------------------------
        # Semantic Ranking
        # -----------------------------

        for rank, doc in enumerate(semantic_docs, start=1):

            key = doc.page_content

            if key not in scores:

                scores[key] = {
                    "document": doc,
                    "score": 0.0,
                }

            scores[key]["score"] += 1 / (rrf_k + rank)

        # -----------------------------
        # Keyword Ranking
        # -----------------------------

        for rank, doc in enumerate(keyword_docs, start=1):

            key = doc.page_content

            if key not in scores:

                scores[key] = {
                    "document": doc,
                    "score": 0.0,
                }

            scores[key]["score"] += 1 / (rrf_k + rank)

        results = sorted(

            scores.values(),

            key=lambda x: x["score"],

            reverse=True,

        )

        return results[:final_k]


if __name__ == "__main__":

    retriever = RRFRetriever()

    query = "Who is eligible for premium loan?"

    documents = retriever.search(query)

    print("=" * 80)
    print("RECIPROCAL RANK FUSION")
    print("=" * 80)

    for index, item in enumerate(documents, start=1):

        document = item["document"]

        score = item["score"]

        print(f"\nDocument {index}")
        print("-" * 80)

        print(f"RRF Score : {score:.6f}")

        print("\nContent\n")

        print(document.page_content[:500])

        print("\nMetadata")

        print(document.metadata)