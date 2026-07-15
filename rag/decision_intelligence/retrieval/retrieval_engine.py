"""
retrieval_engine.py

Purpose
-------
Connects the Decision Intelligence module with
the Retrieval-Augmented Generation (RAG) pipeline.

The Retrieval Engine does NOT implement retrieval
algorithms.

Instead, it coordinates:

1. Reciprocal Rank Fusion (RRF)
2. Cross Encoder Re-ranking

and returns the final evidence documents used
by the Decision Prompt.

Pipeline
--------
Evidence Builder
        │
        ▼
Retrieval Query
        │
        ▼
RRF Retriever
        │
        ▼
Cross Encoder
        │
        ▼
Top Evidence Documents

Author
------
Intelligent Credit Decision Support Platform
"""

from rag.retriever.rrf_retriever import RRFRetriever

from rag.retriever.cross_encoder_reranker import (
    CrossEncoderReranker,
)


class RetrievalEngine:
    """
    Connects the Decision Intelligence module
    with the RAG retrieval pipeline.
    """

    def __init__(self):
        """
        Initialize Retrieval Engine.
        """

        self.rrf = RRFRetriever()

        self.reranker = CrossEncoderReranker()

    # ---------------------------------------------------------

    def retrieve(
        self,
        evidence: dict,
        final_k: int = 5,
    ) -> dict:
        """
        Retrieve supporting policy documents.

        Parameters
        ----------
        evidence : dict

            Output produced by Evidence Builder.

        final_k : int

            Number of final evidence documents.

        Returns
        -------
        dict

            Updated evidence object containing
            retrieved documents.
        """

        retrieval_query = evidence["retrieval_query"]

        # -----------------------------------------
        # RRF Retrieval
        # -----------------------------------------

        retrieved_documents = self.rrf.search(

            query=retrieval_query,

        )

        # -----------------------------------------
        # Cross Encoder Re-ranking
        # -----------------------------------------

        reranked_documents = self.reranker.rerank(

            query=retrieval_query,

            documents=retrieved_documents,

            top_k=final_k,

        )

        # -----------------------------------------
        # Store evidence
        # -----------------------------------------

        evidence["retrieved_documents"] = reranked_documents

        return evidence


# ==========================================================
# Testing
# ==========================================================

if __name__ == "__main__":

    evidence = {

        "prediction": "Charged Off",

        "probability": 0.84,

        "top_features": [

            {
                "feature": "dti",
                "value": 41,
                "importance": 0.44,
            },

            {
                "feature": "annual_income",
                "value": 50000,
                "importance": 0.28,
            },

            {
                "feature": "grade",
                "value": "B3",
                "importance": 0.17,
            },

        ],

        "retrieval_query": """Why this loan was rejected?

Loan rejection policy

Debt-to-Income Ratio policy

Annual income eligibility

Credit grade policy

""",

    }

    engine = RetrievalEngine()

    evidence = engine.retrieve(evidence)

    print("=" * 80)
    print("RETRIEVAL ENGINE")
    print("=" * 80)

    print("\nPrediction :", evidence["prediction"])

    print("\nProbability :", evidence["probability"])

    print("\nRetrieved Documents")

    print("-" * 80)

    for index, item in enumerate(

        evidence["retrieved_documents"],

        start=1,

    ):

        print(f"\nDocument {index}")

        print(f"Cross Score : {item['cross_score']:.4f}")

        print(f"RRF Score   : {item['rrf_score']:.6f}")

        print("\nContent\n")

        print(item["document"].page_content[:500])

        print("\nMetadata")

        print(item["document"].metadata)