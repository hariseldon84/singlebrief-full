# SingleBrief Authentication System - Detailed Task Breakdown

**Specification Reference**: auth-system-spec.md  
**Total Estimated Time**: 52 hours (2-3 weeks)  
**Developer Level**: Senior Full-Stack (FastAPI + Next.js experience required)

## 📋 Task Execution Order

### Prerequisites (Complete First)
1. ✅ Database migration keyword conflicts resolved
2. 🔄 Docker environment running (postgres + redis)
3. 🔄 Environment variables configured (.env files)
4. 🔄 Initial database migration executed

---

## Phase 1: Core Authentication Foundation (Week 1 - 24 hours)

### Task 1.1: Database Schema Migration for Auth Tables
**Priority**: P0 Critical  
**Estimated Time**: 4 hours  
**Dependencies**: Docker postgres running  

**Detailed Steps**:
1. Create migration file: `alembic revision -m "Add authentication tables"`
2. Add oauth_providers table:
   ```sql
   CREATE TABLE oauth_providers (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
       provider_type VARCHAR(50) NOT NULL CHECK (provider_type IN ('google', 'microsoft', 'slack')),
       client_id VARCHAR(255) NOT NULL,
       client_secret_encrypted TEXT NOT NULL,
       scopes TEXT[] DEFAULT ARRAY['email', 'profile'],
       is_enabled BOOLEAN DEFAULT true,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       UNIQUE(organization_id, provider_type)
   );
   ```
3. Add user_sessions table:
   ```sql
   CREATE TABLE user_sessions (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       user_id UUID REFERENCES users(id) ON DELETE CASCADE,
       refresh_token_hash VARCHAR(255) UNIQUE NOT NULL,
       device_info JSONB DEFAULT '{}',
       ip_address INET,
       user_agent TEXT,
       expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
       last_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       is_revoked BOOLEAN DEFAULT false,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   ```
4. Add api_keys table for service-to-service auth
5. Update User model with auth enhancement fields
6. Add indexes: `user_sessions(user_id, expires_at)`, `oauth_providers(organization_id)`
7. Test migration up/down

**Acceptance Criteria**:
- [ ] Migration executes without errors
- [ ] All tables created with proper constraints
- [ ] Indexes improve query performance
- [ ] Migration is reversible
- [ ] Foreign key relationships work correctly

**Files to Create/Modify**:
- `alembic/versions/xxx_add_authentication_tables.py`
- `app/models/auth.py` (new OAuth and Session models)
- `app/models/user.py` (enhance existing User model)

---

### Task 1.2: JWT Token Service Implementation
**Priority**: P0 Critical  
**Estimated Time**: 8 hours  
**Dependencies**: Database migration complete  

**Detailed Steps**:
1. Install additional dependencies:
   ```bash
   pip install python-jose[cryptography] cryptography
   ```
2. Create JWT service class:
   ```python
   # app/services/jwt_service.py
   class JWTService:
       def __init__(self):
           self.private_key = self._load_private_key()
           self.public_key = self._load_public_key()
           
       async def create_access_token(self, user: User, expires_delta: timedelta = None) -> str
       async def create_refresh_token(self, user: User) -> str  
       async def verify_token(self, token: str) -> dict
       async def decode_token(self, token: str) -> dict
       def _load_private_key(self) -> str
       def _load_public_key(self) -> str
   ```
3. Generate RSA key pair for production:
   ```bash
   openssl genrsa -out private_key.pem 2048
   openssl rsa -in private_key.pem -pubout -out public_key.pem
   ```
4. Implement token payload structure:
   ```python
   {
       "sub": user_id,
       "email": user.email,
       "org_id": user.organization_id,
       "role": user.role,
       "permissions": [...],
       "iat": issued_at,
       "exp": expires_at,
       "type": "access" | "refresh"
   }
   ```
5. Create FastAPI dependency for token validation:
   ```python
   # app/auth/dependencies.py
   async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
       # Validate JWT and return user
   ```
6. Add error handling for expired/invalid tokens
7. Write comprehensive unit tests

