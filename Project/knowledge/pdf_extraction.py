"""Gets the text out of the PDFs and does nothing else with it."""

import os

from pypdf import PdfReader


def extract_text_from_directory(docs_directory):
    """Read every PDF in the folder once, in a settled (alphabetical) order."""
    document_names = sorted(name for name in os.listdir(docs_directory)
                            if name.lower().endswith(".pdf")
                            and os.path.isfile(os.path.join(docs_directory, name)))
    documents = []
    for document_name in document_names:
        reader = PdfReader(os.path.join(docs_directory, document_name))
        page_texts = [(page.extract_text() or "").strip() for page in reader.pages]
        documents.append({
            "document_name": document_name,
            "document_text": "\n\n".join(page_texts),
        })
    return documents
