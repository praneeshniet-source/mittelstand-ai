from pathlib import Path
import hashlib

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

    # Step 4: Store in ChromaDB
    collection.upsert(
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



def search_documents(question, top_k=3):
    """Retrieve document chunks using hybrid semantic and keyword search."""

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

    # Step 2: Keyword matching
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

    # Step 3: Hybrid ranking
    candidates.sort(
        key=lambda item: (
            -item["keyword_matches"],
            item["distance"]
        )
    )

    return candidates[:min(top_k, len(candidates))]