**Acceptance Criteria**:
- [ ] RS256 algorithm used for signing
- [ ] Access tokens expire in 30 minutes
- [ ] Refresh tokens expire in 7 days
- [ ] Token validation catches all error cases
- [ ] Performance: <50ms token creation/validation
- [ ] 100% test coverage for JWT functions

**Files to Create/Modify**:
- `app/services/jwt_service.py`
- `app/auth/dependencies.py`
- `app/core/security.py`
- `tests/test_jwt_service.py`

---

### Task 1.3: Session Management System
**Priority**: P0 Critical  
**Estimated Time**: 6 hours  
**Dependencies**: Database migration, JWT service  

**Detailed Steps**:
1. Create SessionService class:
   ```python
   # app/services/session_service.py
   class SessionService:
       async def create_session(self, user: User, device_info: dict, ip: str) -> UserSession
       async def refresh_session(self, refresh_token: str) -> TokenPair
       async def revoke_session(self, session_id: str) -> bool
       async def revoke_all_sessions(self, user_id: str) -> int
       async def cleanup_expired_sessions(self) -> int
       async def get_user_sessions(self, user_id: str) -> List[UserSession]
   ```
2. Implement refresh token hashing with bcrypt
3. Add session cleanup background task:
   ```python
   # app/tasks/auth_tasks.py
   @celery_app.task
   def cleanup_expired_sessions():
       # Run every hour to clean expired sessions
   ```
4. Implement concurrent session limits (max 5 per user)
5. Add device fingerprinting for security
6. Create session monitoring endpoints
7. Add Redis caching for active sessions

**Acceptance Criteria**:
- [ ] Refresh tokens securely hashed before storage
- [ ] Sessions auto-expire after 7 days
- [ ] Concurrent session limit enforced
- [ ] Background cleanup removes expired sessions
- [ ] Device info tracked for security monitoring
- [ ] Redis cache improves session lookup performance

**Files to Create/Modify**:
- `app/services/session_service.py`
- `app/tasks/auth_tasks.py`
- `app/models/auth.py` (UserSession model)
- `tests/test_session_service.py`

---

### Task 1.4: Basic Authentication Endpoints
**Priority**: P0 Critical  
**Estimated Time**: 6 hours  
**Dependencies**: JWT service, session management  

**Detailed Steps**:
1. Create authentication router:
   ```python
   # app/api/v1/endpoints/auth.py
   @router.post("/login/email", response_model=AuthResponse)
   async def login_with_email(credentials: EmailLoginRequest)
   
   @router.post("/logout", status_code=204)
   async def logout(current_user: User = Depends(get_current_user))
   
   @router.post("/refresh", response_model=TokenResponse) 
   async def refresh_token(refresh_request: RefreshTokenRequest)
   
   @router.get("/me", response_model=UserResponse)
   async def get_current_user_info(current_user: User = Depends(get_current_user))
   
   @router.put("/me", response_model=UserResponse)
   async def update_current_user(update_data: UserUpdateRequest, current_user: User = Depends(get_current_user))
   ```
2. Create Pydantic request/response models:
   ```python
   # app/schemas/auth.py
   class EmailLoginRequest(BaseModel):
       email: EmailStr
       password: str
       
   class AuthResponse(BaseModel):
       access_token: str
       refresh_token: str
       token_type: str = "bearer"
       expires_in: int
       user: UserResponse
   ```
3. Implement rate limiting (100 req/min per IP)
4. Add comprehensive error handling:
   - Invalid credentials (401)
   - Account locked (423)
   - Too many requests (429)
   - Server errors (500)
5. Add request/response logging for security
6. Write API integration tests

**Acceptance Criteria**:
- [ ] All endpoints return proper HTTP status codes
- [ ] Request validation prevents malformed data
- [ ] Rate limiting blocks excessive requests
- [ ] Error responses don't leak sensitive info
- [ ] Comprehensive logging for security events
- [ ] API tests cover all success/error scenarios

