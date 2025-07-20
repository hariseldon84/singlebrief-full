# 📐 Coding Standards

## Table of Contents
- [General Standards](#general-standards)
- [Backend Standards (Python/FastAPI)](#backend-standards-pythonfastapi)
- [Frontend Standards (Next.js/React)](#frontend-standards-nextjsreact)
- [Database Standards](#database-standards)
- [Testing Standards](#testing-standards)
- [Documentation Standards](#documentation-standards)
- [Security Standards](#security-standards)

## General Standards

### Code Style
- **Readability**: Code should prioritize readability and maintainability over cleverness
- **Comments**: Use comments to explain "why" not "what" (code should be self-documenting)
- **Error Handling**: Proper error handling with meaningful error messages
- **Naming**: Use descriptive names for variables, functions, classes, and files

### Version Control
- **Branching**: Use feature branches with the naming convention `feature/feature-name`
- **Commits**: Write clear commit messages that explain the purpose of the change
- **Pull Requests**: All changes must go through PR review before merging
- **CI/CD**: All PRs must pass CI checks before merging

## Backend Standards (Python/FastAPI)

### Python Code Style
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines
- Use type hints for all function parameters and return values
- Maximum line length: 88 characters (Black formatter default)
- Use docstrings for all public functions, classes, and methods

### Project Structure
```
backend/
├── app/
│   ├── api/            # API routes
│   │   └── endpoints/  # Route handlers
│   ├── auth/           # Authentication logic
│   ├── core/           # Core application code
│   ├── models/         # SQLAlchemy models
│   └── schemas/        # Pydantic schemas
├── alembic/            # Database migrations
├── tests/              # Test modules
└── main.py             # Application entry point
```

### API Design
- Use RESTful principles for API design
- Use appropriate HTTP methods and status codes
- Versioned API endpoints (e.g., `/api/v1/resource`)
- Comprehensive API documentation using OpenAPI/Swagger

### FastAPI Best Practices
- Use dependency injection for shared resources
- Use Pydantic for request/response validation
- Implement proper exception handling with custom exception handlers
- Use async/await for I/O-bound operations

## Frontend Standards (Next.js/React)

### JavaScript/TypeScript Style
- Use TypeScript for type safety
- Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Use ESLint and Prettier for code formatting
- Use modern ES6+ features where appropriate

### Component Structure
- Prefer functional components with hooks over class components
- Follow the single responsibility principle for components
- Use component composition for reusable UI elements
- Keep components small and focused

### State Management
- Use React Context for global state when appropriate
- Use Zustand for more complex state management
- Avoid prop drilling through multiple component levels
- Separate UI state from business logic

### Styling
- Use Tailwind CSS for component styling
- Follow a consistent design system
- Use design tokens for colors, spacing, typography, etc.
- Ensure responsive design across all screen sizes

## Database Standards

### Schema Design
- Follow normalization principles (avoid redundancy)
- Use appropriate data types
- Define proper indexes for performance
- Document table relationships and constraints

### Migrations
- All schema changes must be done through migrations
- Migrations must be reversible when possible
- Test migrations in a staging environment before production
- Document complex migrations

### Queries
- Optimize database queries for performance
- Use query parameters to prevent SQL injection
- Implement pagination for large data sets
- Add appropriate indexes for query patterns

## Testing Standards

### Backend Testing
- Unit tests for all business logic
- Integration tests for API endpoints
- Use pytest for testing framework
- Aim for >80% code coverage

### Frontend Testing
- Unit tests for utility functions and hooks
- Component tests with React Testing Library
- End-to-end tests for critical user flows
- Test responsive behavior across viewports

### Test Organization
- Tests should mirror the structure of the application code
- Use fixtures and factories for test data
- Mock external dependencies
- Use CI/CD pipeline for automated testing

## Documentation Standards

### Code Documentation
- Document complex algorithms and business logic
- Use type hints and docstrings for Python code
- Use JSDoc comments for JavaScript/TypeScript
- Keep documentation updated with code changes

### API Documentation
- Document all API endpoints with examples
- Include request/response schemas
- Document error responses and status codes
- Keep API documentation in sync with implementation

### User Documentation
- Provide clear user guides for features
- Include screenshots or diagrams where helpful
- Update documentation with each feature release
- Collect user feedback to improve documentation

## Security Standards

### Authentication & Authorization
- Follow OAuth 2.0 best practices
- Implement proper role-based access control
- Use secure password storage (bcrypt)
- Implement proper token validation and expiration

### Data Protection
- Encrypt sensitive data at rest and in transit
- Implement proper input validation
- Follow least privilege principle
- Regular security audits and vulnerability scanning

### API Security
- Rate limiting to prevent abuse
- CORS configuration for frontend access
- Input validation for all API endpoints
- Protection against common attacks (CSRF, XSS, etc.)

### Dependency Management
- Regular updates of dependencies
- Security scanning of dependencies
- Lock dependency versions
- Document security-related dependency updates
