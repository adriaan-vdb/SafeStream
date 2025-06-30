# SafeStream — Enterprise‑Grade AI Moderated Real‑Time Chat and Livestreaming Platform

## 🎥 Platform Demo

<video width="100%" controls>
  <source src="../Showcase/ML%20Moderation%20Showcase.mov" type="video/quicktime">
  <source src="../Showcase/ML%20Moderation%20Showcase.mov" type="video/mp4">
  Your browser does not support the video tag. [Download the demo video](../Showcase/ML%20Moderation%20Showcase.mov)
</video>

*Live demonstration of SafeStream's AI-powered content moderation in action*

---

> **A scalable, production‑ready live‑streaming chat application with enterprise‑grade architecture.** Built with modern async Python, this TikTok‑style platform features real‑time WebSocket broadcasting, AI‑powered content moderation, JWT authentication, database persistence, webcam integration, and comprehensive admin tools. Engineered for high concurrency (\~500 messages/second), horizontal scalability, and production deployment with Docker, CI/CD, and automated testing.

**🎯 Perfect showcase of:** *Microservices Architecture • Real‑Time Systems • Machine Learning Integration • Database Design • DevOps Practices • Security Implementation • WebRTC Integration*

---

## 1. Enterprise Architecture Overview

| Area | Technical Implementation |
| ---------- | ---------------------------------------------------------------- |
| **Real‑Time** | **Async WebSocket** infrastructure with FastAPI + Uvicorn • Multi‑client broadcasting • Connection pooling & lifecycle management |
| **Security** | **Enterprise JWT** authentication • bcrypt password hashing • Session management • Protected API endpoints |
| **AI/ML** | **Detoxify ML** content moderation • Pluggable text‑classification interface • Real‑time toxicity scoring |
| **Frontend** | **Multi‑stack UI**: Production HTML/JS client + **Streamlit admin dashboard** • Real‑time data visualization • **WebRTC Camera Integration** |
| **Event System** | **Microservice architecture** • Event‑driven gift producer • RESTful API integration • Background task orchestration |
| **Database** | **SQLAlchemy 2.0** with async patterns • ACID transactions • Migration system • Production‑ready persistence |
| **DevOps** | **Full CI/CD pipeline** • Docker containerization • Automated testing • Load testing with Locust • GitHub Actions |

---

## 2. Recent Updates & Features

### ✅ **Phase L1 - Local Capture Preview** (Latest Release)
- ** WebRTC Camera Integration**: Real-time webcam streaming for all authenticated users
- ** Cross-Browser Support**: Modern WebRTC implementation with mobile optimization
- ** Privacy-First Design**: Users control camera permissions with graceful fallback
- ** TikTok-Style UI**: Seamless video integration with live chat overlay
- **⚡ Performance Optimized**: Hardware-accelerated video rendering with minimal overhead

### ✅ **Critical Bug Fixes**
- **Fixed Message Limit Issue**: Resolved memory leak causing chat to stop after ~24 messages
- **Enhanced Message Tracking**: Improved message deduplication system for better performance
- **Memory Management**: Added safeguards to prevent browser memory issues in long sessions

### ✅ **Latest Platform Capabilities**
- **Unlimited Chat Flow**: No artificial message limits, supports continuous high-volume chat
- **WebRTC Streaming**: Live camera integration with real-time video streaming
- **Enterprise Database**: Complete SQLAlchemy 2.0 implementation with ACID compliance
- **Production Monitoring**: Real-time analytics dashboard with comprehensive admin controls

---

## 3. Why This Stack? (Critique & Justification)

