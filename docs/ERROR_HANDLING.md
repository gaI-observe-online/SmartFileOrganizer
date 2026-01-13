# Error Handling Guide

SmartFileOrganizer provides comprehensive error handling with user-friendly messages and recovery workflows.

## Error Code Stability Policy

**IMPORTANT:** Error codes are stable and immutable once released.

- **Error codes E001-E006 are STABLE**: Their meaning will never change
- **New semantics require new codes**: If you need different behavior, add E007+, don't reuse E002
- **Codes can be deprecated but never repurposed**: This ensures documentation links, support workflows, and telemetry remain consistent across versions
- **Why this matters**: Users and enterprise deployments rely on stable error codes for automation, logging, and support workflows

### Adding New Error Codes

When introducing a new error type:
1. Assign the next available sequential code (E007, E008, etc.)
2. Create the error class in `src/smartfile/utils/errors.py`
3. Document it in this file following the existing format
4. Update the error code list below
5. Never reuse or repurpose existing codes

### Current Error Codes

- **E001**: Connection Error (network connectivity to services)
- **E002**: AI Provider Error (AI service failures)
- **E003**: Filesystem Error (file/directory operations)
- **E004**: Configuration Error (invalid config)
- **E005**: Scan Interrupted (incomplete scan)
- **E006**: Database Error (database operations)
- **E007+**: Reserved for future use

---

## Error Categories

### User-Actionable Errors
These errors can be resolved by the user:
- **Configuration Errors** - Invalid or missing configuration
- **Permission Errors** - Insufficient file/directory permissions
- **Input Errors** - Invalid user input
- **Not Found Errors** - Missing files or directories

### Network Errors
Connection-related issues with automatic retry:
- **Connection Errors** - Cannot connect to services (Ollama, etc.)
- **Timeout Errors** - Request timeout
- **Offline Errors** - No network connectivity

### System Errors
Internal system issues:
- **Internal Errors** - Unexpected system errors
- **Database Errors** - Database operation failures
- **Filesystem Errors** - File system operation failures
- **AI Provider Errors** - AI service errors (with fallback to rule-based)

## Error Codes

### E001: Connection Error
**Category:** Network  
**Severity:** Error  
**Description:** Unable to connect to external service (Ollama AI provider)

**Common Causes:**
- Ollama is not running
- Incorrect endpoint configuration
- Network connectivity issues

**Recovery Steps:**
1. Check if Ollama is running: `ollama list`
2. Verify endpoint in config: `python organize.py config --show`
3. Test connection: `curl http://localhost:11434/api/tags`
4. Check firewall settings

**Note:** The system will automatically fall back to rule-based organization if AI provider is unavailable.

---

### E002: AI Provider Error
**Category:** AI Provider  
**Severity:** Warning  
**Description:** AI provider failed during operation

**Common Causes:**
- Model not available
- Generation timeout
- Invalid model configuration

**Recovery Steps:**
1. Pull required model: `ollama pull llama3.3`
2. Check model availability: `ollama list`
3. Verify model name in config
4. System will fall back to rule-based organization

---

### E003: Filesystem Error
**Category:** Filesystem  
**Severity:** Error  
**Description:** File system operation failed

**Common Causes:**
- Permission denied
- Disk full
- File in use
- Invalid path

**Recovery Steps:**
1. Check file/directory permissions: `ls -la`
2. Verify disk space: `df -h`
3. Ensure no process is using the files
4. Verify path exists and is accessible

---

### E004: Configuration Error
**Category:** Configuration  
**Severity:** Error  
**Description:** Invalid or missing configuration

**Common Causes:**
- Missing required configuration key
- Invalid configuration value
- Malformed config file

**Recovery Steps:**
1. Review configuration: `python organize.py config --show`
2. Edit config: `python organize.py config --edit`
3. Check config.example.json for valid structure
4. Reset to defaults if needed

---

### E005: Scan Interrupted
**Category:** Internal  
**Severity:** Warning  
**Description:** File scan was interrupted before completion

**Common Causes:**
- Application crash
- User interruption (Ctrl+C)
- System shutdown

**Recovery Steps:**
1. Restart application - it will detect the interruption
2. Choose recovery option:
   - Resume scan from where it left off
   - Start new scan
   - Enter safe mode for diagnostics

---

### E006: Database Error
**Category:** Database  
**Severity:** Error  
**Description:** Database operation failed

**Common Causes:**
- Database file corrupted
- Permission denied
- Disk full
- Concurrent access issue

