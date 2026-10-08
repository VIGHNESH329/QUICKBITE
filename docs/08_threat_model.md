# Phase 7: Threat Modeling & Vulnerability Analysis — QuickBite

## 1. Asset Inventory & Security Objectives (CIA Triad)

| # | Asset Name | Description & Storage Location | Confidentiality (C) | Integrity (I) | Availability (A) |
|---|---|---|---|---|---|
| **A1** | **User Credentials** | Passwords stored as salted hashes in `USER` database table; plaintext in transit during login. | **High**: Exposure leads to full account takeover. | **High**: Hash modification locks legitimate users out. | **Medium**: Service denial if account locked or altered. |
| **A2** | **Customer Profile (PII)** | Names, delivery addresses, phone numbers in `USER` and `ORDER` tables. | **High**: Regulated under privacy standards (GDPR/DPDP); leaks enable harassment/doxing. | **Medium**: Tampering alters delivery destinations. | **Medium**: Profile retrieval must remain responsive. |
| **A3** | **Restaurant Data** | Vendor identity, legal address, operational status, kitchen manager mapping. | **Medium**: Public info, but banking/commission metadata is confidential. | **High**: Unauthorized status tampering could falsely show restaurant as closed. | **High**: Diners cannot place orders if restaurant listing disappears. |
| **A4** | **Food & Menu Data** | Dishes, descriptions, dietary flags, canonical unit prices in `FOOD_ITEM` table. | **Low**: Menu descriptions are public facing. | **Critical**: Unauthorized price drops cause direct financial loss to vendor. | **High**: Essential for browsing and cart compilation. |
| **A5** | **Cart State** | Transient user item selections and quantities stored in `CART` / `CART_ITEM`. | **Medium**: Dining preferences and habits. | **High**: Tampering could inject arbitrary items into order. | **Medium**: Losing cart causes customer frustration. |
| **A6** | **Order Records** | Line items, subtotal, delivery address, timestamp, order status in `ORDER` table. | **High**: Contains customer consumption history and location. | **Critical**: Modifying status or line items violates contractual fulfillment. | **High**: Real-time order tracking requires continuous availability. |
| **A7** | **Payment Tokens & Metadata** | Gateway transaction references, masked card tokens, settlement statuses. | **High**: Exposing payment tokens allows fraudulent charges on mock gateway. | **Critical**: Falsifying payment success without charging causes financial fraud. | **High**: Essential to confirm revenue before cooking. |
| **A8** | **Authentication & JWT Tokens** | Cryptographic bearer tokens stored in client memory/storage and transmitted in headers. | **High**: Bearer tokens grant direct access to user privileges. | **Critical**: Token forgery bypasses all authorization. | **High**: Revocation or validation failures degrade system. |
| **A9** | **Tamper-Evident Audit Logs** | Security logs recording logins, failed authorizations, price edits, order milestones. | **Medium**: May contain metadata; requires restricted administrative access. | **Critical**: Repudiation prevention relies on append-only immutability. | **High**: Regulatory and forensic investigation availability. |
| **A10**| **Staff Privileges & Scopes** | RBAC role definitions and `restaurant_id` tenant scoping attributes. | **High**: Staff roles must not be discoverable or self-assignable. | **Critical**: Privilege elevation allows kitchen staff to alter rival restaurants. | **High**: Kitchen operations halt without staff access. |

---

## 2. STRIDE Threat Identification & Risk Assessment

Risk is evaluated using the standard qualitative matrix:
$$\text{Risk Level} = \text{Likelihood} \times \text{Impact}$$

