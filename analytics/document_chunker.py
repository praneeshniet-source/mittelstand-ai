def chunk_text(text, chunk_size=1000, overlap=150):
    """
    Split document text into overlapping chunks.
    Keeps paragraphs together where possible.
    """

    if not text or not text.strip():
        return []

    paragraphs = [
        paragraph.strip()
        for paragraph in text.split("\n")
        if paragraph.strip()
    ]

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:

        # Split very long paragraphs into smaller pieces.
        if len(paragraph) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            start = 0

            while start < len(paragraph):
                end = start + chunk_size
                piece = paragraph[start:end].strip()

                if piece:
                    chunks.append(piece)

                start += chunk_size - overlap

            continue

        # Add paragraph if it fits.
        if len(current_chunk) + len(paragraph) + 1 <= chunk_size:
            current_chunk += "\n" + paragraph

        else:
            if current_chunk:
                chunks.append(current_chunk.strip())

            # Carry some context into the next chunk.
            current_chunk = current_chunk[-overlap:] + "\n" + paragraph

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
