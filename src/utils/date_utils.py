"""
Date and time utilities for date operations, formatting, and timezone handling.

This module provides utilities for date/time operations, formatting,
timezone conversions, and time calculations.
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Union, Optional, List, Dict, Any
import calendar


class DateUtils:
    """Utilities for date and time operations."""
    
    @staticmethod
    def get_current_timestamp() -> float:
        """
        Get current timestamp.
        
        Returns:
            Current timestamp as float
        """
        return time.time()
    
    @staticmethod
    def get_current_datetime() -> datetime:
        """
        Get current datetime in UTC.
        
        Returns:
            Current datetime in UTC
        """
        return datetime.now(timezone.utc)
    
    @staticmethod
    def get_current_datetime_local() -> datetime:
        """
        Get current datetime in local timezone.
        
        Returns:
            Current datetime in local timezone
        """
        return datetime.now()
    
    @staticmethod
    def timestamp_to_datetime(timestamp: float, tz: Optional[timezone] = None) -> datetime:
        """
        Convert timestamp to datetime.
        
        Args:
            timestamp: Unix timestamp
            tz: Timezone (default: UTC)
            
        Returns:
            Datetime object
        """
        if tz is None:
            tz = timezone.utc
        return datetime.fromtimestamp(timestamp, tz=tz)
    
    @staticmethod
    def datetime_to_timestamp(dt: datetime) -> float:
        """
        Convert datetime to timestamp.
        
        Args:
            dt: Datetime object
            
        Returns:
            Unix timestamp
        """
        return dt.timestamp()
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Format datetime to string.
        
        Args:
            dt: Datetime object
            format_str: Format string
            
        Returns:
            Formatted datetime string
        """
        return dt.strftime(format_str)
    
    @staticmethod
    def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
        """
        Parse datetime string to datetime object.
        
        Args:
            date_str: Date string
            format_str: Format string
            
        Returns:
            Datetime object, None if parsing fails
        """
        try:
            return datetime.strptime(date_str, format_str)
        except ValueError:
            return None
    
    @staticmethod
    def format_timestamp(timestamp: float, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Format timestamp to string.
        
        Args:
            timestamp: Unix timestamp
            format_str: Format string
            
        Returns:
            Formatted datetime string
        """
        dt = DateUtils.timestamp_to_datetime(timestamp)
        return DateUtils.format_datetime(dt, format_str)
    
    @staticmethod
    def get_iso_format(dt: Optional[datetime] = None) -> str:
        """
        Get ISO format string.
        
        Args:
            dt: Datetime object (default: current time)
            
        Returns:
            ISO format string
        """
        if dt is None:
            dt = DateUtils.get_current_datetime()
        return dt.isoformat()
    
    @staticmethod
    def parse_iso_format(iso_str: str) -> Optional[datetime]:
        """
        Parse ISO format string to datetime.
        
        Args:
            iso_str: ISO format string
            
        Returns:
            Datetime object, None if parsing fails
        """
        try:
            return datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        except ValueError:
            return None
    
    @staticmethod
    def add_time(dt: datetime, **kwargs) -> datetime:
        """
        Add time to datetime.
        
        Args:
            dt: Base datetime
            **kwargs: Time components (days, hours, minutes, seconds, etc.)
            
        Returns:
            New datetime with added time
        """
        return dt + timedelta(**kwargs)
    
    @staticmethod
    def subtract_time(dt: datetime, **kwargs) -> datetime:
        """
        Subtract time from datetime.
        
        Args:
            dt: Base datetime
            **kwargs: Time components (days, hours, minutes, seconds, etc.)
            
        Returns:
            New datetime with subtracted time
        """
        return dt - timedelta(**kwargs)
    
    @staticmethod
    def time_difference(dt1: datetime, dt2: datetime) -> timedelta:
        """
        Calculate time difference between two datetimes.
        
        Args:
            dt1: First datetime
            dt2: Second datetime
            
        Returns:
            Time difference as timedelta
        """
        return dt2 - dt1
    
    @staticmethod
    def time_difference_seconds(dt1: datetime, dt2: datetime) -> float:
        """
        Calculate time difference in seconds.
        
        Args:
            dt1: First datetime
            dt2: Second datetime
            
        Returns:
            Time difference in seconds
        """
        return (dt2 - dt1).total_seconds()
    
    @staticmethod
    def is_same_day(dt1: datetime, dt2: datetime) -> bool:
        """
        Check if two datetimes are on the same day.
        
        Args:
            dt1: First datetime
            dt2: Second datetime
            
        Returns:
            True if same day
        """
        return dt1.date() == dt2.date()
    
    @staticmethod
    def is_same_week(dt1: datetime, dt2: datetime) -> bool:
        """
        Check if two datetimes are in the same week.
        
        Args:
            dt1: First datetime
            dt2: Second datetime
            
        Returns:
            True if same week
        """
        return dt1.isocalendar()[:2] == dt2.isocalendar()[:2]
    
    @staticmethod
    def is_same_month(dt1: datetime, dt2: datetime) -> bool:
        """
        Check if two datetimes are in the same month.
        
        Args:
            dt1: First datetime
            dt2: Second datetime
            
        Returns:
            True if same month
        """
        return dt1.year == dt2.year and dt1.month == dt2.month
    
    @staticmethod
    def is_same_year(dt1: datetime, dt2: datetime) -> bool:
        """
        Check if two datetimes are in the same year.
        
        Args:
            dt1: First datetime
            dt2: Second datetime
            
        Returns:
            True if same year
        """
        return dt1.year == dt2.year
    
    @staticmethod
    def get_start_of_day(dt: datetime) -> datetime:
        """
        Get start of day (00:00:00) for given datetime.
        
        Args:
            dt: Datetime object
            
        Returns:
            Start of day datetime
        """
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    
    @staticmethod
    def get_end_of_day(dt: datetime) -> datetime:
        """
        Get end of day (23:59:59.999999) for given datetime.
        
        Args:
            dt: Datetime object
            
        Returns:
            End of day datetime
        """
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    @staticmethod
    def get_start_of_week(dt: datetime) -> datetime:
        """
        Get start of week (Monday) for given datetime.
        
        Args:
            dt: Datetime object
            
        Returns:
            Start of week datetime
        """
        days_since_monday = dt.weekday()
        return DateUtils.get_start_of_day(dt - timedelta(days=days_since_monday))
    
    @staticmethod
    def get_end_of_week(dt: datetime) -> datetime:
        """
        Get end of week (Sunday) for given datetime.
        
        Args:
            dt: Datetime object
            
        Returns:
            End of week datetime
        """
        days_until_sunday = 6 - dt.weekday()
        return DateUtils.get_end_of_day(dt + timedelta(days=days_until_sunday))
    
    @staticmethod
    def get_start_of_month(dt: datetime) -> datetime:
        """
        Get start of month for given datetime.
        
        Args:
            dt: Datetime object
            
        Returns:
            Start of month datetime
        """
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    @staticmethod
    def get_end_of_month(dt: datetime) -> datetime:
        """
        Get end of month for given datetime.
        
        Args:
            dt: Datetime object
            
        Returns:
            End of month datetime
        """
        # Get last day of month
        last_day = calendar.monthrange(dt.year, dt.month)[1]
        return dt.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
    
    @staticmethod
    def get_start_of_year(dt: datetime) -> datetime:
        """
        Get start of year for given datetime.
        
        Args:
            dt: Datetime object
            
        Returns:
            Start of year datetime
        """
        return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    @staticmethod
    def get_end_of_year(dt: datetime) -> datetime:
        """
        Get end of year for given datetime.
        
        Args:
            dt: Datetime object
            
        Returns:
            End of year datetime
        """
        return dt.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Format duration in seconds to human readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f}h"
        else:
            days = seconds / 86400
            return f"{days:.1f}d"
    
    @staticmethod
    def format_relative_time(dt: datetime, reference: Optional[datetime] = None) -> str:
        """
        Format datetime as relative time (e.g., "2 hours ago").
        
        Args:
            dt: Datetime to format
            reference: Reference datetime (default: current time)
            
        Returns:
            Relative time string
        """
        if reference is None:
            reference = DateUtils.get_current_datetime()
        
        diff = reference - dt
        
        if diff.total_seconds() < 60:
            return "just now"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.days < 7:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.days < 30:
            weeks = int(diff.days / 7)
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        elif diff.days < 365:
            months = int(diff.days / 30)
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = int(diff.days / 365)
            return f"{years} year{'s' if years != 1 else ''} ago"
    
    @staticmethod
    def get_timezone_offset(dt: datetime) -> str:
        """
        Get timezone offset string.
        
        Args:
            dt: Datetime object
            
        Returns:
            Timezone offset string (e.g., "+02:00")
        """
        if dt.tzinfo is None:
            return "+00:00"
        
        offset = dt.tzinfo.utcoffset(dt)
        if offset is None:
            return "+00:00"
        
        total_seconds = int(offset.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        return f"{hours:+03d}:{minutes:02d}"
    
    @staticmethod
    def convert_timezone(dt: datetime, target_tz: timezone) -> datetime:
        """
        Convert datetime to target timezone.
        
        Args:
            dt: Source datetime
            target_tz: Target timezone
            
        Returns:
            Converted datetime
        """
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt.astimezone(target_tz)
    
    @staticmethod
    def get_weekday_name(dt: datetime, short: bool = False) -> str:
        """
        Get weekday name.
        
        Args:
            dt: Datetime object
            short: Return short name
            
        Returns:
            Weekday name
        """
        if short:
            return dt.strftime("%a")
        else:
            return dt.strftime("%A")
    
    @staticmethod
    def get_month_name(dt: datetime, short: bool = False) -> str:
        """
        Get month name.
        
        Args:
            dt: Datetime object
            short: Return short name
            
        Returns:
            Month name
        """
        if short:
            return dt.strftime("%b")
        else:
            return dt.strftime("%B")
    
    @staticmethod
    def is_leap_year(year: int) -> bool:
        """
        Check if year is leap year.
        
        Args:
            year: Year to check
            
        Returns:
            True if leap year
        """
        return calendar.isleap(year)
    
    @staticmethod
    def get_days_in_month(year: int, month: int) -> int:
        """
        Get number of days in month.
        
        Args:
            year: Year
            month: Month (1-12)
            
        Returns:
            Number of days in month
        """
        return calendar.monthrange(year, month)[1]
    
    @staticmethod
    def get_quarter(dt: datetime) -> int:
        """
        Get quarter of year for datetime.
        
        Args:
            dt: Datetime object
            
        Returns:
            Quarter number (1-4)
        """
        return (dt.month - 1) // 3 + 1
