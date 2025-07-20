# 📁 Source Tree Structure

## Table of Contents
- [Project Overview](#project-overview)
- [Root Directory](#root-directory)
- [Backend Structure](#backend-structure)
- [Frontend Structure](#frontend-structure)
- [Documentation Structure](#documentation-structure)
- [Configuration Files](#configuration-files)

## Project Overview

SingleBrief follows a modern monorepo structure with clear separation between frontend, backend, and documentation. The project is organized to maximize developer productivity while maintaining separation of concerns and modularity.

## Root Directory

```
singlebrief_fullversion/
├── .github/                    # GitHub Actions workflows and configurations
├── .bmad-core/                 # BMad methodology framework resources
├── .claude/                    # Claude AI configurations
├── .cursor/                    # Cursor IDE settings
├── backend/                    # Backend FastAPI application
├── docs/                       # Project documentation
├── frontend/                   # Next.js frontend application
├── docker-compose.yml          # Development environment setup
└── README.md                   # Project overview
```

## Backend Structure

The backend is built with FastAPI and follows a modular structure with clear separation of concerns.

```
backend/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration scripts
│   ├── env.py                  # Alembic environment configuration
│   └── script.py.mako          # Migration script template
├── app/                        # Main application package
│   ├── api/                    # API routes and handlers
│   │   ├── endpoints/          # Route handlers by resource
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── users.py        # User management endpoints
│   │   │   └── ...             # Other resource endpoints
│   │   ├── dependencies.py     # Shared API dependencies
│   │   └── router.py           # Main API router configuration
│   ├── auth/                   # Authentication and authorization
│   │   ├── auth_backend.py     # Auth backend implementation
│   │   ├── dependencies.py     # Auth-specific dependencies
│   │   ├── oauth.py            # OAuth providers
│   │   ├── permissions.py      # Permission classes
│   │   └── utils.py            # Authentication utilities
│   ├── core/                   # Core application code
│   │   ├── config.py           # Application configuration
│   │   ├── events.py           # Application events
│   │   └── security.py         # Security utilities
│   ├── models/                 # SQLAlchemy models
│   │   ├── base.py             # Base model class
│   │   ├── user.py             # User model
│   │   └── ...                 # Other database models
│   ├── schemas/                # Pydantic schemas
│   │   ├── auth.py             # Auth-related schemas
│   │   ├── user.py             # User schemas
│   │   └── ...                 # Other resource schemas
│   └── services/               # Business logic services
│       ├── ai/                 # AI-related services
│       │   ├── llm.py          # LLM integration
│       │   ├── rag.py          # RAG implementation
│       │   └── embedding.py    # Text embedding services
│       ├── integration/        # External service integration
│       │   ├── slack.py        # Slack integration
│       │   └── ...             # Other integrations
│       └── ...                 # Other services
├── tests/                      # Test modules
│   ├── conftest.py             # Test configuration
│   ├── api/                    # API tests
│   ├── services/               # Service tests
│   └── ...                     # Other test modules
├── .env.example                # Environment variable template
├── Dockerfile                  # Docker configuration
├── alembic.ini                 # Alembic configuration
├── main.py                     # Application entry point
└── requirements.txt            # Python dependencies
```

## Frontend Structure

The frontend is built with Next.js and follows a modern React application structure with clear separation between pages, components, and utilities.

```
frontend/
├── app/                        # App Router pages and layout
│   ├── (auth)/                 # Authentication pages
│   │   ├── login/              # Login page
│   │   ├── register/           # Registration page
│   │   └── ...                 # Other auth pages
│   ├── dashboard/              # Dashboard pages
│   │   ├── page.tsx            # Dashboard main page
│   │   ├── integrations/       # Integration settings
│   │   ├── settings/           # User settings
│   │   └── ...                 # Other dashboard pages
│   ├── layout.tsx              # Root layout
│   └── page.tsx                # Home/landing page
├── src/                        # Source code
│   ├── components/             # UI components
│   │   ├── common/             # Shared components
│   │   │   ├── Button.tsx      # Button component
│   │   │   ├── Card.tsx        # Card component
│   │   │   └── ...             # Other common components
│   │   ├── dashboard/          # Dashboard-specific components
│   │   ├── forms/              # Form components
│   │   └── ...                 # Other component categories
│   ├── hooks/                  # Custom React hooks
│   │   ├── useAuth.ts          # Authentication hook
│   │   ├── useBrief.ts         # Brief-related hook
│   │   └── ...                 # Other custom hooks
│   ├── lib/                    # Utility libraries
│   │   ├── api.ts              # API client
│   │   ├── auth.ts             # Auth utilities
│   │   └── ...                 # Other utilities
│   ├── services/               # Service modules
│   │   ├── api/                # API service wrappers
│   │   ├── analytics.ts        # Analytics service
│   │   └── ...                 # Other services
│   ├── store/                  # State management
│   │   ├── authStore.ts        # Auth-related state
│   │   ├── briefStore.ts       # Brief-related state
│   │   └── ...                 # Other state modules
│   ├── styles/                 # Global styles
│   │   └── globals.css         # Global CSS
│   ├── types/                  # TypeScript type definitions
│   │   ├── auth.ts             # Auth-related types
│   │   ├── user.ts             # User-related types
│   │   └── ...                 # Other type definitions
│   └── utils/                  # Utility functions
│       ├── date.ts             # Date utilities
│       ├── formatting.ts       # Text formatting utilities
│       └── ...                 # Other utilities
├── tests/                      # Test files
│   ├── components/             # Component tests
│   ├── hooks/                  # Hook tests
│   └── ...                     # Other test categories
├── .env.local.example          # Environment variable template
├── Dockerfile                  # Docker configuration
├── jest.config.js              # Jest configuration
├── jest.setup.js               # Jest setup file
├── next-env.d.ts               # Next.js type definitions
├── next.config.js              # Next.js configuration
├── package.json                # Node.js dependencies
├── postcss.config.js           # PostCSS configuration
├── tailwind.config.js          # Tailwind CSS configuration
└── tsconfig.json               # TypeScript configuration
```

## Documentation Structure

The documentation is organized by topic, with separate directories for product requirements, architecture, and user stories.

```
docs/
├── architecture/              # System architecture specifications
│   ├── 1-core-modules.md      # Core module descriptions
│   ├── 2-data-flow-diagram-simplified.md  # Data flow diagrams
│   ├── 3-privacy-by-design-principles.md  # Privacy architecture
│   ├── 4-deployment-stack.md  # Deployment specifications
│   ├── coding-standards.md    # Coding standards and conventions
│   ├── source-tree.md         # Source code structure
│   ├── tech-stack.md          # Technology stack details
│   └── index.md               # Architecture overview
├── prd/                       # Product Requirements Document
│   ├── 1-product-overview.md  # Product overview
│   ├── 2-goals-success-criteria.md  # Goals and metrics
│   ├── 3-key-features-functionality.md  # Features
│   ├── 4-target-users-personas.md  # User personas
│   ├── 5-assumptions-dependencies.md  # Assumptions
│   ├── 6-success-metrics-kpis.md  # Success metrics
│   ├── epic-1-foundation-infrastructure.md  # Epic 1 details
│   ├── epic-2-core-ai-intelligence.md  # Epic 2 details
│   ├── epic-3-memory-engine.md  # Epic 3 details
│   ├── epic-4-data-streams-integration.md  # Epic 4 details
│   ├── epic-5-daily-brief-generator.md  # Epic 5 details
│   ├── epic-6-team-interrogation-ai.md  # Epic 6 details
│   └── index.md               # PRD overview
├── stories/                   # User stories
│   ├── 1.1.project-setup-infrastructure.md  # Story 1.1
│   ├── 1.2.user-authentication-authorization.md  # Story 1.2
│   ├── ...                    # Other stories
├── architecture.md            # Architecture overview
├── brainstorming.md           # Project brainstorming notes
├── epic-story-overview.md     # Epic and story structure
├── frontend-dev-instructions.md  # Frontend development guide
├── prd.md                     # Product Requirements overview
├── raw_prompts.md             # AI prompt templates
├── story-index.md             # Story index and status
├── terraform_infra(donotread).md  # Infrastructure as code
└── ui-design-guide.md         # UI design guidelines
```

## Configuration Files

Important configuration files in the project:

```
# Docker Configuration
docker-compose.yml             # Development environment setup

# Backend Configuration
backend/.env.example           # Environment variable template
backend/alembic.ini            # Database migration configuration
backend/requirements.txt       # Python dependencies

# Frontend Configuration
frontend/.env.local.example    # Environment variable template
frontend/next.config.js        # Next.js configuration
frontend/tailwind.config.js    # Tailwind CSS configuration
frontend/package.json          # Node.js dependencies
frontend/tsconfig.json         # TypeScript configuration

# CI/CD Configuration
.github/workflows/             # GitHub Actions workflows
```

## Convention Standards

The project follows these naming and organization conventions:

### Files and Directories
- Use kebab-case for documentation files: `file-name.md`
- Use snake_case for Python files: `file_name.py`
- Use PascalCase for React components: `ComponentName.tsx`
- Use camelCase for other JavaScript/TypeScript files: `fileName.ts`

### Code Organization
- Group related functionality in directories
- Keep files focused on a single responsibility
- Separate business logic from presentation
- Use consistent patterns across similar files
