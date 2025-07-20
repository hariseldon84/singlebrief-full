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

## ✅ Current Status

**Epic 1 & 2 Complete, Epic 3 Completed, Epic 4 In Progress**:

- **Epic 1: Foundation Infrastructure** - Stories 1.1 through 1.5 completed (Ready for Review)
  - Project setup, authentication, core database models, UI framework, and orchestrator agent framework
- **Epic 2: Core AI Intelligence** - Stories 2.1 through 2.5 completed (Ready for Review)
  - Orchestrator core, LLM integration, synthesizer engine, trust layer, and query optimization
- **Epic 3: Memory Engine and Personalization** - Stories 3.1 through 3.5 completed
  - Core memory storage, user preference learning, team memory, privacy management, and context-aware responses
- **Epic 4: Data Streams and Integration Hub** - Story 4.1 under development
  - Integration Hub Framework currently in progress

### Implementation Progress Log (as of July 20, 2025)

- **Project Foundation**: Established with Next.js 14+ frontend, FastAPI backend, PostgreSQL+Redis database
- **Authentication**: OAuth 2.0 with role-based access control and multi-tenant security implemented
- **Core AI**: LLM integration with RAG pipeline completed and tested with confidence scoring
- **Memory System**: Vector-based memory storage with personalization and privacy management
- **Current Work**: Building extensible plugin architecture for external service integration

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- Python 3.11+
- Docker & Docker Compose
- Git

### Development Setup

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd singlebrief_fullversion
   ```

2. **Environment Configuration**
   ```bash
   # Frontend
   cp frontend/.env.local.example frontend/.env.local
   
   # Backend  
   cp backend/.env.example backend/.env
   ```

3. **Start with Docker (Recommended)**
   ```bash
   docker-compose up -d
   ```
   
   **Services Available:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Celery Flower: http://localhost:5555

## 🤝 Contributing

This project follows the **BMad methodology** for structured development. See the `.bmad-core/` directory for agent definitions, workflows, and templates.

## � Next Developer Guidelines

### Current Priority: Integration Hub Framework (Story 4.1)

The next developer should focus on completing Story 4.1 (Integration Hub Framework) which is currently in progress. This component is critical as it enables all future external service integrations.

#### Getting Started
1. Review the architecture design in `docs/architecture/1-core-modules.md` focusing on the Integration Hub section
2. Examine Story 4.1 requirements in `docs/stories/4.1.integration-hub-framework.md`
3. Continue implementation following these priorities:
   - First complete Plugin Architecture Design (Task 1)
   - Then implement Standardized Connector Interface (Task 2)
   - Follow with Health Monitoring, Rate Limiting, and Error Handling

#### Development Standards
- Maintain test coverage above 80% for all new code
- Follow established patterns for error handling and logging
- Document all public APIs and extension points
- Ensure backward compatibility with existing services

#### Known Issues
- Pay special attention to rate limiting implementation as it needs to work across multiple plugin instances. Also, a lot of the work is done by using Claude and other MCP servers as initiator and pair programer. Critical tasks , functions and logics are driven by manual intervention and thinking.
- Consider sandboxing requirements carefully as plugins need proper isolation

Once Story 4.1 is complete, proceed to Story 4.2 (Slack Integration) which will be the first integration built on this framework.

## �📝 License

Copyright (c) 2025 Anand Arora

All Rights Reserved.

---

**Built with privacy-first principles and enterprise-grade security in mind.**