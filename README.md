# AssetFlow ONE — Backend

## Quick Start

```bash
# 1. Start PostgreSQL
docker compose up -d

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
alembic upgrade head

# 4. Seed demo data
python seed.py

# 5. Start server
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@assetflow.dev | password123 |
| Asset Manager | priya@assetflow.dev | password123 |
| Dept Head (Eng) | rahul@assetflow.dev | password123 |
| Dept Head (Ops) | sneha@assetflow.dev | password123 |
| Employee | vikram@assetflow.dev | password123 |
