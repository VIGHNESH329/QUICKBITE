# QuickBite: Secure Online Food Ordering Application
## Comprehensive Final Technical Report — Phases 1 to 16
### Secure Software Engineering End-Semester Laboratory Examination
**Release Version:** `2.0.0` (Production Hardened & Kubernetes Ready)  
**Verification Status:** ✅ 20/20 Passing Pytest, 0 Bandit SAST Findings, 0 pip-audit Vulnerabilities, 2/2 Kubernetes Pods Running

---

## Executive Summary & System Overview

QuickBite is an enterprise-grade, defense-in-depth secure web application engineered for modern online food ordering. Unlike commercial food delivery prototypes that prioritize graphical aesthetics over foundational security, QuickBite is architected from inception to proactively eliminate systemic web application and API vulnerabilities, specifically addressing the **OWASP Top 10 Web Application** and **OWASP Top 10 API Security Risks**.

This report encapsulates the comprehensive, end-to-end engineering lifecycle across all 16 phases prescribed in the Secure Software Engineering curriculum. Every phase is backed by verifiable code implementations, architectural decision records (ADRs), automated test results (20 passed tests, 0 failures), static analysis reports (Bandit 0 issues), dependency security audits (pip-audit 0 vulnerabilities), and resilient container orchestration manifests running in Kubernetes with hardened non-root execution.

![Figure 1: High-Level System Architecture](assets/fig_01_architecture.png)
*Figure 1: High-Level System Architecture and Multi-Tier Security Boundaries of QuickBite*

---

## Technology Stack

| Layer / Component | Technology Selected | Engineering & Security Justification |
|---|---|---|
| **Backend Framework** | Python 3.11 / FastAPI | High-speed asynchronous ASGI REST framework with native OpenAPI schema generation and dependency injection. |
| **Data Validation** | Pydantic v2 | Strict type coercion defense, schema boundary validation, regex sanitization, and positive integer constraints. |
| **Database & ORM** | SQLite 3 / SQLAlchemy 2.0 | Third Normal Form (3NF) relational schema with parameterized SQL abstraction, eliminating SQL injection. |
| **Cryptographic Security** | bcrypt & PyJWT | Salted password hashing (cost factor >= 12) and cryptographically signed bearer tokens (HMAC-SHA256) with 60-min TTL. |
| **Frontend Presentation** | HTML5, Vanilla CSS3, JavaScript | Zero-dependency, accessible, responsive interface with context-aware entity escaping against Cross-Site Scripting (XSS). |
| **Automated Testing** | pytest & HTTPX TestClient | Multi-suite harness covering unit cryptography, BOLA authorization boundaries, fuzzing, and end-to-end integration. |
| **Container & Cloud** | Docker & Kubernetes (k8s) | Minimal `python:3.11-slim` base, dedicated non-root user (`appuser:10001`), dropped Linux capabilities, and `seccompProfile: RuntimeDefault`. |

---

## Complete Phase-by-Phase Documentation (Phases 1 to 16)

### Phase 1 — Agile Software Engineering Methodology & Security Integration
- **Objective:** Establish a tailored Agile lifecycle mapping the Agile Manifesto to defensive engineering practices.
- **Key Deliverables:** 2-week Scrum sprints, Security Definition of Done (DoD), 2 architectural refactoring cases.

![Figure 2: Agile Scrum Workflow](assets/fig_02_agile_workflow.png)
*Figure 2: Agile Scrum Workflow with Integrated Security Definition of Done (DoD)*

---

### Phase 2 — Software Requirements Specification (SRS) & Security Requirements
- **Objective:** Formulate functional, non-functional, and security requirements across all stakeholders (Customer, Staff, Admin).
- **Core Requirements:** `REQ-AUTH-01` (Bcrypt), `REQ-AUTH-02` (JWT & Rate Limit), `REQ-ORD-01` (Authoritative Pricing), `REQ-ORD-02` (BOLA Ownership), `REQ-STF-01` (Tenant Isolation), `REQ-PAY-01` (Tokenized Payment), `REQ-LOG-01` (Audit Trail).

![Figure 3: SRS Requirements Matrix](assets/fig_03_srs_requirements.png)
*Figure 3: QuickBite Requirements Specification and Security Control Mapping Artifact*

