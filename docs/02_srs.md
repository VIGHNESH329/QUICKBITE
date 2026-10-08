# Phase 2: Software Requirements Specification (SRS) — QuickBite

## 1. System Overview & Scope
**QuickBite** is a secure, web-based food ordering platform that connects diners (Customers) with culinary vendors (Restaurants) managed by Restaurant Staff and governed by System Administrators. 

The primary business lifecycle covers:
$$\text{Customer Browsing} \longrightarrow \text{Cart Composition} \longrightarrow \text{Order Placement \& Payment} \longrightarrow \text{Kitchen Acceptance/Rejection} \longrightarrow \text{Status Tracking} \longrightarrow \text{Fulfillment / Cancellation}$$

Security is architected as a foundational pillar across data confidentiality, transactional integrity, strict least-privilege authorization, and auditability.

---

## 2. Stakeholders & Personas

1. **Customer (Diner)**:
   - Primary consumer who registers, authenticates, explores restaurant listings, browses menus, maintains a persistent cart, executes payments, monitors preparation status, and cancels unconfirmed orders.
2. **Restaurant Staff**:
   - Kitchen and counter personnel responsible for maintaining restaurant menus (dishes, pricing, availability), reviewing incoming orders, accepting or rejecting orders, and advancing order fulfillment milestones (`PLACED` → `ACCEPTED` → `PREPARING` → `OUT_FOR_DELIVERY` → `DELIVERED`).
3. **Platform Administrator**:
   - Security and compliance officer responsible for onboarding verified restaurants, managing staff role assignments, inspecting tamper-evident audit logs, and enforcing security policies across tenants.

---

## 3. Requirements Categorization

### 3.1 Functional Requirements (FR)
- **FR-01 (Registration & Authentication)**: The system shall allow Customers and Staff to register and log in securely.
- **FR-02 (Restaurant Browsing)**: The system shall display verified active restaurants with cuisine tags and operating hours.
- **FR-03 (Menu Browsing)**: The system shall present food items with titles, descriptions, canonical prices, and real-time availability.
- **FR-04 (Cart Management)**: The system shall permit users to add items, modify quantities, remove items, and view calculated sub-totals.
- **FR-05 (Order Checkout)**: The system shall allow the customer to submit an order against an active cart.
- **FR-06 (Order Status Tracking)**: Customers shall view real-time status transitions of their active and historical orders.
- **FR-07 (Order Cancellation)**: Customers shall be permitted to cancel an order only while it is in the `PLACED` state (prior to staff acceptance).
- **FR-08 (Staff Order Review)**: Restaurant staff shall view incoming orders targeted exclusively to their assigned restaurant.
- **FR-09 (Staff Order Progression)**: Staff shall update order status (`ACCEPTED`, `REJECTED`, `PREPARING`, `OUT_FOR_DELIVERY`, `DELIVERED`).
- **FR-10 (Menu Management)**: Staff shall add, modify, or toggle availability of food items within their restaurant boundary.

### 3.2 Non-Functional Requirements (NFR)
- **NFR-01 (Performance)**: Order placement API calls shall complete within 350 ms under 1,000 concurrent requests.
- **NFR-02 (Reliability)**: The platform shall guarantee 99.9% uptime with idempotent payment retry semantics.
- **NFR-03 (Usability)**: Intuitive navigation requiring no more than 3 steps from cart to confirmed order, conforming to Nielsen's Usability Heuristics.
- **NFR-04 (Maintainability)**: Modular, decoupled service layers using Dependency Injection and Repository patterns.

### 3.3 Security Requirements (SR)
- **SR-01 (Strong Password Hashing)**: User passwords must be hashed using bcrypt (cost factor $\ge 12$) or Argon2id with unique cryptographic salts.
- **SR-02 (Session & JWT Security)**: Stateless authentication tokens (JWT) must use HMAC-SHA256 (HS256) or RSA signatures, short expiry (15-60 min), and secure transmission.
- **SR-03 (Broken Object Level Authorization Prevention - BOLA/IDOR)**:
  - Customers can access and cancel **only** orders where `order.customer_id == current_user.id`.
  - Staff can access and update **only** orders where `order.restaurant_id == staff.restaurant_id`.
- **SR-04 (Server-Side Price Integrity)**: Item pricing and order total computations must occur exclusively on the server using canonical database prices. Client-supplied price parameters must be discarded.
- **SR-05 (Payment Data Protection & PCI-DSS Scope Reduction)**:
  - Zero storage of raw Primary Account Numbers (PAN), expiration dates, or Card Verification Values (CVV) on QuickBite servers.
  - Transactions must use tokenized payment representations (mock gateway token `tok_...`).
