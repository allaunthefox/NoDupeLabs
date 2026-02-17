"""
Tests for TimeSync Failure Rules

These tests validate the comprehensive failure handling and retry strategies
implemented in the TimeSync failure rules module.
"""

import time
from collections import defaultdict, deque
from unittest.mock import MagicMock, patch

import pytest

from nodupe.core.time_sync_failure_rules import (
    AdaptiveFailureHandler,
    ConnectionAttempt,
    ConnectionStrategy,
    FailureReason,
    FailureRuleEngine,
    FallbackLevel,
    RetryStrategy,
    ServerPriority,
    ServerStats,
    get_failure_rules,
    reset_failure_rules,
)


class TestServerStats:
    """Test server statistics tracking."""

    def test_server_stats_initialization(self):
        """Test that ServerStats initializes correctly."""
        stats = ServerStats(host="test.com", priority=ServerPriority.PRIMARY)

        assert stats.host == "test.com"
        assert stats.priority == ServerPriority.PRIMARY
        assert stats.success_count == 0
        assert stats.failure_count == 0
        assert stats.total_attempts == 0
        assert stats.success_rate == 0.0
        assert stats.avg_delay == 0.0
        assert stats.is_healthy is True  # Not enough data yet

    def test_record_success(self):
        """Test recording successful connections."""
        stats = ServerStats(host="test.com", priority=ServerPriority.PRIMARY)

        stats.record_success(0.1)
        assert stats.success_count == 1
        assert stats.total_attempts == 1
        assert stats.success_rate == 100.0
        assert stats.avg_delay == 0.1
        assert len(stats.recent_delays) == 1

        stats.record_success(0.2)
        assert stats.success_count == 2
        assert stats.total_attempts == 2
        assert stats.success_rate == 100.0
        assert stats.avg_delay == 0.15

    def test_record_failure(self):
        """Test recording failed connections."""
        stats = ServerStats(host="test.com", priority=ServerPriority.PRIMARY)

        stats.record_failure(FailureReason.TIMEOUT)
        assert stats.failure_count == 1
        assert stats.total_attempts == 1
        assert stats.success_rate == 0.0
        assert stats.failure_reasons[FailureReason.TIMEOUT] == 1

        stats.record_failure(FailureReason.NETWORK_ERROR)
        assert stats.failure_count == 2
        assert stats.total_attempts == 2
        assert stats.failure_reasons[FailureReason.NETWORK_ERROR] == 1

    def test_health_determination(self):
        """Test server health determination based on success rate."""
        stats = ServerStats(host="test.com", priority=ServerPriority.PRIMARY)

        # Not enough data yet - should be healthy
        assert stats.is_healthy is True

        # Add some data with low success rate
        stats.record_failure(FailureReason.TIMEOUT)
        stats.record_failure(FailureReason.TIMEOUT)
        stats.record_failure(FailureReason.TIMEOUT)
        stats.record_success(0.1)

        assert stats.success_rate == 25.0
        assert stats.is_healthy is False  # Below 50% threshold

        # Improve success rate
        for _ in range(6):
            stats.record_success(0.1)

        assert stats.success_rate == 70.0
        assert stats.is_healthy is True


