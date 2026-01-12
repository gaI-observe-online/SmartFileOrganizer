# Architecture Overview: SmartFileOrganizer with Web UI

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────┐         ┌─────────────────────────┐    │
│  │   Web Browser       │         │   Terminal (CLI)        │    │
│  │                     │         │                         │    │
│  │  React 18 + TypeScript       │  Click + Rich Console   │    │
│  │  Material-UI        │         │                         │    │
│  │  http://localhost:8001       │  python organize.py     │    │
│  └──────────┬──────────┘         └────────────┬────────────┘    │
│             │                                  │                  │
└─────────────┼──────────────────────────────────┼─────────────────┘
              │                                  │
              │ REST API + WebSocket             │ Direct calls
              ▼                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Application Layer                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │               FastAPI Backend (Port 8001)               │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │    │
│  │  │  Health  │  │   Scan   │  │  Files   │  │Settings│ │    │
│  │  │  Routes  │  │  Routes  │  │  Routes  │  │ Routes │ │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────┘ │    │
│  │                                                         │    │
│  │  ┌──────────────────────────────────────────────────┐ │    │
│  │  │         WebSocket Handler (Real-time)            │ │    │
│  │  └──────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                    │
│                              │ Calls                              │
│                              ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │         SmartFileOrganizer Core (Python)                │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │    │
│  │  │ Scanner  │  │Categorizer│ │   Risk   │  │Organizer│ │    │
│  │  │          │  │           │  │Assessor  │  │         │ │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────┘ │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                    │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Integration Layer                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────────┐   │
│  │   Ollama     │    │   SQLite     │    │  File System    │   │
│  │  (AI Models) │    │  (Audit DB)  │    │  (Content)      │   │
│  │              │    │              │    │                 │   │
│  │ llama3.3     │    │ audit.db     │    │ Files to scan   │   │
│  │ qwen2.5      │    │              │    │ Organized files │   │
│  └──────────────┘    └──────────────┘    └─────────────────┘   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Web UI Scan Flow

```
1. User Action (Web Browser)
   └─> Click "Start Scan" button
       └─> Input: /home/user/Downloads

2. HTTP Request
   └─> POST /api/scan/start
       └─> Body: { path: "/home/user/Downloads", recursive: true }

3. FastAPI Backend
   └─> Create scan ID (UUID)
   └─> Start background task
   └─> Return: { scan_id: "abc-123", status: "started" }

4. WebSocket Connection
   └─> Client connects: ws://localhost:8001/ws/scan/abc-123
   └─> Real-time updates every second:
       └─> { progress_percent: 45, current_file: "document.pdf" }

5. Core Processing
   └─> Scanner.scan_directory()
       └─> ContentExtractor.extract()
       └─> Categorizer.categorize()
       └─> RiskAssessor.assess()

6. AI Integration
   └─> OllamaProvider.categorize()
       └─> HTTP to http://localhost:11434
       └─> Model: llama3.3 or qwen2.5

7. Database Storage
   └─> Database.insert_scan()
   └─> AuditTrail.log()
   └─> SQLite: ~/.organizer/audit.db

8. WebSocket Update (Complete)
   └─> { type: "complete", status: "completed" }
   └─> Client displays results
```

### CLI Scan Flow

```
1. User Command
   └─> python organize.py scan ~/Downloads

2. Click CLI
   └─> cli.scan() function
       └─> Direct Python call (no HTTP)

3. Core Processing (Same as Web)
   └─> Scanner → Categorizer → Risk Assessor → Organizer

4. Terminal Output
   └─> Rich Console formatting
   └─> Progress bars
   └─> Color-coded results
```

## Port Configuration Priority

