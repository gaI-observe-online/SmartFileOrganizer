# Web UI Documentation

## Overview

SmartFileOrganizer Web UI provides a modern, user-friendly interface for managing and organizing your files using AI. The web interface runs on **port 8001** by default and offers real-time scan progress, visual file management, and comprehensive settings control.

## Quick Start

### Starting the Web Server

```bash
# Using the CLI command
smartfile serve

# Or with custom port
smartfile serve --port 8002

# Or using environment variable
SMARTFILE_PORT=8002 smartfile serve
```

The web UI will automatically open in your browser at `http://localhost:8001`.

## Features

### 1. Dashboard

The dashboard provides an at-a-glance view of your system:

- **System Health**: Database status, AI provider connection, disk space, memory usage
- **Quick Actions**: Start new scan, view results, access settings
- **Categories**: Visual breakdown of files by category (documents, images, code, etc.)
- **Recent Scans**: History of recent scan operations

### 2. Scanner

Interactive file scanning interface with real-time progress:

- **Directory Selection**: Enter or browse to select scan directory
- **Real-time Progress**: Live updates via WebSocket
  - Current file being scanned
  - Progress percentage
  - Files processed count
  - Estimated time remaining
- **Scan Controls**:
  - Start: Begin new scan
  - Pause: Temporarily pause scanning
  - Cancel: Stop and cancel scan operation

**WebSocket Updates**: The scanner uses WebSocket connections for instant progress updates without polling.

### 3. Results

View and filter scanned files:

- **File List**: Table view of all scanned files
- **Filtering**:
  - By category (documents, images, code, videos, audio)
  - By risk level (low, medium, high)
- **Sortable Columns**: Name, category, size, risk, confidence
- **Pagination**: Navigate through large file sets
- **Risk Visualization**: Color-coded risk indicators
  - Green: Low risk (0-30)
  - Yellow: Medium risk (31-70)
  - Red: High risk (71-100)

### 4. Settings

Configure SmartFileOrganizer:

#### AI Provider Configuration
- **Ollama Endpoint**: URL of your Ollama instance (default: `http://localhost:11434`)
- **AI Model**: Model to use (llama3.3, qwen2.5, etc.)

#### Scan Preferences
- **Auto-Approve Threshold**: Risk score threshold for auto-approval (0-100)
  - Files below this score are automatically approved
  - Recommended: 30 for balanced security

#### General Settings
- **Database Path**: Location of audit database (read-only)
- **Server Port**: Current web server port (read-only)
- **Help Base URL**: Base URL for documentation links

### 5. Dark/Light Mode

Toggle between dark and light themes using the brightness icon in the top-right corner. Theme preference is saved in browser local storage.

## Port Configuration

SmartFileOrganizer uses **port 8001** by default to avoid conflicts with common services.

### Setting Custom Port

**Priority order** (highest to lowest):

1. **CLI Flag**: `smartfile serve --port 8002`
2. **Environment Variable**: `SMARTFILE_PORT=8002`
3. **Config File**: `~/.organizer/config.json`
4. **Default**: 8001

### Port Conflict Handling

If port 8001 is already in use:

```bash
❌ Error: Port 8001 is already in use

💡 Suggested actions:
  • Try port 8002: smartfile serve --port 8002
  • Stop the service using port 8001
  • Configure a custom port in settings

🔍 Detecting available ports... Found: 8002, 8003, 8080
```

The CLI will:
1. Detect the conflict
2. Suggest alternative available ports
3. Offer to use an alternative port automatically

### Configuring in config.json

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

## Architecture

### Backend (FastAPI)

- **Port**: 8001 (default)
- **API Base**: `/api`
- **WebSocket Base**: `/ws`

#### API Endpoints

```
GET  /api/health              - System health check
GET  /api/status              - AI provider status
POST /api/scan/start          - Start new scan
GET  /api/scan/{id}           - Get scan progress
POST /api/scan/{id}/pause     - Pause scan
POST /api/scan/{id}/cancel    - Cancel scan
GET  /api/scans               - List recent scans
GET  /api/files               - List scanned files
GET  /api/categories          - Get category stats
PUT  /api/settings            - Update settings
GET  /api/settings            - Get current settings
WS   /ws/scan/{id}            - WebSocket for live updates
POST /api/diagnostics/export  - Export diagnostic bundle
```

### Frontend (React)

- **Framework**: React 18 with TypeScript
- **UI Library**: Material-UI (MUI)
- **State Management**: Zustand
- **Build Tool**: Vite
- **Routing**: React Router

#### Component Structure

