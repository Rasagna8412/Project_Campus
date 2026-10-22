# Project Campus — Low-Cost Staging Deployment Plan

**Document Version:** 1.0.0  
**Status:** Architecture Recommendation for Supervised Pilot & Staging  
**Objective:** Deploy Project Campus to a controlled staging environment without purchasing a custom domain  
**Target Monthly Budget:** $0 to $12 / month  
**Date:** October 2026  

---

## 1. Executive Summary & Staging Readiness Evaluation

The local Project Campus application has passed all verification gates:
* **Backend:** FastAPI with SQLAlchemy 2.0 (240 tests passing in CI; 10-stage student journey verified).
* **Database:** Alembic schema at head `0cbebed2ada2` across 23 tables.
* **Frontend:** React + Vite + Tailwind + KaTeX (48 Vitest tests passing; 0-error production build).
* **Docker Support:** Multi-stage Dockerfiles and `docker-compose.production.yml` pre-configured.

**Readiness Verdict:** **READY FOR STAGING DEPLOYMENT.**

---

## 2. Low-Cost Hosting Architecture Options

### Option A: Single-Node VPS with Docker Compose (Recommended)
This approach mirrors the repository's existing `docker-compose.production.yml` and keeps the entire platform enclosed on a single secure virtual private server.

* **Recommended Provider:** **Hetzner Cloud (CX22)** or **DigitalOcean Basic Droplet** or **AWS Lightsail**
  * Specifications: 2 vCPU, 4 GB RAM, 40 GB NVMe SSD.
  * Estimated Ongoing Cost: **$4.50 – $6.00 / month** (€3.79/mo on Hetzner; $6.00/mo on Lightsail/DigitalOcean).
* **Architecture:**
  * Reverse Proxy: Nginx / Caddy container with automatic Let's Encrypt TLS.
  * Backend: FastAPI container (`uvicorn`, 2 workers).
  * Frontend: Nginx static container serving pre-compiled Vite SPA bundle.
  * Database: Dedicated PostgreSQL 15 container with persistent volume.
* **Temporary URL without Custom Domain:**
  * Free wildcard DNS matching the public VPS IP:
    `staging.<IP_ADDRESS>.nip.io` or `staging.<IP_ADDRESS>.sslip.io`
  * Fully supports automated Let's Encrypt SSL/TLS certificates over HTTPS without purchasing a domain.

---

### Option B: Managed Serverless & Edge PaaS (Zero Infrastructure Maintenance)
For a completely hands-off setup where frontend and database are fully managed:

* **Frontend:** **Vercel** or **Cloudflare Pages**
  * Cost: **$0.00 / month** (Generous free tiers: global CDN, automated Git preview deployments).
  * URL: Automatically provided free subdomains (e.g., `project-campus-staging.vercel.app` or `project-campus.pages.dev`).
* **Backend:** **Render** or **Railway** (Web Service container)
  * Cost: **$5.00 – $7.00 / month** for persistent 512MB–1GB RAM instance.
* **Database:** **Neon** or **Supabase** (Serverless PostgreSQL 15)
  * Cost: **$0.00 / month** (Free tier provides up to 500MB storage and pooled connections, sufficient for 50–200 pilot students).
* **Total Cost:** **$5.00 – $7.00 / month**.

---

## 3. Staging Configuration & Environment Variables

Create a secure `.env.staging` file on the staging host (never commit to source control):

```bash
# Environment Mode
ENVIRONMENT=staging
DEBUG=False
APP_NAME="Project Campus (Staging)"
APP_VERSION=0.1.0

# Server Bindings
HOST=0.0.0.0
PORT=8000

# CORS Whitelist (allow your temporary staging URL)
CORS_ORIGINS=["https://staging.<YOUR_IP>.nip.io","http://localhost:5173"]

# PostgreSQL Connection
DATABASE_URL=postgresql+asyncpg://campus_staging_user:StrongStagingPassword#2026@postgres:5432/campus_staging_db
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Security Secrets (Generate using: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
AUTH_COOKIE_SECURE=True
AUTH_COOKIE_SAMESITE=lax

# Rate Limiting
AUTH_RATE_LIMIT_MAX_ATTEMPTS=10
AUTH_RATE_LIMIT_WINDOW_SECONDS=60
```

---

## 4. Step-by-Step Staging Deployment Sequence (Option A)

### Step 1: Provision Server & Install Docker
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-v2 git
sudo systemctl enable --now docker
```

### Step 2: Clone Repository & Create Staging Env
```bash
git clone https://github.com/Rasagna8412/Project_Campus.git
cd Project_Campus
cp .env.example .env.staging
# Edit .env.staging with strong generated secrets
```

### Step 3: Run Database Migrations
```bash
docker compose -f docker-compose.production.yml run --rm backend alembic upgrade head
```

### Step 4: Boot Staging Stack
```bash
docker compose -f docker-compose.production.yml up -d
```

### Step 5: Verify Health Endpoint
```bash
curl -I https://staging.<YOUR_IP>.nip.io/api/v1/health
# Expected: HTTP/2 200 OK
```

---

## 5. Security, Backups & Monitoring for Staging

1. **Access Restriction:**
   * To prevent unauthorized public access during the pilot, configure HTTP Basic Authentication or IP whitelisting at the Nginx reverse proxy layer.
2. **Automated Daily Backups:**
   * Use the repository's verified backup script via cron:
     ```bash
     0 2 * * * /opt/project_campus/scripts/backup_postgres.sh
     ```
3. **Log Aggregation:**
   * View live application logs using:
     ```bash
     docker compose -f docker-compose.production.yml logs -f --tail=100
     ```

---

## 6. Conclusion & Recommendation

* **Do not buy a domain yet.** Use a free temporary URL (`nip.io` or `vercel.app`) to experience the platform with real students in staging first.
* Deploying to a **$5/month VPS (Option A)** provides the highest fidelity to your production Docker architecture and enables testing of real PostgreSQL database backups and recovery.
