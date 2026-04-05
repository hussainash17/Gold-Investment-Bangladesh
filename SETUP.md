# Gold Scraper — Setup Guide

## Prerequisites
- Docker Desktop
- Python 3.12+
- Node.js 20+

## 1. Start LocalStack

```bash
docker-compose up -d
```

## 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

## 3. Create AWS resources in LocalStack

```bash
python infrastructure/setup_localstack.py
```

Copy the API Gateway URL printed at the end.

## 4. Configure frontend

```bash
cd frontend
cp .env.example .env
# Edit .env and paste the API Gateway URL from step 3
```

## 5. Install and run frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## 6. Run the scraper manually (for testing)

```bash
python scripts/run_scraper_local.py
```

This fetches today's prices from bajus.org and stores them in LocalStack DynamoDB.

---

## Project Structure

```
Gold Scraper/
├── backend/
│   ├── lambdas/
│   │   ├── scraper/       # Daily price scraper Lambda
│   │   │   └── handler.py
│   │   └── api/           # API Gateway Lambda (prices + ROI)
│   │       └── handler.py
│   └── shared/
│       ├── dynamo.py      # DynamoDB helpers
│       ├── models.py      # Data models
│       └── units.py       # Gold unit conversions
├── frontend/              # React + Vite SPA
│   └── src/
│       ├── components/    # PriceCard, PriceChart, RoiCalculator, Portfolio
│       ├── hooks/         # useLatestPrice, usePriceHistory
│       └── utils/         # api.js, constants.js, portfolio.js
├── infrastructure/
│   └── setup_localstack.py   # One-time AWS resource setup
├── scripts/
│   └── run_scraper_local.py  # Test scraper without Lambda deploy
├── docker-compose.yml         # LocalStack + Mailhog
└── requirements.txt
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/prices/latest` | Latest gold price record |
| GET | `/prices?start=&end=` | Price history between dates |
| GET | `/prices/roi?buy_date=&amount=&unit=&karat=` | ROI calculation |
