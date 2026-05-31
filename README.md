# Competitive Intelligence Engine -- Graph RAG POC

> Demonstrating **Vanilla RAG + Graph RAG + Hybrid** on a real consulting use case.
> Built with **free cloud services** -- no Docker, no local models, no admin permissions needed.

---

## What This Does

A consultant preparing for a client pitch needs to know:
- What the **market research** says --> **Vanilla RAG** (document search)
- Which **competitors** are active, who they've won, and why --> **Graph RAG** (knowledge graph traversal)
- A **complete brief** combining structure + narrative --> **Hybrid** (both layers combined)

This POC shows all three layers side-by-side through a single query router.

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Graph Database | Neo4j Aura Free (cloud) | No install, free tier (200K nodes) |
| LLM | Google Gemini API (free) | Fast responses, no local GPU needed |
| Embeddings | Google Gemini text-embedding-004 | Free embeddings via API |
| Vector Store | FAISS (pip install) | Fast similarity search, no system install |
| Orchestration | LangChain 0.3 + Python | Connects all components together |

> **Zero system-level installations.** Everything runs through pip packages and API calls.

---

## Prerequisites

| Requirement | How to Get It |
|------------|---------------|
| Python 3.10+ | `python --version` (usually pre-installed or request from IT) |
| pip | Comes with Python |
| Internet access | For API calls to Neo4j Aura and Google Gemini |

---

## Setup (Step by Step)

### Step 1: Create Neo4j Aura Free Instance

1. Go to **https://neo4j.com/cloud/aura-free/**
2. Sign up with your email (personal or work email)
3. Create a **Free** instance (select any region)
4. **IMPORTANT: Save the password** shown on creation -- you won't see it again!
5. Wait for the instance to start (~1-2 minutes)
6. Copy the **Connection URI** from the dashboard (looks like `neo4j+s://xxxxxxxx.databases.neo4j.io`)

### Step 2: Get Google Gemini API Key

1. Go to **https://aistudio.google.com/apikey**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the API key

### Step 3: Clone/Copy the Project

Copy the project folder to your office laptop (USB, email, Git, etc.)

### Step 4: Create Virtual Environment & Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate it (Windows PowerShell)
.venv\Scripts\activate

# Activate it (Windows CMD)
.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Configure Your Credentials

Open the `.env` file and fill in your credentials:

```env
# Neo4j Aura
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io    # <-- paste your Aura URI
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-aura-password-here               # <-- paste the password from Step 1

# Google Gemini
GOOGLE_API_KEY=your-gemini-api-key-here               # <-- paste your API key from Step 2

# Model Configuration (no need to change these)
GEMINI_LLM_MODEL=gemini-2.0-flash
GEMINI_EMBED_MODEL=models/text-embedding-004
```

### Step 6: Seed the Knowledge Graph

```bash
python data/seed_neo4j.py
```

This creates **34 nodes** and **59 relationships** in your Neo4j Aura instance.
You can verify at **https://console.neo4j.io** by running:
```cypher
MATCH (n)-[r]->(m) RETURN n, r, m
```

### Step 7: Generate Documents & Build Vector Index

```bash
# Generate synthetic research documents
python data/generate_docs.py

# Embed documents and build FAISS index
python rag/ingest.py --build
```

### Step 8: Run the Demo!

```bash
python app/main.py
```

Type **1**, **2**, or **3** for preset demo questions, or type your own!

---

---

## Demo Questions

> **Tip:** In the running app, you don't have to use only the 3 preset questions.
> Just type **any question** and press Enter — the router will automatically pick the right mode!

---

### Mode 1 -- Vanilla RAG (Document Search)
These questions search across the 5 research documents using FAISS vector similarity.
The router detects keywords like: `research`, `trend`, `Gartner`, `market`, `report`, `summarize`, `analyst`

**Preset question:**
```
What does recent market research say about the top trends in cloud consulting?
```

**More questions you can ask:**
```
What does Gartner say about cloud adoption barriers?
What are the top FinTech cloud trends?
Summarize the key findings on cloud cost optimization
What challenges do healthcare organizations face with cloud migration?
What is the projected market size for cloud consulting?
What does the research say about multi-cloud governance?
What is FinOps and why is it trending?
What does the market report say about AI-native infrastructure?
Which consulting firms are gaining market share in cloud?
What are green cloud strategies and why do clients want them?
What does the latest analysis say about legacy system modernization?
What are the growth opportunities in mid-market cloud consulting?
```

---

### Mode 2 -- Graph RAG (Knowledge Graph Traversal)
These questions traverse the Neo4j graph using Cypher queries.
The router detects keywords like: `competitor`, `who won`, `pain point`, `relationship`, `who knows`, `technology gap`, `consultants`, `worked with`

**Preset question:**
```
Which competitors are active in TechCorp's market segment, which of our past clients did they win, and what pain points drove those clients away?
```

