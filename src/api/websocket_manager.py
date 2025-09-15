"""
WebSocket Manager for real-time communication.

This module manages WebSocket connections for real-time data streaming,
notifications, and live updates.
"""

import asyncio
import json
import time
from typing import Dict, Set, Any, Optional, Callable
from aiohttp import web, WSMsgType
from aiohttp.web_ws import WebSocketResponse
import logging

from ..utils.logger import Logger
from ..core.event_system import EventSystem


class WebSocketManager:
    """Manages WebSocket connections and real-time communication."""
    
    def __init__(self):
        """Initialize WebSocket manager."""
        self.logger = Logger(__name__)
        self.connections: Dict[str, Set[WebSocketResponse]] = {}
        self.event_system = EventSystem()
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup event handlers for real-time updates."""
        # System status updates
        self.event_system.subscribe('system.status', self._broadcast_system_status)
        self.event_system.subscribe('system.metrics', self._broadcast_system_metrics)
        
        # Log updates
        self.event_system.subscribe('log.new', self._broadcast_log_entry)
        
        # User notifications
        self.event_system.subscribe('user.notification', self._broadcast_notification)
        
        # API metrics
        self.event_system.subscribe('api.metrics', self._broadcast_api_metrics)
    
    async def websocket_handler(self, request: web.Request) -> WebSocketResponse:
        """
        Handle WebSocket connection requests.
        
        Args:
            request: HTTP request
            
        Returns:
            WebSocket response
        """
        ws = WebSocketResponse()
        await ws.prepare(request)
        
        # Get connection type from query parameters
        connection_type = request.query.get('type', 'general')
        
        # Add connection to appropriate group
        if connection_type not in self.connections:
            self.connections[connection_type] = set()
        
        self.connections[connection_type].add(ws)
        
        self.logger.info(f"WebSocket connection established: {connection_type}")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self._handle_message(ws, msg.data, connection_type)
                elif msg.type == WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error: {ws.exception()}")
                    break
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
        finally:
            # Remove connection from group
            if connection_type in self.connections:
                self.connections[connection_type].discard(ws)
                if not self.connections[connection_type]:
                    del self.connections[connection_type]
            
            self.logger.info(f"WebSocket connection closed: {connection_type}")
        
        return ws
    
    async def _handle_message(self, ws: WebSocketResponse, message: str, connection_type: str):
        """
        Handle incoming WebSocket message.
        
        Args:
            ws: WebSocket connection
            message: Message data
            connection_type: Type of connection
        """
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self._send_message(ws, {'type': 'pong', 'timestamp': time.time()})
            elif message_type == 'subscribe':
                # Handle subscription requests
                await self._handle_subscription(ws, data, connection_type)
            elif message_type == 'unsubscribe':
                # Handle unsubscription requests
                await self._handle_unsubscription(ws, data, connection_type)
            else:
                self.logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            self.logger.error("Invalid JSON in WebSocket message")
        except Exception as e:
            self.logger.error(f"Error handling WebSocket message: {e}")
    
    async def _handle_subscription(self, ws: WebSocketResponse, data: Dict[str, Any], connection_type: str):
        """
        Handle subscription requests.
        
        Args:
            ws: WebSocket connection
            data: Subscription data
            connection_type: Type of connection
        """
        subscription_type = data.get('subscription_type')
        
        if subscription_type == 'system_status':
            # Send current system status
            await self._send_system_status(ws)
        elif subscription_type == 'logs':
            # Send recent logs
            await self._send_recent_logs(ws)
        elif subscription_type == 'metrics':
            # Send current metrics
            await self._send_current_metrics(ws)
    
    async def _handle_unsubscription(self, ws: WebSocketResponse, data: Dict[str, Any], connection_type: str):
        """
        Handle unsubscription requests.
        
        Args:
            ws: WebSocket connection
            data: Unsubscription data
            connection_type: Type of connection
        """
        # For now, just acknowledge the unsubscription
        await self._send_message(ws, {'type': 'unsubscribed', 'timestamp': time.time()})
    
    async def _send_message(self, ws: WebSocketResponse, data: Dict[str, Any]):
        """
        Send message to WebSocket connection.
        
        Args:
            ws: WebSocket connection
            data: Message data
        """
        try:
            if not ws.closed:
                await ws.send_str(json.dumps(data))
        except Exception as e:
            self.logger.error(f"Error sending WebSocket message: {e}")
    
    async def broadcast_to_type(self, connection_type: str, data: Dict[str, Any]):
        """
        Broadcast message to all connections of specific type.
        
        Args:
            connection_type: Type of connections to broadcast to
            data: Message data
        """
        if connection_type not in self.connections:
            return
        
        message = json.dumps(data)
        closed_connections = set()
        
        for ws in self.connections[connection_type]:
            try:
                if not ws.closed:
                    await ws.send_str(message)
                else:
                    closed_connections.add(ws)
            except Exception as e:
                self.logger.error(f"Error broadcasting to WebSocket: {e}")
                closed_connections.add(ws)
        
        # Remove closed connections
        self.connections[connection_type] -= closed_connections
    
    async def broadcast_to_all(self, data: Dict[str, Any]):
        """
        Broadcast message to all connections.
        
        Args:
            data: Message data
        """
        for connection_type in self.connections:
            await self.broadcast_to_type(connection_type, data)
    
    async def _broadcast_system_status(self, data: Dict[str, Any]):
        """Broadcast system status updates."""
        await self.broadcast_to_type('system_status', {
            'type': 'system_status',
            'data': data,
            'timestamp': time.time()
        })
    
    async def _broadcast_system_metrics(self, data: Dict[str, Any]):
        """Broadcast system metrics updates."""
        await self.broadcast_to_type('metrics', {
            'type': 'system_metrics',
            'data': data,
            'timestamp': time.time()
        })
    
    async def _broadcast_log_entry(self, data: Dict[str, Any]):
        """Broadcast new log entries."""
        await self.broadcast_to_type('logs', {
            'type': 'log_entry',
            'data': data,
            'timestamp': time.time()
        })
    
    async def _broadcast_notification(self, data: Dict[str, Any]):
        """Broadcast user notifications."""
        await self.broadcast_to_type('notifications', {
            'type': 'notification',
            'data': data,
            'timestamp': time.time()
        })
    
    async def _broadcast_api_metrics(self, data: Dict[str, Any]):
        """Broadcast API metrics updates."""
        await self.broadcast_to_type('api_metrics', {
            'type': 'api_metrics',
            'data': data,
            'timestamp': time.time()
        })
    
    async def _send_system_status(self, ws: WebSocketResponse):
        """Send current system status to WebSocket."""
        # This would typically get real system status
        status_data = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_percent': 0,
            'uptime': 0
        }
        
        await self._send_message(ws, {
            'type': 'system_status',
            'data': status_data,
            'timestamp': time.time()
        })
    
    async def _send_recent_logs(self, ws: WebSocketResponse):
        """Send recent logs to WebSocket."""
        # This would typically get recent logs from database
        logs_data = []
        
        await self._send_message(ws, {
            'type': 'recent_logs',
            'data': logs_data,
            'timestamp': time.time()
        })
    
    async def _send_current_metrics(self, ws: WebSocketResponse):
        """Send current metrics to WebSocket."""
        # This would typically get current metrics
        metrics_data = {
            'requests_per_minute': 0,
            'response_time_avg': 0,
            'error_rate': 0
        }
        
        await self._send_message(ws, {
            'type': 'current_metrics',
            'data': metrics_data,
            'timestamp': time.time()
        })
    
    def get_connection_count(self) -> Dict[str, int]:
        """
        Get count of active connections by type.
        
        Returns:
            Dictionary with connection counts
        """
        return {
            connection_type: len(connections)
            for connection_type, connections in self.connections.items()
        }
    
    def get_total_connections(self) -> int:
        """
        Get total number of active connections.
        
        Returns:
            Total connection count
        """
        return sum(len(connections) for connections in self.connections.values())
    
    async def close_all_connections(self):
        """Close all WebSocket connections."""
        for connection_type, connections in self.connections.items():
            for ws in list(connections):
                try:
                    if not ws.closed:
                        await ws.close()
                except Exception as e:
                    self.logger.error(f"Error closing WebSocket: {e}")
        
        self.connections.clear()
        self.logger.info("All WebSocket connections closed")


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
