# URL Shortener Microservice

FastAPI microservice that shortens URLs using auto-increment PK → Base62 encoding.  
Stack: Python 3.11, FastAPI, SQLAlchemy 2, PostgreSQL, Alembic, pytest.

---


# QUICK START

### Local (requires PostgreSQL running)

```bash
pip install -r requirements.txt
# edit .env with your DATABASE_URL and BASE_DOMAIN
# alembic upgrade head
# uvicorn app.main:app --reload
```

### Docker

```bash
docker-compose up --build
# app is on http://localhost:8000
# migrations run automatically on container start
# to test the tests run:
docker-compose exec app pytest tests/ -v
#to stop container
docker stop urlshortener_app
```

# API Examples

Примеры использования API для сокращения URL.

## Базовый URL
```
http://localhost:8000
```

---

## Migrations (Alembic)

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "description"

# Roll back one step
alembic downgrade -1
```

---

## Tests

```bash
# Requires PostgreSQL at DATABASE_URL in .env.test
pytest tests/ -v

# Base62 unit tests only (no DB needed)
pytest tests/test_shorten.py -v
```

Test files:

| File                  | Type        | Requires DB |
|-----------------------|-------------|-------------|
| `test_shorten.py`     | Unit        | No          |
| `test_redirect.py`    | Integration | Yes         |

`conftest.py` loads `.env.test` before any app import, creates/drops the schema around each test.

---

## Environment variables

| Variable       | Required | Example                                          | Description                    |
|----------------|----------|--------------------------------------------------|--------------------------------|
| `DATABASE_URL` | Yes      | `postgresql://user:pass@localhost:5432/shortener`| PostgreSQL connection string   |
| `BASE_DOMAIN`  | Yes      | `http://localhost:8000`                          | Domain prepended to short URLs |
| `DEBUG`        | No       | `false`                                          | Enables SQL query logging      |



## Project structure

```
url-shortener/
├── app/
│   ├── main.py                 # FastAPI app, router registration
│   ├── core/
│   │   ├── config.py           # Settings loaded from .env
│   │   └── database.py         # SQLAlchemy engine, SessionLocal, get_db()
│   ├── models/
│   │   └── link.py             # Link ORM model
│   ├── schemas/
│   │   └── link.py             # Pydantic request / response schemas
│   ├── repositories/
│   │   └── link_repository.py  # DB access — create, get_by_short_id, increment_clicks
│   ├── services/
│   │   └── link_service.py     # Business logic — shorten, resolve, stats
│   ├── api/
│   │   └── routes.py           # HTTP endpoints
│   └── utils/
│       └── base62.py           # encode_base62 / decode_base62
├── alembic/
│   ├── env.py                  # Alembic wired to settings.database_url + Base.metadata
│   └── versions/
│       └── 0001_create_links_table.py
├── tests/
│   ├── conftest.py             # DB fixtures (PostgreSQL, loaded from .env.test)
│   ├── test_shorten.py         # Unit tests — Base62 encode/decode (no DB)
│   └── test_redirect.py        # Integration tests — all three endpoints
├── .env                        # Local dev environment variables
├── .env.test                   # Test environment variables
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Database — links table

```
┌─────────────────────────────────────────────────────┐
│                       links                         │
├────────────┬──────────────┬───────────────────────┤
│  Column    │  Type        │  Constraints          │
├────────────┼──────────────┼───────────────────────┤
│ id         │ INTEGER      │ PK, autoincrement      │
│ short_id   │ VARCHAR(12)  │ NOT NULL, UNIQUE, idx  │
│ original_url│ TEXT        │ NOT NULL               │
│ clicks     │ BIGINT       │ NOT NULL, default 0    │
│ created_at │ TIMESTAMPTZ  │ NOT NULL, default now()│
└────────────┴──────────────┴───────────────────────┘
```

**short_id generation:**

```
INSERT row  →  DB assigns id (e.g. 125)
                    │
                    ▼
          encode_base62(125)  →  "21"
                    │
                    ▼
          UPDATE links SET short_id = "21" WHERE id = 125
```

Base62 alphabet: `0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`  
A 6-character Base62 code covers ~56 billion unique IDs.

---

## Request flow and DB session lifecycle

```
HTTP Request
     │
     ▼
FastAPI router  ──  Depends(get_db)
                         │
                         │  get_db() opens SessionLocal()
                         │
                         ▼
                    Route handler
                         │
                         ▼
                    Service function
                         │
                         ▼
                    LinkRepo method
                    (db.add / db.flush / db.query / db.execute)
                         │
                         ▼
                    PostgreSQL
                         │
                         ▼
                    Route handler returns response
                         │
                         ▼
                  get_db() finally: db.close()
                         │
                         ▼
               HTTP Response sent to client
```

**Session rules:**
- One session per request, opened by `get_db()`, always closed in `finally`.
- `increment_clicks` uses `UPDATE ... SET clicks = clicks + 1` — atomic, no read-modify-write race.
- `create` uses `flush()` (gets the PK without committing) then sets `short_id`, then a single `commit()`.

---

## Schemas

### ShortenRequest

Accepted by `POST /shorten` as the JSON request body.

```
┌──────────┬─────────┬──────────────────────────────────────────┐
│ Field    │ Type    │ Notes                                    │
├──────────┼─────────┼──────────────────────────────────────────┤
│ url      │ HttpUrl │ Required. Pydantic validates it is a URL.│
└──────────┴─────────┴──────────────────────────────────────────┘
```

Example request body:
```json
{
  "url": "https://www.example.com/very/long/path?q=foo"
}
```

---

### ShortenResponse

Returned by `POST /shorten` (HTTP 201).

```
┌──────────────┬────────┬───────────────────────────────────────────────────┐
│ Field        │ Type   │ Notes                                             │
├──────────────┼────────┼───────────────────────────────────────────────────┤
│ short_id     │ str    │ Base62-encoded DB id, e.g. "21"                   │
│ short_url    │ str    │ BASE_DOMAIN + "/" + short_id, e.g. "http://.../21"│
│ original_url │ str    │ The URL that was shortened                        │
└──────────────┴────────┴───────────────────────────────────────────────────┘
```

Example response:
```json
{
  "short_id": "21",
  "short_url": "http://localhost:8000/21",
  "original_url": "https://www.example.com/very/long/path?q=foo"
}
```

---

### StatsResponse

Returned by `GET /stats/{short_id}` (HTTP 200).

```
┌──────────────┬──────────┬──────────────────────────────────────────┐
│ Field        │ Type     │ Notes                                    │
├──────────────┼──────────┼──────────────────────────────────────────┤
│ short_id     │ str      │ Base62 identifier                        │
│ original_url │ str      │ The original long URL                    │
│ clicks       │ int      │ Total redirect count                     │
│ created_at   │ datetime │ UTC timestamp of creation                │
└──────────────┴──────────┴──────────────────────────────────────────┘
```

Example response:
```json
{
  "short_id": "21",
  "original_url": "https://www.example.com/very/long/path?q=foo",
  "clicks": 42,
  "created_at": "2026-03-05T10:00:00Z"
}
```

---

## Endpoints

| Method | Path              | Status | Description                            |
|--------|-------------------|--------|----------------------------------------|
| POST   | `/shorten`        | 201    | Create a short link                    |
| GET    | `/{short_id}`     | 302    | Redirect to original URL, bump clicks  |
| GET    | `/stats/{short_id}`| 200   | Return click count and metadata        |
| GET    | `/health`         | 200    | Health check                           |

---
