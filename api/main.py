
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config.settings import settings
from config.logging_config import configure_logging

from analytics.database import fetch_dataframe

from analytics.financial_assistant import (
    ask_financial_assistant,
    get_portfolio_metrics,
    get_customer_metrics,
    get_supplier_metrics,
    DEFAULT_REPORTING_DATE,
)

from analytics.rag_assistant import ask_document_question
from analytics.rag_pipeline import ingest_pdf


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

configure_logging()

logger = logging.getLogger("mittelstand_ai.api")

app = FastAPI(
    title=f"{settings.app_name} API",
    description="AI-powered financial operations and invoice analytics API.",
    version="1.0.0",
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

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


# ============================================================
# FINANCIAL QUESTION ROUTING
# ============================================================

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


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    logger.info("Health check requested.")

    return {
        "status": "healthy",
        "application": settings.app_name,
    }


# ============================================================
# FINANCIAL ANALYTICS
# ============================================================

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
        logger.exception(
            "Failed to retrieve supplier portfolio analytics."
        )

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


# ============================================================
# INVOICE MANAGEMENT
# ============================================================

@app.get("/invoices")
def list_invoices(
    search: str | None = Query(
        default=None,
        max_length=100,
        description="Search by invoice ID or supplier name",
    ),
    status: str | None = Query(
        default=None,
        description="Filter by Paid or Unpaid status",
    ),
    overdue_only: bool = Query(
        default=False,
        description="Show only overdue unpaid invoices",
    ),
    sort_by: str = Query(
        default="due_date",
        description="Sort by due_date, invoice_date or amount_eur",
    ),
    sort_order: str = Query(
        default="asc",
        description="Sort direction: asc or desc",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="Page number",
    ),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of invoices per page",
    ),
):
    """Retrieve searchable, filterable and paginated supplier invoices."""

    logger.info("Invoice list requested.")

    allowed_sort_columns = {
        "due_date": "due_date",
        "invoice_date": "invoice_date",
        "amount_eur": "amount_eur",
    }

    sort_column = allowed_sort_columns.get(sort_by.casefold())

    if sort_column is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid sort_by value. Use due_date, "
                "invoice_date or amount_eur."
            ),
        )

    direction = sort_order.casefold()

    if direction not in ("asc", "desc"):
        raise HTTPException(
            status_code=400,
            detail="sort_order must be asc or desc.",
        )

    normalized_status = None

    if status is not None:
        normalized_status = status.strip().casefold()

        if normalized_status not in ("paid", "unpaid"):
            raise HTTPException(
                status_code=400,
                detail="status must be Paid or Unpaid.",
            )

    conditions = []
    params = []

    if search and search.strip():
        search_term = f"%{search.strip()}%"

        conditions.append(
            """
            (
                invoice_id ILIKE %s
                OR supplier ILIKE %s
            )
            """
        )

        params.extend([search_term, search_term])

    if normalized_status:
        conditions.append(
            "LOWER(TRIM(status)) = %s"
        )
        params.append(normalized_status)

    if overdue_only:
        conditions.append(
            """
            LOWER(TRIM(status)) = 'unpaid'
            AND due_date < %s
            """
        )
        params.append(DEFAULT_REPORTING_DATE.date())

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions
        else ""
    )

    try:
        count_query = f"""
            SELECT COUNT(*) AS total
            FROM invoices
            {where_clause}
        """

        count_result = fetch_dataframe(
            count_query,
            tuple(params),
        )

        total_records = int(count_result.iloc[0]["total"])

        offset = (page - 1) * page_size

        invoice_query = f"""
            SELECT
                invoice_id,
                supplier,
                country,
                category,
                invoice_date,
                due_date,
                amount_eur,
                status,
                CASE
                    WHEN LOWER(TRIM(status)) = 'unpaid'
                     AND due_date < %s
                    THEN TRUE
                    ELSE FALSE
                END AS is_overdue
            FROM invoices
            {where_clause}
            ORDER BY {sort_column} {direction.upper()}, invoice_id ASC
            LIMIT %s OFFSET %s
        """

        query_params = [
            DEFAULT_REPORTING_DATE.date(),
            *params,
            page_size,
            offset,
        ]

        data = fetch_dataframe(
            invoice_query,
            tuple(query_params),
        )

        total_pages = (
            (total_records + page_size - 1) // page_size
        )

        logger.info(
            "Retrieved %s invoice records on page %s.",
            len(data),
            page,
        )

        return {
            "invoices": data.to_dict(orient="records"),
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_records": total_records,
                "total_pages": total_pages,
            },
            "filters": {
                "search": search,
                "status": normalized_status,
                "overdue_only": overdue_only,
                "sort_by": sort_by,
                "sort_order": direction,
            },
            "reporting_date": (
                DEFAULT_REPORTING_DATE.date().isoformat()
            ),
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Failed to retrieve invoice records.")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve invoice records.",
        )


# ============================================================
# AI ASSISTANT
# ============================================================

@app.post("/ai/ask")
def ask_ai(request: QuestionRequest):
    logger.info("AI question received.")

    try:
        if is_financial_question(request.question):
            logger.info("Routing question to financial assistant.")

            answer = ask_financial_assistant(request.question)

            logger.info(
                "Financial assistant completed successfully."
            )

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


# ============================================================
# PDF DOCUMENT UPLOAD
# ============================================================

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):

    if not file.filename:
        logger.warning(
            "Document upload rejected: missing filename."
        )

        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    if not file.filename.lower().endswith(".pdf"):
        logger.warning(
            "Document upload rejected: unsupported file type."
        )

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    upload_dir = Path(settings.upload_directory)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate a unique filename to prevent overwriting existing files.
    original_name = Path(file.filename).name

    unique_name = (
        f"{Path(original_name).stem}_{uuid4().hex[:8]}.pdf"
    )

    file_path = upload_dir / unique_name

    try:
        content = await file.read(
            settings.max_upload_size + 1
        )

        if len(content) > settings.max_upload_size:
            limit_mb = settings.max_upload_size / (1024 * 1024)

            logger.warning(
                "Document upload rejected: file exceeds size limit."
            )

            raise HTTPException(
                status_code=413,
                detail=(
                    f"File size exceeds the {limit_mb:g} MB upload limit."
                ),
            )

        if not content:
            logger.warning(
                "Document upload rejected: empty file."
            )

            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        if not content.startswith(b"%PDF-"):
            logger.warning(
                "Document upload rejected: invalid PDF signature."
            )

            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file.",
            )

        file_path.write_bytes(content)

        logger.info(
            "PDF saved. Starting document ingestion."
        )

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
        file_path.unlink(missing_ok=True)

        logger.exception(
            "Document ingestion failed due to invalid content."
        )

        raise HTTPException(
            status_code=400,
            detail="The uploaded document could not be processed.",
        )

    except Exception:
        file_path.unlink(missing_ok=True)

        logger.exception(
            "Unexpected document upload failure."
        )

        raise HTTPException(
            status_code=500,
            detail="Document upload failed due to an internal error.",
        )

    finally:
        await file.close()