**Files to Create/Modify**:
- `app/api/v1/endpoints/auth.py`
- `app/schemas/auth.py`
- `app/api/v1/api.py` (include auth router)
- `tests/test_auth_endpoints.py`

---

## Phase 2: OAuth Integration (Week 2 - 24 hours)

### Task 2.1: OAuth Provider Framework
**Priority**: P1 High  
**Estimated Time**: 4 hours  
**Dependencies**: Basic auth endpoints complete  

**Detailed Steps**:
1. Create abstract OAuth provider base class:
   ```python
   # app/auth/providers/base.py
   class OAuthProvider(ABC):
       @abstractmethod
       async def get_authorization_url(self, state: str) -> str
       
       @abstractmethod  
       async def exchange_code(self, code: str, state: str) -> OAuthUserInfo
       
       @abstractmethod
       async def refresh_access_token(self, refresh_token: str) -> OAuthTokens
   ```
2. Create OAuth user info data model:
   ```python
   @dataclass
   class OAuthUserInfo:
       provider_id: str
       email: str
       name: str
       avatar_url: Optional[str]
       provider_data: Dict[str, Any]
   ```
3. Implement provider registry and factory:
   ```python
   # app/auth/providers/registry.py
   class OAuthProviderRegistry:
       def register_provider(self, name: str, provider_class: Type[OAuthProvider])
       def get_provider(self, name: str) -> OAuthProvider
       def list_providers(self) -> List[str]
   ```
4. Add OAuth configuration management
5. Create state parameter generation/validation
6. Add PKCE support for enhanced security

**Acceptance Criteria**:
- [ ] Provider framework supports multiple OAuth types
- [ ] State parameter prevents CSRF attacks
- [ ] Configuration management is secure and flexible
- [ ] Registry allows easy addition of new providers
- [ ] PKCE implementation enhances security
- [ ] Framework is testable and mockable

**Files to Create/Modify**:
- `app/auth/providers/base.py`
- `app/auth/providers/registry.py`
- `app/auth/oauth_config.py`
- `tests/test_oauth_framework.py`

---

### Task 2.2: Google OAuth Implementation
**Priority**: P1 High  
**Estimated Time**: 6 hours  
**Dependencies**: OAuth framework complete  

**Detailed Steps**:
1. Install Google OAuth dependencies:
   ```bash
   pip install google-auth google-auth-oauthlib google-auth-httplib2
   ```
2. Implement GoogleOAuthProvider:
   ```python
   # app/auth/providers/google.py
   class GoogleOAuthProvider(OAuthProvider):
       def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
           self.client_id = client_id
           self.client_secret = client_secret
           self.redirect_uri = redirect_uri
           self.scopes = ['openid', 'email', 'profile']
   ```
3. Add Google-specific user info mapping
4. Handle Google workspace domain restrictions
5. Implement token refresh functionality
6. Add Google API rate limit handling
7. Create comprehensive test suite with mocked Google API

**Implementation Details**:
```python
async def get_authorization_url(self, state: str) -> str:
    return (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"response_type=code&"
        f"client_id={self.client_id}&"
        f"redirect_uri={self.redirect_uri}&"
        f"scope={'+'.join(self.scopes)}&"
        f"state={state}&"
        f"access_type=offline&"
        f"prompt=consent"
    )

async def exchange_code(self, code: str, state: str) -> OAuthUserInfo:
    # Exchange authorization code for tokens
    # Fetch user info from Google API
    # Map to OAuthUserInfo format
```

**Acceptance Criteria**:
- [ ] Google OAuth flow works end-to-end
- [ ] User info correctly mapped from Google API
- [ ] Workspace domain restrictions enforced
- [ ] Token refresh prevents expired access
- [ ] Rate limiting handled gracefully
- [ ] Comprehensive error handling for all failure modes

**Files to Create/Modify**:
- `app/auth/providers/google.py`
- `app/api/v1/endpoints/auth.py` (add Google routes)
- `tests/test_google_oauth.py`

---

### Task 2.3: Microsoft OAuth Implementation
**Priority**: P1 High  
**Estimated Time**: 8 hours  
**Dependencies**: OAuth framework complete  

