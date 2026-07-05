"""
text_splitter.py

Purpose:
--------
This module splits LangChain Document objects into smaller,
overlapping chunks suitable for embedding generation.

Author:
-------
Intelligent Credit Decision Support Platform
"""

from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentSplitter:
    """
    Splits documents into smaller chunks while preserving metadata.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Initialize the text splitter.

        Args:
            chunk_size (int):
                Maximum number of characters in each chunk.

            chunk_overlap (int):
                Number of overlapping characters between chunks.
        """

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                ""
            ]
        )

    def split_documents(
        self,
        documents: List[Document]
    ) -> List[Document]:
        """
        Split documents into smaller chunks.

        Args:
            documents:
                List of LangChain Document objects.

        Returns:
            List of chunked Document objects.
        """

        chunks = self.splitter.split_documents(documents)

        return chunks


if __name__ == "__main__":

    from document_loader import DocumentLoader
    from pathlib import Path

    BASE_DIR = Path(__file__).resolve().parents[2]

    DOCS_PATH = BASE_DIR / "docs" / "raw"

    loader = DocumentLoader(DOCS_PATH)

    documents = loader.load_all_pdfs()

    splitter = DocumentSplitter()

    chunks = splitter.split_documents(documents)

    print("=" * 60)
    print(f"Original Pages : {len(documents)}")
    print(f"Total Chunks   : {len(chunks)}")
    print("=" * 60)

    if chunks:

        print("\nFirst Chunk\n")

        print(f"Source : {chunks[0].metadata.get('source')}")
        print(f"Page   : {chunks[0].metadata.get('page')}")

        print("-" * 60)

        print(chunks[0].page_content)