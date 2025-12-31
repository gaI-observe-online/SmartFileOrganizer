# SmartFileOrganizer

**AI-Powered Intelligent File Organization System with Web UI**

SmartFileOrganizer is a production-ready, privacy-first file organization tool that uses local AI (Ollama/LLama) to intelligently categorize and organize your files. Now with a modern web interface for easy, visual file management!

## ✨ Features

### Web UI (New in v2.0!)
- 🌐 **Modern Web Interface** - Beautiful, consumer-grade UI in your browser
- 🚀 **One-Click Auto-Scan** - Scan Downloads, Documents, Desktop, Pictures instantly
- 📊 **Visual Plan Preview** - See what will happen before files are moved
- ✅ **Interactive Approval** - Approve, execute, and rollback with one click
- 🎯 **Real-Time Status** - Live server health monitoring
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

### Core Features
- 🤖 **AI-Powered Organization** - Uses Ollama (llama3.3/qwen2.5) for intelligent file categorization
- 🔒 **Privacy-First** - 100% local processing, no external communication
- 📊 **4-Level Categorization** - Type → Context → Time → Smart naming
- ⚠️ **Risk Assessment** - Automatic detection of sensitive content (SSN, credit cards, API keys)
- 📝 **Complete Audit Trail** - Triple-format logging (SQLite + JSON Lines + human-readable)
- ↩️ **Rollback Support** - Undo any operation with full file restoration
- 👁️ **Watch Mode** - Real-time monitoring and organization (CLI)
- 🎨 **Rich Terminal UI** - Beautiful, color-coded CLI interface
- 🧠 **Self-Learning** - Learns from your preferences over time
- 🐳 **Docker Ready** - Easy deployment with Docker Compose

## 🚀 Quick Start

### One-Click Installation

**Linux/macOS:**
```bash
./install.sh
```

**Windows:**
```batch
install.bat
```

The installer will:
1. ✅ Check Python 3.8+ and system requirements
2. ✅ Install Ollama (if needed) and download AI models
3. ✅ Set up Python environment with all dependencies
4. ✅ **Start web server automatically**
5. ✅ **Open browser to http://localhost:8001**

**That's it!** You're ready to organize files.

### First Use: Web UI

1. **Click "Auto-Scan Common Folders"** - Scans Downloads, Documents, Desktop, Pictures
2. **Review organization plans** - See file count, space savings, risk level
3. **Click "Approve"** on plans you like
4. **Click "Execute"** to organize files
5. **Use "Rollback"** to undo if needed

**Zero terminal interaction required!** 🎉

## 📖 Usage

### Web UI (Primary Interface)

The web interface is now the recommended way to use SmartFileOrganizer:

1. **Start the server** (if not already running):
   ```bash
   ./start.sh  # Linux/macOS
   start.bat   # Windows
   ```

2. **Open browser**: http://localhost:8001

3. **Use the interface**:
   - Auto-scan common folders with one click
   - Manually enter folder paths to scan
   - Review organization plans with visual metrics
   - Approve and execute plans
   - Rollback executed plans if needed

### CLI (Advanced Users)

### CLI (Advanced Users)

The CLI is still fully functional for power users:

```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate.bat  # Windows

# Interactive mode (preview and confirm)
python organize.py scan ~/Downloads

# Dry run (preview only, no changes)
python organize.py scan ~/Downloads --dry-run

# Batch mode (auto-approve low risk files)
python organize.py scan ~/Downloads --batch --auto-approve-threshold 30
```

### Watch Folder (Real-time)

```bash
# Batch mode (collect for 5 minutes, then process)
python organize.py watch ~/Downloads

# Immediate mode (process files instantly)
python organize.py watch ~/Downloads --immediate

# Queue mode (collect for manual review)
python organize.py watch ~/Downloads --queue-for-review
```

### Rollback Operations

```bash
# Rollback last operation
python organize.py rollback --last

# Rollback specific proposal
python organize.py rollback --proposal 42

# Show rollback history
python organize.py rollback --show-history
```

### View Statistics

```bash
# Show audit history
python organize.py audit --last 100

# Show statistics
python organize.py stats --summary
```

## 🎯 How It Works

### Organization Workflow

```
1. SCAN     → Discovers files and extracts content
2. ANALYZE  → AI categorizes and assesses risk
3. PROPOSE  → Generates organization plan
4. REVIEW   → User approves (auto for low-risk)
5. EXECUTE  → Moves files with backup
6. AUDIT    → Records everything
```

### 4-Level Categorization

```
Level 1 (Type)    → Documents, Images, Code, Finance, Videos, Audio
Level 2 (Context) → Work, Personal, Projects, Clients
Level 3 (Time)    → 2024, 2024-12, 2024-12-31
Level 4 (Smart)   → AI-detected project/client/topic names

Example: Documents/Work/2024/ProjectX/report.pdf
```

### Risk Scoring (0-100)

- **0-30 (Low)** → Auto-approve ✅
- **31-70 (Medium)** → Preview & confirm ⚠️
- **71-100 (High)** → Mandatory review 🚨

**Risk Factors:**
- SSN/Credit card patterns: +40
- Passwords/API keys: +50
- Large files >500MB: +10
- System files (.dll, .sys): +30
- Recently modified (<24h): +20

## 🔧 Configuration

Edit `~/.organizer/config.json`:

```json
{
  "ai": {
    "primary": "ollama",
    "models": {
      "ollama": {
        "endpoint": "http://localhost:11434",
        "model": "llama3.3",
        "fallback_model": "qwen2.5"
      }
    }
  },
  "preferences": {
    "auto_approve_threshold": 30,
    "backup_before_move": true,
    "ignore_hidden": true
  },
  "privacy": {
    "redact_sensitive_in_logs": true
  }
}
```

## 🐳 Docker Deployment

```bash
docker-compose up -d
docker exec smartfile-organizer python organize.py scan /data/Downloads
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/smartfile
```

## 📦 Supported File Types

- **Documents:** PDF, Word, TXT, Markdown
- **Spreadsheets:** Excel, CSV
- **Images:** JPG, PNG, GIF (with OCR support)
- **Code:** Python, JavaScript, Java, C/C++, Go, Rust
- **Email:** .eml files
- **Archives:** ZIP, RAR, 7Z, TAR, GZ
- **Media:** Videos (MP4, AVI, MKV), Audio (MP3, WAV, FLAC)

## 🔐 Privacy Guarantees

- ✅ 100% local processing (no cloud, no external APIs)
- ✅ All AI runs on your machine via Ollama
- ✅ Sensitive data automatically redacted in logs
- ✅ No telemetry, no tracking, no phone-home
- ✅ Complete control over your data

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines and submit PRs.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## ⚠️ Requirements

- Python 3.8+
- Ollama (auto-installed during setup)
- 10GB+ free disk space
- Linux, macOS, or Windows (WSL or native)

## 🆘 Support

- **Issues:** [GitHub Issues](https://github.com/gaI-observe-online/SmartFileOrganizer/issues)
- **Documentation:** [Full Docs](docs/)

---

**Made with ❤️ for privacy-conscious file organization**

