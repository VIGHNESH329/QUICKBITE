# Phase 8: Attack Tree Modeling & Architectural Refinements — QuickBite

## 1. Primary Attack Tree: "Modify Another Customer's Order or Order Amount"

This attack tree models an adversary attempting to alter an existing customer's order (e.g., cancelling a rival customer's order, changing delivery address) OR tampering with the total payable amount during checkout.

### 1.1 Hierarchical AND/OR Tree Structure

```
[GOAL] Modify Another Customer's Order OR Manipulate Payable Order Amount
  ├── [OR 1.0] Tamper with Order Payable Amount (Pay Less for Food)
  │     ├── [1.1] Client-Side Parameter Tampering in HTTP Request Payload
  │     │     ├── [1.1.1] Modify unit price in POST /api/orders JSON body (e.g. $25 -> $0.01)
  │     │     └── [1.1.2] Inject negative item quantities (e.g. qty: -5 to offset positive costs)
  │     └── [1.2] Intercept & Modify Tokenized Payment Charge Amount
  │           └── [1.2.1] Alter client-submitted payment gateway amount parameter
  │
  └── [OR 2.0] Mutate Another Customer's Existing Order (IDOR / BOLA)
        ├── [OR 2.1] Compromise Legitimate Customer's Authentication
        │     ├── [2.1.1] Brute-force / credential-stuffing user login credentials
        │     ├── [2.1.2] Intercept JWT bearer token in transit (unencrypted HTTP)
        │     └── [2.1.3] Steal token via Cross-Site Scripting (XSS) in browser
        └── [OR 2.2] Bypass Backend Authorization Checks (IDOR / BOLA)
              ├── [2.2.1] Submit cancellation request (POST /api/orders/{id}/cancel) with victim's order ID
              ├── [2.2.2] Submit status update (PATCH /api/orders/{id}/status) pretending to be restaurant staff
              └── [2.2.3] Exploit race condition between order creation and kitchen acceptance
```

---

### 1.2 Node Analysis, Preventive & Detective Controls

| Node ID | Attack Step / Technique | Logic | Preventive Control | Detective Control |
|---|---|---|---|---|
| **1.1.1** | Modify unit price in order creation request | LEAF | **Authoritative Server Pricing**: Backend completely discards client price inputs and looks up item prices directly from the database. | Comparison alert: Log warning if client submitted price differs from database price. |
| **1.1.2** | Inject negative or zero quantities | LEAF | **Strict Schema Validation**: Pydantic `conint(ge=1, le=99)` rejects negative or zero quantities with HTTP 422. | Web Application Firewall (WAF) rule flagging anomalous numerical parameters. |
| **1.2.1** | Tamper with payment charge parameter | LEAF | Server calculates total amount and sends it directly to payment gateway adapter; client never touches payment amount. | Reconcile daily payment gateway captured totals against database order sums. |
| **2.1.1** | Brute-force customer credentials | LEAF | Rate limiting (max 5 attempts/min/IP) + bcrypt salted password hashing with work factor $\ge 12$. | Audit log entry for `AUTH_LOGIN_FAILED`; alert on threshold exceedance ($\ge 5$ failures in 1 min). |
| **2.1.2** | Intercept JWT token in transit | LEAF | Enforce HTTPS/TLS 1.3 with HTTP Strict Transport Security (HSTS) headers. | Network security scanner verifying TLS cipher suites and certificate expiration. |
| **2.1.3** | Steal JWT via Cross-Site Scripting (XSS) | LEAF | Context-aware HTML escaping, `Content-Security-Policy: default-src 'self'`, avoid `eval()` or unescaped `innerHTML`. | Automated DAST scanning for reflected and stored XSS vectors. |
| **2.2.1** | IDOR order cancellation with victim's ID | LEAF | **Ownership Verification**: Check `order.customer_id == current_user.id` and `order.status == 'PLACED'` before cancelling. | Audit log event `AUTHZ_FAILURE_ORDER_MISMATCH` with source IP and attempted order ID. |
| **2.2.2** | Unauthorized order status manipulation | LEAF | **RBAC & Tenant Check**: Enforce `role == restaurant_staff` AND `order.restaurant_id == staff.restaurant_id`. | Audit log event `AUTHZ_FAILURE_STAFF_TENANT_VIOLATION`. |
| **2.2.3** | Race condition state mutation | LEAF | Atomic database transactions with row-level locking (`SELECT ... FOR UPDATE` or atomic state check). | Database transaction conflict logging and latency anomaly alerts. |

---

## 2. Secondary Attack Tree: "Access Payment-Sensitive Information"

```
[GOAL] Exfiltrate or Harvest Sensitive Payment Information
  ├── [OR 1.0] Intercept Raw Payment Credentials During Ingestion
  │     ├── [1.1] Capture raw Primary Account Number (PAN) / CVV on server
  │     └── [1.2] Intercept unencrypted card data in transit from client
  └── [OR 2.0] Harvest Stored Financial Data from Application Tier
        ├── [2.1] Extract database dumps via SQL Injection
        ├── [2.2] Inspect server logs for plaintext payment tokens or card data
        └── [2.3] Exploit over-fetching in API responses (Mass Assignment)
```

| Node ID | Attack Step | Logic | Preventive Control | Detective Control |
|---|---|---|---|---|
| **1.1** | Capture raw card data on server | LEAF | **Tokenization Architecture**: Frontend interacts with mock gateway using tokenized strings (`tok_...`). Server never receives raw PAN/CVV. | Periodic PCI-DSS compliance audits scanning codebase for cardholder patterns. |
| **1.2** | Intercept unencrypted data in transit | LEAF | Strict TLS 1.3 with certificate pinning; deny unencrypted HTTP connections. | Continuous SSL Labs / automated TLS configuration audits. |
| **2.1** | SQL Injection database exfiltration | LEAF | Object-Relational Mapping (SQLAlchemy) with parameterized SQL; no raw string queries. | Database activity monitoring (DAM) alerting on abnormal table-scan query volumes. |
| **2.2** | Log inspection for sensitive secrets | LEAF | Custom log sanitization interceptor that strips tokens, passwords, and authorization headers before logging. | Log pattern scanning (Semgrep/Trufflehog) flagging potential secrets in stdout/log sinks. |
| **2.3** | API response over-fetching | LEAF | Explicit Pydantic response models (`response_model=OrderResponseDTO`) masking internal payment tokens. | Automated contract testing verifying API response bodies against public schemas. |

---

## 3. How Attack Tree Findings Refined the QuickBite Architecture

1. **Elimination of Client-Side Price Reliance**:
   - The finding in Node 1.1.1 led directly to the creation of the dedicated **Authoritative Pricing Engine** in the domain services layer. All client-supplied price parameters were stripped from the API contract.
2. **Centralized Ownership Policy Enforcement**:
   - The risk of IDOR in Nodes 2.2.1 and 2.2.2 prompted the introduction of an **Authorization Policy Middleware** that enforces ownership rules (`customer_id` and `restaurant_id`) before requests reach domain mutation services.
3. **Architectural Isolation of Payment Processing**:
   - The analysis in secondary attack tree Node 1.1 confirmed that QuickBite must never touch or store raw card numbers. The application adopted an opaque tokenization pattern (`tok_...`), reducing PCI-DSS scope to SAQ A-EP.
4. **Append-Only Tamper-Evident Audit Ledger**:
   - To counter repudiation threats, the audit logging system was decoupled into an append-only store with separate privileges, ensuring that even privileged staff users cannot modify historical logs.
