"""
Server management service for controlling the API server.

This service handles server start/stop/restart operations, configuration management,
and server status monitoring. It integrates with the AioHTTP server manager.
"""

import asyncio
import subprocess
import psutil
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from .base_service import BaseService
from ..db.models import Server, SystemLog
from ..core.settings import settings
from ..core.constants import ServerStatus, LogLevel
from ..utils.logger import logger


class ServerService(BaseService[Server]):
    """
    Service for managing the API server and server operations.
    
    This service provides methods for server control, configuration management,
    and server status monitoring.
    """
    
    def __init__(self):
        """Initialize the server service."""
        super().__init__(Server)
        self.server_process = None
        self.server_status = ServerStatus.OFFLINE
        self.start_time = None
        self.config_file = Path("data/config.json")
    
    async def start_server(self) -> Dict[str, Any]:
        """
        Start the API server.
        
        Returns:
            Dictionary with operation result
        """
        try:
            if self.server_status == ServerStatus.ONLINE:
                return {
                    "success": False,
                    "message": "Server is already running",
                    "status": self.server_status.value
                }
            
            # Update status to starting
            self.server_status = ServerStatus.STARTING
            self.logger.info("Starting API server...")
            
            # Load server configuration
            config = await self._load_server_config()
            if not config:
                self.server_status = ServerStatus.ERROR
                return {
                    "success": False,
                    "message": "Failed to load server configuration",
                    "status": self.server_status.value
                }
            
            # Start the server process
            success = await self._start_server_process(config)
            
            if success:
                self.server_status = ServerStatus.ONLINE
                self.start_time = datetime.now()
                
                # Log server start
                await self._log_server_event("Server started successfully", LogLevel.INFO)
                
                self.logger.info("API server started successfully")
                return {
                    "success": True,
                    "message": "Server started successfully",
                    "status": self.server_status.value,
                    "start_time": self.start_time.isoformat(),
                    "config": config
                }
            else:
                self.server_status = ServerStatus.ERROR
                await self._log_server_event("Failed to start server", LogLevel.ERROR)
                
                return {
                    "success": False,
                    "message": "Failed to start server",
                    "status": self.server_status.value
                }
                
        except Exception as e:
            self.server_status = ServerStatus.ERROR
            self.logger.error(f"Error starting server: {e}")
            await self._log_server_event(f"Server start error: {e}", LogLevel.ERROR)
            
            return {
                "success": False,
                "message": f"Server start error: {e}",
                "status": self.server_status.value
            }
    
    async def stop_server(self) -> Dict[str, Any]:
        """
        Stop the API server.
        
        Returns:
            Dictionary with operation result
        """
        try:
            if self.server_status == ServerStatus.OFFLINE:
                return {
                    "success": False,
                    "message": "Server is already stopped",
                    "status": self.server_status.value
                }
            
            # Update status to stopping
            self.server_status = ServerStatus.STOPPING
            self.logger.info("Stopping API server...")
            
            # Stop the server process
            success = await self._stop_server_process()
            
            if success:
                self.server_status = ServerStatus.OFFLINE
                self.start_time = None
                
                # Log server stop
                await self._log_server_event("Server stopped successfully", LogLevel.INFO)
                
                self.logger.info("API server stopped successfully")
                return {
                    "success": True,
                    "message": "Server stopped successfully",
                    "status": self.server_status.value
                }
            else:
                self.server_status = ServerStatus.ERROR
                await self._log_server_event("Failed to stop server", LogLevel.ERROR)
                
                return {
                    "success": False,
                    "message": "Failed to stop server",
                    "status": self.server_status.value
                }
                
        except Exception as e:
            self.server_status = ServerStatus.ERROR
            self.logger.error(f"Error stopping server: {e}")
            await self._log_server_event(f"Server stop error: {e}", LogLevel.ERROR)
            
            return {
                "success": False,
                "message": f"Server stop error: {e}",
                "status": self.server_status.value
            }
    
    async def restart_server(self) -> Dict[str, Any]:
        """
        Restart the API server.
        
        Returns:
            Dictionary with operation result
        """
        try:
            self.logger.info("Restarting API server...")
            
            # Update status to restarting
            self.server_status = ServerStatus.RESTARTING
            
            # Stop server first
            stop_result = await self.stop_server()
            if not stop_result["success"] and self.server_status != ServerStatus.OFFLINE:
                return {
                    "success": False,
                    "message": f"Failed to stop server: {stop_result['message']}",
                    "status": self.server_status.value
                }
            
            # Wait a moment
            await asyncio.sleep(2)
            
            # Start server
            start_result = await self.start_server()
            
            if start_result["success"]:
                self.logger.info("API server restarted successfully")
                return {
                    "success": True,
                    "message": "Server restarted successfully",
                    "status": self.server_status.value,
                    "start_time": self.start_time.isoformat() if self.start_time else None
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to restart server: {start_result['message']}",
                    "status": self.server_status.value
                }
                
        except Exception as e:
            self.server_status = ServerStatus.ERROR
            self.logger.error(f"Error restarting server: {e}")
            await self._log_server_event(f"Server restart error: {e}", LogLevel.ERROR)
            
            return {
                "success": False,
                "message": f"Server restart error: {e}",
                "status": self.server_status.value
            }
    
    async def get_server_status(self) -> Dict[str, Any]:
        """
        Get current server status and information.
        
        Returns:
            Dictionary with server status information
        """
        try:
            # Get system information
            system_info = await self._get_system_info()
            
            # Get server configuration
            config = await self._load_server_config()
            
            # Calculate uptime
            uptime = None
            if self.start_time and self.server_status == ServerStatus.ONLINE:
                uptime = (datetime.now() - self.start_time).total_seconds()
            
            return {
                "status": self.server_status.value,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "uptime_seconds": uptime,
                "config": config,
                "system_info": system_info,
                "process_info": await self._get_process_info()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting server status: {e}")
            return {
                "status": self.server_status.value,
                "error": str(e)
            }
    
    async def update_server_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update server configuration.
        
        Args:
            config_updates: Dictionary with configuration updates
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Load current configuration
            current_config = await self._load_server_config()
            if not current_config:
                return {
                    "success": False,
                    "message": "Failed to load current configuration"
                }
            
            # Check if server is running
            if self.server_status == ServerStatus.ONLINE:
                return {
                    "success": False,
                    "message": "Cannot update configuration while server is running. Please stop the server first."
                }
            
            # Update configuration
            updated_config = {**current_config, **config_updates}
            
            # Save configuration
            success = await self._save_server_config(updated_config)
            
            if success:
                self.logger.info("Server configuration updated successfully")
                return {
                    "success": True,
                    "message": "Configuration updated successfully",
                    "config": updated_config
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to save configuration"
                }
                
        except Exception as e:
            self.logger.error(f"Error updating server configuration: {e}")
            return {
                "success": False,
                "message": f"Configuration update error: {e}"
            }
    
    async def get_server_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent server logs.
        
        Args:
            limit: Maximum number of log entries to return
            
        Returns:
            List of log entries
        """
        try:
            logs = (SystemLog.select()
                    .where(SystemLog.module == "server")
                    .order_by(SystemLog.created_at.desc())
                    .limit(limit))
            
            log_entries = []
            for log in logs:
                log_entries.append({
                    "id": log.id,
                    "level": log.level,
                    "message": log.message,
                    "created_at": log.created_at.isoformat(),
                    "extra_data": log.extra_data
                })
            
            return log_entries
            
        except Exception as e:
            self.logger.error(f"Error getting server logs: {e}")
            return []
    
    async def _start_server_process(self, config: Dict[str, Any]) -> bool:
        """
        Start the server process.
        
        Args:
            config: Server configuration
            
        Returns:
            True if process started successfully, False otherwise
        """
        try:
            # This is a placeholder for actual server process management
            # In a real implementation, this would start the AioHTTP server
            # For now, we'll simulate the process
            
            self.logger.info(f"Starting server on {config.get('host', '127.0.0.1')}:{config.get('port', 8080)}")
            
            # Simulate server start
            await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting server process: {e}")
            return False
    
    async def _stop_server_process(self) -> bool:
        """
        Stop the server process.
        
        Returns:
            True if process stopped successfully, False otherwise
        """
        try:
            # This is a placeholder for actual server process management
            # In a real implementation, this would stop the AioHTTP server
            
            self.logger.info("Stopping server process...")
            
            # Simulate server stop
            await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping server process: {e}")
            return False
    
    async def _load_server_config(self) -> Optional[Dict[str, Any]]:
        """
        Load server configuration from file.
        
        Returns:
            Server configuration dictionary or None if failed
        """
        try:
            if not self.config_file.exists():
                self.logger.warning("Configuration file not found, using defaults")
                return self._get_default_config()
            
            import json
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            return config.get("server", {})
            
        except Exception as e:
            self.logger.error(f"Error loading server configuration: {e}")
            return None
    
    async def _save_server_config(self, config: Dict[str, Any]) -> bool:
        """
        Save server configuration to file.
        
        Args:
            config: Configuration to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Load full config
            full_config = {}
            if self.config_file.exists():
                import json
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    full_config = json.load(f)
            
            # Update server section
            full_config["server"] = config
            
            # Save config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(full_config, f, indent=4)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving server configuration: {e}")
            return False
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """
        Get system information.
        
        Returns:
            Dictionary with system information
        """
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}"
            }
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return {}
    
    async def _get_process_info(self) -> Dict[str, Any]:
        """
        Get server process information.
        
        Returns:
            Dictionary with process information
        """
        try:
            if not self.server_process:
                return {"status": "not_running"}
            
            # This would return actual process information
            # For now, return placeholder data
            return {
                "status": "running",
                "pid": None,
                "memory_usage": 0,
                "cpu_usage": 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting process info: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default server configuration.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "host": "127.0.0.1",
            "port": 8080,
            "ssl_enabled": False,
            "auto_start": False,
            "max_connections": 1000,
            "timeout": 30
        }
    
    async def _log_server_event(self, message: str, level: LogLevel) -> None:
        """
        Log a server event.
        
        Args:
            message: The log message
            level: The log level
        """
        try:
            SystemLog.create(
                level=level.value,
                module="server",
                message=message,
                created_at=datetime.now()
            )
        except Exception as e:
            self.logger.error(f"Error logging server event: {e}")
    
    async def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate server configuration data.
        
        Args:
            data: The data to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate port
        if "port" in data:
            port = data["port"]
            if not isinstance(port, int) or port < 1 or port > 65535:
                errors.append("Port must be an integer between 1 and 65535")
        
        # Validate host
        if "host" in data:
            host = data["host"]
            if not host or len(host) > 255:
                errors.append("Host must be a valid hostname or IP address")
        
        # Validate SSL settings
        if "ssl_enabled" in data:
            ssl_enabled = data["ssl_enabled"]
            if not isinstance(ssl_enabled, bool):
                errors.append("SSL enabled must be a boolean value")
        
        return errors
