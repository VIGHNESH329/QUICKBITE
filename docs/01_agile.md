# Phase 1: Agile Process & Security Integration — QuickBite

## 1. Agile Approach Selection
For the development of **QuickBite**, an online food ordering platform handling consumer transactions, menu management, and real-time order tracking, the **Scrum framework** within Agile was selected, operating with **two-week sprint cadences**.

In food e-commerce, consumer usability and restaurant partner satisfaction depend upon rapid iterations. Concurrently, handling customer credentials, payment tokens, and order state machines necessitates early, continuous security engineering. Scrum provides timeboxed iterations (sprints), structured roles (Product Owner, Scrum Master, Cross-Functional Team), and formal inspect-and-adapt ceremonies (Daily Standups, Sprint Planning, Reviews, and Retrospectives) that accommodate incremental feature delivery while enabling security gating at each iteration boundary.

---

## 2. Rationale for Selecting Scrum for QuickBite
1. **Incremental Delivery of Customer and Staff Value**: The core flow (Browse → Cart → Order → Tracking) can be released as an initial Minimum Viable Product (MVP) in Sprint 1, followed by restaurant staff management, order rejection/acceptance workflows, and payment tokenization hardening in Sprint 2.
2. **Shift-Left Security & Continuous Threat Re-Assessment**: Every new user story introduces a threat boundary (e.g., adding an order cancellation API requires verifying customer order ownership to prevent Broken Object Level Authorization). In Scrum, security requirements are treated as first-class backlog items rather than a late-stage audit phase.
3. **Short Feedback Cycles with Key Stakeholders**: Restaurant owners and customers provide immediate behavioral feedback regarding order dispatching speed, menu item updates, and checkout clarity, reducing wasteful rework.
4. **Enforceable "Definition of Done" (DoD)**: Security controls (static analysis, dependency checks, ownership unit tests, and audit logging) are baked into the Sprint DoD. A story cannot transition to `DONE` unless its security criteria are verified.

---

## 3. Mapping Agile Manifesto Principles to QuickBite

| # | Agile Manifesto Principle | Application to QuickBite System Development |
|---|---|---|
| **1** | *Our highest priority is to satisfy the customer through early and continuous delivery of valuable software.* | Deliver usable food browsing and checkout capabilities in Sprint 1, giving diners immediate value while layering fraud-prevention controls continuously. |
| **2** | *Welcome changing requirements, even late in development. Agile processes harness change for the customer's competitive advantage.* | Easily accommodate shifts in food delivery regulations, merchant discount rates, or third-party payment gateway tokenization requirements without discarding architectural baselines. |
| **3** | *Deliver working software frequently, from a couple of weeks to a couple of months, with a preference to the shorter timescale.* | QuickBite operates on strict 2-week sprints, deploying verified, containerized releases containing end-to-end working features with automated regression suites. |
| **4** | *Business people and developers must work together daily throughout the project.* | Restaurant partners, operations coordinators, and backend engineers align during backlog refinement to ensure menu synchronization and kitchen order-acceptance workflows reflect operational reality. |
| **5** | *Continuous attention to technical excellence and good design enhances agility.* | Proactively refactor order processing logic, isolate payment handling behind abstractions, enforce strict type schemas, and automate security scans to prevent technical and security debt accumulation. |

---

## 4. Realistic Refactoring Opportunities

### Refactoring 1: Consolidating Price Calculation to Authoritative Server-Side Pipeline

#### Before Structure / Code (Vulnerable & Coupled):
The client application sent the calculated `total_amount` or item prices directly within the order creation payload, and the backend blindly accepted it.
```python
# VULNERABLE: Direct acceptance of client-supplied pricing
@router.post("/api/orders")
def create_order(order_payload: dict, user=Depends(get_current_user)):
    # Vulnerability: Trusting client total_amount
    total = order_payload.get("total_amount")
    new_order = db.insert_order(user_id=user.id, amount=total, items=order_payload["items"])
    return {"order_id": new_order.id, "charged": total}
```

