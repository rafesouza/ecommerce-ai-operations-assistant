# E-commerce AI Operations Assistant

**A Python-based e-commerce operations and analytics platform featuring inventory intelligence, demand forecasting, and machine learning model comparison.**

Built as a software engineering portfolio project to demonstrate backend development, relational databases, data analysis, machine learning, API design, and automated testing.

## Project Overview

E-commerce AI Operations Assistant brings together core e-commerce management features and data-driven decision-support tools.

The application provides a REST API developed with FastAPI, a PostgreSQL database, and an interactive dashboard built with HTML, CSS, and vanilla JavaScript.

It includes statistical demand forecasting, historical forecast accuracy evaluation, and an experimental machine learning component using scikit-learn.

## Key Features

### Product Management

- Create, view, update, and delete products.
- Manage product prices and purchase costs.
- Track available stock.
- Configure inventory parameters.
- Associate products with suppliers.

### Order Management

- Create orders containing multiple products.
- Retrieve order details.
- Manage order statuses.
- Track confirmed sales for analytics.

### Inventory Intelligence

- Inventory monitoring and alerts.
- Product sales velocity analysis.
- Stock coverage estimates.
- Inventory replenishment recommendations.
- Dashboard visualization of inventory indicators.

### Sales and Profitability Analytics

- Operational summary indicators.
- Product profitability estimates.
- Marketplace fee calculations.
- Estimated marketplace profitability.

### Demand Forecasting

- Predict future demand using historical daily sales averages.
- Configure historical analysis periods and forecasting horizons.
- Compare projected demand with available stock.
- Identify potential stock shortages.
- Handle products without sufficient sales history.

### Forecast Accuracy

- Historical backtesting of demand forecasts.
- Comparison of predicted quantities with observed sales.
- Mean Absolute Error (MAE).
- Weighted Absolute Percentage Error (WAPE).
- Product-level evaluation results.

### Machine Learning

- Demand forecasting using scikit-learn LinearRegression.
- Chronological separation of training and evaluation data.
- Comparison with a historical-average baseline.
- Model evaluation using MAE and WAPE.
- Interactive demonstration scenarios covering linear growth, constant sales, and trend reversal.

**Important:** The machine learning comparison currently uses synthetic demonstration data. Its predictive performance has not been validated using real marketplace sales histories.

## Technology Stack

| Layer | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Database | PostgreSQL 17 |
| ORM | SQLAlchemy |
| Database migrations | Alembic |
| Frontend | HTML, CSS, JavaScript |
| Machine learning | scikit-learn |
| Numerical computing | NumPy, SciPy |
| Data validation | Pydantic |
| Testing | pytest, FastAPI TestClient |
| Database environment | Docker Compose |
| Version control | Git, GitHub |
| CI | GitHub Actions |

## Architecture

The application uses a modular structure:

```text
ecommerce-ai-operations-assistant/
├── .github/
├── alembic/
│   └── versions/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   ├── forecast_accuracy.py
│   │   ├── ml_demand_forecast.py
│   │   └── ml_model_comparison.py
│   └── tests/
├── frontend/
│   ├── css/
│   ├── js/
│   └── index.html
├── alembic.ini
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

FastAPI handles HTTP requests and business logic. SQLAlchemy manages database interactions, while Alembic manages schema migrations.

The dashboard communicates with the backend through REST endpoints.

Machine learning calculations are implemented in reusable Python modules.

## Getting Started

### Prerequisites

Install the following tools:

- Python 3.13
- Docker Desktop with Docker Compose
- Git

The examples below use Windows PowerShell.

### 1. Clone the repository

```powershell
git clone https://github.com/rafesouza/ecommerce-ai-operations-assistant.git
cd ecommerce-ai-operations-assistant
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Update `.env` with your local PostgreSQL credentials.

The example configuration uses:

```dotenv
POSTGRES_USER=ecommerce_user
POSTGRES_PASSWORD=replace_with_your_local_password
POSTGRES_DB=ecommerce_ai
POSTGRES_PORT=5433
```

Replace the example password with a suitable local password.

