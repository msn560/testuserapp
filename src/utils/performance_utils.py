"""
Performance utilities for performance monitoring, profiling, and optimization.

This module provides utilities for performance monitoring, profiling,
memory tracking, and performance optimization.
"""

import time
import psutil
import threading
from typing import Dict, Any, Optional, Callable, List
from functools import wraps
from contextlib import contextmanager
import tracemalloc
import gc


class PerformanceUtils:
    """Utilities for performance monitoring and optimization."""
    
    @staticmethod
    def measure_time(func: Callable) -> Callable:
        """
        Decorator to measure function execution time.
        
        Args:
            func: Function to measure
            
        Returns:
            Wrapped function with timing
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            
            execution_time = end_time - start_time
            print(f"{func.__name__} executed in {execution_time:.4f} seconds")
            
            return result
        return wrapper
    
    @staticmethod
    def measure_time_async(func: Callable) -> Callable:
        """
        Decorator to measure async function execution time.
        
        Args:
            func: Async function to measure
            
        Returns:
            Wrapped async function with timing
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            end_time = time.perf_counter()
            
            execution_time = end_time - start_time
            print(f"{func.__name__} executed in {execution_time:.4f} seconds")
            
            return result
        return wrapper
    
    @staticmethod
    @contextmanager
    def measure_context(name: str = "operation"):
        """
        Context manager to measure execution time.
        
        Args:
            name: Name of the operation being measured
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            print(f"{name} completed in {execution_time:.4f} seconds")
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """
        Get current memory usage information.
        
        Returns:
            Dictionary with memory usage information
        """
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss,  # Resident Set Size
            'vms': memory_info.vms,  # Virtual Memory Size
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024,
            'total_mb': psutil.virtual_memory().total / 1024 / 1024
        }
    
    @staticmethod
    def get_cpu_usage() -> Dict[str, Any]:
        """
        Get current CPU usage information.
        
        Returns:
            Dictionary with CPU usage information
        """
        return {
            'percent': psutil.cpu_percent(interval=1),
            'per_cpu': psutil.cpu_percent(interval=1, percpu=True),
            'count': psutil.cpu_count(),
            'load_avg': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    
    @staticmethod
    def get_process_info() -> Dict[str, Any]:
        """
        Get current process information.
        
        Returns:
            Dictionary with process information
        """
        process = psutil.Process()
        
        return {
            'pid': process.pid,
            'name': process.name(),
            'status': process.status(),
            'create_time': process.create_time(),
            'cpu_percent': process.cpu_percent(),
            'memory_percent': process.memory_percent(),
            'num_threads': process.num_threads(),
            'num_fds': process.num_fds() if hasattr(process, 'num_fds') else None,
            'connections': len(process.connections())
        }
    
    @staticmethod
    def start_memory_tracing() -> None:
        """
        Start memory tracing for memory leak detection.
        """
        tracemalloc.start()
    
    @staticmethod
    def stop_memory_tracing() -> Dict[str, Any]:
        """
        Stop memory tracing and get memory statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        if not tracemalloc.is_tracing():
            return {'error': 'Memory tracing not started'}
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        return {
            'current_mb': current / 1024 / 1024,
            'peak_mb': peak / 1024 / 1024,
            'current_bytes': current,
            'peak_bytes': peak
        }
    
    @staticmethod
    def get_memory_snapshot() -> Dict[str, Any]:
        """
        Get current memory snapshot.
        
        Returns:
            Dictionary with memory snapshot information
        """
        if not tracemalloc.is_tracing():
            return {'error': 'Memory tracing not started'}
        
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        return {
            'total_blocks': sum(stat.count for stat in top_stats),
            'total_size_mb': sum(stat.size for stat in top_stats) / 1024 / 1024,
            'top_allocations': [
                {
                    'filename': stat.traceback.format()[0],
                    'size_mb': stat.size / 1024 / 1024,
                    'count': stat.count
                }
                for stat in top_stats[:10]
            ]
        }
    
    @staticmethod
    def force_garbage_collection() -> Dict[str, Any]:
        """
        Force garbage collection and return statistics.
        
        Returns:
            Dictionary with garbage collection statistics
        """
        before = len(gc.get_objects())
        collected = gc.collect()
        after = len(gc.get_objects())
        
        return {
            'objects_before': before,
            'objects_after': after,
            'objects_collected': before - after,
            'generations_collected': collected
        }
    
    @staticmethod
    def get_gc_stats() -> Dict[str, Any]:
        """
        Get garbage collection statistics.
        
        Returns:
            Dictionary with GC statistics
        """
        return {
            'counts': gc.get_count(),
            'thresholds': gc.get_threshold(),
            'stats': gc.get_stats()
        }
    
    @staticmethod
    def profile_function(func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Profile a function and return performance metrics.
        
        Args:
            func: Function to profile
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Dictionary with performance metrics
        """
        # Start memory tracing
        PerformanceUtils.start_memory_tracing()
        
        # Get initial memory usage
        initial_memory = PerformanceUtils.get_memory_usage()
        
        # Measure execution time
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        end_time = time.perf_counter()
        
        # Get final memory usage
        final_memory = PerformanceUtils.get_memory_usage()
        memory_stats = PerformanceUtils.stop_memory_tracing()
        
        execution_time = end_time - start_time
        
        return {
            'function_name': func.__name__,
            'success': success,
            'error': error,
            'execution_time_seconds': execution_time,
            'initial_memory_mb': initial_memory['rss'] / 1024 / 1024,
            'final_memory_mb': final_memory['rss'] / 1024 / 1024,
            'memory_delta_mb': (final_memory['rss'] - initial_memory['rss']) / 1024 / 1024,
            'memory_tracing': memory_stats,
            'result': result
        }
    
    @staticmethod
    def benchmark_function(func: Callable, iterations: int = 1000, *args, **kwargs) -> Dict[str, Any]:
        """
        Benchmark a function with multiple iterations.
        
        Args:
            func: Function to benchmark
            iterations: Number of iterations
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Dictionary with benchmark results
        """
        times = []
        errors = 0
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            try:
                func(*args, **kwargs)
            except Exception:
                errors += 1
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        if not times:
            return {'error': 'All iterations failed'}
        
        times.sort()
        
        return {
            'function_name': func.__name__,
            'iterations': iterations,
            'errors': errors,
            'success_rate': (iterations - errors) / iterations * 100,
            'min_time': min(times),
            'max_time': max(times),
            'avg_time': sum(times) / len(times),
            'median_time': times[len(times) // 2],
            'p95_time': times[int(len(times) * 0.95)],
            'p99_time': times[int(len(times) * 0.99)]
        }
    
    @staticmethod
    def monitor_resource_usage(duration: float = 60.0, interval: float = 1.0) -> List[Dict[str, Any]]:
        """
        Monitor resource usage over time.
        
        Args:
            duration: Monitoring duration in seconds
            interval: Sampling interval in seconds
            
        Returns:
            List of resource usage snapshots
        """
        snapshots = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            snapshot = {
                'timestamp': time.time(),
                'cpu': PerformanceUtils.get_cpu_usage(),
                'memory': PerformanceUtils.get_memory_usage(),
                'process': PerformanceUtils.get_process_info()
            }
            snapshots.append(snapshot)
            time.sleep(interval)
        
        return snapshots
    
    @staticmethod
    def get_performance_summary() -> Dict[str, Any]:
        """
        Get comprehensive performance summary.
        
        Returns:
            Dictionary with performance summary
        """
        return {
            'timestamp': time.time(),
            'cpu': PerformanceUtils.get_cpu_usage(),
            'memory': PerformanceUtils.get_memory_usage(),
            'process': PerformanceUtils.get_process_info(),
            'gc': PerformanceUtils.get_gc_stats()
        }
    
    @staticmethod
    def optimize_memory() -> Dict[str, Any]:
        """
        Perform memory optimization.
        
        Returns:
            Dictionary with optimization results
        """
        # Force garbage collection
        gc_stats = PerformanceUtils.force_garbage_collection()
        
        # Get memory usage after optimization
        memory_usage = PerformanceUtils.get_memory_usage()
        
        return {
            'gc_stats': gc_stats,
            'memory_usage': memory_usage,
            'optimization_time': time.time()
        }
    
    @staticmethod
    def create_performance_monitor(name: str) -> 'PerformanceMonitor':
        """
        Create a performance monitor instance.
        
        Args:
            name: Monitor name
            
        Returns:
            PerformanceMonitor instance
        """
        return PerformanceMonitor(name)


class PerformanceMonitor:
    """Performance monitoring class for tracking metrics over time."""
    
    def __init__(self, name: str):
        """
        Initialize performance monitor.
        
        Args:
            name: Monitor name
        """
        self.name = name
        self.metrics = []
        self.start_time = None
        self.is_monitoring = False
    
    def start(self) -> None:
        """Start monitoring."""
        self.start_time = time.time()
        self.is_monitoring = True
        self.metrics = []
    
    def stop(self) -> Dict[str, Any]:
        """
        Stop monitoring and return summary.
        
        Returns:
            Dictionary with monitoring summary
        """
        if not self.is_monitoring:
            return {'error': 'Monitor not started'}
        
        self.is_monitoring = False
        duration = time.time() - self.start_time
        
        if not self.metrics:
            return {'error': 'No metrics collected'}
        
        # Calculate statistics
        cpu_values = [m['cpu']['percent'] for m in self.metrics]
        memory_values = [m['memory']['percent'] for m in self.metrics]
        
        return {
            'name': self.name,
            'duration_seconds': duration,
            'sample_count': len(self.metrics),
            'avg_cpu_percent': sum(cpu_values) / len(cpu_values),
            'max_cpu_percent': max(cpu_values),
            'avg_memory_percent': sum(memory_values) / len(memory_values),
            'max_memory_percent': max(memory_values),
            'metrics': self.metrics
        }
    
    def collect_metric(self) -> None:
        """Collect current performance metric."""
        if not self.is_monitoring:
            return
        
        metric = {
            'timestamp': time.time(),
            'cpu': PerformanceUtils.get_cpu_usage(),
            'memory': PerformanceUtils.get_memory_usage(),
            'process': PerformanceUtils.get_process_info()
        }
        self.metrics.append(metric)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.
        
        Returns:
            Dictionary with current metrics
        """
        return {
            'timestamp': time.time(),
            'cpu': PerformanceUtils.get_cpu_usage(),
            'memory': PerformanceUtils.get_memory_usage(),
            'process': PerformanceUtils.get_process_info()
        }
