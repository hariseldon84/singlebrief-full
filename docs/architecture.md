
# 🧱 System Architecture – SingleBrief

---

## 🧩 1. Core Modules

| Module Name | Description | Technologies |
|-------------|-------------|---------------|
| **Orchestrator Agent** | Brain of the system that receives queries and decides what intel to gather from where. | Python, LangChain, Celery (task queue) |
| **Team Comms Crawler** | Hooks into Slack, Teams, Emails to fetch context. | Slack API, Gmail API, MS Graph |
| **Memory Engine** | Long-term user-specific + team-level memory storage. | PostgreSQL / Redis / Vector DB (Pinecone, Weaviate) |
| **Synthesizer Engine** | Summarizes, deduplicates, and resolves contradictions across sources. | OpenAI / Claude + RAG pipelines |
| **Daily Brief Generator** | Renders briefs (text, visual blocks, etc.) via templates. | Jinja, PDFKit, HTML renderer |
| **Consent & Privacy Layer** | Controls data access per user/team/org + audit logs. | OAuth 2.0, Admin SDKs, Vault |
| **Dashboard & UI Layer** | Web UI for briefs, settings, audit, memory. | Next.js or React + Tailwind CSS |
| **Integration Hub** | Scalable plug-in system for tools: Slack, Drive, GitHub, Zoom, CRMs, Notion, etc. | Zapier-like engine + REST adapters |
| **Trust Layer** | Explains confidence scores, source trace, and enables raw data view. | Custom scoring logic + source metadata |
| **Feedback Engine** | Collects “Was this helpful?” and tunes outputs + prompts. | Embedding store + metrics pipeline |

---

## 📡 2. Data Flow Diagram (Simplified)

```
         +-------------------+         +---------------------+
         |  Team Lead Query  |  --->   |  Orchestrator Agent |
         +-------------------+         +---------------------+
                                               |
         +-------------------------------------+--------------------------------------+
         |                                     |                                      |
  +---------------+                  +-------------------+                   +------------------+
  | Team Comms    |                  | Docs / Drive /    |                   | Calendar / Email |
  | Crawler       |                  | Knowledge Sources |                   | Adapter          |
  +---------------+                  +-------------------+                   +------------------+
         |                                     |                                      |
         +-------------> Synthesizer Engine <----------------------------------------+
                                  |
                          +----------------+
                          | Trust Layer    |
                          | + Confidence   |
                          +----------------+
                                  |
                      +--------------------------+
                      | Daily Brief Generator     |
                      +--------------------------+
                                  |
                          +----------------+
                          | Web UI / Email |
                          +----------------+
```

---

## 🔐 3. Privacy-by-Design Principles

- Every data access is scoped, logged, and consented
- Team members control what’s shared with lead vs what stays local
- Memory can be toggled off, reset, or exported
- Enterprise Admin Portal for compliance & policy

---

## 📦 4. Deployment Stack

| Layer | Tech Suggestion |
|-------|-----------------|
| Frontend | Next.js + Tailwind |
| Backend | FastAPI or Node.js |
| Auth | OAuth 2.0 + Role-based access |
| Storage | Postgres + S3 + Redis |
| Vector DB | Weaviate or Pinecone |
| LLM | OpenAI / Claude + RAG |
| Hosting | Vercel (FE) + AWS/GCP (BE) |
| CI/CD | GitHub Actions + Docker |
| Logging & Monitoring | Sentry, Datadog, Prometheus |