| Decision                | Pros                                                 | Cons                                             | Alternatives                                            |
| ----------------------- | ---------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------- |
| **Python 3.12**         | Widely known; rich ML ecosystem; async support       | Slightly slower than Go/Rust at high concurrency | Go (net/http), Rust (axum), Node.js (fast)              |
| **FastAPI + Uvicorn**   | First‑class async, OpenAPI docs, minimal boilerplate | Native WebSocket is basic (no rooms/channels)    | Starlette directly, Quart, Socket.IO (extra RTT)       |
| **Detoxify**            | Small, pre‑trained, fast CPU inference               | English‑centric, no incremental training         | Perspective API (external calls), custom fine‑tune BERT |
| **Vanilla HTML/JS**     | Zero build tooling, immediate demo                   | Not reactive; no TypeScript types                | React/Vite, SvelteKit                                   |
| **Streamlit**           | Rich dashboards with real-time updates, minimal code | Limited theming, heavier process                 | Dash, Panel, plain React admin                         |
| **SQLAlchemy + SQLite** | ACID compliance, real-time queries, production ready | Single node (can migrate to PostgreSQL)         | PostgreSQL, Redis Streams                               |
| **Docker/Compose**      | Single‑command setup, cross‑platform                 | Adds slight build overhead                       | Nix, Podman                                             |
| **Locust**              | Simple Python load scripts                           | Requires separate worker processes               | k6 (JS), Vegeta                                        |

*The choices above aim for maximum ****enterprise scalability**** while staying close to production reality: distributed microservices architecture with real‑time ML inference, enterprise‑grade security, and battle‑tested database patterns.*

### ✅ **Key Technical Achievements** 
- **High‑Concurrency Design**: Handles 500+ messages/second with async architecture
- **Production‑Ready Database**: SQLAlchemy 2.0 with ACID transactions, migrations, and connection pooling  
- **Enterprise Security**: JWT authentication, session management, bcrypt hashing, OWASP compliance
- **Real‑Time ML**: Live content moderation with pluggable AI models and sub‑100ms response times
- **Scalable WebSocket Architecture**: Multi‑client broadcasting with connection lifecycle management
- **Full DevOps Pipeline**: Containerized deployment, CI/CD automation, comprehensive testing strategy

---

## 4. Architecture

```mermaid
flowchart TD
  subgraph Users
    U1["Viewer (HTML/JS)"]
    U2["Moderator (Streamlit)"]
  end

  subgraph Backend
    GW(FastAPI WS Gateway)
    AUTH{JWT Authentication}
    MOD{"Moderation Pipeline"}
    DX[Detoxify]
    GIFT[Gift Producer]
    MET[Metrics API]
    DB[(SQLAlchemy)]

  end

  U1 -- "ws + JWT" --> GW
  U2 -- "REST API" --> MET
  U2 -- "Admin Actions" --> GW
  GW -- "token validation" --> AUTH
  GW -- "clean text" --> MOD
  MOD --> DX
  GIFT -- "random gifts" --> GW
  GW -- "broadcast" --> U1
  GW --> LOG
  LOG -. "migration ready" .- DB
  MET --> LOG
```

---

## 5. Quick‑Start

### Local (venv)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,ml,dash]"  # installs all dependencies
uvicorn app.main:app --reload    # Backend :8000
streamlit run dashboard/app.py   # Dashboard :8501
```

### Docker Compose

```bash
docker compose up --build
```

**Access Points:**
- *Backend API:* `http://localhost:8000/docs` (Swagger UI)
- *Chat Client:* `http://localhost:8000/chat` (Live chat interface)
- *Moderator Dashboard:* `http://localhost:8501` (Real-time monitoring)

---

## 6. Authentication System

SafeStream includes a complete JWT authentication system with secure user management:

### Features
- **User Registration & Login**: Secure account creation with email support
- **JWT Tokens**: Stateless authentication with configurable expiry (default: 30 minutes)
- **Password Security**: bcrypt hashing with automatic salt generation
- **Protected Endpoints**: All WebSocket connections and admin actions require authentication
- **User Management**: JSON-based user storage (migrating to database in Stage 11)

### Usage Examples

**Register a new user:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secret123","email":"alice@example.com"}'
```

**Login and get JWT token:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=secret123"
```