- **SR-06 (Strict Input Validation & Sanitization)**: All incoming payloads must be strictly validated using schema models (Pydantic/DTOs) enforcing length constraints, type checks, and regex matching.
- **SR-07 (Tamper-Evident Audit Logging)**: Critical security events (login success/failure, authorization denials, order placements, status changes, cancellations, menu price modifications) must be logged with timestamp, user ID, client IP, action, and outcome.
- **SR-08 (Secure API Communications)**: All API endpoints must enforce TLS 1.3 in transit with HTTP Strict Transport Security (HSTS) headers.
- **SR-09 (Fail-Closed Error Handling)**: Unhandled exceptions must return sanitized, generic error identifiers (e.g., `{"detail": "Internal processing error", "error_code": "ERR_500"}`) with zero stack traces or SQL snippets exposed.
- **SR-10 (Availability & Denial of Service Defense)**: Sensitive endpoints (e.g., `/api/auth/login`, `/api/orders`) must be rate-limited using a sliding window algorithm (e.g., maximum 5 login attempts per minute per IP).

---

## 4. Comprehensive Requirements Specification Table

| Req ID | Requirement Description | Type | Priority | CIA | Actor | Security Consideration |
|---|---|---|---|---|---|---|
| **REQ-AUTH-01** | User Registration with email, password, role, and profile details | FR / SR | Must Have | C, I | Customer, Staff | Enforce password complexity (min 8 chars, mixed case, digit, symbol); prevent duplicate identity spoofing. |
| **REQ-AUTH-02** | User Authentication returning signed JWT bearer token | FR / SR | Must Have | C, I | All | Secure token generation with HMAC-SHA256, expiration claim (`exp`), and revocation checks. |
| **REQ-AUTH-03** | Rate limiting on authentication endpoint (5 requests/min/IP) | SR | Must Have | A | Public | Mitigate automated credential stuffing and brute-force dictionary attacks. |
| **REQ-MENU-01** | Public retrieval of active restaurant list and food menus | FR | Must Have | A, C | Customer | Read-only access; cache results; filter out unpublished/inactive items to prevent information leakage. |
| **REQ-MENU-02** | Restaurant Staff creates and edits food items and prices | FR / SR | Must Have | I | Staff | Authorize against `staff.restaurant_id`; staff cannot alter competitor menus; audit all price changes. |
| **REQ-CART-01** | Customer creates and manages shopping cart items | FR | Must Have | I | Customer | Cart items bind to customer session; ensure quantities are positive integers ($\ge 1$ and $\le 99$). |
| **REQ-ORD-01** | Authoritative order creation with server-side pricing | FR / SR | Must Have | I, C | Customer | **Zero trust for client prices**. Database unit price multiplied by quantity; atomic database transaction. |
| **REQ-ORD-02** | Customer views own order history and live status | FR / SR | Must Have | C | Customer | **BOLA/IDOR protection**: Enforce `WHERE customer_id = current_user.id`; prevent viewing other users' orders. |
| **REQ-ORD-03** | Customer cancels unconfirmed order (state must be `PLACED`) | FR / SR | Must Have | I | Customer | Ownership check + state machine invariant check (`status == PLACED`). Prevents cancellation after cooking begins. |
| **REQ-STF-01** | Staff views incoming orders for their assigned restaurant | FR / SR | Must Have | C | Staff | Scope query strictly by `staff.restaurant_id`; reject cross-tenant data exfiltration. |
| **REQ-STF-02** | Staff transitions order status through lifecycle | FR / SR | Must Have | I | Staff | Strict state machine transitions (`PLACED` → `ACCEPTED`/`REJECTED` → `PREPARING` → `OUT_FOR_DELIVERY` → `DELIVERED`). |
| **REQ-PAY-01** | Tokenized payment processing via secure gateway abstraction | FR / SR | Must Have | C, I | Customer | Token-only exchange; no card numbers or CVVs stored; enforce transaction idempotency keys. |
| **REQ-LOG-01** | System generates append-only audit trail for sensitive actions | SR | Must Have | C, I, A | System | Immutable logging of authentication, authorization failures, orders, and status updates; redact PII/credentials. |
| **REQ-SEC-01** | Strict HTTP security headers and CORS policy | SR | Should Have | C, I | Public | Enforce `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`. |
| **REQ-SEC-02** | Sanitized uniform error responses | SR | Must Have | C | Public | Shield internal database engine, schema, and directory paths from debugging output. |
