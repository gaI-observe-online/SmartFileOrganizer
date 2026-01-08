# Upgrading from PR #1 (CLI-only Version)

If you installed the CLI-only version of SmartFileOrganizer (PR #1), this guide will help you upgrade to the full version with web UI.

## What's New in v2.0.0?

### Major Additions

✅ **Web UI** - Modern, consumer-grade browser interface
✅ **One-Click Installation** - Automated setup with server auto-start
✅ **Auto-Scan** - Scan common folders with one click
✅ **Visual Plan Preview** - See what will happen before it happens
✅ **Interactive Workflow** - Approve, execute, and rollback from UI

### What Stays the Same

✅ **All CLI Commands** - Every command you used still works
✅ **API Endpoints** - All existing endpoints unchanged
✅ **Configuration** - Your config file is compatible
✅ **Audit Trail** - All logging continues to work
✅ **Database** - Existing data is preserved

## Quick Upgrade

### Option 1: Fresh Install (Recommended)

If you want a clean start:

```bash
# Backup your configuration (optional)
cp ~/.organizer/config.json ~/config.backup.json

# Pull latest changes
git pull origin main

# Run installer (this adds web UI components)
./install.sh
```

The installer will:
1. Detect existing venv and dependencies
2. Add FastAPI and uvicorn
3. Create static files directory
4. Start the web server
5. Open browser to http://localhost:8001

### Option 2: Manual Upgrade

If you prefer manual control:

```bash
# 1. Pull latest code
git pull origin main

# 2. Activate existing venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate.bat  # Windows

# 3. Install new dependencies
pip install fastapi==0.109.0 uvicorn==0.27.0

# 4. Verify static files exist
ls static/  # Should show: index.html, app.js, styles.css

# 5. Start server
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001

# 6. Open browser
# Navigate to: http://localhost:8001
```

## Verification Checklist

After upgrading, verify everything works:

### ✅ Web UI

- [ ] Browser opens to http://localhost:8001
- [ ] Status shows "✅ Connected"
- [ ] Auto-Scan button is visible
- [ ] Manual scan form is present
- [ ] Footer shows privacy message

### ✅ CLI (Regression Test)

All existing commands should still work:

```bash
# Activate venv first
source venv/bin/activate

# Test commands
python organize.py --version        # Should show version
python organize.py --help           # Should show commands
python organize.py scan ~/Downloads # Should work as before
```

### ✅ API

API endpoints should be accessible:

```bash
# Health check
curl http://localhost:8001/health

# API docs
# Visit: http://localhost:8001/docs
```

### ✅ Configuration

Your existing config should work:

```bash
# Check config location
ls ~/.organizer/config.json

# Verify it's valid JSON
cat ~/.organizer/config.json | python -m json.tool
```

### ✅ Database

Existing data should be preserved:

```bash
# Check database exists
ls ~/.organizer/audit.db

# Verify it's readable
sqlite3 ~/.organizer/audit.db "SELECT COUNT(*) FROM scans;"
```

## Migrating Workflows

### Before (PR #1): CLI-Only

```bash
# Old workflow
source venv/bin/activate
python organize.py scan ~/Downloads --dry-run
python organize.py scan ~/Downloads  # Execute
```

### After (v2.0.0): Web UI First

```
1. Open http://localhost:8001
2. Click "Auto-Scan"
3. Review plans
4. Click "Approve" → "Execute"
```

**CLI still works!** Nothing changed for power users.

## New Features to Try

### 1. Auto-Scan Common Folders

Instead of manually scanning each folder:

**Old Way (CLI):**
```bash
python organize.py scan ~/Downloads
python organize.py scan ~/Documents
python organize.py scan ~/Desktop
python organize.py scan ~/Pictures
```

**New Way (Web UI):**
- Click "Auto-Scan Common Folders"
- All folders scanned at once
- All plans displayed in grid

### 2. Visual Plan Review

**Old Way (CLI):**
- Read text output in terminal
- Approve with Y/N prompt

**New Way (Web UI):**
- See plan cards with metrics
- Color-coded risk levels
- Click to approve/execute/rollback

### 3. Rollback from UI

**Old Way (CLI):**
```bash
python organize.py rollback --last
python organize.py rollback --proposal 42
```

**New Way (Web UI):**
- Click "Rollback" button on any executed plan
- Instant confirmation dialog
- Files restored automatically

## Configuration Updates

No configuration changes required! Your existing `~/.organizer/config.json` works as-is.

### Optional: Enable New Features

If you want to customize web UI behavior, add these optional settings:

```json
{
  "web_ui": {
    "auto_refresh_interval": 30,
    "show_notifications": true,
    "theme": "light"
  }
}
```

*Note: These settings are planned for future releases.*

## Troubleshooting

### Issue: "Module not found: fastapi"

**Solution:**
```bash
source venv/bin/activate
pip install fastapi==0.109.0 uvicorn==0.27.0
```

### Issue: "Static files not found"

**Solution:**
```bash
# Verify static directory exists
ls static/

# If missing, pull latest code
git pull origin main
```

### Issue: "Port 8001 already in use"

**Solution:**
```bash
# Find and kill process
lsof -i :8001
kill <PID>

# Or use different port
python -m uvicorn src.main:app --host 0.0.0.0 --port 8002
```

### Issue: "CLI commands don't work"

**Solution:**
```bash
# Ensure venv is activated
source venv/bin/activate

# Verify organize.py exists
ls organize.py

# Try with python directly
python organize.py --help
```

## Rollback to PR #1

If you need to go back to CLI-only version:

```bash
# 1. Stop server
# Press Ctrl+C or kill process

# 2. Checkout PR #1 branch
git checkout <PR1-branch-or-tag>

# 3. Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt

# 4. Continue using CLI
python organize.py --help
```

## FAQ

### Q: Do I need to reinstall Ollama?

**A:** No, existing Ollama installation works fine.

### Q: Will my existing scans/proposals be visible in web UI?

**A:** Yes! All historical data appears in the plans grid.

### Q: Can I use both CLI and Web UI?

**A:** Absolutely! They work together. Changes in one appear in the other.

### Q: Is the web UI secure?

**A:** Yes:
- Runs locally on `localhost:8001`
- No external access by default
- All processing stays on your machine
- Same privacy guarantees as CLI

### Q: Can I disable the web UI and use CLI only?

**A:** Yes! Just don't start the server. Use CLI as before:
```bash
source venv/bin/activate
python organize.py scan ~/Downloads
```

## Support

If you encounter issues during upgrade:

1. Check [QUICK_START.md](QUICK_START.md) for common solutions
2. Review [INSTALLATION.md](INSTALLATION.md) for detailed setup
3. Open an issue: [GitHub Issues](https://github.com/gaI-observe-online/SmartFileOrganizer/issues)

## What's Next?

Explore new features:
- 📖 [QUICK_START.md](QUICK_START.md) - Get started with web UI
- 📚 [USAGE.md](USAGE.md) - Advanced features
- 🔐 [PRIVACY.md](PRIVACY.md) - Security details

---

**Welcome to SmartFileOrganizer v2.0.0!** 🎉
