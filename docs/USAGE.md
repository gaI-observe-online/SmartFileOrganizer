# Usage Guide

## Getting Started

### First Run

```bash
# Activate virtual environment (if not using system-wide install)
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Check version
python organize.py --version

# View help
python organize.py --help
```

## Core Commands

### Scan and Organize

#### Interactive Mode (Recommended)

```bash
# Scan and organize with review
python organize.py scan ~/Downloads

# Example output:
# ╔════════════════════════════════════════════════╗
# ║         📁 Scan Results: ~/Downloads           ║
# ╠════════════════════════════════════════════════╣
# ║ Total Files: 47                                ║
# ║ Documents: 23 | Images: 12 | Code: 8          ║
# ╚════════════════════════════════════════════════╝
#
# Organization Proposal:
# ┌──────────────┬─────────────────────┬──────┬──────┐
# │ File         │ Destination         │ Risk │ Conf │
# ├──────────────┼─────────────────────┼──────┼──────┤
# │ report.pdf   │ Documents/Work/2024 │ 15   │ 92%  │
# │ invoice.xlsx │ Finance/2024        │ 45   │ 88%  │
# └──────────────┴─────────────────────┴──────┴──────┘
#
# Proceed with organization? [y/N]:
```

#### Dry Run (Preview Only)

```bash
# See what would happen without making changes
python organize.py scan ~/Downloads --dry-run
```

#### Batch Mode (Automation)

```bash
# Auto-approve low-risk files (<= 30 risk score)
python organize.py scan ~/Downloads --batch

# Custom threshold
python organize.py scan ~/Downloads --batch --auto-approve-threshold 50
```

#### Recursive Scan

```bash
# Scan directory and all subdirectories
python organize.py scan ~/Downloads --recursive
```

### Watch Folder Mode

#### Batch Mode (Default)

Collects files for 5 minutes, then processes them together:

```bash
python organize.py watch ~/Downloads

# Press Ctrl+C to stop
```

#### Immediate Mode

Processes files as soon as they appear:

```bash
python organize.py watch ~/Downloads --immediate
```

#### Queue Mode

Collects files for manual review:

```bash
python organize.py watch ~/Downloads --queue-for-review
```

### Rollback Operations

#### Rollback Last Operation

```bash
python organize.py rollback --last

# Example:
# Rollback last operation? [y/N]: y
# ✓ Restored 23 files
```

#### Rollback Specific Proposal

```bash
# View history first
python organize.py rollback --show-history

# Rollback specific proposal
python organize.py rollback --proposal 42
```

### Audit Trail

#### View Recent Operations

```bash
# Last 100 operations
python organize.py audit --last 100

# Last 50 operations
python organize.py audit --last 50
```

#### Filter by Date

```bash
python organize.py audit --date 2024-12-31
```

#### Filter by Filename

```bash
python organize.py audit --file report.pdf
```

### Statistics

```bash
# View summary statistics
python organize.py stats --summary

# Example output:
# ╔════════════════════════════════════════╗
# ║            📊 Statistics               ║
# ╠════════════════════════════════════════╣
# ║ Total Scans: 15                        ║
# ║ Total Proposals: 15                    ║
# ║ Approved: 12                           ║
# ║ Rolled Back: 2                         ║
# ║ Total Files Moved: 345                 ║
# ╚════════════════════════════════════════╝
```

### Configuration

#### View Current Configuration

```bash
python organize.py config --show

# Example output:
# Current AI Provider: ollama
# Endpoint: http://localhost:11434
# Model: llama3.3
```

#### Switch AI Provider

```bash
# Switch to Ollama (default)
python organize.py config --set-provider ollama --model llama3.3

# Switch to OpenAI (requires API key)
python organize.py config --set-provider openai \
  --api-key sk-xxxxx \
  --model gpt-4o-mini

# Switch to Anthropic (requires API key)
python organize.py config --set-provider anthropic \
  --api-key sk-ant-xxxxx \
  --model claude-3-sonnet
```

#### Edit Configuration File

```bash
# Opens config in default editor
python organize.py config --edit

# Or manually edit
nano ~/.organizer/config.json
```

## Advanced Usage

### Custom Configuration Path

