"""
weighted_hybrid.py

Purpose
-------
Combine Semantic Search and BM25 Keyword Search
using weighted score fusion.

Final Score =
(semantic_weight × semantic_score)
+
(keyword_weight × keyword_score)

Author
------
Intelligent Credit Decision Support Platform
"""

from rag.retriever.semantic_retriever import SemanticRetriever
from rag.retriever.keyword_retriever import KeywordRetriever


class WeightedHybridRetriever:
    """
    Combines semantic similarity search and BM25 keyword search
    using weighted score fusion.
    """

    def __init__(self):
        """
        Initialize both retrievers.
        """

        self.semantic = SemanticRetriever()
        self.keyword = KeywordRetriever()

    # ---------------------------------------------------------

    @staticmethod
    def distance_to_similarity(distance: float):
        """
        Convert Chroma distance into similarity.

        Smaller distance -> Higher similarity.

        Formula:
            similarity = 1 / (1 + distance)

        Example

        distance = 0.20
        similarity = 0.83

        distance = 1.00
        similarity = 0.50
        """

        return 1 / (1 + distance)

    # ---------------------------------------------------------

    def search(
        self,
        query: str,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        semantic_k: int = 30,
        keyword_k: int = 30,
    ):
        """
        Perform weighted hybrid retrieval.

        Parameters
        ----------
        query : str

        semantic_weight : float

        keyword_weight : float

        semantic_k : int

        keyword_k : int

        Returns
        -------
        List of tuples

        (
            Document,
            Final Score,
            Semantic Score,
            Keyword Score
        )
        """

        # ---------------------------------------------
        # Semantic Search
        # ---------------------------------------------

        semantic_results = self.semantic.similarity_search_with_score(
            query=query,
            k=semantic_k,
        )

        # ---------------------------------------------
        # BM25 Search
        # ---------------------------------------------

        keyword_results = self.keyword.search(
            query=query,
            k=keyword_k,
        )

        # ---------------------------------------------
        # Store document scores
        # ---------------------------------------------

        documents = {}

        # ---------------------------------------------
        # Process Semantic Results
        # ---------------------------------------------

        for doc, distance in semantic_results:

            key = doc.page_content

            semantic_score = self.distance_to_similarity(distance)

            documents[key] = {
                "document": doc,
                "semantic_score": semantic_score,
                "keyword_score": 0.0,
            }

        # ---------------------------------------------
        # Process BM25 Results
        # ---------------------------------------------

        total = len(keyword_results)

        for rank, doc in enumerate(keyword_results):

            key = doc.page_content

            keyword_score = (total - rank) / total

            if key not in documents:

                documents[key] = {
                    "document": doc,
                    "semantic_score": 0.0,
                    "keyword_score": keyword_score,
                }

            else:

                documents[key]["keyword_score"] = keyword_score

        # ---------------------------------------------
        # Calculate Final Score
        # ---------------------------------------------

        final_results = []

        for value in documents.values():

            final_score = (
                semantic_weight * value["semantic_score"]
                +
                keyword_weight * value["keyword_score"]
            )

            final_results.append(
                (
                    value["document"],
                    final_score,
                    value["semantic_score"],
                    value["keyword_score"],
                )
            )

        # ---------------------------------------------
        # Sort by Final Score
        # ---------------------------------------------

        final_results.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        return final_results


# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------

if __name__ == "__main__":

    retriever = WeightedHybridRetriever()

    query = "Who is eligible for premium loan?"

    results = retriever.search(query)

    print("=" * 80)
    print("WEIGHTED HYBRID SEARCH")
    print("=" * 80)

    for i, (doc, final_score, semantic_score, keyword_score) in enumerate(results, start=1):

        print(f"\nDocument {i}")
        print("-" * 80)

        print(f"Final Score     : {final_score:.4f}")
        print(f"Semantic Score : {semantic_score:.4f}")
        print(f"Keyword Score  : {keyword_score:.4f}")

        print("\nContent\n")

        print(doc.page_content[:500])

        print("\nMetadata")

        print(doc.metadata)