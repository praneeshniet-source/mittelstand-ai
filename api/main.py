
from uuid import uuid4
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from analytics.financial_assistant import (
    get_portfolio_metrics,
    get_customer_metrics,
    get_supplier_metrics,
)
from analytics.rag_assistant import ask_document_question
from analytics.rag_pipeline import ingest_pdf


MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

app = FastAPI(
    title="Mittelstand AI API",
    description="AI-powered financial operations and invoice analytics API.",
    version="1.0.0",
)


class QuestionRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000,
        description="Question about the uploaded invoice documents",
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of document chunks to retrieve",
    )


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "Mittelstand AI",
    }


@app.get("/analytics/overview")
def analytics_overview():
    try:
        metrics = get_portfolio_metrics()

        if metrics is None:
            raise HTTPException(
                status_code=404,
                detail="No supplier invoice data available.",
            )

        return metrics

    except HTTPException:
        raise
    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/analytics/customers")
def customer_analytics():
    try:
        metrics = get_customer_metrics()

        if metrics is None:
            raise HTTPException(
                status_code=404,
                detail="No customer invoice data available.",
            )

        return metrics

    except HTTPException:
        raise
    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/ai/ask")
def ask_ai(request: QuestionRequest):
    try:
        return ask_document_question(
            request.question,
            top_k=request.top_k,
        )

    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/analytics/suppliers/{supplier}")
def supplier_analytics(supplier: str):
    try:
        metrics = get_supplier_metrics(supplier)

        if metrics is None:
            raise HTTPException(
                status_code=404,
                detail=f"No invoice data found for supplier: {supplier}",
            )

        return metrics

    except HTTPException:
        raise
    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate a unique filename to prevent overwriting existing files.
    original_name = Path(file.filename).name
    unique_name = f"{Path(original_name).stem}_{uuid4().hex[:8]}.pdf"
    file_path = upload_dir / unique_name

    try:
        content = await file.read(MAX_UPLOAD_SIZE + 1)

        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File size exceeds the 10 MB upload limit.",
            )

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file.",
            )

        file_path.write_bytes(content)

        result = ingest_pdf(file_path)

        return {
            "message": "Document uploaded and indexed successfully.",
            **result,
        }

    except HTTPException:
        raise

    except (FileNotFoundError, ValueError) as error:
        # Remove the saved file if ingestion fails.
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    finally:
        await file.close()