---

### Phase 3 — UML Use Case & Scenario-Based Analysis Modeling
- **Objective:** Visually model actor interactions, boundary conditions, and exception flows.
- **Key Deliverables:** Complete UML Use Case Diagram, UC-04 (Place Order), UC-09 (Update Status).

![Figure 4: UML Use Case Diagram](assets/fig_04_use_case_diagram.png)
*Figure 4: Complete UML Use Case Diagram for QuickBite Food Ordering Platform*

![Figure 5: BCE Sequence Diagram](assets/fig_05_bce_sequence.png)
*Figure 5: BCE Sequence Diagram for Scenario-Based Analysis: "Place Order"*

---

### Phase 4 & 5 — Data Modeling (3NF ER) & Data Flow Diagrams (DFD)
- **Objective:** Design an optimal relational schema in Third Normal Form (3NF) and trace information flows across trust boundaries.

![Figure 6: 3NF ER Diagram](assets/fig_06_er_diagram.png)
*Figure 6: Complete 3NF Entity-Relationship Diagram (ERD) for QuickBite Relational Database*

![Figure 7: DFD Level 0 Context Diagram](assets/fig_07_dfd_level0.png)
*Figure 7: DFD Level 0 Context Diagram with External Entities and Data Flows*

![Figure 8: DFD Level 1 Decomposition](assets/fig_08_dfd_level1.png)
*Figure 8: DFD Level 1 Decomposition Diagram with Processes, Data Stores, and Trust Boundaries*

---

### Phase 6 — Secure System Architecture & Layered Design Patterns
- **Objective:** Enforce a unidirectional layered software architecture with decoupled service modules.

![Figure 9: Secure Layered Architecture](assets/fig_09_layered_architecture.png)
*Figure 9: Secure Layered Software Architecture and Component Interaction Model*

---

### Phase 7 — User Interface (UI/UX) & Usability Engineering
- **Objective:** Deliver an accessible, responsive, error-preventing interface adhering to Shneiderman's 8 Golden Rules and Nielsen's Usability Heuristics.

![Figure 10: Dedicated Login Page](assets/fig_23_login_page.png)
*Figure 10: Dedicated QuickBite Login Page with 1-Click Role Switcher and Security Notice*

![Figure 11: Storefront Browsing](assets/fig_10_ui_browsing.png)
*Figure 11: Customer Restaurant and Food Menu Browsing Interface with Category Filters*

![Figure 12: Cart Drawer & Checkout](assets/fig_11_ui_cart_checkout.png)
*Figure 12: QuickBite Shopping Cart and Checkout Screen with Authoritative Pricing Notice*

![Figure 13: Live Order Tracking Stepper](assets/fig_12_ui_order_tracking.png)
*Figure 13: Real-Time Order Status Tracking Screen with Visual Progress Stepper and Cancellation*

![Figure 14: Kitchen Staff Dashboard](assets/fig_13_ui_kitchen_dashboard.png)
*Figure 14: Restaurant Staff Kitchen Dashboard with Order Progression Actions*

![Figure 15: Staff Menu Management](assets/fig_14_ui_menu_management.png)
*Figure 15: Restaurant Staff Menu and Authoritative Price Management Interface*

![Figure 16: Admin Audit Ledger](assets/fig_15_ui_admin_audit.png)
*Figure 16: Platform Administrator Tamper-Evident Security Audit Log Viewer*

![Figure 17: Dedicated Registration](assets/fig_24_register_page.png)
*Figure 17: Dedicated Customer Registration Page with Live Password Strength Meter*

---

### Phase 8 & 9 — Threat Modeling (STRIDE) & Attack Tree Analysis
- **Objective:** Systematically enumerate and mitigate threats across 10 core system assets using STRIDE and hierarchical Boolean AND/OR trees.

![Figure 18: STRIDE Threat Model](assets/fig_16_stride_threat_model.png)
*Figure 18: STRIDE Threat Model and Sensitive Information Flow Matrix*

![Figure 19: Attack Tree Pricing](assets/fig_17_attack_tree_pricing.png)
*Figure 19: Hierarchical AND/OR Attack Tree: Order Modification & Price Tampering*

