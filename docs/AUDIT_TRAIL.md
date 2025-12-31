# Audit Trail

## Overview

SmartFileOrganizer maintains a comprehensive audit trail of all operations using three complementary formats:

1. **SQLite Database** - Structured queries and analytics
2. **JSON Lines** - Machine-readable event stream
3. **Human-Readable Log** - Easy reading and debugging

All three formats are kept in sync automatically.

## Storage Location

```
~/.organizer/
├── audit.db           # SQLite database
├── audit.jsonl        # JSON Lines log
└── operations.log     # Human-readable log
```

## Format Details

### 1. SQLite Database

#### Schema

```sql
-- Scans table
CREATE TABLE scans (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    path TEXT,
    file_count INTEGER
);

-- Proposals table
CREATE TABLE proposals (
    id INTEGER PRIMARY KEY,
    scan_id INTEGER,
    plan TEXT,              -- JSON
    confidence REAL,
    timestamp DATETIME,
    user_approved BOOLEAN,
    rolled_back BOOLEAN DEFAULT 0
);

-- Moves table
CREATE TABLE moves (
    id INTEGER PRIMARY KEY,
    proposal_id INTEGER,
    original_path TEXT,
    new_path TEXT,
    timestamp DATETIME
);

-- Learning data table
CREATE TABLE learning_data (
    id INTEGER PRIMARY KEY,
    file_type TEXT,
    target_folder TEXT,
    user_approved BOOLEAN,
    timestamp DATETIME
);
```

#### Query Examples

```sql
-- Get all scans from today
SELECT * FROM scans 
WHERE DATE(timestamp) = DATE('now');

-- Get all approved proposals
SELECT * FROM proposals 
WHERE user_approved = 1 AND rolled_back = 0;

-- Get moves for a specific proposal
SELECT * FROM moves 
WHERE proposal_id = 42;

-- Get learning patterns
SELECT 
    file_type,
    target_folder,
    COUNT(*) as count,
    SUM(CASE WHEN user_approved THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as approval_rate
FROM learning_data
GROUP BY file_type, target_folder
HAVING count >= 10;
```

### 2. JSON Lines Format

Each line is a separate JSON object:

```jsonl
{"timestamp": "2025-12-31T10:00:00", "action": "scan", "path": "/Downloads", "file_count": 47, "scan_id": 1}
{"timestamp": "2025-12-31T10:01:00", "action": "propose", "scan_id": 1, "proposal_id": 1, "confidence": 0.92}
{"timestamp": "2025-12-31T10:02:00", "action": "approval", "proposal_id": 1, "approved": true}
{"timestamp": "2025-12-31T10:03:00", "action": "execute", "proposal_id": 1, "files_moved": 45, "success": true}
```

#### Event Types

- `scan` - Directory scan completed
- `propose` - Organization proposal generated
- `approval` - User approved/rejected proposal
- `execute` - Proposal execution completed
- `rollback` - Rollback operation completed

### 3. Human-Readable Log

```
[2025-12-31 10:00:00] SCAN: /Downloads → 47 files discovered
[2025-12-31 10:01:00] PROPOSE: AI generated plan (confidence: 92%)
[2025-12-31 10:02:00] APPROVED: Proposal 1
[2025-12-31 10:03:00] EXECUTE: Moved 45 files successfully
```

## Viewing Audit Trail

### Command Line

```bash
# Show last 100 operations
python organize.py audit --last 100

# Filter by date
python organize.py audit --date 2024-12-31

# Filter by filename
python organize.py audit --file report.pdf

# Show statistics
python organize.py stats --summary
```

### Direct Database Access

```bash
# Using sqlite3
sqlite3 ~/.organizer/audit.db

# Example queries
SELECT * FROM scans ORDER BY timestamp DESC LIMIT 10;
SELECT * FROM proposals WHERE user_approved = 1;
```

### Programmatic Access

