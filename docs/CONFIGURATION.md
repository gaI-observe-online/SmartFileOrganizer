# Configuration Reference

## Configuration File Location

SmartFileOrganizer looks for configuration in the following order:

1. Path specified with `--config` flag
2. `SMARTFILE_CONFIG` environment variable
3. `~/.organizer/config.json`
4. `./config.json`

## Complete Configuration

```json
{
  "version": "1.0.0",
  "ai": {
    "primary": "ollama",
    "fallback": "rule-based",
    "models": {
      "ollama": {
        "endpoint": "http://localhost:11434",
        "model": "llama3.3",
        "fallback_model": "qwen2.5",
        "timeout": 30
      },
      "openai": {
        "api_key": "",
        "model": "gpt-4o-mini",
        "enabled": false
      },
      "anthropic": {
        "api_key": "",
        "model": "claude-3-sonnet-20240229",
        "enabled": false
      }
    }
  },
  "rules": {
    "documents": {
      "extensions": [".pdf", ".doc", ".docx", ".txt", ".md"],
      "folder": "Documents"
    },
    "images": {
      "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
      "folder": "Images"
    },
    "code": {
      "extensions": [".py", ".js", ".java", ".cpp", ".c", ".h", ".go", ".rs"],
      "folder": "Code"
    },
    "videos": {
      "extensions": [".mp4", ".avi", ".mkv", ".mov", ".wmv"],
      "folder": "Videos"
    },
    "audio": {
      "extensions": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
      "folder": "Audio"
    },
    "archives": {
      "extensions": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
      "folder": "Archives"
    },
    "finance": {
      "extensions": [".xlsx", ".xls", ".csv"],
      "folder": "Finance",
      "keywords": ["invoice", "receipt", "statement", "tax", "payment"]
    }
  },
  "preferences": {
    "create_date_folders": false,
    "backup_before_move": true,
    "dry_run": false,
    "auto_approve_threshold": 30,
    "ignore_hidden": true
  },
  "backup": {
    "enabled": true,
    "max_operations": 100,
    "max_size_mb": 5000,
    "skip_large_files_mb": 500,
    "retention_days": 30
  },
  "privacy": {
    "no_external_communication": true,
    "redact_sensitive_in_logs": true,
    "sensitive_patterns": ["SSN", "CreditCard", "APIKey", "Password", "Email", "Phone"]
  },
  "watch": {
    "enabled": false,
    "batch_interval_seconds": 300,
    "auto_approve_low_risk": true,
    "queue_medium_risk": true,
    "queue_high_risk": true
  },
  "learning": {
    "enabled": true,
    "suggest_threshold": 10,
    "auto_apply_threshold": 20,
    "min_confidence": 0.80
  }
}
```

## Configuration Sections

### AI Configuration

#### `ai.primary`

**Type:** String  
**Default:** `"ollama"`  
**Options:** `"ollama"`, `"openai"`, `"anthropic"`, `"rule-based"`

Primary AI provider for file organization.

```json
{
  "ai": {
    "primary": "ollama"
  }
}
```

#### `ai.fallback`

**Type:** String  
**Default:** `"rule-based"`  
**Options:** `"rule-based"`, AI provider name

Fallback method if primary AI fails.

#### `ai.models.ollama`

Ollama configuration:

```json
{
  "ollama": {
    "endpoint": "http://localhost:11434",  // Ollama API endpoint
    "model": "llama3.3",                   // Primary model
    "fallback_model": "qwen2.5",           // Fallback model
    "timeout": 30                          // Request timeout (seconds)
  }
}
```

#### `ai.models.openai`

OpenAI configuration (admin-enabled only):

```json
{
  "openai": {
    "api_key": "sk-xxxxx",      // Your OpenAI API key
    "model": "gpt-4o-mini",     // Model to use
    "enabled": false            // Must be explicitly enabled
  }
}
```

#### `ai.models.anthropic`

Anthropic configuration (admin-enabled only):

```json
{
  "anthropic": {
    "api_key": "sk-ant-xxxxx",            // Your Anthropic API key
    "model": "claude-3-sonnet-20240229",  // Model to use
    "enabled": false                      // Must be explicitly enabled
  }
}
```

### Rules Configuration

Define file categorization rules:

```json
{
  "rules": {
    "category_name": {
      "extensions": [".ext1", ".ext2"],  // File extensions
      "folder": "FolderName",            // Target folder
      "keywords": ["keyword1"]           // Optional keywords
    }
  }
}
```

**Example: Custom Category**

```json
{
  "rules": {
    "design": {
      "extensions": [".psd", ".ai", ".sketch", ".fig"],
      "folder": "Design"
    }
  }
}
```

### Preferences

#### `preferences.create_date_folders`

**Type:** Boolean  
**Default:** `false`

Create date-based subfolders (e.g., `2024-12-31`).

```json
{
  "preferences": {
    "create_date_folders": true
  }
}
```

Result: `Documents/Work/2024-12-31/report.pdf`

#### `preferences.backup_before_move`

**Type:** Boolean  
**Default:** `true`

Create backups before moving files.

#### `preferences.dry_run`

**Type:** Boolean  
**Default:** `false`

Global dry-run mode (preview only, no changes).

#### `preferences.auto_approve_threshold`

**Type:** Integer (0-100)  
**Default:** `30`

