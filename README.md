# Mittelstand AI

**AI-Powered Financial Operations Assistant for Small and Medium-Sized Enterprises (SMEs)**

Mittelstand AI is a prototype designed to help SMEs understand their financial operations through invoice analytics, cash-flow insights, anomaly detection, document extraction, and AI-assisted document question answering.

The project combines traditional data analytics with locally running AI models to demonstrate how intelligent automation can support everyday financial operations.

## Project Objectives

- Analyse supplier invoices and customer receivables.
- Identify overdue invoices and outstanding payments.
- Monitor supplier spending and payment patterns.
- Forecast short-term cash flow.
- Detect potentially unusual invoice records.
- Extract information from digital and scanned PDF invoices.
- Retrieve relevant information from business documents using RAG.
- Generate natural-language explanations using a local LLM.

## Key Features

### Financial Analytics
- Supplier spending analysis.
- Paid versus unpaid invoice analysis.
- Overdue invoice monitoring.
- Customer receivables tracking.
- Net cash-flow analysis.
- 30-day cash-flow forecasting.

### Invoice Processing
- PDF invoice text extraction.
- OCR support for scanned invoices.
- Invoice information extraction and validation.
- Invoice import functionality.

### Anomaly Detection
- Identify potentially unusual invoice records.
- Flag suspicious patterns for further review.

### AI Financial Assistant
- Answer financial questions using structured invoice data.
- Generate explanations using a locally hosted language model.
- Keep financial calculations in deterministic Python and SQL logic.

### Document Intelligence (RAG)
- Extract text from business documents.
- Split documents into searchable chunks.
- Generate embeddings using Nomic Embed.
- Store and retrieve document embeddings using ChromaDB.
- Answer document-related questions using retrieved context.
- Return source filenames with answers.

## Technology Stack

| Area | Technologies |
|---|---|
| Programming | Python |
| Dashboard | Streamlit |
| Data analysis | Pandas |
| Visualisation | Matplotlib, Altair |
| Database | SQLite |
| Vector database | ChromaDB |
| LLM | Ollama, Qwen 2.5 1.5B |
| Embeddings | Nomic Embed Text |
| PDF processing | PyMuPDF |
| OCR | Tesseract, Pytesseract |
| API communication | Requests |

## Architecture

```text
                  Business Documents
                         |
                         v
                  PDF Text Extraction
                         |
                         v
                    Text Chunking
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
                  Qwen 2.5 (Ollama)
                         |
                         v
                  Document Answers


                  Invoice Datasets
                         |
                         v
                       SQLite
                         |
                         v
                 Python / Pandas
                         |
              +----------+----------+
              |          |          |
              v          v          v
          Financial   Anomaly    Cash Flow
          Analytics   Detection  Forecasting
              |          |          |
              +----------+----------+
                         |
                         v
                  Streamlit Dashboard
```

## Project Structure

```text
mittelstand-ai/
│
├── analytics/
│   ├── create_database.py
│   ├── data_quality.py
│   ├── dashboard.py
│   ├── pdf_extractor.py
│   ├── invoice_importer.py
│   ├── overdue_analysis.py
│   ├── customer_receivables.py
│   ├── net_cash_flow.py
│   ├── anomaly_detector.py
│   ├── financial_insights.py
│   ├── financial_context.py
│   ├── financial_assistant.py
│   ├── ollama_client.py
│   ├── document_chunker.py
│   ├── embedding_client.py
│   ├── rag_pipeline.py
│   └── rag_assistant.py
│
├── data/
│   └── raw/
│       ├── invoices.csv
│       └── customer_invoices.csv
│
├── docs/
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
├── app.py
├── requirements.txt
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd mittelstand-ai
```

### 2. Create a virtual environment

Python 3.12 is recommended.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Tesseract OCR

On macOS:

```bash
brew install tesseract
```

Verify:

```bash
tesseract --version
```

### 5. Install Ollama

Download Ollama from:

https://ollama.com/

Pull the required models:

```bash
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text
```

Ensure the Ollama service is running before using the AI features.

### 6. Run the application

```bash
.venv/bin/streamlit run app.py
```

The Streamlit dashboard will open in your browser.

## Current Project Status

The prototype includes:

- Financial analytics dashboard.
- Supplier and customer invoice analysis.
- Cash-flow forecasting.
- Invoice PDF extraction and OCR.
- Anomaly detection.
- Local LLM-powered financial assistant.
- ChromaDB-based document retrieval.
- RAG-based document question answering.

The RAG pipeline has been tested independently with digital and scanned invoice PDFs. Full integration of every RAG feature into the main dashboard is not yet claimed.

## Future Improvements

- German and English invoice processing.
- Improved multilingual document retrieval.
- More robust hybrid search and reranking.
- Page-level source citations.
- Automated invoice ingestion.
- Improved financial forecasting.
- Role-based access and authentication.
- Production deployment and monitoring.
- Evaluation datasets for retrieval and answer accuracy.

## Project Disclaimer

Mittelstand AI is an educational and portfolio prototype built using synthetic invoice datasets.

It is not a production-ready accounting system, financial auditing platform, or replacement for professional financial advice. AI-generated explanations should be verified against the original financial records and documents.

## Author

**Praneesh S.**

Aspiring Business Analyst | Data Analytics | AI Applications | Financial Operations