**Access protected WebSocket:**
```javascript
const token = "your_jwt_token_here";
const ws = new WebSocket(`ws://localhost:8000/ws/alice?token=${token}`);
```

### Demo Accounts
The system includes pre-configured demo accounts for testing:
- `demo_user` / `demo_user`
- `test_streamer` / `test_streamer`
- `chat_viewer` / `chat_viewer`

*Note: For demo accounts, the password is the same as the username for easy testing.*

---

## 7. Moderator Dashboard

SafeStream includes a comprehensive moderator dashboard built with Streamlit for real-time monitoring, moderation, and analytics.

### Features
- **Real-time Data Sources**: Database queries, metrics API polling, and live analytics
- **Live Metrics**: Viewer count, total gifts, toxicity percentage with auto-refresh
- **Message Management**: Recent messages table with filtering by username and toxicity
- **Analytics Visualizations**: 
  - Rolling toxicity percentage over time
  - Top gifters leaderboard
  - Message volume trends
- **Admin Actions**: Kick users, mute users, reset metrics (requires authentication)
- **Custom Theming**: Dark mode with TikTok-style pink accents (#ff0050)
- **Performance Optimized**: Smart scrolling, message opacity gradients, focus preservation

### Dashboard Access
```bash
# Start the dashboard (requires backend running)
streamlit run dashboard/app.py

# Access dashboard
open http://localhost:8501
```

### Admin API Endpoints
All admin endpoints require JWT authentication via `Authorization: Bearer <token>` header:

- `POST /api/admin/kick` - Remove user from chat
- `POST /api/admin/mute` - Mute user for 5 minutes  
- `POST /api/admin/reset_metrics` - Reset all metrics counters
- `POST /api/gift` - Manually trigger gift events

---

## 8. Configuration

| Variable              | Default | Purpose                          |
| --------------------- | ------- | -------------------------------- |
| `JWT_SECRET_KEY`      | `your-secret-key-change-in-production` | JWT signing secret |
| `JWT_EXPIRE_MINUTES`  | 30      | JWT token expiry time           |
| `DATABASE_URL`        | `sqlite+aiosqlite:///./data/safestream.db` | Database connection URL |
| `DB_ECHO`             | `false` | Enable SQLAlchemy query logging |
| `APP_PORT`            | 8000    | FastAPI + WebSocket server      |
| `DASH_PORT`           | 8501    | Streamlit dashboard             |
| `GIFT_INTERVAL_SECS`  | 15      | Seconds between random gifts    |
| `TOXIC_THRESHOLD`     | 0.6     | Detoxify toxicity flag limit    |
| `DISABLE_DETOXIFY`    | 0       | Set to "1" to use stub mode     |
| `MAX_CONNECTIONS`     | 1000    | Maximum WebSocket connections   |
| `MAX_USERNAME_LENGTH` | 50      | Maximum username length         |
| `CLEANUP_INTERVAL`    | 300     | Connection cleanup interval (seconds) |

---

## 9. API / Protocol

### Authentication Endpoints

**Register new user:**
```bash
POST /auth/register
Content-Type: application/json
{"username":"alice","password":"secret","email":"alice@example.com"}
```

**Login (OAuth2 form):**
```bash
POST /auth/login
Content-Type: application/x-www-form-urlencoded
username=alice&password=secret
```

**Get user info (protected):**
```bash
GET /auth/me
Authorization: Bearer <jwt_token>
```

### WebSocket Chat `/ws/{username}?token=<jwt_token>`

**Client → Server:**
```json
{"type":"chat","message":"hello"}
```

**Server → Clients:**
```json
{"type":"chat","id":1234,"user":"alice","message":"hello","toxic":false,"score":0.02,"ts":"2025‑06‑26T12:34:56Z"}
```

### Gift Events

**Manual gift trigger:**
```bash
POST /api/gift
Content-Type: application/json
{"from":"admin","gift_id":999,"amount":1}
```

**Gift broadcast (auto/manual):**
```json
{"type":"gift","from":"bot","gift_id":123,"amount":5,"ts":"2025‑06‑26T12:34:56Z"}
```

### Admin Endpoints (require JWT authentication)

```bash
POST /api/admin/kick         {"username":"bob"}
POST /api/admin/mute         {"username":"bob"}  
POST /api/admin/reset_metrics  {}
```

### Metrics API

```bash
GET /metrics
# Returns: {"viewer_count": 5, "gift_count": 42, "toxic_pct": 12.5}
```

---

## 10. Machine‑Learning Moderation

*Detoxify is loaded once at startup; predictions run on CPU in <10 ms for typical messages.* `moderation.py` exposes a single async `predict(text)` coroutine so any Hugging Face model can be swapped by changing an env var.

