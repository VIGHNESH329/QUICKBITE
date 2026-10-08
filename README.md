# QuickBite — Secure Online Food Ordering Platform
**Secure Software Engineering End-Semester Laboratory Examination Project**  
**Version:** `2.0.0` (FINAL END-SEM RELEASE) | **Target:** Production Readiness & Examination Evidence

---

## 1. Problem Statement & Executive Summary

Modern food ordering platforms face severe application security challenges:
- **Price Manipulation & Tampering:** Malicious clients altering item prices or order totals before submission.
- **Broken Object Level Authorization (BOLA / IDOR):** Unauthorized customers accessing or cancelling peer orders.
- **Multi-Tenant Data Crossover:** Restaurant staff accessing orders or modifying menu items belonging to rival restaurants.
- **Privilege Escalation:** Unprivileged users creating administrative accounts or staff profiles during self-registration.
- **PCI-DSS Compliance Exposure:** Premature exposure to cardholder data storage risks.
- **Container & Cluster Vulnerabilities:** Running processes as root, shadowing critical volumes in Kubernetes, or lacking namespace isolation.

**QuickBite v2.0.0** is an enterprise-grade reference implementation engineered from the ground up under Secure Software Engineering (SSE) principles to systematically eliminate these vulnerabilities through defense-in-depth, authoritative server-side computation, strict role-based access control, automated testing, container hardening, and full requirements-to-deployment traceability across all 16 exam phases.

---

## 2. Core Features & Capabilities

- **Dedicated Authentication System:**
  - Dedicated `/login` portal with role routing (Customer, Restaurant Staff, Administrator) and demo persona selectors.
  - Dedicated `/register` page restricted strictly to `customer` accounts with live password strength metrics.
  - Bcrypt salted hashing (work factor 12) + HMAC-SHA256 signed JWT sessions (60-min expiration).
- **Major UI/UX Redesign:**
  - Modern light theme with warm neutrals, card elevation, and responsive typography.
  - Interactive **Security Posture Card & Architecture Dashboard** modal displaying active controls.
  - Restaurant catalog, category chips (Pizza, Pasta, Curry, Breads, Dessert, Beverages), search, and canonical price pills.
  - Interactive shopping cart with authoritative breakdown (Subtotal, 10% Tax, $3.00 Delivery, Total).
  - Live order tracking timeline stepper (Placed -> Accepted -> Preparing -> Dispatched -> Delivered).
- **Multi-Tenant Operations:**
  - Staff kitchen dashboard with order progression actions (`ACCEPTED`, `PREPARING`, `OUT_FOR_DELIVERY`, `DELIVERED`).
  - Staff menu management with real-time audit logging for dish and price changes.
- **Audit & Forensics:**
  - Tamper-evident read-only audit ledger for administrators tracking all security and financial events.

---

## 3. Security Architecture & Threat Defenses

```
  [Client Web Browser / UI]
            │
            ▼  (HTTPS / Reverse Proxy)
  [Security Headers Middleware (CSP, HSTS, X-Frame-Options: DENY, X-Content-Type-Options: nosniff)]
            │
            ▼
  [FastAPI REST API Gateway] ──── Rate Limiting (Sliding Window IP)
            │
    ┌───────┴────────────────────────────────┐
    ▼                                        ▼
[Authentication Layer]              [Authorization Layer (RBAC)]
- Bcrypt Hash (Salted, Cost 12)     - Customer Ownership (BOLA Guard)
- JWT HMAC-SHA256 Bearer Tokens     - Restaurant Multi-Tenant Isolation
- 60-min Expiration                 - Self-Registration Role Invariant
    │                                        │
    └───────────────────┬────────────────────┘
                        ▼
       [Authoritative Pricing Engine]
       - Discards all client price inputs
       - Fetches canonical DB prices
       - Computes Subtotal, Tax, Delivery
                        │
                        ▼
       [Order Finite State Machine]
       - PLACED -> ACCEPTED -> PREPARING -> OUT_FOR_DELIVERY -> DELIVERED
       - Cancellation restricted to PLACED
                        │
    ┌───────────────────┴────────────────────┐
    ▼                                        ▼
[Payment Gateway Adapter]           [Tamper-Evident Audit Ledger]
- Tokenized Mock (tok_visa_*)       - Structured Event Logging
- Zero Card PAN/CVV Storage         - IP, Actor, Entity, Status
```

---

## 4. Technology Stack