**More questions you can ask:**
```
Who on our team has a relationship with TechCorp?
Which consultants have worked with clients in the Cloud Migration segment?
What technologies does Accenture use in their engagements?
Which clients did McKinsey Digital win from us?
What technology gap does Deloitte Tech have compared to ThoughtWorks?
Which competitors are active in the Cybersecurity market segment?
What pain points does RetailGiant have?
Who are the consultants with relationships at FinanceHub?
Which deals did Alice Chen deliver and what was the outcome?
What technologies did we use in the TechCorp deal?
Which clients operate in the Data & AI market segment?
Who competes in the Digital Transformation space?
What pain points are most common across our lost deals?
Which competitor has the most client wins?
What is the relationship between Bob Martinez and TechCorp?
Which clients have we lost to Accenture?
```

---

### Mode 3 -- Hybrid (Graph + Documents Combined)
These questions combine structured graph data with unstructured research documents.
The router detects keywords like: `full brief`, `everything about`, `pitch`, `comprehensive`, `complete overview`, `why did we lose`, `prepare for`

**Preset question:**
```
Build me a complete competitive intelligence brief for the TechCorp pitch.
```

**More questions you can ask:**
```
Give me everything about Accenture -- their strategy, clients they won, and technologies they use
Prepare a full competitive brief for the RetailGiant pitch
Why did we lose the RetailGiant deal and how do we counter McKinsey next time?
Build me a comprehensive overview of the Cloud Migration market and who our competition is
Give me the full picture on our FinanceHub opportunity
What is the complete win-loss pattern in our last 4 deals?
Prepare me for a pitch meeting with a client in the Cybersecurity segment
Build a brief combining what the market research says and what our graph data shows about Accenture
Give me a complete analysis of TechCorp including who knows them and what the market says
Everything about the Data & AI consulting landscape -- competitors, clients, and research
```

---

### How the Router Decides

| Keywords detected | Route chosen |
|------------------|-------------|
| `research`, `Gartner`, `trend`, `market`, `report`, `analysis`, `summarize` | Vanilla RAG |
| `competitor`, `who won`, `pain point`, `relationship`, `who knows`, `technology gap`, `consultants` | Graph RAG |
| `full brief`, `everything`, `pitch`, `comprehensive`, `complete`, `why did we lose`, `prepare` | Hybrid |
| No clear signal (ambiguous) | Hybrid (safest default) |



## Project Structure

```
Graph_RAG_POC/
|-- README.md                     # This file
|-- requirements.txt              # Python dependencies
|-- .env                          # Configuration (Aura + Gemini credentials)
|-- .gitignore
|
|-- data/
|   |-- seed_neo4j.py             # Populates Neo4j Aura with synthetic data
|   |-- generate_docs.py          # Creates .txt research documents
|   +-- documents/                # Auto-generated documents (5 files)
|
|-- graph/
|   |-- schema.cypher             # Neo4j constraints and indexes
|   |-- queries.py                # 5 named Cypher query functions
|   +-- graph_rag.py              # GraphRAGPipeline: graph + Gemini synthesis
|
|-- rag/
|   +-- ingest.py                 # FAISS ingestion + Gemini embeddings
|
|-- router/
|   +-- router.py                 # Hybrid query router + CompetitiveIntelEngine
|
|-- app/
|   +-- main.py                   # Interactive CLI demo application
|
+-- faiss_index/                  # Persisted FAISS vector index (auto-generated)
```

---

## Architecture

```
                    User Question
                         |
                         v
              +---------------------+
              |  Hybrid Query Router |
              |  (keyword signals)   |
              +---------------------+
               /          |          \
              v           v           v
        [Graph RAG]  [Vanilla RAG]  [Both]
              |           |           |
              v           v           v
        [Neo4j Aura]  [FAISS]    [Neo4j Aura
         Cypher        Vector     + FAISS]
         Traversal     Search
              \          |          /
               \         v         /
                +----------------+
                |Context Assembly|
                +-------+--------+
                        |
                        v
                +----------------+
                | Google Gemini  |
                | (Cloud LLM)   |
                +-------+--------+
                        |
                        v
               Final Answer + Sources
```

---

## Key Concepts Demonstrated

| Capability | Vanilla RAG | Graph RAG | Hybrid |
|-----------|:-----------:|:---------:|:------:|
| Retrieve relevant documents | YES | - | YES |
| Answer "what does research say" | YES | - | YES |
| Multi-hop relationship traversal | - | YES | YES |
| Rank competitors by win count | - | YES | YES |
| Connect pain points to competitors | - | YES | YES |
| Combine structure + narrative | - | - | YES |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Activate venv: `.venv\Scripts\activate` |
| Neo4j connection refused | Check `.env` has correct Aura URI and password |
| `GOOGLE_API_KEY not set` | Add your Gemini API key to `.env` |
| `403 Forbidden` from Gemini | Verify API key at aistudio.google.com |
| FAISS index not found | Run `python rag/ingest.py --build` first |
| `pip install` fails | Try `pip install --user -r requirements.txt` |
| Slow first query | Normal -- Neo4j Aura cold starts take a few seconds |

---

## Stopping and Restarting

Your Neo4j Aura instance runs in the cloud -- it pauses automatically when inactive and resumes when you connect. No need to start/stop anything.

To run the demo again:
```bash
.venv\Scripts\activate
python app/main.py
```
