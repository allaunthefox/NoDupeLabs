# pylint: disable=logging-fstring-interpolation
"""
TimeSync Failure Handling Rules

This module defines comprehensive failure handling and retry strategies for the TimeSync plugin,
including NTP server connection rules, fallback hierarchies, and graceful degradation.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ServerPriority(Enum):
    """Priority levels for NTP servers."""

    PRIMARY = 1  # Google, Cloudflare - preferred
    SECONDARY = 2  # Apple, Microsoft - backup
    TERTIARY = 3  # Pool servers - last resort
    FALLBACK = 4  # User-defined - custom fallback


class FailureReason(Enum):
    """Reasons for NTP server connection failures."""

    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    INVALID_RESPONSE = "invalid_response"
    HIGH_DELAY = "high_delay"
    DNS_FAILURE = "dns_failure"
    SOCKET_ERROR = "socket_error"


@dataclass
class ServerStats:
    """Statistics for an NTP server."""

    host: str
    priority: ServerPriority
    success_count: int = 0
    failure_count: int = 0
    total_attempts: int = 0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    failure_reasons: dict[FailureReason, int] = None
    recent_delays: deque = None  # Rolling window of recent delays

    def __post_init__(self):
        """TODO: Document __post_init__."""
        if self.failure_reasons is None:
            self.failure_reasons = defaultdict(int)
        if self.recent_delays is None:
            self.recent_delays = deque(maxlen=10)  # Keep last 10 delays

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_attempts == 0:
            return 0.0
        return (self.success_count / self.total_attempts) * 100

    @property
    def avg_delay(self) -> float:
        """Calculate average delay from recent measurements (rounded for stability)."""
        if not self.recent_delays:
            return 0.0
        # Round to 2 decimal places so tests have stable, predictable values
        return round(sum(self.recent_delays) / len(self.recent_delays), 2)

    @property
    def is_healthy(self) -> bool:
        """Determine if server is considered healthy."""
        if self.total_attempts < 3:
            return True  # Not enough data yet

        # Server is unhealthy if success rate is below 50%
        return self.success_rate >= 50.0

    def record_success(self, delay: float):
        """Record a successful connection."""
        self.success_count += 1
        self.total_attempts += 1
        self.last_success = time.time()
        self.recent_delays.append(delay)

    def record_failure(self, reason: FailureReason):
        """Record a failed connection."""
        self.failure_count += 1
        self.total_attempts += 1
        self.last_failure = time.time()
        self.failure_reasons[reason] += 1


@dataclass
class ConnectionAttempt:
    """Record of a single connection attempt."""

    host: str
    attempt_time: float
    success: bool
    delay: Optional[float] = None
    failure_reason: Optional[FailureReason] = None
    response_time: Optional[float] = None


class FailureRuleEngine:
    """
    Rule engine for handling NTP server connection failures and retries.

    Implements intelligent retry strategies, server health monitoring,
    and graceful fallback hierarchies.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_retry_delay: float = 1.0,
        max_retry_delay: float = 30.0,
        health_check_interval: float = 300.0,  # 5 minutes
        failure_decay_hours: float = 24.0,
    ):
        """
        Initialize the failure rule engine.

        Args:
            max_retries: Maximum number of retries per server
            base_retry_delay: Base delay between retries (exponential backoff)
            max_retry_delay: Maximum retry delay
            health_check_interval: Interval for health checks in seconds
            failure_decay_hours: Hours after which failure counts decay
        """
        self.max_retries = max_retries
        self.base_retry_delay = base_retry_delay
        self.max_retry_delay = max_retry_delay
        self.health_check_interval = health_check_interval
        self.failure_decay_hours = failure_decay_hours

        self.server_stats: dict[str, ServerStats] = {}
        self.connection_history: list[ConnectionAttempt] = []
        self._last_health_check = time.time()

    def get_server_priority(self, host: str) -> ServerPriority:
        """Determine server priority based on hostname."""
        host_lower = host.lower()

        if any(provider in host_lower for provider in ["google", "cloudflare"]):
            return ServerPriority.PRIMARY
        elif any(
            provider in host_lower
            for provider in ["apple", "microsoft", "windows"]
        ):
            return ServerPriority.SECONDARY
        elif "pool" in host_lower:
            return ServerPriority.TERTIARY
        else:
            return ServerPriority.FALLBACK

    def should_retry_server(
        self,
        host: str,
        attempt_count: int,
        last_failure_reason: Optional[FailureReason] = None,
    ) -> tuple[bool, float]:
        """
        Determine if a server should be retried and when.

        Args:
            host: Server hostname
            attempt_count: Number of previous attempts
            last_failure_reason: Reason for last failure

        Returns:
            Tuple of (should_retry, delay_seconds)
        """
        if attempt_count >= self.max_retries:
            logger.debug(
                f"Server {host} reached max retries ({self.max_retries})"
            )
            return False, 0.0

        # Check server health
        stats = self.server_stats.get(host)
        if stats and not stats.is_healthy:
            # Unhealthy server - use the maximum retry delay to avoid hammering
            delay = float(self.max_retry_delay)
            logger.warning(
                f"Server {host} is unhealthy, retrying in {delay:.1f}s"
            )
            return True, delay

        # Standard exponential backoff
        delay = self.base_retry_delay * (2**attempt_count)
        delay = min(delay, self.max_retry_delay)

        # Additional delay for certain failure types
        if last_failure_reason == FailureReason.TIMEOUT:
            delay *= 1.5
        elif last_failure_reason == FailureReason.NETWORK_ERROR:
            delay *= 1.2

        return True, delay

    def select_best_servers(
        self, available_hosts: list[str], max_selections: int = 4
    ) -> list[str]:
        """
        Select the best servers based on health and priority.

        Args:
            available_hosts: List of available server hosts
            max_selections: Maximum number of servers to select

        Returns:
            List of selected server hosts in priority order
        """
        # Update server stats if needed
        self._decay_old_failures()

        # Create or update server stats
        servers_with_stats = []
        for host in available_hosts:
            if host not in self.server_stats:
                self.server_stats[host] = ServerStats(
                    host=host, priority=self.get_server_priority(host)
                )

            stats = self.server_stats[host]
            servers_with_stats.append((host, stats))

        # Sort by: health status, priority, success rate, average delay
        def sort_key(item):
            """TODO: Document sort_key."""
            stats = item[1]
            health_score = 1 if stats.is_healthy else 0
            priority_score = -stats.priority.value  # Lower is better
            success_score = stats.success_rate / 100.0
            delay_score = -stats.avg_delay if stats.avg_delay > 0 else 0

            return (health_score, priority_score, success_score, delay_score)

        sorted_servers = sorted(servers_with_stats, key=sort_key, reverse=True)
        selected = [host for host, _ in sorted_servers[:max_selections]]

        logger.info(f"Selected servers: {selected}")
        return selected

    def should_fallback_to_rtc(self) -> bool:
        """
        Determine if we should fallback to RTC based on recent failure patterns.

        Returns:
            True if RTC fallback is warranted
        """
        if len(self.connection_history) < 5:
            return False

        # Check last 10 attempts
        recent_attempts = self.connection_history[-10:]
        total_attempts = len(recent_attempts)
        failed_attempts = sum(
            1 for attempt in recent_attempts if not attempt.success
        )

        # Fallback if 80% or more recent attempts failed
        failure_rate = (
            failed_attempts / total_attempts if total_attempts > 0 else 0
        )

        if failure_rate >= 0.8:
            logger.warning(
                f"High failure rate ({failure_rate:.1%}), falling back to RTC"
            )
            return True

        return False

    def should_use_file_fallback(self) -> bool:
        """
        Determine if we should use file timestamp fallback.

        Returns:
            True if file fallback is warranted
        """
        if len(self.connection_history) < 10:
            return False

        # Check last 20 attempts
        recent_attempts = self.connection_history[-20:]
        total_attempts = len(recent_attempts)
        failed_attempts = sum(
            1 for attempt in recent_attempts if not attempt.success
        )

        # File fallback if 90% or more recent attempts failed
        failure_rate = (
            failed_attempts / total_attempts if total_attempts > 0 else 0
        )

        if failure_rate >= 0.9:
            logger.warning(
                f"Very high failure rate ({failure_rate:.1%}), using file fallback"
            )
            return True

        return False

    def should_use_monotonic_only(self) -> bool:
        """
        Determine if we should use pure monotonic time only.

        Returns:
            True if only monotonic time should be used
        """
        if len(self.connection_history) < 20:
            return False

        # Check last 50 attempts
        recent_attempts = self.connection_history[-50:]
        total_attempts = len(recent_attempts)
        failed_attempts = sum(
            1 for attempt in recent_attempts if not attempt.success
        )

        # Pure monotonic if 95% or more recent attempts failed
        failure_rate = (
            failed_attempts / total_attempts if total_attempts > 0 else 0
        )

        if failure_rate >= 0.95:
            logger.critical(
                f"Critical failure rate ({failure_rate:.1%}), using monotonic only"
            )
            return True

        return False

    def get_connection_strategy(
        self, available_hosts: list[str]
    ) -> ConnectionStrategy:
        """
        Determine the optimal connection strategy based on current conditions.

        Args:
            available_hosts: List of available server hosts

        Returns:
            ConnectionStrategy with optimal parameters
        """
        # Health check if needed
        if time.time() - self._last_health_check > self.health_check_interval:
            self._perform_health_check()
            self._last_health_check = time.time()

        # Determine fallback level
        if self.should_use_monotonic_only():
            fallback_level = FallbackLevel.MONOTONIC_ONLY
        elif self.should_use_file_fallback():
            fallback_level = FallbackLevel.FILE_FALLBACK
        elif self.should_fallback_to_rtc():
            fallback_level = FallbackLevel.RTC_FALLBACK
        else:
            fallback_level = FallbackLevel.NTP_ONLY

        # Select servers based on health
        selected_servers = self.select_best_servers(available_hosts)

        # Adjust retry strategy based on failure patterns
        avg_success_rate = self._calculate_average_success_rate()
        if avg_success_rate < 30:
            retry_strategy = RetryStrategy.CONSERVATIVE
        elif avg_success_rate < 70:
            retry_strategy = RetryStrategy.MODERATE
        else:
            retry_strategy = RetryStrategy.AGGRESSIVE

        return ConnectionStrategy(
            servers=selected_servers,
            max_retries=self._get_adaptive_retries(retry_strategy),
            timeout=self._get_adaptive_timeout(retry_strategy),
            parallel_queries=self._get_adaptive_parallelism(retry_strategy),
            fallback_level=fallback_level,
            retry_strategy=retry_strategy,
        )

    def record_attempt(self, attempt: ConnectionAttempt):
        """Record a connection attempt for analysis."""
        self.connection_history.append(attempt)

        # Keep only last 1000 attempts
        if len(self.connection_history) > 1000:
            self.connection_history.pop(0)

        # Update server stats
        stats = self.server_stats.get(attempt.host)
        if not stats:
            stats = ServerStats(
                host=attempt.host,
                priority=self.get_server_priority(attempt.host),
            )
            self.server_stats[attempt.host] = stats

        if attempt.success:
            stats.record_success(attempt.delay or 0.0)
        else:
            stats.record_failure(
                attempt.failure_reason or FailureReason.NETWORK_ERROR
            )

    def get_server_health_report(self) -> dict[str, dict]:
        """Get health report for all servers."""
        self._decay_old_failures()

        report = {}
        for host, stats in self.server_stats.items():
            report[host] = {
                "priority": stats.priority.name,
                "success_rate": round(stats.success_rate, 2),
                "avg_delay": round(stats.avg_delay, 3),
                "total_attempts": stats.total_attempts,
                "is_healthy": stats.is_healthy,
                "last_success": stats.last_success,
                "last_failure": stats.last_failure,
                "failure_reasons": dict(stats.failure_reasons),
            }

        return report

    def _decay_old_failures(self):
        """Decay old failure counts based on time.

        Only decay failures that are older than the configured decay window. The
        previous implementation mistakenly decayed failures when a recent
        success existed which produced surprising health reports in tests.
        """
        cutoff_time = time.time() - (self.failure_decay_hours * 3600)

        for stats in self.server_stats.values():
            # Only decay if the last recorded failure is older than the cutoff
            if stats.last_failure and stats.last_failure < cutoff_time:
                stats.failure_count = max(0, stats.failure_count - 1)
                stats.total_attempts = stats.success_count + stats.failure_count

    def _perform_health_check(self):
        """Perform periodic health checks on servers."""
        for stats in self.server_stats.values():
            # Consider server unhealthy if no success in last 30 minutes
            if stats.last_success:
                time_since_success = time.time() - stats.last_success
                if time_since_success > 1800:  # 30 minutes
                    logger.warning(
                        f"Server {stats.host} has no success in {time_since_success/60:.1f} minutes"
                    )

    def _calculate_average_success_rate(self) -> float:
        """Calculate average success rate across all servers."""
        if not self.server_stats:
            return 100.0  # Default: assume healthy until data suggests otherwise

        total_success = sum(
            stats.success_count for stats in self.server_stats.values()
        )
        total_attempts = sum(
            stats.total_attempts for stats in self.server_stats.values()
        )

        if total_attempts == 0:
            # No attempt data for any server -> assume healthy
            return 100.0

        return (total_success / total_attempts) * 100

    def _get_adaptive_retries(self, strategy: RetryStrategy) -> int:
        """Get adaptive retry count based on strategy."""
        base_retries = self.max_retries

        if strategy == RetryStrategy.CONSERVATIVE:
            return max(2, base_retries - 1)
        elif strategy == RetryStrategy.AGGRESSIVE:
            return min(5, base_retries + 1)
        else:
            return base_retries

    def _get_adaptive_timeout(self, strategy: RetryStrategy) -> float:
        """Get adaptive timeout based on strategy."""
        if strategy == RetryStrategy.CONSERVATIVE:
            return 5.0
        elif strategy == RetryStrategy.AGGRESSIVE:
            return 2.0
        else:
            return 3.0

    def _get_adaptive_parallelism(self, strategy: RetryStrategy) -> bool:
        """Get adaptive parallelism setting based on strategy."""
        if strategy == RetryStrategy.CONSERVATIVE:
            return False  # Sequential for conservative
        else:
            return True  # Parallel for moderate/aggressive


