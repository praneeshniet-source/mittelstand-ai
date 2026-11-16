
# Mittelstand AI — System Architecture

**Project:** AI-Powered Financial Operations Assistant

**Status:** Active prototype / React frontend and FastAPI backend

**Version:** 1.1

**Last updated:** 16 November 2026

---

## 1. Project Overview

Mittelstand AI is an AI-powered financial operations assistant designed for small and medium-sized enterprises (SMEs).

The system combines financial analytics, invoice processing, document intelligence, vector search, and locally hosted language models through a modular architecture.

Its primary capabilities include:

- Supplier invoice analytics and accounts payable monitoring.
- Customer receivables analytics.
- Overdue payment identification.
- Cash-flow and financial insights.
- PDF invoice extraction and OCR.
- Evidence-based document question answering.
- AI-assisted financial explanations.
- Interactive financial dashboards.
- Invoice search, filtering, sorting, and pagination.
- Natural-language financial question answering through POKO.

The system separates deterministic financial calculations from generative AI responses. Financial metrics are calculated using structured data rather than relying on language-model estimates.

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Programming language | Python 3.12 |
| Backend API | FastAPI, Uvicorn |
| Frontend framework | React 19 |
| Frontend language | TypeScript |
| Frontend build tool | Vite |
| Frontend styling | Tailwind CSS 4 |
| Data visualisation | Recharts |
| UI icons | Lucide React |
| Data processing | Pandas |
| Relational database | PostgreSQL |
| Database driver | Psycopg 3 |
| Vector database | ChromaDB |
| Embedding model | Nomic Embed Text |
| Language model | Qwen 2.5 1.5B |
| Local AI runtime | Ollama |
| PDF extraction | PyMuPDF |
| OCR | Tesseract / Pytesseract |
| Image processing | Pillow |
| Configuration | Pydantic Settings |
| Logging | Python logging with JSON-formatted output |
| Legacy dashboard | Streamlit |
| API communication | Fetch API |

## 3. High-Level Architecture

The system consists of six logical layers:

1. Presentation layer — React frontend and existing Streamlit dashboard.
2. API layer — FastAPI endpoints for financial analytics, invoices, and AI questions.
3. Business logic layer — financial calculations, invoice processing, and document intelligence.
4. Data layer — PostgreSQL for structured financial records and ChromaDB for document embeddings.
5. AI layer — embeddings, document retrieval, evidence validation, and language-model responses.
6. Configuration and observability layer — centralised settings and structured logging.

### 3.1 Architecture flow

```text
                   USER
                     |
          +----------+----------+
          |                     |
          v                     v
    REACT FRONTEND         STREAMLIT
          |               DASHBOARD
          |                     |
          +----------+----------+
                     |
                     v
                 FASTAPI
                     |
          +----------+----------+
          |                     |
          v                     v
   FINANCIAL OPERATIONS    DOCUMENT INTELLIGENCE
          |                     |
          v                     v
     POSTGRESQL             PDF EXTRACTION
          |                     |
          v                     v
   PANDAS CALCULATIONS      TEXT CHUNKING
          |                     |
          v                     v
    VERIFIED METRICS      EMBEDDING GENERATION
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
                     |
                     v
               REACT / POKO
```

### 3.2 Frontend architecture

The React frontend communicates with the FastAPI backend over HTTP.

The frontend currently contains:

- Financial overview dashboard.
- Portfolio KPI cards.
- Invoice portfolio visualisation.
- Payment composition visualisation.
- Risk overview.
- Invoice Explorer.
- POKO financial assistant.

The frontend uses React state and effects to manage API requests, loading states, filters, pagination, and assistant conversations.

The API base URL can be configured using `VITE_API_BASE_URL`. The development configuration defaults to `http://localhost:8000`.

Cross-origin requests are configured for the local Vite development origins.

## 4. PostgreSQL Data Model

The current PostgreSQL database contains two main invoice tables.

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
| GET | `/invoices` | Searchable and filterable invoice explorer |
| POST | `/ai/ask` | Financial and document question answering |
| POST | `/documents/upload` | PDF document upload and ingestion |

### 5.2 Invoice Explorer endpoint

The `GET /invoices` endpoint provides paginated access to supplier invoice records.

Supported query parameters:

| Parameter | Description |
|---|---|
| `search` | Searches invoice identifiers and supplier names |
| `status` | Filters by Paid or Unpaid status |
| `overdue_only` | Returns overdue unpaid invoices when enabled |
| `sort_by` | Sorts by due date, invoice date, or amount |
| `sort_order` | Ascending or descending order |
| `page` | Requested page number |
| `page_size` | Number of records per page, maximum 100 |

The endpoint validates sorting fields using an allowlist and uses parameterised SQL values for filtering.

The response includes:

- Invoice records.
- Pagination metadata.
- Applied filter information.
- Reporting date.
- An `is_overdue` indicator for each invoice.

Pagination metadata includes page number, page size, total record count, and total page count.

### 5.3 AI question request

The `/ai/ask` endpoint accepts:

