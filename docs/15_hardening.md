# Phase 15: Security Hardening, Audit Logging & Monitoring — QuickBite

## 1. Security Audit Logging Policy

QuickBite maintains an **append-only, tamper-evident audit ledger** to guarantee non-repudiation and facilitate forensic investigation.

### 1.1 Events Subject to Mandatory Audit Logging
1. **`AUTH_LOGIN_SUCCESS`**: Successful customer, staff, or admin authentication.
2. **`AUTH_LOGIN_FAILURE`**: Authentication failure (tracks IP and email attempted).
3. **`AUTHZ_FAILURE`**: Authorization rejection (e.g., customer attempting to view another's order, staff modifying rival restaurant).
4. **`MENU_ITEM_MODIFIED`**: Food dish creation, description update, or price revision by staff.
5. **`ORDER_CREATED`**: Order submission with authoritative total and delivery address.
6. **`ORDER_CANCELLED`**: Customer-initiated cancellation before kitchen acceptance.
7. **`ORDER_STATUS_CHANGED`**: Order lifecycle progression by kitchen staff (`PLACED` $\to$ `ACCEPTED` $\to$ `DELIVERED`).
8. **`STAFF_PRIVILEGE_CHANGED`**: Administrative role assignment or restaurant management reassignment.

### 1.2 Strict Data Redaction & Data Minimization Rules
The logging engine enforces an automated redaction filter. The following sensitive items **must NEVER appear in application logs or audit records**:
- Plaintext user passwords
- Raw JWT tokens or session cookies (must be masked: e.g., `eyJh...`)
- Credit Card Primary Account Numbers (PAN), CVVs, or card expiration dates
- Payment gateway secret API keys
- Database connection credentials

---

## 2. Security Monitoring Metrics & Alerting Rules

| Metric Name | Measurement Window | Alert Trigger Threshold | Potential Security Threat | Automated Response / Incident Playbook |
|---|---|---|---|---|
| **Failed Login Rate** | 1 minute per IP | $\ge 5$ failures within 60s | Credential stuffing or brute-force attack | Trigger HTTP 429 Too Many Requests; temporarily throttle IP for 15 minutes; alert on SecOps dashboard. |
| **Authorization Failures (BOLA/IDOR Spikes)** | 5 minutes platform-wide | $\ge 10$ authorization rejections (`HTTP 403`) | Adversary probing sequential object IDs or escalating privileges | Flag source IP and account; alert security analyst for active IDOR reconnaissance. |
| **Price Tampering Anomalies** | Real-time per request | $\ge 1$ occurrence where client supplied a price field | API client manipulation via proxy or script | Drop client price; enforce authoritative DB price; log warning in security log with client IP. |
| **API Server Error Rate (5xx)** | 5-minute sliding window | $> 2\%$ of total API responses returning 5xx | Application crash, unexpected exception, or denial of service | PagerDuty alert to DevOps; inspect container health and resource utilization. |
| **Payment Gateway Rejection Spikes** | 10 minutes | $> 15\%$ payment decline rate | Card testing fraud or payment gateway connectivity issue | Alert on billing dashboard; verify gateway webhook connectivity. |
| **High Request Rate (DoS Threat)** | 10 seconds per IP | $> 100$ requests in 10s | Layer 7 HTTP flood or scraping bot | Cloudflare / Nginx rate-limiting drops traffic with HTTP 429. |

---

## 3. Comprehensive Production Hardening Checklist

| Domain | Hardening Standard | Verification Method | Status |
|---|---|---|---|
| **Network & Ports** | Only port 8000 exposed internally; external traffic restricted strictly to 443 (HTTPS) via reverse proxy. Direct database port exposure disabled. | Port scan via `nmap` confirms non-standard ports closed. | **Enforced** |
| **Services & OS** | Base OS stripped of build tools (`gcc`, `make`, `curl`, `wget`) in production container. | Container image vulnerability scan. | **Enforced** |
| **Secret Management** | Zero secrets in Git or Dockerfile. Secrets injected via Kubernetes `Secret` resources or runtime environment variables. | Automated git history scan with Trufflehog. | **Enforced** |
| **Dependency Governance** | All Python packages pinned to exact versions in `requirements.txt`. Automated `pip audit` in CI pipeline. | CI build fails on High/Critical CVEs. | **Enforced** |
| **System Updates** | Container base image uses updated `python:3.11-slim` with latest security patches. | Weekly base image rebuild schedule. | **Enforced** |
| **File Permissions** | Container filesystem set to `readOnlyRootFilesystem: true` where practical; writable paths restricted to `/tmp`. | Kubernetes pod security admission check. | **Enforced** |
| **User Privileges** | Application runs as non-root user (`appuser`, UID 10001, GID 10001). `allowPrivilegeEscalation: false`. | Verified via `id` inside running container. | **Enforced** |
| **Container Isolation** | Drop all Linux capabilities (`capabilities: drop: ["ALL"]`). No host network or host IPC access. | Container runtime security profile check. | **Enforced** |
| **Kubernetes Scoping** | Deployment isolated in dedicated `quickbite` namespace with resource requests and limits enforced. | `kubectl get pods -n quickbite` | **Enforced** |
| **Least Privilege (RBAC)**| FastAPI endpoints enforce granular role policies (`customer`, `restaurant_staff`, `admin`) and tenant ownership. | Automated pytest security authorization suite. | **Enforced** |
| **HTTP Security Headers**| Enforce `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Content-Security-Policy`, and `HSTS`. | HTTP response header verification. | **Enforced** |