#### Problem:
- **Security Vulnerability**: Untrusted client-side data tampering. An attacker could intercept the HTTP request (via proxy like Burp Suite or browser DevTools) and modify `"total_amount": 0.01`, ordering expensive dishes for pennies.
- **Maintainability Flaw**: Business logic for discounts, taxes, and item pricing was duplicated across client mobile/web views and backend models.

#### After Structure / Code (Authoritative Server Pricing Engine):
```python
# SECURE & REFACTORED: Authoritative pricing calculation via domain service
@router.post("/api/orders", response_model=OrderResponse)
def create_order(payload: OrderCreateDTO, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pricing_service = PricingEngine(db)
    # Backend strictly retrieves canonical prices from the database for each item_id
    verified_items, calculated_total = pricing_service.calculate_order_totals(
        restaurant_id=payload.restaurant_id, 
        items=payload.items
    )
    new_order = OrderService(db).create_verified_order(
        customer_id=user.id,
        restaurant_id=payload.restaurant_id,
        items=verified_items,
        total_amount=calculated_total
    )
    return new_order
```

#### Security & Maintainability Benefit:
- **Security**: Complete mitigation of price manipulation attacks (Integrity). The client cannot dictate prices under any circumstances.
- **Maintainability**: Centralizes financial calculation, tax rules, and promotional voucher validation in a single testable `PricingEngine` domain service.

---

### Refactoring 2: Decoupling Direct Database Access into Repository & Authorization Policy Layer

#### Before Structure / Code:
Order status updates and queries mixed raw SQL or ad-hoc ORM filtering with no centralized authorization checks inside the web route.
```python
# VULNERABLE: Ad-hoc query with Missing Ownership Check (IDOR)
@router.get("/api/orders/{order_id}")
def get_order_details(order_id: int, user=Depends(get_current_user)):
    order = db.query("SELECT * FROM orders WHERE id = ?", order_id)
    # Missing verification whether order belongs to 'user' or 'user' is staff for this restaurant!
    return order
```

#### Problem:
- **Security Vulnerability**: Insecure Direct Object Reference (IDOR / BOLA). Any authenticated user can view any other user's delivery address, meal history, and contact details by incrementing `order_id`.
- **Maintainability Flaw**: Database queries and authorization checks were scattered across individual API handlers, leading to inconsistent security enforcement.

#### After Structure / Code:
```python
# SECURE & REFACTORED: Repository Pattern with Centralized Authorization Policy
@router.get("/api/orders/{order_id}", response_model=OrderDetailDTO)
def get_order_details(
    order_id: int, 
    current_user: User = Depends(get_current_user),
    order_repo: OrderRepository = Depends(get_order_repository),
    auth_policy: AccessPolicy = Depends(get_access_policy)
):
    order = order_repo.get_by_id(order_id)
    if not order:
        raise NotFoundException("Order not found")
        
    # Enforce granular tenant & ownership rules
    auth_policy.enforce_order_read_access(current_user, order)
    return order
```

#### Security & Maintainability Benefit:
- **Security**: Ensures strict authorization checks (Confidentiality & Access Control). Customers can only read their own orders; staff can only access orders belonging to their assigned restaurant.
- **Maintainability**: Decouples persistence from routing logic. Authorization policies can be modified in one location and verified with isolated unit tests.

---

## 5. Agile Limitations / Risks & Pragmatic Mitigations

| # | Agile Risk / Limitation | Impact on Security | Concrete Mitigation in QuickBite |
|---|---|---|---|
| **1** | **Accumulation of "Security Debt" in Fast Sprints** | Under pressure to deliver feature velocity ("burn charts"), teams may postpone security activities (threat modeling, input boundary tests, rate limiting) as secondary tasks. | **Security in the Definition of Done (DoD)**: A story is not marked `DONE` without automated unit tests for negative/authorization cases, passing SAST/dependency scans (`npm audit`, `bandit`), and security sign-off on API boundaries. |
| **2** | **Fragmented Documentation & Loss of Architectural Cohesion** | Rapid iteration can result in scattered documentation where developers lack an authoritative overview of cryptographic keys, trust boundaries, and authorization matrices. | **Living Documentation & ADRs**: Architectural Decision Records (ADRs) are committed in the `/docs` repository alongside the codebase. Every API endpoint has typed schemas and OpenAPI/Swagger documentation generated directly from code models. |
