# Phase 9: Product Backlog & Sprint Planning — QuickBite

## 1. Product Backlog Overview

All user stories strictly follow the standard format:
$$\textbf{As a } \langle\text{role}\rangle\textbf{, I want } \langle\text{functionality}\rangle\textbf{, so that } \langle\text{benefit}\rangle.$$

Epics covered: **Authentication**, **Restaurant/Menu**, **Cart**, **Ordering**, **Payment**, **Order Tracking**, **Staff Management**, **Security**, and **Audit**.

---

## 2. Product Backlog Table

| Story ID | Epic | User Story | Priority | Story Points | Acceptance Criteria (Given / When / Then) |
|---|---|---|---|---|---|
| **US-01** | Authentication | **As a** new customer, **I want** to register with my email and password, **so that** I can create a secure account to place food orders. | Must Have | 3 | **Given** a new email and password meeting complexity rules (min 8 chars, 1 digit, 1 special char), **When** submitted to `/api/auth/register`, **Then** the account is created with salted bcrypt hash, role `customer`, and HTTP 201 response. |
| **US-02** | Authentication | **As an** existing user, **I want** to log in with my credentials, **so that** I receive a secure session token to access protected features. | Must Have | 3 | **Given** valid credentials, **When** posted to `/api/auth/login`, **Then** return an HMAC-SHA256 signed JWT with user ID, role, and 1-hour expiry. On invalid credentials, return HTTP 401 without username enumeration. |
| **US-03** | Security | **As a** system administrator, **I want** authentication endpoints to be rate-limited, **so that** brute-force and credential stuffing attacks are thwarted. | Must Have | 3 | **Given** more than 5 failed login requests from the same IP within 1 minute, **When** subsequent attempts arrive, **Then** return HTTP 429 Too Many Requests with a `Retry-After` header. |
| **US-04** | Restaurant/Menu | **As a** diner, **I want** to browse active restaurants and their food items, **so that** I can view descriptions and prices before ordering. | Must Have | 3 | **Given** active restaurants in the database, **When** `GET /api/restaurants` is queried, **Then** return a list of restaurants; querying `/api/restaurants/{id}/menu` returns available items with authoritative prices. Inactive restaurants are omitted. |
| **US-05** | Cart | **As a** diner, **I want** to add, update, and remove food items in my shopping cart, **so that** I can assemble my meal before checkout. | Must Have | 5 | **Given** an authenticated customer, **When** items are added with positive integer quantities ($1..99$), **Then** cart state is persisted. If quantity is outside $1..99$, reject with HTTP 422. |
| **US-06** | Ordering | **As a** diner, **I want** to place an order from my cart, **so that** the restaurant prepares and delivers my food. | Must Have | 8 | **Given** a non-empty cart, delivery address, and payment token, **When** `POST /api/orders` is executed, **Then** compute total using canonical DB prices, charge payment gateway, create order with status `PLACED`, clear the cart, and return HTTP 201. |
| **US-07** | Ordering | **As a** security officer, **I want** all order prices to be calculated server-side, **so that** diners cannot manipulate prices in transit. | Must Have | 5 | **Given** an order submission containing tampered client prices (e.g., $0.01 instead of $20.00), **When** processed by the server, **Then** completely ignore client prices, use canonical DB prices, and charge the true computed amount. |
| **US-08** | Payment | **As a** customer, **I want** my checkout payment to use secure tokenization, **so that** my sensitive card details are never stored on QuickBite servers. | Must Have | 5 | **Given** a valid mock payment token (`tok_...`), **When** checkout executes, **Then** the payment service charges the token via external gateway abstraction, records an opaque transaction ID, and stores zero raw card numbers or CVVs. |
| **US-09** | Order Tracking | **As a** diner, **I want** to view real-time status and history of my orders, **so that** I know when my meal will arrive. | Must Have | 3 | **Given** an authenticated customer, **When** `GET /api/orders` is called, **Then** return only orders where `customer_id == current_user.id`. Requesting another customer's order ID returns HTTP 403 or 404. |
| **US-10** | Order Tracking | **As a** diner, **I want** to cancel my order if it has not yet been accepted, **so that** I am refunded if my plans change. | Should Have | 3 | **Given** an order owned by the customer with status `PLACED`, **When** `POST /api/orders/{id}/cancel` is called, **Then** transition status to `CANCELLED`, trigger refund, and return HTTP 200. If status is `ACCEPTED` or later, return HTTP 400. |
| **US-11** | Staff Management | **As a** restaurant staff member, **I want** to view and manage incoming orders for my restaurant, **so that** the kitchen can prepare meals promptly. | Must Have | 5 | **Given** an authenticated staff member, **When** `GET /api/orders/kitchen` is called, **Then** return orders scoped strictly to `staff.restaurant_id`. Staff cannot view or alter orders for other restaurants. |
| **US-12** | Staff Management | **As a** restaurant staff member, **I want** to update the status of kitchen orders, **so that** customers are updated on meal progress. | Must Have | 5 | **Given** an incoming order, **When** staff updates status following the sequence `PLACED` $\to$ `ACCEPTED` $\to$ `PREPARING` $\to$ `OUT_FOR_DELIVERY` $\to$ `DELIVERED`, **Then** update status and timestamp in DB, write audit entry, and reject illegal transitions with HTTP 400. |
| **US-13** | Restaurant/Menu | **As a** restaurant staff member, **I want** to update menu items and prices for my restaurant, **so that** our offerings reflect current stock and rates. | Should Have | 5 | **Given** authenticated staff, **When** updating an item at `/api/restaurants/{id}/menu`, **Then** verify `staff.restaurant_id == id`, validate price $\ge 0.01$, update DB, and generate an audit log entry. |
| **US-14** | Audit | **As a** platform administrator, **I want** an immutable audit trail of critical actions, **so that** security incidents and disputes can be investigated. | Must Have | 5 | **Given** logins, authz failures, order creations, cancellations, and status changes, **When** executed, **Then** append an entry with timestamp, actor ID, client IP, action type, and status to `AUDIT_LOG`. Only admins can read logs. |

