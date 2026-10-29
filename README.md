# SOLACE Backend

FastAPI backend for the SOLACE application. It provides authentication, product,
cart, order, support-ticket, and AI-powered knowledge endpoints.

## Requirements

- Python and pip
- An OpenAI API key for AI chat, embeddings, and policy indexing

## Local setup

From the repository root, create and activate a virtual environment, then install
the pinned dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate the environment with `.venv\Scripts\activate`.

Create a `.env` file in the repository root. At minimum, set a private JWT
secret and, to use AI features, an OpenAI API key:

```dotenv
OPENAI_API_KEY=your-openai-api-key
JWT_SECRET_KEY=replace-with-a-long-random-secret
```

For example, generate a JWT secret with `openssl rand -hex 32`. Do not commit
`.env` or share its values.

Create the database tables and start the development server:

```bash
python -m scripts.create_db
uvicorn app.main:app --reload
```

The server is available at <http://127.0.0.1:8000>. Interactive API
documentation is at <http://127.0.0.1:8000/docs>, and the health check is
<http://127.0.0.1:8000/api/health>.

The default database is SQLite at `data/solace.db`; the database setup script
creates the `data` directory as needed. ChromaDB persists its local data under
`data/chroma_db` by default.

## Configuration

Settings are loaded from the repository-root `.env` file. Values not set there
use the defaults shown below.

| Variable | Default | Description |
| --- | --- | --- |
| `APP_NAME` | `SOLACE` | API title and application name in the health response |
| `APP_ENV` | `development` | Environment name reported by the health response |
| `APP_DEBUG` | `false` | Debug flag |
| `HOST` | `127.0.0.1` | Configured host |
| `PORT` | `8000` | Configured port |
| `FRONTEND_URL` | `http://localhost:5173` | Single allowed CORS origin |
| `OPENAI_API_KEY` | (empty) | OpenAI credential; required for AI and embedding features |
| `OPENAI_MODEL` | `gpt-4.1-mini` | Chat/completion model |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `DATABASE_URL` | `sqlite:///./data/solace.db` | SQLAlchemy database URL |
| `JWT_SECRET_KEY` | (empty) | Secret used to sign and verify access tokens; set this before use |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access-token lifetime |
| `CHROMA_PERSIST_DIR` | `./data/chroma_db` | Local ChromaDB persistence directory |
| `CHROMA_COLLECTION_NAME` | `solace_knowledge_base` | ChromaDB knowledge collection |
| `CACHE_ENABLED` | `true` | Cache configuration flag |
| `CACHE_TTL_SECONDS` | `3600` | Cache time-to-live in seconds |
| `AI_TEMPERATURE` | `0.2` | AI temperature configuration |
| `AI_MAX_OUTPUT_TOKENS` | `1000` | AI output-token limit configuration |

`HOST`, `PORT`, `APP_DEBUG`, `CACHE_ENABLED`, `CACHE_TTL_SECONDS`, and
`AI_TEMPERATURE` are currently declared in settings but are not applied by the
server or AI service. The `uvicorn` command uses its own defaults unless you
pass `--host` and `--port` explicitly.

## Optional demo data

To create the bundled demo admin and customers, run:

```bash
python -m app.seed
```

The demo accounts use hard-coded sample credentials in
[`scripts/seed_admin.py`](scripts/seed_admin.py) and
[`scripts/seed_customer.py`](scripts/seed_customer.py). Use these only in a
local development database; never use the seeded accounts in a deployed
environment.

To index the bundled demo store policies into ChromaDB (requires
`OPENAI_API_KEY`), run:

```bash
python -m scripts.index_store_policies
```

**Warning:** `python fresh_db.py` drops all existing database tables before
recreating them. Use it only when you intend to erase the database. Add `--seed`
to also load the demo accounts.