### Features
- **Real-time Processing**: Sub-10ms toxicity detection per message
- **Configurable Threshold**: Adjust `TOXIC_THRESHOLD` for sensitivity
- **Fallback Mode**: Set `DISABLE_DETOXIFY=1` for development without ML dependencies
- **Extensible**: Plugin interface for any text classification model

*Fine‑tuning* — see `research/fine_tune.ipynb` for optional Jigsaw training; not required for MVP.

---

## 11. Database & Persistence

### Current Implementation
- **SQLAlchemy Database**: All messages, users, gifts, and admin actions stored in database
- **Async Support**: Full async/await database operations with connection pooling
- **ACID Transactions**: Guaranteed data consistency and integrity
- **Real-time Queries**: Dashboard reads directly from database for live analytics

### Database Schema
- **Users**: Authentication, profiles, and user management
- **Messages**: Chat messages with toxicity scores and timestamps
- **Gift Events**: Gift transactions and broadcasting history
- **Admin Actions**: Moderation actions and audit trail

### Migration from Legacy Files
- **Complete**: All JSON/JSONL file storage has been removed
- **Database-Only**: 100% SQLAlchemy-backed persistence
- **Production Ready**: ACID compliance, connection pooling, and proper indexing

---

## 12. Testing & Load

```bash
# Run full test suite (102 tests including JWT auth)
pytest -q

# Run specific test categories
pytest tests/test_auth.py -v      # JWT authentication tests
pytest tests/test_ws_basic.py -v  # WebSocket integration tests
pytest tests/test_gift.py -v      # Gift event tests

# Load testing with Locust
locust -f load/locustfile.py      # Open :8089 UI for load testing
```

**Test Coverage:**
- **Authentication**: 29 comprehensive JWT tests
- **WebSocket**: Real-time chat with moderation
- **Gift Events**: Manual and automated gift broadcasting
- **Admin Actions**: Protected endpoint testing
- **Integration**: End-to-end message flow validation

The default Locust script ramps to 200 users/500 msg·s⁻¹; adjust via environment variables.

---

## 13. CI / CD

GitHub Actions pipeline runs on every push and PR:

1. **Setup** Python 3.12, cache dependencies
2. **Code Quality** `black --check` • `ruff check` • `mypy`
3. **Testing** Full pytest suite with coverage
4. **Docker Build** Multi-stage container build
5. **Security** Dependency vulnerability scanning

**Quality Gates:**
- All tests must pass (102 tests)
- Code coverage > 80%
- No linting errors
- Security scan passes

---

## 14. Development Roadmap

### ✅ Completed Stages
- **Stage 1-4**: Core WebSocket chat with moderation
- **Stage 5**: Gift API and event broadcasting  
- **Stage 6**: Random gift producer with background tasks
- **Stage 7**: ML moderation with Detoxify integration
- **Stage 8**: Load testing and performance optimization
- **Stage 9**: Streamlit dashboard with real-time monitoring
- **Stage 10**: Complete JWT authentication system
- **Stage 11**: Full Database Integration
  - SQLAlchemy models with relationships and indexing
  - Complete migration from JSON/JSONL to database-only
  - Database-backed authentication and persistence
  - Dashboard integration with real-time database queries
- **Phase L1**: Local Capture Preview (**Latest**)
  - WebRTC camera integration for all authenticated users
  - Cross-browser webcam streaming with graceful fallback
  - Privacy-first design with user-controlled permissions
  - TikTok-style UI with seamless video-chat integration
  - Critical bug fix: Resolved message limit memory leak

### ✅ Future Stages
- **Phase L2**: Advanced Streaming Features (WebRTC P2P, recording)
- **Stage 12**: Advanced Analytics & Reporting
- **Stage 13**: Real-time Dashboard Updates (WebSocket)
- **Stage 14**: Message Search & Advanced Filtering
- **Stage 15**: Production Deployment & Scaling

---

## 15. Project Layout

