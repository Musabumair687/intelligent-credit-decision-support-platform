"""
cross_encoder_reranker.py

Purpose
-------
Re-rank retrieved documents using a Cross Encoder model.

Pipeline
--------
User Query
      │
      ▼
RRF Retriever
      │
      ▼
Top Retrieved Documents
      │
      ▼
Cross Encoder
      │
      ▼
Final Ranked Documents
"""

from sentence_transformers import CrossEncoder

from rag.retriever.rrf_retriever import RRFRetriever


class CrossEncoderReranker:
    """
    Re-ranks retrieved documents using a Cross Encoder model.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ):
        self.model = CrossEncoder(model_name)

    # ---------------------------------------------------------

    def rerank(
        self,
        query: str,
        documents: list,
        top_k: int = 5,
    ):
        """
        Re-rank retrieved documents.

        Parameters
        ----------
        query : str
            User question.

        documents : list
            Output returned by RRFRetriever.

        top_k : int
            Number of final documents.

        Returns
        -------
        list[dict]

        Example

        [
            {
                "document": Document(...),
                "rrf_score": 0.031,
                "cross_score": 8.74
            }
        ]
        """

        # ---------------------------------------------
        # Build (query, document) sentence pairs
        # ---------------------------------------------

        sentence_pairs = [
            (
                query,
                item["document"].page_content,
            )
            for item in documents
        ]

        # ---------------------------------------------
        # Cross Encoder prediction
        # ---------------------------------------------

        scores = self.model.predict(sentence_pairs)

        # ---------------------------------------------
        # Store results
        # ---------------------------------------------

        ranked_documents = []

        for item, score in zip(documents, scores):

            ranked_documents.append(
                {
                    "document": item["document"],
                    "rrf_score": item["score"],
                    "cross_score": float(score),
                }
            )

        # ---------------------------------------------
        # Sort by Cross Encoder score
        # ---------------------------------------------

        ranked_documents.sort(
            key=lambda x: x["cross_score"],
            reverse=True,
        )

        return ranked_documents[:top_k]


# ============================================================
# Testing
# ============================================================

if __name__ == "__main__":

    rrf = RRFRetriever()

    reranker = CrossEncoderReranker()

    query = "List all seven primary risk domains defined in Stratum Capital Bank's Enterprise Risk Management framework, and identify which chapter of the EGRF specifically addresses credit risk monitoring and loan classification."
    

    retrieved_docs = rrf.search(query)

    ranked_docs = reranker.rerank(
        query=query,
        documents=retrieved_docs,
        top_k=5,
    )

    print("=" * 80)
    print("CROSS ENCODER RERANKER")
    print("=" * 80)

    for i, item in enumerate(ranked_docs, start=1):

        doc = item["document"]

        print(f"\nDocument {i}")
        print("-" * 80)

        print(f"Cross Encoder Score : {item['cross_score']:.4f}")
        print(f"RRF Score           : {item['rrf_score']:.6f}")

        print("\nContent\n")

        print(doc.page_content[:500])

        print("\nMetadata")

        print(doc.metadata)