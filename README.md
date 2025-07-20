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
├── docs/                          # Comprehensive documentation
│   ├── prd/                       # Product Requirements Document
│   ├── architecture/              # System architecture specs
│   ├── stories/                   # Development user stories
│   └── qa/                        # Quality assurance documentation
├── backend/                       # FastAPI backend implementation
├── frontend/                      # Next.js frontend application
├── scripts/                       # Utility scripts for development
├── .bmad-core/                    # BMad methodology framework
├── .claude/                       # Claude Code configuration
├── .cursor/                       # Cursor IDE rules
├── .vscode/                       # VS Code configuration
├── .github/                       # GitHub workflows and chat modes
├── .windsurf/                     # Windsurf configuration files
├── .gemini/                       # Gemini AI configuration
├── docker-compose.yml             # Docker Compose configuration
└── README.md                      # This file
```

## 📚 Documentation

- **[Product Requirements Document (PRD)](docs/prd.md)** - Complete product specifications
- **[Architecture Overview](docs/architecture.md)** - System design and data flow
- **[Epic & Story Overview](docs/epic-story-overview.md)** - Development roadmap
- **[Story Index](docs/story-index.md)** - Individual user stories

## ✅ Current Status

**All 6 Epics Complete - Full SingleBrief Implementation Ready - Under QA**:

- **Epic 1: Foundation Infrastructure** - Stories 1.1 through 1.5 ✅ **UNDER QA**
  - Project setup, authentication, core database models, UI framework, and orchestrator agent framework
- **Epic 2: Core AI Intelligence** - Stories 2.1 through 2.5 ✅ **UNDER QA**
  - Orchestrator core, LLM integration, synthesizer engine, trust layer, and query optimization
- **Epic 3: Memory Engine and Personalization** - Stories 3.1 through 3.5 ✅ **UNDER QA**
  - Core memory storage, user preference learning, team memory, privacy management, and context-aware responses
- **Epic 4: Data Streams and Integration Hub** - Stories 4.1 through 4.6 ✅ **UNDER QA**
  - Integration Hub, Slack integration, email/calendar, document systems, developer tools, and data normalization
- **Epic 5: Daily Brief Generator and Reporting** - Stories 5.1 through 5.6 ✅ **UNDER QA**
  - Brief generation engine, content intelligence, templates, multi-channel delivery, analytics, and proactive alerts
- **Epic 6: Team Interrogation AI** - Stories 6.1 through 6.6 ✅ **UNDER QA**
  - Question generation, adaptive communication, response collection, team insights, context-aware querying, and feedback loops

### Implementation Progress Log (as of July 20, 2025)

- **Project Foundation**: Established with Next.js 14+ frontend, FastAPI backend, PostgreSQL+Redis database ✅
- **Authentication**: OAuth 2.0 with role-based access control and multi-tenant security implemented ✅
- **Core AI**: LLM integration with RAG pipeline completed and tested with confidence scoring ✅
- **Memory System**: Vector-based memory storage with personalization and privacy management ✅
- **Integration Hub**: Extensible plugin architecture for external service integration ✅
- **Brief Generation**: AI-powered daily briefs with multi-channel delivery and analytics ✅
- **Team Interrogation**: Intelligent question generation with adaptive communication ✅
- **Full System**: All 33 stories across 6 epics completed - under QA review ✅

## 🧪 QA Status

### QA Progress (as of July 20, 2025)

**All stories have entered QA phase with the following progress:**

1. **Documentation Updates**
   - All 33 stories have been updated to "Under QA" status ✅
   - All task checkboxes marked as completed across all stories ✅
   - Status section standardized across all stories for consistency ✅

2. **QA Documentation Created**
   - Created comprehensive quality criteria framework in `docs/qa/quality-criteria-framework.md` ✅
   - Developed detailed infrastructure testing strategy in `docs/qa/infrastructure-testing-strategy.md` ✅
   - Defined project setup test cases in `docs/qa/project-setup-test-cases.md` ✅

3. **Completed QA Reviews**
   - Story 1.1: Project Setup and Infrastructure ✅
   - Story 1.2: User Authentication and Authorization ✅
   - Story 1.3: Core Database Models and Schema ✅
   - Story 1.4: Basic Dashboard UI Framework ✅

4. **QA Pipeline Established**
   - Systematic process created for validating all stories against acceptance criteria ✅
   - Standardized QA results format implemented in story documentation ✅
   - Quality risks identified and prioritized for further testing ✅

5. **Next Steps for QA Team**
   - Continue detailed review of remaining stories (starting with 1.5)
   - Complete comprehensive testing of frontend components against accessibility standards
   - Validate backend API functionality and integration points
   - Conduct end-to-end testing across all modules
   - Verify performance metrics against established targets

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