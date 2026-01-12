# Troubleshooting Guide

Quick reference for common SmartFileOrganizer installation and runtime issues.

## 🔍 First Steps

When encountering any issue:

1. **Run diagnostics:**
   ```bash
   ./diagnose.sh
   ```

2. **Check logs:**
   ```bash
   cat ~/.organizer/install.log      # Installation log
   cat ~/.organizer/operations.log   # Runtime log
   ```

3. **Verify installation:**
   ```bash
   source venv/bin/activate
   python organize.py --version
   ```

## 🚨 Common Installation Issues

### Issue: "Python 3 not found"

**Symptoms:** Installer exits with "Python 3 not found"

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install python3.8 python3-pip python3-venv

# Fedora/RHEL
sudo dnf install python3 python3-pip

# macOS
brew install python@3.8
```

**Verify:**
```bash
python3 --version  # Should show 3.8 or higher
```

---

### Issue: "pip not available"

**Symptoms:** "pip3: command not found" or "No module named pip"

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-pip

# Download pip manually
curl https://bootstrap.pypa.io/get-pip.py | python3
```

**Verify:**
```bash
python3 -m pip --version
```

---

### Issue: "venv module not found"

**Symptoms:** "No module named venv"

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-venv

# Fedora/RHEL
sudo dnf install python3-virtualenv
```

---

### Issue: "Ollama not responding"

**Symptoms:** "Cannot reach Ollama at localhost:11434"

**Solution:**
```bash
# Check if Ollama is installed
which ollama

# Start Ollama service
ollama serve &  # Or
sudo systemctl start ollama  # Linux with systemd

# Verify
curl http://localhost:11434/api/version
```

---

### Issue: "Permission denied" errors

**Symptoms:** Cannot write to directory, cannot create symlink

**Solution:**
```bash
# Install directory
sudo chown -R $USER:$USER .

# Config directory
mkdir -p ~/.organizer
chmod 755 ~/.organizer

# Symlink (optional)
sudo ln -sf $(pwd)/organize.py /usr/local/bin/organize
```

---

### Issue: "Disk space insufficient"

**Symptoms:** Warning about low disk space

**Solution:**
```bash
# Check space
df -h .

# Clean up
pip cache purge
docker system prune  # If using Docker
ollama rm <model>    # Remove unused models

# Required: 10GB+ free space
```

---

### Issue: "Installation failed mid-way"

**Symptoms:** Installer crashed, partial installation

**Solution:**
```bash
# The installer has automatic rollback, but if needed:
rm -rf venv/
rm -f ~/.organizer/install.state

# Run installer again
./install.sh
```

---

### Issue: "Network connectivity problems"

**Symptoms:** Cannot reach PyPI, Ollama, or GitHub

**Solution:**
```bash
# Test connectivity
curl -I https://pypi.org
curl -I https://ollama.com

# If behind proxy
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port

# Install with proxy
pip install -r requirements.txt
```

---

## 🔧 Common Runtime Issues

### Issue: "Module not found" errors

**Symptoms:** `ModuleNotFoundError: No module named 'click'`

**Solution:**
```bash
# Activate virtual environment first
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify
python -c "import click, rich, ollama; print('OK')"
```

---

### Issue: "Ollama connection refused"

**Symptoms:** Cannot connect to Ollama during file organization

**Solution:**
```bash
# Check Ollama status
curl http://localhost:11434/api/version

# Start if not running
ollama serve &

# Or restart
sudo systemctl restart ollama
```

---

### Issue: "Config file not found"

**Symptoms:** "config.json not found at ~/.organizer/config.json"

**Solution:**
```bash
# Copy example config
cp config.example.json ~/.organizer/config.json

# Or run installer to recreate
./install.sh
```

---

### Issue: "Database locked"

**Symptoms:** "database is locked" error

**Solution:**
```bash
# Check for running instances
ps aux | grep organize

# Kill if needed
pkill -f organize

# Remove lock file
rm ~/.organizer/*.db-wal
rm ~/.organizer/*.db-shm
```

---

### Issue: "Tesseract not found"

**Symptoms:** OCR features don't work, "tesseract not found"

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Verify
tesseract --version
```

---

## 📊 Performance Issues

### Issue: "Slow file processing"

**Symptoms:** Processing takes very long

**Solutions:**
1. Check AI model is downloaded:
   ```bash
   ollama list
   # Should show llama3.3 and qwen2.5
   ```

2. Use smaller models:
   ```bash
   ollama pull llama2:7b  # Faster, less accurate
   ```

3. Increase batch size in config:
   ```json
   {
     "preferences": {
       "batch_size": 50
     }
   }
   ```

---

### Issue: "High memory usage"

**Symptoms:** System slows down, high RAM usage

**Solutions:**
1. Use lighter AI model
2. Process fewer files at once
3. Increase swap space (Linux)
4. Close other applications

---

## 🛠 Advanced Troubleshooting

### Full Reset

If all else fails, perform a complete reset:

```bash
# 1. Uninstall completely
./uninstall.sh
# Answer 'yes' to remove config

# 2. Remove all traces
rm -rf venv/
rm -rf ~/.organizer/
sudo rm -f /usr/local/bin/organize

# 3. Clean reinstall
git pull origin main
./install.sh
```

---

### Collect Debug Information

For bug reports, collect this information:

```bash
# Run diagnostics
./diagnose.sh > diagnostics.txt

# System info
uname -a > system-info.txt
python3 --version >> system-info.txt
pip list >> system-info.txt

# Logs
tar -czf logs.tar.gz ~/.organizer/*.log

# Share diagnostics.txt, system-info.txt, and logs.tar.gz
```

---

## 💬 Getting Help

1. **Search existing issues:**
   https://github.com/gaI-observe-online/SmartFileOrganizer/issues

2. **Create new issue with:**
   - Output of `./diagnose.sh`
   - Contents of `~/.organizer/install.log`
   - System information
   - Steps to reproduce

3. **Include:**
   - OS and version
   - Python version
   - Installation method used
   - Error messages (full text)

---

## ✅ Health Check Checklist

Run this checklist to verify everything is working:

- [ ] Python 3.8+ installed: `python3 --version`
- [ ] Virtual environment created: `ls venv/`
- [ ] Dependencies installed: `source venv/bin/activate && pip list`
- [ ] Ollama installed: `which ollama`
- [ ] Ollama running: `curl http://localhost:11434/api/version`
- [ ] Models downloaded: `ollama list` (llama3.3, qwen2.5)
- [ ] Config file exists: `ls ~/.organizer/config.json`
- [ ] Config is valid JSON: `python3 -c "import json, os; json.load(open(os.path.expanduser('~/.organizer/config.json')))"`
- [ ] CLI works: `python organize.py --help`
- [ ] Can scan (dry-run): `python organize.py scan ~/Downloads --dry-run`

If all checkboxes pass, installation is successful! ✨
