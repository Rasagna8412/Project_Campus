# Project Campus — Phase C: Affordable Staging Deployment & Hosting Architecture Guide

**Document Version:** 1.0.0  
**Status:** Approved for Restricted Staging Evaluation  
**Objective:** Host Project Campus securely for a supervised pilot (5–10 students) at minimal cost ($0 to $7 / month) without purchasing a custom domain.  
**Target Date:** October 2026  

---

## 1. Executive Summary & Cost Boundary

Before investing capital in custom apex domains (`projectcampus.in` or similar), marketing, or multi-node production clusters, Project Campus can be deployed to a secure, low-cost staging environment.

### Target Monthly Budget Comparison:
* **Local LAN Evaluation:** **$0.00 / month** (Free on existing hardware)
* **Single-Node VPS with Docker Compose (Option A):** **~$4.00 – $6.00 / month** (€3.79/mo on Hetzner Cloud; $5.00/mo on Lightsail/DigitalOcean)
* **Hybrid Serverless & Managed PaaS (Option B):** **~$0.00 – $7.00 / month** (Vercel Frontend $0 + Neon DB $0 + Render Backend $7)
* **Domain Acquisition Cost:** **$0.00** (Utilizing free wildcard DNS services: `nip.io` or `sslip.io` with automated Let's Encrypt TLS)

---

## 2. Environment Comparison Matrix

| Deployment Tier | Monthly Cost | Infrastructure Model | Best Suited For | Key Advantages | Operational Constraints |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **Tier 0: Local Machine & LAN** | **$0.00** | Windows 11 host running Uvicorn + Vite dev server. Accessible to phones/laptops on same WiFi via LAN IP. | Internal testing, solo feature exploration, demo recordings. | Zero cost, instant reloads, full diagnostic visibility. | Only accessible on the local WiFi network; computer must remain awake. |
| **Tier 1: Single-Node VPS (Option A — Recommended)** | **$4.00 – $6.00** | 1 Linux VM (2 vCPU, 4GB RAM) running `docker-compose.production.yml`: Caddy/Nginx reverse proxy, FastAPI backend, static SPA container, and PostgreSQL 15. | 5–10 student supervised pilot, external stakeholder reviews. | Exactly mirrors production container architecture; full control over DB & backups; no cold starts; HTTPS included via `nip.io`. | Requires basic Linux server administration via SSH. |
| **Tier 2: Managed Serverless PaaS (Option B)** | **$0.00 – $7.00** | Cloudflare Pages / Vercel (Frontend) + Render / Railway (Backend) + Neon / Supabase (PostgreSQL 15). | Quick cloud staging without Linux VM maintenance. | Automated Git deployments, zero server patching, global CDN for static assets. | Potential cold starts on free tiers; fragmented logs across 3 providers; connection pooling limits on serverless DB. |

---

## 3. Recommended Architecture: Single-Node VPS with Docker Compose (Option A)

This architecture is recommended because it runs Project Campus's existing [`docker-compose.production.yml`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/docker-compose.production.yml) with zero architectural divergence from our tested CI environment.

### 3.1. Infrastructure Blueprint
```
+-------------------------------------------------------------------------------+
|                             STUDENT CLIENTS                                   |
|                      https://staging.<IP>.nip.io                              |
+--------------------------------------+----------------------------------------+
                                       | TLS 443 (Let's Encrypt)
                                       v
+-------------------------------------------------------------------------------+
|                      HETZNER / LIGHTSAIL VPS (Linux VM)                       |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  |                       CADDY / NGINX REVERSE PROXY                       |  |
|  |  * Automatic Let's Encrypt TLS on wildcard domain (staging.<IP>.nip.io) |  |
|  |  * HTTP Basic Auth gate (restricts access to pilot cohort)              |  |
|  |  * Routes / -> Frontend Static Container                                |  |
|  |  * Routes /api/* -> Backend API Container (preserves IP headers)       |  |
|  +-----------------------+-------------------------+-----------------------+  |
|                          |                         |                          |
|             Forward      |                         | Forward                  |
|             Static Req   |                         | API Req                  |
|                          v                         v                          |
|  +--------------------------------+   +------------------------------------+  |
|  |       FRONTEND CONTAINER       |   |       BACKEND API CONTAINER        |  |
|  |  * Pre-built React bundle      |   |  * FastAPI / Uvicorn (2 workers)   |  |
|  |  * Nginx alpine static host    |   |  * Python 3.12+ asyncpg            |  |
|  +--------------------------------+   +------------------+-----------------+  |
|                                                          |                    |
|                                             SQL Queries  | Pool: 5 conn       |
|                                                          v                    |
|                                       +------------------------------------+  |
|                                       |       POSTGRESQL 15 CONTAINER      |  |
|                                       |  * Dedicated persistent volume     |  |
|                                       |  * Daily backup script via cron    |  |
|                                       +------------------------------------+  |
+-------------------------------------------------------------------------------+
```

### 3.2. Temporary Domain Setup (Zero Cost)
Instead of purchasing a custom domain, use **nip.io** or **sslip.io**, which map any subdomain containing an IP address back to that IP address automatically:
* Example: If your staging server's public IP is `138.199.12.45`, your staging URL is:
  ```
  https://staging.138.199.12.45.nip.io
  ```
* **SSL/TLS Support:** Let's Encrypt fully supports issuing valid, free HTTPS certificates for `.nip.io` hostnames. Caddy or Nginx Certbot handles renewal automatically.

---

## 4. Staging Configuration & Environment Security

Create an isolated `.env.staging` file on the VPS (never commit to source control):

```bash
# Staging Environment Mode
ENVIRONMENT=staging
DEBUG=False
APP_NAME="Project Campus (Staging)"
APP_VERSION=0.1.0

# Host Bindings
HOST=0.0.0.0
PORT=8000

# CORS Allowed Origins
CORS_ORIGINS=["https://staging.<SERVER_IP>.nip.io"]

# Database Connection (PostgreSQL 15 Container)
DATABASE_URL=postgresql+asyncpg://campus_staging_user:GenerateAStrongPasswordHere2026!@postgres:5432/campus_staging_db
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

# Security Keys (Generate via: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=generate_a_random_64_character_hex_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Production Cookie Enforcement over HTTPS
AUTH_COOKIE_NAME=campus_access_token
AUTH_COOKIE_SECURE=True
AUTH_COOKIE_SAMESITE=lax

# Rate Limiting
AUTH_RATE_LIMIT_MAX_ATTEMPTS=10
AUTH_RATE_LIMIT_WINDOW_SECONDS=60
FORWARDED_ALLOW_IPS="127.0.0.1,172.16.0.0/12"
```

---

## 5. Potential Behavioral Changes: Local vs Hosted Staging

When moving Project Campus from local development to a hosted staging environment, be aware of the following architectural transitions:

| Feature / Behavior | Local Development (Windows) | Hosted Staging Environment (Linux VM) | Action Required |
| :--- | :--- | :--- | :--- |
| **Database Dialect** | Asynchronous SQLite (`aiosqlite`) via `backend/project_campus_dev.db`. | Dedicated PostgreSQL 15 (`asyncpg`) in Docker container. | Run `alembic upgrade head` and `python -m app.core.seed` on the staging container. |
| **Cookie Security** | `AUTH_COOKIE_SECURE=False` (permits HTTP on `localhost:5173`). | `AUTH_COOKIE_SECURE=True` (strictly enforces `Secure` flag on HTTPS). | Ensure SSL certificate is active before setting `AUTH_COOKIE_SECURE=True`, otherwise browsers reject auth cookies. |
| **CORS Origins** | Accepts `http://localhost:5173` and `http://127.0.0.1:5173`. | Must include `https://staging.<SERVER_IP>.nip.io`. | Update `CORS_ORIGINS` in `.env.staging`. |
| **Proxy Header IP** | Client IP is always `127.0.0.1`. | Client IP passed via `X-Forwarded-For` from Caddy/Nginx. | Ensure `FORWARDED_ALLOW_IPS` includes the Docker network bridge (`172.16.0.0/12`). |
| **Rate Limiter State** | In-memory limiter persists for the life of the Uvicorn process. | In-memory limiter resets if the backend container restarts. | Acceptable for pilot; deploy Redis for production. |

---

## 6. Access Control for Restricted Pilot

To prevent uninvited search crawlers or public internet users from discovering the staging pilot, implement one of these two gates:

### Method A: HTTP Basic Auth on Reverse Proxy (Simplest)
Configure Caddy or Nginx to require a shared username and password (`pilot / academic2026`) before exposing the React frontend:
```caddy
# Caddyfile example
staging.138.199.12.45.nip.io {
    basicauth {
        pilot $2a$14$Zkx19XLiW6... # Hashed password
    }
    reverse_proxy /api/* backend:8000
    reverse_proxy /* frontend:80
}
```

### Method B: Registration Invite Token Gate
If open registration should be disabled on staging, configure the registration endpoint to require an optional `INVITE_CODE=CAMPUS_PILOT_2026`.

---

## 7. Step-by-Step Staging Launch Sequence

### Step 1: Provision Cloud Instance
Create a virtual server on Hetzner Cloud (CX22, €3.79/mo) or AWS Lightsail ($5.00/mo) running **Ubuntu 24.04 LTS**.

### Step 2: Install Docker and Docker Compose
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-v2 git ufw
sudo systemctl enable --now docker

# Configure firewall
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

### Step 3: Clone Repository & Configure Environment
```bash
git clone https://github.com/Rasagna8412/Project_Campus.git /opt/project_campus
cd /opt/project_campus

# Create production/staging environment file
cp .env.example .env.production
nano .env.production # Populate staging secrets and nip.io URL
```

### Step 4: Launch Containers & Execute Database Migrations
```bash
# Build and launch containers in background
docker compose -f docker-compose.production.yml up -d --build

# Run Alembic migrations to head
docker compose -f docker-compose.production.yml exec backend alembic upgrade head

# Seed initial curriculum taxonomy, chapters, lessons, and questions
docker compose -f docker-compose.production.yml exec backend python -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.core.seed import seed_initial_data

async def main():
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)

asyncio.run(main())
"
```

### Step 5: Verify Live Staging Deployment
```bash
curl -I https://staging.<SERVER_IP>.nip.io/api/v1/health
# Expected: HTTP/2 200 with {"status":"healthy","version":"0.1.0","database":"connected"}
```

---

## 8. Staging Teardown & Resource Cleanup Instructions

To completely decommission the staging environment after the pilot concludes and avoid incurring further cloud costs:

1. **Export Final Database Backup:**
   ```bash
   docker compose -f docker-compose.production.yml exec postgres pg_dump -U campus_staging_user -d campus_staging_db | gzip > /tmp/pilot_final_backup.sql.gz
   scp user@<SERVER_IP>:/tmp/pilot_final_backup.sql.gz ./local_backups/
   ```
2. **Stop and Remove Containers & Volumes:**
   ```bash
   cd /opt/project_campus
   docker compose -f docker-compose.production.yml down -v --rmi all
   ```
3. **Terminate Cloud Virtual Server:**
   - Log into the Hetzner or AWS console.
   - Click **"Delete / Terminate Server"**.
   - Cloud billing immediately ceases to accrue.
