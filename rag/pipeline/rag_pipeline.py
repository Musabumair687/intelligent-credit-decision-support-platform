"""
rag_pipeline.py

Purpose
-------
Complete Retrieval-Augmented Generation (RAG) pipeline.

Workflow
--------
User Query
      │
      ▼
Hybrid Retriever
      │
      ▼
Cross Encoder Reranker
      │
      ▼
Prompt Builder
      │
      ▼
Gemini
      │
      ▼
Final Answer
"""

from rag.retriever.rrf_retriever import RRFRetriever
from rag.retriever.cross_encoder_reranker import CrossEncoderReranker

from rag.prompt.prompt_builder import PromptBuilder
from rag.LLM.gemini_service import GeminiService


class RAGPipeline:
    """
    Complete RAG pipeline.
    """

    def __init__(self):

        self.retriever = RRFRetriever()

        self.reranker = CrossEncoderReranker()

        self.prompt_builder = PromptBuilder()

        self.llm = GeminiService()

    def run(self, query: str):

        # -----------------------------
        # Step 1 : Retrieve Documents
        # -----------------------------
        retrieved_docs = self.retriever.search(query)

        # -----------------------------
        # Step 2 : Re-rank
        # -----------------------------
        ranked_docs = self.reranker.rerank(
            query=query,
            documents=retrieved_docs,
            top_k=5
        )

        # -----------------------------
        # Step 3 : Extract Documents
        # -----------------------------
        documents = []

        for item in ranked_docs:

            documents.append(item["document"])

        # -----------------------------
        # Step 4 : Build Prompt
        # -----------------------------
        prompt = self.prompt_builder.build_prompt(
            query=query,
            documents=documents
        )

        # -----------------------------
        # Step 5 : Gemini
        # -----------------------------
        answer = self.llm.generate(prompt)

        return {
            "query": query,
            "answer": answer,
            "documents": documents,
            "prompt": prompt
        }


if __name__ == "__main__":

    pipeline = RAGPipeline()

    query = "What is minimum threshold and what about B5 and G4 subgrade "

    result = pipeline.run(query)

    print("=" * 80)
    print("QUESTION")
    print("=" * 80)

    print(result["query"])

    print()

    print("=" * 80)
    print("ANSWER")
    print("=" * 80)

    print(result["answer"])

    print()

    print("=" * 80)
    print("SOURCES")
    print("=" * 80)

    for i, doc in enumerate(result["documents"], start=1):

        print(f"\nDocument {i}")

        print(doc.metadata["source"])

        print(f"Page : {doc.metadata['page_label']}")