- `question`: 3–1,000 characters.
- `top_k`: Number of retrieved document chunks, between 1 and 10; default is 3.

The API uses keyword-based question classification to select the financial assistant or document RAG assistant.

### 5.4 Document upload validation

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

### 6.1 Supplier analytics

The supplier analytics module calculates:

- Total supplier invoice count.
- Total invoice value.
- Paid invoice value.
- Unpaid supplier exposure.
- Overdue supplier exposure.
- Unpaid invoices that are not yet due.
- Individual supplier metrics.

### 6.2 Customer analytics

The customer analytics module supports:

- Customer-level receivables.
- Outstanding balances.
- Overdue customer invoices.
- Collected payment amounts.
- Highest outstanding customer.
- Average payment delay.

### 6.3 Financial question processing

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

## 7. POKO — Financial Operations Companion

POKO is the conversational assistant interface integrated into the React frontend.

Its current role is to provide natural-language access to the financial question-answering API.

POKO supports questions about:

- Overdue invoices.
- Outstanding payments.
- Supplier exposure.
- Invoice portfolio metrics.
- Financial business questions supported by the backend.

The frontend sends questions to the `/ai/ask` endpoint and displays the returned answer in a conversational interface.

POKO is currently an interface and identity for the existing financial assistant. It does not yet represent a separate autonomous agent or an enterprise workflow execution engine.

Financial answers should remain grounded in backend calculations and available records.

## 8. Document Intelligence and RAG Architecture

The document intelligence pipeline allows users to ask questions about uploaded business documents.

### 8.1 Document ingestion

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

### 8.2 Document retrieval

The retrieval process combines:

- Semantic similarity using embeddings.
- Keyword matching.
- Supplier-name matching.
- Invoice identifier matching.
- Hybrid candidate ranking.

The final results are limited by the requested `top_k` value.

### 8.3 Evidence validation

Before generating an answer, the evidence validator checks:

1. Whether the question is empty.
2. Whether an exact invoice identifier is present.
3. Whether the requested invoice field is recognised.
4. Whether retrieved documents contain relevant field evidence.
5. Whether the requested supplier can be matched.

Recognised invoice fields include invoice number, supplier, invoice date, due date, amount and bank account.

English and German invoice terminology is supported in the validation patterns.

### 8.4 Answer generation

The RAG assistant:

1. Retrieves document chunks.
2. Validates supporting evidence.
3. Builds document context.
4. Creates a grounded prompt.
5. Sends the prompt to the local Qwen model through Ollama.
6. Returns an answer and source filenames.

The prompt instructs the model not to invent facts and not to treat document content as instructions.

## 9. Configuration and Logging

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

The frontend API base URL is configured through `VITE_API_BASE_URL`.

### Logging

`config/logging_config.py` provides structured JSON logging.

Log entries include:

- Timestamp.
- Log level.
- Logger name.
- Message.
- Exception details when available.

Application logging is configured under the `mittelstand_ai` logger namespace.

## 10. Current Limitations

The current prototype has several areas for improvement:

1. Financial reporting dates are currently fixed rather than dynamically determined.
2. Question routing uses keyword-based classification.
3. Document retrieval currently evaluates all stored candidates before selecting the final results.
4. Document identity is derived from the file path rather than document content.
5. Database schema creation and migration scripts need to be formalised.
6. The current application does not yet implement enterprise approval workflows or role-based access control.
7. External enterprise integrations such as Jira and Confluence are not yet implemented.
8. The frontend currently depends on the FastAPI backend being available.
9. The production JavaScript bundle currently exceeds Vite's default 500 kB warning threshold and needs code-splitting optimisation.
10. The application does not yet provide production authentication or multi-tenant data isolation.

These are recognised development opportunities, not features claimed as complete.

## 11. Planned Architecture Extensions

The planned development roadmap includes:

- Jira and Confluence integration using an MCP-first architecture.
- Common AI provider interface for Ollama, OpenAI and Claude.
- AI tool orchestration.
- Workflow engine.
- Human approval mechanisms.
- Role-based access control.
- Audit logging.
- Docker-based deployment.
- Enterprise-oriented end-to-end testing.
- Frontend performance optimisation.
- Automated financial operations workflows.

The intended future business workflow is to combine invoice evidence, financial analytics, external business context and approved actions into a traceable financial operations process.

## 12. Project Status

The project has completed its initial analytics, database, RAG foundation, FastAPI backend and React frontend foundation.

The current implementation demonstrates:

- Structured financial analysis.
- PostgreSQL-backed invoice analytics.
- PDF document intelligence.
- Evidence-validated RAG.
- Local language-model integration.
- API-based access to financial and document intelligence.
- Centralised configuration and structured logging.
- React and TypeScript financial dashboard.
- Invoice search, filtering, sorting and pagination.
- POKO financial assistant interface.
- Frontend and backend integration.

The next development phase focuses on frontend refinement, Jira and Confluence integration, multi-provider AI architecture and enterprise workflow capabilities.

---

**Document classification:** Technical project documentation

**Project:** Mittelstand AI