```python
from smartfile.core.database import Database
from pathlib import Path

db = Database(Path.home() / ".organizer" / "audit.db")

# Get recent scans
scans = db.get_recent_scans(limit=10)

# Get proposal
proposal = db.get_proposal_by_id(42)

# Get moves
moves = db.get_moves_by_proposal(42)
```

## Rollback Using Audit Trail

### View Rollback History

```bash
python organize.py rollback --show-history
```

Output:
```
┌─────────────┬─────────────────────┬───────┬────────────┐
│ Proposal ID │ Timestamp           │ Files │ Status     │
├─────────────┼─────────────────────┼───────┼────────────┤
│ 5           │ 2024-12-31 10:00:00 │ 23    │ Active     │
│ 4           │ 2024-12-30 15:30:00 │ 15    │ Rolled Back│
│ 3           │ 2024-12-29 09:15:00 │ 42    │ Active     │
└─────────────┴─────────────────────┴───────┴────────────┘
```

### Rollback Operations

```bash
# Rollback last operation
python organize.py rollback --last

# Rollback specific proposal
python organize.py rollback --proposal 5
```

## Data Retention

### Default Settings

```json
{
  "backup": {
    "max_operations": 100,
    "retention_days": 30
  }
}
```

### Auto-Cleanup

Backups are automatically cleaned up:
- After 30 days (configurable)
- Keeping last 100 operations (configurable)

### Manual Cleanup

```bash
# Delete old backups
find ~/.organizer/backups/ -mtime +30 -delete

# Vacuum database
sqlite3 ~/.organizer/audit.db "VACUUM;"
```

## Sensitive Data Redaction

### Automatic Redaction

All logs automatically redact:
- SSN: `123-45-6789` → `***-**-****`
- Credit cards: `4111-1111-1111-1111` → `****-****-****-****`
- Emails: `user@example.com` → `****@example.com`
- Paths: `/Users/john/` → `/Users/****/`

### Configuration

```json
{
  "privacy": {
    "redact_sensitive_in_logs": true,
    "sensitive_patterns": [
      "SSN",
      "CreditCard",
      "APIKey",
      "Password",
      "Email",
      "Phone"
    ]
  }
}
```

## Export Audit Trail

### Export to JSON

```bash
python organize.py audit export --format json --output audit-2024.json
```

### Export to CSV

```bash
python organize.py audit export --format csv --output audit-2024.csv
```

## Audit Trail Integrity

### Verification

The audit trail is append-only and timestamped:
- SQLite database provides ACID guarantees
- JSON Lines format is immutable (append-only)
- Logs include microsecond timestamps

### Backup Audit Trail

```bash
# Backup entire .organizer directory
tar -czf organizer-backup-$(date +%Y%m%d).tar.gz ~/.organizer/
```

## Troubleshooting

### Database Locked

```bash
# Close all connections
pkill -f "python.*organize"

# Retry operation
```

### Corrupt Database

```bash
# Backup first
cp ~/.organizer/audit.db ~/.organizer/audit.db.backup

# Try to repair
sqlite3 ~/.organizer/audit.db "PRAGMA integrity_check;"

# If needed, rebuild from JSON Lines
python organize.py audit rebuild
```

### Large Log Files

```bash
# Rotate logs
mv ~/.organizer/operations.log ~/.organizer/operations.log.old
gzip ~/.organizer/operations.log.old

# Archive JSON Lines
gzip -c ~/.organizer/audit.jsonl > audit-archive-$(date +%Y%m%d).jsonl.gz
> ~/.organizer/audit.jsonl  # Truncate
```

## Best Practices

1. **Regular Backups**
   ```bash
   # Daily cron job
   0 2 * * * tar -czf ~/backups/organizer-$(date +\%Y\%m\%d).tar.gz ~/.organizer/
   ```

2. **Monitor Disk Space**
   ```bash
   du -sh ~/.organizer/
   ```

3. **Periodic Review**
   ```bash
   # Weekly audit review
   python organize.py stats --summary
   ```

4. **Clean Old Backups**
   ```bash
   # Remove backups older than 60 days
   find ~/.organizer/backups/ -mtime +60 -delete
   ```