**Detailed Steps**:
1. Install Microsoft Graph dependencies:
   ```bash
   pip install msal requests
   ```
2. Implement MicrosoftOAuthProvider:
   ```python
   # app/auth/providers/microsoft.py
   class MicrosoftOAuthProvider(OAuthProvider):
       def __init__(self, client_id: str, client_secret: str, tenant_id: str):
           self.client_id = client_id
           self.client_secret = client_secret
           self.tenant_id = tenant_id
           self.authority = f"https://login.microsoftonline.com/{tenant_id}"
   ```
3. Handle multi-tenant Azure AD scenarios
4. Implement enterprise user provisioning
5. Add Microsoft Graph API integration for user details
6. Handle Azure AD group mapping to roles
7. Add conditional access policy support
8. Create comprehensive test suite

**Implementation Details**:
```python
async def exchange_code(self, code: str, state: str) -> OAuthUserInfo:
    # Use MSAL to exchange code for tokens
    # Query Microsoft Graph for user info
    # Handle enterprise attributes (department, manager, etc.)
    # Map Azure AD groups to SingleBrief roles
```

**Acceptance Criteria**:
- [ ] Azure AD integration works for single and multi-tenant
- [ ] Enterprise attributes properly mapped
- [ ] Group-based role assignment functional
- [ ] Conditional access policies respected
- [ ] Token caching optimizes performance
- [ ] Error handling covers all Microsoft-specific scenarios

**Files to Create/Modify**:
- `app/auth/providers/microsoft.py`
- `app/services/azure_ad_service.py`
- `tests/test_microsoft_oauth.py`

---

### Task 2.4: Slack OAuth Implementation
**Priority**: P1 High  
**Estimated Time**: 6 hours  
**Dependencies**: OAuth framework complete  

**Detailed Steps**:
1. Install Slack SDK:
   ```bash
   pip install slack-sdk
   ```
2. Implement SlackOAuthProvider:
   ```python
   # app/auth/providers/slack.py
   class SlackOAuthProvider(OAuthProvider):
       def __init__(self, client_id: str, client_secret: str):
           self.client_id = client_id
           self.client_secret = client_secret
           self.scopes = ['identity.basic', 'identity.email', 'identity.team']
   ```
3. Handle workspace-based authentication
4. Implement bot token management for integration
5. Add workspace member validation
6. Create user-to-workspace mapping
7. Handle Slack-specific rate limiting
8. Add comprehensive test coverage

**Implementation Details**:
```python
async def exchange_code(self, code: str, state: str) -> OAuthUserInfo:
    # Exchange code for user and bot tokens
    # Validate user is member of authorized workspace
    # Store bot token for future Slack API calls
    # Map Slack user info to SingleBrief format
```

**Acceptance Criteria**:
- [ ] Slack workspace authentication functional
- [ ] Bot token properly stored and managed
- [ ] User workspace membership validated
- [ ] Rate limiting prevents API blocks
- [ ] Integration tokens available for future features
- [ ] Error handling covers Slack-specific scenarios

**Files to Create/Modify**:
- `app/auth/providers/slack.py`
- `app/services/slack_integration_service.py`
- `tests/test_slack_oauth.py`

---

## Phase 3: Authorization & Security (Week 3 - 16 hours)

### Task 3.1: Role-Based Access Control Implementation
**Priority**: P1 High  
**Estimated Time**: 8 hours  
**Dependencies**: OAuth integration complete  

