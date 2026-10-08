# Phase 10: Scrum Execution Ceremonies & Metric Definitions — QuickBite

## 1. Scrum Board Template & Workflow States

The QuickBite team utilizes a 4-column physical/digital Kanban board to visualize work items flowing through each 2-week sprint:

```
+--------------------+--------------------+--------------------+--------------------+
|       TO DO        |    IN PROGRESS     |      TESTING       |        DONE        |
+--------------------+--------------------+--------------------+--------------------+
| [US-03] Rate Limit | [US-08] Tokenized  | [US-11] Kitchen    | [US-01] Bcrypt Reg |
|   Auth Endpoints   |   Payment Adapter  |   Order Scoping    |   (3 pts)          |
|   (3 pts)          |   (5 pts)          |   (5 pts)          | [US-02] JWT Login  |
|                    |                    |                    |   (3 pts)          |
| [US-14] Audit Log  | [US-12] Order      | [US-09] Order      | [US-04] Browse     |
|   Append-Only      |   State Machine    |   Ownership Check  |   Menu (3 pts)     |
|   (5 pts)          |   (5 pts)          |   (3 pts)          | [US-06] Order      |
|                    |                    |                    |   Pricing (8 pts)  |
+--------------------+--------------------+--------------------+--------------------+
```

### Definition of Done (DoD) Checklist for Any Story Reaching `DONE`:
1. Peer-reviewed by at least one engineer via Pull Request with zero outstanding comments.
2. 100% of unit tests passing, including negative boundary cases (e.g., negative price, unauthorized order ID).
3. Zero high/critical findings in automated static analysis (`bandit`, `npm audit`).
4. Authorization and ownership verified at service layer.
5. All security-relevant actions instrumented with audit log hooks.
6. Deployed and verified in containerized testing environment.

---

## 2. Daily Scrum Template (Standup Logs)

**Timebox**: 15 minutes daily.
**Format**: Three structured questions per team member:
1. *What did you complete yesterday that helped the team meet the Sprint Goal?*
2. *What will you work on today to help the team meet the Sprint Goal?*
3. *What blockers or impediments are slowing down your progress?*

### Sample Execution Standup (Mid-Sprint 2, Day 6)

#### Lead Backend Engineer:
- **Yesterday**: Implemented the deterministic Finite State Machine for order progression (`PLACED` $\to$ `ACCEPTED` $\to$ `PREPARING` $\to$ `OUT_FOR_DELIVERY` $\to$ `DELIVERED`) in `OrderService`.
- **Today**: Adding tenant ownership check so staff can only update orders where `order.restaurant_id == staff.restaurant_id`.
- **Blockers**: None.

#### Security & Quality Engineer:
- **Yesterday**: Created test cases attempting to manipulate order totals by injecting altered prices and negative quantities into `POST /api/orders`.
- **Today**: Writing test suite for Insecure Direct Object Reference (IDOR) on `GET /api/orders/{id}` and `POST /api/orders/{id}/cancel`.
- **Blockers**: Waiting on merge of the staff JWT context provider to test multi-tenant cross-restaurant boundaries.

#### Frontend Engineer:
- **Yesterday**: Built the responsive Live Order Tracking view with visual stepper milestones and cancellation button.
- **Today**: Integrating kitchen staff dashboard orders table with live status transition buttons.
- **Blockers**: Needed confirmation on whether rejected orders trigger an automatic refund indicator in the UI (confirmed: yes).

---

## 3. Sprint Review Template

**Event**: Sprint Review (End of Sprint 1)  
**Attendees**: Product Owner, Scrum Master, Development Team, Restaurant Partner Representative.

### 3.1 Completed & Accepted Work
- Completed user stories: US-01 (Registration), US-02 (JWT Login), US-04 (Browse Restaurants & Menus), US-05 (Cart Management), US-06 (Order Creation), US-07 (Authoritative Server Pricing).
- Total story points accepted by Product Owner: 27 / 27 points.

### 3.2 Working Software Demonstration
- Demonstrated diner registration with strong password enforcement.
- Demonstrated customer browsing items from "Bella Italia" and adding pasta to cart.
- **Security Demonstration**: Intercepted `POST /api/orders` payload and modified price from $18.50 to $0.05. Showed server rejecting client price and charging exactly $18.50 + delivery + tax.
- Demonstrated receipt generation and database record persistence.

### 3.3 Stakeholder Feedback & Adjustments
- *Feedback*: Restaurant partner noted that kitchen staff need to see item notes (e.g. "no onions") in the order lines.
- *Adjustment*: Logged new backlog story `US-15: Dietary Notes on Order Items` for Sprint 2 refinement.

---

## 4. Sprint Retrospective Template

**Event**: Sprint Retrospective (End of Sprint 1)  
**Framework**: What Went Well / What Did Not Go Well / Improvement Actions.

### 4.1 What Went Well
1. Enforcing authoritative server pricing from Day 1 completely eliminated the risk of price tampering without requiring later refactoring.
2. Pydantic DTOs caught type mismatches and negative quantities automatically before reaching service logic.
3. Automated unit tests ran fast ($<2$ seconds), providing immediate feedback during development.

### 4.2 What Did Not Go Well
1. Initial delay in agreeing on JWT claim structure (`sub` vs `user_id`, `role`, `restaurant_id`), which caused temporary merge conflicts between auth and order branches.
2. Local database schema migrations were applied manually on developer machines, causing one test failure in CI due to missing columns.

### 4.3 Concrete Improvement Actions for Sprint 2
- **Action Item 1**: Standardize JWT claims across all services by defining a central `TokenPayload` Pydantic model in `backend/app/core/security.py`. *(Owner: Lead Backend Engineer)*
- **Action Item 2**: Implement an automated database migration and seeding script executed inside Docker and CI workflows before tests run. *(Owner: DevOps/Dev Engineer)*

---

## 5. Agile Metric Definitions & Calculations

*(Note: In accordance with academic integrity guidelines, these are formal mathematical definitions and tracking mechanisms. Operational values are to be recorded during physical lab execution).*

### 5.1 Velocity
- **Definition**: The total number of accepted user story points completed by the development team within a single sprint.
- **Formula**:
  $$\text{Velocity} = \sum \text{Story Points of all stories meeting Definition of Done in Sprint}$$
- **Usage**: Used in Sprint Planning to forecast team capacity for subsequent sprints without overloading engineers.

### 5.2 Sprint Burndown
- **Definition**: A visual chart plotting remaining story points or estimated hours against elapsed sprint days.
- **Formula**:
  $$\text{Remaining Points}(t) = \text{Total Committed Points} - \sum_{i=1}^{t} \text{Points Completed on Day } i$$
- **Ideal Line**: A straight line from $(\text{Day } 0, \text{Total Points})$ to $(\text{Day } 10, 0)$.

### 5.3 Defect Density
- **Definition**: The number of confirmed software defects discovered per unit size (story points or KLOC) during a sprint.
- **Formula**:
  $$\text{Defect Density} = \frac{\text{Total Confirmed Defects Discovered}}{\text{Total Story Points Delivered}}$$

### 5.4 Carry-Over Rate
- **Definition**: The proportion of committed story points that were not completed within the sprint timebox and had to be pushed to the subsequent sprint.
- **Formula**:
  $$\text{Carry-Over Rate (\%)} = \left( \frac{\text{Committed Points} - \text{Accepted Points}}{\text{Committed Points}} \right) \times 100$$
