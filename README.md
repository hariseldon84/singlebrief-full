# SingleBrief

> **"Answers from everyone. Delivered by one."**

An AI-powered intelligence operative designed for managers and team leads that consolidates team intelligence, document data, and personal sources into one unified AI interface.

## 🎯 What is SingleBrief?

SingleBrief transforms how managers get updates by **proactively collecting, synthesizing, and delivering intelligence** rather than requiring users to chase updates across multiple sources. It includes persistent memory that learns over time and adapts to user/team behavior patterns.

Instead of spending hours gathering status updates from team members, documents, and tools, SingleBrief delivers synthesized, high-trust answers from fragmented information streams.

## ✨ Key Features

- **🧠 Team Interrogation AI**: Actively queries team members with adaptive tone and context
- **🔁 Memory Engine**: Tracks decisions, conversations, and outcomes with optional user opt-in
- **🗂️ Data Streams Layer**: Real-time integration with Slack, Email, Docs, Calendar, GitHub, CRMs
- **📊 Daily Brief Generator**: Personalized TL;DR summaries for leaders
- **👁️ Trust & Transparency System**: Confidence scores, source attribution, raw data access

## 🏗️ Architecture Overview

SingleBrief follows a modular architecture with 10 core modules:

### Core System Components
1. **Orchestrator Agent** - Central brain coordinating intelligence gathering
2. **Team Comms Crawler** - Integrates with Slack, Teams, Email
3. **Memory Engine** - Persistent storage with vector embeddings
4. **Synthesizer Engine** - AI-powered synthesis using RAG pipelines
5. **Daily Brief Generator** - Template-based brief rendering

### Supporting Infrastructure
6. **Consent & Privacy Layer** - Granular data access control
7. **Dashboard & UI Layer** - Web interface for briefs and settings
8. **Integration Hub** - Extensible plugin system
9. **Trust Layer** - Confidence scoring and source traceability
10. **Feedback Engine** - Continuous improvement through user feedback

## 🔧 Technology Stack

- **Frontend**: Next.js + Tailwind CSS
- **Backend**: FastAPI or Node.js
- **Authentication**: OAuth 2.0 + Role-based access control
- **Storage**: PostgreSQL + S3 + Redis
- **Vector Database**: Weaviate or Pinecone
- **AI/LLM**: OpenAI/Claude with RAG pipelines
- **Task Queue**: Celery
- **Hosting**: Vercel (Frontend) + AWS/GCP (Backend)
- **CI/CD**: GitHub Actions + Docker
- **Monitoring**: Sentry, Datadog, Prometheus

## 🎯 Target Users

- **Mid-to-senior managers** leading distributed teams
- **Founders & startup execs** managing chaos across channels
- **Department heads** (Marketing, Sales, HR, Ops) needing updates without meetings
- **Product & Engineering leaders** juggling multiple systems and blockers

## 🚀 Performance Targets

- **Brief response time**: <3 seconds
- **Brief accuracy**: 90% positive feedback
- **Team response compliance**: 85% response rate
- **Memory opt-in rate**: 60%+ users
- **Weekly active usage**: >50% of pilot organizations

## 🔒 Privacy by Design

- Every data access is scoped, logged, and consented
- Team members control what's shared vs. kept local
- Memory can be toggled off, reset, or exported
- Enterprise admin portal for compliance and policy management

## 📊 Data Flow

1. **Team Lead Query** → Orchestrator Agent
2. **Orchestrator coordinates** parallel data gathering from:
   - Team Comms Crawler (Slack, Teams, Email)
   - Document/Drive/Knowledge Sources
   - Calendar/Email Adapters
3. **All data flows** to Synthesizer Engine for consolidation
4. **Trust Layer** adds confidence scoring and source attribution
5. **Daily Brief Generator** renders final output
6. **Delivery** via Web UI or Email

## 📁 Project Structure

```
singlebrief_fullversion/
├── docs/                           # Comprehensive documentation
│   ├── prd/                       # Product Requirements Document
│   ├── architecture/              # System architecture specs
│   └── stories/                   # Development user stories
├── .bmad-core/                    # BMad methodology framework
├── .claude/                       # Claude Code configuration
├── .cursor/                       # Cursor IDE rules
├── .github/                       # GitHub workflows and chat modes
└── README.md                      # This file
```

## 📚 Documentation

- **[Product Requirements Document (PRD)](docs/prd.md)** - Complete product specifications
- **[Architecture Overview](docs/architecture.md)** - System design and data flow
- **[Epic & Story Overview](docs/epic-story-overview.md)** - Development roadmap
- **[Story Index](docs/story-index.md)** - Individual user stories

## 🚧 Current Status

This repository contains comprehensive documentation (PRD, architecture specs, user stories) but **no implementation code yet**. The project is in the **design/planning phase** with detailed specifications ready for development.

## 🤝 Contributing

This project follows the **BMad methodology** for structured development. See the `.bmad-core/` directory for agent definitions, workflows, and templates.

## 📝 License

Copyright (c) 2025 Anand Arora

All Rights Reserved.

---

**Built with privacy-first principles and enterprise-grade security in mind.**