# QuickBite v2.0.0 — Implementation & Verification Status Matrix
**Secure Software Engineering End-Semester Laboratory Examination Project**  
**Final Release:** `v2.0.0` | **Date:** 2026-10-08

---

## Complete Phase Status Overview (Phases 1–16)

| Phase | Domain / Milestone | Key Requirement | Implementation Details | Verification Command | Actual Result | Status |
|---|---|---|---|---|---|---|
| **Phase 1** | Agile Methodology & Scrum | Sprint planning, backlog grooming, Scrum cadence | Multi-sprint plan, burndown tracking, DoD, security story criteria | `docs/01_agile.md`, `docs/11_scrum.md` | Sprint artifacts & team ceremonies defined | **VERIFIED** |
| **Phase 2** | SRS (Requirements) | Functional & Security Requirements Specification | 18 Functional requirements, 10 Non-functional security requirements | `docs/02_srs.md` | Formal IEEE 830-aligned specification | **VERIFIED** |
| **Phase 3** | Use Case Modeling | Actor boundaries, preconditions, postconditions | Customer, Staff, Admin use case narratives & misuse cases | `docs/03_use_cases.md` | 10 Use Cases + Misuse cases documented | **VERIFIED** |
| **Phase 4** | Domain Analysis | Domain object analysis, invariants, class diagrams | Class specifications, domain invariants, pricing rules | `docs/04_analysis.md` | Domain model validated | **VERIFIED** |
| **Phase 5** | ER & DFD | Relational data schema & process data flow | Level 0, Level 1, Level 2 DFDs, 7 relational entities | `docs/05_er_dfd.md` | Validated ER diagram with foreign keys | **VERIFIED** |
| **Phase 6** | System Architecture | Architectural layers, design patterns, micro-segmentation | 3-tier secure architecture, Adapter pattern, Gateway pattern | `docs/06_architecture.md` | Modular FastAPI + SQLite + Static UI | **VERIFIED** |
| **Phase 7** | UI/UX & Authentication | Dedicated `/login`, `/register`, modern light theme | Responsive cards, role-routing, interactive Security Posture Card | Browser inspection `/login`, `/register`, `/` | Clean UI, role-based dashboards | **VERIFIED** |
| **Phase 8** | Threat Modeling | STRIDE analysis, assets, sensitive information flows | 8 assets, CIA triage, 12 STRIDE threats, 6 vulnerability mitigations | `docs/08_threat_model.md` | STRIDE model documented | **VERIFIED** |
| **Phase 9** | Attack Trees | Critical attacker goal modeling (AND/OR trees) | "Tamper with order price or access peer order" attack trees | `docs/09_attack_tree.md` | Attack vectors neutralized | **VERIFIED** |
| **Phase 10** | Product Backlog | User stories with security acceptance criteria | 10+ user stories with Gherkin acceptance criteria | `docs/10_backlog.md` | INVEST-compliant user stories | **VERIFIED** |
| **Phase 11** | Scrum Execution | Sprints, velocity, burn-down, defect tracking | 3 Sprints mapped to v1.0.0, v1.1.0/1.2.0, and v2.0.0 final release | `docs/11_scrum.md` | Real velocity & defect tracking documented | **VERIFIED** |
| **Phase 12** | Secure Build & CI/CD | GitHub Actions, reproducibility, non-root user | Multi-stage Docker build, non-root UID 10001, `.github/workflows/ci.yml` | `docker build -t quickbite:2.0.0 .` & `docker run --rm quickbite:2.0.0 id` | `uid=10001(appuser)` verified; container healthy | **VERIFIED** |
| **Phase 13** | Secure Coding & SAST | Salted Bcrypt, JWTs, no secrets, SAST & SCA audit | Fixed B105/B106 in Bandit; upgraded pip dependencies for SCA | `bandit -r backend/app` & `pip-audit --desc` | Bandit: 0 issues; pip-audit: 0 vulnerabilities | **VERIFIED** |
| **Phase 14** | Automated Testing | Unit, BOLA, FSM, Fuzzing & boundary resilience | 20 automated tests in Pytest covering all security controls | `pytest -v` | 20 passed, 0 failed in 1.93s | **VERIFIED** |
| **Phase 15** | Hardening & Orchestration | Kubernetes manifests, non-root, seccomp, health probes | Resolved emptyDir volume conflict, updated tag to v2.0.0 | `kubectl apply -f k8s/` & `kubectl get pods -n quickbite` | 2/2 Pods in `1/1 Running` state; NodePort verified | **VERIFIED** |
| **Phase 16** | Traceability | End-to-end requirement to deployment trace | Complete bidirectional traceability from REQ-SEC-01 to K8s deploy | `docs/16_traceability.md` | Bidirectional trace matrix verified | **VERIFIED** |

---

## Detailed Security Controls Verification

1. **Authentication:**
   - Hashing: Salted Bcrypt (work factor 12) via `bcrypt.hashpw` (`VERIFIED`)
   - Tokens: HMAC-SHA256 JWT tokens with 60-minute expiration (`VERIFIED`)
   - Dedicated screens: `/login` and `/register` with role routing (`VERIFIED`)

2. **Authorization (RBAC + BOLA/IDOR):**
   - Customer accesses only their own orders (`test_customer_order_ownership_bola_protection`: `VERIFIED`)
   - Restaurant staff accesses only their assigned restaurant (`test_restaurant_staff_tenant_isolation`: `VERIFIED`)
   - Public self-registration restricted to `customer` (`test_registration_role_privilege_escalation_rejected`: `VERIFIED`)

3. **Authoritative Pricing:**
   - Server strictly recomputes total amounts from DB (`test_price_tampering_attempt_is_strictly_neutralized`: `VERIFIED`)

4. **Order State Machine (FSM):**
   - Strict progression (`PLACED -> ACCEPTED -> PREPARING -> OUT_FOR_DELIVERY -> DELIVERED`)
   - Cancellation permitted strictly in `PLACED` state (`test_order_cancellation_state_machine_invariant`: `VERIFIED`)

5. **Container & Orchestration Security:**
   - Docker non-root user `10001:10001` (`VERIFIED`)
   - Kubernetes namespace `quickbite`, seccomp `RuntimeDefault`, capabilities dropped `ALL` (`VERIFIED`)
   - Pod status: `quickbite-deployment` 2 replicas in `1/1 Running` (`VERIFIED`)
