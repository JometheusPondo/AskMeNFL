# Ask Me NFL

A full-stack web application that lets you ask questions about NFL statistics in plain English and get back actual data. Built with FastAPI, React, and Google Gemini AI.

**Live:** [gridironstats.app](https://gridironstats.app)

## What It Does

Stop writing SQL queries. Just ask questions like "Who are the top 5 QBs by passing yards in 2024?" and get results. The app uses AI to convert your natural language into SQL, executes it against a 2.2GB database of NFL play-by-play data, and displays the results.

You can save queries, view your history, and download results as CSV. It works pretty much how you'd expect it to.

## Tech Stack

**Backend:**
- FastAPI (Python)
- SQLite (2 databases: NFL stats + users)
- Google Gemini 2.5 Pro (query generation)
- JWT authentication
- Bcrypt password hashing

**Frontend:**
- React 18
- Context API for state
- Custom CSS (dark theme)
- No UI libraries - just vanilla React

**Infrastructure:**
- Docker + Docker Compose
- AWS EC2 (Ubuntu)
- Cloudflare (DNS, SSL, CDN)
- Nginx (serving the frontend)

## Features

- Natural language query interface
- User authentication (register/login)
- Save and manage queries
- Download results as CSV
- Example queries to get started
- Shows generated SQL (toggle on/off)
- Query timing metrics

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Google Gemini API key

### Setup

1. **Clone the repo:**
```bash
git clone <your-gitlab-url>
cd nfl-nli-query-backend
```

2. **Create environment file:**
```bash
# Create g-api.env
GEMINI_API_KEY=your_key_here
JWT_SECRET_KEY=your_secret_here
```

3. **Download the NFL database:**
```bash
# This takes 30-60 minutes and downloads ~2.2GB
python nfl-db-downloader.py
```

4. **Run with Docker Compose:**
```bash
docker-compose up --build
```

Backend: http://localhost:8000  
Frontend: http://localhost:3000  
API docs: http://localhost:8000/docs

### Development Without Docker

**Backend:**
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd nfl-query-frontend
npm install
npm start
```

## Project Structure

```
├── main.py                    # FastAPI app
├── Dockerfile                 # Backend container
├── docker-compose.yml         # Local dev
├── docker-compose.prod.yml    # Production
├── database/
│   ├── connection.py         # Base DB connection (inheritance)
│   └── userDB.py             # User/query operations
├── services/
│   └── queryProcessor.py     # Main query logic
├── llm/
│   ├── provider.py           # Abstract LLM base (polymorphism)
│   └── geminiProvider.py     # Gemini implementation
├── models/
│   ├── user.py               # User model
│   └── savedQuery.py         # Query model
├── utils/
│   ├── jwt.py                # Token handling
│   ├── password.py           # Password hashing
│   └── authDependencies.py   # Auth middleware
└── nfl-query-frontend/
    ├── src/
    │   ├── App.js            # Main component
    │   ├── contexts/
    │   │   └── authContext.js
    │   └── components/
    │       ├── login.js
    │       ├── register.js
    │       └── savedQueries.js
    ├── Dockerfile
    └── nginx.conf
```

## Deployment

Deployed on AWS EC2 (t3.medium, 8GB RAM) running Ubuntu with Docker.

**Quick deploy:**
```bash
# SSH into EC2
ssh ubuntu@<your-ip>

# Pull latest
cd ~/AskMeNFL
git pull

# Rebuild and restart
sudo docker-compose -f docker-compose.prod.yml build
sudo docker-compose -f docker-compose.prod.yml up -d

# Check logs
sudo docker logs -f nfl-backend-prod
```

**First-time setup on EC2:**
- Install Docker
- Clone repo
- Set up environment variables
- Run `docker-compose -f docker-compose.prod.yml up -d`
- Point domain to EC2 IP
- Configure Cloudflare (SSL in Flexible mode)

The database downloads automatically on first run (takes ~1 hour).

## OOP Design

Built with proper object-oriented principles for my WGU capstone:

**Inheritance:**
- `QueryProcessor` extends `DatabaseConnection`

**Polymorphism:**
- `LLMProvider` abstract base class
- `GeminiProvider` concrete implementation
- Easy to swap AI providers without touching core logic

**Encapsulation:**
- Private attributes with `_` prefix
- Property decorators for controlled access
- Separation of concerns across services

## API Endpoints

**Public:**
- `GET /` - Root info
- `GET /health` - Health check
- `GET /status` - Database status
- `GET /examples` - Example queries
- `GET /models` - Available AI models

**Auth Required:**
- `POST /query` - Execute natural language query
- `GET /queries` - Get user's saved queries
- `POST /queries/save` - Save a query
- `PUT /queries/{id}` - Update query name
- `DELETE /queries/{id}` - Delete query

**Authentication:**
- `POST /auth/register` - Create account
- `POST /auth/login` - Get JWT token
- `GET /auth/profile` - Get user info
- `PUT /auth/profile` - Update profile
- `DELETE /auth/account` - Delete account

## Database Schema

**NFL Stats Database (2.2GB):**
- `plays` - Play-by-play data (1999-2024)
- `weekly_stats` - Player weekly stats
- `seasonal_stats` - Season aggregates
- `ngs_passing/rushing/receiving` - Next Gen Stats
- `schedules`, `draft_picks`, `combine_results`

**Users Database:**
- `users` - User accounts (hashed passwords)
- `saved_queries` - User query history

## Security Features

- JWT token authentication
- Bcrypt password hashing (12 rounds)
- Parameterized SQL queries (prevents injection)
- CORS configured for specific origins
- Environment variables for secrets
- Protected API routes

## Known Issues / Future Improvements

- First query after cold start is slow (~3-5 seconds) due to AI call
- No query result caching yet
- Could add more AI model options
- Mobile UI could use some work
- No email verification on signup (yet)

## Why This Tech Stack?

**FastAPI:** Fast, modern Python framework with automatic API docs. Easy to work with and deploy.

**React:** Straightforward frontend framework. No need to overcomplicate with Next.js or similar for this use case.

**SQLite:** Perfect for this dataset size. No need for Postgres complexity when SQLite works great.

**Gemini:** Better at SQL generation than GPT-4 in my testing. Plus it's cheaper.

**Docker:** Makes deployment consistent. No "works on my machine" issues.


## Credits

NFL data from [nfl_data_py](https://github.com/nflverse/nfl_data_py)

Built by Joseph Ahrens

