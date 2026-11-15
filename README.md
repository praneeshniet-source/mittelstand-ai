
# Mittelstand AI

**AI-Powered Financial Operations Assistant for Small and Medium-Sized Enterprises (SMEs)**

Mittelstand AI is an educational portfolio project exploring how AI and data analytics can support financial operations in small and medium-sized enterprises.

The prototype combines structured financial analytics, invoice processing, document retrieval, and locally hosted language models to help users investigate financial information and understand business documents.

## Project Objectives

- Analyse supplier invoices and customer receivables.
- Identify overdue invoices and outstanding payments.
- Monitor supplier spending and payment patterns.
- Analyse short-term cash flow.
- Detect potentially unusual invoice records.
- Extract information from digital and scanned PDF invoices.
- Retrieve relevant information from business documents using Retrieval-Augmented Generation (RAG).
- Provide evidence-based answers to financial and document-related questions.
- Expose financial and AI capabilities through a REST API.

## Key Features

### 1. Financial Analytics

- Supplier spending analysis.
- Paid and unpaid invoice analysis.
- Overdue invoice monitoring.
- Customer receivables tracking.
- Net cash-flow analysis.
- 30-day cash-flow forecasting.
- Supplier and customer financial insights.

### 2. Invoice Processing

- PDF invoice text extraction.
- OCR support for scanned invoices.
- Invoice information extraction and validation.
- Invoice import functionality.
- Financial data quality checks.

### 3. Anomaly Detection

- Identify potentially unusual invoice records.
- Flag suspicious patterns for further investigation.

### 4. AI Financial Assistant

- Answer financial questions using structured invoice data.
- Perform deterministic financial calculations using Python and SQL.
- Use a locally hosted language model for natural-language explanations.
- Provide financial context to reduce unsupported AI-generated claims.

### 5. Document Intelligence (RAG)

- Extract text from business documents.
- Split documents into searchable chunks.
- Generate embeddings using Nomic Embed Text.
- Store document embeddings in ChromaDB.
- Retrieve relevant document passages.
- Generate answers using retrieved evidence and Ollama.
- Return source filenames with document answers.
- Validate evidence for supported invoice fields.

### 6. REST API

The FastAPI backend exposes endpoints for:

- Application health checks.
- Financial portfolio analytics.
- Customer analytics.
- Supplier analytics.
- Financial and document-related questions.
- PDF document uploads and ingestion.

API documentation is available through FastAPI's interactive documentation interface when the backend is running.

## Technology Stack

| Area | Technologies |
|---|---|
| Programming | Python 3.12 |
| Backend API | FastAPI, Uvicorn |
| Dashboard | Streamlit |
| Data analysis | Pandas |
| Visualisation | Matplotlib, Altair |
| Relational database | PostgreSQL |
| Database driver | Psycopg 3 |
| Vector database | ChromaDB |
| LLM runtime | Ollama |
| Language model | Qwen 2.5 1.5B |
| Embeddings | Nomic Embed Text |
| PDF processing | PyMuPDF |
| OCR | Tesseract, Pytesseract |
| Configuration | Pydantic Settings |
| Logging | Python logging with JSON-formatted output |
| API communication | Requests |

## Architecture

### High-Level Architecture

```text
                 Users
                   |
          +--------+--------+
          |                 |
          v                 v
   Streamlit Dashboard   REST API
                         (FastAPI)
                             |
                             v
                    Analytics and AI
                       Services
                             |
                 +-----------+-----------+
                 |                       |
                 v                       v
             PostgreSQL             Document RAG
                 |                       |
                 v                       v
          Financial Analytics       PDF Extraction
                 |                       |
                 v                       v
          Financial Insights        Text Chunking
                                         |
                                         v
                                  Nomic Embeddings
                                         |
                                         v
                                     ChromaDB
                                         |
                                         v
                                   RAG Retrieval
                                         |
                                         v
                                  Ollama / LLM
```

### Document Intelligence Flow

```text
Business PDF Documents
         |
         v
   PDF Extraction
         |
         v
    OCR if needed
         |
         v
    Text Chunking
         |
         v
   Embedding Generation
         |
         v
      ChromaDB
         |
         v
   Document Retrieval
         |
         v
 Evidence Validation
         |
         v
   Ollama Language Model
         |
         v
  Answer with Sources
```

### Financial Analytics Flow

```text
        Invoice Data
             |
             v
         PostgreSQL
             |
             v
      Python / Pandas
             |
      +------+------+
      |      |      |
      v      v      v
   Supplier Customer Cash Flow
   Analysis Analysis Analysis
      |      |      |
      +------+------+
             |
             v
       Financial Assistant
             |
             v
        REST API / UI
```

## Project Structure

