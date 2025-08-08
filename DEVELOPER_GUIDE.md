# SingleBrief Developer Guide

## Quick Start

### Prerequisites
- Node.js 18+ 
- Python 3.11+
- Docker & Docker Compose

### Setup (Automated)
```bash
./setup.sh
```

### Setup (Manual)
```bash
# 1. Install root dependencies
npm install

# 2. Start services
npm run docker:up

# 3. Install frontend dependencies
npm run setup:frontend

# 4. Install backend dependencies  
npm run setup:backend

# 5. Run migrations
npm run migrate
```

## Development Commands

### Starting Services
```bash
# Start both frontend and backend
npm run dev

# Start frontend only (Next.js)
npm run dev:frontend
# Runs on: http://localhost:3000

# Start backend only (FastAPI)
npm run dev:backend  
# Runs on: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Building & Testing
```bash
# Run all tests
npm run test

# Run linting
npm run lint

# Build frontend
npm run build
```

### Database Management
```bash
# Run migrations
npm run migrate

# Rollback migration
npm run migrate:down

# Reset database
npm run migrate:reset
```

### Docker Services
```bash
# Start PostgreSQL & Redis
npm run docker:up

# Stop services
npm run docker:down

# View logs
npm run docker:logs
```

## Project Structure

```
singlebrief/
├── frontend/          # Next.js 14 + TypeScript
│   ├── app/           # App Router pages
│   ├── components/    # React components
│   ├── lib/           # Utilities
│   └── package.json   # Frontend dependencies
├── backend/           # FastAPI + Python
│   ├── app/           # Application code
│   ├── alembic/       # Database migrations
│   ├── tests/         # Python tests
│   └── requirements.txt
├── docs/              # Documentation
├── nginx/             # Reverse proxy config
└── docker-compose.yml # Development services
```

## Technology Stack

### Frontend
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State**: Zustand + React Query
- **UI Components**: Radix UI + Headless UI
- **Testing**: Jest + React Testing Library

### Backend  
- **Framework**: FastAPI
- **Language**: Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis
- **Migrations**: Alembic
- **Testing**: pytest

### Infrastructure
- **Development**: Docker Compose
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Proxy**: Nginx (production)

## Common Issues & Solutions

### Issue: `npm run dev` fails with ENOENT
**Solution**: Run from correct directory
```bash
# ❌ Wrong - from root without package.json
npm run dev

# ✅ Correct - use root package.json scripts
npm run dev:frontend
# or
cd frontend && npm run dev
```

### Issue: Database connection failed
**Solution**: Ensure Docker services are running
```bash
npm run docker:up
# Wait 10 seconds for services to start
npm run migrate
```

### Issue: Port already in use
**Solution**: Check what's using the ports
```bash
# Check ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend  
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill processes if needed
kill -9 <PID>
```

### Issue: Python virtual environment issues
**Solution**: Recreate virtual environment
```bash
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Development Workflow

1. **Start Services**: `npm run docker:up`
2. **Start Development**: `npm run dev` 
3. **Make Changes**: Edit code in respective directories
4. **Test Changes**: `npm run test`
5. **Commit**: Follow conventional commits
6. **Push**: Create PR for review

## Environment Variables

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Backend (.env)
```env
DATABASE_URL=postgresql://singlebrief:singlebrief_dev@localhost:5432/singlebrief
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
```

## Debugging

### Frontend Debugging
- Use browser DevTools
- React DevTools extension
- Next.js debug mode: `DEBUG=* npm run dev:frontend`

### Backend Debugging  
- Use FastAPI auto-docs: http://localhost:8000/docs
- Enable debug logging in `main.py`
- Use `pdb` for breakpoints

### Database Debugging
```bash
# Connect to database
docker exec -it singlebrief_postgres psql -U singlebrief -d singlebrief

# View tables
\dt

# View table structure  
\d table_name
```

## Contributing

1. Create feature branch from `main`
2. Make changes following code style
3. Add tests for new functionality
4. Ensure all tests pass
5. Create PR with detailed description
6. Address review feedback
7. Merge when approved

## Support

- **Documentation**: Check `/docs` directory
- **Issues**: Create GitHub issue
- **Questions**: Ask in team chat