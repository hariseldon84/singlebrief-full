# SingleBrief API Authentication & Authorization System Specification

**Feature ID**: SB-AUTH-001  
**Priority**: Critical (P0)  
**Estimated Development Time**: 2-3 weeks  
**Dependencies**: Database migration completion, Docker environment setup  

## 🎯 Feature Overview

### Purpose
Implement a comprehensive, production-ready authentication and authorization system for SingleBrief's API that supports multiple OAuth providers, role-based access control, and enterprise security requirements.

### Success Criteria
- ✅ Secure JWT-based authentication with refresh tokens
- ✅ Multi-provider OAuth integration (Google, Microsoft, Slack)
- ✅ Role-based access control (RBAC) with organization scoping
- ✅ Enterprise features: SSO, MFA, audit logging
- ✅ 99.9% uptime with <200ms auth response times
- ✅ GDPR compliance with privacy controls

### User Impact
- **Team Leads**: Secure access to intelligence briefs and team data
- **Team Members**: Controlled access to relevant organizational information
- **Administrators**: Complete user management and access control
- **Developers**: Robust API security for all integrations

## 🏗️ Technical Architecture

### Authentication Flow
```
1. User initiates login → OAuth provider selection
2. Provider authorization → callback with code
3. Token exchange → JWT access + refresh tokens
4. API requests → Bearer token validation
5. Token refresh → automatic renewal before expiry
```

### Authorization Model
```
Organization → Teams → Users → Roles → Permissions
├── Admin (full org access)
├── TeamLead (team + reporting access)
├── Member (team data access)
└── ReadOnly (limited query access)
```

### Security Features
- **JWT Access Tokens**: 30-minute expiry, RS256 signing
- **Refresh Tokens**: 7-day expiry, secure HTTP-only cookies
- **Rate Limiting**: 100 requests/minute per user
- **Audit Logging**: All auth events tracked and monitored
- **Session Management**: Concurrent session limits, device tracking

## 📋 Technical Specifications

### Database Schema Updates

#### New Tables
```sql
-- OAuth provider configurations
CREATE TABLE oauth_providers (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    provider_type VARCHAR(50) NOT NULL, -- google, microsoft, slack
    client_id VARCHAR(255) NOT NULL,
    client_secret_encrypted TEXT NOT NULL,
    scopes TEXT[] DEFAULT ARRAY['email', 'profile'],
    is_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User sessions and refresh tokens  
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) UNIQUE NOT NULL,
    device_info JSONB,
    ip_address INET,
    expires_at TIMESTAMP NOT NULL,
    last_used_at TIMESTAMP DEFAULT NOW(),
    is_revoked BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- API keys for service-to-service auth
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    permissions TEXT[] DEFAULT ARRAY[],
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Enhanced User Model
```python
# Add to existing User model
class User(Base):
    # ... existing fields ...
    
    # Enhanced auth fields
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False) 
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    sessions: Mapped[List["UserSession"]] = relationship(back_populates="user")
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="user")
```

### API Endpoints

#### Authentication Endpoints
```python
# /api/v1/auth/
POST   /login/oauth/{provider}     # Initiate OAuth flow
POST   /login/callback/{provider}  # Handle OAuth callback  
GET    /login/providers           # List available providers
POST   /logout                    # Revoke current session
POST   /refresh                   # Refresh access token
GET    /me                        # Current user profile
PUT    /me                        # Update user profile
```

#### User Management Endpoints  
```python
# /api/v1/users/ (Admin only)
GET    /                         # List organization users
POST   /                         # Create user (invite)
GET    /{user_id}                # Get user details
PUT    /{user_id}                # Update user
DELETE /{user_id}                # Deactivate user
PUT    /{user_id}/role           # Update user role
GET    /{user_id}/sessions       # List user sessions
DELETE /{user_id}/sessions/{id}  # Revoke specific session
```

#### Organization Management
```python
# /api/v1/organizations/
GET    /current                  # Current org details
PUT    /current                  # Update org settings
GET    /current/oauth-providers  # List OAuth configs
POST   /current/oauth-providers  # Add OAuth provider
PUT    /current/oauth-providers/{id}  # Update provider
DELETE /current/oauth-providers/{id}  # Remove provider
```

### FastAPI Implementation

#### Core Authentication Service
```python
# app/services/auth_service.py
class AuthenticationService:
    async def authenticate_oauth(self, provider: str, code: str) -> AuthResult
    async def refresh_token(self, refresh_token: str) -> TokenPair
    async def revoke_session(self, session_id: str) -> bool
    async def verify_jwt_token(self, token: str) -> User
    async def get_user_permissions(self, user: User) -> List[str]