```text
mittelstand-ai/
|
├── analytics/
│   ├── create_database.py
│   ├── database.py
│   ├── customer_receivables.py
│   ├── dashboard.py
│   ├── data_quality.py
│   ├── financial_assistant.py
│   ├── financial_context.py
│   ├── financial_insights.py
│   ├── import_to_postgres.py
│   ├── invoice_importer.py
│   ├── net_cash_flow.py
│   ├── anomaly_detector.py
│   ├── overdue_analysis.py
│   ├── pdf_extractor.py
│   ├── document_chunker.py
│   ├── embedding_client.py
│   ├── ollama_client.py
│   ├── rag_pipeline.py
│   ├── rag_assistant.py
│   └── evidence_validator.py
│
├── api/
│   └── main.py
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── logging_config.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── uploads/
│   └── vector_store/
│
├── docs/
│   ├── architecture.md
│   ├── day1_findings.md
│   ├── day3_data_quality.md
│   ├── day3_overdue_findings.md
│   ├── day8_supplier_risk.md
│   ├── day9_cash_flow_forecast.md
│   ├── day10_receivables_findings.md
│   └── day11_net_cash_flow.md
│
├── sql/
│   └── 01_basic_analysis.sql
│
├── tests/
│   ├── test_evidence_validator.py
│   └── test_rag_retrieval.py
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Installation and Setup

### Prerequisites

- Python 3.12
- PostgreSQL
- Ollama
- Tesseract OCR
- Git

### 1. Clone the repository

```bash
git clone https://github.com/praneeshniet-source/mittelstand-ai.git
cd mittelstand-ai
```

### 2. Create a virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Review `.env` and configure the PostgreSQL connection and other settings for your environment.

The application expects the PostgreSQL database and required invoice tables to be available. The current database verification script checks for existing tables; it is not a complete database schema migration tool.

### 5. Install Tesseract OCR

On macOS:

```bash
brew install tesseract
```

Verify:

```bash
tesseract --version
```

### 6. Install Ollama and download models

Install Ollama from:

https://ollama.com/

Download the language model:

```bash
ollama pull qwen2.5:1.5b
```

Download the embedding model:

```bash
ollama pull nomic-embed-text
```

Ensure Ollama is running before using the AI and document intelligence features.

### 7. Start the FastAPI backend

```bash
.venv/bin/uvicorn api.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### 8. Start the Streamlit dashboard

Open another terminal, activate the virtual environment, and run:

```bash
.venv/bin/streamlit run app.py
```

## Testing

Run the automated tests:

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
```

The repository also contains manually executable analysis and verification scripts. Not every script in the project is an automated pytest test.

## Documentation

Detailed technical architecture and implementation notes:

- [System Architecture](docs/architecture.md)
- [Data Quality Findings](docs/day3_data_quality.md)
- [Overdue Invoice Analysis](docs/day3_overdue_findings.md)
- [Supplier Risk Analysis](docs/day8_supplier_risk.md)
- [Cash Flow Forecast](docs/day9_cash_flow_forecast.md)
- [Customer Receivables](docs/day10_receivables_findings.md)
- [Net Cash Flow Analysis](docs/day11_net_cash_flow.md)

## Current Project Status

The current prototype includes:

- PostgreSQL-backed financial analytics.
- Supplier and customer invoice analysis.
- Cash-flow analysis and forecasting.
- PDF invoice extraction and OCR.
- Anomaly detection.
- Local LLM-powered financial assistance.
- ChromaDB-based document retrieval.
- Evidence validation for document answers.
- FastAPI endpoints for analytics, AI questions and document uploads.
- Centralised application configuration and structured logging.

The project is still under active development. The Streamlit dashboard, API and RAG components should not be considered a fully integrated production financial platform.

## Known Limitations

- The current financial reporting date is configured as a fixed date in parts of the financial assistant.
- Document retrieval currently retrieves a broad candidate set before local ranking, which may not scale efficiently to large document collections.
- PDF OCR depends on the local Tesseract installation.
- Document retrieval and answer quality depend on extracted text and embedding relevance.
- Financial question routing currently uses keyword-based classification.
- The database schema is not yet managed through a formal migration framework.
- Authentication, role-based access control and production deployment are not yet implemented.

## Future Development Roadmap

Planned development areas include:

- React and TypeScript frontend.
- Jira and Confluence enterprise integrations.
- MCP-based enterprise tool integration.
- Multi-provider AI architecture.
- Workflow orchestration.
- Human approval mechanisms.
- Role-based access control.
- Audit logging.
- Automated financial operations workflows.
- Docker-based deployment.
- Improved testing and evaluation.

## Project Disclaimer

Mittelstand AI is an educational and portfolio prototype developed using synthetic invoice datasets.

It is not a production-ready accounting system, financial auditing platform, or replacement for professional financial advice. AI-generated explanations and recommendations should be verified against original financial records and documents.

## Author

**Praneesh S.**

Aspiring Business Analyst | Data Analytics | AI Applications | Financial Operations
