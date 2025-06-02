"""Concrete implementation of configuration interface."""

import json
import os
from typing import Any, Dict, Optional, List
from pathlib import Path

from app.core.interfaces import ConfigurationInterface


class ConfigurationService(ConfigurationInterface):
    """Concrete implementation of configuration service."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self._config: Dict[str, Any] = {}
        self._config_path = config_path
        self._environment = os.getenv("ENVIRONMENT", "development")
        
        if config_path and config_path.exists():
            self.load_from_file(config_path)
        else:
            self._load_defaults()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self._config.get(section, {})
    
    def load_from_file(self, path: Path) -> None:
        """Load configuration from file."""
        if path.suffix == '.json':
            with open(path, 'r') as f:
                self._config = json.load(f)
        elif path.suffix in ['.yaml', '.yml']:
            # Add YAML support if needed
            raise NotImplementedError("YAML configuration not yet supported")
        else:
            raise ValueError(f"Unsupported configuration file type: {path.suffix}")
    
    def save_to_file(self, path: Path) -> None:
        """Save configuration to file."""
        with open(path, 'w') as f:
            json.dump(self._config, f, indent=2)
    
    def merge(self, config: Dict[str, Any]) -> None:
        """Merge configuration with existing."""
        self._deep_merge(self._config, config)
    
    def validate(self) -> bool:
        """Validate configuration integrity."""
        # Add validation logic based on schema
        required_sections = ['api', 'data', 'strategies']
        return all(section in self._config for section in required_sections)
    
    def get_environment(self) -> str:
        """Get current environment (dev, test, prod)."""
        return self._environment
    
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all configuration keys."""
        keys = []
        self._collect_keys(self._config, keys, prefix or '')
        return keys
    
    def reload(self) -> None:
        """Reload configuration from source."""
        if self._config_path and self._config_path.exists():
            self.load_from_file(self._config_path)
        else:
            self._load_defaults()
    
    def _deep_merge(self, base: Dict, update: Dict) -> None:
        """Deep merge two dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _collect_keys(self, config: Dict, keys: List[str], prefix: str) -> None:
        """Recursively collect all keys."""
        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.append(full_key)
            if isinstance(value, dict):
                self._collect_keys(value, keys, full_key)
    
    def _load_defaults(self) -> None:
        """Load default configuration."""
        self._config = {
            "api": {
                "host": "127.0.0.1",
                "port": 8000,
                "reload": False,
                "workers": 1,
            },
            "data": {
                "base_path": "csv",
                "cache_enabled": True,
                "cache_ttl": 3600,
            },
            "strategies": {
                "ma_cross": {
                    "default_fast_period": 10,
                    "default_slow_period": 20,
                },
                "execution": {
                    "timeout": 3600,
                    "max_workers": 4,
                },
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        }