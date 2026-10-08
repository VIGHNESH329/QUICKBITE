# Phase 3: Scenario-Based Analysis Model — "Place Order"

## 1. Overview of the Analysis Model
In robust software engineering (BCE — Boundary-Control-Entity modeling), the scenario-based analysis model bridges requirements to architectural design. This model defines the specific responsibilities and collaborations among:
- **Actors**: External initiators interacting with the system boundary.
- **Boundary Objects**: User interfaces, API controllers, and input validators that encapsulate interaction with external actors.
- **Control Objects**: Domain orchestrators, coordination managers, and business rule engines coordinating the execution flow.
- **Entity Objects**: Core business domain data models and persistence state.

---

## 2. Object Classification for "Place Order"

### 2.1 Actor
- **Customer (Diner)**: Authenticated user initiating checkout.

### 2.2 Boundary Objects
1. `CheckoutUI`: Web/Mobile client view presenting cart summary, address input, and payment authorization interface.
2. `OrderApiController`: FastAPI REST endpoint (`POST /api/orders`) handling HTTP request decoding, header token verification, and payload deserialization.
3. `PaymentGatewayClient`: Network boundary adapter communicating securely with the external tokenized payment processor.

### 2.3 Control Objects
1. `AuthenticationMiddleware`: Verifies cryptographic signature and expiry of the JWT bearer token, resolving the `current_user` principal.
2. `OrderCoordinator`: Central application service orchestrating cart verification, inventory check, transaction execution, and state persistence.
3. `AuthoritativePricingEngine`: Pure business rule engine that calculates subtotal, delivery charges, and taxes strictly from canonical database prices.
4. `AuditLoggerService`: Immutable security logging control that writes audit events into persistent storage.

### 2.4 Entity Objects
1. `Customer`: Entity representing the authenticated diner (`id`, `email`, `role`).
2. `Restaurant`: Entity representing the target culinary provider (`id`, `name`, `is_active`).
3. `FoodItem`: Entity representing individual menu items (`id`, `restaurant_id`, `name`, `price`, `is_available`).
4. `Cart` & `CartItem`: Temporary entities holding customer selections and requested quantities.
5. `Order`: Persistent transaction record (`id`, `customer_id`, `restaurant_id`, `total_amount`, `status`, `created_at`).
6. `OrderItem`: Persistent snapshot record (`order_id`, `food_item_id`, `unit_price`, `quantity`).
7. `Payment`: Record capturing transaction reference, token used, payment status, and amount charged.
8. `AuditLog`: Tamper-evident record of the order placement event.

---

## 3. Interaction Sequence Diagram (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    actor Customer as 👤 Customer
    participant UI as 🖥️ CheckoutUI
    participant Controller as 🚪 OrderApiController
    participant AuthMW as 🛡️ AuthMiddleware
    participant Coordinator as ⚙️ OrderCoordinator
    participant PricingEngine as 🧮 AuthoritativePricingEngine
    participant FoodRepo as 📦 FoodItemRepository
    participant PayClient as 💳 PaymentGatewayClient
    participant OrderRepo as 🗄️ OrderRepository
    participant AuditService as 📜 AuditLoggerService

    Customer->>UI: Clicks "Confirm & Pay Order"
    UI->>Controller: POST /api/orders {restaurant_id, items: [{item_id, qty}], delivery_addr, payment_token}
    
    activate Controller
    Controller->>AuthMW: Validate JWT Token
    AuthMW-->>Controller: Token Valid (Customer: ID=42)

    Controller->>Coordinator: submit_order(customer_id=42, payload)
    activate Coordinator

    Coordinator->>FoodRepo: get_items_by_ids([101, 104])
    FoodRepo-->>Coordinator: [FoodItem(101, price=12.99), FoodItem(104, price=4.50)]

    Coordinator->>PricingEngine: calculate_totals(items, db_prices)
    activate PricingEngine
    Note over PricingEngine: Authoritative Server Pricing:<br/>(12.99 * 1) + (4.50 * 2) = 21.99<br/>+ Tax (2.20) + Delivery (3.00)<br/>Total = 27.19
    PricingEngine-->>Coordinator: Verified Total: $27.19
    deactivate PricingEngine

    Coordinator->>PayClient: execute_charge(token="tok_...", amount=27.19)
    activate PayClient
    Note over PayClient: Secure PCI-DSS boundary:<br/>No raw card data exposed
    PayClient-->>Coordinator: Charge Success (tx_id="tx_889922")
    deactivate PayClient

    Coordinator->>OrderRepo: create_order_atomic(customer_id=42, rest_id=3, total=27.19, status="PLACED")
    activate OrderRepo
    OrderRepo-->>Coordinator: Persisted Order (ID=1001)
    deactivate OrderRepo

    Coordinator->>AuditService: record_event("ORDER_CREATED", actor_id=42, order_id=1001, amount=27.19)
    activate AuditService
    AuditService-->>Coordinator: Audit Log Appended
    deactivate AuditService

    Coordinator-->>Controller: OrderSummaryDTO(order_id=1001, status="PLACED")
    deactivate Coordinator

    Controller-->>UI: HTTP 201 Created {order_id: 1001, status: "PLACED", total: 27.19}
    deactivate Controller

    UI-->>Customer: Display Order Confirmed Screen with Live Tracking
```

---

## 4. Architectural Boundaries and Trust Zones Highlighted in Analysis

1. **Untrusted Boundary (Client-Side)**:
   - The browser / client interface runs in an untrusted execution environment. Any data submitted by the client (including attempted price overrides, custom discounts, or fake user identities) is treated as completely untrusted.
2. **Perimeter Security Boundary (API Controller & Middleware)**:
   - Enforces cryptographic token validation, schema validation (Pydantic), and rate-limiting before any execution enters the domain core.
3. **Internal Core Business Boundary (Coordinator & Pricing Engine)**:
   - Executes authoritative financial computations strictly from verified persistent storage, guaranteeing complete transactional and data integrity.
4. **Third-Party Payment Boundary**:
   - Isolates sensitive financial operations behind an abstract payment client, ensuring no cardholder data (PAN/CVV) ever enters QuickBite application storage.
