"""
build_vector_store.py

Purpose:
--------
Build the Chroma Vector Database from PDF documents.

Workflow:
---------
1. Load PDF documents
2. Split documents into chunks
3. Initialize embedding model
4. Create Chroma Vector Database
5. Save database to disk

Author:
--------
Intelligent Credit Decision Support Platform
"""

from pathlib import Path

from rag.documents.document_loader import DocumentLoader
from rag.documents.text_splitter import DocumentSplitter
from rag.embeddings.embedding import EmbeddingModel
from rag.vector_db.vector_store import VectorStoreManager


# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DOCUMENT_PATH = PROJECT_ROOT / "docs" / "raw"

VECTOR_DB_PATH = PROJECT_ROOT / "vector_db"

COLLECTION_NAME = "credit_policy"


def main():
    """
    Build the complete vector database.
    """

    print("=" * 60)
    print("Building Chroma Vector Database")
    print("=" * 60)

    # --------------------------------------------------------------
    # Step 1 : Load Documents
    # --------------------------------------------------------------

    print("\nLoading PDF documents...")

    loader = DocumentLoader(DOCUMENT_PATH)

    documents = loader.load_all_pdfs()

    print(f"Loaded {len(documents)} pages.")

    # --------------------------------------------------------------
    # Step 2 : Split Documents
    # --------------------------------------------------------------

    print("\nSplitting documents into chunks...")

    splitter = DocumentSplitter()

    chunks = splitter.split_documents(documents)

    print(f"Created {len(chunks)} chunks.")

    # --------------------------------------------------------------
    # Step 3 : Initialize Embedding Model
    # --------------------------------------------------------------

    print("\nLoading embedding model...")

    embedding_model = EmbeddingModel().get_embedding_model()

    print("Embedding model loaded successfully.")

    # --------------------------------------------------------------
    # Step 4 : Create Vector Store
    # --------------------------------------------------------------

    print("\nCreating Chroma Vector Database...")

    vector_store = VectorStoreManager(
        persist_directory=str(VECTOR_DB_PATH),
        collection_name=COLLECTION_NAME,
        embedding_model=embedding_model,
    )
    print(type(embedding_model))
    print(embedding_model)


    vector_store.create_vector_store(chunks[:10])

    # --------------------------------------------------------------
    # Success Message
    # --------------------------------------------------------------

    print("\n" + "=" * 60)
    print("Vector Database Created Successfully!")
    print("=" * 60)

    print(f"Documents Loaded : {len(documents)}")
    print(f"Chunks Created   : {len(chunks)}")
    print(f"Database Saved   : {VECTOR_DB_PATH}")


if __name__ == "__main__":
    main()
    