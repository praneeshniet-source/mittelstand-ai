
from pathlib import Path
import hashlib
import re

import chromadb

from analytics.pdf_extractor import extract_text_from_pdf
from analytics.document_chunker import chunk_text
from analytics.embedding_client import get_embedding


# Persistent vector database location
PROJECT_ROOT = Path(__file__).resolve().parents[1]
VECTOR_STORE_PATH = PROJECT_ROOT / "data" / "vector_store"

VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)

# Initialize ChromaDB
client = chromadb.PersistentClient(
    path=str(VECTOR_STORE_PATH)
)

collection = client.get_or_create_collection(
    name="mittelstand_documents",
    metadata={"hnsw:space": "cosine"}
)


def ingest_pdf(pdf_path):
    """Extract, chunk, embed and store a PDF document."""

    pdf_path = Path(pdf_path).resolve()

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    print(f"Processing: {pdf_path.name}")

    # Step 1: Extract PDF text
    text = extract_text_from_pdf(str(pdf_path))

    if not text.strip():
        raise ValueError("No text could be extracted from the PDF.")

    # Step 2: Split text into chunks
    chunks = chunk_text(text)

    if not chunks:
        raise ValueError("No document chunks were generated.")

    # Generate a stable document identifier
    source_hash = hashlib.sha256(
        str(pdf_path).encode("utf-8")
    ).hexdigest()[:12]

    ids = []
    embeddings = []
    metadatas = []

    # Step 3: Generate embeddings
    for index, chunk in enumerate(chunks):
        vector = get_embedding("search_document: " + chunk)

        ids.append(f"{source_hash}_{index}")
        embeddings.append(vector)

        metadatas.append({
            "source": pdf_path.name,
            "source_path": str(pdf_path),
            "chunk_index": index
        })

    # Step 4: Remove old chunks for this document
    existing_records = collection.get(
        where={"source_path": str(pdf_path)},
        include=["metadatas"]
    )

    if existing_records["ids"]:
        collection.delete(ids=existing_records["ids"])

    # Step 5: Store updated document chunks
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return {
        "source": pdf_path.name,
        "chunks_created": len(chunks),
        "stored_count": collection.count()
    }


def normalise_text(value):
    """Normalise text for reliable keyword and supplier matching."""
    return re.sub(r"[^a-z0-9]", "", value.lower())


def search_documents(question, top_k=3):
    """Retrieve document chunks using supplier-aware hybrid search."""

    if not question or not question.strip():
        raise ValueError("Search question cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    total_documents = collection.count()

    if total_documents == 0:
        return []

    # Step 1: Semantic retrieval
    query_vector = get_embedding("search_query: " + question)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=total_documents,
        include=["documents", "metadatas", "distances"]
    )

    candidates = []

    for index in range(len(results["ids"][0])):
        candidates.append({
            "document": results["documents"][0][index],
            "source": results["metadatas"][0][index]["source"],
            "source_path": results["metadatas"][0][index]["source_path"],
            "chunk_index": results["metadatas"][0][index]["chunk_index"],
            "distance": results["distances"][0][index]
        })

    # Step 2: Extract the requested supplier name
    # Prioritise "from" to avoid matching an earlier "of"
    supplier_reference = re.search(
        r"\bfrom\s+(.+?)[?.!]*$",
        question,
        re.IGNORECASE
    )

    # Fallback for questions using "for" or "of"
    if not supplier_reference:
        supplier_reference = re.search(
            r"\b(?:for|of)\s+(?:the\s+)?(?:supplier\s+)?(.+?)[?.!]*$",
            question,
            re.IGNORECASE
        )

    requested_supplier = (
        supplier_reference.group(1).strip()
        if supplier_reference else None
    )

    normalised_supplier = (
        normalise_text(requested_supplier)
        if requested_supplier else None
    )

    # Step 3: Keyword matching
    stop_words = {
        "which", "invoice", "belongs", "belong", "to",
        "what", "is", "the", "a", "an", "of", "for",
        "find", "who", "issued", "by", "and", "number",
        "account", "bank", "give", "me", "from"
    }

    question_terms = {
        term.lower().strip(".,?!:;()[]{}")
        for term in question.split()
        if (
            len(term.strip(".,?!:;()[]{}")) >= 3
            and term.lower().strip(".,?!:;()[]{}") not in stop_words
        )
    }

    for candidate in candidates:
        document_text = candidate["document"].lower()

        matched_terms = [
            term for term in question_terms
            if term in document_text
        ]

        candidate["keyword_matches"] = len(matched_terms)
        candidate["matched_terms"] = matched_terms

        # Exact supplier-name matching
        normalised_document = normalise_text(candidate["document"])

        candidate["supplier_match"] = bool(
            normalised_supplier
            and normalised_supplier in normalised_document
        )

    # Step 4: Invoice identifier matching
    identifier_pattern = (
        r"\b[A-Z]{2,5}-\d{3,4}(?:-\d{3,4})?\b"
    )

    question_identifiers = {
        identifier.upper()
        for identifier in re.findall(
            identifier_pattern,
            question.upper()
        )
    }

    for candidate in candidates:
        document_text = candidate["document"].upper()

        candidate["identifier_match"] = any(
            identifier in document_text
            for identifier in question_identifiers
        )

    # Step 5: Hybrid ranking
    candidates.sort(
        key=lambda item: (
            -int(item["identifier_match"]),
            -int(item["supplier_match"]),
            -item["keyword_matches"],
            item["distance"]
        )
    )

    return candidates[:min(top_k, len(candidates))]
