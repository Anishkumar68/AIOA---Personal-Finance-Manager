# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install PostgreSQL
Make sure PostgreSQL is installed and running:
```bash
# Check if PostgreSQL is running
pg_isready

# If not installed (Ubuntu/Debian):
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Create Database
```bash
# Create database (as postgres user or with appropriate permissions)
sudo -u postgres createdb finance_db
```

### 3. Setup Environment
```bash
# Copy environment file
cp .env.example .env

# The default values work for local development
# Update SECRET_KEY for production
```

### 4. Install Dependencies & Setup
```bash
# Virtual environment is already created
source .venv/bin/activate

# Run migrations
alembic upgrade head

# Seed demo data
python scripts/seed.py
```

### 5. Start Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🖥️ Start the UI (React + Tailwind)

In a second terminal:
```bash
cd ui
npm install
npm run dev
```

Open: http://localhost:5173

## 🎯 Test the API

### 1. Open API Documentation
Visit: http://localhost:8000/docs

### 2. Register a New User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepassword"
  }'
```

### 3. Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepassword"
  }'
```

### 4. Use Demo Account
- **Email:** demo@example.com
- **Password:** demopassword

## 📚 Common API Examples

### Create an Account
```bash
curl -X POST http://localhost:8000/api/v1/accounts/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Bank Account",
    "type": "bank",
    "currency": "USD",
    "opening_balance": 1000.00
  }'
```

### Create a Transaction
```bash
curl -X POST http://localhost:8000/api/v1/transactions/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "expense",
    "amount": 50.00,
    "account_id": 1,
    "category_id": 6,
    "date": "2026-04-12",
    "note": "Grocery shopping"
  }'
```

### Get Dashboard Summary
```bash
curl -X GET http://localhost:8000/api/v1/dashboard/summary \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🧪 Run Tests
```bash
python -m pytest tests/ -v
```

## 📖 API Endpoints

All endpoints are available at http://localhost:8000/docs

### Authentication
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`

### Accounts
- `GET /api/v1/accounts/`
- `POST /api/v1/accounts/`
- `GET /api/v1/accounts/{id}`
- `PUT /api/v1/accounts/{id}`
- `DELETE /api/v1/accounts/{id}`

### Categories
- `GET /api/v1/categories/`
- `POST /api/v1/categories/`
- `GET /api/v1/categories/{id}`
- `PUT /api/v1/categories/{id}`
- `DELETE /api/v1/categories/{id}`

### Transactions
- `GET /api/v1/transactions/`
- `POST /api/v1/transactions/`
- `GET /api/v1/transactions/{id}`
- `PUT /api/v1/transactions/{id}`
- `DELETE /api/v1/transactions/{id}`

### Dashboard
- `GET /api/v1/dashboard/summary`

### Budgets
- `GET /api/v1/budgets/`
- `POST /api/v1/budgets/`
- `PUT /api/v1/budgets/{id}`
- `DELETE /api/v1/budgets/{id}`

### Reports
- `GET /api/v1/reports/monthly-summary?month=2026-04-01`
- `GET /api/v1/reports/category-expense?month=2026-04-01`
- `GET /api/v1/reports/account-balances`

## 🛠️ Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
pg_isready

# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL
```

### Port Already in Use
```bash
# Use a different port
uvicorn app.main:app --reload --port 8001
```

### Import Errors
```bash
# Make sure you're in the project root
pwd  # Should end with /AIOA

# Reinstall dependencies
pip install -r requirements.txt
```

## 📝 Additional Commands

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Reset Database
```bash
# Drop and recreate
dropdb finance_db
createdb finance_db
alembic upgrade head
python scripts/seed.py
```

## 🎉 You're All Set!

The API is fully functional with:
- ✅ User authentication
- ✅ Account management
- ✅ Category management (15 default categories seeded)
- ✅ Transaction tracking with balance logic
- ✅ Budget monitoring
- ✅ Financial reports
- ✅ Dashboard overview

Happy coding! 🚀
