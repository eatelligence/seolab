# SEOLab

Open SEO analytics platform — a self-hosted alternative to SEMrush. Multi-project,
docker-composed, deployable on a fresh Ubuntu VPS in ≤10 minutes.

## What's inside

**8 modules**, all scoped per project:

- **Dashboard** — organic traffic (GSC), tracked keywords, visibility, domain authority, audit health
- **Keyword Research** — recursive Google Suggest expansion + DataForSEO volume / KD / CPC / intent / trend
- **Rank Tracker** — daily SERP checks via DataForSEO, visibility curve, alerts on |Δ|>5 spots
- **Site Audit** — async crawler with 14 SEO checks + Core Web Vitals via PageSpeed Insights, PDF report
- **Backlinks** — DataForSEO live index, Open PageRank DA, anchor distribution, toxic detection, daily snapshots
- **Competitors** — side-by-side benchmark, keyword gap, content gap, SERP overlap
- **Content & AI** — Anthropic Claude: SEO briefs, content optimizer, meta variants, 30/60/90-day calendar
- **AI Visibility** — track brand mentions in AI assistant responses with sentiment + competitor share-of-voice

## Stack

| Layer        | Tech                                                            |
| ------------ | --------------------------------------------------------------- |
| Backend      | Python 3.11 · FastAPI · SQLAlchemy 2.0 async · Alembic · Pydantic v2 |
| Workers      | Celery 5 + Redis (beat: rank tracker daily, audit weekly, AI vis daily) |
| Database     | PostgreSQL 15                                                   |
| Cache/queue  | Redis 7                                                         |
| Frontend     | React 18 · Vite · Tailwind · TanStack Query · Recharts · framer-motion |
| Reverse proxy| Nginx (in the frontend container)                               |
| External APIs| DataForSEO · Google Search Console · Google PageSpeed · Open PageRank · Anthropic Claude |

## Quickstart (local)

```bash
cp .env.example .env
# Edit .env — fill in DataForSEO, Anthropic, Google credentials
docker compose up -d --build
open http://localhost
```

API health: `curl http://localhost/api/health | jq`

## Deploy on a fresh Ubuntu 22.04 VPS

```bash
git clone <this-repo> seolab && cd seolab
sudo ./deploy/install.sh                       # HTTP only
# or with automatic HTTPS (Caddy + Let's Encrypt):
sudo ./deploy/install.sh seolab.example.com
```

The installer sets up Docker, UFW, fail2ban, generates secrets, and brings up
the full stack. See [`deploy/README.md`](./deploy/README.md) for the operations
manual, OAuth setup, scaling, and security checklist.

## Project layout

```
SEOLab/
├── docker-compose.yml         # 6 services: db, redis, backend, worker, beat, frontend
├── .env.example               # All required environment variables
├── deploy/
│   ├── install.sh             # One-shot Ubuntu 22.04 installer
│   └── README.md              # Operations manual
├── backend/                   # FastAPI app
│   ├── main.py · config.py · database.py
│   ├── models/                # 14 tables (projects, tags, keywords, rankings,
│   │                          # audit_runs/issues/pages, backlinks/snapshots,
│   │                          # ai_visibility, gsc_tokens)
│   ├── alembic/               # Migrations
│   ├── routers/               # 11 routers — all responses {success, data, error}
│   ├── services/              # External API clients + business logic
│   │                          # (dataforseo, gsc, claude, crawler, audit,
│   │                          #  backlinks, ai_visibility, openpr, pagespeed,
│   │                          #  cache, crypto, suggest, rank_tracker)
│   └── workers/               # Celery app + scheduled tasks
└── frontend/                  # React SPA
    └── src/
        ├── pages/             # 12 pages
        ├── components/        # ui/ primitives + bespoke (HealthRing, MetricCard,
        │                      # Sparkline, DeltaBadge, ProjectSwitcher, ...)
        ├── api/               # Axios clients per module
        ├── context/           # ProjectContext (active project switcher)
        └── lib/               # api, queryClient, format, utils
```

## Multi-project & tags

Every dataset is FK-scoped to `projects.id` — keywords, rankings, audits,
backlinks, AI visibility checks, GSC tokens. Switch projects from the sidebar;
the active project is persisted to localStorage. Tags group projects in
`/tags` and filter the listing in `/projects`.

## License

MIT.