```bash
# Use custom config file
python organize.py --config /path/to/config.json scan ~/Downloads

# Or set environment variable
export SMARTFILE_CONFIG=/path/to/config.json
python organize.py scan ~/Downloads
```

### Verbose Mode

```bash
# Enable debug logging
python organize.py --verbose scan ~/Downloads
```

### Combining Options

```bash
# Dry run + verbose + custom threshold
python organize.py --verbose scan ~/Downloads \
  --dry-run \
  --auto-approve-threshold 20
```

## Workflows

### Daily Downloads Cleanup

```bash
# Morning routine: scan downloads folder
python organize.py scan ~/Downloads --batch

# Review any high-risk files
python organize.py audit --last 10
```

### Project Organization

```bash
# Organize project files
python organize.py scan ~/Projects/MyProject --recursive

# Review proposal before approving
# Files will be organized by type, context, and project name
```

### Email Attachments

```bash
# Watch email attachments folder
python organize.py watch ~/Mail/Attachments --immediate
```

### Archive Old Files

```bash
# Scan and organize old documents
python organize.py scan ~/Documents/Old --recursive --batch
```

## Tips & Tricks

### 1. Test First with Dry Run

Always test with `--dry-run` first to see what would happen:

```bash
python organize.py scan ~/Downloads --dry-run
```

### 2. Lower Threshold for More Automation

If you trust the AI, lower the auto-approve threshold:

```bash
python organize.py scan ~/Downloads --auto-approve-threshold 50
```

### 3. Use Watch Mode for Downloads

Set up watch mode to automatically organize new downloads:

```bash
# In a screen/tmux session
python organize.py watch ~/Downloads --immediate
```

### 4. Regular Rollback Checks

Periodically review what can be rolled back:

```bash
python organize.py rollback --show-history
```

### 5. Backup Before Big Operations

For large operations, ensure backups are enabled:

```json
{
  "backup": {
    "enabled": true,
    "max_operations": 100
  }
}
```

### 6. Monitor Audit Trail

Regularly check the audit trail:

```bash
python organize.py stats --summary
python organize.py audit --last 50
```

## Automation

### Cron Jobs (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add daily scan at 2 AM
0 2 * * * /path/to/venv/bin/python /path/to/organize.py scan ~/Downloads --batch

# Add weekly cleanup
0 3 * * 0 /path/to/venv/bin/python /path/to/organize.py scan ~/Documents --recursive --batch
```

### Task Scheduler (Windows)

```powershell
# Create scheduled task
schtasks /create /tn "SmartFileOrganizer" /tr "C:\path\to\organize.bat scan C:\Downloads --batch" /sc daily /st 02:00
```

### systemd Service (Linux)

Create service file `/etc/systemd/system/smartfile-watch.service`:

```ini
[Unit]
Description=SmartFileOrganizer Watch Service
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/SmartFileOrganizer
ExecStart=/path/to/venv/bin/python organize.py watch /home/youruser/Downloads
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable smartfile-watch
sudo systemctl start smartfile-watch
```

## Troubleshooting

### Files Not Moving

Check permissions:

```bash
ls -la ~/Downloads
# Ensure you have write permissions
```

### AI Not Working

Check Ollama status:

```bash
ollama list
# Ensure llama3.3 is installed

# Pull model if needed
ollama pull llama3.3
```

### High Memory Usage

For large scans, use batch mode:

```bash
# Process in smaller batches
python organize.py scan ~/Downloads --batch
```

### Database Locked

Close other instances:

```bash
pkill -f "python.*organize"
```

## Best Practices

1. **Start Small** - Test on a small folder first
2. **Use Dry Run** - Always preview before executing
3. **Review High-Risk** - Manually check files with risk > 70
4. **Regular Backups** - Keep separate backups of important files
5. **Monitor Audit** - Regularly review audit trail
6. **Cleanup Old Backups** - Periodically clean old backups
7. **Update Models** - Keep Ollama models up to date

## Getting Help

```bash
# General help
python organize.py --help

# Command-specific help
python organize.py scan --help
python organize.py watch --help
python organize.py rollback --help
```

## Next Steps

- Read [CONFIGURATION.md](CONFIGURATION.md) for detailed config options
- Review [PRIVACY.md](PRIVACY.md) for privacy information
- Check [AUDIT_TRAIL.md](AUDIT_TRAIL.md) for audit trail details
