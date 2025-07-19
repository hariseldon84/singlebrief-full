# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SingleBrief is an AI-powered intelligence operative designed for managers and team leads. It consolidates team intelligence, document data, and personal sources (email, calendar, cloud files) into one unified AI interface. The tagline is "Answers from everyone. Delivered by one."

The system proactively collects, synthesizes, and delivers intelligence rather than requiring users to chase updates across multiple sources. It includes persistent memory that learns over time and adapts to user/team behavior patterns.

## Architecture Overview

SingleBrief follows a modular architecture with 10 core modules working together:

### Core System Components

1. **Orchestrator Agent** - Central brain that receives queries and coordinates intelligence gathering (Python, LangChain, Celery)
2. **Team Comms Crawler** - Integrates with Slack, Teams, Email to fetch contextual data (Slack API, Gmail API, MS Graph)
3. **Memory Engine** - Persistent storage for user/team-specific memory with vector embeddings (PostgreSQL, Redis, Pinecone/Weaviate)
4. **Synthesizer Engine** - AI-powered synthesis and deduplication using RAG pipelines (OpenAI/Claude)
5. **Daily Brief Generator** - Template-based brief rendering (Jinja, PDFKit, HTML)

### Supporting Infrastructure

6. **Consent & Privacy Layer** - Granular data access control and audit logging (OAuth 2.0, Admin SDKs)
7. **Dashboard & UI Layer** - Web interface for briefs, settings, and memory management (Next.js, Tailwind CSS)
8. **Integration Hub** - Extensible plugin system for third-party tools (Zapier-like engine, REST adapters)
9. **Trust Layer** - Confidence scoring and source traceability for transparency
10. **Feedback Engine** - User feedback collection for continuous improvement (embedding store, metrics pipeline)

## Key Features

- **Team Interrogation AI**: Actively queries team members with adaptive tone and context
- **Memory Engine**: Tracks decisions, conversations, and outcomes with optional user opt-in
- **Data Streams Layer**: Real-time integration with Slack, Email, Docs, Calendar, GitHub, CRMs
- **Daily Brief Generator**: Personalized TL;DR summaries for leaders
- **Trust & Transparency System**: Confidence scores, source attribution, raw data access

## Technology Stack

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

## Development Principles

### Privacy by Design
- Every data access must be scoped, logged, and consented
- Team members control what's shared vs. kept local
- Memory can be toggled off, reset, or exported
- Enterprise admin portal for compliance and policy management

### Performance Targets
- Brief response time: <3 seconds
- Brief accuracy: 90% positive feedback
- Team response compliance: 85% response rate
- Memory opt-in rate: 60%+ users
- Weekly active usage: >50% of pilot organizations

## Data Flow Architecture

The system follows this high-level data flow:
1. Team Lead Query → Orchestrator Agent
2. Orchestrator coordinates parallel data gathering from:
   - Team Comms Crawler (Slack, Teams, Email)
   - Document/Drive/Knowledge Sources
   - Calendar/Email Adapters
3. All data flows to Synthesizer Engine for consolidation
4. Trust Layer adds confidence scoring and source attribution
5. Daily Brief Generator renders final output
6. Delivery via Web UI or Email

## Module Dependencies

- **Orchestrator Agent** depends on all other modules for coordination
- **Memory Engine** is shared across Team Interrogation AI, Synthesizer, and Feedback Engine
- **Trust Layer** processes output from Synthesizer Engine
- **Integration Hub** feeds data to Team Comms Crawler and Data Streams Layer
- **Consent & Privacy Layer** controls access for all data-touching modules

## Current Status

This repository contains comprehensive documentation (PRD, architecture specs) but no implementation code yet. The project is in the design/planning phase with detailed specifications ready for development.