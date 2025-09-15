"""
System utilities for system information, monitoring, and operations.

This module provides utilities for system information gathering,
process monitoring, and system operations.
"""

import os
import sys
import platform
import psutil
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path


class SystemUtils:
    """Utilities for system operations and monitoring."""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """
        Get comprehensive system information.
        
        Returns:
            Dictionary with system information
        """
        return {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'architecture': platform.architecture()[0]
            },
            'python': {
                'version': sys.version,
                'version_info': sys.version_info,
                'executable': sys.executable,
                'path': sys.path
            },
            'environment': {
                'user': os.getenv('USER', os.getenv('USERNAME', 'unknown')),
                'home': os.path.expanduser('~'),
                'cwd': os.getcwd(),
                'path': os.getenv('PATH', ''),
                'pythonpath': os.getenv('PYTHONPATH', '')
            },
            'timestamp': time.time()
        }
    
    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """
        Get CPU information.
        
        Returns:
            Dictionary with CPU information
        """
        try:
            return {
                'count': psutil.cpu_count(),
                'count_logical': psutil.cpu_count(logical=True),
                'count_physical': psutil.cpu_count(logical=False),
                'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                'usage_percent': psutil.cpu_percent(interval=1),
                'usage_per_cpu': psutil.cpu_percent(interval=1, percpu=True),
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """
        Get memory information.
        
        Returns:
            Dictionary with memory information
        """
        try:
            virtual_memory = psutil.virtual_memory()
            swap_memory = psutil.swap_memory()
            
            return {
                'virtual': {
                    'total': virtual_memory.total,
                    'available': virtual_memory.available,
                    'used': virtual_memory.used,
                    'free': virtual_memory.free,
                    'percent': virtual_memory.percent,
                    'cached': getattr(virtual_memory, 'cached', 0),
                    'buffers': getattr(virtual_memory, 'buffers', 0)
                },
                'swap': {
                    'total': swap_memory.total,
                    'used': swap_memory.used,
                    'free': swap_memory.free,
                    'percent': swap_memory.percent
                }
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_disk_info() -> List[Dict[str, Any]]:
        """
        Get disk information.
        
        Returns:
            List of dictionaries with disk information
        """
        try:
            disks = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info = {
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'opts': partition.opts,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100 if usage.total > 0 else 0
                    }
                    disks.append(disk_info)
                except PermissionError:
                    # Skip partitions we don't have permission to access
                    continue
            return disks
        except Exception as e:
            return [{'error': str(e)}]
    
    @staticmethod
    def get_network_info() -> Dict[str, Any]:
        """
        Get network information.
        
        Returns:
            Dictionary with network information
        """
        try:
            net_io = psutil.net_io_counters()
            net_connections = len(psutil.net_connections())
            
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errin': net_io.errin,
                'errout': net_io.errout,
                'dropin': net_io.dropin,
                'dropout': net_io.dropout,
                'connections': net_connections
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_processes() -> List[Dict[str, Any]]:
        """
        Get list of running processes.
        
        Returns:
            List of process information dictionaries
        """
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    proc_info = proc.info
                    proc_info['create_time'] = proc.create_time()
                    proc_info['memory_info'] = proc.memory_info()._asdict()
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return processes
        except Exception as e:
            return [{'error': str(e)}]
    
    @staticmethod
    def get_boot_time() -> float:
        """
        Get system boot time.
        
        Returns:
            Boot time as timestamp
        """
        try:
            return psutil.boot_time()
        except Exception:
            return 0.0
    
    @staticmethod
    def get_uptime() -> float:
        """
        Get system uptime in seconds.
        
        Returns:
            Uptime in seconds
        """
        try:
            return time.time() - psutil.boot_time()
        except Exception:
            return 0.0
    
    @staticmethod
    def format_uptime(uptime_seconds: float) -> str:
        """
        Format uptime in human readable format.
        
        Args:
            uptime_seconds: Uptime in seconds
            
        Returns:
            Formatted uptime string
        """
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    @staticmethod
    def get_system_load() -> Dict[str, Any]:
        """
        Get system load information.
        
        Returns:
            Dictionary with load information
        """
        try:
            if hasattr(psutil, 'getloadavg'):
                load_avg = psutil.getloadavg()
                return {
                    'load_1min': load_avg[0],
                    'load_5min': load_avg[1],
                    'load_15min': load_avg[2]
                }
            else:
                return {'error': 'Load average not available on this system'}
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_temperature_info() -> Dict[str, Any]:
        """
        Get system temperature information.
        
        Returns:
            Dictionary with temperature information
        """
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                return temps
            else:
                return {'error': 'Temperature sensors not available on this system'}
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_fan_info() -> Dict[str, Any]:
        """
        Get system fan information.
        
        Returns:
            Dictionary with fan information
        """
        try:
            if hasattr(psutil, 'sensors_fans'):
                fans = psutil.sensors_fans()
                return fans
            else:
                return {'error': 'Fan sensors not available on this system'}
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_battery_info() -> Dict[str, Any]:
        """
        Get battery information.
        
        Returns:
            Dictionary with battery information
        """
        try:
            if hasattr(psutil, 'sensors_battery'):
                battery = psutil.sensors_battery()
                if battery:
                    return {
                        'percent': battery.percent,
                        'secsleft': battery.secsleft,
                        'power_plugged': battery.power_plugged
                    }
                else:
                    return {'error': 'No battery found'}
            else:
                return {'error': 'Battery information not available on this system'}
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def is_admin() -> bool:
        """
        Check if running with administrator privileges.
        
        Returns:
            True if running as administrator
        """
        try:
            if platform.system() == "Windows":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:
                return os.geteuid() == 0
        except Exception:
            return False
    
    @staticmethod
    def get_environment_variables() -> Dict[str, str]:
        """
        Get environment variables.
        
        Returns:
            Dictionary of environment variables
        """
        return dict(os.environ)
    
    @staticmethod
    def get_python_packages() -> List[Dict[str, str]]:
        """
        Get list of installed Python packages.
        
        Returns:
            List of package information
        """
        try:
            import pkg_resources
            packages = []
            for dist in pkg_resources.working_set:
                packages.append({
                    'name': dist.project_name,
                    'version': dist.version,
                    'location': dist.location
                })
            return packages
        except Exception as e:
            return [{'error': str(e)}]
    
    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """
        Get comprehensive system metrics.
        
        Returns:
            Dictionary with all system metrics
        """
        return {
            'timestamp': time.time(),
            'uptime': SystemUtils.get_uptime(),
            'boot_time': SystemUtils.get_boot_time(),
            'cpu': SystemUtils.get_cpu_info(),
            'memory': SystemUtils.get_memory_info(),
            'disk': SystemUtils.get_disk_info(),
            'network': SystemUtils.get_network_info(),
            'load': SystemUtils.get_system_load(),
            'temperature': SystemUtils.get_temperature_info(),
            'fans': SystemUtils.get_fan_info(),
            'battery': SystemUtils.get_battery_info(),
            'processes_count': len(SystemUtils.get_processes())
        }
    
    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """
        Format bytes in human readable format.
        
        Args:
            bytes_value: Bytes value
            
        Returns:
            Formatted string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    @staticmethod
    def get_disk_usage_percent(path: Union[str, Path] = "/") -> float:
        """
        Get disk usage percentage for given path.
        
        Args:
            path: Path to check
            
        Returns:
            Disk usage percentage
        """
        try:
            usage = psutil.disk_usage(path)
            return (usage.used / usage.total) * 100 if usage.total > 0 else 0
        except Exception:
            return 0.0
    
    @staticmethod
    def get_memory_usage_percent() -> float:
        """
        Get memory usage percentage.
        
        Returns:
            Memory usage percentage
        """
        try:
            return psutil.virtual_memory().percent
        except Exception:
            return 0.0
    
    @staticmethod
    def get_cpu_usage_percent() -> float:
        """
        Get CPU usage percentage.
        
        Returns:
            CPU usage percentage
        """
        try:
            return psutil.cpu_percent(interval=1)
        except Exception:
            return 0.0