```
┌─────────────────────────────────────────────────┐
│  Port 8001 Selection                            │
├─────────────────────────────────────────────────┤
│                                                 │
│  Priority (Highest to Lowest):                  │
│                                                 │
│  1. CLI Flag                                    │
│     smartfile serve --port 8002                 │
│                                                 │
│  2. Environment Variable                        │
│     SMARTFILE_PORT=8002                         │
│                                                 │
│  3. Config File                                 │
│     ~/.organizer/config.json                    │
│     { "web": { "port": 8002 } }                 │
│                                                 │
│  4. Default                                     │
│     8001                                        │
│                                                 │
│  Port Conflict Detection:                       │
│  ├─> Check if port available                    │
│  ├─> If occupied, suggest alternatives          │
│  └─> User can accept or specify custom          │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Technology Stack

### Backend (Python)

```
┌──────────────────────────────────────┐
│  FastAPI 0.109.0                     │
│  ├─> Web framework                   │
│  ├─> Async support                   │
│  └─> OpenAPI docs                    │
├──────────────────────────────────────┤
│  Uvicorn 0.27.0                      │
│  ├─> ASGI server                     │
│  ├─> WebSocket support               │
│  └─> Production-ready                │
├──────────────────────────────────────┤
│  Existing Core                       │
│  ├─> Click (CLI)                     │
│  ├─> Rich (Terminal UI)              │
│  ├─> Ollama (AI)                     │
│  └─> SQLite (Database)               │
└──────────────────────────────────────┘
```

### Frontend (Node.js)

```
┌──────────────────────────────────────┐
│  React 18.2.0                        │
│  ├─> Hooks                           │
│  ├─> TypeScript                      │
│  └─> JSX                             │
├──────────────────────────────────────┤
│  Material-UI 5.15.0                  │
│  ├─> Components                      │
│  ├─> Theme system                    │
│  └─> Responsive design               │
├──────────────────────────────────────┤
│  Vite 5.0.8                          │
│  ├─> Fast dev server                 │
│  ├─> Hot module reload               │
│  └─> Production build                │
├──────────────────────────────────────┤
│  Zustand 4.4.7                       │
│  ├─> State management                │
│  ├─> React hooks                     │
│  └─> Minimal boilerplate             │
└──────────────────────────────────────┘
```

## Component Architecture

### React Component Tree

```
App (Router)
├─> Layout
│   ├─> AppBar (Navigation)
│   ├─> Drawer (Sidebar)
│   └─> Main Content
│       ├─> Dashboard (Route: /)
│       │   ├─> System Health Card
│       │   ├─> Quick Actions Card
│       │   ├─> Categories List
│       │   └─> Recent Scans List
│       │
│       ├─> Scanner (Route: /scan)
│       │   ├─> Path Input
│       │   ├─> Scan Controls
│       │   └─> Progress Display
│       │       ├─> Progress Bar
│       │       ├─> Current File
│       │       └─> Statistics
│       │
│       ├─> Results (Route: /results)
│       │   ├─> Filter Controls
│       │   ├─> File Table
│       │   └─> Pagination
│       │
│       └─> Settings (Route: /settings)
│           ├─> AI Provider Config
│           ├─> Scan Preferences
│           └─> General Settings
```

## State Management

```
Zustand Store
├─> Theme State
│   ├─> darkMode: boolean
│   └─> toggleDarkMode()
│
├─> Settings State
│   ├─> settings: Settings | null
│   └─> setSettings(settings)
│
├─> Scan State
│   ├─> currentScan: ScanProgress | null
│   └─> setCurrentScan(scan)
│
└─> Notifications State
    ├─> notifications: Notification[]
    ├─> addNotification(type, message)
    └─> removeNotification(id)