**Recovery Steps:**
1. Check database file permissions
2. Verify disk space
3. Try running with `--safe-mode` flag
4. If corrupted, backup and delete database file (will be recreated)

## Features

### Auto-Retry with Exponential Backoff
Network errors are automatically retried with increasing delays:
- Attempt 1: Immediate
- Attempt 2: 1 second delay
- Attempt 3: 2 seconds delay
- Maximum: 30 seconds delay

### Offline Mode Detection
- Automatically detects when AI provider is offline
- Falls back to rule-based organization
- Queues operations for retry when connection restored

### Crash Recovery
On startup, the application:
1. Detects if previous session crashed
2. Shows incident reconstruction
3. Offers recovery options:
   - Clear and continue
   - Enter safe mode
   - View crash details

### Safe Mode
Start with minimal functionality for diagnostics:
```bash
python organize.py scan /path --safe-mode
```

Safe mode disables:
- AI provider
- Auto-retry
- Background operations

### Error Details Export
Copy full error details for support:
```bash
# During interactive mode
Choose "Copy error details to clipboard"

# Or save to file
python organize.py scan /path 2>&1 | tee error.log
```

### Progressive Disclosure
Error messages show:
- Simple user-friendly message by default
- Technical details on request with `--show-technical-details`
- "Show more" toggle in UI

## Command Line Options

### Error-Related Flags
- `--safe-mode` - Run in safe mode
- `--show-technical-details` - Show technical error details
- `--verbose` - Enable detailed logging

### Crash Recovery Commands
```bash
# View crash history
ls ~/.organizer/state/crash.log

# Clear incomplete scan state
rm ~/.organizer/state/current_scan.json

# Exit safe mode
rm ~/.organizer/state/recovery_state.json
```

## Best Practices

### For Users
1. Always check error recovery suggestions first
2. Use `--verbose` flag to get more context
3. Copy error details before reporting issues
4. Try safe mode if normal mode fails

### For Developers
1. Use appropriate error categories
2. Provide actionable recovery suggestions
3. Include relevant technical context
4. Test error paths thoroughly

## Getting Help

### Documentation
- [Installation Guide](INSTALLATION.md)
- [Usage Guide](USAGE.md)
- [Configuration Reference](CONFIGURATION.md)

### Support Channels
- GitHub Issues: Report bugs and feature requests
- Discussions: Ask questions and share tips
- Wiki: Detailed troubleshooting guides

### Error Report Template
When reporting errors, include:
1. Error code and message
2. Technical details (use `--show-technical-details`)
3. Steps to reproduce
4. System information (OS, Python version, etc.)
5. Relevant configuration (redact sensitive info)

## Recovery Workflows

### Scenario 1: AI Provider Unavailable
```
❌ Error [E001]: Unable to connect to Ollama
```
1. Check if Ollama is running
2. If not available, system automatically uses rule-based organization
3. No manual intervention required

### Scenario 2: Permission Denied
```
❌ Error [E003]: File system error during move file
```
1. Note the file path from error details
2. Check permissions: `ls -la /path/to/file`
3. Grant permissions: `chmod +rw /path/to/file`
4. Retry operation

### Scenario 3: Application Crash
```
⚠️  Previous session did not complete normally
Scan #42: 150/200 files processed
```
1. Review incident reconstruction
2. Choose to resume or start fresh
3. If issues persist, use safe mode

### Scenario 4: Configuration Error
```
❌ Error [E004]: Configuration error for 'ai.model'
```
1. Edit config: `python organize.py config --edit`
2. Fix the issue based on error message
3. Verify: `python organize.py config --show`
4. Retry operation

## Technical Details

### Error Structure
Each error contains:
- **code**: Unique error code (E001-E999)
- **message**: User-friendly message
- **category**: Error classification
- **severity**: Error severity level
- **technical_details**: Technical context (optional)
- **recovery_suggestions**: Actionable recovery steps
- **help_url**: Link to detailed documentation

### Retry Logic
```python
RetryConfig(
    max_attempts=3,        # Maximum retry attempts
    initial_delay=1.0,     # Initial delay in seconds
    max_delay=30.0,        # Maximum delay
    exponential_base=2.0,  # Backoff multiplier
    jitter=True            # Add randomization
)
```

### State Recovery
The system tracks:
- Current scan progress
- Interrupted operations
- Crash information
- Recovery mode state

Files stored in `~/.organizer/state/`:
- `current_scan.json` - Active scan state
- `crash.log` - Crash history
- `recovery_state.json` - Safe mode flag

## See Also

- [Architecture Overview](ARCHITECTURE.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Testing Guide](TESTING.md)
