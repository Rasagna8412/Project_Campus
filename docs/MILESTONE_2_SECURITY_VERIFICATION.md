# Project Campus — Milestone 2 Security Verification Gate Report

**Review Date:** October 15, 2026  
**Auditor Role:** Senior Application Security Engineer  
**Baseline Git Commit:** `fd7aa0a` (`feat: complete milestone 2 secure authentication, authorization, and student onboarding`)  
**Evaluation Scope:** Milestone 2 Authentication, Authorization, Session Lifecycle, Data Isolation, and Privacy Scaffolding  

---

## 1. Executive Summary & Verification Decision

Project Campus underwent an independent, evidence-based application security inspection following the completion of Milestone 2. The review encompassed authentication flows, session handling, token mechanics, authorization enforcement, password security, brute-force mitigation, account erasure, and automated test coverage.

### Formal Readiness Decision:
> **READY FOR MILESTONE 3 WITH DOCUMENTED NON-BLOCKING LIMITATIONS**

The implementation provides genuine cryptographic hashing (bcrypt), robust JWT signing, strict authenticated identity extraction (preventing IDOR), cascaded account erasure, and role-based guards. Defects identified during the gate review (silent fallback secret in production, registration rate-limit reset bypass, and unauthenticated student route role checks) have been remediated with minimal, justified fixes and covered by 12 new automated security tests (36/36 backend tests passing, 10/10 frontend tests passing). Remaining operational limitations (in-memory rate limiter, stateless access token revocation window) are documented with concrete production upgrade paths.

---

## 2. Files Inspected

The following repository components were independently reviewed line-by-line:

