#!/bin/bash

# SingleBrief Development Setup Script
set -e

echo "🚀 Setting up SingleBrief development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [[ ! -f "docker-compose.yml" ]]; then
    print_error "Please run this script from the SingleBrief root directory"
    exit 1
fi

# Check system requirements
print_status "Checking system requirements..."

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js found: $NODE_VERSION"
else
    print_error "Node.js not found. Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python found: $PYTHON_VERSION"
else
    print_error "Python 3.11+ not found. Please install Python from https://python.org/"
    exit 1
fi

# Check Docker
if command -v docker &> /dev/null; then
    print_success "Docker found"
else
    print_error "Docker not found. Please install Docker from https://docker.com/"
    exit 1
fi

# Start Docker services
print_status "Starting Docker services (PostgreSQL & Redis)..."
docker-compose up -d postgres redis

# Wait for services to be ready
print_status "Waiting for database to be ready..."
sleep 10

# Install frontend dependencies
print_status "Installing frontend dependencies..."
cd frontend
npm install
print_success "Frontend dependencies installed"
cd ..

# Install backend dependencies
print_status "Installing backend dependencies..."
cd backend
if [[ ! -d "venv" ]]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
print_success "Backend dependencies installed"

# Run database migrations
print_status "Running database migrations..."
alembic upgrade head
print_success "Database migrations completed"

cd ..

print_success "🎉 Setup completed successfully!"
print_status ""
print_status "To start development:"
print_status "  Frontend: npm run dev:frontend"
print_status "  Backend:  npm run dev:backend"
print_status "  Both:     npm run dev"
print_status ""
print_status "Other useful commands:"
print_status "  View logs: npm run docker:logs"
print_status "  Run tests: npm run test"
print_status "  Stop services: npm run docker:down"