- **Backend Runtime:** Python 3.11 / 3.12, FastAPI 0.142.4, Uvicorn 0.54.0
- **Data Persistence:** SQLAlchemy 2.0 ORM, SQLite with WAL mode
- **Security & Cryptography:** bcrypt 5.0.0, PyJWT 2.15.1, Pydantic V2
- **Frontend:** Vanilla HTML5, CSS3 Modern Light Theme, JavaScript ES6+
- **Testing & Quality:** Pytest 9.1.1, HTTPX, Flake8
- **Security Scanners:** Bandit 1.9.4 (SAST), pip-audit 2.10.1 (SCA)
- **Containerization:** Docker (Multi-stage python:3.11-slim, non-root user `10001:10001`)
- **Orchestration:** Kubernetes (Minikube v1.39.0 / K8s v1.36.1, Namespace isolation, Seccomp)

---

## 5. Quick Start & Execution Guide

### 5.1 Local Application Execution

1. Clone or navigate to the repository:
   ```powershell
   cd c:\Users\deepa\Downloads\sse_endsem\QuickBite
   ```
2. Activate virtual environment or install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Run the Uvicorn application server:
   ```powershell
   $env:PYTHONPATH="backend"
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Access in browser:
   - Login Portal: `http://localhost:8000/login`
   - Customer Registration: `http://localhost:8000/register`
   - Storefront & Dashboard: `http://localhost:8000/`
   - Health & Security Posture: `http://localhost:8000/api/health`

### 5.2 Docker Container Execution

1. Build the production container image:
   ```powershell
   docker build -t quickbite:2.0.0 .
   ```
2. Verify non-root user (`10001:10001`):
   ```powershell
   docker run --rm quickbite:2.0.0 id
   # Output: uid=10001(appuser) gid=10001(appgroup) groups=10001(appgroup)
   ```
3. Run container:
   ```powershell
   docker run -d --name quickbite-app -p 8000:8000 quickbite:2.0.0
   ```
4. Verify health status:
   ```powershell
   curl.exe http://localhost:8000/api/health
   ```

### 5.3 Kubernetes Deployment (Minikube)

1. Verify Minikube status:
   ```powershell
   minikube status
   ```
2. Load local image into Minikube:
   ```powershell
   minikube image load quickbite:2.0.0
   ```
3. Apply manifests:
   ```powershell
   kubectl apply -f k8s/
   ```
4. Verify pods reach `1/1 Running`:
   ```powershell
   kubectl get pods -n quickbite
   kubectl get svc -n quickbite
   ```
5. Test in-cluster health check:
   ```powershell
   minikube ssh "curl -s http://localhost:30080/api/health"
   ```

### 5.4 Automated Test Suite Execution

Run all 20 automated unit, security, integration, and fuzzing tests:
```powershell
$env:PYTHONPATH="backend"
pytest -v
```
**Results:** `20 passed, 0 failed in 1.93s`

### 5.5 Static & Dependency Security Scans

1. **Bandit (SAST):**
   ```powershell
   bandit -r backend/app
   # Output: No issues identified. (Total issues: 0)
   ```
2. **pip-audit (SCA):**
   ```powershell
   pip-audit --desc
   # Output: No known vulnerabilities found
   ```

---

## 6. Project Directory Structure

