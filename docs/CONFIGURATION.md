# Configuration Integration Documentation

This document describes how the `config.json` file is integrated into the API Server Management System and which configuration keys are used by which modules.

## Overview

The application uses a centralized configuration system based on `config.json` located in the `data/` directory. All modules access configuration through the `ConfigManager` singleton pattern implemented in `src/core/config_manager.py`.

## Configuration Manager

### Core Functions

- `get_config_manager()`: Returns the singleton ConfigManager instance
- `get_config()`: Returns the complete configuration dictionary
- `get_config_value(key_path, default)`: Gets a specific configuration value using dot notation

### Usage Example

```python
from src.core.config_manager import get_config_value

# Get a specific value
host = get_config_value("server.host", "localhost")

# Get nested values
jwt_secret = get_config_value("security.jwt_secret_key", "default-secret")
```

## Configuration Mappings by Module

### 1. Application (`src/app.py`)

**Configuration Keys Used:**
- `app.debug` → Debug mode for Qt application
- `ui.show_splash_screen` → Whether to show splash screen on startup
- `ui.splash_screen_duration` → Splash screen display duration (ms)
- `ui.window_width` → Main window width
- `ui.window_height` → Main window height
- `ui.window_min_width` → Main window minimum width
- `ui.window_min_height` → Main window minimum height
- `ui.theme` → Application theme (dark/light)

**Functions:**
- `_create_application()`: Uses `app.debug` for high DPI scaling
- `_show_splash_screen()`: Uses `ui.show_splash_screen` and `ui.splash_screen_duration`
- `_create_main_window()`: Uses window dimensions from `ui.*`
- `_apply_theme()`: Uses `ui.theme` for QSS theme loading

### 2. Server Manager (`src/api/server_manager.py`)

**Configuration Keys Used:**
- `server.host` → Server bind host address
- `server.port` → Server port number
- `server.ssl` → SSL/TLS enabled flag
- `server.ssl_cert_path` → SSL certificate file path
- `server.ssl_key_path` → SSL private key file path
- `server.max_connections` → Maximum concurrent connections
- `server.timeout` → Request timeout in seconds

**Classes:**
- `ServerWorker.__init__()`: Loads server connection settings
- `APIServerManager.__init__()`: Loads server connection settings
- `_create_application()`: Applies max_connections and timeout to aiohttp app

### 3. CORS Middleware (`src/api/middlewares/cors_middleware.py`)

**Configuration Keys Used:**
- `server.cors_origins` → Allowed CORS origins list
- `server.cors_methods` → Allowed HTTP methods list
- `server.cors_headers` → Allowed HTTP headers list

**Classes:**
- `CORSMiddleware.__init__()`: Loads CORS configuration from server settings

### 4. Security Manager (`src/core/security.py`)

**Configuration Keys Used:**
- `security.jwt_secret_key` → JWT signing secret key
- `security.jwt_algorithm` → JWT signing algorithm
- `security.jwt_access_token_expire_minutes` → Access token expiration
- `security.jwt_refresh_token_expire_days` → Refresh token expiration
- `security.max_login_attempts` → Maximum failed login attempts
- `security.lockout_duration_minutes` → Account lockout duration
- `security.password_min_length` → Minimum password length
- `security.password_require_uppercase` → Require uppercase letters
- `security.password_require_lowercase` → Require lowercase letters
- `security.password_require_numbers` → Require numbers
- `security.password_require_special_chars` → Require special characters
- `security.bcrypt_rounds` → bcrypt hashing rounds

**Classes:**
- `SecurityManager.__init__()`: Loads all security configuration
- `hash_password()`: Uses `bcrypt_rounds` for password hashing
- `validate_password_strength()`: Uses password requirements

### 5. Rate Limiting Middleware (`src/api/middlewares/rate_limit.py`)

**Configuration Keys Used:**
- `rate_limiting.enabled` → Enable/disable rate limiting
- `rate_limiting.requests_per_minute` → Requests per minute limit
- `rate_limiting.burst_size` → Burst request allowance
- `rate_limiting.per_ip_limit` → Enable per-IP limiting
- `rate_limiting.per_user_limit` → Enable per-user limiting

**Classes:**
- `RateLimitMiddleware.__init__()`: Loads rate limiting configuration

### 6. Database Manager (`src/db/database.py`)

**Configuration Keys Used:**
- `database` → Database connection URL/string

**Classes:**
- `DatabaseManager.__init__()`: Uses database URL for SQLite connection

### 7. Backup Service (`src/services/backup_service.py`)

