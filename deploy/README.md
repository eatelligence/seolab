# SEOLab — VPS deploy

Production deploy on a fresh **Ubuntu 22.04 LTS** VPS in ≤10 minutes.

## Prereqs

- Ubuntu 22.04 LTS, ≥ 2 vCPU / 4 GB RAM (8 GB recommended for site audits)
- Root SSH access
- (Optional) DNS A record pointing your domain to the server's IP

## 1. Clone or upload the repository

```bash
git clone <your-repo-url> seolab
cd seolab
```

Or `scp -r ./SEOLab user@your-server:~/seolab`.

## 2. Run the installer

```bash
sudo ./deploy/install.sh                  # HTTP only on port 80
# or with automatic HTTPS via Caddy + Let's Encrypt:
sudo ./deploy/install.sh seolab.example.com
```

The script:

1. Installs Docker Engine + Compose plugin
2. Hardens UFW (allows 22 / 80 / 443 only) and enables fail2ban
3. Generates a random `SECRET_KEY` and `POSTGRES_PASSWORD` if `.env` is absent
4. Copies the project to `/opt/seolab` and runs `docker compose up -d --build`
5. (If a domain is passed) installs Caddy and writes a `Caddyfile` that
   reverse-proxies the domain to the frontend container with automatic TLS

## 3. Fill in API keys

Edit `/opt/seolab/.env` and provide:

```
DATAFORSEO_LOGIN=
DATAFORSEO_PASSWORD=
ANTHROPIC_API_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_OAUTH_REDIRECT_URI=https://seolab.example.com/api/gsc/oauth/callback
GOOGLE_PAGESPEED_API_KEY=
OPEN_PAGERANK_API_KEY=
```

Then restart:

```bash
cd /opt/seolab
docker compose restart backend worker beat
```

## 4. Verify

```bash
curl -s http://localhost/api/health | jq          # backend health
docker compose logs -f beat                       # Celery beat schedule
docker compose ps                                  # all services Up
```

Open the UI at `http://your-server-ip` (or `https://seolab.example.com`).

## Operations

| Task                          | Command                                                                |
| ----------------------------- | ---------------------------------------------------------------------- |
| View logs                     | `docker compose logs -f backend`                                       |
| Restart one service           | `docker compose restart backend`                                       |
| Apply latest code             | `git pull && docker compose up -d --build`                             |
| Trigger rank tracker now      | `docker compose exec worker celery -A workers.celery_app.celery call workers.tasks.run_rank_tracker_for_all_projects` |
| Trigger an audit              | `curl -X POST http://localhost/api/projects/<id>/audit/runs -H 'content-type: application/json' -d '{"run_pagespeed":true}'` |
| Postgres shell                | `docker compose exec db psql -U seolab seolab`                         |
| Backup database               | `docker compose exec -T db pg_dump -U seolab seolab > backup.sql`      |
| Restore database              | `docker compose exec -T db psql -U seolab -d seolab < backup.sql`      |
| Wipe local volumes (dev only) | `docker compose down -v`                                               |

## Google Search Console OAuth setup

In Google Cloud Console:

1. Create an OAuth 2.0 Client (type: Web application)
2. Authorized redirect URIs: `https://seolab.example.com/api/gsc/oauth/callback`
3. Enable the **Google Search Console API**
4. Copy `client_id` / `client_secret` into `.env` and restart `backend`

The same flow works for `http://localhost/api/gsc/oauth/callback` in dev.

## Scaling notes

- Audit + rank tracker tasks are CPU-bound (crawl) and IO-bound (DataForSEO).
  Increase Celery concurrency in `docker-compose.yml` (`worker` command).
- Postgres volume is `pgdata`. For larger workloads, mount a bigger disk and
  tune `shared_buffers` / `work_mem` via a `postgresql.conf` override.
- Redis is used as broker + cache. The default setup persists with AOF.
- For multi-tenant deployments, add an auth layer in `backend/main.py` and an
  `owner_id` column on `projects` (the schema is ready for it).

## Security checklist

- [ ] Replace generated `SECRET_KEY` with a value you store in a vault
- [ ] Use a strong `POSTGRES_PASSWORD` (the installer generates one)
- [ ] Lock down `.env` permissions: `chmod 600 .env`
- [ ] Enable HTTPS via Caddy (the installer can do this)
- [ ] Restrict GSC OAuth redirect URI to your production domain only
- [ ] Configure off-server `pg_dump` backups (cron + S3)
- [ ] Monitor disk usage of Redis AOF and Postgres
