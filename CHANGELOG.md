# Changelog — QuickBite

All notable changes to the QuickBite Secure Online Food Ordering Platform will be documented in this file.

The project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-10-08 — FINAL END-SEM SECURE SOFTWARE ENGINEERING RELEASE

### Added
- **Dedicated Authentication Screens:**
  - Separate `/login` page with role-based tabs (Customer, Restaurant Staff, Platform Admin), live form validation, and quick persona demo selectors.
  - Separate `/register` page strictly restricted to Customer role with dynamic password strength meter (8+ chars, uppercase, digit).
- **Major UI/UX Redesign:**
  - Modern, responsive light theme using warm neutral surfaces, crisp typography, and mobile/desktop layouts.
  - Interactive **Security Posture Card & Architecture Dashboard** modal reporting 10 live security controls.
  - Category filters (All, Pizza, Pasta, Curry, Breads, Dessert, Beverages) and responsive food cards with canonical price pills.
  - Cart drawer and authoritative checkout breakdown (Subtotal, 10% Tax, $3.00 Delivery, Total).
  - Live order tracking stepper (Placed -> Accepted -> Preparing -> Out for Delivery -> Delivered).
  - Staff kitchen queue and menu management views; Admin audit ledger view.
- **Automated Test Suite Expansion:**
  - Expanded pytest suite to 20 automated tests across unit, integration, BOLA/IDOR, and boundary fuzzing domains.
  - Dedicated tests for price tampering neutralization, unauthenticated access rejection, self-registration role escalation defense, and FSM lifecycle progression.
  - Boundary and fuzzing tests for quantity limits (1, 99, 10000, 0, -5), SQLi, XSS, and oversized string inputs (>250 chars).
- **Security Audit & Evidence:**
  - Static Application Security Testing (SAST) via Bandit with 0 issues identified.
  - Software Composition Analysis (SCA) via pip-audit with 0 known vulnerabilities.
  - Structured evidence repository in `evidence/` covering phases 11 to 16.
  - Implementation verification matrix in `docs/IMPLEMENTATION_STATUS.md`.

### Changed
- **Kubernetes Runtime Root Cause Remediation:**
  - Diagnosed and resolved `ModuleNotFoundError: No module named 'app'` caused by an emptyDir volume mounting over `/home/appuser/quickbite/backend`.
  - Re-routed volume mount path to `/home/appuser/quickbite/data` for persistent SQLite data without shadowing container code.
  - Corrected YAML indentation under `configMapRef` and `secretRef`.
  - Upgraded deployment image to `quickbite:2.0.0` with `imagePullPolicy: IfNotPresent`.
  - Verified 2/2 pods running in 1/1 Running state in Minikube namespace `quickbite`.
- **Docker Hardening:**
  - Added explicit `PYTHONPATH=/home/appuser/quickbite/backend` to environment.
  - Verified non-root execution under UID 10001 (`appuser:appgroup`).
- **Pydantic V2 Migration:**
  - Migrated legacy `class Config` across all models to `ConfigDict(from_attributes=True)`.
  - Enforced strict role validator in `UserRegisterDTO` to disallow self-registration as staff or admin.

---

## [1.3.0] - 2026-09-28 — Docker, Kubernetes & CI/CD Baseline
- Containerized application using `python:3.11-slim` with non-root user.
- Configured Kubernetes manifests (`namespace`, `configmap`, `secret`, `deployment`, `service`).
- Added GitHub Actions pipeline for linting, security scanning, and unit testing.

## [1.2.0] - 2026-09-14 — Security Hardening & Secure Coding
- Implemented Authoritative Server Pricing Engine discarding client-submitted amounts.
- Implemented Server-Side RBAC and BOLA/IDOR ownership checks on orders and restaurants.
- Added mock tokenized payment gateway adapter to reduce PCI-DSS scope.
- Enforced order lifecycle Finite State Machine.

## [1.1.0] - 2026-08-30 — UI Improvements & Authentication
- Added JWT bearer token authentication and salted bcrypt password hashing.
- Added multi-tenant restaurant scoping and in-memory login rate limiter.
- Created initial prototype UI.

## [1.0.0] - 2026-08-15 — QuickBite Baseline
- Initial FastAPI backend with SQLite database and basic CRUD routes.
