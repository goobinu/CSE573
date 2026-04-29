# TrendScout AI (Group 11)

## Overview

**TrendScout AI** is a Conversational Market Intelligence system built using a Knowledge Graph-enhanced Retrieval-Augmented Generation (KG-RAG) architecture. It collects data from **LinkedIn**, **Reddit**, **TechCrunch**, **Startups Gallery**, and **Job Boards (Greenhouse)**, extracts entities and relationships into a **Neo4j** knowledge graph, and indexes content in a **ChromaDB** vector store for semantic search. Users can query complex market trends with high accuracy and source-backed citations via the **ASU Voyager LLM** (Qwen3-235B).

---

## Architecture

```
Data Sources → Scraping → Ingestion → Extraction → Entity Resolution → Neo4j + ChromaDB → Streamlit UI
```

| Stage            | Tool / Module                          |
|------------------|----------------------------------------|
| Scraping         | Playwright, BeautifulSoup4             |
| LLM Extraction   | ASU Voyager (Qwen3-235B via OpenAI API)|
| Entity Resolution| `jellyfish` (fuzzy dedup), LLM merging |
| Knowledge Graph  | Neo4j (Bolt)                           |
| Vector Store     | ChromaDB                               |
| Evaluation       | RAGAS, ablation study, KG health checks|
| UI               | Streamlit                              |

---

## Directory Structure

```
CSE573/
├── CODE/
│   ├── app.py                          # Streamlit chat interface
│   ├── ingestion_template.py           # Template for new source ingestion modules
│   ├── post_process_graph.py           # Post-processes and cleans the knowledge graph
│   ├── scraping/
│   │   ├── linkedin/                   # LinkedIn category, results, and subpage scrapers
│   │   ├── reddit/                     # Reddit data collection modules
│   │   ├── techcrunch/                 # TechCrunch scraping and filtering
│   │   ├── startups_gallery/           # Startups Gallery scraper
│   │   └── jobboards/                  # Greenhouse job board scraper, parser, and cleaner
│   ├── processing/
│   │   ├── ingestion.py                # LinkedIn master dataset normalization
│   │   ├── reddit_ingestion.py         # Reddit data normalization
│   │   ├── techcrunch_ingestion.py     # TechCrunch data normalization
│   │   ├── startups_gallery_ingestion.py # Startups Gallery normalization
│   │   ├── jobboards_ingestion.py      # Greenhouse job board normalization (salary, employment fields)
│   │   ├── extraction.py               # LLM-powered entity & relationship extraction (parallel, checkpointed)
│   │   └── entity_resolution.py        # LLM-based entity deduplication with checkpointing
│   ├── database/
│   │   ├── db_integration.py           # Neo4j upload and graph merge
│   │   └── vector_store_setup.py       # ChromaDB collection setup and upsert
│   └── utilities/
│       ├── backup_manager.py           # Automated pre-run backup of processed data
│       ├── browser.py                  # Playwright browser session helpers
│       ├── checkpoint_manager.py       # Thread-safe checkpoint read/write utilities
│       ├── csvhandling.py              # CSV read/write helpers
│       └── llm_client.py              # ASU Voyager LLM client wrapper
├── DATA/
│   ├── raw/
│   │   ├── linkedin/                   # Raw LinkedIn CSVs and subpage results
│   │   ├── reddit/                     # Raw Reddit data
│   │   ├── techcrunch/                 # Raw TechCrunch articles
│   │   ├── startups_gallery/           # Raw startup JSON data
│   │   ├── greenhouse/                 # Raw Greenhouse job board HTML/JSON
│   │   └── master_dataset_cleaned.csv  # Merged and deduplicated LinkedIn master file
│   ├── processed/
│   │   ├── *_cleaned_for_extraction.csv  # Normalized per-source CSVs
│   │   ├── extracted_knowledge.json    # Raw LLM extraction output
│   │   ├── final_knowledge_graph.json  # Resolved, deduplicated KG entities
│   │   └── chroma_db/                  # Persisted ChromaDB vector store
│   └── db_backups/                     # Automated backups of processed files
├── EVALUATIONS/
│   ├── kg_health.py                    # Knowledge graph structural metrics (Cypher)
│   ├── rag_eval.py                     # RAGAS generation quality evaluation
│   ├── ablation_study.py               # Vector-only vs. Graph-only vs. KG-RAG comparison
│   └── Output_Reports/
│       └── run_YYYYMMDD_HHMMSS/        # Per-run reports: ablation_results.md, graph_metrics.txt, ragas_scores.json
├── TESTS/
│   └── test_jobboards_smoke.py         # Smoke tests for the job boards ingestion pipeline
├── config.py                           # Centralised paths, env vars, and KG schema config
├── main.py                             # Pipeline orchestrator (argparse entrypoint)
├── DATA_SCHEMA.md                      # Canonical ChromaDB metadata and Neo4j schema spec
└── requirements.txt                    # Python dependencies
```

