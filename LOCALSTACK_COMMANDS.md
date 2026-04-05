# LocalStack — Setup, Deployment & Debug Command Log

Full record of every command run to stand up the Gold Scraper on LocalStack,
including the debugging session that found and fixed three deployment bugs.

---

## Environment

| Item | Value |
|------|-------|
| Platform | Windows 11, WSL/bash via Claude Code terminal |
| LocalStack edition | Pro 4.14.1 |
| LocalStack endpoint | `http://localhost:4566` |
| AWS region (fake) | `ap-southeast-1` |
| AWS account (fake) | `000000000000` |
| LocalStack credentials | `AWS_ACCESS_KEY_ID=test` / `AWS_SECRET_ACCESS_KEY=test` |
| API Gateway ID | `2mdvlqjnsz` (stable — reused across re-runs) |

---

## Phase 1 — Initial Setup

### Start LocalStack
```bash
docker-compose up -d
```
Starts LocalStack Pro container defined in `docker-compose.yml`.
All services (DynamoDB, Lambda, API Gateway, S3, EventBridge) start automatically.

### Install Python dependencies
```bash
pip install -r requirements.txt
```

### Create all AWS resources on LocalStack
```bash
python infrastructure/setup_localstack.py
```
**What it does:**
- Creates DynamoDB table `gold-prices` (PK: `date`, string)
- Zips and deploys two Lambda functions: `gold-scraper` and `gold-api`
- Creates API Gateway REST API named `gold-api`, registers `GET /prices` + `OPTIONS /prices`, deploys to `prod` stage
- Creates EventBridge rule `daily-gold-scraper` (cron: `0 6 * * ? *` = 6AM UTC)
- Creates S3 bucket `gold-frontend` with static website hosting

**Output includes the API Gateway ID** — used in `frontend/.env`.

### Run the scraper locally (without Lambda)
```bash
python scripts/run_scraper_local.py
```
Runs the scraper directly (outside Lambda), fetches bajus.org via Playwright, stores today's prices in DynamoDB.

### Seed historical data
```bash
python scripts/seed_historical.py
```
Batch-writes 707 rows from `backend/prices.csv` (2007–2025) into DynamoDB, converting per-gram prices to per-bhari (× 11.664).

### Start the frontend
```bash
cd frontend
npm install
npm run dev
```
Vite dev server starts at `http://localhost:5173`.
`frontend/.env` must have:
```
VITE_API_URL=http://localhost:4566/restapis/2mdvlqjnsz/prod/_user_request_
```

---

## Phase 2 — Debugging (first deployment errors)

After running setup, the frontend reported API connection errors.
The following commands were used to diagnose and fix three bugs.

---

### Debug Step 1 — Confirm LocalStack is running

```bash
curl -s http://localhost:4566/_localstack/health
```

**What to look for:** `"lambda": "running"`, `"dynamodb": "running"`, `"apigateway": "running"`.
If any show `"stopped"`, restart with `docker-compose restart`.

**Result:** All services running. LocalStack Pro 4.14.1.

---

### Debug Step 2 — Test the API endpoint directly

```bash
curl -s "http://localhost:4566/restapis/2mdvlqjnsz/prod/_user_request_/prices/latest"
```

**Result:** `{"message": "Missing Authentication Token"}`

This is API Gateway's way of saying: route not found. The resource `/prices/latest`
was never registered — the setup script only created `/prices`.

```bash
curl -s "http://localhost:4566/restapis/2mdvlqjnsz/prod/_user_request_/prices"
```

**Result:** `{"message": "Internal server error"}`

`/prices` IS registered but the Lambda is crashing internally.

---

### Debug Step 3 — List registered API Gateway resources

```bash
curl -s "http://localhost:4566/restapis" \
  -H "Authorization: AWS4-HMAC-SHA256 Credential=test/20260402/ap-southeast-1/apigateway/aws4_request"
```

**Result:**
```json
{
  "item": [{
    "id": "2mdvlqjnsz",
    "name": "gold-api",
    ...
  }]
}
```
Confirmed: API ID `2mdvlqjnsz` is correct and stable.

```bash
curl -s "http://localhost:4566/restapis/2mdvlqjnsz/resources" \
  -H "Authorization: AWS4-HMAC-SHA256 Credential=test/20260402/ap-southeast-1/apigateway/aws4_request"
```

**Result:** Only `/` (root) and `/prices` exist. No `/prices/latest`, no `/prices/roi`.

**→ Bug #2 confirmed:** `setup_localstack.py` was missing sub-resource creation.

---