```
QuickBite/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI/CD pipeline
├── backend/
│   └── app/
│       ├── api/                 # API routers (auth, cart, orders, restaurants, audit)
│       ├── core/                # Config, security, rate limiting
│       ├── db/                  # SQLAlchemy session & SQLite setup
│       ├── models/              # Relational models (User, Restaurant, Order, etc.)
│       ├── schemas/             # Pydantic V2 DTOs with validation rules
│       ├── services/            # Domain services (Authoritative pricing, payment, audit)
│       └── main.py              # Application entrypoint & static mounting
├── frontend/
│   ├── index.html               # Main application storefront & dashboards
│   ├── login.html               # Dedicated authentication portal
│   ├── register.html            # Dedicated customer self-registration
│   ├── styles.css               # Modern light-theme design system
│   └── app.js                   # Client application engine
├── k8s/                         # Kubernetes manifests
│   ├── namespace.yaml           # Dedicated quickbite namespace
│   ├── configmap.yaml           # Non-sensitive configuration
│   ├── secret.yaml              # Cryptographic secrets
│   ├── deployment.yaml          # Pod security context & volume configuration
│   └── service.yaml             # NodePort 30080 service definition
├── tests/
│   ├── test_unit.py             # Cryptography & pricing unit tests
│   ├── test_authz.py            # BOLA, IDOR & tenant isolation tests
│   ├── test_integration.py     # End-to-end order lifecycle & price tampering
│   └── test_fuzz.py             # Boundary & input fuzzing tests
├── evidence/                    # Exam verification evidence artifacts
│   ├── phase11/                 # Sprint & velocity evidence
│   ├── phase12/                 # Docker build & non-root logs
│   ├── phase13/                 # Bandit & pip-audit scan logs
│   ├── phase14/                 # Pytest 20/20 execution log
│   ├── phase15/                 # Kubernetes 1/1 Running pod logs
│   └── phase16/                 # Traceability matrix verification
├── docs/                        # Complete 16-Phase examination documentation
│   ├── 01_agile.md              # Phase 1: Agile Methodology
│   ├── 02_srs.md                # Phase 2: SRS
│   ├── 03_use_cases.md          # Phase 3: Use Cases
│   ├── 04_analysis.md           # Phase 4: Domain Analysis
│   ├── 05_er_dfd.md             # Phase 5: ER & DFD Diagrams
│   ├── 06_architecture.md       # Phase 6: Architecture
│   ├── 07_ui.md                 # Phase 7: UI Wireframes & Design
│   ├── 08_threat_model.md       # Phase 8: Threat Modeling (STRIDE)
│   ├── 09_attack_tree.md        # Phase 9: Attack Trees
│   ├── 10_backlog.md            # Phase 10: Product Backlog
│   ├── 11_scrum.md              # Phase 11: Scrum Execution
│   ├── 12_secure_build.md       # Phase 12: Secure Build Systems
│   ├── 13_secure_coding.md      # Phase 13: Secure Coding & SAST
│   ├── 14_testing.md            # Phase 14: Automated Testing
│   ├── 15_hardening.md          # Phase 15: Hardening & Orchestration
│   ├── 16_traceability.md       # Phase 16: End-to-End Traceability
│   └── IMPLEMENTATION_STATUS.md # Complete verification matrix
├── Dockerfile                   # Hardened multi-stage Dockerfile
├── docker-compose.yml           # Local multi-container configuration
├── requirements.txt             # Pinned Python dependencies
├── VERSION                      # 2.0.0
└── CHANGELOG.md                 # Detailed release history
```

---

## 7. Mapping to Examination Phases 1–16

| Phase | Title | Document Link | Implementation Status |
|---|---|---|---|
| 1 | Agile Methodology | [`docs/01_agile.md`](docs/01_agile.md) | **VERIFIED** |
| 2 | Software Requirements Specification | [`docs/02_srs.md`](docs/02_srs.md) | **VERIFIED** |
| 3 | Use Case Modeling | [`docs/03_use_cases.md`](docs/03_use_cases.md) | **VERIFIED** |
| 4 | Domain Object Analysis | [`docs/04_analysis.md`](docs/04_analysis.md) | **VERIFIED** |
| 5 | ER Diagrams & DFDs | [`docs/05_er_dfd.md`](docs/05_er_dfd.md) | **VERIFIED** |
| 6 | System Architecture | [`docs/06_architecture.md`](docs/06_architecture.md) | **VERIFIED** |
| 7 | UI/UX & Authentication | [`docs/07_ui.md`](docs/07_ui.md) | **VERIFIED** |
| 8 | Threat Modeling & STRIDE | [`docs/08_threat_model.md`](docs/08_threat_model.md) | **VERIFIED** |
| 9 | Attack Tree Modeling | [`docs/09_attack_tree.md`](docs/09_attack_tree.md) | **VERIFIED** |
| 10 | Product Backlog | [`docs/10_backlog.md`](docs/10_backlog.md) | **VERIFIED** |
| 11 | Scrum Execution & Sprints | [`docs/11_scrum.md`](docs/11_scrum.md) | **VERIFIED** |
| 12 | Secure Build & CI/CD | [`docs/12_secure_build.md`](docs/12_secure_build.md) | **VERIFIED** |
| 13 | Secure Coding & SAST | [`docs/13_secure_coding.md`](docs/13_secure_coding.md) | **VERIFIED** |
| 14 | Security & Fuzz Testing | [`docs/14_testing.md`](docs/14_testing.md) | **VERIFIED** |
| 15 | Hardening & Kubernetes | [`docs/15_hardening.md`](docs/15_hardening.md) | **VERIFIED** |
| 16 | End-to-End Traceability | [`docs/16_traceability.md`](docs/16_traceability.md) | **VERIFIED** |

---

## 8. Known Limitations & Future Enhancements

- **In-Memory Rate Limiting:** The current rate limiter uses an in-memory sliding window per worker. In a horizontally scaled multi-node environment, an external distributed Redis token-bucket store is recommended.
- **Mutual TLS (mTLS):** Internal pod-to-pod communication in Kubernetes can be augmented with Istio/Linkerd service mesh mTLS.
- **Hardware Security Modules (HSM):** Production JWT signing keys can be backed by Cloud KMS or HashiCorp Vault.