class TestFailureRuleEngine:
    """Test the main failure rule engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = FailureRuleEngine(
            max_retries=3,
            base_retry_delay=1.0,
            max_retry_delay=10.0
        )

    def test_server_priority_detection(self):
        """Test automatic server priority detection."""
        assert self.engine.get_server_priority("time.google.com") == ServerPriority.PRIMARY
        assert self.engine.get_server_priority("time.cloudflare.com") == ServerPriority.PRIMARY
        assert self.engine.get_server_priority("time.apple.com") == ServerPriority.SECONDARY
        assert self.engine.get_server_priority("time.microsoft.com") == ServerPriority.SECONDARY
        assert self.engine.get_server_priority("pool.ntp.org") == ServerPriority.TERTIARY
        assert self.engine.get_server_priority("custom.server.com") == ServerPriority.FALLBACK

    def test_retry_decision(self):
        """Test retry decision logic."""
        # Healthy server should retry
        should_retry, delay = self.engine.should_retry_server("test.com", 0)
        assert should_retry is True
        assert delay == 1.0  # base_retry_delay

        # Exponential backoff
        should_retry, delay = self.engine.should_retry_server("test.com", 1)
        assert should_retry is True
        assert delay == 2.0  # base_retry_delay * 2^1

        should_retry, delay = self.engine.should_retry_server("test.com", 2)
        assert should_retry is True
        assert delay == 4.0  # base_retry_delay * 2^2

        # Max retries reached
        should_retry, delay = self.engine.should_retry_server("test.com", 3)
        assert should_retry is False
        assert delay == 0.0

    def test_unhealthy_server_retry(self):
        """Test retry behavior for unhealthy servers."""
        # Make server unhealthy
        stats = ServerStats(host="bad.com", priority=ServerPriority.PRIMARY)
        for _ in range(5):
            stats.record_failure(FailureReason.TIMEOUT)
        for _ in range(2):
            stats.record_success(0.1)
        self.engine.server_stats["bad.com"] = stats

        # Unhealthy server should have longer delays
        should_retry, delay = self.engine.should_retry_server("bad.com", 0)
        assert should_retry is True
        assert delay >= 10.0  # Max retry delay for unhealthy

    def test_failure_reason_delays(self):
        """Test additional delays for specific failure reasons."""
        # Timeout should add 50% delay
        should_retry, delay = self.engine.should_retry_server(
            "test.com", 1, FailureReason.TIMEOUT
        )
        assert should_retry is True
        assert delay == 3.0  # 2.0 * 1.5

        # Network error should add 20% delay
        should_retry, delay = self.engine.should_retry_server(
            "test.com", 1, FailureReason.NETWORK_ERROR
        )
        assert should_retry is True
        assert delay == 2.4  # 2.0 * 1.2

    def test_server_selection(self):
        """Test intelligent server selection based on health and priority."""
        # Add some test servers with different health levels
        healthy_stats = ServerStats(host="healthy.com", priority=ServerPriority.PRIMARY)
        for _ in range(5):
            healthy_stats.record_success(0.1)
        self.engine.server_stats["healthy.com"] = healthy_stats

        unhealthy_stats = ServerStats(host="unhealthy.com", priority=ServerPriority.TERTIARY)
        for _ in range(5):
            unhealthy_stats.record_failure(FailureReason.TIMEOUT)
        self.engine.server_stats["unhealthy.com"] = unhealthy_stats

        # Select best servers
        available_hosts = ["healthy.com", "unhealthy.com", "new.com"]
        selected = self.engine.select_best_servers(available_hosts, max_selections=2)

        # Healthy primary should be selected first
        assert selected[0] == "healthy.com"
        # New server should be preferred over unhealthy
        assert selected[1] == "new.com"

    def test_fallback_decisions(self):
        """Test fallback level decisions based on failure patterns."""
        # Add some failed attempts
        for i in range(8):
            attempt = ConnectionAttempt(
                host=f"server{i}.com",
                attempt_time=time.time() - 1,
                success=False,
                failure_reason=FailureReason.TIMEOUT
            )
            self.engine.record_attempt(attempt)

        # High failure rate should trigger RTC fallback
        assert self.engine.should_fallback_to_rtc() is True

        # Clear history and test file fallback
        self.engine.connection_history = []
        for i in range(18):
            attempt = ConnectionAttempt(
                host=f"server{i}.com",
                attempt_time=time.time() - 1,
                success=False,
                failure_reason=FailureReason.TIMEOUT
            )
            self.engine.record_attempt(attempt)

        assert self.engine.should_use_file_fallback() is True

    def test_connection_strategy(self):
        """Test adaptive connection strategy generation."""
        # Test with healthy network
        strategy = self.engine.get_connection_strategy(["time.google.com"])

        assert isinstance(strategy, ConnectionStrategy)
        assert "time.google.com" in strategy.servers
        assert strategy.fallback_level == FallbackLevel.NTP_ONLY
        assert strategy.retry_strategy == RetryStrategy.AGGRESSIVE

        # Simulate poor network by adding failures
        for i in range(20):
            attempt = ConnectionAttempt(
                host="time.google.com",
                attempt_time=time.time() - 1,
                success=False,
                failure_reason=FailureReason.TIMEOUT
            )
            self.engine.record_attempt(attempt)

        strategy = self.engine.get_connection_strategy(["time.google.com"])
        assert strategy.retry_strategy == RetryStrategy.CONSERVATIVE
        assert strategy.fallback_level != FallbackLevel.NTP_ONLY

    def test_connection_attempt_recording(self):
        """Test recording and analysis of connection attempts."""
        attempt = ConnectionAttempt(
            host="test.com",
            attempt_time=time.time(),
            success=True,
            delay=0.1
        )
        self.engine.record_attempt(attempt)

        assert len(self.engine.connection_history) == 1
        assert self.engine.connection_history[0].success is True

        # Check server stats were updated
        stats = self.engine.server_stats["test.com"]
        assert stats.success_count == 1
        assert stats.total_attempts == 1

    def test_health_report(self):
        """Test server health reporting."""
        # Add some test data
        stats = ServerStats(host="test.com", priority=ServerPriority.PRIMARY)
        for _ in range(3):
            stats.record_success(0.1)
        for _ in range(2):
            stats.record_failure(FailureReason.TIMEOUT)
        self.engine.server_stats["test.com"] = stats

        report = self.engine.get_server_health_report()

        assert "test.com" in report
        assert report["test.com"]["success_rate"] == 60.0
        assert report["test.com"]["priority"] == "PRIMARY"
        assert report["test.com"]["is_healthy"] is True


class TestAdaptiveFailureHandler:
    """Test the adaptive failure handler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rule_engine = FailureRuleEngine()
        self.handler = AdaptiveFailureHandler(self.rule_engine)

    def test_network_pattern_analysis(self):
        """Test network pattern analysis and recommendations."""
        # Add some connection attempts with specific patterns
        current_time = time.time()

        # Add timeout failures
        for i in range(15):
            attempt = ConnectionAttempt(
                host="server.com",
                attempt_time=current_time - 60,  # 1 minute ago
                success=False,
                failure_reason=FailureReason.TIMEOUT
            )
            self.rule_engine.record_attempt(attempt)

        # Add DNS failures
        for i in range(8):
            attempt = ConnectionAttempt(
                host="dns-fail.com",
                attempt_time=current_time - 60,
                success=False,
                failure_reason=FailureReason.DNS_FAILURE
            )
            self.rule_engine.record_attempt(attempt)

        # Analyze pattern
        result = self.handler.analyze_network_pattern()

        assert result["pattern"] in ["high_failure_network", "moderate_failure_network"]
        assert len(result["recommendations"]) > 0

        # Check for timeout-specific recommendations
        timeout_recs = [r for r in result["recommendations"] if "timeout" in r.lower()]
        assert len(timeout_recs) > 0

        # Check for DNS-specific recommendations
        dns_recs = [r for r in result["recommendations"] if "dns" in r.lower()]
        assert len(dns_recs) > 0

    def test_server_exclusion_recommendation(self):
        """Test recommendations to exclude poor-performing servers."""
        # Add many failures for a specific server
        current_time = time.time()

        for i in range(25):
            attempt = ConnectionAttempt(
                host="bad-server.com",
                attempt_time=current_time - 60,
                success=False,
                failure_reason=FailureReason.TIMEOUT
            )
            self.rule_engine.record_attempt(attempt)

        # Add some successes for another server
        for i in range(8):
            attempt = ConnectionAttempt(
                host="good-server.com",
                attempt_time=current_time - 60,
                success=True,
                delay=0.1
            )
            self.rule_engine.record_attempt(attempt)

        result = self.handler.analyze_network_pattern()

        # Should recommend excluding the bad server
        exclude_recs = [r for r in result["recommendations"] if "bad-server.com" in r]
        assert len(exclude_recs) > 0


