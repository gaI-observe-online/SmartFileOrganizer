# SmartFileOrganizer Web UI - Quick Start Guide

## 🌐 What's New: Web Interface

SmartFileOrganizer now includes a modern, consumer-grade web interface! No more CLI-only experience - manage your files through an intuitive dashboard.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies (includes web server)
pip install -r requirements.txt
```

### 2. Start the Web Server

```bash
# Start on default port 8001
smartfile serve

# Or with custom port
smartfile serve --port 8002
```

### 3. Open Your Browser

Navigate to: `http://localhost:8001`

## ✨ Features

### Dashboard
- System health monitoring
- Recent scans overview
- Category breakdown
- Quick actions

### Scanner
- Interactive directory selection
- Real-time progress updates via WebSocket
- Visual progress bars
- Pause/cancel controls

### Results
- Filterable file listings
- Risk level indicators
- Category-based organization
- Sortable columns

### Settings
- AI provider configuration
- Auto-approve threshold adjustment
- Help URL customization
- Dark/light mode toggle

## 🔧 Configuration

### Port Configuration

**Priority (highest to lowest):**

1. CLI flag: `--port 8002`
2. Environment variable: `SMARTFILE_PORT=8002`
3. Config file: `~/.organizer/config.json`
4. Default: `8001`

### Config File

Edit `~/.organizer/config.json`:

```json
{
  "web": {
    "port": 8001,
    "host": "127.0.0.1",
    "auto_open_browser": true
  }
}
```

### Port Conflicts

If port 8001 is in use, the CLI will:
- Detect the conflict
- Suggest alternative ports (8002, 8003, 8080)
- Offer to use an alternative automatically

```bash
❌ Error: Port 8001 is already in use

💡 Suggested actions:
  • Try port 8002: smartfile serve --port 8002
  • Stop the service using port 8001

🔍 Detecting available ports... Found: 8002, 8003, 8080
```

## 📚 Documentation

- **[Web UI Guide](docs/WEB_UI.md)** - Complete web interface documentation
- **[Installation](docs/INSTALLATION.md)** - Installation instructions
- **[Configuration](docs/CONFIGURATION.md)** - Configuration reference

## 🏗️ Architecture

### Backend (Python + FastAPI)
- **Port**: 8001 (default)
- **API Base**: `/api`
- **WebSocket**: `/ws`

**Key Endpoints:**
```
GET  /api/health        - System health check
GET  /api/status        - AI provider status
POST /api/scan/start    - Start new scan
GET  /api/scan/{id}     - Get scan progress
WS   /ws/scan/{id}      - Real-time updates
```

### Frontend (React + TypeScript)
- **Framework**: React 18
- **UI Library**: Material-UI
- **State**: Zustand
- **Build**: Vite

## 🧪 Testing

```bash
# Test API endpoints
pytest tests/api/test_endpoints.py -v

# All tests should pass
# ✓ 6 passed in 0.49s
```

## 🔒 Security

- **Local-only by default**: Binds to `127.0.0.1`
- **CORS configured**: Only localhost origins allowed
- **No authentication required**: For single-user local use
- **Privacy-first**: All processing remains local

## 🛠️ Development

### Building the Web UI

```bash
cd src/web
npm install
npm run build
```

### Development Mode

```bash
# Terminal 1: Backend
smartfile serve

# Terminal 2: Frontend (with hot-reload)
cd src/web
npm run dev
```

Frontend dev server: `http://localhost:3000` (proxies to backend at 8001)

## 📊 Screenshots

### Dashboard
![Dashboard](https://via.placeholder.com/800x500?text=Dashboard+%E2%80%94+System+Health+%26+Quick+Actions)

### Scanner
![Scanner](https://via.placeholder.com/800x500?text=Scanner+%E2%80%94+Real-time+Progress+Tracking)

### Results
![Results](https://via.placeholder.com/800x500?text=Results+%E2%80%94+Filterable+File+Listings)

## 🐛 Troubleshooting

### "Web UI not built" Error

```bash
cd src/web
npm install
npm run build
```

### Port Conflict

```bash
# Use different port
smartfile serve --port 8002

# Or find what's using the port
lsof -i :8001  # Linux/Mac
netstat -ano | findstr :8001  # Windows
```

### WebSocket Connection Failed

1. Check backend is running
2. Verify no firewall blocking WebSocket
3. Check browser console for errors
4. Fallback polling will activate automatically

## 🎯 Next Steps

1. **Start the server**: `smartfile serve`
2. **Open browser**: `http://localhost:8001`
3. **Scan a directory**: Use the Scanner interface
4. **View results**: Check the Results page
5. **Configure settings**: Adjust AI provider settings

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Made with ❤️ for privacy-conscious file organization**
