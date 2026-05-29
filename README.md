# 🔍 Competitive Intelligence Engine — Graph RAG POC

> Demonstrating **Vanilla RAG + Graph RAG + Hybrid** on a real consulting use case.
> Built entirely with **local, free tools** — no API keys, no cloud costs.

---

## What This Does

A consultant preparing for a client pitch needs to know:
- What the **market research** says (→ **Vanilla RAG** — document search)
- Which **competitors** are active, who they've won, and why (→ **Graph RAG** — knowledge graph traversal)
- A **complete brief** combining structure + narrative (→ **Hybrid** — both layers combined)

This POC shows all three layers side-by-side through a single query router.

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Graph Database | Neo4j 5.x (Docker) | Native graph storage, Cypher query language |
| LLM | Ollama + phi3.5 (local) | Free, runs locally, no API keys needed |
| Embeddings | Ollama nomic-embed-text | Free local embeddings for vector search |
| Vector Store | FAISS (Facebook AI) | Fast similarity search, pre-built wheels |
| Orchestration | LangChain 0.3 + Python | Connects all components together |

---

## Prerequisites

Before starting, make sure you have:

| Prerequisite | Required Version | Check Command |
|-------------|-----------------|---------------|
| Python | 3.10+ | `python --version` |
| Docker Desktop | Any recent | `docker --version` |
| Ollama | Any recent | `ollama list` |

### Ollama Models Required

```bash
# Pull these two models (one-time download)
ollama pull phi3.5              # LLM for generating answers (~2.2 GB)
ollama pull nomic-embed-text    # Embedding model for RAG (~274 MB)

# Verify both are available
ollama list
```

> **Note:** You can use a different LLM by changing `OLLAMA_LLM_MODEL` in the `.env` file.
> Just make sure the model fits in your available RAM.

---

## Quick Start (Step by Step)

### Step 1: Start Neo4j

```bash
docker-compose up -d
```

Wait ~10 seconds, then open **http://localhost:7474** in your browser.
Login with username `neo4j` and password `password123`.

### Step 2: Create & Activate Virtual Environment

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\activate

# Windows (CMD)
.venv\Scripts\activate.bat
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

> This installs LangChain, Neo4j driver, FAISS, Ollama SDK, and other dependencies.

### Step 4: Seed the Knowledge Graph

```bash
python -X utf8 data/seed_neo4j.py
```

This creates **34 nodes** (competitors, clients, consultants, deals, etc.) and **59 relationships** in Neo4j. The `-X utf8` flag ensures emoji output works on Windows.

### Step 5: Generate Synthetic Documents

```bash
python data/generate_docs.py
```

Creates 5 research documents (Gartner reports, competitor news, industry analysis) in `data/documents/`.

### Step 6: Build the FAISS Vector Index

```bash
python -X utf8 rag/ingest.py --build
```

Loads documents → splits into 17 chunks → embeds with nomic-embed-text → saves FAISS index.

### Step 7: Run the Demo! 🚀

```bash
python -X utf8 app/main.py
```

This launches the interactive CLI. Type `1`, `2`, or `3` for preset demo questions, or type your own.

---

## Demo Questions

Run these in order — the progression from familiar to impressive is deliberate:

### 1. Vanilla RAG (the baseline)
```
What does recent market research say about the top trends in cloud consulting?
```
**What happens:** Router classifies as RAG → retrieves chunks from Gartner/market reports in FAISS → Ollama synthesizes a market summary.

### 2. Graph RAG (the wow moment)
```
Which competitors are active in TechCorp's market segment, which of our past clients did they win, and what pain points drove those clients away?
```
**What happens:** Router classifies as Graph RAG → 4-hop Cypher query traverses Neo4j → shows competitor names, stolen clients, and pain points ranked by win frequency.

### 3. Hybrid (the closer)
```
Build me a complete competitive intelligence brief for the TechCorp pitch.
```
**What happens:** Router fires BOTH layers → graph data provides competitive landscape + relationship map → documents provide market research → LLM synthesizes everything into a structured brief.

---

## Project Structure

```
Graph_RAG_POC/
├── README.md                     # This file
├── requirements.txt              # Python dependencies
├── docker-compose.yml            # Neo4j container setup
├── .env                          # Configuration (Neo4j creds, model names)
├── .gitignore
│
├── data/
│   ├── seed_neo4j.py             # Populates Neo4j with synthetic data
│   ├── generate_docs.py          # Creates .txt research documents
│   └── documents/                # Auto-generated documents (5 files)
│
├── graph/
│   ├── schema.cypher             # Neo4j constraints and indexes
│   ├── queries.py                # 5 named Cypher query functions
│   └── graph_rag.py              # GraphRAGPipeline: graph + LLM synthesis
│
├── rag/
│   └── ingest.py                 # FAISS ingestion + retrieval + Ollama embeddings
│
├── router/
│   └── router.py                 # Hybrid query router + CompetitiveIntelEngine
│
├── app/
│   └── main.py                   # Interactive CLI demo application
│
└── faiss_index/                  # Persisted FAISS vector index (auto-generated)
```

---

## Architecture

```
                    User Question
                         │
                         ▼
              ┌─────────────────────┐
              │  Hybrid Query Router │
              │  (keyword signals)   │
              └─────────────────────┘
               /          │          \
              ▼           ▼           ▼
        [Graph RAG]  [Vanilla RAG]  [Both]
              │           │           │
              ▼           ▼           ▼
          [Neo4j]    [FAISS]      [Neo4j +
         Cypher      Vector       FAISS]
         Traversal   Search
              \          │          /
               \         ▼         /
                ┌────────────────┐
                │Context Assembly│
                └────────┬───────┘
                         │
                         ▼
                ┌────────────────┐
                │ Ollama phi3.5  │
                │   (Local LLM)  │
                └────────┬───────┘
                         │
                         ▼
               Final Answer + Sources
```

---

## Key Concepts Demonstrated

| Capability | Vanilla RAG | Graph RAG | Hybrid |
|-----------|:-----------:|:---------:|:------:|
| Retrieve relevant documents | ✅ | ❌ | ✅ |
| Answer "what does research say" | ✅ | ❌ | ✅ |
| Multi-hop relationship traversal | ❌ | ✅ | ✅ |
| Rank competitors by win count | ❌ | ✅ | ✅ |
| Connect pain points to competitors | ❌ | ✅ | ✅ |
| Combine structure + narrative | ❌ | ❌ | ✅ |
| Works with no API key or cost | ✅ | ✅ | ✅ |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Make sure venv is activated: `.venv\Scripts\activate` |
| Neo4j connection refused | Run `docker-compose up -d` and wait 10 seconds |
| Ollama model not found | Run `ollama pull phi3.5` and `ollama pull nomic-embed-text` |
| Slow LLM responses | Normal for CPU-only machines. First query loads the model (~1-2 min), subsequent queries are faster |
| `UnicodeEncodeError` on Windows | Use the `-X utf8` flag: `python -X utf8 app/main.py` |
| Out of memory error | Switch to a smaller model in `.env` (e.g., `phi3.5:latest` is 2.2GB) |
| FAISS index not found | Run `python -X utf8 rag/ingest.py --build` first |

---

## Stopping Everything

```bash
# Stop Neo4j container
docker-compose down

# Deactivate virtual environment
deactivate
```

To start again later:
```bash
docker-compose up -d
.venv\Scripts\activate
python -X utf8 app/main.py
```
