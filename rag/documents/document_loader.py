"""
document_loader.py

Purpose:
--------
This module is responsible for loading PDF documents from the
docs/raw directory and converting them into LangChain Document
objects while preserving metadata such as page number and source.

Author:
--------
Intelligent Credit Decision Support Platform
"""

from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader


class DocumentLoader:
    """
    Loads PDF documents from a directory or a single PDF file.
    """

    def __init__(self, documents_path: str):
        """
        Initialize the document loader.

        Args:
            documents_path (str): Path to the folder containing PDF files.
        """
        self.documents_path = Path(documents_path)

    def load_single_pdf(self, pdf_path: Path) -> List[Document]:
        """
        Load a single PDF file.

        Args:
            pdf_path (Path): Path to the PDF.

        Returns:
            List[Document]:
                List of LangChain Document objects,
                one for each page.
        """

        loader = PyPDFLoader(str(pdf_path))
        documents = loader.load()

        return documents

    def load_all_pdfs(self) -> List[Document]:
        """
        Load all PDF files from the directory.

        Returns:
            List[Document]:
                Combined list of Document objects.
        """

        all_documents = []

        pdf_files = sorted(self.documents_path.glob("*.pdf"))

        if not pdf_files:
            raise FileNotFoundError(
                f"No PDF files found in: {self.documents_path}"
            )

        for pdf_file in pdf_files:
            documents = self.load_single_pdf(pdf_file)
            all_documents.extend(documents)

        return all_documents


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parents[2]
    DOCS_PATH = BASE_DIR / "docs" / "raw"
    loader = DocumentLoader(DOCS_PATH)


    

    documents = loader.load_all_pdfs()

    print("=" * 60)
    print(f"Total Pages Loaded : {len(documents)}")
    print("=" * 60)

    if documents:
        print("\nFirst Page Preview\n")
        print(f"Source : {documents[0].metadata.get('source')}")
        print(f"Page   : {documents[0].metadata.get('page')}")
        print("-" * 60)
        print(documents[0].page_content[:500])



        