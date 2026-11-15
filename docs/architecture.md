# Mittelstand AI — System Architecture

**Project:** AI-Powered Financial Operations Assistant
**Status:** Prototype / Backend foundation
**Version:** 1.0

---

## 1. Project Overview

Mittelstand AI is an AI-powered financial operations assistant designed for small and medium-sized enterprises (SMEs).

The system combines traditional financial analytics, document processing, vector search and locally hosted language models.

Its primary capabilities are:

- Supplier invoice analytics and accounts payable monitoring.
- Customer receivables analytics.
- Overdue payment identification.
- Cash-flow and financial insights.
- PDF invoice extraction and OCR.
- Evidence-based document question answering.
- AI-assisted financial explanations.

The system separates deterministic financial calculations from generative AI responses.

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Programming language | Python |
| API framework | FastAPI |
| Data processing | Pandas |
| Relational database | PostgreSQL |
| Database driver | Psycopg |
| Vector database | ChromaDB |
| Embedding model | Nomic Embed Text |
| Language model | Qwen 2.5 1.5B |
| Local AI runtime | Ollama |
| PDF extraction | PyMuPDF |
| OCR | Tesseract / Pytesseract |
| Image processing | Pillow |
| Configuration | Pydantic Settings |
| Logging | Python logging with JSON formatter |
| Existing dashboard | Streamlit |

## 3. High-Level Architecture

The system consists of five main layers:

1. API layer — receives user requests and returns responses.
2. Business logic layer — performs financial calculations and document processing.
3. Data layer — stores structured invoice data and document embeddings.
4. AI layer — generates embeddings and natural-language responses.
5. Configuration and observability layer — manages application settings and structured logs.

### Architecture flow

```text
                    USER
                     |
                     v
                FASTAPI API
                     |
          +----------+----------+
          |                     |
          v                     v
   FINANCIAL ANALYTICS     DOCUMENT INTELLIGENCE
          |                     |
          v                     v
     POSTGRESQL             PDF EXTRACTION
          |                     |
          v                     v
   PANDAS CALCULATIONS      TEXT CHUNKING
          |                     |
          v                     v
   VERIFIED METRICS       EMBEDDING GENERATION
          |                     |
          |                     v
          |                  CHROMADB
          |                     |
          |                     v
          |                RAG RETRIEVAL
          |                     |
          |                     v
          |              EVIDENCE VALIDATION
          |                     |
          |                     v
          |                OLLAMA / QWEN
          |                     |
          +----------+----------+
                     |
                     v
                API RESPONSE
```

## 4. PostgreSQL Data Model

The current PostgreSQL database contains two main tables.

### 4.1 Supplier invoices — `invoices`

Represents invoices received by the business from suppliers.

| Column | Data type | Nullable |
|---|---|---|
| invoice_id | VARCHAR | No |
| supplier | VARCHAR | No |
| country | VARCHAR | Yes |
| category | VARCHAR | Yes |
| invoice_date | DATE | No |
| due_date | DATE | No |
| amount_eur | NUMERIC | No |
| status | VARCHAR | No |

Primary key: `invoice_id`

### 4.2 Customer invoices — `customer_invoices`

Represents invoices issued by the business to customers.

| Column | Data type | Nullable |
|---|---|---|
| invoice_id | VARCHAR | No |
| customer | VARCHAR | No |
| country | VARCHAR | Yes |
| category | VARCHAR | Yes |
| invoice_date | DATE | No |
| due_date | DATE | No |
| amount_eur | NUMERIC | No |
| status | VARCHAR | No |
| payment_date | DATE | Yes |

Primary key: `invoice_id`

### 4.3 Database constraints

Both tables enforce:

- Unique invoice identifiers through primary keys.
- Status values restricted to `Paid` and `Unpaid`.
- Invoice amounts greater than or equal to zero.
- NOT NULL constraints on mandatory fields.

No foreign-key relationships were found in the inspected schema.

The schema was inspected directly from the running PostgreSQL database. A dedicated schema creation script has not yet been identified in the current source tree.

## 5. API Architecture

FastAPI provides the backend HTTP interface.

### 5.1 API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Application health check |
| GET | `/analytics/overview` | Supplier portfolio analytics |
| GET | `/analytics/customers` | Customer receivables analytics |
| GET | `/analytics/suppliers/{supplier}` | Individual supplier analytics |
| POST | `/ai/ask` | Financial and document question answering |
| POST | `/documents/upload` | PDF document upload and ingestion |

### 5.2 AI question request

The `/ai/ask` endpoint accepts:

- `question`: 3–1,000 characters.
- `top_k`: Number of retrieved document chunks, between 1 and 10; default is 3.

The API uses keyword-based question classification to select the financial assistant or document RAG assistant.

### 5.3 Document upload validation

The `/documents/upload` endpoint currently:

- Accepts PDF files only.
- Enforces a configurable maximum upload size (10 MB by default).
- Rejects empty files.
- Checks the PDF file signature.
- Generates unique filenames.
- Removes saved files when ingestion fails.
- Closes uploaded files after processing.

