"""
build_chunk_store.py

Purpose
-------
Builds and stores chunked documents.

Workflow
--------
PDF Documents
      │
      ▼
Document Loader
      │
      ▼
Document Splitter
      │
      ▼
Save chunks.pkl

Author
------
Intelligent Credit Decision Support Platform
"""

import pickle
from pathlib import Path

from rag.documents.document_loader import DocumentLoader
from rag.documents.text_splitter import DocumentSplitter


class ChunkStoreBuilder:
    """
    Creates and stores chunked documents.
    """

    def __init__(self):

        self.base_dir = Path(__file__).resolve().parents[2]

        self.raw_docs_path = self.base_dir / "docs" / "raw"

        self.chunk_store_path = self.base_dir / "docs" / "chunks"

        self.chunk_file = self.chunk_store_path / "chunks.pkl"

    def build(self):
        """
        Build chunk store.
        """

        print("=" * 70)
        print("BUILDING CHUNK STORE")
        print("=" * 70)

        # -------------------------------------
        # Load PDFs
        # -------------------------------------

        loader = DocumentLoader(self.raw_docs_path)

        documents = loader.load_all_pdfs()

        print(f"\nLoaded Pages : {len(documents)}")

        # -------------------------------------
        # Split Documents
        # -------------------------------------

        splitter = DocumentSplitter()

        chunks = splitter.split_documents(documents)

        print(f"Generated Chunks : {len(chunks)}")

        # -------------------------------------
        # Create Folder
        # -------------------------------------

        self.chunk_store_path.mkdir(
            parents=True,
            exist_ok=True
        )

        # -------------------------------------
        # Save Chunks
        # -------------------------------------

        with open(self.chunk_file, "wb") as file:

            pickle.dump(chunks, file)

        print("\nChunk Store Saved Successfully")

        print(f"\nLocation : {self.chunk_file}")

        print("=" * 70)

        return chunks


if __name__ == "__main__":

    builder = ChunkStoreBuilder()

    chunks = builder.build()

    print("\nFirst Chunk Preview\n")

    print("-" * 70)

    print(chunks[0].page_content[:500])

    print("\nMetadata")

    print(chunks[0].metadata)