#!/usr/bin/env python3
"""
Configuration Management System for MCP Server
Centralizes all configuration with validation and environment overrides
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict


@dataclass
class MemoryConfig:
    """Memory tool configuration"""
    storage_file: str = "data/memory_store.json"
    auto_backup: bool = True
    backup_interval_hours: int = 24
    max_memory_size_mb: int = 100
    default_importance: float = 0.5


@dataclass
class SessionConfig:
    """Session management configuration"""
    sessions_dir: str = "data/sessions"
    auto_memory_formation: bool = True
    max_session_duration_hours: int = 24
    cleanup_old_sessions_days: int = 30


@dataclass
class SecurityConfig:
    """Security settings"""
    enable_shell_access: bool = True
    enable_web_access: bool = True
    max_file_size_mb: int = 100
    allowed_shell_commands: Optional[list] = None
    blocked_file_patterns: Optional[list] = None
    max_execution_time_seconds: int = 30


@dataclass
class AutomationConfig:
    """Intelligent automation configuration"""
    enable_pattern_detection: bool = True
    pattern_detection_window: int = 10
    min_pattern_frequency: int = 3
    automation_confidence_threshold: float = 0.7
    max_stored_patterns: int = 100
    pattern_retention_days: int = 30
    enable_adaptive_learning: bool = True


@dataclass
class PerformanceConfig:
    """Performance and resource limits"""
    max_concurrent_tools: int = 5
    memory_limit_mb: int = 512
    disk_cache_size_mb: int = 256
    log_retention_days: int = 7


@dataclass
class IntegrationConfig:
    """External integration configuration — webhooks, SSE, ChatGPT, Claude, certs"""
    # Webhook engine
    enable_webhooks: bool = True
    webhook_max_retries: int = 3
    webhook_timeout_seconds: float = 10.0
    # SSE broadcaster
    enable_sse: bool = True
    sse_heartbeat_seconds: int = 30
    # ChatGPT Custom GPT Actions
    chatgpt_plugin_name: str = "Sovereign MCP"
    chatgpt_plugin_description: str = "Neural MCP tool server"
    chatgpt_contact_email: str = "admin@sovereign-mcp.local"
    # MCP Streamable HTTP transport
    enable_mcp_streamable_http: bool = True
    # External TLS certificates (Let's Encrypt / custom CA)
    external_cert_file: str = ""
    external_key_file: str = ""
    # CORS
    cors_allow_all: bool = False


@dataclass
class MCPServerConfig:
    """Complete MCP Server configuration"""
    memory: MemoryConfig
    sessions: SessionConfig
    security: SecurityConfig
    automation: AutomationConfig
    performance: PerformanceConfig
    integration: IntegrationConfig
    debug_mode: bool = False
    log_level: str = "INFO"
    data_directory: str = "data"


class ConfigManager:
    """Manages MCP server configuration with validation and environment overrides"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.logger = logging.getLogger(__name__)
        self._config: MCPServerConfig = None  # type: ignore
        self.load_config()
    
    def load_config(self) -> MCPServerConfig:
        """Load configuration from file with environment overrides"""
        # Default configuration
        default_config = MCPServerConfig(
            memory=MemoryConfig(),
            sessions=SessionConfig(),
            security=SecurityConfig(blocked_file_patterns=[
                "*.exe", "*.dll", "*.so", "*.dylib", "/etc/passwd", "/etc/shadow"
            ]),
            automation=AutomationConfig(),
            performance=PerformanceConfig(),
            integration=IntegrationConfig(),
        )
        
        # Load from file if exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                
                # Merge with defaults
                config_dict = asdict(default_config)
                self._deep_merge(config_dict, file_config)
                
                # Reconstruct config objects
                self._config = MCPServerConfig(
                    memory=MemoryConfig(**config_dict['memory']),
                    sessions=SessionConfig(**config_dict['sessions']),
                    security=SecurityConfig(**config_dict['security']),
                    automation=AutomationConfig(**config_dict['automation']),
                    performance=PerformanceConfig(**config_dict['performance']),
                    integration=IntegrationConfig(**config_dict.get('integration', {})),
                    debug_mode=config_dict['debug_mode'],
                    log_level=config_dict['log_level'],
                    data_directory=config_dict['data_directory']
                )
                
            except Exception as e:
                self.logger.error(f"Error loading config file: {e}. Using defaults.")
                self._config = default_config
        else:
            self._config = default_config
        
        # Apply environment overrides
        self._apply_env_overrides()
        
        # Validate configuration
        self._validate_config()
        
        return self._config
    
    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Deep merge override dict into base dict"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides"""
        env_mappings = {
            'MCP_DEBUG': ('debug_mode', lambda x: x.lower() == 'true'),
            'MCP_LOG_LEVEL': ('log_level', str),
            'MCP_DATA_DIR': ('data_directory', str),
            'MCP_MEMORY_FILE': ('memory.storage_file', str),
            'MCP_MAX_FILE_SIZE': ('security.max_file_size_mb', int),
            'MCP_SHELL_ACCESS': ('security.enable_shell_access', lambda x: x.lower() == 'true'),
            'MCP_WEB_ACCESS': ('security.enable_web_access', lambda x: x.lower() == 'true'),
            'MCP_EXTERNAL_CERT': ('integration.external_cert_file', str),
            'MCP_EXTERNAL_KEY': ('integration.external_key_file', str),
            'MCP_ENABLE_WEBHOOKS': ('integration.enable_webhooks', lambda x: x.lower() == 'true'),
            'MCP_ENABLE_SSE': ('integration.enable_sse', lambda x: x.lower() == 'true'),
        }
        
        for env_var, (config_path, converter) in env_mappings.items():
            if env_var in os.environ:
                try:
                    value = converter(os.environ[env_var])
                    self._set_nested_attr(self._config, config_path, value)
                    self.logger.info(f"Applied environment override: {env_var} = {value}")
                except Exception as e:
                    self.logger.error(f"Invalid environment variable {env_var}: {e}")
    
    def _set_nested_attr(self, obj: Any, path: str, value: Any) -> None:
        """Set nested attribute using dot notation"""
        parts = path.split('.')
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)
    
    def _validate_config(self) -> None:
        """Validate configuration values"""
        config = self._config
        
        # Validate memory settings
        if config.memory.max_memory_size_mb < 1:
            raise ValueError("Memory size must be at least 1MB")
        
        # Validate security settings
        if config.security.max_file_size_mb < 1:
            raise ValueError("Max file size must be at least 1MB")
        
        if config.security.max_execution_time_seconds < 1:
            raise ValueError("Max execution time must be at least 1 second")
        
        # Validate automation settings
        if config.automation.pattern_detection_window < 1:
            raise ValueError("Pattern detection window must be at least 1")
        
        if config.automation.automation_confidence_threshold < 0 or config.automation.automation_confidence_threshold > 1:
            raise ValueError("Automation confidence threshold must be between 0 and 1")
        
        # Validate performance settings
        if config.performance.max_concurrent_tools < 1:
            raise ValueError("Must allow at least 1 concurrent tool")
        
        # Create data directory
        Path(config.data_directory).mkdir(exist_ok=True)
        
        self.logger.info("Configuration validation passed")
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self._config), f, indent=2)
            self.logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
    
    @property
    def config(self) -> MCPServerConfig:
        """Get current configuration"""
        return self._config
    
    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """Get configuration specific to a tool"""
        tool_configs = {
            'memory': asdict(self._config.memory),
            'sessions': asdict(self._config.sessions),
            'security': asdict(self._config.security),
            'automation': asdict(self._config.automation),
            'performance': asdict(self._config.performance)
        }
        
        # Add common config
        common_config = {
            'debug_mode': self._config.debug_mode,
            'data_directory': self._config.data_directory,
            'log_level': self._config.log_level
        }
        
        # Merge tool-specific and common config
        result = common_config.copy()
        if tool_name in tool_configs:
            result.update(tool_configs[tool_name])
        
        return result


# Global config manager instance
_config_manager = None

def get_config() -> MCPServerConfig:
    """Get global configuration instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.config

def get_tool_config(tool_name: str) -> Dict[str, Any]:
    """Get tool-specific configuration"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.get_tool_config(tool_name)


# For standalone testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test configuration management
    config_manager = ConfigManager()
    config = config_manager.config
    
    print("Current configuration:")
    print(f"Debug mode: {config.debug_mode}")
    print(f"Data directory: {config.data_directory}")
    print(f"Memory file: {config.memory.storage_file}")
    print(f"Shell access: {config.security.enable_shell_access}")
    
    # Test tool-specific config
    memory_config = config_manager.get_tool_config('memory')
    print(f"\nMemory tool config: {memory_config}")
