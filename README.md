# Blockchain AI LMS - Quick Start Guide

A Django-based Learning Management System with blockchain integration, AI-powered chatbot, and token-gated course access.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git

### Option 1: Local Development (Recommended)

Run services in Docker, Django locally for fast iteration.

#### 1. Clone and Setup

```powershell
git clone <repository-url>
cd blockchain-ai-lms
```

#### 2. Environment Configuration

```powershell
# Copy environment template
copy .env.example .env
# Edit .env with your settings (especially GOOGLE_API_KEY for AI features)
```

#### 3. Start Services

```powershell
# Start all required services (Postgres, Redis, Qdrant, Hardhat)
docker compose -f docker-compose.dev.yml up -d

# Verify services are running
docker compose -f docker-compose.dev.yml ps
```

#### 4. Setup Python Environment

```powershell
# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Optional: Install AI/ML packages for full functionality
# pip install torch sentence-transformers langchain langchain-google-genai qdrant-client
```

#### 5. Run Django

```powershell
# Run database migrations
python src/manage.py migrate

# Create superuser (optional)
python src/manage.py createsuperuser

# Start development server
python src/manage.py runserver 0.0.0.0:8000
```

#### 6. Start Celery (Optional, for background tasks)

```powershell
# In a new terminal (with .venv activated)
celery -A src worker -l info

# In another terminal for scheduled tasks
celery -A src beat -l info
```

### Option 2: Full Docker Setup

Everything runs in containers.

#### 1. Setup Environment

```powershell
# Copy and edit environment file
copy .env.example .env
# Edit .env - change DB_HOST to 'db' and service URLs to container names
```

#### 2. Run Full Stack

```powershell
# Build and start all services
docker compose up --build

# Or run in background
docker compose up -d --build
```

## 📋 Service Overview

| Service           | Port      | Purpose               | Local Dev    | Docker       |
| ----------------- | --------- | --------------------- | ------------ | ------------ |
| **Django API**    | 8000      | Main application      | ✅ Local     | 🐳 Container |
| **PostgreSQL**    | 5432      | Primary database      | 🐳 Container | 🐳 Container |
| **pgAdmin**       | 5050      | DB management UI      | 🐳 Container | 🐳 Container |
| **Redis**         | 6379      | Cache & Celery broker | 🐳 Container | 🐳 Container |
| **Qdrant**        | 6333/6334 | Vector DB for AI      | 🐳 Container | 🐳 Container |
| **Hardhat**       | 8545      | Local blockchain      | 🐳 Container | 🐳 Container |
| **Celery Worker** | -         | Background tasks      | ✅ Local     | 🐳 Container |

## 🔗 Access Points

- **Main App**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs/
- **Admin Panel**: http://localhost:8000/admin/
- **pgAdmin**: http://localhost:5050 (admin@local.com / admin)
- **Frontend Prototype**: http://localhost:8000/ (served by Django)

## 🧪 Testing

```powershell
# Run Django tests
python src/manage.py test

# Test specific service
python src/manage.py test src.services.auth_service

# Check service health
curl http://localhost:8000/api/v1/auth/
```

## 🎯 Key Features to Test

### 1. Authentication

- Register: http://localhost:8000/api/v1/auth/register/
- Login: http://localhost:8000/api/v1/auth/token/
- JWT tokens for API access

### 2. Blockchain Features

- Connect wallet (requires Hardhat node running)
- Token transactions
- Smart contract interactions

### 3. AI Chatbot

- Requires `GOOGLE_API_KEY` in .env
- Vector database (Qdrant) for RAG
- Context-aware responses about platform

### 4. Course Management

- Course CRUD operations
- Progress tracking
- Certificate generation

## 🛠 Development Workflow

### Local Development (Recommended)

1. Start services: `docker compose -f docker-compose.dev.yml up -d`
2. Activate venv: `.venv\Scripts\Activate.ps1`
3. Run Django: `python src/manage.py runserver`
4. Make changes and reload automatically

### Docker Development

1. Make changes to code
2. Rebuild: `docker compose up --build`
3. Slower iteration but matches production

## 🔧 Troubleshooting

### Common Issues

#### Port Conflicts

```powershell
# Check if ports are in use
netstat -an | findstr :5432
netstat -an | findstr :6379
netstat -an | findstr :8000

# Stop conflicting services or change ports in docker-compose
```

#### Database Connection

```powershell
# Test Postgres connection
python -c "import psycopg2; psycopg2.connect(host='localhost', port=5432, user='postgres', password='postgres', database='lms_db')"

# Reset database
docker compose -f docker-compose.dev.yml down
docker volume rm blockchain-ai-lms_postgres_data_dev
docker compose -f docker-compose.dev.yml up -d
```

#### AI Features Not Working

- Ensure `GOOGLE_API_KEY` is set in .env
- Install AI packages: `pip install torch sentence-transformers langchain-google-genai`
- Check Qdrant is running: `curl http://localhost:6333/health`

#### Hardhat/Blockchain Issues

```powershell
# Check Hardhat logs
docker logs lms-hardhat-dev

# Restart Hardhat
docker compose -f docker-compose.dev.yml restart hardhat
```

### Service Health Checks

```powershell
# Check all services
docker compose -f docker-compose.dev.yml ps

# Test individual services
curl http://localhost:5432  # Postgres (should connection refused but port open)
redis-cli -h localhost ping  # Redis
curl http://localhost:6333/health  # Qdrant
curl http://localhost:8545  # Hardhat (JSON-RPC)
```

## 📁 Project Structure

```
blockchain-ai-lms/
├── src/                     # Django project root
│   ├── config/             # Settings and main URLs
│   ├── services/           # Feature-based apps
│   │   ├── auth_service/   # Authentication
│   │   ├── chatbot_service/ # AI chatbot with RAG
│   │   ├── blockchain_service/ # Web3 integration
│   │   ├── courses_service/ # Course management
│   │   └── ...
│   ├── shared/             # Common utilities
│   └── users/              # User model
├── frontend-simple/        # Static frontend prototype
├── docs/                   # Documentation and RAG data
├── docker-compose.yml      # Full Docker setup
├── docker-compose.dev.yml  # Services-only setup
├── Dockerfile              # Django container
├── requirements.txt        # Python dependencies
└── .env.example           # Environment template
```

## 🚀 Next Steps

1. **Configure AI**: Add your `GOOGLE_API_KEY` to `.env` for chatbot functionality
2. **Explore APIs**: Visit http://localhost:8000/api/docs/ for interactive API documentation
3. **Test Blockchain**: Connect a wallet and test token transactions
4. **Create Content**: Add courses and test the full learning workflow
5. **Scale**: Move to production-ready setup with proper secrets management

## 📞 Support

- Check logs: `docker compose -f docker-compose.dev.yml logs <service>`
- Django debug: Set `DEBUG=True` in .env
- Reset everything: `docker compose -f docker-compose.dev.yml down -v`
