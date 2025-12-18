"""
LeapYear Plugin

Provides fast leap year calculations using Ben Joffe's algorithm.
This plugin offers efficient leap year detection for the NoDupeLabs system.

Features:
- Fast leap year detection using optimized algorithm
- Support for Gregorian and Julian calendars
- Batch processing for multiple years
- ISO 8601 date validation with leap year awareness
- Runtime configuration and caching

Algorithm source: https://www.benjoffe.com/fast-leap-year

Example usage:
    from nodupe.plugins.leap_year import LeapYearPlugin
    
    plugin = LeapYearPlugin()
    is_leap = plugin.is_leap_year(2024)
    leap_years = plugin.find_leap_years(2000, 2050)
    is_valid_date = plugin.is_valid_date(2024, 2, 29)  # True (leap year)
"""

from .leap_year import LeapYearPlugin

__all__ = ["LeapYearPlugin"]