**Configuration Keys Used:**
- `backup.enabled` → Enable automatic backups
- `backup.interval_hours` → Backup interval in hours
- `backup.retention_days` → Number of days to keep backups
- `backup.compress` → Compress backup files
- `backup.include_logs` → Include log files in backups
- `backup.include_config` → Include config files in backups

**Classes:**
- `BackupService.__init__()`: Loads backup configuration settings

### 8. Logger (`src/utils/logger.py`)

**Configuration Keys Used:**
- `logging.file_max_size` → Maximum log file size in bytes
- `logging.file_backup_count` → Number of backup log files to keep

**Classes:**
- `Logger._setup_file_handlers()`: Uses file size and backup count settings
- `Logger._setup_error_handler()`: Uses file size and backup count settings

### 9. Main Window (`src/ui/main_window.py`)

**Configuration Keys Used:**
- `ui.window_min_width` → Minimum window width
- `ui.window_min_height` → Minimum window height
- `ui.window_width` → Default window width
- `ui.window_height` → Default window height
- `ui.auto_refresh_interval` → UI refresh interval in milliseconds
- `ui.always_on_top` → Keep window always on top
- `ui.theme` → UI theme selection

**Functions:**
- `_init_ui()`: Uses window dimensions
- `_setup_timer()`: Uses auto-refresh interval
- `_center_window()`: Uses always_on_top setting
- `load_theme()`: Uses theme setting

## Configuration File Structure

The `config.json` file follows this structure:

```json
{
  "app": {
    "name": "API Server Management System",
    "version": "1.0.0",
    "debug": false
  },
  "server": {
    "host": "localhost",
    "port": 8080,
    "ssl": false,
    "ssl_cert_path": "",
    "ssl_key_path": "",
    "max_connections": 1000,
    "timeout": 30,
    "cors_origins": ["*"],
    "cors_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "cors_headers": ["Content-Type", "Authorization"]
  },
  "security": {
    "jwt_secret_key": "your-secret-key",
    "jwt_algorithm": "HS256",
    "jwt_access_token_expire_minutes": 30,
    "jwt_refresh_token_expire_days": 7,
    "bcrypt_rounds": 12,
    "password_min_length": 8,
    "password_require_uppercase": true,
    "password_require_lowercase": true,
    "password_require_numbers": true,
    "password_require_special_chars": true,
    "max_login_attempts": 5,
    "lockout_duration_minutes": 15
  },
  "rate_limiting": {
    "enabled": true,
    "requests_per_minute": 100,
    "burst_size": 20,
    "per_ip_limit": true,
    "per_user_limit": true
  },
  "database": "sqlite:///data/app.db",
  "backup": {
    "enabled": true,
    "interval_hours": 24,
    "retention_days": 30,
    "compress": true,
    "include_logs": true,
    "include_config": true
  },
  "logging": {
    "level": 20,
    "file_max_size": 10485760,
    "file_backup_count": 5
  },
  "ui": {
    "theme": "dark",
    "language": "tr",
    "auto_refresh_interval": 8000,
    "window_width": 1360,
    "window_height": 840,
    "window_min_width": 800,
    "window_min_height": 600,
    "remember_window_state": true,
    "always_on_top": false,
    "show_splash_screen": true,
    "splash_screen_duration": 3000
  }
}
```

## Dynamic Configuration Updates

The configuration system supports dynamic updates through the `ConfigManager`:

```python
from src.core.config_manager import get_config_manager

config_manager = get_config_manager()

# Update a single value
config_manager.set_config_value("server.port", 9090)

# Update multiple values
updates = {
    "server": {
        "host": "0.0.0.0",
        "port": 9090
    }
}
config_manager.update_config(updates)
```

## Validation

The `ConfigManager` includes validation for critical configuration values:

- Server port must be between 1-65535
- JWT secret key must be at least 32 characters
- Log level must be a valid logging level

## Backup and Restore

Configuration files are automatically backed up when changes are made. The system maintains:

- Automatic backup before each configuration change
- Timestamped backup files in `data/backup/`
- Configuration validation before applying changes
- Rollback capability through backup restore

## Best Practices

1. **Always use `get_config_value()`** with appropriate defaults
2. **Validate configuration values** before using them
3. **Use dot notation** for nested configuration access
4. **Provide meaningful defaults** for all configuration values
5. **Document configuration changes** in this file when adding new keys

## Error Handling

The configuration system handles errors gracefully:

- Missing configuration files are created with defaults
- Invalid JSON is handled with fallback to defaults
- Missing configuration keys return provided default values
- Configuration validation errors are logged and reported