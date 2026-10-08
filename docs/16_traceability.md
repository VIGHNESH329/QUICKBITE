# Phase 16: End-to-End Security Traceability & Final Architecture Review — QuickBite

## 1. End-to-End Traceability Matrix for Critical Requirement

This matrix traces the critical security requirement **REQ-ORD-01: Authoritative Order Integrity & Pricing Protection** through the entire software engineering lifecycle, demonstrating full traceability across requirements, architecture, threat models, code implementation, verification, and deployment.

| Lifecycle Phase | Artifact Reference | Specific Traceability Evidence & Implementation Details |
|---|---|---|
| **1. Requirements (SRS)** | `docs/02_srs.md`<br>**REQ-ORD-01** | *"The system shall calculate all item costs, sub-totals, taxes, and final order payable amounts exclusively on the server using canonical database prices. Client-supplied price parameters shall be discarded."* (Priority: Must Have, CIA: Integrity) |
| **2. Use Case Modeling** | `docs/03_use_cases.md`<br>**UC-04: Place Order** | *Use Case Specification Step 4-5*: System extracts item IDs from cart, queries canonical database prices, and calculates subtotal, taxes, and delivery fee. Discards client-supplied price parameters. |
| **3. Analysis Model (BCE)** | `docs/04_analysis.md`<br>**Interaction Sequence** | Sequence step 5-7: `OrderCoordinator` invokes `AuthoritativePricingEngine.calculate_totals(items, db_prices)`. Client never sends or controls unit prices. |
| **4. Data Flow Diagram** | `docs/05_er_dfd.md`<br>**Process 4.0** | DFD Level 1: Process 4.0 (Order Processing & Authoritative Pricing) reads canonical price data directly from Data Store D2 (Menu Store) and passes the verified total to Process 5.0 (Payment Processing). |
| **5. Threat Modeling** | `docs/08_threat_model.md`<br>**Threat TH-02** | STRIDE category: **Tampering**. Attackers intercept `POST /api/orders` to lower prices (e.g., $25.00 $\to$ $0.01$). Risk: **CRITICAL**. Mitigation: Authoritative server-side pricing engine. |
| **6. Vulnerability Analysis**| `docs/08_threat_model.md`<br>**Vulnerability 1** | Client-side parameter tampering due to reliance on client-side calculations. Root cause: trusting user input for financial values. |
| **7. Attack Tree** | `docs/09_attack_tree.md`<br>**Node 1.1.1** | Branch: *Client-Side Parameter Tampering in HTTP Request Payload*. Preventive Control: Authoritative Server Pricing. Detective Control: Alert on price divergence. |
| **8. Product Backlog** | `docs/10_backlog.md`<br>**US-07** | *"As a security officer, I want all order prices to be calculated server-side, so that diners cannot manipulate prices in transit."* (5 Story Points) |
| **9. Sprint Task** | `docs/10_backlog.md`<br>**Sprint 1, US-07 Task** | Task: Implement `PricingEngine` in `backend/app/services/pricing.py` querying DB canonical prices and writing unit tests to verify price override behavior. |
| **10. Implementation** | `backend/app/api/orders.py`<br>& `backend/app/services/pricing.py` | `SecureOrderCreateDTO` completely excludes price fields. Route controller queries database item records, computes verified total, and charges gateway with authoritative sum. |
| **11. Automated Testing** | `tests/test_unit.py`<br>& `tests/test_authz.py` | `test_order_price_tampering_is_prevented()` sends a payload attempting to supply price $0.01; verifies the returned order total is exactly the canonical DB price plus taxes and fees. |
| **12. Deployment Control** | `k8s/deployment.yaml`<br>& `Dockerfile` | Image runs as non-root user (`appuser:10001`), immutable container filesystem, API rate-limiting enabled, ensuring runtime protection against external manipulation. |

---

## 2. Top Three System Risks & Corresponding Controls

| Rank | Security Risk | Threat Scenario & Impact | Multi-Layered Defense Controls |
|---|---|---|---|
| **1** | **Broken Object-Level Authorization (BOLA / IDOR)** | An attacker alters the order ID parameter in `GET /api/orders/{id}` or `POST /api/orders/{id}/cancel` to view or cancel orders belonging to other customers. | 1. **Preventive**: Service layer checks `order.customer_id == current_user.id` for customers, and `order.restaurant_id == staff.restaurant_id` for staff.<br>2. **Detective**: Automatic audit log entry (`AUTHZ_FAILURE_ORDER_MISMATCH`) recording user ID, IP address, and target resource ID. |
| **2** | **Client-Side Financial Parameter Tampering** | An attacker modifies unit prices, discount flags, or order totals using an intercepting proxy during checkout to acquire food items at nominal or zero cost. | 1. **Preventive**: Absolute elimination of price fields from input DTO schemas; all computations occur strictly within `PricingEngine` using canonical database prices.<br>2. **Detective**: Real-time logging of cart totals vs. charged amounts. |
| **3** | **Credential Stuffing & Authentication Brute-Force** | An attacker scripts dictionary attacks against `/api/auth/login` to compromise customer or staff accounts. | 1. **Preventive**: Sliding-window rate limiting (max 5 requests/min per IP); bcrypt password hashing with work factor $\ge 12$; strong password complexity validation.<br>2. **Detective**: Security alerting upon 5 consecutive failed login attempts; audit logging of all authentication failures. |

---

## 3. System Limitations & Future Security Enhancements

### 3.1 Known System Limitations
1. **Mock Payment Gateway Integration**:
   - The current lab implementation uses a simulated tokenized payment gateway adapter (`tok_...`). While architecturally compliant with PCI-DSS tokenization best practices, production deployment requires integration with a certified PCI-DSS Level 1 payment processor (e.g., Stripe Elements or Razorpay Secure SDK) with webhook signature verification.
2. **In-Memory Rate Limiting**:
   - The development rate limiter maintains request counters in local process memory. In a distributed multi-replica deployment behind a load balancer, rate limits must be centralized (e.g., using Redis) to prevent split-brain request quota bypass.

### 3.2 Future Security Enhancements
1. **WebAuthn / FIDO2 Multi-Factor Authentication (MFA)**:
   - Introduce hardware-backed biometric or TOTP secondary authentication for Restaurant Staff and Administrator portals, eliminating risk from credential compromise.
2. **Cryptographic Order State Signatures (HMAC Chain)**:
   - Implement an append-only cryptographic HMAC hash chain on order status transitions, ensuring that each state change is cryptographically signed by the acting staff member or system dispatcher, providing mathematical non-repudiation.
