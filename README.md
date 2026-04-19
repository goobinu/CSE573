# TrendScout AI (Group 11)

## Overview
**TrendScout AI** is a Conversational Market Intelligence system built using a Knowledge Graph-enhanced Retrieval-Augmented Generation (KG-RAG) architecture. It scrapes LinkedIn, Reddit, TechCrunch, and Startups Gallery for the latest tech trends, extracts entities and relationships into a Neo4j knowledge graph, and uses a ChromaDB vector store for semantic search. The system enables users to query complex market trends with high accuracy and source-backed citations via the ASU Voyager LLM.

---

## Directory Structure

- **CODE/**: Contains all source code for the project.
  - **scraping/**: Scripts for data collection, organized by source platform:
    - **linkedin/**: LinkedIn scraping modules.
    - **reddit/**: Reddit scraping modules.
    - **techcrunch/**: TechCrunch scraping and filtering modules.
    - **startups_gallery/**: Startups Gallery scraping modules.
  - **processing/**: Data ingestion, entity extraction, and resolution.
  - **database/**: Neo4j and ChromaDB setup and integration.
  - **utilities/**: Reusable helper scripts encompassing browser actions, file handling, and LLM clients.
  - `app.py`: Streamlit-based user interface.
- **DATA/**: Storage for all datasets.
  - **raw/**: Initial scraped CSV/JSON files, organized into **linkedin/**, **reddit/**, **techcrunch/**, and **startups_gallery/** subdirectories.
  - **processed/**: Final knowledge graph JSON and vector database files.
- **EVALUATIONS/**: Contains performance reports and evaluation results.
  - **Output_Reports/**: Automated pipeline logs and intelligence reports. Each evaluation generates a distinct `run_YYYYMMDD_HHMMSS/` subfolder containing `ablation_results.md`, `graph_metrics.txt`, and `ragas_scores.json`.

---

## Setup Instructions

### 1. Requirements
Ensure you have Python 3.9+ installed. Install the necessary dependencies:
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the root directory and configure the following:
```env
# ASU Voyager API
VOYAGER_API_KEY=sk-...

# Neo4j Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

---

## Execution

### Run the Full Pipeline
To run the end-to-end data pipeline (Scrape -> Process -> Upload), use:
```bash
python main.py --all
```

### Individual Pipeline Stages
- **Scrape**: `python main.py --scrape`
- **Process**: `python main.py --process`
- **Upload**: `python main.py --upload`
- **Evaluate**: `python main.py --evaluate`

### Launch the UI
After processing the data, start the Streamlit chat interface:
```bash
streamlit run CODE/app.py
```

---

## Authors
- Group 11 (CSE 573): Gabriel Habeeb, Jadhav Kunal, Yuvraj Rasal, Saswata Dutta