```

#### OAuth Provider Implementations
```python
# app/auth/providers/
class GoogleOAuthProvider:
    async def get_authorization_url(self) -> str
    async def exchange_code(self, code: str) -> OAuthUserInfo
    
class MicrosoftOAuthProvider:
    async def get_authorization_url(self) -> str  
    async def exchange_code(self, code: str) -> OAuthUserInfo

class SlackOAuthProvider:
    async def get_authorization_url(self) -> str
    async def exchange_code(self, code: str) -> OAuthUserInfo
```

#### Permission System
```python
# app/auth/permissions.py
class Permissions:
    # Brief management
    BRIEF_READ = "brief:read"
    BRIEF_CREATE = "brief:create"
    BRIEF_DELETE = "brief:delete"
    
    # Team management  
    TEAM_READ = "team:read"
    TEAM_MANAGE = "team:manage"
    
    # Organization admin
    ORG_ADMIN = "org:admin"
    ORG_USER_MANAGE = "org:user:manage"
    
    # Memory and AI
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    AI_QUERY = "ai:query"

class RolePermissions:
    ADMIN = [Permissions.ORG_ADMIN, ...]
    TEAM_LEAD = [Permissions.TEAM_MANAGE, Permissions.BRIEF_CREATE, ...]
    MEMBER = [Permissions.BRIEF_READ, Permissions.AI_QUERY, ...]
    READ_ONLY = [Permissions.BRIEF_READ]
```

### Frontend Integration

#### Next.js Authentication Provider
```typescript
// lib/auth/AuthProvider.tsx
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  
  const login = async (provider: string) => { /* OAuth flow */ };
  const logout = async () => { /* Clear tokens */ };
  const refreshToken = async () => { /* Auto refresh */ };
  
  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
```

#### Protected Route Component
```typescript
// components/auth/ProtectedRoute.tsx
export const ProtectedRoute = ({ 
  children, 
  requiredPermissions = [],
  fallback = <LoginPage />
}) => {
  const { user, hasPermissions } = useAuth();
  
  if (!user) return fallback;
  if (!hasPermissions(requiredPermissions)) return <UnauthorizedPage />;
  
  return <>{children}</>;
};
```

## 🧪 Testing Strategy

### Unit Tests
- JWT token generation/validation
- OAuth provider implementations  
- Permission checking logic
- Database model operations
- Session management functions

### Integration Tests
- Full OAuth flows for each provider
- API endpoint authentication
- Role-based access control
- Token refresh mechanisms
- Audit logging functionality

### Security Tests
- JWT token tampering attempts
- Rate limiting effectiveness
- SQL injection prevention
- XSS protection validation
- Session hijacking prevention

### Performance Tests
- Authentication latency (<200ms)
- Concurrent user handling (1000+ users)
- Database query optimization
- Memory usage under load
- Token refresh efficiency

## 📚 Implementation Tasks

### Phase 1: Core Authentication (Week 1)
- [ ] **Task 1.1**: Database schema migration for auth tables
  - Create oauth_providers, user_sessions, api_keys tables
  - Update User model with enhanced auth fields
  - Add proper indexes and constraints
  - **Estimated**: 4 hours

- [ ] **Task 1.2**: JWT token service implementation
  - RS256 token signing with key rotation
  - Access token (30 min) + refresh token (7 days) 
  - Token validation middleware
  - **Estimated**: 8 hours

- [ ] **Task 1.3**: Session management system
  - Refresh token storage and validation
  - Session creation/revocation
  - Device tracking and concurrent session limits
  - **Estimated**: 6 hours

- [ ] **Task 1.4**: Basic authentication endpoints
  - /login, /logout, /refresh, /me endpoints
  - Request/response models with Pydantic
  - Error handling and validation
  - **Estimated**: 6 hours

### Phase 2: OAuth Integration (Week 2)
- [ ] **Task 2.1**: OAuth provider framework
  - Abstract base provider class
  - Provider registration and discovery
  - Configuration management
  - **Estimated**: 4 hours

- [ ] **Task 2.2**: Google OAuth implementation
  - Authorization URL generation
  - Token exchange and user info retrieval
  - Scope validation and consent handling
  - **Estimated**: 6 hours

- [ ] **Task 2.3**: Microsoft OAuth implementation  
  - Azure AD integration
  - Enterprise user provisioning
  - Group and role mapping
  - **Estimated**: 8 hours

- [ ] **Task 2.4**: Slack OAuth implementation
  - Workspace-based authentication
  - Bot token management
  - Channel access permissions
  - **Estimated**: 6 hours

### Phase 3: Authorization & Security (Week 3)
- [ ] **Task 3.1**: Role-based access control
  - Permission definition and checking
  - Role assignment and inheritance
  - Organization-scoped access control
  - **Estimated**: 8 hours

- [ ] **Task 3.2**: Frontend authentication integration
  - AuthProvider context implementation
  - Protected route components
  - Login/logout UI components
  - Automatic token refresh handling
  - **Estimated**: 10 hours

- [ ] **Task 3.3**: Security hardening
  - Rate limiting implementation
  - Audit logging for all auth events
  - Account lockout after failed attempts
  - CSRF protection for auth flows
  - **Estimated**: 8 hours

- [ ] **Task 3.4**: User management interface
  - Admin dashboard for user management
  - OAuth provider configuration UI
  - Session monitoring and revocation
  - **Estimated**: 12 hours

### Phase 4: Testing & Documentation (Week 4)
- [ ] **Task 4.1**: Comprehensive test suite
  - Unit tests for all auth components
  - Integration tests for OAuth flows
  - Security penetration testing
  - Performance and load testing
  - **Estimated**: 16 hours

- [ ] **Task 4.2**: API documentation
  - OpenAPI/Swagger documentation
  - Authentication guide for developers
  - OAuth provider setup instructions
  - **Estimated**: 6 hours

- [ ] **Task 4.3**: Production deployment prep
  - Environment variable configuration
  - SSL certificate setup
  - Database migration scripts
  - Monitoring and alerting setup
  - **Estimated**: 8 hours

## 🚀 Deployment Considerations

### Environment Variables
```bash
# JWT Configuration
JWT_SECRET_KEY=your-rsa-private-key
JWT_PUBLIC_KEY=your-rsa-public-key
JWT_ALGORITHM=RS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth Providers
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
SLACK_CLIENT_ID=your-slack-client-id
SLACK_CLIENT_SECRET=your-slack-client-secret

