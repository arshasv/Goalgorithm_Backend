# Feature 02: Authentication & Authorization

## Feature Overview

JWT-based authentication system supporting two user roles (Team Leader, Organizer) with registration, login, password management (change, forgot, reset via OTP), and admin user creation. All protected endpoints enforce role-based access control via FastAPI dependencies.

## Purpose & Requirements

- Secure user registration with email domain validation
- JWT token-based stateless authentication
- Role-based access control (TEAM_LEADER vs ORGANIZER)
- Password hashing with bcrypt
- Password reset flow via email OTP
- Admin can create team accounts with temporary passwords

## Related Specifications

- `architecture/system-architecture.md` — Auth Provider design
- `architecture/error-handling-architecture.md` — Auth-related exception flow
- `api/team-management-api.md` — Register endpoint specification
- `api/error-responses.md` — 401/403 error responses

## User/Business Flow

### Team Leader Registration
```
Team Leader submits: username, email, password, team_name (A-E), team_leader_name
    ↓
Validate email domain (allowed list)
    ↓
Check team_name is valid (A-E)
    ↓
Check team not already registered
    ↓
Hash password with bcrypt
    ↓
Create UserModel (role=TEAM_LEADER) + TeamModel
    ↓
Link user to team (user.team_id = team.id)
    ↓
Generate JWT token
    ↓
Return token + user info
```

### Team Leader Login
```
Email + password submitted
    ↓
Find user by email
    ↓
Verify bcrypt hash
    ↓
Check user.is_active
    ↓
Generate JWT token (24hr expiry)
    ↓
Return token + user info
```

### Organizer Login
```
Email + password submitted
    ↓
Find user by email where role=ORGANIZER
    ↓
Verify bcrypt hash
    ↓
Generate JWT token
    ↓
Return token + user info
```

### Password Reset Flow
```
1. Forgot Password: email → generate 6-digit OTP → store in password_reset_otps → send email
2. Reset Password: email + otp + new_password → verify OTP → update password → mark OTP used
```

### Admin User Creation
```
Organizer submits: username, email, team_name, team_leader_name
    ↓
Generate random 8-char temporary password
    ↓
Create UserModel + TeamModel + link
    ↓
Hash temp password, store in DB
    ↓
Send welcome email with temp password via AgentMail
    ↓
Return user info
```

## How the Feature is Created

1. Auth service handles all business logic (hashing, JWT, OTP)
2. Auth bearer class extracts tokens from requests
3. Dependency functions validate roles
4. Route handlers delegate to auth service

## How the Feature Works Internally

### JWT Token Structure
```python
payload = {
    "sub": str(user.id),      # User ID as subject
    "exp": expiry_datetime     # 24-hour expiry
}
token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
```

### Token Verification Flow
1. `JWTBearer` extracts `Authorization: Bearer <token>` header
2. `auth_service.decode_token(token)` decodes and validates
3. `get_current_user()` looks up user by ID from token
4. `get_current_organizer()` / `get_current_team_leader()` checks role

### Password Hashing
```python
# Hashing
hashed = pwd_context.hash(plain_password)

# Verification
verified = pwd_context.verify(plain_password, hashed_password)
```

### OTP Flow
1. Generate 6-digit random code: `str(random.randint(100000, 999999))`
2. Store in `PasswordResetOtpModel` with 15-minute expiry
3. Send via AgentMail email service
4. On reset: verify OTP matches and not expired and not used
5. Update password, mark OTP as used

## Architecture & Components Involved

```
app/auth/
├── auth_service.py        ← Password hashing, JWT create/decode, get_current_user
└── auth_bearer.py         ← HTTPBearer dependency class

app/api/
├── auth_routes.py         ← Team leader auth endpoints
└── admin_auth_routes.py   ← Organizer auth endpoints

app/schemas/
├── auth_schema.py         ← Register/Login/Token/User response schemas
└── admin_auth_schema.py   ← Admin create user schemas

app/services/
└── auth_service.py        ← Business logic for registration, login, password management

app/utils/
└── email_validator.py     ← Email domain whitelist
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/auth/auth_service.py` | 35 | Password hashing, JWT encode/decode |
| `app/auth/auth_bearer.py` | 27 | JWTBearer dependency |
| `app/schemas/auth_schema.py` | 132 | All auth Pydantic schemas |
| `app/schemas/admin_auth_schema.py` | 16 | Admin user creation schema |
| `app/services/auth_service.py` | 320 | Auth business logic |
| `app/api/auth_routes.py` | 425 | Team leader auth endpoints |
| `app/api/admin_auth_routes.py` | 126 | Admin auth endpoints |
| `app/utils/email_validator.py` | 16 | Email domain validation |

