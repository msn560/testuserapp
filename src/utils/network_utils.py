"""
Network utilities for network operations, validation, and monitoring.

This module provides utilities for network operations, IP validation,
port checking, and network monitoring.
"""

import socket
import ipaddress
import requests
import asyncio
import aiohttp
from typing import Optional, List, Dict, Any, Union
from urllib.parse import urlparse, urljoin
import time


class NetworkUtils:
    """Utilities for network operations and validation."""
    
    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """
        Check if string is a valid IP address.
        
        Args:
            ip: IP address string
            
        Returns:
            True if valid IP address
        """
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_ipv4(ip: str) -> bool:
        """
        Check if string is a valid IPv4 address.
        
        Args:
            ip: IP address string
            
        Returns:
            True if valid IPv4 address
        """
        try:
            ipaddress.IPv4Address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_ipv6(ip: str) -> bool:
        """
        Check if string is a valid IPv6 address.
        
        Args:
            ip: IP address string
            
        Returns:
            True if valid IPv6 address
        """
        try:
            ipaddress.IPv6Address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_port(port: Union[int, str]) -> bool:
        """
        Check if port number is valid.
        
        Args:
            port: Port number
            
        Returns:
            True if valid port number
        """
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_port_open(host: str, port: int, timeout: float = 3.0) -> bool:
        """
        Check if port is open on host.
        
        Args:
            host: Host address
            port: Port number
            timeout: Connection timeout
            
        Returns:
            True if port is open
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                return result == 0
        except Exception:
            return False
    
    @staticmethod
    async def async_is_port_open(host: str, port: int, timeout: float = 3.0) -> bool:
        """
        Asynchronously check if port is open on host.
        
        Args:
            host: Host address
            port: Port number
            timeout: Connection timeout
            
        Returns:
            True if port is open
        """
        try:
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=timeout)
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_local_ip() -> Optional[str]:
        """
        Get local IP address.
        
        Returns:
            Local IP address, None if error
        """
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return None
    
    @staticmethod
    def get_hostname() -> Optional[str]:
        """
        Get local hostname.
        
        Returns:
            Local hostname, None if error
        """
        try:
            return socket.gethostname()
        except Exception:
            return None
    
    @staticmethod
    def resolve_hostname(hostname: str) -> Optional[str]:
        """
        Resolve hostname to IP address.
        
        Args:
            hostname: Hostname to resolve
            
        Returns:
            IP address, None if error
        """
        try:
            return socket.gethostbyname(hostname)
        except Exception:
            return None
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Check if string is a valid URL.
        
        Args:
            url: URL string
            
        Returns:
            True if valid URL
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def is_https_url(url: str) -> bool:
        """
        Check if URL uses HTTPS.
        
        Args:
            url: URL string
            
        Returns:
            True if HTTPS URL
        """
        try:
            return urlparse(url).scheme.lower() == 'https'
        except Exception:
            return False
    
    @staticmethod
    def get_domain_from_url(url: str) -> Optional[str]:
        """
        Extract domain from URL.
        
        Args:
            url: URL string
            
        Returns:
            Domain name, None if error
        """
        try:
            return urlparse(url).netloc
        except Exception:
            return None
    
    @staticmethod
    def ping_host(host: str, timeout: float = 3.0) -> bool:
        """
        Ping host to check connectivity.
        
        Args:
            host: Host to ping
            timeout: Ping timeout
            
        Returns:
            True if host is reachable
        """
        try:
            import subprocess
            import platform
            
            # Choose ping command based on OS
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), host]
            else:
                cmd = ["ping", "-c", "1", "-W", str(int(timeout)), host]
            
            result = subprocess.run(cmd, capture_output=True, timeout=timeout + 1)
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    async def async_ping_host(host: str, timeout: float = 3.0) -> bool:
        """
        Asynchronously ping host to check connectivity.
        
        Args:
            host: Host to ping
            timeout: Ping timeout
            
        Returns:
            True if host is reachable
        """
        try:
            # Use asyncio to run ping in subprocess
            import subprocess
            import platform
            
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), host]
            else:
                cmd = ["ping", "-c", "1", "-W", str(int(timeout)), host]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            try:
                await asyncio.wait_for(process.wait(), timeout=timeout + 1)
                return process.returncode == 0
            except asyncio.TimeoutError:
                process.kill()
                return False
        except Exception:
            return False
    
    @staticmethod
    def check_http_response(url: str, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Check HTTP response for URL.
        
        Args:
            url: URL to check
            timeout: Request timeout
            
        Returns:
            Dictionary with response information
        """
        result = {
            'success': False,
            'status_code': None,
            'response_time': None,
            'error': None
        }
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            end_time = time.time()
            
            result['success'] = True
            result['status_code'] = response.status_code
            result['response_time'] = end_time - start_time
            
        except requests.exceptions.Timeout:
            result['error'] = 'Timeout'
        except requests.exceptions.ConnectionError:
            result['error'] = 'Connection error'
        except requests.exceptions.RequestException as e:
            result['error'] = str(e)
        
        return result
    
    @staticmethod
    async def async_check_http_response(url: str, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Asynchronously check HTTP response for URL.
        
        Args:
            url: URL to check
            timeout: Request timeout
            
        Returns:
            Dictionary with response information
        """
        result = {
            'success': False,
            'status_code': None,
            'response_time': None,
            'error': None
        }
        
        try:
            start_time = time.time()
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url, allow_redirects=True) as response:
                    end_time = time.time()
                    
                    result['success'] = True
                    result['status_code'] = response.status
                    result['response_time'] = end_time - start_time
                    
        except asyncio.TimeoutError:
            result['error'] = 'Timeout'
        except aiohttp.ClientError as e:
            result['error'] = str(e)
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    @staticmethod
    def get_network_interfaces() -> List[Dict[str, Any]]:
        """
        Get list of network interfaces.
        
        Returns:
            List of network interface information
        """
        interfaces = []
        try:
            import psutil
            
            for interface, addrs in psutil.net_if_addrs().items():
                interface_info = {
                    'name': interface,
                    'addresses': []
                }
                
                for addr in addrs:
                    if addr.family == socket.AF_INET:  # IPv4
                        interface_info['addresses'].append({
                            'type': 'IPv4',
                            'address': addr.address,
                            'netmask': addr.netmask,
                            'broadcast': addr.broadcast
                        })
                    elif addr.family == socket.AF_INET6:  # IPv6
                        interface_info['addresses'].append({
                            'type': 'IPv6',
                            'address': addr.address,
                            'netmask': addr.netmask
                        })
                
                if interface_info['addresses']:
                    interfaces.append(interface_info)
                    
        except ImportError:
            # Fallback without psutil
            pass
        
        return interfaces
    
    @staticmethod
    def is_private_ip(ip: str) -> bool:
        """
        Check if IP address is private.
        
        Args:
            ip: IP address string
            
        Returns:
            True if private IP address
        """
        try:
            return ipaddress.ip_address(ip).is_private
        except ValueError:
            return False
    
    @staticmethod
    def is_loopback_ip(ip: str) -> bool:
        """
        Check if IP address is loopback.
        
        Args:
            ip: IP address string
            
        Returns:
            True if loopback IP address
        """
        try:
            return ipaddress.ip_address(ip).is_loopback
        except ValueError:
            return False
    
    @staticmethod
    def get_network_info() -> Dict[str, Any]:
        """
        Get comprehensive network information.
        
        Returns:
            Dictionary with network information
        """
        info = {
            'hostname': NetworkUtils.get_hostname(),
            'local_ip': NetworkUtils.get_local_ip(),
            'interfaces': NetworkUtils.get_network_interfaces(),
            'timestamp': time.time()
        }
        
        return info
    
    @staticmethod
    def validate_network_config(host: str, port: int) -> Dict[str, Any]:
        """
        Validate network configuration.
        
        Args:
            host: Host address
            port: Port number
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate host
        if not NetworkUtils.is_valid_ip(host) and not host:
            result['valid'] = False
            result['errors'].append('Invalid host address')
        
        # Validate port
        if not NetworkUtils.is_valid_port(port):
            result['valid'] = False
            result['errors'].append('Invalid port number')
        
        # Check if port is in well-known range
        if 1 <= port <= 1023:
            result['warnings'].append('Port is in well-known range (1-1023)')
        
        # Check if host is private
        if NetworkUtils.is_valid_ip(host) and NetworkUtils.is_private_ip(host):
            result['warnings'].append('Host is a private IP address')
        
        return result