**Detailed Steps**:
1. Define permission constants:
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
       USER_MANAGE = "user:manage"
   ```
2. Create role-permission mapping:
   ```python
   class RolePermissions:
       ADMIN = [Permissions.ORG_ADMIN, Permissions.USER_MANAGE, ...]
       TEAM_LEAD = [Permissions.TEAM_MANAGE, Permissions.BRIEF_CREATE, ...]
       MEMBER = [Permissions.BRIEF_READ, Permissions.TEAM_READ, ...]
   ```
3. Implement permission checking decorators:
   ```python
   def require_permissions(*permissions: str):
       def decorator(func):
           @wraps(func)
           async def wrapper(*args, **kwargs):
               # Check user has required permissions
   ```
4. Add organization-scoped access control
5. Create FastAPI dependencies for permission checking
6. Implement permission inheritance for team hierarchies
7. Add comprehensive test coverage

**Acceptance Criteria**:
- [ ] All permissions properly defined and documented
- [ ] Role assignments function correctly
- [ ] Organization scoping prevents cross-org access
- [ ] Permission decorators integrate with FastAPI
- [ ] Team hierarchy permissions work as expected
- [ ] Performance: <10ms permission checks

**Files to Create/Modify**:
- `app/auth/permissions.py`
- `app/auth/rbac.py`
- `app/auth/dependencies.py` (enhanced)
- `tests/test_rbac.py`

---

### Task 3.2: Frontend Authentication Integration
**Priority**: P1 High  
**Estimated Time**: 10 hours  
**Dependencies**: Backend auth system complete  

**Detailed Steps**:
1. Create AuthContext and Provider:
   ```typescript
   // lib/auth/AuthContext.tsx
   interface AuthContextType {
     user: User | null;
     login: (provider: string) => Promise<void>;
     logout: () => Promise<void>;
     hasPermission: (permission: string) => boolean;
     loading: boolean;
   }
   ```
2. Implement token management:
   ```typescript
   // lib/auth/TokenManager.ts
   class TokenManager {
     getAccessToken(): string | null
     getRefreshToken(): string | null
     setTokens(access: string, refresh: string): void
     clearTokens(): void
     isTokenExpired(token: string): boolean
     refreshToken(): Promise<TokenPair>
   }
   ```
3. Create protected route component:
   ```typescript
   // components/auth/ProtectedRoute.tsx
   interface ProtectedRouteProps {
     children: React.ReactNode;
     requiredPermissions?: string[];
     fallback?: React.ReactNode;
   }
   ```
4. Add automatic token refresh with axios interceptors
5. Create login/logout UI components
6. Implement OAuth provider selection UI
7. Add error handling and user feedback
8. Create comprehensive test suite with React Testing Library

**Acceptance Criteria**:
- [ ] AuthContext provides auth state across app
- [ ] Token refresh works automatically
- [ ] Protected routes enforce permissions
- [ ] OAuth login flow intuitive and reliable
- [ ] Error states handled gracefully
- [ ] Loading states provide good UX

**Files to Create/Modify**:
- `lib/auth/AuthContext.tsx`
- `lib/auth/TokenManager.ts`
- `components/auth/ProtectedRoute.tsx`
- `components/auth/LoginPage.tsx`
- `components/auth/OAuthButtons.tsx`
- `tests/auth/auth.test.tsx`

---

### Task 3.3: Security Hardening
**Priority**: P0 Critical  
**Estimated Time**: 8 hours  
**Dependencies**: All auth components complete  

**Detailed Steps**:
1. Implement rate limiting with Redis:
   ```python
   # app/middleware/rate_limiting.py
   class RateLimitMiddleware:
       async def __call__(self, request: Request, call_next):
           # Check rate limits by IP and user
           # Return 429 if limits exceeded
   ```
2. Add comprehensive audit logging:
   ```python
   # app/services/audit_service.py
   class AuditService:
       async def log_auth_event(self, event_type: str, user_id: str, details: dict)
       async def log_failed_login(self, email: str, ip: str, reason: str)
       async def log_permission_denial(self, user_id: str, resource: str, action: str)
   ```
3. Implement account lockout after failed attempts:
   ```python
   async def handle_failed_login(self, user: User, ip: str):
       user.failed_login_attempts += 1
       if user.failed_login_attempts >= 5:
           user.locked_until = datetime.utcnow() + timedelta(minutes=30)
   ```
4. Add CSRF protection for auth flows
5. Implement session hijacking detection
6. Add security headers middleware
7. Create security monitoring alerts

**Security Measures**:
- Rate limiting: 100 requests/minute per IP
- Account lockout: 5 failed attempts = 30 minutes
- Session timeout: 8 hours of inactivity
- CSRF tokens for state changes
- Secure cookie settings (httpOnly, secure, sameSite)
- Content Security Policy headers

**Acceptance Criteria**:
- [ ] Rate limiting prevents brute force attacks
- [ ] Account lockout protects against credential stuffing
- [ ] Audit logs capture all security events
- [ ] CSRF protection prevents cross-site attacks
- [ ] Session security prevents hijacking
- [ ] Security headers protect against common attacks

**Files to Create/Modify**:
- `app/middleware/rate_limiting.py`
- `app/middleware/security_headers.py`
- `app/services/audit_service.py`
- `app/core/security.py` (enhanced)
- `tests/test_security.py`

---

## Phase 4: Testing & Documentation (Week 4 - 12 hours)

### Task 4.1: Comprehensive Test Suite
**Priority**: P1 High  
**Estimated Time**: 8 hours  
**Dependencies**: All implementation complete  

**Test Categories**:
1. **Unit Tests** (app/tests/unit/):
   - JWT service functions
   - OAuth provider implementations
   - Permission checking logic
   - Session management
   - Database model operations

2. **Integration Tests** (app/tests/integration/):
   - Complete OAuth flows
   - API endpoint authentication
   - Database transactions
   - Redis caching behavior

3. **Security Tests** (app/tests/security/):
   - JWT token tampering attempts
   - Rate limiting effectiveness
   - SQL injection prevention
   - CSRF attack prevention
   - Session security validation

4. **Performance Tests** (app/tests/performance/):
   - Authentication latency measurement
   - Concurrent user simulation
   - Database query optimization
   - Memory usage monitoring

**Target Coverage**: 95% code coverage minimum

---

### Task 4.2: API Documentation & Developer Guide
**Priority**: P2 Medium  
**Estimated Time**: 4 hours  
**Dependencies**: All implementation complete  

**Documentation Deliverables**:
1. **OpenAPI/Swagger Documentation**:
   - All authentication endpoints documented
   - Request/response examples
   - Error code explanations
   - Security scheme definitions

2. **Developer Integration Guide**:
   - Quick start guide for new developers
   - OAuth provider setup instructions
   - Common integration patterns
   - Troubleshooting guide

3. **Security Best Practices**:
   - Token handling recommendations
   - HTTPS configuration
   - Environment variable security
   - Monitoring and alerting setup

---

## 🚀 Ready for Implementation

This specification provides a complete roadmap for implementing a production-ready authentication system for SingleBrief. Each task includes:

- ✅ **Clear acceptance criteria**
- ✅ **Detailed implementation steps**  
- ✅ **Time estimates based on senior developer experience**
- ✅ **Dependencies and prerequisites**
- ✅ **File structure and code examples**
- ✅ **Comprehensive testing requirements**

**Total Estimated Time**: 52 hours over 3-4 weeks  
**Next Step**: Execute `/execute-tasks` to begin Phase 1 implementation

---

## 📊 Progress Tracking

Use this checklist to track implementation progress:

### Phase 1 Progress (24 hours)
- [ ] Task 1.1: Database Schema Migration (4h)
- [ ] Task 1.2: JWT Token Service (8h)  
- [ ] Task 1.3: Session Management (6h)
- [ ] Task 1.4: Basic Auth Endpoints (6h)

### Phase 2 Progress (24 hours)  
- [ ] Task 2.1: OAuth Framework (4h)
- [ ] Task 2.2: Google OAuth (6h)
- [ ] Task 2.3: Microsoft OAuth (8h)
- [ ] Task 2.4: Slack OAuth (6h)

### Phase 3 Progress (16 hours)
- [ ] Task 3.1: RBAC System (8h)
- [ ] Task 3.2: Frontend Integration (10h)
- [ ] Task 3.3: Security Hardening (8h)

### Phase 4 Progress (12 hours)
- [ ] Task 4.1: Comprehensive Testing (8h)
- [ ] Task 4.2: Documentation (4h)

**Status**: Ready for development team assignment and sprint planning.