# AIOA - Personal Finance Manager

A personal finance management application built with FastAPI (backend) and designed to scale.

## Features

- ✅ **User Authentication** - JWT-based auth with register, login, refresh
- ✅ **Account Management** - Track multiple accounts (cash, bank, wallet, credit card)
- ✅ **Category Management** - Income and expense categories with seeding
- ✅ **Transaction Tracking** - Record income, expenses, and transfers
- ✅ **Dashboard** - Overview of finances, recent transactions, category breakdown
- ✅ **Budget Management** - Set and track monthly budgets per category
- ✅ **Reports** - Monthly summary, category expenses, account balances

## Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **Alembic** - Database migration tool
- **Pydantic** - Data validation using Python type annotations
- **JWT** - Secure authentication
- **PostgreSQL** - Primary database

### Testing
- **pytest** - Testing framework
- **httpx** - Async HTTP client for testing

## Project Structure

```
AIOA/
├── app/
│   ├── api/              # API route handlers
│   │   ├── auth.py
│   │   ├── accounts.py
│   │   ├── categories.py
│   │   ├── transactions.py
│   │   ├── dashboard.py
│   │   ├── budgets.py
│   │   └── reports.py
│   ├── core/             # Core configuration and utilities
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/           # SQLAlchemy database models
│   │   ├── user.py
│   │   ├── account.py
│   │   ├── category.py
│   │   ├── transaction.py
│   │   └── budget.py
│   ├── schemas/          # Pydantic schemas
│   │   ├── auth.py
│   │   ├── account.py
│   │   ├── category.py
│   │   ├── transaction.py
│   │   ├── budget.py
│   │   ├── dashboard.py
│   │   └── pagination.py
│   ├── services/         # Business logic
│   │   ├── auth_service.py
│   │   ├── account_service.py
│   │   ├── category_service.py
│   │   ├── transaction_service.py
│   │   ├── dashboard_service.py
│   │   ├── budget_service.py
│   │   └── report_service.py
│   └── main.py           # FastAPI application entry point
├── alembic/              # Database migrations
│   ├── env.py
│   └── versions/
├── scripts/
│   └── seed.py           # Database seeding script
├── tests/                # Test files
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_accounts.py
│   └── test_transactions.py
├── requirements.txt
├── alembic.ini
├── .env.example
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AIOA
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and update:
   - `DATABASE_URL` - Your PostgreSQL connection string
   - `SECRET_KEY` - A secure random string for JWT signing

5. **Create PostgreSQL database**
   ```bash
   createdb finance_db  # Or use psql: CREATE DATABASE finance_db;
   ```

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Seed the database** (optional, creates demo user and categories)
   ```bash
   python scripts/seed.py
   ```

### Running the Application

**Start the development server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

**Interactive API documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Running the UI (React + Tailwind)

The frontend lives in `AIOA/ui/` and talks to the API at `http://localhost:8000` (Vite dev proxy is configured for `/api/*`).

```bash
cd ui
npm install
npm run dev
```

Then open: `http://localhost:5173`

### Running Tests

```bash
pytest tests/ -v
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user info

### Accounts
- `GET /api/v1/accounts/` - List all accounts
- `POST /api/v1/accounts/` - Create account
- `GET /api/v1/accounts/{id}` - Get account details
- `PUT /api/v1/accounts/{id}` - Update account
- `DELETE /api/v1/accounts/{id}` - Delete/archive account

### Categories
- `GET /api/v1/categories/` - List all categories
- `POST /api/v1/categories/` - Create category
- `GET /api/v1/categories/{id}` - Get category details
- `PUT /api/v1/categories/{id}` - Update category
- `DELETE /api/v1/categories/{id}` - Delete category (if unused)

### Transactions
- `GET /api/v1/transactions/` - List transactions (with filters)
- `POST /api/v1/transactions/` - Create transaction
- `GET /api/v1/transactions/{id}` - Get transaction details
- `PUT /api/v1/transactions/{id}` - Update transaction
- `DELETE /api/v1/transactions/{id}` - Delete transaction

**Filters:** `from_date`, `to_date`, `account_id`, `category_id`, `type`, `search`

### Dashboard
- `GET /api/v1/dashboard/summary` - Get dashboard summary

### Budgets
- `GET /api/v1/budgets/` - List budgets
- `POST /api/v1/budgets/` - Create budget
- `PUT /api/v1/budgets/{id}` - Update budget
- `DELETE /api/v1/budgets/{id}` - Delete budget

### Reports
- `GET /api/v1/reports/monthly-summary?month=YYYY-MM-DD` - Monthly summary
- `GET /api/v1/reports/category-expense?month=YYYY-MM-DD` - Category expense report
- `GET /api/v1/reports/account-balances` - Account balances report

## Business Rules

1. **Account Balance Management**
   - Expense transactions reduce account balance
   - Income transactions increase account balance
   - Transfers move balance between accounts without changing net wealth

2. **Category Validation**
   - Income categories can only be used for income transactions
   - Expense categories can only be used for expense transactions
   - Archived categories cannot be used for new transactions

3. **Transaction Integrity**
   - All transactions belong to a user
   - Deleting/editing transactions recalculates balances
   - Transfer transactions require source and target accounts

4. **Budget Tracking**
   - One budget per category per month
   - Budgets track spending against limits
   - Overspending is flagged

## Development

### Database Migrations

**Create a new migration:**
```bash
alembic revision --autogenerate -m "description of changes"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback migration:**
```bash
alembic downgrade -1
```

### Code Structure

- **models/** - Database models (SQLAlchemy)
- **schemas/** - Request/response schemas (Pydantic)
- **services/** - Business logic layer
- **api/** - HTTP route handlers
- **core/** - Configuration, database, security utilities

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | AIOA - Personal Finance Manager |
| `APP_VERSION` | Application version | 0.1.0 |
| `DEBUG` | Debug mode | False |
| `HOST` | Server host | 0.0.0.0 |
| `PORT` | Server port | 8000 |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `SECRET_KEY` | JWT secret key | - |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | 7 |
| `LOG_LEVEL` | Logging level | INFO |

## Demo User

After running the seed script:
- **Email:** demo@example.com
- **Password:** demopassword

## License

MIT

## Support

For issues, questions, or contributions, please open an issue on GitHub.