```
src/web/src/
├── components/
│   ├── Layout.tsx       # Main layout with navigation
│   ├── Dashboard.tsx    # Home dashboard
│   ├── Scanner.tsx      # Scan interface
│   ├── Results.tsx      # Results view
│   └── Settings.tsx     # Settings page
├── api/
│   └── client.ts        # API client
├── utils/
│   └── store.ts         # Global state
└── App.tsx              # Root component
```

## Development

### Prerequisites

- Node.js 18+
- Python 3.8+
- FastAPI and Uvicorn

### Setup

1. **Install Python dependencies**:
```bash
pip install fastapi uvicorn websockets psutil requests
```

2. **Install Node dependencies**:
```bash
cd src/web
npm install
```

3. **Start development server**:
```bash
# Terminal 1: Start backend
smartfile serve

# Terminal 2: Start frontend dev server
cd src/web
npm run dev
```

Frontend dev server runs on port 3000 with API proxy to port 8001.

### Building for Production

```bash
cd src/web
npm run build
```

Built files are output to `src/web/dist/` and automatically served by the FastAPI backend.

## Security

### Local-Only Access

By default, the web server binds to `127.0.0.1` (localhost) and is **only accessible from the local machine**.

### Network Access (Optional)

To enable network access (NOT RECOMMENDED for production):

```bash
smartfile serve --host 0.0.0.0 --port 8001
```

⚠️ **Warning**: This exposes the interface to your network. Implement authentication before enabling network access.

### CORS Configuration

CORS is configured to allow:
- `http://localhost:8001`
- `http://127.0.0.1:8001`
- `http://localhost:3000` (for development)

### Future Security Features

- JWT authentication
- HTTPS support
- Role-based access control
- API rate limiting
- CSRF protection

## Troubleshooting

### Web UI Not Loading

**Symptom**: Browser shows "Web UI not built" error

**Solution**:
```bash
cd src/web
npm install
npm run build
```

### WebSocket Connection Failed

**Symptom**: Real-time updates not working

**Solution**:
1. Check backend is running on correct port
2. Verify WebSocket endpoint: `ws://localhost:8001/ws/scan/{id}`
3. Check browser console for errors
4. Fallback to polling will activate automatically

### Port Already in Use

**Symptom**: `Error: Port 8001 is already in use`

**Solution**:
1. Find process using port:
   ```bash
   # Linux/Mac
   lsof -i :8001
   
   # Windows
   netstat -ano | findstr :8001
   ```

2. Use alternative port:
   ```bash
   smartfile serve --port 8002
   ```

### AI Provider Not Connected

**Symptom**: Dashboard shows "AI Provider: Disconnected"

**Solution**:
1. Ensure Ollama is running:
   ```bash
   ollama serve
   ```

2. Verify endpoint in Settings:
   - Default: `http://localhost:11434`
   - Test: `curl http://localhost:11434/api/tags`

3. Check firewall settings

## Browser Compatibility

Supported browsers:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Accessibility

The web UI includes:
- Keyboard navigation (Tab, Enter, Escape)
- ARIA labels for screen readers
- High contrast mode via dark theme
- Responsive font sizes
- Focus indicators

## Performance

### Optimization Features

- Lazy loading of components
- Debounced search/filter inputs
- Pagination for large result sets
- WebSocket for efficient real-time updates
- Production build minification

### Recommended Specs

- Modern browser with JavaScript enabled
- 2GB+ RAM
- Stable network connection (for WebSocket)

## Help and Support

### In-App Help

- Tooltips on hover (? icons)
- Field helper text
- Error messages with suggestions

### Documentation Links

Configure `SMARTFILE_HELP_BASE_URL` environment variable to customize help links:

```bash
export SMARTFILE_HELP_BASE_URL="https://your-docs.com/smartfile"
```

Default: `https://github.com/gaI-observe-online/SmartFileOrganizer/tree/main/docs`

### Diagnostics Export

Export system diagnostics from Settings page for troubleshooting:

1. Go to Settings
2. Click "Export Diagnostics" (future feature)
3. ZIP file includes:
   - System information
   - Configuration (redacted)
   - Recent logs (redacted)

## Future Enhancements

Planned features:
- [ ] First-run setup wizard
- [ ] Interactive onboarding tour
- [ ] File preview with thumbnails
- [ ] Drag-and-drop folder selection
- [ ] Bulk file operations
- [ ] Export results to CSV
- [ ] Advanced search and filtering
- [ ] Keyboard shortcuts overlay
- [ ] Multi-language support (i18n)
- [ ] Mobile app (React Native)

## License

MIT License - see [LICENSE](../../LICENSE) for details.