Never commit `.env` files containing actual credentials.

### 5. Start PostgreSQL

```powershell
docker compose up -d db
```

Verify the database container:

```powershell
docker compose ps
```

The PostgreSQL service is configured to use port `5433` on the local machine.

### 6. Apply database migrations

```powershell
python -m alembic upgrade head
```

This command applies the database schema migrations.

### 7. Start the FastAPI application

```powershell
python -m uvicorn backend.app.main:app --reload
```

Open the application at:

**Dashboard:** http://127.0.0.1:8000/

**Interactive API documentation:** http://127.0.0.1:8000/docs

**Health endpoint:** http://127.0.0.1:8000/health

## Main API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Application health |
| GET | `/products` | List products |
| POST | `/products` | Create products |
| GET | `/orders` | List orders |
| POST | `/orders` | Create orders |
| GET | `/suppliers` | List suppliers |
| POST | `/suppliers` | Create suppliers |
| GET | `/analytics/summary` | Operational summary |
| GET | `/inventory/alerts` | Inventory alerts |
| GET | `/inventory/velocity` | Sales velocity |
| GET | `/inventory/coverage` | Stock coverage |
| GET | `/inventory/replenishment` | Replenishment analysis |
| GET | `/analytics/demand-forecast` | Statistical demand forecasting |
| GET | `/analytics/forecast-accuracy` | Historical forecast evaluation |
| POST | `/analytics/ml-model-comparison` | Compare statistical and ML models |

Additional endpoints are available in the interactive API documentation.

## Machine Learning Demonstration

The application implements linear regression to estimate future demand from chronological daily sales observations.

A historical-average model serves as a baseline.

### Example API request

```json
{
  "daily_sales": [
    1, 2, 3, 4, 5, 6, 7,
    8, 9, 10, 11, 12, 13, 14,
    15, 16, 17, 18, 19, 20, 21
  ],
  "evaluation_days": 7
}
```

Send this JSON body to:

`POST /analytics/ml-model-comparison`

The API trains both approaches using earlier observations and evaluates their predictions against the held-out period.

The response includes:

- Historical-average forecast.
- Linear regression forecast.
- Actual sales in the evaluation period.
- MAE for each model.
- WAPE for each model.

The dashboard also provides three predefined synthetic demonstration scenarios.

### Model Limitations

- Linear regression assumes a simple relationship between time and sales.
- The model does not explicitly capture seasonality, promotions, stockouts, or marketplace competition.
- Synthetic demonstration results do not establish real-world forecasting accuracy.
- Historical backtesting uses the current order status because order status transitions are not stored historically.
- Forecasted demand should not be interpreted as guaranteed future sales.

## Automated Testing

The project uses pytest for automated validation of API endpoints, database operations, analytics calculations, forecasting models, and dashboard integration.

Run the complete test suite:

```powershell
python -m pytest backend/tests/ -q -p no:cacheprovider
```

The latest completed local validation passed **253 automated tests**.

GitHub Actions also runs automated tests as part of the development workflow.

## Development Practices

The project follows an incremental development process involving:

- Feature branches.
- Pull requests.
- Automated testing.
- Backend input validation.
- Database migrations.
- Separation of forecasting calculations from API handlers.
- GitHub Actions checks.

## Security and Data

The repository is intended for educational and portfolio use.

Local database credentials are configured using environment variables.

Synthetic data is used for machine learning demonstrations.

Do not commit private customer information, production credentials, or confidential marketplace data.

## Project Scope

This application is a software engineering portfolio project, not a production-ready commercial e-commerce platform.

The current version does not include a complete marketplace data synchronization pipeline, multi-user authentication, or production deployment hardening.

Potential future enhancements include real marketplace integrations, more advanced forecasting models, historical order-status tracking, and additional operational automation.

## Author

**Rafael Gomes de Souza**

Software Engineering Undergraduate
Python | FastAPI | PostgreSQL | Machine Learning | E-commerce Systems

Montpellier, France

[LinkedIn](https://www.linkedin.com/in/rafael-gomes-de-souza-311764239/) | [GitHub](https://github.com/rafesouza)