| Component | File Path | Focus Area |
| :--- | :--- | :--- |
| **Cryptography & Limiter** | [`backend/app/core/security.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/core/security.py) | Bcrypt work factor, JWT issuance/decoding, `AuthRateLimiter` logic |
| **System Configuration** | [`backend/app/core/config.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/core/config.py) | Secret keys, CORS settings, cookie policies, environment toggles |
| **Dependencies & Guards** | [`backend/app/api/deps.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/api/deps.py) | `get_current_user`, `require_role`, `get_current_student`, token fallback |
| **Authentication Endpoints** | [`backend/app/api/v1/endpoints/auth.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/api/v1/endpoints/auth.py) | `/register`, `/login`, `/logout`, `/me`, cookie headers, rate limiting |
| **Student Endpoints** | [`backend/app/api/v1/endpoints/student.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/api/v1/endpoints/student.py) | `/profile`, `/onboarding`, `/account` (DPDP erasure), identity derivation |
| **Curricula Endpoints** | [`backend/app/api/v1/endpoints/curricula.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/api/v1/endpoints/curricula.py) | Public read-only taxonomy retrieval |
| **Database Models** | [`backend/app/models/identity.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/models/identity.py) | User, Role, UserRole, StudentProfile, StudentProfileSubject cascades |
| **Alembic Migrations** | [`backend/alembic/versions/eeac6986a79e_milestone_2_auth_and_onboarding.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/alembic/versions/eeac6986a79e_milestone_2_auth_and_onboarding.py) | Table definitions, unique constraints, foreign keys |
| **Application Entry & CORS**| [`backend/app/main.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/main.py) | CORS origins, credentials, global exception sanitization |
| **Frontend Auth State** | [`frontend/src/context/AuthContext.tsx`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/frontend/src/context/AuthContext.tsx) | Session storage, token lifecycle, state initialization |
| **Frontend API Client** | [`frontend/src/services/api.ts`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/frontend/src/services/api.ts) | Request headers, token storage, timeout, error parsing |
| **Automated Test Suites** | [`tests/test_auth.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/tests/test_auth.py), [`tests/test_authorization.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/tests/test_authorization.py), [`tests/test_error_handling.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/tests/test_error_handling.py) | Backend security assertions, IDOR checks, validation |
| **Verification Pipeline** | [`scripts/verify_milestone_2.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/scripts/verify_milestone_2.py) | Multi-stage cross-stack verification execution |

---

## 3. Security Findings & Remediations Registry

### Finding Summary

| ID | Title | Severity | Status | Scope |
| :--- | :--- | :---: | :---: | :---: |
| **SEC-01** | Missing Production Validation for Default `SECRET_KEY` | **MEDIUM** | **RESOLVED** | Configuration |
| **SEC-02** | Registration Rate Limiter Reset on Successful Registration | **LOW** | **RESOLVED** | Rate Limiting |
| **SEC-03** | Student Endpoints Lacked Explicit `STUDENT` Role Guard | **LOW** | **RESOLVED** | Authorization |
| **SEC-04** | Rate Limiter State Bleed Between Pytest Execution Units | **LOW** | **RESOLVED** | Testing |
| **SEC-05** | Stateless Access Tokens Reusable After Logout Until Expiry | **INFORMATIONAL** | **DOCUMENTED** | Session Lifecycle |
| **SEC-06** | In-Memory Sliding-Window Limiter Not Distributed Across Workers | **INFORMATIONAL** | **DOCUMENTED** | Scalability |

---

### Detailed Findings

#### Finding SEC-01: Missing Production Validation for Default `SECRET_KEY`
* **Severity:** **MEDIUM** (Production Blocker if unaddressed)
* **Code Evidence:** [`backend/app/core/config.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/core/config.py#L34)
  ```python
  SECRET_KEY: str = "dev-insecure-secret-key-change-in-production-campus-2026-xyz"
  ```
* **Reproduction / Verification Method:**
  Instantiating `Settings(ENVIRONMENT="production")` without setting `SECRET_KEY` would succeed silently, using the hardcoded default key to sign production tokens.
* **Actual Impact:**
  An attacker could forge valid administrative or student JWTs in production if the administrator neglected to set `SECRET_KEY`.
* **Remediation Applied:**
  Added a Pydantic `model_validator(mode="after")` to `Settings` that strictly asserts: when `ENVIRONMENT == "production"`, `SECRET_KEY` must be $\ge 32$ characters and must not contain `"dev-insecure"`. Also enforces `AUTH_COOKIE_SECURE = True` automatically. Tested via `test_production_secret_key_validation`.

---

#### Finding SEC-02: Registration Rate Limiter Reset on Successful Registration
* **Severity:** **LOW** (Milestone 2 Defect)
* **Code Evidence:** [`backend/app/api/v1/endpoints/auth.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/api/v1/endpoints/auth.py)
  ```python
  # Previous code:
  if existing_user:
      auth_rate_limiter.record_attempt(rate_limit_id)
      raise HTTPException(...)
  ...
  auth_rate_limiter.reset(rate_limit_id)  # Cleared attempts on every success!
  ```
* **Reproduction / Verification Method:**
  A script issuing 50 registration requests with unique emails from the same IP would never be throttled because `record_attempt` was only called on duplicates, and `reset` wiped the counter on every success.
* **Actual Impact:**
  Automated bots could mass-create thousands of dummy accounts from a single IP.
* **Remediation Applied:**
  Called `auth_rate_limiter.record_attempt(rate_limit_id)` on every registration request, and removed `auth_rate_limiter.reset(rate_limit_id)` from registration. Tested via `test_registration_rate_limiting`.

---

#### Finding SEC-03: Student Endpoints Lacked Explicit `STUDENT` Role Guard
* **Severity:** **LOW** (Access Control Defect)
* **Code Evidence:** [`backend/app/api/v1/endpoints/student.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/api/v1/endpoints/student.py)
  ```python
  # Previous code:
  async def get_student_profile(current_user: User = Depends(get_current_user), ...)
  ```
* **Reproduction / Verification Method:**
  An authenticated user with only the `EDUCATOR` role could call `GET /api/v1/student/profile` and have a `StudentProfile` automatically created and returned.
* **Actual Impact:**
  Role separation was not enforced on student endpoints; non-student roles could manipulate student workspace settings.
* **Remediation Applied:**
  Replaced `get_current_user` with `require_role("STUDENT")` across all routes in `student.py` (`/profile`, `/onboarding`, `/account`). Tested via `test_role_guard_enforcement`.

---

#### Finding SEC-04: Rate Limiter State Bleed Between Pytest Execution Units
* **Severity:** **LOW** (Test Flakiness Defect)
* **Code Evidence:** [`tests/conftest.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/tests/conftest.py) lacked a fixture to clear `auth_rate_limiter._attempts`.
* **Actual Impact:**
  As test suites expanded, accumulated failed attempts from one test suite could trigger unexpected 429 errors in subsequent test suites running against the same in-memory singleton.
* **Remediation Applied:**
  Added an `autouse=True` fixture `reset_rate_limiter_state` in `tests/conftest.py` that clears `auth_rate_limiter._attempts` before and after each test.

---

#### Finding SEC-05: Stateless Access Tokens Reusable After Logout Until Expiry
* **Severity:** **INFORMATIONAL** (Standard Stateless JWT Property; Non-blocking for Milestone 2)
* **Code Evidence:**
  [`backend/app/api/v1/endpoints/auth.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/api/v1/endpoints/auth.py#L232-L239) clears the HttpOnly cookie, but the signed JWT remains cryptographically valid until its `exp` claim (60 minutes).
* **Actual Impact:**
  If a bearer token is exfiltrated prior to logout (e.g. from network traffic if unencrypted or compromised memory), the token remains usable until expiration even after the user clicked "Logout".
* **Remediation Plan for Production:**
  Before production launch, implement a token revocation mechanism (e.g., Redis-backed JTI denylist or user `token_version` increment on logout) combined with shorter access token lifetimes (15 minutes). For Milestone 2 local development, client-side token discard is standard and acceptable. Tested and verified in `test_logout_cookie_clearing_and_token_reuse`.

---

#### Finding SEC-06: In-Memory Sliding-Window Limiter Not Distributed Across Workers
* **Severity:** **INFORMATIONAL** (Architectural Scalability Limitation)
* **Code Evidence:**
  [`backend/app/core/security.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/core/security.py#L74) stores timestamps in `self._attempts = defaultdict(list)`.
* **Actual Impact:**
  In a multi-worker deployment (e.g. `uvicorn --workers 4`), rate limits are tracked per worker process. An attacker's requests can round-robin across workers, multiplying effective attempt allowances. Furthermore, `request.client.host` will reflect the reverse proxy IP unless trusted proxy middleware is configured.
* **Remediation Plan for Production:**
  Connect rate limiting to a shared Redis cluster using token bucket keys and configure Uvicorn/FastAPI with `ProxyHeadersMiddleware` trusting only designated proxy CIDRs. Acceptable for single-process local development.

---

## 4. Deep-Dive Security Domain Assessments

### 4.1. JWT & Logout Lifecycle Assessment

1. **Where is the JWT stored in the frontend?**
   * Stored in `sessionStorage` under key `campus_auth_token` via [`frontend/src/services/api.ts`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/frontend/src/services/api.ts#L11).
   * Decoded user profile state is held in React context memory ([`AuthContext.tsx`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/frontend/src/context/AuthContext.tsx)).
   * *Assessment:* Storing access tokens in `sessionStorage` isolates tokens per browser tab (unlike `localStorage` which persists across tabs and windows indefinitely) and clears them when the browser tab closes.

2. **Does the frontend send the bearer token, the cookie, or both?**
   * The frontend explicitly attaches the bearer token: `headers['Authorization'] = 'Bearer ' + token` on every request.
   * In cross-origin requests without `credentials: 'include'`, cookies are not transmitted. On same-origin requests, the browser also attaches the cookie.
   * In [`backend/app/api/deps.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/api/deps.py#L26-L34), `get_token_from_request` prioritizes the `Authorization` header. The cookie is used strictly as a fallback.

3. **Does logout revoke access tokens?**
   * `/api/v1/auth/logout` sends a `Set-Cookie` header with `Max-Age=0` to instruct the browser to delete the cookie.
   * The frontend calls `removeAuthToken()` to delete the token from `sessionStorage` and resets React state to `null`.
   * The token itself is stateless; no server-side denylist check is performed.

4. **Security Impact:**
   * Low for local development; Medium for shared public terminals (e.g. school computer labs). Addressed by the production roadmap item for token denylisting/short-lived tokens.

---

### 4.2. Cookie, CSRF, and CORS Review

* **Cookie Flags:**
  * `HttpOnly = True`: Blocks JavaScript `document.cookie` access, defending against token theft via XSS.
  * `SameSite = "lax"`: Prevents the cookie from being attached to cross-site POST/PUT/DELETE requests initiated by external origins.
  * `Secure = False` in development; dynamically enforced to `True` when `ENVIRONMENT == "production"`.
  * `Path = "/"`: Scoped to entire domain.
* **CSRF Vulnerability Assessment:**
  * Requests utilizing `Authorization: Bearer <token>` are **immune to CSRF** because web browsers do not automatically attach custom `Authorization` headers on cross-site requests, and cross-origin scripts cannot read `sessionStorage` under the Same-Origin Policy.
  * For fallback cookie authentication: `SameSite=Lax` defends against cross-site form submissions and cross-site script-driven mutations. Because the frontend relies entirely on Bearer headers for API interactions, CSRF tokens are not required at this milestone.
* **CORS Settings:**
  * Configured via [`backend/app/main.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/main.py#L52-L58):
    ```python
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,  # ["http://localhost:5173", "http://127.0.0.1:5173"]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    ```
  * `allow_origins` strictly whitelists localhost development origins. Wildcard `"*"` is NOT used when credentials are enabled.

---

### 4.3. Authorization & Account Isolation (IDOR Verification)

Every student endpoint derives identity exclusively from the cryptographically verified JWT principal:

| Endpoint | Method | Identity Extraction Source | Client Parameter Spoofing Resistance |
| :--- | :---: | :--- | :--- |
| `/api/v1/student/profile` | `GET` | `current_user.id` from token `sub` | Verified. `?user_id=...` parameter is ignored. |
| `/api/v1/student/onboarding` | `PUT` | `current_user.id` from token `sub` | Verified. Client payload cannot target other profiles. |
| `/api/v1/student/profile` | `PUT` | `current_user.id` from token `sub` | Verified. Body/query user IDs cannot redirect update. |
| `/api/v1/student/account` | `DELETE`| `current_user.id` from token `sub` | Verified. Cannot delete another student's account. |

* **Verified Tests:**
  * `test_student_data_isolation`: Confirms Student A cannot see Student B's data.
  * `test_student_cannot_modify_other_student_profile`: Confirms Student A cannot alter Student B's goal.
  * `test_student_cannot_delete_other_student_account`: Confirms Student A cannot trigger deletion of Student B.
  * `test_role_guard_enforcement`: Confirms `EDUCATOR` role accounts cannot invoke student endpoints (403 Forbidden).

---

### 4.4. Passwords, Secrets, and Error Handling

* **Password Hashing:**
  * Bcrypt with work factor 12 (`bcrypt.gensalt(rounds=12)`).
  * Password verification uses `bcrypt.checkpw` in constant time, returning boolean `False` on any exception.
* **Password Validation:**
  * Enforced on backend schema ([`UserRegisterRequest`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/schemas/auth.py#L38-L43)): length 8–128, must contain both letters and digits.
* **Plaintext Leakage:**
  * Plaintext passwords and `hashed_password` are excluded from all Pydantic response models (`UserResponse`, `StudentProfileResponse`).
  * Exception handler ([`backend/app/main.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/main.py#L62-L74)) masks unhandled server errors into generic JSON responses without stack traces or secret strings (`test_internal_error_does_not_leak_stack_trace_or_secrets`).
* **Authentication Error Consistency:**
  * Both incorrect passwords and non-existent accounts return identical 401 response: `"Invalid email or password"`. User enumeration via login timing/error messaging is prevented.

---

### 4.5. Rate Limiting Review

* **Implementation:** `AuthRateLimiter` sliding window tracking timestamped attempts.
* **Thresholds:**
  * Registration: Max 5 attempts per 60 seconds per IP (`reg:{client_ip}`).
  * Login: Max 5 attempts per 60 seconds per IP + Email (`login:{client_ip}:{email}`).
* **Window Expiration:** Timestamps older than `window_seconds` are pruned on each request.
* **Verified Tests:**
  * `test_registration_rate_limiting`: 6th registration from same IP triggers 429 Too Many Requests.
  * `test_login_rate_limiting`: 6th failed login for same target email triggers 429 Too Many Requests.

---

### 4.6. Account Deletion & Privacy (DPDP Act 2023 Assessment)

* **Technical Verification:**
  * `DELETE /api/v1/student/account` performs `await db.delete(current_user)`.
  * Verified via `test_account_deletion_cleanses_database` that `users`, `student_profiles`, and `student_profile_subjects` rows are purged with zero orphan records.
  * Subsequent logins fail with 401; subsequent token usage fails with 401.
* **DPDP Act 2023 Statutory Boundary Clarification:**
  * This endpoint implements the *technical mechanism* for self-service data erasure (Section 12 of the DPDP Act 2023).
  * It does **not** constitute complete statutory compliance. Full compliance requires legal and operational frameworks outside the application codebase:
    1. Verifiable parental consent architecture for users identifying as minors under Section 9.
    2. Comprehensive privacy notice in 22 scheduled Indian languages (Section 5).
    3. Designated Data Protection Officer (DPO) and Grievance Redressal mechanism (Section 13).
    4. Data retention compliance with Indian tax/regulatory archiving laws.

---

## 5. Automated Test Execution Results

### Backend Test Suite (Pytest)
Command: `.\.venv\Scripts\pytest.exe -v tests`

```
tests/test_auth.py::test_student_registration_success PASSED             [  2%]
tests/test_auth.py::test_registration_duplicate_normalized_email_rejected PASSED [  5%]
tests/test_auth.py::test_registration_validation_errors PASSED           [  8%]
tests/test_auth.py::test_login_successful PASSED                         [ 11%]
tests/test_auth.py::test_login_invalid_credentials_rejected PASSED       [ 13%]
tests/test_auth.py::test_authenticated_me_endpoint PASSED                [ 16%]
tests/test_auth.py::test_logout_endpoint PASSED                          [ 19%]
tests/test_auth.py::test_expired_jwt_rejected PASSED                     [ 22%]
tests/test_auth.py::test_tampered_jwt_rejected PASSED                    [ 25%]
tests/test_auth.py::test_inactive_user_login_rejected PASSED             [ 27%]
tests/test_auth.py::test_inactive_user_token_access_rejected PASSED      [ 30%]
tests/test_auth.py::test_logout_cookie_clearing_and_token_reuse PASSED   [ 33%]
tests/test_auth.py::test_registration_rate_limiting PASSED               [ 36%]
tests/test_auth.py::test_login_rate_limiting PASSED                      [ 38%]
tests/test_authorization.py::test_student_data_isolation PASSED          [ 41%]
tests/test_authorization.py::test_unauthenticated_access_rejected PASSED [ 44%]
tests/test_authorization.py::test_account_erasure_dpdp_compliance PASSED [ 47%]
tests/test_authorization.py::test_student_cannot_modify_other_student_profile PASSED [ 50%]
tests/test_authorization.py::test_student_cannot_delete_other_student_account PASSED [ 52%]
tests/test_authorization.py::test_role_guard_enforcement PASSED          [ 55%]
tests/test_authorization.py::test_account_deletion_cleanses_database PASSED [ 58%]
tests/test_database.py::test_database_connectivity PASSED                [ 61%]
tests/test_database.py::test_database_table_presence PASSED              [ 63%]
tests/test_error_handling.py::test_non_existent_endpoint_returns_404 PASSED [ 66%]
tests/test_error_handling.py::test_internal_error_does_not_leak_stack_trace_or_secrets PASSED [ 69%]
tests/test_error_handling.py::test_production_secret_key_validation PASSED [ 72%]
tests/test_health.py::test_root_health_endpoint PASSED                   [ 75%]
tests/test_health.py::test_api_v1_health_endpoint PASSED                 [ 77%]
tests/test_health.py::test_api_v1_health_with_database_check PASSED      [ 80%]
tests/test_models.py::test_create_curriculum_taxonomy PASSED             [ 83%]
tests/test_models.py::test_duplicate_board_code_raises_integrity_error PASSED [ 86%]
tests/test_models.py::test_user_role_and_student_profile_association PASSED [ 88%]
tests/test_onboarding.py::test_list_curricula_taxonomy PASSED            [ 91%]
tests/test_onboarding.py::test_student_onboarding_lifecycle_and_resumption PASSED [ 94%]
tests/test_onboarding.py::test_onboarding_rejects_incompatible_selections PASSED [ 97%]
tests/test_onboarding.py::test_partial_profile_update PASSED             [100%]

============================= 36 passed in 16.82s =============================
```
* **Result:** **36 Passed, 0 Failed, 0 Skipped** (expanded from 24 baseline tests).

---

### Database Migration Check
Command: `.\.venv\Scripts\python.exe -m alembic current` (in `backend/`)
```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
eeac6986a79e (head)
```
* **Result:** Migration state verified at `eeac6986a79e (head)`.

---

### Frontend Vitest Suite
Command: `npm test -- --run` (in `frontend/`)
```
 RUN  v4.1.11 C:/Users/LOQ/OneDrive/Desktop/project_campus/frontend

 ✓ src/test/Onboarding.test.tsx (2 tests)
 ✓ src/test/App.test.tsx (4 tests)
 ✓ src/test/Auth.test.tsx (4 tests)

 Test Files  3 passed (3)
      Tests  10 passed (10)
   Duration  6.15s
```
* **Result:** **10 Passed, 0 Failed** across 3 test suites.

---

### Frontend Production Build
Command: `npm run build` (in `frontend/`)
```
vite v5.4.21 building for production...
transforming...
✓ 1587 modules transformed.
rendering chunks...
dist/index.html                   0.78 kB │ gzip:   0.48 kB
dist/assets/index-Bm1Oh2rK.css   28.44 kB │ gzip:   5.33 kB
dist/assets/index-CNrapJFO.js   464.91 kB │ gzip: 138.84 kB
✓ built in 8.85s
```
* **Result:** Clean TypeScript compilation with 0 errors.

---

## 6. Summary of Files Changed During Security Verification Gate

| File | Change Description |
| :--- | :--- |
| [`backend/app/core/config.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/core/config.py) | Added `@model_validator(mode="after")` preventing silent dev secrets and forcing `AUTH_COOKIE_SECURE=True` when `ENVIRONMENT == "production"`. |
| [`backend/app/api/v1/endpoints/auth.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/api/v1/endpoints/auth.py) | Fixed registration rate limiting by recording attempts unconditionally and removing the success reset bypass. |
| [`backend/app/api/v1/endpoints/student.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/api/v1/endpoints/student.py) | Applied `require_role("STUDENT")` to `/profile`, `/onboarding`, and `/account` endpoints to enforce strict role separation. |
| [`tests/conftest.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/tests/conftest.py) | Added `reset_rate_limiter_state` fixture to isolate test runs and prevent rate limiter attempt accumulation bleed. |
| [`tests/test_auth.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/tests/test_auth.py) | Added 7 security tests: expired JWT, tampered JWT, inactive login, inactive token access, cookie clearing & token reuse, registration rate limiting, login rate limiting. |
| [`tests/test_authorization.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/tests/test_authorization.py) | Added 4 security tests: cross-student profile modification defense, cross-student account deletion defense, role guard enforcement, and account deletion database cleansing. |
| [`tests/test_error_handling.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/tests/test_error_handling.py) | Added 1 configuration test: `test_production_secret_key_validation`. |
| [`docs/MILESTONE_2_SECURITY_VERIFICATION.md`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/docs/MILESTONE_2_SECURITY_VERIFICATION.md) | Created authoritative, comprehensive security verification gate report. |

---

## 7. Remaining Limitations & Roadmap to Production

1. **Token Revocation Infrastructure:**
   * *Status in Milestone 2:* Access tokens are stateless. Logout clears the cookie and client storage, but the token itself remains cryptographically valid until its 60-minute expiration.
   * *Production Action:* Implement a Redis-backed token denylist or user `token_version` increment on logout, paired with short-lived access tokens (15 minutes).
2. **Distributed Rate Limiting & Trusted Proxies:**
   * *Status in Milestone 2:* Limiter is in-memory and process-local, keyed by `request.client.host`.
   * *Production Action:* Integrate Redis-backed token bucket rate limiting and configure `ProxyHeadersMiddleware` for trusted reverse proxies (Nginx/ALB).
3. **Statutory DPDP Compliance Obligations:**
   * *Status in Milestone 2:* Technical self-service data erasure is fully implemented and tested.
   * *Production Action:* Prior to public launch, establish minor consent workflows, multilingual notice disclosures, and formal breach notification protocols.

---

## 8. Verification Gate Conclusion

All security properties required for Milestone 2 have been verified through actual code inspection and automated test execution. The identified defects were resolved without architectural churn or breaking changes.

**Milestone 2 is formally verified and approved. No Milestone 3 features have been implemented. The application is ready for stakeholder review prior to Milestone 3 authorization.**
