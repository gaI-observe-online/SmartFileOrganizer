"""Configuration management for SmartFileOrganizer."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration manager for SmartFileOrganizer."""
    
    DEFAULT_CONFIG_NAME = "config.json"
    DEFAULT_ORGANIZER_DIR = ".organizer"
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to config file. If None, uses default locations.
        """
        self.config_path = self._resolve_config_path(config_path)
        self.config: Dict[str, Any] = {}
        self.load()
    
    def _resolve_config_path(self, config_path: Optional[Path]) -> Path:
        """Resolve configuration file path.
        
        Priority:
        1. Provided config_path
        2. SMARTFILE_CONFIG environment variable
        3. ~/.organizer/config.json
        4. ./config.json
        """
        if config_path:
            return Path(config_path)
        
        env_config = os.getenv("SMARTFILE_CONFIG")
        if env_config:
            return Path(env_config)
        
        home_config = Path.home() / self.DEFAULT_ORGANIZER_DIR / self.DEFAULT_CONFIG_NAME
        if home_config.exists():
            return home_config
        
        local_config = Path(self.DEFAULT_CONFIG_NAME)
        if local_config.exists():
            return local_config
        
        # Default to home config (will be created if needed)
        return home_config
    
    def load(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = self._get_default_config()
            self.save()
    
    def save(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'ai.models.ollama.endpoint')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'ai.models.ollama.endpoint')
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
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
                        "enabled": False
                    },
                    "anthropic": {
                        "api_key": "",
                        "model": "claude-3-sonnet-20240229",
                        "enabled": False
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
                "create_date_folders": False,
                "backup_before_move": True,
                "dry_run": False,
                "auto_approve_threshold": 30,
                "ignore_hidden": True
            },
            "backup": {
                "enabled": True,
                "max_operations": 100,
                "max_size_mb": 5000,
                "skip_large_files_mb": 500,
                "retention_days": 30
            },
            "privacy": {
                "no_external_communication": True,
                "redact_sensitive_in_logs": True,
                "sensitive_patterns": ["SSN", "CreditCard", "APIKey", "Password", "Email", "Phone"]
            },
            "watch": {
                "enabled": False,
                "batch_interval_seconds": 300,
                "auto_approve_low_risk": True,
                "queue_medium_risk": True,
                "queue_high_risk": True
            },
            "learning": {
                "enabled": True,
                "suggest_threshold": 10,
                "auto_apply_threshold": 20,
                "min_confidence": 0.80
            },
            "web": {
                "port": 8001,
                "host": "127.0.0.1",
                "auto_open_browser": True
            }
        }
    
    @property
    def organizer_dir(self) -> Path:
        """Get .organizer directory path."""
        return Path.home() / self.DEFAULT_ORGANIZER_DIR
    
    def ensure_organizer_dir(self) -> None:
        """Ensure .organizer directory exists."""
        self.organizer_dir.mkdir(parents=True, exist_ok=True)