| Threat ID | Target Asset | STRIDE Category | Threat Description | Attack Scenario | Impact | Likelihood | Risk Level | Security Control & Mitigation |
|---|---|---|---|---|---|---|---|---|
| **TH-01** | User Credentials | **Spoofing** | Credential stuffing / Brute-force guessing of user passwords. | Attacker scripts millions of login attempts using common passwords against `/api/auth/login`. | High | High | **HIGH** | Rate limiting (5 attempts/min/IP), account lockout threshold, strong password complexity policy. |
| **TH-02** | Food & Menu Data | **Tampering** | Parameter tampering on unit prices during checkout. | Attacker intercepts `POST /api/orders` and alters dish unit price from $25.00 to $0.01. | High | High | **CRITICAL** | **Server-side authoritative pricing**: Backend completely ignores client prices and computes totals from DB prices. |
| **TH-03** | Order Records | **Tampering** | Insecure Direct Object Reference (IDOR) to cancel another diner's order. | Attacker sends `POST /api/orders/942/cancel` replacing order ID with a rival customer's ID. | High | Medium | **HIGH** | Object-level ownership check (`order.customer_id == current_user.id`) enforced in service layer before mutation. |
| **TH-04** | Order & Payment | **Repudiation** | Staff member denies rejecting or accepting an order after customer dispute. | Staff maliciously rejects 50 orders and claims the system automated the action. | Medium | Medium | **MEDIUM** | Append-only audit log recording actor ID, timestamp, old state, new state, and client IP for every transition. |
| **TH-05** | Customer Profile | **Information Disclosure** | IDOR / BOLA exposing personal addresses and phone numbers. | Attacker iterates `GET /api/orders/{id}` from 1 to 10000 harvesting customer names and addresses. | High | High | **CRITICAL** | Strict authorization filter: customers can only query their own orders; staff restricted to their own restaurant. |
| **TH-06** | System APIs | **Denial of Service** | Resource exhaustion via massive cart or search payloads. | Attacker posts an order with 1,000,000 line items or queries search with nested wildcards. | High | Medium | **HIGH** | Pydantic schema validation restricting cart items ($\le 50$), quantity bounds ($1..99$), and query length limits. |
| **TH-07** | Staff Privileges | **Elevation of Privilege** | Mass Assignment vulnerability during user registration. | Attacker sends `{"email": "x", "password": "y", "role": "admin"}` in registration JSON. | Critical | Medium | **CRITICAL** | Strict DTO schema ignoring client-specified roles on public registration; role defaults strictly to `customer`. |
| **TH-08** | Authentication Tokens | **Spoofing** | JWT signature forgery using `none` algorithm or weak HMAC secret. | Attacker crafts a JWT with header `alg: none` or brute-forces a short HMAC secret ("secret123"). | Critical | Low | **HIGH** | Explicit algorithm enforcement (HS256 with cryptographically random 256-bit secret from environment), rejecting `none`. |
| **TH-09** | Payment Information | **Information Disclosure** | Accidental logging of raw card data or payment secrets in debug logs. | Developer outputs request payloads `logger.info(request_body)` into server logs. | Critical | Medium | **HIGH** | PCI-DSS scope reduction: use mock tokenized gateway; implement strict log sanitization / redaction filters. |
| **TH-10** | Restaurant Menu | **Tampering** | Cross-tenant menu manipulation by rogue restaurant staff. | Staff of Restaurant A calls `POST /api/restaurants/B/menu` to poison Restaurant B's prices or disable items. | High | Medium | **HIGH** | Multi-tenant authorization check verifying `staff.restaurant_id == path.restaurant_id` before allowing menu writes. |
| **TH-11** | Database Engine | **Tampering** | SQL Injection via raw SQL queries in search or filter parameters. | Attacker injects `' OR '1'='1` in restaurant cuisine filter. | Critical | Low | **HIGH** | Object-Relational Mapping (SQLAlchemy) with parameterized queries; zero concatenated raw SQL strings. |
| **TH-12** | Client UI | **Tampering** | Stored Cross-Site Scripting (XSS) in food description fields. | Staff enters `<script>stealCookie()</script>` in dish title. | High | Low | **MEDIUM** | Context-aware HTML entity encoding in frontend template rendering; strict Content-Security-Policy (CSP) headers. |

---

## 3. Information Flow Analysis for Sensitive Assets