### Debug Step 4 — Invoke Lambda directly to see crash details

```bash
AWS_ACCESS_KEY_ID=test \
AWS_SECRET_ACCESS_KEY=test \
AWS_DEFAULT_REGION=ap-southeast-1 \
aws --endpoint-url http://localhost:4566 \
  lambda invoke \
  --function-name gold-api \
  --payload '{"httpMethod":"GET","path":"/prices/latest","queryStringParameters":{}}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/lambda-out.json

cat /tmp/lambda-out.json
```

**Result (first run — before any fixes):**
```json
{
  "errorMessage": "Unable to import module 'handler': No module named 'backend'",
  "errorType": "Runtime.ImportModuleError"
}
```

**→ Bug #1 confirmed:** The Lambda zip packs shared code as `shared/` at the zip root,
but the handler imports used `from backend.shared.dynamo import ...`.
Inside the container, there is no `backend/` — it's just `shared/`.

---

### Fix #1 — Correct Lambda import paths

**Files changed:**
- `backend/lambdas/api/handler.py`
- `backend/lambdas/scraper/handler.py`

**Before:**
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from backend.shared.dynamo import get_latest_price, get_price, get_prices_range
from backend.shared.units import to_bhari, UNIT_LABELS, UNIT_TO_BHARI
```

**After:**
```python
from shared.dynamo import get_latest_price, get_price, get_prices_range
from shared.units import to_bhari, UNIT_LABELS, UNIT_TO_BHARI
```
Removed the broken `sys.path.insert` entirely. The `shared/` module is at the zip root,
so a direct `from shared.X import ...` works without any path manipulation.

---

### Fix #2 — Register missing API Gateway sub-resources

**File changed:** `infrastructure/setup_localstack.py`

Added a loop after creating `/prices` that also creates `/prices/latest` and `/prices/roi`,
each with `GET` and `OPTIONS` methods, both pointing to the same `gold-api` Lambda integration.

```python
for path_part in ["latest", "roi"]:
    sub = apigateway.create_resource(
        restApiId=api_id, parentId=prices_id, pathPart=path_part
    )
    for method in ["GET", "OPTIONS"]:
        apigateway.put_method(...)
        apigateway.put_integration(...)
```

---

### Redeploy after fixes #1 and #2

```bash
python infrastructure/setup_localstack.py
```

Output:
```
Lambda 'gold-scraper' updated.
Lambda 'gold-api' updated.
API Gateway already exists: 2mdvlqjnsz
API deployed: http://localhost:4566/restapis/2mdvlqjnsz/prod/_user_request_/prices
```

### Retest after fixes #1 and #2

```bash
curl -s "http://localhost:4566/restapis/2mdvlqjnsz/prod/_user_request_/prices/latest"
```

**Result:** `{"message": "Internal server error"}` — still failing, but "Missing Authentication
Token" is gone, meaning the route now exists. Progress. Invoked Lambda directly again:

```bash
AWS_ACCESS_KEY_ID=test \
AWS_SECRET_ACCESS_KEY=test \
AWS_DEFAULT_REGION=ap-southeast-1 \
aws --endpoint-url http://localhost:4566 \
  lambda invoke \
  --function-name gold-api \
  --payload '{"httpMethod":"GET","path":"/prices/latest","queryStringParameters":{}}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/lambda-out2.json

cat /tmp/lambda-out2.json
```

**Result (second run — after import fix):**
```json
{
  "errorMessage": "Could not connect to the endpoint URL: \"http://localhost:4566/\"",
  "errorType": "EndpointConnectionError",
  "stackTrace": ["... shared/dynamo.py ... table.scan ..."]
}
```

**→ Bug #3 confirmed:** Lambda runs inside a Docker container managed by LocalStack.
`localhost` inside that container is the container itself, not the host machine.
The Lambda env var `LOCALSTACK_ENDPOINT=http://localhost:4566` was unreachable.

---

### Fix #3 — Use LOCALSTACK_HOSTNAME inside Lambda containers

**File changed:** `backend/shared/dynamo.py`

LocalStack Pro automatically sets `LOCALSTACK_HOSTNAME` inside every Lambda container
to the hostname the container can use to reach back to LocalStack.

**Before:**
```python
ENDPOINT_URL = os.environ.get("LOCALSTACK_ENDPOINT", None)  # None = real AWS
```

**After:**
```python
_ls_hostname = os.environ.get("LOCALSTACK_HOSTNAME")
_ls_port = os.environ.get("EDGE_PORT", "4566")
ENDPOINT_URL = (
    f"http://{_ls_hostname}:{_ls_port}"
    if _ls_hostname
    else os.environ.get("LOCALSTACK_ENDPOINT", None)
)
```

