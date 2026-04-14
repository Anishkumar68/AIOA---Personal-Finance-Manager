Good.
Use this **exact MVP**. Nothing extra.

## MVP goal

Personal finance app that lets you:

* track money in and out
* see balance
* manage accounts
* manage categories
* check monthly spending
* set simple budgets

---

## 1. Core MVP modules

### A. Auth

Must have:

* sign up
* login
* logout
* refresh token
* forgot password later, not now

For personal test, even this is enough:

* 1 user system with normal auth structure
* keep it ready for multi-user later

---

### B. Accounts

User can create accounts like:

* cash
* bank account
* wallet
* credit card

Fields:

* account name
* account type
* opening balance
* current balance
* currency
* active/inactive

Actions:

* create account
* edit account
* archive account
* list accounts

---

### C. Categories

Two types:

* income
* expense

Examples:

* salary
* food
* rent
* shopping
* transport
* health
* entertainment

Fields:

* name
* type
* color/icon optional later
* active/inactive

Actions:

* create
* edit
* delete only if unused
* list

---

### D. Transactions

This is main feature.

Transaction types:

* income
* expense
* transfer

Fields:

* type
* amount
* account_id
* category_id
* date
* note
* reference optional
* transfer_account_id if transfer
* created_at

Actions:

* add transaction
* edit transaction
* delete transaction
* list transactions
* filter by date
* filter by account
* filter by category
* filter by type
* search by note

Rules:

* expense reduces account balance
* income increases account balance
* transfer moves balance from one account to another
* transfer should create linked double-entry internally or one transfer record with source/target logic

---

### E. Dashboard

Keep it simple.

Show:

* total balance
* this month income
* this month expense
* this month savings
* recent 10 transactions
* expense by category
* account balances

That is enough for MVP.

---

### F. Budget

Simple monthly budget only.

Fields:

* month
* category_id
* limit_amount

Show:

* budget limit
* spent amount
* remaining amount
* overspent status

Actions:

* set budget
* update budget
* delete budget

No yearly budgets now.

---

### G. Reports

Only 3 reports:

1. monthly summary

   * total income
   * total expense
   * net savings

2. category expense report

   * how much spent per category

3. account report

   * balance per account

No PDF export now.
No tax report now.

---

## 2. Exact MVP screens

Frontend pages:

1. Login
2. Dashboard
3. Accounts
4. Categories
5. Transactions List
6. Add/Edit Transaction
7. Budgets
8. Reports
9. Settings basic

That’s enough.

---

## 3. Exact backend API modules

Create these backend modules:

* auth
* users
* accounts
* categories
* transactions
* budgets
* reports
* dashboard

---

## 4. Exact API list

### Auth

* `POST /auth/register`
* `POST /auth/login`
* `POST /auth/refresh`
* `GET /auth/me`

### Accounts

* `GET /accounts`
* `POST /accounts`
* `GET /accounts/{id}`
* `PUT /accounts/{id}`
* `DELETE /accounts/{id}`

### Categories

* `GET /categories`
* `POST /categories`
* `GET /categories/{id}`
* `PUT /categories/{id}`
* `DELETE /categories/{id}`

### Transactions

* `GET /transactions`
* `POST /transactions`
* `GET /transactions/{id}`
* `PUT /transactions/{id}`
* `DELETE /transactions/{id}`

Filters in list:

* from_date
* to_date
* account_id
* category_id
* type
* search
* page
* limit

### Dashboard

* `GET /dashboard/summary`

### Budgets

* `GET /budgets`
* `POST /budgets`
* `PUT /budgets/{id}`
* `DELETE /budgets/{id}`

### Reports

* `GET /reports/monthly-summary`
* `GET /reports/category-expense`
* `GET /reports/account-balances`

---

## 5. Exact database tables for MVP

Create only these first:

### users

* id
* name
* email
* password_hash
* is_active
* created_at
* updated_at

### accounts

* id
* user_id
* name
* type
* currency
* opening_balance
* current_balance
* is_active
* created_at
* updated_at

### categories

* id
* user_id
* name
* type
* is_active
* created_at
* updated_at

### transactions

* id
* user_id
* account_id
* category_id nullable for transfer maybe
* type
* amount
* date
* note
* transfer_account_id nullable
* created_at
* updated_at

### budgets

* id
* user_id
* category_id
* month
* amount
* created_at
* updated_at

---

## 6. Exact business rules

Keep these fixed from start:

* every record belongs to a user
* account balance must always match transactions
* deleting or editing a transaction must recalculate balance safely
* transfer must not change net total wealth
* expense category cannot be used for income transaction
* income category cannot be used for expense transaction
* archived account/category cannot be used for new transaction

---

## 7. Exact non-functional MVP requirements

Must have:

* JWT auth
* pagination
* validation
* soft archive for accounts/categories
* clean error handling
* migrations
* basic tests
* seed default categories

Nice later, not now:

* Redis
* background jobs
* OCR
* AI
* bank integrations

---

## 8. Exact frontend state split

Use:

* **React Query** for API/server state
* **Zustand** for auth + UI filters only

Zustand store:

* user
* access token
* theme
* transaction filters UI

Do not store API lists in Zustand.

---

## 9. Exact MVP milestones

### Milestone 1

* auth
* db schema
* accounts
* categories

### Milestone 2

* transactions
* balance logic
* filters

### Milestone 3

* dashboard
* budgets
* reports

### Milestone 4

* polish
* validation
* tests
* deploy

---

## 10. What to skip now

Do not build yet:

* AI finance advice
* OCR bills
* family sharing
* admin panel
* bank sync
* subscriptions
* reminders
* investments
* multi-currency conversion
* SaaS billing
* RBAC

---

Best next step: **database schema first**.

techstack : **Tech stack (MVP scalable):**

**Frontend**

* React (Vite)
* TailwindCSS
* React Router
* React Query
* Zustand
* shadcn/ui

**Backend**

* FastAPI
* Python 3.11+
* SQLAlchemy / SQLModel
* Pydantic
* Alembic (migrations)
* JWT auth

**Database**

* PostgreSQL

**Cache (later)**

* Redis

**Async jobs (later)**

* Celery or Dramatiq

**Deploy**

* Frontend: Vercel
* Backend: VPS / Railway / Render
* DB: Managed PostgreSQL