---

## 3. Sprint Allocation (2 Sprints)

### 3.1 Sprint 1: Customer Onboarding, Browsing, Cart & Authoritative Ordering
- **Sprint Goal**: Deliver an end-to-end working MVP enabling customers to register, log in, browse restaurants and menus, manage carts, and place orders with tamper-proof server-side pricing.
- **Sprint Capacity**: 24 Story Points.

| Story ID | User Story Summary | Points | Implementation Tasks |
|---|---|---|---|
| **US-01** | User Registration with bcrypt | 3 | 1. Implement Pydantic `UserRegisterDTO` with password regex.<br>2. Implement bcrypt password hashing service.<br>3. Create `UserRepository` and database migration. |
| **US-02** | JWT User Authentication | 3 | 1. Implement `/api/auth/login` endpoint.<br>2. Build JWT token issuance with HS256 and 1-hour expiry.<br>3. Implement `get_current_user` FastAPI dependency. |
| **US-04** | Restaurant & Menu Browsing | 3 | 1. Create `Restaurant` and `FoodItem` models and seed data.<br>2. Implement `GET /api/restaurants` and `GET /api/restaurants/{id}/menu`.<br>3. Filter out inactive vendors and unavailable items. |
| **US-05** | Persistent Shopping Cart | 5 | 1. Create `Cart` and `CartItem` models with foreign key constraints.<br>2. Implement `GET /api/cart` and `POST /api/cart` endpoints.<br>3. Add quantity boundary validation ($1..99$). |
| **US-06** | Authoritative Order Placement | 8 | 1. Implement `POST /api/orders` endpoint.<br>2. Build `PricingEngine` computing totals from DB prices.<br>3. Implement atomic transaction saving `Order` and `OrderItem` records.<br>4. Integrate simulated payment charge and cart clearing. |
| **US-07** | Price Tampering Immunity | 5 | 1. Write unit tests submitting modified client prices and verifying override.<br>2. Remove client price fields from `OrderCreateDTO`. |
| **Total** | | **27 pts** | *(Sprint 1 committed scope)* |

---

### 3.2 Sprint 2: Staff Order Management, Order Tracking, Payment Security, Audit & Hardening
- **Sprint Goal**: Complete kitchen staff management, order lifecycle state machine, customer order cancellation, tokenized payment protection, tamper-evident audit logging, and automated containerized deployment.
- **Sprint Capacity**: 26 Story Points.

| Story ID | User Story Summary | Points | Implementation Tasks |
|---|---|---|---|
| **US-03** | Auth Rate Limiting | 3 | 1. Implement sliding window in-memory rate limiter middleware.<br>2. Return HTTP 429 upon $>5$ failed attempts/min/IP. |
| **US-08** | Payment Tokenization Protection | 5 | 1. Implement mock payment gateway adapter accepting `tok_...`.<br>2. Mask payment references; verify zero raw card numbers stored. |
| **US-09** | Order Tracking & Ownership (BOLA) | 3 | 1. Implement `GET /api/orders/{id}` with `order.customer_id == user.id` check.<br>2. Write tests verifying HTTP 403 when user attempts to view another's order. |
| **US-10** | Order Cancellation (Status = PLACED) | 3 | 1. Implement `POST /api/orders/{id}/cancel` endpoint.<br>2. Enforce ownership and state invariant checks; trigger refund. |
| **US-11** | Staff Kitchen Orders Dashboard | 5 | 1. Implement `GET /api/orders/kitchen` scoped to `staff.restaurant_id`.<br>2. Prevent cross-tenant restaurant order leakage. |
| **US-12** | Order Lifecycle State Machine | 5 | 1. Implement `PATCH /api/orders/{id}/status` with transition validations.<br>2. Prevent illegal state transitions (e.g. `DELIVERED` $\to$ `PREPARING`). |
| **US-13** | Staff Menu Item Management | 5 | 1. Implement `POST /api/restaurants/{id}/menu` with staff ownership check.<br>2. Add canonical price validation ($\ge 0.01$). |
| **US-14** | Tamper-Evident Audit Logging | 5 | 1. Create `AuditLog` model and repository.<br>2. Wire audit hooks for login, authz failures, orders, and status changes.<br>3. Expose admin-only `GET /api/audit/logs`. |
| **Total** | | **34 pts** | *(Sprint 2 committed scope)* |
