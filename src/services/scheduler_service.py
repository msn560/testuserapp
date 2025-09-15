"""
Scheduler service for managing background tasks and scheduled jobs.

This service handles task scheduling, background processing, and periodic operations.
It integrates with the system monitoring and maintenance tasks.
"""

import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from ..db.models import MaintenanceTask, SystemLog
from ..core.constants import LogLevel
from ..utils.logger import logger


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """Represents a scheduled task."""
    id: str
    name: str
    function: Callable
    interval: timedelta
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    is_active: bool = True
    max_retries: int = 3
    retry_count: int = 0
    metadata: Dict[str, Any] = None


class SchedulerService:
    """
    Service for managing scheduled tasks and background operations.
    
    This service provides methods for scheduling tasks, managing periodic operations,
    and handling background processing with retry logic and error handling.
    """
    
    def __init__(self):
        """Initialize the scheduler service."""
        self.tasks: Dict[str, ScheduledTask] = {}
        self.is_running = False
        self.scheduler_thread = None
        self.stop_event = threading.Event()
        self.logger = logger
        
        # Default tasks
        self._register_default_tasks()
    
    def start(self) -> bool:
        """
        Start the scheduler service.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            if self.is_running:
                self.logger.warning("Scheduler is already running")
                return True
            
            self.is_running = True
            self.stop_event.clear()
            
            # Start scheduler thread
            self.scheduler_thread = threading.Thread(
                target=self._scheduler_loop,
                daemon=True,
                name="SchedulerService"
            )
            self.scheduler_thread.start()
            
            self.logger.info("Scheduler service started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start scheduler service: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Stop the scheduler service.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            if not self.is_running:
                self.logger.warning("Scheduler is not running")
                return True
            
            self.is_running = False
            self.stop_event.set()
            
            # Wait for scheduler thread to finish
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=10)
            
            self.logger.info("Scheduler service stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop scheduler service: {e}")
            return False
    
    def schedule_task(self, task_id: str, name: str, function: Callable, 
                     interval: timedelta, metadata: Dict[str, Any] = None) -> bool:
        """
        Schedule a new task.
        
        Args:
            task_id: Unique identifier for the task
            name: Human-readable name for the task
            function: Function to execute
            interval: Time interval between executions
            metadata: Additional metadata for the task
            
        Returns:
            True if scheduled successfully, False otherwise
        """
        try:
            if task_id in self.tasks:
                self.logger.warning(f"Task '{task_id}' already exists")
                return False
            
            task = ScheduledTask(
                id=task_id,
                name=name,
                function=function,
                interval=interval,
                next_run=datetime.now() + interval,
                metadata=metadata or {}
            )
            
            self.tasks[task_id] = task
            self.logger.info(f"Task '{name}' scheduled with ID '{task_id}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to schedule task '{task_id}': {e}")
            return False
    
    def unschedule_task(self, task_id: str) -> bool:
        """
        Remove a scheduled task.
        
        Args:
            task_id: The task ID to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        try:
            if task_id not in self.tasks:
                self.logger.warning(f"Task '{task_id}' not found")
                return False
            
            task = self.tasks.pop(task_id)
            self.logger.info(f"Task '{task.name}' unscheduled")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unschedule task '{task_id}': {e}")
            return False
    
    def pause_task(self, task_id: str) -> bool:
        """
        Pause a scheduled task.
        
        Args:
            task_id: The task ID to pause
            
        Returns:
            True if paused successfully, False otherwise
        """
        try:
            if task_id not in self.tasks:
                self.logger.warning(f"Task '{task_id}' not found")
                return False
            
            self.tasks[task_id].is_active = False
            self.logger.info(f"Task '{self.tasks[task_id].name}' paused")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to pause task '{task_id}': {e}")
            return False
    
    def resume_task(self, task_id: str) -> bool:
        """
        Resume a paused task.
        
        Args:
            task_id: The task ID to resume
            
        Returns:
            True if resumed successfully, False otherwise
        """
        try:
            if task_id not in self.tasks:
                self.logger.warning(f"Task '{task_id}' not found")
                return False
            
            self.tasks[task_id].is_active = True
            self.logger.info(f"Task '{self.tasks[task_id].name}' resumed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to resume task '{task_id}': {e}")
            return False
    
    def run_task_now(self, task_id: str) -> bool:
        """
        Execute a task immediately.
        
        Args:
            task_id: The task ID to execute
            
        Returns:
            True if executed successfully, False otherwise
        """
        try:
            if task_id not in self.tasks:
                self.logger.warning(f"Task '{task_id}' not found")
                return False
            
            task = self.tasks[task_id]
            self._execute_task(task)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to run task '{task_id}' immediately: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a task.
        
        Args:
            task_id: The task ID
            
        Returns:
            Task status information or None if not found
        """
        try:
            if task_id not in self.tasks:
                return None
            
            task = self.tasks[task_id]
            return {
                "id": task.id,
                "name": task.name,
                "is_active": task.is_active,
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "next_run": task.next_run.isoformat() if task.next_run else None,
                "interval_seconds": task.interval.total_seconds(),
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
                "metadata": task.metadata
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get task status for '{task_id}': {e}")
            return None
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Get status information for all tasks.
        
        Returns:
            List of task status information
        """
        try:
            tasks = []
            for task_id in self.tasks:
                task_status = self.get_task_status(task_id)
                if task_status:
                    tasks.append(task_status)
            return tasks
            
        except Exception as e:
            self.logger.error(f"Failed to get all tasks: {e}")
            return []
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop that runs in a separate thread."""
        try:
            self.logger.info("Scheduler loop started")
            
            while self.is_running and not self.stop_event.is_set():
                try:
                    current_time = datetime.now()
                    
                    # Check for tasks that need to run
                    for task in self.tasks.values():
                        if (task.is_active and 
                            task.next_run and 
                            current_time >= task.next_run):
                            
                            # Execute task in a separate thread to avoid blocking
                            task_thread = threading.Thread(
                                target=self._execute_task,
                                args=(task,),
                                daemon=True,
                                name=f"Task-{task.id}"
                            )
                            task_thread.start()
                    
                    # Sleep for a short interval
                    self.stop_event.wait(1)  # 1 second interval
                    
                except Exception as e:
                    self.logger.error(f"Error in scheduler loop: {e}")
                    self.stop_event.wait(5)  # Wait longer on error
            
            self.logger.info("Scheduler loop stopped")
            
        except Exception as e:
            self.logger.error(f"Fatal error in scheduler loop: {e}")
    
    def _execute_task(self, task: ScheduledTask) -> None:
        """
        Execute a scheduled task.
        
        Args:
            task: The task to execute
        """
        try:
            self.logger.info(f"Executing task '{task.name}'")
            
            # Update task status
            task.last_run = datetime.now()
            task.retry_count = 0
            
            # Execute the task function
            if asyncio.iscoroutinefunction(task.function):
                # Handle async functions
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(task.function())
                finally:
                    loop.close()
            else:
                # Handle sync functions
                task.function()
            
            # Schedule next run
            task.next_run = datetime.now() + task.interval
            
            self.logger.info(f"Task '{task.name}' completed successfully")
            
            # Log task completion
            self._log_task_event(task, "Task completed successfully", LogLevel.INFO)
            
        except Exception as e:
            self.logger.error(f"Task '{task.name}' failed: {e}")
            
            # Handle retries
            task.retry_count += 1
            if task.retry_count < task.max_retries:
                # Schedule retry
                retry_delay = timedelta(minutes=task.retry_count * 5)  # Exponential backoff
                task.next_run = datetime.now() + retry_delay
                self.logger.info(f"Task '{task.name}' will retry in {retry_delay}")
            else:
                # Max retries reached, deactivate task
                task.is_active = False
                self.logger.error(f"Task '{task.name}' deactivated after {task.max_retries} retries")
            
            # Log task failure
            self._log_task_event(task, f"Task failed: {e}", LogLevel.ERROR)
    
    def _register_default_tasks(self) -> None:
        """Register default system tasks."""
        try:
            # Database cleanup task
            self.schedule_task(
                task_id="db_cleanup",
                name="Database Cleanup",
                function=self._cleanup_old_logs,
                interval=timedelta(hours=24),
                metadata={"type": "maintenance", "priority": "low"}
            )
            
            # System metrics collection
            self.schedule_task(
                task_id="collect_metrics",
                name="Collect System Metrics",
                function=self._collect_system_metrics,
                interval=timedelta(minutes=5),
                metadata={"type": "monitoring", "priority": "high"}
            )
            
            # Configuration backup
            self.schedule_task(
                task_id="config_backup",
                name="Configuration Backup",
                function=self._backup_configuration,
                interval=timedelta(hours=6),
                metadata={"type": "backup", "priority": "medium"}
            )
            
            self.logger.info("Default tasks registered")
            
        except Exception as e:
            self.logger.error(f"Failed to register default tasks: {e}")
    
    async def _cleanup_old_logs(self) -> None:
        """Clean up old log entries."""
        try:
            # Delete logs older than 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            deleted_count = (SystemLog.delete()
                           .where(SystemLog.created_at < cutoff_date)
                           .execute())
            
            self.logger.info(f"Cleaned up {deleted_count} old log entries")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")
    
    async def _collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        try:
            import psutil
            
            # This would collect and store system metrics
            # For now, just log that the task ran
            self.logger.debug("System metrics collected")
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
    
    async def _backup_configuration(self) -> None:
        """Backup system configuration."""
        try:
            # This would backup configuration files
            # For now, just log that the task ran
            self.logger.debug("Configuration backup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to backup configuration: {e}")
    
    def _log_task_event(self, task: ScheduledTask, message: str, level: LogLevel) -> None:
        """
        Log a task-related event.
        
        Args:
            task: The task that generated the event
            message: The log message
            level: The log level
        """
        try:
            SystemLog.create(
                level=level.value,
                module="scheduler",
                message=f"[{task.name}] {message}",
                extra_data=f'{{"task_id": "{task.id}", "retry_count": {task.retry_count}}}',
                created_at=datetime.now()
            )
        except Exception as e:
            self.logger.error(f"Failed to log task event: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler service status.
        
        Returns:
            Dictionary with service status information
        """
        try:
            active_tasks = sum(1 for task in self.tasks.values() if task.is_active)
            total_tasks = len(self.tasks)
            
            return {
                "is_running": self.is_running,
                "total_tasks": total_tasks,
                "active_tasks": active_tasks,
                "paused_tasks": total_tasks - active_tasks,
                "tasks": self.get_all_tasks()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get scheduler status: {e}")
            return {"is_running": False, "error": str(e)}