---

## Setup Instructions

### 1. Prerequisites

- Python **3.9+**
- A running **Neo4j** instance (local or cloud, Bolt protocol)
- An **ASU Voyager API key**
- Playwright browsers (for scraping):
  ```bash
  playwright install chromium
  ```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the project root and populate the following:

```env
# ASU Voyager LLM API
VOYAGER_API_KEY=sk-...

# Neo4j Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

> **Note:** The model currently in use is `qwen3-235b-a22b-instruct-2507` via `https://openai.rc.asu.edu/v1`.

---

## Execution

### Run the Full Pipeline

Runs Scrape → Process → Upload end-to-end (with an automatic pre-run backup):

```bash
python main.py --all
```

### Individual Pipeline Stages

| Command                    | What it does                                                        |
|----------------------------|---------------------------------------------------------------------|
| `python main.py --scrape`  | Scrapes LinkedIn and Greenhouse job boards                          |
| `python main.py --process` | Normalizes data, runs LLM extraction and entity resolution          |
| `python main.py --upload`  | Uploads resolved graph to Neo4j and embeds docs into ChromaDB       |
| `python main.py --evaluate`| Runs KG health check, RAGAS eval, and ablation study; saves reports |

> A **pre-run backup** of `DATA/processed/` is triggered automatically before `--process`, `--upload`, and `--all`.

### Launch the Chat UI

```bash
streamlit run CODE/app.py
```

### Run Tests

```bash
pytest TESTS/
```

---

## Data Sources

| Source           | Type          | Content                                        |
|------------------|---------------|------------------------------------------------|
| LinkedIn         | Social        | Job posts, categories, company subpages        |
| Reddit           | Forum         | Tech discussion threads and sentiment          |
| TechCrunch       | News          | Startup funding, product launches              |
| Startups Gallery | Directory     | Startup profiles, investors, funding rounds    |
| Greenhouse       | Job Board     | Job listings with salary ranges, skills, roles |

The full ChromaDB metadata schema and Neo4j node/relationship spec are documented in **[DATA_SCHEMA.md](DATA_SCHEMA.md)**.

---

## Knowledge Graph Schema (Summary)

**Node Labels:** `Organization`, `Technology`, `Trend`, `Person`, `Investor`, `FundingRound`, `Skill`

**Key Relationships:** `INVESTED_IN`, `ACQUIRED`, `RELEASED`, `USES`, `COMPETES_WITH`, `HIRES_FOR`, `RAISED_IN`, `WORKS_AT`, `DISCUSSES`, `PARTNERED_WITH`

> The pipeline validates all labels and relationship types against `config.py::SCHEMA_CONFIG` before uploading to Neo4j.

---

## Evaluation Metrics

| Script               | Metric                                                          |
|----------------------|-----------------------------------------------------------------|
| `kg_health.py`       | Node/edge counts, orphan nodes, relationship coverage           |
| `rag_eval.py`        | RAGAS: faithfulness, answer relevancy, context precision/recall |
| `ablation_study.py`  | Head-to-head: Vector-only vs. Graph-only vs. KG-RAG hybrid      |

Reports are saved to `EVALUATIONS/Output_Reports/run_YYYYMMDD_HHMMSS/`.

---

## Authors

Group 11 — CSE 573: Gabriel Habeeb, Jadhav Kunal, Yuvraj Rasal, Saswata Dutta
