# 🛡️ DataHub Learning Lab

> A complete, beginner-friendly educational monorepo to visually understand DataHub OSS internals, metadata ingestion, lineage DAGs, ownership, governance tags, and grounded AI assistant integrations.

---

## 📚 Table of Contents
- [📖 Core Concepts Explained](#-core-concepts-explained)
  - [What is Metadata?](#what-is-metadata)
  - [Difference Between Metadata and Actual Data](#difference-between-metadata-and-actual-data)
  - [How Ingestion Works](#how-ingestion-works)
  - [How Lineage Works](#how-lineage-works)
  - [How Ownership Works](#how-ownership-works)
  - [How AI Agents Use DataHub (Grounding RAG)](#how-ai-agents-use-datahub-grounding-rag)
  - [How MCP (Model Context Protocol) Elevates DataHub](#how-mcp-model-context-protocol-elevates-datahub)
- [📁 Monorepo Project Structure](#-monorepo-project-structure)
- [🚀 Quickstart Execution Guide](#-quickstart-execution-guide)
  - [1. Start Services via Docker Compose](#1-start-services-via-docker-compose)
  - [2. Start FastAPI Backend](#2-start-fastapi-backend)
  - [3. Start Streamlit Frontend UI](#3-start-streamlit-frontend-ui)
- [🧪 Step-by-Step Educational Walkthrough](#-step-by-step-educational-walkthrough)

---

## 📖 Core Concepts Explained

### What is Metadata?
**Metadata is "data about data."** In modern data engineering, raw datasets contain business transactional rows, while metadata describes the structural, operational, and governance properties of those datasets.

### Difference Between Metadata and Actual Data

| Feature | Actual Data (PostgreSQL) | Metadata (DataHub OSS) |
| :--- | :--- | :--- |
| **Example Content** | `Alice Smith`, `alice@example.com`, `$249.99` | Column `email` is `VARCHAR(100)` tagged `PII` owned by `Alice Data Lead` |
| **Storage Engine** | PostgreSQL database tables | Elasticsearch search indexes & DataHub GMS entity aspects |
| **Purpose** | Process business transactions (orders, payments) | Enable search, data governance, lineage tracking, and AI grounding |
| **Size** | Gigabytes / Terabytes | Megabytes / Gigabytes |

### How Ingestion Works
Ingestion extracts metadata from databases, data warehouses (Snowflake, BigQuery), ETL pipelines (Airflow, dbt), and BI tools (Looker, Tableau).
* **Pull-Based Crawling**: DataHub CLI connects to source databases, queries `pg_catalog`, parses comments, and pushes Metadata Change Proposals (MCPs) to `datahub-gms` (Port 8080).
* **Push-Based Emissions**: Data pipelines emit metadata events over REST HTTP emitters or Kafka event streams during execution.

### How Lineage Works
Lineage forms a Directed Acyclic Graph (DAG) mapping how data flows from root source tables down into analytical reports and BI dashboards.
* **Example Path**: `customers` ➔ `orders` ➔ `sales_report` ➔ `revenue_dashboard`
* **Why Lineage Matters**: Allows **Impact Analysis** (knowing what reports will break if a column or table is altered) and **Root Cause Analysis** (tracing broken dashboard metrics back to upstream database bugs).

### How Ownership Works
DataHub attaches **Ownership Aspects** to datasets.
* **Technical Owner**: Engineers responsible for database maintenance and schema migrations (e.g., `Alice Data Lead`).
* **Business Owner**: Domain leads responsible for data accuracy and business definitions (e.g., `Bob Warehouse Manager`).

### How AI Agents Use DataHub (Grounding RAG)
Generic LLMs hallucinate table structures and column names. DataHub grounds AI Agents:
1. User asks a natural language question (e.g. *"What dashboards depend on Orders?"*).
2. The system **first queries DataHub** REST/GraphQL APIs to retrieve verified schema, owners, and lineage DAGs.
3. The real DataHub metadata is injected into the LLM system context prompt.
4. The LLM (Gemini API or local `llama.cpp` running `gemma4:e2b`) produces a 100% verified, zero-hallucination response!

### How MCP (Model Context Protocol) Elevates DataHub
Model Context Protocol (MCP) standardizes how AI Agents interact with enterprise services. An MCP server wrapping DataHub allows tools like Claude Desktop, Cursor, or autonomous agents to tool-call DataHub functions (`search_catalog`, `get_lineage_graph`, `perform_impact_analysis`) directly during agentic planning loops.

---

## 📁 Monorepo Project Structure

```
Datahub_DemoProject/
├── README.md                      # Complete Monorepo Guide & Concept Explanation
├── backend/                       # FastAPI Backend Service
│   ├── main.py                    # REST Endpoints (/search, /dataset, /schema, /lineage, /ask)
│   ├── config.py                  # Config settings for DataHub, Gemini API, and llama.cpp
│   ├── datahub_client.py          # DataHub GMS GraphQL & REST Client with fallback store
│   ├── ai_grounding.py            # Grounded AI Assistant logic (Gemini & llama.cpp gemma4:e2b)
│   └── requirements.txt
├── frontend/                      # Streamlit UI Frontend
│   ├── app.py                     # Main Streamlit Launcher & Navigation
│   ├── components/
│   │   ├── metadata_explorer.py   # Step 4 & 7 Metadata Explorer Page
│   │   ├── lineage_viewer.py      # Step 3 Interactive Plotly Lineage DAG
│   │   └── ai_assistant.py        # Step 6 Grounded Chatbot UI with Grounding Inspector
│   └── requirements.txt
├── database/                      # PostgreSQL E-Commerce DB Init
│   └── init.sql                   # DDL schemas & sample data (Customers, Orders, Products, etc.)
├── docker/                        # Infrastructure Orchestration
│   ├── docker-compose.yml         # Starts Postgres, DataHub GMS, Frontend, Kafka, ZooKeeper, ES
│   └── datahub-ingestion/
│       ├── postgres_ingestion.yml # DataHub Ingestion Recipe
│       └── lineage_emission.py    # Python SDK REST Emitter Script
├── docs/                          # Detailed Technical Architecture Guides
│   ├── 01_DATAHUB_ARCHITECTURE.md # Step 1 Docker Services Breakdown
│   ├── 02_INGESTION_AND_LINEAGE.md # Step 2 & 3 Metadata & Lineage Mechanics
│   └── 03_AI_GROUNDING_AND_MCP.md # Step 6 & MCP AI Integration Breakdown
└── sample_data/                   # Metadata Declarations & Schemas
```

---

## 🚀 Quickstart Execution Guide

### 1. Start Services via Docker Compose (Step 1)
```bash
cd docker
docker compose up -d
```
* PostgreSQL Sample Database runs at `localhost:5432`
* DataHub GMS REST/GraphQL runs at `localhost:8080`
* DataHub Web UI runs at `localhost:9002`

### 2. Ingest Metadata & Lineage (Steps 2 & 3)
```bash
# Ingest PostgreSQL schema into DataHub
./venv/bin/datahub ingest -c docker/datahub-ingestion/postgres_ingestion.yml

# Emit End-to-End Lineage & Governance Aspects
./venv/bin/python docker/datahub-ingestion/lineage_emission.py
```

### 3. Start FastAPI Backend (Step 5)
```bash
./venv/bin/python backend/main.py
```
FastAPI server starts on `http://localhost:8000`. Open `http://localhost:8000/docs` to view interactive Swagger REST API documentation.

### 4. Start Streamlit Frontend UI (Steps 4, 6, 7)
```bash
./venv/bin/streamlit run frontend/app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Step-by-Step Educational Walkthrough

1. **Inspect DataHub UI**: Open `http://localhost:9002` to see raw DataHub OSS interface.
2. **Metadata Explorer**: In Streamlit UI, go to **"Metadata Explorer"**, search `orders` or `customers`, click on column schemas, and click **"Jump to Downstream"** buttons to navigate the lineage tree.
3. **AI Grounded Assistant**: In Streamlit UI, go to **"AI Grounded Assistant"**, select **Gemini API** or **llama_cpp (`gemma4:e2b`)**, ask *"What breaks if I delete Orders?"*, and expand the **"GROUNDING INSPECTOR"** tab to see the exact DataHub context payload passed to the LLM prior to generation!