**Why this works:**
- When running inside Lambda container: `LOCALSTACK_HOSTNAME` is set → uses internal hostname
- When running local scripts (seed, scraper test): `LOCALSTACK_HOSTNAME` is not set → falls back to `LOCALSTACK_ENDPOINT=http://localhost:4566`
- On real AWS: neither env var is set → `ENDPOINT_URL = None` → boto3 uses real AWS endpoints

---

### Final redeploy

```bash
python infrastructure/setup_localstack.py
```

---

## Phase 3 — Verification (all routes confirmed working)

### /prices/latest
```bash
curl -s "http://localhost:4566/restapis/2mdvlqjnsz/prod/_user_request_/prices/latest"
```
**Result:**
```json
{
  "date": "2026-04-02",
  "karat_22": 247977.0,
  "karat_21": 236721.0,
  "karat_18": 202895.0,
  "sanatan": 165279.0,
  "currency": "BDT",
  "unit": "bhari",
  "source": "bajus.org"
}
```

### /prices (history range)
```bash
curl -s "http://localhost:4566/restapis/2mdvlqjnsz/prod/_user_request_/prices?start=2025-01-01&end=2025-03-01"
```
**Result:** `{"start": "2025-01-01", "end": "2025-03-01", "count": 60, "prices": [...]}`

### /prices/roi
```bash
curl -s "http://localhost:4566/restapis/2mdvlqjnsz/prod/_user_request_/prices/roi?buy_date=2025-01-15&amount=1&unit=bhari&karat=karat_22"
```
**Result:**
```json
{
  "buy_date": "2025-01-15",
  "current_date": "2026-04-02",
  "karat": "karat_22",
  "amount": 1.0,
  "unit": "bhari",
  "buy_price_per_bhari": 139443.0,
  "current_price_per_bhari": 247977.0,
  "buy_value_bdt": 139443.0,
  "current_value_bdt": 247977.0,
  "profit_loss_bdt": 108534.0,
  "percent_change": 77.83,
  "is_profit": true
}
```

---

## Quick Reference — Common Commands

### Full restart from scratch
```bash
docker-compose down && docker-compose up -d
python infrastructure/setup_localstack.py
python scripts/seed_historical.py
python scripts/run_scraper_local.py
```

### Re-deploy Lambda only (after code changes)
```bash
python infrastructure/setup_localstack.py
```
The script is idempotent — uses `update_function_code` if Lambda already exists.

### Check LocalStack health
```bash
curl -s http://localhost:4566/_localstack/health | python -m json.tool
```

### Invoke Lambda directly (bypass API Gateway)
```bash
AWS_ACCESS_KEY_ID=test \
AWS_SECRET_ACCESS_KEY=test \
AWS_DEFAULT_REGION=ap-southeast-1 \
aws --endpoint-url http://localhost:4566 \
  lambda invoke \
  --function-name gold-api \
  --payload '{"httpMethod":"GET","path":"/prices/latest","queryStringParameters":{}}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/out.json && cat /tmp/out.json
```

### Query DynamoDB directly
```bash
AWS_ACCESS_KEY_ID=test \
AWS_SECRET_ACCESS_KEY=test \
AWS_DEFAULT_REGION=ap-southeast-1 \
aws --endpoint-url http://localhost:4566 \
  dynamodb scan \
  --table-name gold-prices \
  --select COUNT
```

### List API Gateway resources
```bash
curl -s "http://localhost:4566/restapis/2mdvlqjnsz/resources" \
  -H "Authorization: AWS4-HMAC-SHA256 Credential=test/20260402/ap-southeast-1/apigateway/aws4_request"
```

---

## Bug Summary

| # | Symptom | Root cause | Fix |
|---|---------|-----------|-----|
| 1 | `No module named 'backend'` | `zip_lambda()` puts shared code at `shared/` (zip root), but imports used `backend.shared` path | Changed all handler imports to `from shared.X import ...`, removed `sys.path.insert` |
| 2 | `/prices/latest` → `"Missing Authentication Token"` | API Gateway only had `/prices` resource; sub-paths not registered | Added `/prices/latest` and `/prices/roi` resource creation in `setup_localstack.py` |
| 3 | `EndpointConnectionError: localhost:4566` | Lambda runs in Docker container; `localhost` = container, not host | `dynamo.py` now uses `LOCALSTACK_HOSTNAME` env var (set by LocalStack Pro inside containers) |
