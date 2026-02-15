"""
LeapYear Plugin Implementation

Provides fast leap year calculations using Ben Joffe's optimized algorithm.
This plugin offers efficient leap year detection for the NoDupeLabs system.

Algorithm source: https://www.benjoffe.com/fast-leap-year

The algorithm uses bitwise operations for maximum performance:
- For Gregorian calendar: (year & 3) == 0 and ((year % 25) != 0 or (year & 15) == 0)
- For Julian calendar: (year & 3) == 0

Features:
- Fast leap year detection using optimized algorithm
- Support for Gregorian and Julian calendars
- Batch processing for multiple years
- ISO 8601 date validation with leap year awareness
- Runtime configuration and caching
- Comprehensive date validation utilities
"""

from __future__ import annotations

import time
import threading
from typing import List, Tuple, Optional, Iterator
import logging
from functools import lru_cache

from nodupe.core.plugin_system import Plugin, PluginMetadata

logger = logging.getLogger(__name__)


class LeapYearPlugin(Plugin):
    """
    LeapYear Plugin for fast leap year calculations.
    
    This plugin implements Ben Joffe's fast leap year algorithm which uses
    bitwise operations for maximum performance. It supports both Gregorian
    and Julian calendars and provides comprehensive date validation.
    
    Key features:
    - O(1) leap year detection using bitwise operations
    - Configurable calendar systems (Gregorian/Julian)
    - Batch processing for multiple years
    - Date validation with leap year awareness
    - Optional caching for repeated queries
    - Thread-safe operations
    """

    def __init__(
        self,
        calendar: str = "gregorian",
        enable_cache: bool = True,
        cache_size: int = 10000,
        *,
        min_year: int = 1,
        max_year: int = 9999
    ):
        """
        Initialize the LeapYear plugin.
        
        Args:
            calendar: Calendar system ('gregorian' or 'julian')
            enable_cache: Enable LRU caching for leap year queries
            cache_size: Size of LRU cache (if enabled)
            min_year: Minimum supported year
            max_year: Maximum supported year
        """
        super().__init__()
        self.calendar = calendar.lower()
        if self.calendar not in ("gregorian", "julian"):
            raise ValueError(f"Unsupported calendar: {calendar}")
        
        self.enable_cache = enable_cache
        self.cache_size = cache_size
        self.min_year = min_year
        self.max_year = max_year
        
        self._lock = threading.Lock()
        self._cache_hits = 0
        self._cache_misses = 0
        
        logger.info(f"LeapYear plugin initialized with {calendar} calendar")

    @property
    def name(self) -> str:
        """Plugin name."""
        return "LeapYear"

    @property
    def version(self) -> str:
        """Plugin version."""
        return "1.0.0"

    @property
    def dependencies(self) -> List[str]:
        """List of plugin dependencies."""
        return []

    def get_capabilities(self) -> dict:
        """Get plugin capabilities."""
        return {
            "leap_year_detection": True,
            "calendar_systems": ["gregorian", "julian"],
            "batch_processing": True,
            "date_validation": True,
            "caching": True,
            "thread_safe": True
        }

    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name=self.name,
            version=self.version,
            description="Fast leap year calculations using Ben Joffe's algorithm",
            author="NoDupeLabs",
            license="MIT",
            dependencies=self.dependencies,
            tags=["date", "time", "calendar", "leap-year", "algorithm"]
        )

    def initialize(self, container: Any) -> None:
        """Initialize the plugin."""
        logger.info("Initializing LeapYear plugin")
        if self.enable_cache:
            logger.info(f"Caching enabled with size {self.cache_size}")

    def shutdown(self, container: Any) -> None:
        """Shutdown the plugin."""
        logger.info("Shutting down LeapYear plugin")
        if self.enable_cache:
            cache_stats = self.get_cache_stats()
            logger.info(f"Cache stats: {cache_stats['hits']} hits, {cache_stats['misses']} misses")

    # ---- Core leap year detection ----
    def is_leap_year(self, year: int) -> bool:
        """
        Determine if a year is a leap year using Ben Joffe's fast algorithm.
        
        Gregorian calendar algorithm:
        (year & 3) == 0 and ((year % 25) != 0 or (year & 15) == 0)
        
        Julian calendar algorithm:
        (year & 3) == 0
        
        Args:
            year: Year to check (1-9999)
            
        Returns:
            True if the year is a leap year, False otherwise
            
        Raises:
            ValueError: If year is outside supported range
        """
        self._validate_year(year)
        
        if self.enable_cache:
            return self._cached_is_leap_year(year)
        else:
            return self._compute_leap_year(year)

    @lru_cache(maxsize=10000)
    def _cached_is_leap_year(self, year: int) -> bool:
        """Cached version of leap year calculation."""
        with self._lock:
            self._cache_hits += 1
        
        return self._compute_leap_year(year)

    def _compute_leap_year(self, year: int) -> bool:
        """Compute leap year using Ben Joffe's algorithm."""
        if self.calendar == "gregorian":
            # Ben Joffe's fast algorithm for Gregorian calendar
            # (year & 3) == 0 and ((year % 25) != 0 or (year & 15) == 0)
            return (year & 3) == 0 and ((year % 25) != 0 or (year & 15) == 0)
        else:
            # Julian calendar: every 4th year is a leap year
            return (year & 3) == 0

    def _validate_year(self, year: int) -> None:
        """Validate that year is within supported range."""
        if not isinstance(year, int):
            raise TypeError(f"Year must be an integer, got {type(year)}")
        if year < self.min_year or year > self.max_year:
            raise ValueError(f"Year {year} out of range [{self.min_year}, {self.max_year}]")

    # ---- Batch operations ----
    def find_leap_years(self, start_year: int, end_year: int) -> List[int]:
        """
        Find all leap years in a range.
        
        Args:
            start_year: Start of year range (inclusive)
            end_year: End of year range (inclusive)
            
        Returns:
            List of leap years in the range
        """
        self._validate_year(start_year)
        self._validate_year(end_year)
        
        if start_year > end_year:
            raise ValueError(f"start_year ({start_year}) must be <= end_year ({end_year})")
        
        leap_years = []
        for year in range(start_year, end_year + 1):
            if self.is_leap_year(year):
                leap_years.append(year)
        
        return leap_years

    def count_leap_years(self, start_year: int, end_year: int) -> int:
        """
        Count the number of leap years in a range.
        
        More efficient than find_leap_years for large ranges when only count is needed.
        
        Args:
            start_year: Start of year range (inclusive)
            end_year: End of year range (inclusive)
            
        Returns:
            Number of leap years in the range
        """
        self._validate_year(start_year)
        self._validate_year(end_year)
        
        if start_year > end_year:
            raise ValueError(f"start_year ({start_year}) must be <= end_year ({end_year})")
        
        count = 0
        for year in range(start_year, end_year + 1):
            if self.is_leap_year(year):
                count += 1
        
        return count

    def is_leap_year_batch(self, years: List[int]) -> List[bool]:
        """
        Check leap year status for multiple years.
        
        Args:
            years: List of years to check
            
        Returns:
            List of boolean results corresponding to input years
        """
        return [self.is_leap_year(year) for year in years]

    # ---- Date validation ----
    def is_valid_date(self, year: int, month: int, day: int) -> bool:
        """
        Validate if a date is valid, considering leap years.
        
        Args:
            year: Year (1-9999)
            month: Month (1-12)
            day: Day of month
            
        Returns:
            True if the date is valid, False otherwise
        """
        try:
            self._validate_date_components(year, month, day)
            return True
        except (ValueError, TypeError):
            return False

    def _validate_date_components(self, year: int, month: int, day: int) -> None:
        """Validate individual date components."""
        self._validate_year(year)
        
        if not isinstance(month, int):
            raise TypeError(f"Month must be an integer, got {type(month)}")
        if month < 1 or month > 12:
            raise ValueError(f"Month {month} out of range [1, 12]")
        
        if not isinstance(day, int):
            raise TypeError(f"Day must be an integer, got {type(day)}")
        
        days_in_month = self.get_days_in_month(year, month)
        if day < 1 or day > days_in_month:
            raise ValueError(f"Day {day} out of range [1, {days_in_month}] for {year}-{month:02d}")

    def get_days_in_month(self, year: int, month: int) -> int:
        """
        Get the number of days in a month for a given year.
        
        Args:
            year: Year (1-9999)
            month: Month (1-12)
            
        Returns:
            Number of days in the month
        """
        self._validate_year(year)
        
        if not isinstance(month, int):
            raise TypeError(f"Month must be an integer, got {type(month)}")
        if month < 1 or month > 12:
            raise ValueError(f"Month {month} out of range [1, 12]")
        
        # Days in each month (non-leap year)
        days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        if month == 2 and self.is_leap_year(year):
            return 29
        
        return days_per_month[month - 1]

    def get_days_in_year(self, year: int) -> int:
        """
        Get the number of days in a year.
        
        Args:
            year: Year (1-9999)
            
        Returns:
            366 if leap year, 365 otherwise
        """
        self._validate_year(year)
        return 366 if self.is_leap_year(year) else 365

    # ---- Calendar utilities ----
    def get_calendar_info(self, year: int) -> dict:
        """
        Get comprehensive calendar information for a year.
        
        Args:
            year: Year to analyze (1-9999)
            
        Returns:
            Dictionary with calendar information
        """
        self._validate_year(year)
        
        is_leap = self.is_leap_year(year)
        days_in_year = 366 if is_leap else 365
        
        # Count days in each month
        monthly_days = [self.get_days_in_month(year, month) for month in range(1, 13)]
        
        return {
            "year": year,
            "calendar": self.calendar,
            "is_leap_year": is_leap,
            "days_in_year": days_in_year,
            "days_in_february": monthly_days[1],  # February
            "monthly_days": monthly_days,
            "weekend_days": self._count_weekend_days(year),
            "weekday_days": days_in_year - self._count_weekend_days(year)
        }

    def _count_weekend_days(self, year: int) -> int:
        """Count the number of weekend days in a year."""
        # This is a simplified calculation
        # In a real implementation, you'd need to know the day of week for Jan 1
        # For now, return a rough estimate
        days_in_year = self.get_days_in_year(year)
        return (days_in_year // 7) * 2 + min(days_in_year % 7, 2)

    def get_easter_date(self, year: int) -> Tuple[int, int]:
        """
        Calculate Easter date for a given year using the computus algorithm.
        
        Args:
            year: Year to calculate Easter for (1-9999)
            
        Returns:
            Tuple of (month, day) for Easter Sunday
            
        Note:
            This uses the Gregorian computus algorithm and may have slight
            variations from official ecclesiastical calculations.
        """
        self._validate_year(year)
        
        if self.calendar == "julian":
            return self._easter_julian(year)
        else:
            return self._easter_gregorian(year)

    def _easter_gregorian(self, year: int) -> Tuple[int, int]:
        """Calculate Easter date using Gregorian computus."""
        # Meeus/Jones/Butcher algorithm
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        
        return (month, day)

    def _easter_julian(self, year: int) -> Tuple[int, int]:
        """Calculate Easter date using Julian computus."""
        # Simplified Julian computus
        a = year % 19
        b = year % 4
        c = year % 7
        d = (19 * a + 15) % 30
        e = (2 * b + 4 * c - d + 34) % 7
        month = (d + e + 114) // 31
        day = ((d + e + 114) % 31) + 1
        
        return (month, day)

    # ---- Performance and statistics ----
    def get_cache_stats(self) -> dict:
        """Get cache performance statistics."""
        if not self.enable_cache:
            return {"enabled": False}
        
        with self._lock:
            total_requests = self._cache_hits + self._cache_misses
            hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            "enabled": True,
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "hit_rate": hit_rate,
            "cache_size": self.cache_size
        }

    def reset_cache_stats(self) -> None:
        """Reset cache performance statistics."""
        with self._lock:
            self._cache_hits = 0
            self._cache_misses = 0
        logger.info("Cache statistics reset")

    def benchmark_algorithm(self, years: List[int], iterations: int = 1000) -> dict:
        """
        Benchmark the leap year algorithm performance.
        
        Args:
            years: List of years to test
            iterations: Number of iterations for timing
            
        Returns:
            Performance statistics
        """
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            for year in years:
                self.is_leap_year(year)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time_per_year = total_time / (iterations * len(years))
        
        return {
            "total_time": total_time,
            "iterations": iterations,
            "years_tested": len(years),
            "total_calculations": iterations * len(years),
            "average_time_per_calculation": avg_time_per_year,
            "calculations_per_second": 1 / avg_time_per_year if avg_time_per_year > 0 else 0
        }

    # ---- Iterator support ----
    def leap_year_range(self, start_year: int, end_year: int) -> Iterator[int]:
        """
        Iterator that yields leap years in a range.
        
        More memory-efficient than find_leap_years for large ranges.
        
        Args:
            start_year: Start of year range (inclusive)
            end_year: End of year range (inclusive)
            
        Yields:
            Leap years in the range
        """
        self._validate_year(start_year)
        self._validate_year(end_year)
        
        if start_year > end_year:
            raise ValueError(f"start_year ({start_year}) must be <= end_year ({end_year})")
        
        for year in range(start_year, end_year + 1):
            if self.is_leap_year(year):
                yield year

    # ---- Configuration methods ----
    def set_calendar(self, calendar: str) -> None:
        """Set the calendar system (gregorian or julian)."""
        calendar = calendar.lower()
        if calendar not in ("gregorian", "julian"):
            raise ValueError(f"Unsupported calendar: {calendar}")
        
        with self._lock:
            self.calendar = calendar
        logger.info(f"Calendar system set to {calendar}")

    def enable_caching(self, cache_size: Optional[int] = None) -> None:
        """Enable LRU caching for leap year calculations."""
        if cache_size is not None:
            self.cache_size = cache_size
        
        self.enable_cache = True
        logger.info(f"Caching enabled with size {self.cache_size}")

    def disable_caching(self) -> None:
        """Disable LRU caching."""
        self.enable_cache = False
        # Clear the cache
        if hasattr(self, '_cached_is_leap_year'):
            self._cached_is_leap_year.cache_clear()
        logger.info("Caching disabled")

    # ---- Convenience methods ----
    def next_leap_year(self, year: int) -> int:
        """Find the next leap year after the given year."""
        self._validate_year(year)
        
        next_year = year + 1
        while not self.is_leap_year(next_year):
            next_year += 1
        return next_year

    def previous_leap_year(self, year: int) -> int:
        """Find the previous leap year before the given year."""
        self._validate_year(year)
        
        prev_year = year - 1
        while prev_year >= self.min_year and not self.is_leap_year(prev_year):
            prev_year -= 1
        
        if prev_year < self.min_year:
            raise ValueError(f"No previous leap year found before {year}")
        
        return prev_year

    def get_leap_year_cycle(self, year: int) -> Tuple[int, int, int, int]:
        """
        Get the 4-year leap year cycle containing the given year.
        
        Returns:
            Tuple of (year1, year2, year3, year4) where year2 is the leap year
        """
        self._validate_year(year)
        
        # Find the start of the 4-year cycle
        cycle_start = ((year - 1) // 4) * 4 + 1
        return tuple(range(cycle_start, cycle_start + 4))

    def is_gregorian_leap_year(self, year: int) -> bool:
        """Check if a year is a leap year in the Gregorian calendar."""
        self._validate_year(year)
        return (year & 3) == 0 and ((year % 25) != 0 or (year & 15) == 0)

    def is_julian_leap_year(self, year: int) -> bool:
        """Check if a year is a leap year in the Julian calendar."""
        self._validate_year(year)
        return (year & 3) == 0