class TestGlobalFailureRules:
    """Test global failure rule engine instance."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_failure_rules()

    def test_get_failure_rules_creates_instance(self):
        """Test that get_failure_rules creates and returns global instance."""
        engine1 = get_failure_rules()
        engine2 = get_failure_rules()

        assert engine1 is engine2  # Same instance
        assert isinstance(engine1, FailureRuleEngine)

    def test_reset_failure_rules(self):
        """Test that reset_failure_rules creates new instance."""
        engine1 = get_failure_rules()
        reset_failure_rules()
        engine2 = get_failure_rules()

        assert engine1 is not engine2  # Different instances


class TestIntegration:
    """Integration tests for failure rules."""

    def test_complete_failure_scenario(self):
        """Test a complete failure scenario with multiple fallback levels."""
        engine = FailureRuleEngine(max_retries=2)

        # Simulate complete network failure
        servers = ["time.google.com", "time.cloudflare.com", "pool.ntp.org"]

        # Record many failures
        for i in range(30):
            attempt = ConnectionAttempt(
                host=servers[i % len(servers)],
                attempt_time=time.time() - 1,
                success=False,
                failure_reason=FailureReason.TIMEOUT
            )
            engine.record_attempt(attempt)

        # Should trigger highest fallback level
        assert engine.should_use_monotonic_only() is True

        # Get connection strategy
        strategy = engine.get_connection_strategy(servers)
        assert strategy.fallback_level == FallbackLevel.MONOTONIC_ONLY
        assert strategy.retry_strategy == RetryStrategy.CONSERVATIVE

    def test_recovery_scenario(self):
        """Test recovery from failure state."""
        engine = FailureRuleEngine()

        # Simulate initial failures
        for i in range(10):
            attempt = ConnectionAttempt(
                host="server.com",
                attempt_time=time.time() - 3600,  # 1 hour ago
                success=False,
                failure_reason=FailureReason.TIMEOUT
            )
            engine.record_attempt(attempt)

        # Should be in fallback mode
        assert engine.should_fallback_to_rtc() is True

        # Simulate recovery with successes
        for i in range(10):
            attempt = ConnectionAttempt(
                host="server.com",
                attempt_time=time.time(),
                success=True,
                delay=0.1
            )
            engine.record_attempt(attempt)

        # Should recover
        assert engine.should_fallback_to_rtc() is False
        assert engine.should_use_file_fallback() is False

        # Server should be healthy again
        stats = engine.server_stats["server.com"]
        assert stats.is_healthy is True
        assert stats.success_rate == 50.0  # 10 successes out of 20 total


class TestPerformance:
    """Performance tests for failure rules."""

    def test_large_history_handling(self):
        """Test handling of large connection history."""
        engine = FailureRuleEngine()

        # Add many connection attempts
        time.time()
        for i in range(1000):
            attempt = ConnectionAttempt(
                host=f"server{i % 10}.com",
                attempt_time=time.time(),
                success=(i % 2 == 0),
                delay=0.1 if i % 2 == 0 else None,
                failure_reason=FailureReason.TIMEOUT if i % 2 != 0 else None
            )
            engine.record_attempt(attempt)

        # Should automatically limit history size
        assert len(engine.connection_history) <= 1000

        # Should still work efficiently
        strategy = engine.get_connection_strategy(["server1.com"])
        assert isinstance(strategy, ConnectionStrategy)

    def test_concurrent_access(self):
        """Test thread safety of failure rules."""
        import threading

        engine = FailureRuleEngine()
        results = []
        errors = []

        def worker():
            try:
                for i in range(100):
                    attempt = ConnectionAttempt(
                        host=f"worker{i % 5}.com",
                        attempt_time=time.time(),
                        success=(i % 3 == 0),
                        delay=0.1 if i % 3 == 0 else None
                    )
                    engine.record_attempt(attempt)

                strategy = engine.get_connection_strategy(["test.com"])
                results.append(strategy)
            except Exception as e:
                errors.append(e)

        # Run multiple threads
        threads = []
        for _ in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Should complete without errors
        assert len(errors) == 0
        assert len(results) == 5


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