![Figure 20: Attack Tree Payment](assets/fig_18_attack_tree_payment.png)
*Figure 20: Hierarchical AND/OR Attack Tree: Payment Credential Exfiltration*

---

### Phase 10 & 11 — Product Backlog & Scrum Sprint Execution
- **Objective:** Translate requirements and security mitigations into an executable, prioritized product backlog and track Scrum metrics.

![Figure 21: Sprint Planning Breakdown](assets/fig_19_backlog_planning.png)
*Figure 21: Sprint Planning Task Breakdown & Story Point Velocity Allocation*

![Figure 22: Visual Scrum Board](assets/fig_20_scrum_board.png)
*Figure 22: Visual Scrum Sprint Board Illustrating User Stories Flowing Through Work Stages*

---

### Phase 12, 13 & 14 — Automated Testing, Static Security & CI/CD
- **Objective:** Automated test suites, static analysis, and dependency audits running in CI.

![Figure 23: Pytest Terminal Execution](assets/fig_21_pytest_terminal.png)
*Figure 23: Automated Pytest Suite Execution Terminal Output (20 Passed in 1.93s)*

![Figure 24: Bandit SAST & pip-audit](assets/fig_22_bandit_pip_audit.png)
*Figure 24: Verified Static Security Scan (Bandit: 0 Issues) and Dependency Audit (pip-audit: 0 Vulnerabilities)*

---

### Phase 15 & 16 — Hardening, Kubernetes Deployment & Traceability
- **Objective:** Deploy QuickBite into a hardened Kubernetes environment with non-root security contexts, and verify end-to-end traceability.

![Figure 25: Kubernetes Cluster](assets/fig_25_k8s_cluster.png)
*Figure 25: Verified Kubernetes Cluster Status in Minikube (2/2 Pods Running) and Hardened Security Context*

---

## Final Verification Scorecard

| Lifecycle Domain | Verification Metric | Target Standard | Verified Outcome / Status |
|---|---|---|---|
| **Agile & Scrum (P1, 10, 11)** | User Stories Delivered | 100% of Committed Points meeting DoD | **61 / 61 Story Points Accepted (0 Carry-Over)** |
| **Requirements & Models (P2-6)** | Formal Specifications | Complete UML, 3NF ER, DFD, Architecture | **100% Complete & Documented** |
| **UI/UX Engineering (P7)** | Screen Implementation | Light theme, accessible, error-preventing | **Dedicated /login, /register, 8 SPA Screens** |
| **Threat Modeling (P8, 9)** | STRIDE & Attack Trees | All Critical/High paths mitigated | **12 STRIDE threats & 2 Attack Trees Mitigated** |
| **Static Security (SAST) (P13)** | Bandit Security Linter | Zero High / Medium Issues | **0 Issues Found (15 files, 915 LOC) — PASSED** |
| **Dependency SCA (P13)** | pip-audit Vulnerability Audit | Zero Known CVEs | **0 Vulnerabilities Found — PASSED** |
| **Automated Tests (P14)** | Pytest Test Suite | 100% Pass Rate Across All Suites | **20 Passed, 0 Failed in 1.93s — PASSED** |
| **Container Security (P12, 15)** | Docker Non-Root Profile | Non-root UID, dropped capabilities | **appuser:10001, capabilities: drop: ALL — PASSED** |
| **Kubernetes Cluster (P15)** | Minikube Pod Status | Pods Running in isolated namespace | **2/2 Pods Running, Service NodePort 30080 — PASSED** |

---

## Conclusion

The QuickBite project demonstrates that software security is not an afterthought, a late-stage audit activity, or a set of isolated patches applied to a broken architecture. Rather, security is an architectural discipline that must be systematically woven into every phase of the engineering lifecycle.

By aligning Scrum processes with security definitions of done, formally modeling threats via STRIDE and hierarchical attack trees, and implementing defense-in-depth controls across authentication, authorization, and data processing, QuickBite provides a resilient, production-ready online food ordering platform that successfully mitigates major OWASP API and web application risks. Every phase from Phase 1 to Phase 16 has been fully implemented, rigorously tested, and empirically verified with all 25 figures and screenshots embedded.
