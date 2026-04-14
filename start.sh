#!/bin/bash
# Quick start script for AIOA Personal Finance Manager

echo "🚀 AIOA Personal Finance Manager - Quick Start"
echo "=============================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo "⚠️  Please update the .env file with your configuration"
    echo ""
fi

# Check if virtual environment exists
if [ ! -d .venv ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo ""
echo "🗄️  Database Setup"
echo "-----------------"
echo "Make sure PostgreSQL is running and database 'finance_db' exists"
echo "If not, run:"
echo "  createdb finance_db"
echo ""

# Run migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Seed database
echo "🌱 Seeding database with demo data..."
python scripts/seed.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 To start the server, run:"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "📚 API Documentation will be available at:"
echo "   http://localhost:8000/docs"
echo ""
echo "🔑 Demo credentials:"
echo "   Email: demo@example.com"
echo "   Password: demopassword"
echo ""
