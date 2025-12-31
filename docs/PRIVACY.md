# Privacy & Security

## Privacy-First Design

SmartFileOrganizer is designed with privacy as the top priority. All processing happens locally on your machine.

## Key Privacy Features

### 1. 100% Local Processing

- ✅ **All AI runs locally** via Ollama (llama3.3/qwen2.5)
- ✅ **No cloud services** - everything stays on your machine
- ✅ **No external API calls** (except optional admin-enabled providers)
- ✅ **No telemetry** - we don't track usage
- ✅ **No internet required** - works completely offline

### 2. Sensitive Data Protection

#### Automatic Detection

The system automatically detects:
- Social Security Numbers (SSN)
- Credit card numbers
- Email addresses
- Phone numbers
- API keys and passwords
- Usernames in file paths

#### Automatic Redaction

All detected sensitive data is redacted in logs:

**Before:**
```
Moved /Users/john/Documents/SSN_123-45-6789.pdf
```

**After:**
```
Moved /Users/****/Documents/SSN_***-**-****.pdf
```

#### Risk Assessment

Files containing sensitive data are flagged for manual review:
- SSN/Credit cards: +40 risk points
- Passwords/API keys: +50 risk points
- High-risk files (>70 points) require manual approval

### 3. Data Storage

#### Local Storage Only

All data is stored locally:
```
~/.organizer/
├── config.json        # Your configuration
├── audit.db           # SQLite database (local)
├── audit.jsonl        # JSON Lines audit log
├── operations.log     # Human-readable log
└── backups/           # File backups
```

#### No Remote Sync

- Files are never uploaded to cloud services
- Backups remain on your local disk
- Audit trails stay on your machine
- No synchronization with external servers

### 4. Configuration Privacy

#### Redaction Settings

In `config.json`:
```json
{
  "privacy": {
    "no_external_communication": true,
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

#### Disable External Communication

By default, all external communication is disabled. Even optional AI providers (OpenAI, Anthropic) require explicit admin enablement:

```json
{
  "ai": {
    "models": {
      "openai": {
        "enabled": false,  // Disabled by default
        "api_key": ""
      }
    }
  }
}
```

### 5. Audit Trail Security

#### Redacted Logging

All logs automatically redact:
- Personal information
- Sensitive data patterns
- Usernames in paths
- Email addresses
- Phone numbers

#### Access Control

Audit files are only accessible to:
- The user running the application
- No other users on the system
- No external services

### 6. File Handling

#### Secure Moves

- Files are moved (not copied) to avoid duplication
- Original permissions are preserved
- No file content modification
- Backups use secure file operations

#### Backup Security

- Backups stored in `~/.organizer/backups/`
- Only accessible by file owner
- Automatic cleanup after 30 days
- Large files (>500MB) use metadata-only backups

## Security Best Practices

### 1. Protect Configuration

```bash
# Restrict config file access
chmod 600 ~/.organizer/config.json

# Don't share config files (contains API keys if enabled)
```

### 2. Regular Backups

While SmartFileOrganizer backs up files before moving, maintain your own backups:

```bash
# Backup important data separately
rsync -av ~/Documents ~/Backup/
```

### 3. Review High-Risk Operations

Always review operations flagged as high-risk:
- Files with SSN/credit card patterns
- Files with passwords/API keys
- Recently modified files
- System files

### 4. Audit Trail Review

Regularly review audit trails:

```bash
# Check recent operations
python organize.py audit --last 100

# Review statistics
python organize.py stats --summary
```

## What Data is Collected?

### Locally Stored

- File paths and names
- File metadata (size, dates)
- Organization decisions
- User approvals/rejections
- Rollback history

### Never Collected

- File contents (only first 1000 chars for analysis, never stored)
- Personal information
- Usage statistics
- Telemetry data
- Crash reports

## Data Retention

### Audit Trail

- SQLite database: Unlimited (manual cleanup)
- JSON Lines log: Unlimited (manual cleanup)
- Human-readable log: Unlimited (manual cleanup)

### Backups

- Retention: 30 days (configurable)
- Max operations: 100 (configurable)
- Auto-cleanup: Enabled by default

### Configuration

```json
{
  "backup": {
    "retention_days": 30,
    "max_operations": 100
  }
}
```

## Third-Party Integrations

### Default (Ollama)

- Runs locally on port 11434
- No external communication
- Models stored locally
- Complete privacy

### Optional (Admin-Enabled)

If you manually enable OpenAI or Anthropic:

- **OpenAI:** File metadata sent to OpenAI API
- **Anthropic:** File metadata sent to Anthropic API
- **Data sent:** Filenames, types, sizes (NOT content)
- **Control:** You explicitly enable and provide API keys

**Recommendation:** Use Ollama (default) for complete privacy.

## Compliance

### GDPR

SmartFileOrganizer is GDPR-compliant by design:
- ✅ Data minimization (only what's needed)
- ✅ Purpose limitation (only for organization)
- ✅ Storage limitation (configurable retention)
- ✅ No data sharing (100% local)
- ✅ Right to erasure (manual deletion supported)

### HIPAA

For healthcare environments:
- ✅ Local processing only
- ✅ Automatic PHI detection
- ✅ Complete audit trail
- ✅ No external transmission

## Questions?

For privacy concerns or questions:
- Review source code: [GitHub Repository](https://github.com/gaI-observe-online/SmartFileOrganizer)
- Open an issue: [GitHub Issues](https://github.com/gaI-observe-online/SmartFileOrganizer/issues)

## Trust but Verify

SmartFileOrganizer is open source. You can:
1. Review all source code
2. Audit network traffic (should be none to external services)
3. Monitor file system changes
4. Inspect audit logs

**Verify yourself:**
```bash
# Monitor network traffic (should show no external connections)
tcpdump -i any port not 11434  # Except Ollama on localhost

# Check file changes
python organize.py scan ~/Downloads --dry-run
```
