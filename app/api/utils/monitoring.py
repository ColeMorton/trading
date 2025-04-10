"""
API Monitoring Utility

This module provides monitoring functionality for the API server.
"""

import time
import logging
import psutil
import os
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

class APIMonitor:
    """
    API server monitoring class.
    
    This class provides functionality for monitoring API server performance,
    resource usage, and request statistics.
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize the API monitor.
        
        Args:
            logger (logging.Logger): Logger instance
        """
        self.logger = logger
        self.start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0
        self.endpoint_stats = {}
        
    def log_request(self, endpoint: str, method: str, status_code: int, 
                   processing_time: float) -> None:
        """
        Log a request to the API.
        
        Args:
            endpoint (str): API endpoint
            method (str): HTTP method
            status_code (int): HTTP status code
            processing_time (float): Request processing time in seconds
        """
        self.request_count += 1
        
        if status_code >= 400:
            self.error_count += 1
        
        # Update endpoint stats
        endpoint_key = f"{method} {endpoint}"
        if endpoint_key not in self.endpoint_stats:
            self.endpoint_stats[endpoint_key] = {
                "count": 0,
                "error_count": 0,
                "total_time": 0,
                "min_time": float('inf'),
                "max_time": 0
            }
        
        stats = self.endpoint_stats[endpoint_key]
        stats["count"] += 1
        stats["total_time"] += processing_time
        stats["min_time"] = min(stats["min_time"], processing_time)
        stats["max_time"] = max(stats["max_time"], processing_time)
        
        if status_code >= 400:
            stats["error_count"] += 1
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system resource usage statistics.
        
        Returns:
            Dict[str, Any]: System statistics
        """
        process = psutil.Process(os.getpid())
        
        return {
            "cpu_percent": process.cpu_percent(),
            "memory_percent": process.memory_percent(),
            "memory_info": {
                "rss": process.memory_info().rss,
                "vms": process.memory_info().vms
            },
            "threads": len(process.threads()),
            "open_files": len(process.open_files()),
            "connections": len(process.connections())
        }
    
    def get_api_stats(self) -> Dict[str, Any]:
        """
        Get API usage statistics.
        
        Returns:
            Dict[str, Any]: API statistics
        """
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Calculate average request time for each endpoint
        endpoint_stats = {}
        for endpoint, stats in self.endpoint_stats.items():
            avg_time = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
            error_rate = stats["error_count"] / stats["count"] if stats["count"] > 0 else 0
            
            endpoint_stats[endpoint] = {
                "count": stats["count"],
                "error_count": stats["error_count"],
                "error_rate": error_rate,
                "avg_time": avg_time,
                "min_time": stats["min_time"] if stats["min_time"] != float('inf') else 0,
                "max_time": stats["max_time"]
            }
        
        return {
            "uptime": uptime,
            "start_time": self.start_time.isoformat(),
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0,
            "endpoints": endpoint_stats
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """
        Get all monitoring statistics.
        
        Returns:
            Dict[str, Any]: All statistics
        """
        return {
            "system": self.get_system_stats(),
            "api": self.get_api_stats(),
            "timestamp": datetime.now().isoformat()
        }
    
    def log_stats(self, interval: int = 3600) -> None:
        """
        Log statistics at regular intervals.
        
        Args:
            interval (int): Logging interval in seconds
        """
        stats = self.get_all_stats()
        
        self.logger.info(f"API Stats: "
                         f"Uptime: {stats['api']['uptime']:.2f}s, "
                         f"Requests: {stats['api']['request_count']}, "
                         f"Errors: {stats['api']['error_count']}, "
                         f"Error Rate: {stats['api']['error_rate']:.2%}")
        
        self.logger.info(f"System Stats: "
                         f"CPU: {stats['system']['cpu_percent']:.2f}%, "
                         f"Memory: {stats['system']['memory_percent']:.2f}%, "
                         f"Threads: {stats['system']['threads']}")