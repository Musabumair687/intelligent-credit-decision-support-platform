"""
embedding.py

Creates the Gemini Embedding Model.
"""

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from rag.config import (
    GOOGLE_API_KEY,
    EMBEDDING_MODEL,
)


class EmbeddingModel:
    """
    Creates and returns the Gemini embedding model.
    """

    def __init__(self):

        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            google_api_key=GOOGLE_API_KEY,
        )

    def get_embedding_model(self):

        return self.embedding_model


if __name__ == "__main__":

    model = EmbeddingModel().get_embedding_model()

    vector = model.embed_query(
        "Customer with high salary gets premium loan."
    )

    print("=" * 60)
    print("Embedding Dimension:", len(vector))
    print("=" * 60)
    print(vector[:10])

    