### Key Classes & Functions

- `AuthService.register(username, email, password, team_name, team_leader_name)` → Creates user + team + returns token
- `AuthService.login(email, password)` → Verifies credentials + returns token
- `AuthService.admin_login(email, password)` → Organizer login
- `AuthService.create_user(username, email, team_name, team_leader_name)` → Admin creates team account
- `AuthService.forgot_password(email)` → Generates + emails OTP
- `AuthService.reset_password(email, otp, new_password)` → Verifies OTP + resets password
- `AuthService.change_password(user, old_password, new_password)` → Changes own password
- `AuthService.create_access_token(data, expires_delta)` → Creates JWT
- `AuthService.decode_token(token)` → Decodes JWT
- `get_password_hash(password)` → bcrypt hash
- `verify_password(plain, hashed)` → bcrypt verify
- `get_current_user(token, db)` → UserModel from JWT
- `get_current_organizer(user)` → Validates ORGANIZER role
- `get_current_team_leader(user)` → Validates TEAM_LEADER role
- `validate_email_domain(email)` → bool

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/register` | None | Team leader registration |
| POST | `/api/v1/auth/login` | None | Team leader login |
| POST | `/api/v1/auth/forgot-password` | None | Request password reset OTP |
| POST | `/api/v1/auth/reset-password` | None | Reset password with OTP |
| POST | `/api/v1/auth/change-password` | TEAM_LEADER | Change own password |
| POST | `/api/v1/admin/auth/login` | None | Organizer login |
| POST | `/api/v1/admin/auth/create-user` | ORGANIZER | Create team account |
| GET | `/api/v1/admin/auth/users` | ORGANIZER | List all users |

### Request/Response Schemas

**POST `/auth/register` Request:**
```json
{
  "username": "team_a_leader",
  "email": "leader@gmail.com",
  "password": "securepass",
  "team_name": "A",
  "team_leader_name": "John Doe"
}
```

**POST `/auth/register` Response (200):**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "username": "team_a_leader",
    "email": "leader@gmail.com",
    "role": "TEAM_LEADER",
    "team_id": "..."
  }
}
```

## Database/Data Models Involved

### `users` Table (`UserModel`)
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| username | String | unique |
| email | String | unique |
| password_hash | String | not null |
| role | Enum (TEAM_LEADER, ORGANIZER) | not null |
| team_id | UUID | FK → teams.id, nullable |
| is_active | Boolean | default True |
| created_at | DateTime | server_default=now |
| updated_at | DateTime | onupdate=now |

### `password_reset_otps` Table (`PasswordResetOtpModel`)
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| email | String | not null |
| otp_code | String | not null |
| expires_at | DateTime | not null |
| is_used | Boolean | default False |
| created_at | DateTime | server_default=now |

## Configuration/Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET_KEY` | Yes | Secret key for JWT signing |
| `JWT_ALGORITHM` | No (default: HS256) | JWT signing algorithm |
| `JWT_EXPIRY_HOURS` | No (default: 24) | Token lifetime in hours |
| `AGENTMAIL_API_KEY` | No | For sending OTP emails |
| `AGENTMAIL_INBOX_ID` | No | Email inbox identifier |

## Authentication/Authorization Requirements

- Registration/Login endpoints: No auth required
- Change Password: Requires valid JWT with TEAM_LEADER role
- Admin endpoints: Requires valid JWT with ORGANIZER role
- JWTBearer dependency: Validates token presence and expiry

## Important Classes, Functions, Services, Modules

### `JWTBearer` (`app/auth/auth_bearer.py`)
FastAPI dependency class. Extends `HTTPBearer`. Validates Bearer token from Authorization header. Raises 403 if not authenticated.

### `EmailValidator` (`app/utils/email_validator.py`)
Whitelist of allowed email domains: `gmail.com`, `opentrends.com`, `opentrends.net`, `fifa-scoring.com`. Called during registration to validate email domain.