```

## Security Model

```
┌─────────────────────────────────────────────────┐
│  Security Layers                                │
├─────────────────────────────────────────────────┤
│                                                 │
│  Network Layer                                  │
│  ├─> Bind to 127.0.0.1 (localhost only)        │
│  ├─> No public network exposure                │
│  └─> WebSocket on same origin                  │
│                                                 │
│  API Layer                                      │
│  ├─> CORS restricted to localhost              │
│  ├─> No authentication (single-user)           │
│  └─> Input validation                          │
│                                                 │
│  Application Layer                              │
│  ├─> Privacy-safe logging                      │
│  ├─> No external communication                 │
│  └─> Local AI processing only                  │
│                                                 │
│  Future Enhancements                            │
│  ├─> JWT authentication                        │
│  ├─> HTTPS support                             │
│  ├─> Rate limiting                             │
│  └─> CSRF protection                           │
│                                                 │
└─────────────────────────────────────────────────┘
```

## File Organization

```
SmartFileOrganizer/
├── src/
│   ├── api/                      # NEW: Web API
│   │   ├── main.py              # FastAPI app
│   │   ├── routes/              # API endpoints
│   │   │   ├── health.py        # Health checks
│   │   │   ├── scan.py          # Scan operations
│   │   │   ├── files.py         # File listing
│   │   │   └── settings.py      # Settings CRUD
│   │   └── websocket.py         # Real-time updates
│   │
│   ├── web/                      # NEW: React UI
│   │   ├── src/
│   │   │   ├── components/      # React components
│   │   │   ├── api/client.ts    # API client
│   │   │   └── utils/store.ts   # State management
│   │   ├── package.json         # Node dependencies
│   │   └── vite.config.ts       # Build config
│   │
│   └── smartfile/                # EXISTING: Core
│       ├── cli/main.py          # CLI (+ serve cmd)
│       ├── core/                # Core logic
│       ├── analysis/            # Scanners
│       ├── ai/                  # AI providers
│       └── utils/               # Utilities
│
├── tests/
│   └── api/                      # NEW: API tests
│       └── test_endpoints.py    # Endpoint tests
│
├── docs/
│   ├── WEB_UI.md                # NEW: Web UI docs
│   └── INSTALLATION.md          # Updated
│
└── requirements.txt              # Updated with web deps
```

## Deployment Scenarios

### Development Mode

```
Terminal 1: Backend
$ smartfile serve
INFO: Uvicorn running on http://127.0.0.1:8001

Terminal 2: Frontend Dev Server
$ cd src/web && npm run dev
VITE ready in 500ms
➜  Local:   http://localhost:3000
```

### Production Mode

```
1. Build Frontend
$ cd src/web
$ npm run build
✓ build complete in 5.2s

2. Start Server (serves built UI)
$ smartfile serve
INFO: Uvicorn running on http://127.0.0.1:8001
INFO: Serving static files from src/web/dist
```

### Docker Mode (Future)

```
$ docker-compose up
Creating smartfile-web...
Creating smartfile-api...
Both services running on http://localhost:8001
```

## Performance Characteristics

```
┌─────────────────────────────────────────────────┐
│  Performance Metrics                            │
├─────────────────────────────────────────────────┤
│                                                 │
│  Backend (Python + FastAPI)                     │
│  ├─> Startup time: ~2 seconds                  │
│  ├─> API response: <100ms avg                  │
│  ├─> WebSocket latency: <50ms                  │
│  └─> Memory: ~50MB                             │
│                                                 │
│  Frontend (React SPA)                           │
│  ├─> Initial load: ~2 seconds                  │
│  ├─> Bundle size: ~500KB (gzipped)             │
│  ├─> Time to Interactive: <3s                  │
│  └─> Lighthouse score: 90+ target              │
│                                                 │
│  Database (SQLite)                              │
│  ├─> Query time: <10ms                         │
│  ├─> Write time: <20ms                         │
│  └─> Concurrent reads: Yes                     │
│                                                 │
│  AI Processing (Ollama)                         │
│  ├─> Categorization: 100-500ms/file            │
│  ├─> Model load: ~5 seconds (first use)        │
│  └─> Concurrent requests: 1-4 (GPU dependent)  │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Error Handling

```
Frontend Error Handling
├─> Network Errors
│   └─> Retry logic (3 attempts)
│   └─> Fallback to polling
│   └─> User notification
│
├─> API Errors
│   └─> HTTP status codes
│   └─> Error messages displayed
│   └─> Suggested actions
│
└─> WebSocket Errors
    └─> Auto-reconnect
    └─> Fallback to HTTP polling
    └─> Connection status indicator

Backend Error Handling
├─> Validation Errors
│   └─> 400 Bad Request
│   └─> Detailed error message
│
├─> Not Found
│   └─> 404 Not Found
│   └─> Resource identifier
│
└─> Server Errors
    └─> 500 Internal Server Error
    └─> Logged for debugging
```

---

**Architecture designed for:**
- Simplicity
- Performance
- Privacy
- Extensibility
- User-friendliness