Auto-approve files with risk score ≤ threshold.

- `0`: Require approval for all files
- `30`: Auto-approve low-risk only
- `70`: Auto-approve low and medium risk
- `100`: Auto-approve everything (not recommended)

```json
{
  "preferences": {
    "auto_approve_threshold": 50
  }
}
```

#### `preferences.ignore_hidden`

**Type:** Boolean  
**Default:** `true`

Skip hidden files (starting with `.`).

### Backup Configuration

#### `backup.enabled`

**Type:** Boolean  
**Default:** `true`

Enable backup system.

#### `backup.max_operations`

**Type:** Integer  
**Default:** `100`

Maximum number of operations to keep backups for.

#### `backup.max_size_mb`

**Type:** Integer (MB)  
**Default:** `5000`

Maximum total backup size (5GB default).

#### `backup.skip_large_files_mb`

**Type:** Integer (MB)  
**Default:** `500`

Files larger than this use metadata-only backup.

#### `backup.retention_days`

**Type:** Integer  
**Default:** `30`

Auto-delete backups older than this many days.

```json
{
  "backup": {
    "enabled": true,
    "max_operations": 50,
    "max_size_mb": 10000,
    "skip_large_files_mb": 1000,
    "retention_days": 60
  }
}
```

### Privacy Configuration

#### `privacy.no_external_communication`

**Type:** Boolean  
**Default:** `true`

Block all external communication (except admin-enabled AI providers).

#### `privacy.redact_sensitive_in_logs`

**Type:** Boolean  
**Default:** `true`

Automatically redact sensitive data in logs.

#### `privacy.sensitive_patterns`

**Type:** Array of Strings  
**Default:** `["SSN", "CreditCard", "APIKey", "Password", "Email", "Phone"]`

Patterns to detect and redact.

```json
{
  "privacy": {
    "redact_sensitive_in_logs": true,
    "sensitive_patterns": ["SSN", "CreditCard", "CustomPattern"]
  }
}
```

### Watch Mode Configuration

#### `watch.enabled`

**Type:** Boolean  
**Default:** `false`

Enable watch mode on startup.

#### `watch.batch_interval_seconds`

**Type:** Integer  
**Default:** `300` (5 minutes)

Batch collection interval.

#### `watch.auto_approve_low_risk`

**Type:** Boolean  
**Default:** `true`

Auto-approve low-risk files in watch mode.

#### `watch.queue_medium_risk`

**Type:** Boolean  
**Default:** `true`

Queue medium-risk files for review.

#### `watch.queue_high_risk`

**Type:** Boolean  
**Default:** `true`

Queue high-risk files for review.

### Learning Configuration

#### `learning.enabled`

**Type:** Boolean  
**Default:** `true`

Enable learning system.

#### `learning.suggest_threshold`

**Type:** Integer  
**Default:** `10`

Suggest learned rules after this many consistent approvals.

#### `learning.auto_apply_threshold`

**Type:** Integer  
**Default:** `20`

Offer to auto-apply rules after this many consistent approvals.

#### `learning.min_confidence`

**Type:** Float (0.0-1.0)  
**Default:** `0.80`

Minimum confidence for learned patterns (80%).

## Configuration Examples

### Minimal Configuration

```json
{
  "version": "1.0.0",
  "preferences": {
    "auto_approve_threshold": 30
  }
}
```

### High Security

```json
{
  "preferences": {
    "auto_approve_threshold": 0,
    "backup_before_move": true
  },
  "privacy": {
    "no_external_communication": true,
    "redact_sensitive_in_logs": true
  }
}
```

### Maximum Automation

```json
{
  "preferences": {
    "auto_approve_threshold": 70,
    "create_date_folders": true
  },
  "watch": {
    "enabled": true,
    "batch_interval_seconds": 60,
    "auto_approve_low_risk": true
  }
}
```

### Development Mode

```json
{
  "preferences": {
    "dry_run": true,
    "auto_approve_threshold": 0
  },
  "backup": {
    "enabled": false
  }
}
```

## Environment Variables

### `SMARTFILE_CONFIG`

Path to configuration file:

```bash
export SMARTFILE_CONFIG=/custom/path/config.json
python organize.py scan ~/Downloads
```

### `OLLAMA_HOST`

Override Ollama endpoint:

```bash
export OLLAMA_HOST=http://localhost:11434
```

## Configuration Management

### View Current Configuration

```bash
python organize.py config --show
```

### Edit Configuration

```bash
python organize.py config --edit
```

### Set Values Programmatically

```python
from smartfile.core.config import Config

config = Config()
config.set('preferences.auto_approve_threshold', 50)
config.save()
```

## Configuration Validation

The system validates configuration on load:

- Required fields must exist
- Values must be correct types
- Ranges must be valid (e.g., threshold 0-100)

Invalid configuration falls back to defaults.

## Migration

When upgrading, configuration is automatically migrated:

1. Backup current config
2. Add new fields with defaults
3. Preserve existing values
4. Update version number

## Best Practices

1. **Keep Backups** - Always backup your config before major changes
2. **Test Changes** - Use `--dry-run` after config changes
3. **Version Control** - Store config in version control (without API keys)
4. **Document Custom Rules** - Comment your custom categorization rules
5. **Regular Review** - Periodically review and update thresholds