# Security
RATE_LIMIT_PER_MINUTE=100
MAX_FAILED_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=30
MAX_CONCURRENT_SESSIONS=5
```

### Production Security Checklist
- [ ] SSL/TLS encryption for all auth endpoints
- [ ] Secure cookie configuration for refresh tokens
- [ ] Rate limiting and DDoS protection
- [ ] Regular security audit and penetration testing
- [ ] OAuth client secret rotation schedule
- [ ] JWT signing key rotation (quarterly)
- [ ] Audit log retention and monitoring
- [ ] GDPR compliance for user data handling

## 📊 Success Metrics

### Performance Targets
- **Authentication Latency**: <200ms for token validation
- **OAuth Flow Time**: <3 seconds end-to-end
- **Concurrent Users**: Support 1000+ simultaneous auth requests
- **Uptime**: 99.9% availability for auth services

### Security Metrics
- **Failed Auth Rate**: <1% of total attempts
- **Token Compromise**: 0 incidents per quarter
- **Audit Coverage**: 100% of auth events logged
- **Compliance**: 100% GDPR and SOC2 requirements met

### User Experience Metrics
- **Login Success Rate**: >98% first-attempt success
- **SSO Adoption**: >80% of enterprise users
- **Session Duration**: Average 4-6 hours active use
- **Support Tickets**: <5% auth-related issues

## 🔗 Integration Points

### Existing SingleBrief Components
- **Memory Engine**: User-scoped memory access control
- **Team Interrogation**: Role-based team querying permissions  
- **Brief Generation**: User preference and access validation
- **Integration Hub**: OAuth token management for external services
- **Audit System**: Authentication event logging

### External Dependencies
- **OAuth Providers**: Google, Microsoft, Slack APIs
- **Database**: PostgreSQL for user and session storage
- **Redis**: Token caching and rate limiting
- **Monitoring**: Sentry for error tracking, DataDog for metrics

This specification provides a comprehensive roadmap for implementing a production-ready authentication and authorization system that will serve as the foundation for all other SingleBrief features.

---

**Next Steps**: Review and approve this specification, then proceed with `/execute-tasks` to begin Phase 1 implementation.