## 6. Financial Analytics Architecture

The financial assistant uses PostgreSQL and Pandas to calculate financial metrics.

### Supplier analytics

The supplier analytics module calculates:

- Total supplier invoice count.
- Total invoice value.
- Paid invoice value.
- Unpaid supplier exposure.
- Overdue supplier exposure.
- Unpaid invoices that are not yet due.
- Individual supplier metrics.

### Customer analytics

The customer analytics module supports:

- Customer-level receivables.
- Outstanding balances.
- Overdue customer invoices.
- Collected payment amounts.
- Highest outstanding customer.
- Average payment delay.

### Financial question processing

The financial assistant attempts deterministic answers first:

1. Identify a customer mentioned in the question.
2. Calculate customer-specific metrics.
3. Check customer portfolio questions.
4. Identify a supplier mentioned in the question.
5. Calculate supplier-specific metrics.
6. Check supplier portfolio questions.
7. Use verified financial context with Ollama as a fallback.

Financial calculations are not delegated to the language model.

**Reporting date:** The current implementation uses a fixed reporting date of `2026-10-27` in its financial assistant configuration.

## 7. Document Intelligence and RAG Architecture

The document intelligence pipeline allows users to ask questions about uploaded business documents.

### 7.1 Document ingestion

```text
PDF UPLOAD
    |
    v
PDF TEXT EXTRACTION
    |
    v
OCR FOR SCANNED PAGES
    |
    v
TEXT CHUNKING
    |
    v
NOMIC EMBEDDINGS
    |
    v
CHROMADB STORAGE
```

The chunking implementation currently uses:

- Chunk size: 1,000 characters.
- Overlap: 150 characters.

### 7.2 Document retrieval

The retrieval process combines:

- Semantic similarity using embeddings.
- Keyword matching.
- Supplier-name matching.
- Invoice identifier matching.
- Hybrid candidate ranking.

The final results are limited by the requested `top_k` value.

### 7.3 Evidence validation

Before generating an answer, the evidence validator checks:

1. Whether the question is empty.
2. Whether an exact invoice identifier is present.
3. Whether the requested invoice field is recognised.
4. Whether retrieved documents contain relevant field evidence.
5. Whether the requested supplier can be matched.

Recognised invoice fields include invoice number, supplier, invoice date, due date, amount and bank account.

English and German invoice terminology is supported in the validation patterns.

### 7.4 Answer generation

The RAG assistant:

1. Retrieves document chunks.
2. Validates supporting evidence.
3. Builds document context.
4. Creates a grounded prompt.
5. Sends the prompt to the local Qwen model through Ollama.
6. Returns an answer and source filenames.

The prompt instructs the model not to invent facts and not to treat document content as instructions.

## 8. Configuration and Logging

### Configuration

Application configuration is centralised in `config/settings.py`.

Pydantic Settings loads environment variables and supports a local `.env` file.

The configuration covers:

- Application name and environment.
- PostgreSQL connection settings.
- Ollama URL, model and timeout.
- Embedding model and dimensions.
- Upload size and directory.
- ChromaDB storage path and collection name.

A `.env.example` file provides the configuration template.

### Logging

`config/logging_config.py` provides structured JSON logging.

Log entries include:

- Timestamp.
- Log level.
- Logger name.
- Message.
- Exception details when available.

Application logging is configured under the `mittelstand_ai` logger namespace.

## 9. Current Limitations

The current prototype has several areas for improvement:

1. Financial reporting dates are currently fixed rather than dynamically determined.
2. Question routing uses keyword-based classification.
3. Document retrieval currently evaluates all stored candidates before selecting the final results.
4. Document identity is derived from the file path rather than document content.
5. Database schema creation and migration scripts need to be formalised.
6. The current application does not yet implement enterprise approval workflows or role-based access control.
7. External enterprise integrations such as Jira and Confluence are not yet implemented.

These are recognised development opportunities, not features claimed as complete.

## 10. Planned Architecture Extensions

The planned development roadmap includes:

- React and TypeScript frontend.
- Jira and Confluence integration using an MCP-first architecture.
- Common AI provider interface for Ollama, OpenAI and Claude.
- AI tool orchestration.
- Workflow engine.
- Human approval mechanisms.
- Role-based access control.
- Audit logging.
- Docker-based deployment.
- Enterprise-oriented end-to-end testing.

The intended future business workflow is to combine invoice evidence, financial analytics, external business context and approved actions into a traceable financial operations process.

## 11. Project Status

The project has completed its initial analytics, database, RAG foundation and FastAPI backend development.

The current implementation demonstrates:

- Structured financial analysis.
- PostgreSQL-backed invoice analytics.
- PDF document intelligence.
- Evidence-validated RAG.
- Local language-model integration.
- API-based access to financial and document intelligence.
- Centralised configuration and structured logging.

The next development phase focuses on frontend development and enterprise integration capabilities.

---

**Document classification:** Technical project documentation
**Project:** Mittelstand AI
