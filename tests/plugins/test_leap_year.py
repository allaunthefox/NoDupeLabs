"""
Tests for LeapYear Plugin

Tests the fast leap year calculations using Ben Joffe's algorithm.
These tests verify the correctness of leap year detection for both
Gregorian and Julian calendars, as well as date validation and utilities.
"""

import pytest
import threading
from unittest.mock import patch
import time

from nodupe.plugins.leap_year import LeapYearPlugin


class TestLeapYearPlugin:
    """Test suite for LeapYearPlugin."""

    def test_plugin_metadata(self):
        """Test that plugin metadata is correctly defined."""
        plugin = LeapYearPlugin()
        
        assert plugin.name == "leapyear"
        assert plugin.version == "1.0"
        assert plugin.dependencies == []

    def test_initialization_defaults(self):
        """Test plugin initialization with default values."""
        plugin = LeapYearPlugin()
        
        assert plugin.calendar == "gregorian"
        assert plugin.enable_cache is True
        assert plugin.cache_size == 10000
        assert plugin.min_year == 1
        assert plugin.max_year == 9999

    def test_initialization_with_metadata(self):
        """Test plugin initialization with custom metadata."""
        metadata = {
            "uuid": "123e4567-e89b-12d3-a456-426614174001",
            "name": "leapyear_test",
            "display_name": "Test Leap Year Calculator",
            "version": "v1.1.0",
            "description": "Test version of leap year calculator",
            "author": "Test Author",
            "category": "test",
            "compatibility": ["nodupe"],
            "marketplace_id": "test-leapyear-calculator"
        }
        plugin = LeapYearPlugin(metadata)
        
        assert plugin.name == "leapyear_test"
        assert plugin.display_name == "Test Leap Year Calculator"
        assert plugin.version == "v1.1.0"
        assert plugin.author == "Test Author"
        assert plugin.category == "test"
        assert plugin.calendar == "gregorian"  # Default values still apply
        assert plugin.enable_cache is True
        assert plugin.cache_size == 10000
        assert plugin.min_year == 1
        assert plugin.max_year == 999

    def test_invalid_calendar(self):
        """Test that invalid calendar raises ValueError."""
        plugin = LeapYearPlugin()
        with pytest.raises(ValueError, match="Unsupported calendar"):
            plugin.set_calendar("invalid")

    def test_year_validation(self):
        """Test year validation."""
        plugin = LeapYearPlugin(min_year=1900, max_year=2100)
        
        # Valid years
        plugin._validate_year(1900)
        plugin._validate_year(2000)
        plugin._validate_year(2100)
        
        # Invalid years
        with pytest.raises(ValueError, match="out of range"):
            plugin._validate_year(1899)
        
        with pytest.raises(ValueError, match="out of range"):
            plugin._validate_year(2101)
        
        with pytest.raises(TypeError, match="must be an integer"):
            plugin._validate_year("2000")

    # ---- Gregorian leap year tests ----
    def test_gregorian_leap_years(self):
        """Test known Gregorian leap years."""
        plugin = LeapYearPlugin(calendar="gregorian")
        
        # Known leap years
        leap_years = [2000, 2004, 2008, 2012, 2016, 2020, 2024, 2028, 2032]
        for year in leap_years:
            assert plugin.is_leap_year(year), f"{year} should be a leap year"
        
        # Known non-leap years
        non_leap_years = [1900, 2100, 2200, 2300, 2001, 2002, 2003, 2005]
        for year in non_leap_years:
            assert not plugin.is_leap_year(year), f"{year} should not be a leap year"

    def test_gregorian_century_years(self):
        """Test Gregorian century year rules."""
        plugin = LeapYearPlugin(calendar="gregorian")
        
        # Divisible by 400 (leap years)
        assert plugin.is_leap_year(1600)
        assert plugin.is_leap_year(2000)
        assert plugin.is_leap_year(2400)
        
        # Divisible by 100 but not 400 (not leap years)
        assert not plugin.is_leap_year(1700)
        assert not plugin.is_leap_year(1800)
        assert not plugin.is_leap_year(1900)
        assert not plugin.is_leap_year(2100)

    # ---- Julian leap year tests ----
    def test_julian_leap_years(self):
        """Test Julian calendar leap years."""
        plugin = LeapYearPlugin(calendar="julian")
        
        # Every 4th year is a leap year in Julian calendar
        leap_years = [1896, 1900, 1904, 1908, 2000, 2004, 2008]
        for year in leap_years:
            assert plugin.is_leap_year(year), f"{year} should be a leap year in Julian calendar"
        
        # Non-leap years
        non_leap_years = [1897, 1898, 1899, 1901, 1902, 1903, 2001, 2002, 2003]
        for year in non_leap_years:
            assert not plugin.is_leap_year(year), f"{year} should not be a leap year in Julian calendar"

    # ---- Algorithm correctness tests ----
    def test_ben_joffe_algorithm_gregorian(self):
        """Test Ben Joffe's algorithm for Gregorian calendar."""
        plugin = LeapYearPlugin(calendar="gregorian")
        
        # Test the algorithm directly
        test_years = [1900, 2000, 2024, 2100, 2023, 2025]
        
        for year in test_years:
            # Ben Joffe's algorithm: (year & 3) == 0 and ((year % 25) != 0 or (year & 15) == 0)
            expected = (year & 3) == 0 and ((year % 25) != 0 or (year & 15) == 0)
            actual = plugin.is_leap_year(year)
            assert actual == expected, f"Algorithm mismatch for {year}"

    def test_ben_joffe_algorithm_julian(self):
        """Test Ben Joffe's algorithm for Julian calendar."""
        plugin = LeapYearPlugin(calendar="julian")
        
        # Test the algorithm directly: (year & 3) == 0
        test_years = [1896, 1897, 1898, 1899, 1900, 1904, 2000, 2001]
        
        for year in test_years:
            expected = (year & 3) == 0
            actual = plugin.is_leap_year(year)
            assert actual == expected, f"Algorithm mismatch for {year} in Julian calendar"

    # ---- Batch operations tests ----
    def test_find_leap_years(self):
        """Test finding leap years in a range."""
        plugin = LeapYearPlugin(calendar="gregorian")
        
        leap_years = plugin.find_leap_years(2000, 2020)
        expected = [2000, 2004, 2008, 2012, 2016, 2020]
        assert leap_years == expected

    def test_count_leap_years(self):
        """Test counting leap years in a range."""
        plugin = LeapYearPlugin(calendar="gregorian")
        
        count = plugin.count_leap_years(2000, 2020)
        assert count == 6  # 2000, 2004, 2008, 2012, 2016, 2020

    def test_is_leap_year_batch(self):
        """Test batch leap year checking."""
        plugin = LeapYearPlugin(calendar="gregorian")
        
        years = [2000, 2001, 2004, 2005, 2100, 2104]
        results = plugin.is_leap_year_batch(years)
        expected = [True, False, True, False, False, True]
        assert results == expected

    def test_leap_year_range_iterator(self):
        """Test leap year range iterator."""
        plugin = LeapYearPlugin(calendar="gregorian")
        
        leap_years = list(plugin.leap_year_range(2000, 2020))
        expected = [2000, 2004, 2008, 2012, 2016, 2020]
        assert leap_years == expected

    # ---- Date validation tests ----
    def test_is_valid_date(self):
        """Test date validation."""
        plugin = LeapYearPlugin()
        
        # Valid dates
        assert plugin.is_valid_date(2024, 1, 31)  # January
        assert plugin.is_valid_date(2024, 2, 29)  # Leap year February
        assert plugin.is_valid_date(2023, 2, 28)  # Non-leap year February
        assert plugin.is_valid_date(2024, 12, 31)  # December
        
        # Invalid dates
        assert not plugin.is_valid_date(2023, 2, 29)  # Non-leap year February 29
        assert not plugin.is_valid_date(2024, 2, 30)  # Invalid February day
        assert not plugin.is_valid_date(2024, 4, 31)  # April has 30 days
        assert not plugin.is_valid_date(2024, 13, 1)  # Invalid month
        assert not plugin.is_valid_date(2024, 1, 0)   # Invalid day

    def test_get_days_in_month(self):
        """Test days in month calculation."""
        plugin = LeapYearPlugin()
        
        # Regular months
        assert plugin.get_days_in_month(2024, 1) == 31
        assert plugin.get_days_in_month(2024, 4) == 30
        assert plugin.get_days_in_month(2024, 6) == 30
        
        # February in leap year
        assert plugin.get_days_in_month(2024, 2) == 29
        
        # February in non-leap year
        assert plugin.get_days_in_month(2023, 2) == 28

    def test_get_days_in_year(self):
        """Test days in year calculation."""
        plugin = LeapYearPlugin()
        
        assert plugin.get_days_in_year(2024) == 366  # Leap year
        assert plugin.get_days_in_year(2023) == 365  # Non-leap year

    # ---- Calendar utilities tests ----
    def test_get_calendar_info(self):
        """Test calendar information retrieval."""
        plugin = LeapYearPlugin()
        
        info = plugin.get_calendar_info(2024)
        
        assert info["year"] == 2024
        assert info["calendar"] == "gregorian"
        assert info["is_leap_year"] is True
        assert info["days_in_year"] == 366
        assert info["days_in_february"] == 29
        assert len(info["monthly_days"]) == 12
        assert info["monthly_days"][1] == 29  # February

    def test_get_easter_date(self):
        """Test Easter date calculation."""
        plugin = LeapYearPlugin(calendar="gregorian")
        
        # Known Easter dates
        easter_2024 = plugin.get_easter_date(2024)
        assert easter_2024 == (3, 31)  # March 31, 2024
        
        easter_2025 = plugin.get_easter_date(2025)
        assert easter_2025 == (4, 20)  # April 20, 2025

    # ---- Performance and caching tests ----
    def test_caching_enabled(self):
        """Test that caching works correctly."""
        plugin = LeapYearPlugin(enable_cache=True, cache_size=100)
        
        # First call (cache miss)
        result1 = plugin.is_leap_year(2024)
        stats = plugin.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1
        
        # Second call (cache hit)
        result2 = plugin.is_leap_year(2024)
        stats = plugin.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert result1 == result2

    def test_caching_disabled(self):
        """Test that caching can be disabled."""
        plugin = LeapYearPlugin(enable_cache=False)
        
        plugin.is_leap_year(2024)
        stats = plugin.get_cache_stats()
        assert stats["enabled"] is False

    def test_reset_cache_stats(self):
        """Test cache statistics reset."""
        plugin = LeapYearPlugin()
        
        plugin.is_leap_year(2024)
        plugin.reset_cache_stats()
        
        stats = plugin.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_benchmark_algorithm(self):
        """Test algorithm benchmarking."""
        plugin = LeapYearPlugin()
        
        years = list(range(1900, 2100))
        stats = plugin.benchmark_algorithm(years, iterations=10)
        
        assert "total_time" in stats
        assert "iterations" in stats
        assert "years_tested" in stats
        assert "total_calculations" in stats
        assert "average_time_per_calculation" in stats
        assert "calculations_per_second" in stats
        
        assert stats["iterations"] == 10
        assert stats["years_tested"] == 200
        assert stats["total_calculations"] == 2000

    # ---- Configuration tests ----
    def test_set_calendar(self):
        """Test calendar system switching."""
        plugin = LeapYearPlugin()
        
        # Switch to Julian
        plugin.set_calendar("julian")
        assert plugin.calendar == "julian"
        
        # Switch back to Gregorian
        plugin.set_calendar("gregorian")
        assert plugin.calendar == "gregorian"
        
        # Invalid calendar
        with pytest.raises(ValueError):
            plugin.set_calendar("invalid")

    def test_enable_disable_caching(self):
        """Test caching enable/disable."""
        plugin = LeapYearPlugin(enable_cache=False)
        
        # Enable caching
        plugin.enable_caching(cache_size=5000)
        assert plugin.enable_cache is True
        assert plugin.cache_size == 5000
        
        # Disable caching
        plugin.disable_caching()
        assert plugin.enable_cache is False

    # ---- Convenience methods tests ----
    def test_next_leap_year(self):
        """Test finding next leap year."""
        plugin = LeapYearPlugin()
        
        assert plugin.next_leap_year(2023) == 2024
        assert plugin.next_leap_year(2024) == 2028
        assert plugin.next_leap_year(2099) == 2104

    def test_previous_leap_year(self):
        """Test finding previous leap year."""
        plugin = LeapYearPlugin()
        
        assert plugin.previous_leap_year(2025) == 2024
        assert plugin.previous_leap_year(2024) == 2020
        assert plugin.previous_leap_year(1901) == 1896

    def test_previous_leap_year_error(self):
        """Test error when no previous leap year exists."""
        plugin = LeapYearPlugin(min_year=2000)
        
        with pytest.raises(ValueError, match="No previous leap year"):
            plugin.previous_leap_year(2000)

    def test_get_leap_year_cycle(self):
        """Test leap year cycle calculation."""
        plugin = LeapYearPlugin()
        
        # Year in leap year position
        cycle = plugin.get_leap_year_cycle(2024)
        assert cycle == (2021, 2022, 2023, 2024)
        
        # Year in non-leap position
        cycle = plugin.get_leap_year_cycle(2025)
        assert cycle == (2021, 2022, 2023, 2024)

    def test_direct_calendar_methods(self):
        """Test direct calendar method calls."""
        # Gregorian
        assert LeapYearPlugin().is_gregorian_leap_year(2000) is True
        assert LeapYearPlugin().is_gregorian_leap_year(1900) is False
        
        # Julian
        assert LeapYearPlugin().is_julian_leap_year(1900) is True
        assert LeapYearPlugin().is_julian_leap_year(1899) is False

    # ---- Thread safety tests ----
    def test_thread_safety(self):
        """Test that the plugin is thread-safe."""
        plugin = LeapYearPlugin()
        
        results = []
        errors = []
        
        def worker():
            try:
                for _ in range(100):
                    result = plugin.is_leap_year(2024)
                    results.append(result)
            except Exception as e:
                errors.append(e)
        
        threads = []
        for _ in range(10):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert all(results), "All results should be True"
        assert len(results) == 1000  # 10 threads * 100 iterations

    # ---- Edge cases tests ----
    def test_boundary_years(self):
        """Test boundary year values."""
        plugin = LeapYearPlugin(min_year=1, max_year=9999)
        
        # Test minimum year
        assert plugin.is_leap_year(1) is False  # Not divisible by 4
        
        # Test maximum year
        assert plugin.is_leap_year(9999) is False  # Not divisible by 4
        
        # Test year 4 (first leap year)
        assert plugin.is_leap_year(4) is True

    def test_large_year_ranges(self):
        """Test with large year ranges."""
        plugin = LeapYearPlugin()
        
        # Test a large range
        start, end = 1000, 3000
        count = plugin.count_leap_years(start, end)
        
        # Should be approximately 1/4 of the years, minus century exceptions
        expected_approx = (end - start + 1) // 4
        assert abs(count - expected_approx) < 10  # Allow some variation

    def test_plugin_lifecycle(self):
        """Test plugin initialization and shutdown."""
        plugin = LeapYearPlugin()
        
        # Test initialization
        plugin.initialize()
        
        # Test shutdown
        plugin.shutdown()

    def test_invalid_date_components(self):
        """Test invalid date component validation."""
        plugin = LeapYearPlugin()
        
        # Test invalid month
        with pytest.raises(ValueError, match="Month.*out of range"):
            plugin._validate_date_components(2024, 13, 1)
        
        # Test invalid day
        with pytest.raises(ValueError, match="Day.*out of range"):
            plugin._validate_date_components(2024, 2, 30)
        
        # Test invalid types
        with pytest.raises(TypeError, match="Month must be an integer"):
            plugin._validate_date_components(2024, "2", 1)
        
        with pytest.raises(TypeError, match="Day must be an integer"):
            plugin._validate_date_components(2024, 2, "1")