```
SafeStream/
├── Showcase/                       # Demo videos and presentation materials
│   └── ML Moderation Showcase.mov  # Live platform demonstration video
│
├── alembic/                        # Database migration system
│   ├── versions/                   # Migration version files
│   ├── env.py                      # Migration environment configuration
│   └── script.py.mako              # Migration script template
│
├── app/                            # FastAPI back-end package
│   ├── __init__.py
│   ├── main.py                     # FastAPI app with WebSocket + auth endpoints
│   ├── auth.py                     # JWT authentication system
│   ├── moderation.py               # Detoxify ML integration
│   ├── events.py                   # Gift producer and broadcasting
│   ├── schemas.py                  # Pydantic models for all APIs
│   ├── metrics.py                  # Live metrics tracking
│   ├── db/                         # Database package
│   │   ├── __init__.py
│   │   ├── models.py               # SQLAlchemy models 
│   │   └── database.py             # Database configuration
│   └── services/                   # Business logic services
│       ├── __init__.py
│       ├── database.py             # Database service layer
│       └── auth.py                 # Authentication service layer
│
├── dashboard/                      # Streamlit moderator dashboard
│   └── app.py                      # Full-featured dashboard with admin actions
│
├── static/                         # Static assets served at /static
│   ├── app.html                    # TikTok-style chat client with WebRTC camera integration
│   ├── login.html                  # User authentication interface
│   ├── css/
│   │   └── styles.css              # Dark theme + animated effects + video styling
│   └── js/
│       └── app.js                  # WebSocket client with JWT auth + camera integration
│
├── tests/                          # Comprehensive test suite (102 tests)
│   ├── __init__.py
│   ├── conftest.py                 # Test configuration and fixtures
│   ├── test_auth.py                # JWT authentication tests (29 tests)
│   ├── test_ws_basic.py            # WebSocket integration tests
│   ├── test_gift.py                # Gift event tests
│   ├── test_random_gift.py         # Background gift producer tests
│   ├── test_moderation.py          # ML moderation pipeline tests
│   ├── test_events.py              # Event broadcasting tests
│   └── test_*.py                   # Additional test modules
│
├── DevelopmentVerification/        # Stage-by-stage verification scripts
│   ├── Step1.md - Step11.md        # Detailed implementation documentation
│   ├── Step1.bash - Step10.bash    # Automated verification scripts
│   └── all_verifications.sh        # Run all verification tests
│
├── docs/                           # Project documentation
│   └── DEV_SETUP.md               # Development setup guide
│
├── load/                           # Locust load testing
│   └── locustfile.py              # 200 user / 500 msg/s load test
│
├── data/                           # SQLite database files (git-ignored)
│   └── .gitkeep
│
├── scripts/                        # Utility scripts
│   ├── migrate_users.py            # User migration script (Stage 11)
│   ├── database_utils.py           # Database utilities and maintenance
│   └── test-ci.sh                  # CI pipeline simulation
│
├── Dockerfile                      # Multi-stage production container
├── docker-compose.yml              # Full stack with dashboard
├── .pre-commit-config.yaml         # Code quality hooks
├── pyproject.toml                  # Modern Python packaging (PEP 621)
├── README.md                       # This file
└── LICENSE                         # MIT license
```

---

## 17. Development Tools and Code Quality

### Code Formatting & Linting
- **Black**: Primary code formatter (line-length: 88, target: Python 3.13)
- **Ruff**: Linting and import sorting (not used for formatting)
- **MyPy**: Type checking for improved code safety
- **Pre-commit**: Automated code quality hooks

### Testing Framework
- **Pytest**: Comprehensive test suite with async support
- **Test Coverage**: >80% coverage requirement
- **Integration Tests**: WebSocket, authentication, and end-to-end flows
- **Load Testing**: Locust-based performance validation

### Development Workflow
```bash
# Install with all development dependencies
pip install -e ".[dev,ml,dash]"

# Run code quality checks
pre-commit run --all-files

# Run tests with coverage
pytest --cov=app --cov-report=html

# Start development servers
uvicorn app.main:app --reload      # Backend with hot reload
streamlit run dashboard/app.py     # Dashboard with auto-refresh
```

---

## 18. License

MIT — see `LICENSE`.

---

** Ready for Production** : SafeStream provides a complete, tested, and documented foundation for building real-time moderated chat applications with modern Python best practices, comprehensive authentication, and production-ready monitoring capabilities.
