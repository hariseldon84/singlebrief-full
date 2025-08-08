# SingleBrief - Agent OS Project Configuration

## Project Overview

**Product Name**: SingleBrief  
**Product Type**: AI-Powered Intelligence Platform  
**Stage**: Development (Post-Design, Implementation Phase)  
**Architecture**: Full-Stack Web Application with AI/ML Pipeline  

## Product Description

SingleBrief is an AI-powered intelligence operative designed for managers and team leads. It consolidates team intelligence, document data, and personal sources (email, calendar, cloud files) into one unified AI interface. The tagline is "Answers from everyone. Delivered by one."

The system proactively collects, synthesizes, and delivers intelligence rather than requiring users to chase updates across multiple sources. It includes persistent memory that learns over time and adapts to user/team behavior patterns.

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis
- **Task Queue**: Celery with Flower monitoring
- **AI/ML**: OpenAI, Anthropic, LangChain
- **Vector DB**: Pinecone/Weaviate
- **Authentication**: OAuth 2.0, JWT

### Frontend
- **Framework**: Next.js 14.0.4 with TypeScript
- **UI**: Tailwind CSS, Radix UI, Framer Motion
- **State**: Zustand, React Query
- **Forms**: React Hook Form with Zod validation

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx
- **Development**: Hot reload, automated testing
- **Monitoring**: Structured logging, Sentry integration

## Current Development Status

### ✅ COMPLETED (35/35 Stories)
- **Epic 1**: Foundation Infrastructure (5/5 stories)
- **Epic 2**: Core AI Intelligence (5/5 stories)
- **Epic 3**: Memory Engine (5/5 stories)
- **Epic 4**: Data Streams Integration (6/6 stories)
- **Epic 5**: Daily Brief Generator (6/6 stories)
- **Epic 6**: Team Interrogation AI (6/6 stories)

### 🚧 CURRENT STATUS
- **Phase**: Post-Documentation, Implementation Verification
- **Database**: Models complete, migration setup needs keyword conflict resolution
- **Backend**: Comprehensive code structure implemented
- **Frontend**: Complete UI framework with component library
- **Integration**: All major services integrated (Slack, Email, Documents, etc.)

## Architecture Modules

### Core System (5 modules)
1. **Orchestrator Agent** - Central intelligence coordination
2. **Team Comms Crawler** - Multi-platform communication integration
3. **Memory Engine** - Persistent learning and context storage
4. **Synthesizer Engine** - AI-powered data consolidation
5. **Daily Brief Generator** - Personalized report generation

### Supporting Infrastructure (5 modules)
6. **Consent & Privacy Layer** - GDPR-compliant data governance
7. **Dashboard & UI Layer** - Modern web interface
8. **Integration Hub** - Extensible third-party connections
9. **Trust Layer** - Confidence scoring and transparency
10. **Feedback Engine** - Continuous improvement system

## Key Features

- **Team Interrogation AI**: Proactive team member querying
- **Memory Engine**: Decision tracking and conversation history
- **Multi-Source Integration**: Slack, Teams, Email, Google Drive, GitHub
- **Daily Briefs**: Personalized TL;DR summaries
- **Trust & Transparency**: Source attribution and confidence scoring
- **Privacy by Design**: Granular consent management

## Development Principles

### Privacy First
- Every data access scoped, logged, and consented
- Team member control over data sharing
- GDPR compliance with audit trails
- Enterprise admin portal for policy management

### Performance Targets
- Brief response time: <3 seconds
- Brief accuracy: 90% positive feedback
- Team response compliance: 85% response rate
- Memory opt-in rate: 60%+ users

## Agent OS Integration Points

### Primary Workflows
1. **Feature Development** - New AI capabilities and integrations
2. **Database Operations** - Schema updates and migrations
3. **API Enhancement** - Backend service improvements
4. **UI/UX Development** - Frontend component creation
5. **Integration Testing** - Multi-service validation
6. **Performance Optimization** - System-wide improvements

### Code Quality Standards
- **Backend**: Black, isort, flake8, mypy for Python
- **Frontend**: ESLint, Prettier, TypeScript strict mode
- **Testing**: Jest (frontend), pytest (backend)
- **Documentation**: Comprehensive inline and architectural docs

## Next Development Priorities

1. **Database Migration Resolution** - Fix SQLAlchemy reserved keyword conflicts
2. **Integration Testing** - End-to-end workflow validation
3. **AI Model Integration** - Connect OpenAI/Anthropic services
4. **Performance Optimization** - Database indexing and caching
5. **Security Hardening** - OAuth implementation and API security
6. **Production Deployment** - CI/CD pipeline and infrastructure setup

## Project Structure

```
singlebrief_fullversion/
├── backend/           # FastAPI application
├── frontend/          # Next.js application
├── docs/              # Comprehensive documentation
├── nginx/             # Web server configuration
├── scripts/           # Deployment and utility scripts
└── docker-compose.yml # Development environment
```

This project represents a mature, well-architected AI platform ready for implementation completion and deployment.