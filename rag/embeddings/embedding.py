"""
embedding.py

Purpose:
--------
Initialize and provide the embedding model used by the RAG pipeline.

The embedding model converts text into vector representations
that ChromaDB can use for semantic similarity search.
"""

from langchain_ollama import OllamaEmbeddings


class EmbeddingModel:
    """
    Creates and provides the embedding model.
    """

    def __init__(self):
        self.embedding_model = OllamaEmbeddings(
            model="nomic-embed-text"
        )

    def get_embedding_model(self):
        """
        Return the initialized embedding model.
        """
        return self.embedding_model


if __name__ == "__main__":

    model = EmbeddingModel().get_embedding_model()

    embedding = model.embed_query(
        "A customer with a high credit score is eligible for a premium loan."
    )

    print("=" * 60)
    print(f"Embedding Dimension : {len(embedding)}")
    print("=" * 60)

    print("\nFirst 10 Values:\n")
    print(embedding[:10])

    