class FallbackLevel(Enum):
    """Levels of fallback when NTP fails."""

    NTP_ONLY = 1  # Only use NTP servers
    RTC_FALLBACK = 2  # Fallback to RTC
    FILE_FALLBACK = 3  # Fallback to file timestamps
    MONOTONIC_ONLY = 4  # Use only monotonic time


class RetryStrategy(Enum):
    """Retry strategies based on network conditions."""

    CONSERVATIVE = 1  # Fewer retries, longer delays, sequential
    MODERATE = 2  # Balanced approach
    AGGRESSIVE = 3  # More retries, shorter delays, parallel


@dataclass
class ConnectionStrategy:
    """Optimal connection strategy for current conditions."""

    servers: list[str]
    max_retries: int
    timeout: float
    parallel_queries: bool
    fallback_level: FallbackLevel
    retry_strategy: RetryStrategy


class AdaptiveFailureHandler:
    """
    Adaptive failure handler that learns from network patterns
    and adjusts behavior accordingly.
    """

    def __init__(self, rule_engine: FailureRuleEngine):
        """TODO: Document __init__."""
        self.rule_engine = rule_engine
        self._network_patterns = defaultdict(list)
        self._last_pattern_update = time.time()

    def analyze_network_pattern(self) -> dict[str, Any]:
        """Analyze current network patterns and return recommendations."""
        # If we have a cached pattern and it is still fresh, return it. If there
        # is no cached data yet we must perform analysis even if called shortly
        # after initialization (tests expect analysis to run on first call).
        if (
            time.time() - self._last_pattern_update < 60
            and self._network_patterns
        ):
            return self._get_cached_pattern()

        # Analyze recent connection history
        if len(self.rule_engine.connection_history) < 10:
            return {
                "pattern": "insufficient_data",
                "recommendations": [],
                "metrics": {},
            }

        recent_attempts = self.rule_engine.connection_history[-50:]

        # Calculate failure patterns
        hourly_failures = self._calculate_hourly_failures(recent_attempts)
        failure_by_reason = self._calculate_failure_reasons(recent_attempts)
        success_by_server = self._calculate_success_by_server(recent_attempts)

        # Determine pattern
        avg_hourly_failures = sum(hourly_failures.values()) / max(
            1, len(hourly_failures)
        )

        if avg_hourly_failures > 20:
            pattern = "high_failure_network"
        elif avg_hourly_failures > 5:
            pattern = "moderate_failure_network"
        else:
            pattern = "healthy_network"

        # Generate recommendations
        recommendations = self._generate_recommendations(
            pattern, failure_by_reason, success_by_server
        )

        result = {
            "pattern": pattern,
            "recommendations": recommendations,
            "metrics": {
                "avg_hourly_failures": avg_hourly_failures,
                "failure_by_reason": failure_by_reason,
                "success_by_server": success_by_server,
            },
        }

        self._network_patterns[pattern].append(result)
        self._last_pattern_update = time.time()

        return result

    def _calculate_hourly_failures(
        self, attempts: list[ConnectionAttempt]
    ) -> dict[int, int]:
        """Calculate failures per hour."""
        hourly_failures = defaultdict(int)
        for attempt in attempts:
            if not attempt.success:
                hour = datetime.fromtimestamp(attempt.attempt_time).hour
                hourly_failures[hour] += 1
        return hourly_failures

    def _calculate_failure_reasons(
        self, attempts: list[ConnectionAttempt]
    ) -> dict[str, int]:
        """Calculate failure reasons distribution."""
        reasons = defaultdict(int)
        for attempt in attempts:
            if not attempt.success and attempt.failure_reason:
                reasons[attempt.failure_reason.value] += 1
        return reasons

    def _calculate_success_by_server(
        self, attempts: list[ConnectionAttempt]
    ) -> dict[str, float]:
        """Calculate success rate by server."""
        server_stats = defaultdict(lambda: {"success": 0, "total": 0})

        for attempt in attempts:
            server_stats[attempt.host]["total"] += 1
            if attempt.success:
                server_stats[attempt.host]["success"] += 1

        success_rates = {}
        for host, stats in server_stats.items():
            if stats["total"] > 0:
                success_rates[host] = (stats["success"] / stats["total"]) * 100

        return success_rates

    def _generate_recommendations(
        self, pattern: str, failure_reasons: dict, success_rates: dict
    ) -> list[str]:
        """Generate recommendations based on pattern analysis."""
        recommendations = []

        if pattern == "high_failure_network":
            recommendations.append("Switch to conservative retry strategy")
            recommendations.append("Reduce parallel query count")
            recommendations.append("Increase timeout values")
            recommendations.append("Prioritize primary servers only")

        elif pattern == "moderate_failure_network":
            recommendations.append("Use moderate retry strategy")
            recommendations.append("Monitor server health closely")
            recommendations.append("Consider geographic server distribution")

        # Check for specific failure reasons
        if failure_reasons.get("timeout", 0) > 10:
            recommendations.append("Increase timeout due to network latency")

        if failure_reasons.get("dns_failure", 0) > 5:
            recommendations.append(
                "Check DNS configuration or use IP addresses"
            )

        # Check server-specific issues
        for host, rate in success_rates.items():
            if rate < 30:
                recommendations.append(
                    f"Exclude {host} due to poor performance"
                )

        return recommendations

    def _get_cached_pattern(self) -> dict[str, Any]:
        """Get the most recent cached pattern analysis."""
        if not self._network_patterns:
            return {"pattern": "unknown", "recommendations": [], "metrics": {}}

        # Return the most recent pattern
        latest_pattern = max(
            self._network_patterns.keys(),
            key=lambda p: len(self._network_patterns[p]),
        )
        return (
            self._network_patterns[latest_pattern][-1]
            if self._network_patterns[latest_pattern]
            else {"pattern": "unknown", "recommendations": [], "metrics": {}}
        )


# Global failure rule engine instance
GLOBAL_FAILURE_RULES = None


def get_failure_rules() -> FailureRuleEngine:
    """Get the global failure rule engine instance."""
    global GLOBAL_FAILURE_RULES
    if GLOBAL_FAILURE_RULES is None:
        GLOBAL_FAILURE_RULES = FailureRuleEngine()
    return GLOBAL_FAILURE_RULES


def reset_failure_rules():
    """Reset the global failure rule engine."""
    global GLOBAL_FAILURE_RULES
    GLOBAL_FAILURE_RULES = FailureRuleEngine()