## Request/Response Flow

```
Client → POST /auth/register
    ↓
auth_routes.py → validate schema
    ↓
auth_service.register()
    ↓
validate_email_domain()
check_team_availability()
get_password_hash()
user_repo.create() + team_repo.create()
create_access_token()
    ↓
Return {access_token, user}
```

## Data Flow

```
Registration: Request → Schema Validation → Service → Repository → DB
Login:        Request → Schema Validation → Service → Repository → DB → JWT
Password OTP: Request → Service → Repository → DB + Email API
Reset:        Request → Service → Repository (verify OTP) → DB (update password)
```

## State Management

- JWT tokens are stateless (no server-side session)
- OTP codes stored in `password_reset_otps` table with expiry
- User active/inactive status tracked in `users.is_active`

## Error Handling

| Scenario | HTTP Code | Error Code |
|----------|-----------|------------|
| Duplicate email | 409 | DUPLICATE_USER |
| Duplicate username | 409 | DUPLICATE_USER |
| Team already registered | 409 | DUPLICATE_TEAM |
| Invalid credentials | 401 | INVALID_CREDENTIALS |
| Invalid OTP | 400 | INVALID_OTP |
| Expired OTP | 400 | OTP_EXPIRED |
| Email domain not allowed | 400 | INVALID_EMAIL_DOMAIN |
| Team name not A-E | 422 | VALIDATION_ERROR |
| Insufficient permissions | 403 | FORBIDDEN |

## Validation

- Email domain whitelist enforced at registration
- Password minimum length enforced by Pydantic schema
- Team name must be A-E (single uppercase letter)
- OTP must be 6 digits
- OTP expiry checked (15 minutes)

## External Dependencies/Integrations

- `python-jose` — JWT encoding/decoding
- `passlib[bcrypt]` — Password hashing
- `AgentMail API` — Sending welcome emails and OTP codes

## Deployment/Runtime Considerations

- JWT secret must be strong and unique per environment
- AgentMail credentials optional (graceful fallback if missing)
- OTP expiry is 15 minutes — clock sync important in distributed deploys

## Edge Cases

- User registering with already-registered email → 409
- Login attempt for deactivated user → 403
- OTP request flood → No rate limiting (potential vulnerability)
- JWT token expiry not checked server-side (checked on decode only)
- Admin creating user with already-registered email → 409

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_api.py` | Registration, login, auth flow (30+ tests) |
| `tests/test_schemas.py` | Auth schema validation |

Tests verify:
- Successful registration creates user + team
- Login returns valid JWT
- Protected endpoints reject unauthenticated requests
- Role-based access control works
- Duplicate registration rejected

## Known Limitations/Technical Debt

- No rate limiting on login/OTP endpoints (brute force risk)
- No refresh token mechanism (24hr fixed expiry)
- No account lockout after failed attempts
- Email validation is a simple domain whitelist
- OTP is 6-digit numeric only (low entropy)
- No email verification flow (just domain check)

## Dependencies on Other Features

- **Team Management** — Registration creates TeamModel records
- **Email Service** — Welcome emails and OTP emails sent via AgentMail
- **Exception Handling** — Uses global exception handlers for error responses

## Step-by-Step Implementation Sequence

1. Create `app/auth/auth_service.py` with password hashing utilities
2. Create `app/auth/auth_bearer.py` with JWTBearer class
3. Create `app/schemas/auth_schema.py` with all auth schemas
4. Create `app/schemas/admin_auth_schema.py` with admin schemas
5. Create `app/services/auth_service.py` with registration, login, password management
6. Create `app/utils/email_validator.py` with domain whitelist
7. Create `app/api/auth_routes.py` with team leader endpoints
8. Create `app/api/admin_auth_routes.py` with admin endpoints
9. Create `app/models/user.py` with UserModel ORM
10. Create `app/models/password_reset_otp.py` with OTP model
11. Create `app/repositories/user_repository.py` with user/OTP queries
12. Wire auth dependencies in `app/api/deps.py`
13. Register auth routers in `app/api/__init__.py`
14. Run Alembic migration for users + password_reset_otps tables
15. Write tests for registration, login, password flows
