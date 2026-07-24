"""Document text extraction for PDF, DOCX, TXT, Markdown, CSV."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from docx import Document
from pypdf import PdfReader

SUPPORTED_DOCUMENT_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
    "text/markdown": "md",
    "text/csv": "csv",
    "application/csv": "csv",
}


def detect_document_kind(filename: str, content_type: str) -> str | None:
    if content_type in SUPPORTED_DOCUMENT_TYPES:
        return SUPPORTED_DOCUMENT_TYPES[content_type]
    suffix = Path(filename).suffix.lower().lstrip(".")
    mapping = {
        "pdf": "pdf",
        "docx": "docx",
        "txt": "txt",
        "md": "md",
        "markdown": "md",
        "csv": "csv",
    }
    return mapping.get(suffix)


def extract_text(data: bytes, kind: str) -> str:
    if kind == "pdf":
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages).strip()
    if kind == "docx":
        document = Document(io.BytesIO(data))
        return "\n".join(p.text for p in document.paragraphs if p.text).strip()
    if kind in {"txt", "md"}:
        return data.decode("utf-8", errors="replace").strip()
    if kind == "csv":
        text = data.decode("utf-8", errors="replace")
        csv_reader = csv.reader(io.StringIO(text))
        rows = [", ".join(row) for row in csv_reader]
        return "\n".join(rows).strip()
    raise ValueError(f"Unsupported document kind: {kind}")
