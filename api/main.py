
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from config.settings import settings
from config.logging_config import configure_logging

from analytics.financial_assistant import (
    ask_financial_assistant,
    get_portfolio_metrics,
    get_customer_metrics,
    get_supplier_metrics,
)
from analytics.rag_assistant import ask_document_question
from analytics.rag_pipeline import ingest_pdf


# Configure application-wide structured logging.
configure_logging()
logger = logging.getLogger("mittelstand_ai.api")


app = FastAPI(
    title=f"{settings.app_name} API",
    description="AI-powered financial operations and invoice analytics API.",
    version="1.0.0",
)


class QuestionRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000,
        description="Financial or uploaded-document question",
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of document chunks to retrieve",
    )


def is_financial_question(question: str) -> bool:
    """Identify questions requiring financial data or calculations."""

    q = question.casefold()

    financial_terms = (
        "overdue",
        "unpaid",
        "outstanding",
        "receivable",
        "receivables",
        "collected",
        "cash flow",
        "cash position",
        "cash balance",
        "highest unpaid",
        "highest overdue",
        "largest unpaid",
        "largest overdue",
        "payment delay",
        "owe us",
        "owes us",
        "owed to us",
        "supplier exposure",
        "customer exposure",
        "total invoiced",
        "total invoice value",
        "paid invoice value",
        "how much does",
    )

    return any(term in q for term in financial_terms)


@app.get("/health")
def health_check():
    logger.info("Health check requested.")

    return {
        "status": "healthy",
        "application": settings.app_name,
    }


@app.get("/analytics/overview")
def analytics_overview():
    logger.info("Supplier portfolio analytics requested.")

    try:
        metrics = get_portfolio_metrics()

        if metrics is None:
            raise HTTPException(
                status_code=404,
                detail="No supplier invoice data available.",
            )

        logger.info("Supplier portfolio analytics retrieved successfully.")
        return metrics

    except HTTPException:
        raise

    except Exception:
        logger.exception("Failed to retrieve supplier portfolio analytics.")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve supplier analytics.",
        )


@app.get("/analytics/customers")
def customer_analytics():
    logger.info("Customer analytics requested.")

    try:
        metrics = get_customer_metrics()

        if metrics is None:
            raise HTTPException(
                status_code=404,
                detail="No customer invoice data available.",
            )

        logger.info("Customer analytics retrieved successfully.")
        return metrics

    except HTTPException:
        raise

    except Exception:
        logger.exception("Failed to retrieve customer analytics.")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve customer analytics.",
        )


@app.post("/ai/ask")
def ask_ai(request: QuestionRequest):
    logger.info("AI question received.")

    try:
        if is_financial_question(request.question):
            logger.info("Routing question to financial assistant.")

            answer = ask_financial_assistant(request.question)

            logger.info("Financial assistant completed successfully.")

            return {
                "answer": answer,
                "sources": [],
            }

        logger.info("Routing question to document RAG assistant.")

        result = ask_document_question(
            request.question,
            top_k=request.top_k,
        )

        logger.info("Document question processed successfully.")

        return result

    except Exception:
        logger.exception("AI question processing failed.")

        raise HTTPException(
            status_code=500,
            detail="Unable to process the AI question.",
        )


@app.get("/analytics/suppliers/{supplier}")
def supplier_analytics(supplier: str):
    logger.info("Supplier analytics requested.")

    try:
        metrics = get_supplier_metrics(supplier)

        if metrics is None:
            raise HTTPException(
                status_code=404,
                detail=f"No invoice data found for supplier: {supplier}",
            )

        logger.info("Supplier analytics retrieved successfully.")
        return metrics

    except HTTPException:
        raise

    except Exception:
        logger.exception("Failed to retrieve supplier analytics.")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve supplier analytics.",
        )


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        logger.warning("Document upload rejected: missing filename.")

        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    if not file.filename.lower().endswith(".pdf"):
        logger.warning("Document upload rejected: unsupported file type.")

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    upload_dir = Path(settings.upload_directory)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate a unique filename to prevent overwriting existing files.
    original_name = Path(file.filename).name
    unique_name = f"{Path(original_name).stem}_{uuid4().hex[:8]}.pdf"
    file_path = upload_dir / unique_name

    try:
        content = await file.read(settings.max_upload_size + 1)

        if len(content) > settings.max_upload_size:
            limit_mb = settings.max_upload_size / (1024 * 1024)

            logger.warning("Document upload rejected: file exceeds size limit.")

            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds the {limit_mb:g} MB upload limit.",
            )

        if not content:
            logger.warning("Document upload rejected: empty file.")

            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        if not content.startswith(b"%PDF-"):
            logger.warning("Document upload rejected: invalid PDF signature.")

            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file.",
            )

        file_path.write_bytes(content)

        logger.info("PDF saved. Starting document ingestion.")

        result = ingest_pdf(file_path)

        logger.info(
            "Document uploaded and indexed successfully: %s",
            unique_name,
        )

        return {
            "message": "Document uploaded and indexed successfully.",
            **result,
        }

    except HTTPException:
        raise

    except ValueError:
        # Remove the saved file if document validation or ingestion fails.
        file_path.unlink(missing_ok=True)

        logger.exception("Document ingestion failed due to invalid content.")

        raise HTTPException(
            status_code=400,
            detail="The uploaded document could not be processed.",
        )

    except Exception:
        # Remove incomplete uploads after unexpected failures.
        file_path.unlink(missing_ok=True)

        logger.exception("Unexpected document upload failure.")

        raise HTTPException(
            status_code=500,
            detail="Document upload failed due to an internal error.",
        )

    finally:
        await file.close()
