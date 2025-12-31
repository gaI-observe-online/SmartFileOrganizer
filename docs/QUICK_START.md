# Quick Start Guide

Get SmartFileOrganizer running in 30 seconds!

## Installation

### Linux/macOS

```bash
./install.sh
```

**That's it!** The installer will:
- ✅ Check Python 3.8+
- ✅ Install Ollama (if needed)
- ✅ Download AI models
- ✅ Set up Python environment
- ✅ Start the server automatically
- ✅ Open your browser to http://localhost:8001

### Windows

```batch
install.bat
```

Follow the same automated process on Windows.

## First Use

### Option 1: Auto-Scan (Recommended)

1. **Click "Auto-Scan Common Folders"** in the web UI
   - Scans: Downloads, Documents, Desktop, Pictures
   - Takes 2-5 seconds
2. **Review organization plans** that appear
3. **Click "Approve"** on any plan you like
4. **Click "Execute"** to organize files
5. **Use "Rollback"** to undo if needed

### Option 2: Manual Scan

1. **Enter a folder path** (e.g., `/home/user/Downloads`)
   - Or click a quick folder chip
2. **Click "Scan Folder"**
3. **Review the plan** that appears
4. **Approve and Execute**

## Understanding Plans

Each organization plan shows:

| Metric | Description |
|--------|-------------|
| **Files** | Number of files to organize |
| **Space** | Total size to be managed (MB) |
| **Risk Level** | Low/Medium/High based on sensitivity |
| **Status** | pending → approved → executed → rolled_back |

### Risk Levels

- 🟢 **Low (0-30)**: Safe to auto-approve
- 🟡 **Medium (31-70)**: Review recommended
- 🔴 **High (71-100)**: Contains sensitive data, review carefully

## Web UI Tour

### Main Sections

1. **Hero Section**: Auto-scan button for quick start
2. **Manual Scan**: Enter custom folder paths
3. **Quick Chips**: One-click access to common folders
4. **Organization Plans**: Grid of all scan results
5. **Status Indicator**: Shows if server is online

### Plan Actions

| Button | Action | When Available |
|--------|--------|----------------|
| ✅ **Approve** | Mark plan as reviewed | Status: pending |
| ▶️ **Execute** | Move files according to plan | Status: pending or approved |
| ↩️ **Rollback** | Undo file moves | Status: executed |

## CLI Usage (Advanced)

For power users who prefer the command line:

```bash
# Activate environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate.bat  # Windows

# Scan a folder
python organize.py scan ~/Downloads

# Watch a folder (auto-organize)
python organize.py watch ~/Downloads

# View help
python organize.py --help
```

## Troubleshooting

### Server Won't Start?

```bash
./start.sh  # Linux/macOS
start.bat   # Windows
```

### Browser Didn't Open?

Manually navigate to: **http://localhost:8001**

### Port 8001 Already in Use?

**Linux/macOS:**
```bash
# Find and kill process using port 8001
lsof -i :8001
kill <PID>

# Restart
./start.sh
```

**Windows:**
```batch
# Find process
netstat -ano | findstr :8001

# Kill process
taskkill /PID <PID> /F

# Restart
start.bat
```

### Server Shows "Offline"?

1. Check if server is running:
   ```bash
   curl http://localhost:8001/health
   ```

2. Restart server:
   ```bash
   ./start.sh  # or start.bat on Windows
   ```

3. Check logs in terminal for errors

### AI Models Not Found?

```bash
# Pull models manually
ollama pull llama3.3
ollama pull qwen2.5

# Restart server
./start.sh
```

## Server Management

### Start Server

```bash
./start.sh  # Linux/macOS
start.bat   # Windows
```

### Stop Server

**Linux/macOS:**
```bash
# Find the process ID
ps aux | grep uvicorn

# Kill it
kill <PID>
```

**Windows:**
```batch
taskkill /IM python.exe /F
```

### Check Server Status

```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "ai_available": true
}
```

## What Gets Organized?

SmartFileOrganizer creates a 4-level directory structure:

```
Level 1 (Type)    → Documents, Images, Code, Finance, Videos, Audio
Level 2 (Context) → Work, Personal, Projects, Clients
Level 3 (Time)    → 2024, 2024-12, 2024-12-31
Level 4 (Smart)   → AI-detected project/client/topic names

Example: Documents/Work/2024/ProjectX/report.pdf
```

## Privacy & Security

- ✅ **100% Local**: All processing happens on your computer
- ✅ **No Cloud**: Files never leave your machine
- ✅ **Open Source**: Audit the code yourself
- ✅ **Full Control**: You approve every action
- ✅ **Audit Trail**: Every operation is logged
- ✅ **Rollback**: Undo any operation with one click

## Next Steps

- 📖 Read [USAGE.md](USAGE.md) for advanced features
- 🔐 Review [PRIVACY.md](PRIVACY.md) for security details
- ⚙️ Customize [CONFIGURATION.md](CONFIGURATION.md)
- 📊 Explore [AUDIT_TRAIL.md](AUDIT_TRAIL.md) for logging

## Support

- **Issues**: [GitHub Issues](https://github.com/gaI-observe-online/SmartFileOrganizer/issues)
- **Docs**: [Full Documentation](../)

---

**Made with ❤️ for privacy-conscious file organization**
