"""
temporary_file.py

Purpose
-------
Benchmark every stage of the RAG pipeline individually.

Measures:

1. Semantic Search
2. Keyword Search (BM25)
3. RRF Fusion
4. Cross Encoder
5. Prompt Builder
6. Gemini
7. Total Pipeline Time
"""

import time

from rag.retriever.rrf_retriever import RRFRetriever
from rag.retriever.cross_encoder_reranker import CrossEncoderReranker
from rag.prompt.prompt_builder import PromptBuilder
from rag.LLM.gemini_service import GeminiService


# ============================================================
# Initialize Components
# ============================================================

query = "What is Debt-to-Income ratio?"

retriever = RRFRetriever()
reranker = CrossEncoderReranker()
builder = PromptBuilder()
llm = GeminiService()


overall_start = time.perf_counter()

# ============================================================
# Semantic Search
# ============================================================

start = time.perf_counter()

semantic_docs = retriever.semantic.similarity_search(
    query=query,
    k=30,
)

semantic_time = time.perf_counter() - start

# ============================================================
# Keyword Search
# ============================================================

start = time.perf_counter()

keyword_docs = retriever.keyword.search(
    query=query,
    k=30,
)

keyword_time = time.perf_counter() - start

# ============================================================
# Reciprocal Rank Fusion (RRF)
# ============================================================

start = time.perf_counter()

scores = {}

rrf_k = 60

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

retrieved_docs = sorted(

    scores.values(),

    key=lambda x: x["score"],

    reverse=True,

)[:20]

rrf_time = time.perf_counter() - start

# ============================================================
# Cross Encoder Re-ranking
# ============================================================

start = time.perf_counter()

ranked_docs = reranker.rerank(

    query=query,

    documents=retrieved_docs,

    top_k=5,

)

rerank_time = time.perf_counter() - start

# ============================================================
# Prompt Builder
# ============================================================

documents = [

    item["document"]

    for item in ranked_docs

]

start = time.perf_counter()

prompt = builder.build_prompt(

    query=query,

    documents=documents,

)

prompt_time = time.perf_counter() - start

# ============================================================
# Gemini
# ============================================================

start = time.perf_counter()

answer = llm.generate(prompt)

llm_time = time.perf_counter() - start

# ============================================================
# Total Time
# ============================================================

overall_time = time.perf_counter() - overall_start

retrieval_total = semantic_time + keyword_time + rrf_time

# ============================================================
# Results
# ============================================================

print("\n")
print("=" * 75)
print("RAG PIPELINE BENCHMARK")
print("=" * 75)

print(f"{'Semantic Search':30} : {semantic_time:.3f} sec")
print(f"{'Keyword Search (BM25)':30} : {keyword_time:.3f} sec")
print(f"{'RRF Fusion':30} : {rrf_time:.6f} sec")

print("-" * 75)

print(f"{'Retrieval Total':30} : {retrieval_total:.3f} sec")

print("-" * 75)

print(f"{'Cross Encoder':30} : {rerank_time:.3f} sec")
print(f"{'Prompt Builder':30} : {prompt_time:.6f} sec")
print(f"{'Gemini':30} : {llm_time:.3f} sec")

print("-" * 75)

print(f"{'TOTAL PIPELINE':30} : {overall_time:.3f} sec")

print("=" * 75)