### 3.1 Asset Flow 1: Authentication Credentials (Passwords & JWT)
1. **Origination**: Plaintext password entered into browser input (`type="password"`).
2. **Transit**: Encapsulated in TLS 1.3 HTTPS POST request to `/api/auth/login`.
3. **Perimeter**: Traverses reverse proxy and rate-limiting filter.
4. **Processing**: `AuthService` extracts username, fetches salted bcrypt hash from `USER` table.
5. **Verification**: Constant-time cryptographic comparison executed (`bcrypt.checkpw`).
6. **Token Issuance**: If valid, HMAC-SHA256 signed JWT is generated with claims (`sub`, `role`, `rest_id`, `exp`).
7. **Storage & Egress**: JWT returned in JSON body, held in memory by frontend client. Raw password is immediately zeroed in server memory and never logged.

### 3.2 Asset Flow 2: Order & Payment Data
1. **Origination**: Diner reviews cart and selects a payment token (`tok_visa_valid`).
2. **Transit**: HTTPS POST to `/api/orders` with item IDs, quantities, address, and payment token.
3. **Verification**: `OrderCoordinator` retrieves canonical prices from database; `PricingEngine` computes authoritative financial total.
4. **Gateway Interaction**: Server forwards payment token and authoritative total to Payment Gateway API. Gateway returns opaque transaction ID.
5. **Persistence**: Order record saved with status `PLACED`, line items saved in `ORDER_ITEM` with price snapshots, payment record saved with transaction ID.
6. **Integrity Rule**: Client-submitted price fields are never processed or persisted.

### 3.3 Asset Flow 3: Staff Authorization & Order Status Updates
1. **Origination**: Staff user clicks "Accept Order" on Kitchen Portal.
2. **Transit**: HTTPS PATCH to `/api/orders/{id}/status` with `{"status": "ACCEPTED"}` and Bearer JWT.
3. **Authorization Check**:
   - `JWTValidator` extracts staff `id` and `restaurant_id`.
   - `RBACEnforcer` verifies user has role `restaurant_staff`.
   - Service fetches order and checks: `order.restaurant_id == staff.restaurant_id`. If mismatch, request is dropped with HTTP 403.
4. **State Machine Verification**: Checks if current state (`PLACED`) allows transition to `ACCEPTED`.
5. **Mutation & Audit**: State persisted in `ORDER` table; audit record written to `AUDIT_LOG` with staff user ID and timestamp.

---

## 4. In-Depth Vulnerability Analysis

### Vulnerability 1: Client-Side Price Manipulation (Tampering)
- **Root Cause**: Reliance on client-side calculations or accepting total prices in HTTP request payloads.
- **Remediation**: Authoritative server-side pricing engine that retrieves menu prices from persistent storage and recalculates all totals server-side.

### Vulnerability 2: Broken Object-Level Authorization (BOLA / IDOR)
- **Root Cause**: Querying objects by user-supplied identifier (e.g., `SELECT * FROM orders WHERE id = :order_id`) without validating whether the requesting user owns or is authorized to view that object.
- **Remediation**: Mandatory ownership filters in queries (`WHERE id = :order_id AND customer_id = :current_user_id`) or explicit authorization checks before returning data.

### Vulnerability 3: SQL Injection (SQLi)
- **Root Cause**: String concatenation in dynamic SQL statements when searching or filtering.
- **Remediation**: Parameterized queries and ORM abstractions (SQLAlchemy) across all data access operations.

### Vulnerability 4: Stored Cross-Site Scripting (XSS)
- **Root Cause**: Rendering unescaped user-supplied inputs (e.g. food item descriptions, user names) directly into web browser DOM.
- **Remediation**: Automatic HTML entity escaping in frontend UI code and implementation of Content Security Policy (`CSP`) headers.

### Vulnerability 5: Sensitive Payment Data Exposure
- **Root Cause**: Capturing and storing raw credit card details on application servers, expanding PCI-DSS regulatory scope and exposure to data breach.
- **Remediation**: Tokenization pattern using mock gateway tokens (`tok_...`), ensuring zero storage or logging of PANs or CVVs.

### Vulnerability 6: Missing State Machine Enforcement (Race Conditions / Illegal State Jumps)
- **Root Cause**: Allowing arbitrary status updates without enforcing logical progression, enabling customers to cancel orders that are already out for delivery or staff to bypass preparation steps.
- **Remediation**: Deterministic Finite State Machine (FSM) implemented in domain service, rejecting any transition not permitted by predefined business rules.
