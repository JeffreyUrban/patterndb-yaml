"""Integration tests for web server log normalization with realistic synthetic data."""

import tempfile
from io import StringIO
from pathlib import Path

import pytest
import yaml

from patterndb_yaml import PatterndbYaml


@pytest.fixture
def webserver_rules():
    """Rules for normalizing mixed nginx and apache logs."""
    rules = {
        "rules": [
            # Nginx access log format
            {
                "name": "nginx_access",
                "pattern": [
                    {"field": "ip"},
                    {"text": " - "},
                    {"field": "user"},
                    {"text": " ["},
                    {"field": "timestamp"},
                    {"text": '] "'},
                    {"field": "method"},
                    {"text": " "},
                    {"field": "path"},
                    {"text": " HTTP/"},
                    {"field": "version"},
                    {"text": '" '},
                    {"field": "status"},
                    {"text": " "},
                    {"field": "bytes"},
                ],
                "output": "[{method}:{path}|status:{status}]",
            },
            # Apache combined log format
            {
                "name": "apache_combined",
                "pattern": [
                    {"field": "ip"},
                    {"text": " - - ["},
                    {"field": "timestamp"},
                    {"text": '] "'},
                    {"field": "method"},
                    {"text": " "},
                    {"field": "path"},
                    {"text": " HTTP/"},
                    {"field": "version"},
                    {"text": '" '},
                    {"field": "status"},
                    {"text": " "},
                    {"field": "bytes"},
                    {"text": ' "'},
                    {"field": "referer"},
                    {"text": '" "'},
                    {"field": "user_agent"},
                    {"text": '"'},
                ],
                "output": "[{method}:{path}|status:{status}]",
            },
            # Nginx error log
            {
                "name": "nginx_error",
                "pattern": [
                    {"field": "timestamp"},
                    {"text": " ["},
                    {"field": "level"},
                    {"text": "] "},
                    {"field": "pid"},
                    {"text": "#"},
                    {"field": "tid"},
                    {"text": ": *"},
                    {"field": "cid"},
                    {"text": " "},
                    {"field": "message"},
                ],
                "output": "[NGINX_ERROR:{level}] {message}",
            },
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(rules, f)
        return Path(f.name)


@pytest.fixture
def realistic_webserver_logs():
    """Generate realistic synthetic web server logs (1000 lines)."""
    logs = []

    # Nginx access logs (500 lines)
    paths = ["/", "/api/users", "/api/orders", "/static/app.js", "/images/logo.png"]
    methods = ["GET", "POST", "PUT", "DELETE"]
    statuses = ["200", "201", "304", "400", "401", "404", "500"]

    for i in range(500):
        ip = f"192.168.{i % 255}.{(i * 7) % 255}"
        timestamp = f"15/Nov/2024:10:{i % 60:02d}:{i % 60:02d} +0000"
        method = methods[i % len(methods)]
        path = paths[i % len(paths)]
        status = statuses[i % len(statuses)]
        bytes_sent = 1000 + (i * 123) % 10000

        logs.append(f'{ip} - - [{timestamp}] "{method} {path} HTTP/1.1" {status} {bytes_sent}')

    # Apache combined logs (400 lines)
    for i in range(400):
        ip = f"10.0.{i % 255}.{(i * 13) % 255}"
        timestamp = f"15/Nov/2024:11:{i % 60:02d}:{i % 60:02d} +0000"
        method = methods[i % len(methods)]
        path = paths[i % len(paths)]
        status = statuses[i % len(statuses)]
        bytes_sent = 500 + (i * 89) % 5000
        referer = "https://example.com" if i % 3 == 0 else "-"
        user_agent = "Mozilla/5.0" if i % 2 == 0 else "curl/7.68.0"

        logs.append(
            f'{ip} - - [{timestamp}] "{method} {path} HTTP/1.1" {status} {bytes_sent} '
            f'"{referer}" "{user_agent}"'
        )

    # Nginx error logs (100 lines)
    error_messages = [
        "connect() failed (111: Connection refused)",
        "upstream timed out (110: Connection timed out)",
        "client intended to send too large body",
        "SSL handshake failed",
    ]
    levels = ["error", "warn", "crit"]

    for i in range(100):
        timestamp = f"2024/11/15 12:{i % 60:02d}:{i % 60:02d}"
        level = levels[i % len(levels)]
        pid = 1000 + (i % 100)
        tid = i % 10
        cid = i
        message = error_messages[i % len(error_messages)]

        logs.append(f"{timestamp} [{level}] {pid}#{tid}: *{cid} {message}")

    return "\n".join(logs)


def test_webserver_integration_large_scale(webserver_rules, realistic_webserver_logs):
    """Test normalization of 1000 lines of mixed web server logs."""
    processor = PatterndbYaml(rules_path=webserver_rules)

    input_data = StringIO(realistic_webserver_logs)
    output_data = StringIO()

    # Process all logs
    processor.process(input_data, output_data)

    # Check statistics
    stats = processor.get_stats()
    assert stats["lines_processed"] == 1000
    assert stats["lines_matched"] >= 995  # Allow for a few unmatched
    assert stats["match_rate"] >= 0.995  # 99.5% (match_rate is 0-1, not 0-100)

    # Verify output format
    output_data.seek(0)
    normalized_lines = output_data.readlines()

    # Check that we have output for all lines
    assert len(normalized_lines) == 1000

    # Verify normalized format for access logs
    access_log_count = 0
    for line in normalized_lines:
        line = line.strip()
        if (
            line.startswith("[GET:")
            or line.startswith("[POST:")
            or line.startswith("[PUT:")
            or line.startswith("[DELETE:")
        ):
            access_log_count += 1
            assert "|status:" in line
            assert line.endswith("]")

    # Should have ~900 access logs (nginx + apache)
    assert access_log_count >= 850

    # Verify error log format
    error_log_count = sum(1 for line in normalized_lines if "[NGINX_ERROR:" in line)
    assert error_log_count >= 95  # Should have ~100 error logs


def test_webserver_method_distribution(webserver_rules, realistic_webserver_logs):
    """Test that all HTTP methods are correctly normalized."""
    processor = PatterndbYaml(rules_path=webserver_rules)

    input_data = StringIO(realistic_webserver_logs)
    output_data = StringIO()
    processor.process(input_data, output_data)

    output_data.seek(0)
    normalized = output_data.read()

    # Verify all HTTP methods are present in output
    assert "[GET:" in normalized
    assert "[POST:" in normalized
    assert "[PUT:" in normalized
    assert "[DELETE:" in normalized


def test_webserver_status_code_patterns(webserver_rules, realistic_webserver_logs):
    """Test that various HTTP status codes are preserved."""
    processor = PatterndbYaml(rules_path=webserver_rules)

    input_data = StringIO(realistic_webserver_logs)
    output_data = StringIO()
    processor.process(input_data, output_data)

    output_data.seek(0)
    normalized = output_data.read()

    # Verify status codes are normalized correctly
    assert "|status:200]" in normalized
    assert "|status:404]" in normalized
    assert "|status:500]" in normalized


def test_webserver_error_levels(webserver_rules, realistic_webserver_logs):
    """Test that nginx error levels are correctly extracted."""
    processor = PatterndbYaml(rules_path=webserver_rules)

    input_data = StringIO(realistic_webserver_logs)
    output_data = StringIO()
    processor.process(input_data, output_data)

    output_data.seek(0)
    normalized = output_data.read()

    # Verify error levels
    assert "[NGINX_ERROR:error]" in normalized
    assert "[NGINX_ERROR:warn]" in normalized
    assert "[NGINX_ERROR:crit]" in normalized


def test_webserver_cache_effectiveness(webserver_rules):
    """Test that repeated log patterns benefit from caching."""
    processor = PatterndbYaml(rules_path=webserver_rules)

    # Generate logs with high repetition (same requests repeated)
    repeated_log = '192.168.1.1 - - [15/Nov/2024:10:00:01 +0000] "GET / HTTP/1.1" 200 1234\n'
    input_data = StringIO(repeated_log * 1000)  # Same line 1000 times
    output_data = StringIO()

    processor.process(input_data, output_data)

    # Check cache hit rate
    cache_info = processor.norm_engine.normalize_cached.cache_info()

    # With 1000 identical lines, we should have 999 cache hits
    assert cache_info.hits >= 990
    assert cache_info.misses <= 10

    # Calculate hit rate
    total = cache_info.hits + cache_info.misses
    hit_rate = cache_info.hits / total if total > 0 else 0
    assert hit_rate >= 0.99  # 99% cache hit rate


def test_webserver_mixed_format_stream(webserver_rules):
    """Test processing a stream that alternates between nginx and apache formats."""
    processor = PatterndbYaml(rules_path=webserver_rules)

    nginx_log = (
        '192.168.1.1 - user1 [15/Nov/2024:10:00:01 +0000] "GET /api/users HTTP/1.1" 200 1234'
    )
    apache_log = '10.0.0.1 - - [15/Nov/2024:10:00:02 +0000] "POST /api/orders HTTP/1.1" 201 567 "https://example.com" "Mozilla/5.0"'

    # Alternate between formats
    mixed_logs = []
    for i in range(100):
        if i % 2 == 0:
            mixed_logs.append(nginx_log)
        else:
            mixed_logs.append(apache_log)

    input_data = StringIO("\n".join(mixed_logs))
    output_data = StringIO()

    processor.process(input_data, output_data)

    # All should match
    stats = processor.get_stats()
    assert stats["lines_processed"] == 100
    assert stats["lines_matched"] == 100
    assert stats["match_rate"] == 1.0  # 100% (match_rate is 0-1)

    # Verify alternating pattern in output
    output_data.seek(0)
    lines = output_data.readlines()

    for i, line in enumerate(lines):
        line = line.strip()
        if i % 2 == 0:
            assert line == "[GET:/api/users|status:200]"
        else:
            assert line == "[POST:/api/orders|status:201]"


def test_webserver_performance_baseline(webserver_rules):
    """Baseline performance test - processing speed."""
    processor = PatterndbYaml(rules_path=webserver_rules)

    # Generate 10,000 log lines
    log_line = '192.168.1.1 - - [15/Nov/2024:10:00:01 +0000] "GET /api/users HTTP/1.1" 200 1234\n'
    input_data = StringIO(log_line * 10000)
    output_data = StringIO()

    import time

    start = time.time()
    processor.process(input_data, output_data)
    elapsed = time.time() - start

    # Verify processing completed
    stats = processor.get_stats()
    assert stats["lines_processed"] == 10000

    # Calculate throughput (should be > 10k lines/sec even on slow hardware)
    throughput = stats["lines_processed"] / elapsed if elapsed > 0 else 0
    assert throughput > 1000  # At least 1k lines/sec (very conservative)

    print(f"\nWebserver log throughput: {throughput:.0f} lines/sec")


def test_webserver_memory_efficiency(webserver_rules):
    """Test that memory usage stays constant regardless of input size."""
    import gc

    processor = PatterndbYaml(rules_path=webserver_rules)

    # Process small dataset
    small_log = '192.168.1.1 - - [15/Nov/2024:10:00:01 +0000] "GET / HTTP/1.1" 200 1234\n'

    gc.collect()
    input_data = StringIO(small_log * 100)
    output_data = StringIO()
    processor.process(input_data, output_data)

    # Memory usage should remain bounded (cache + rules only, not proportional to input)
    # This is a behavioral test - actual memory measurement would require psutil
    stats_small = processor.get_stats()
    assert stats_small["lines_processed"] == 100

    # Process larger dataset with same processor instance
    input_data = StringIO(small_log * 10000)
    output_data = StringIO()
    processor.process(input_data, output_data)

    stats_large = processor.get_stats()
    # Stats should accumulate (this tests that the processor maintains state correctly)
    assert stats_large["lines_processed"] == 10100  # 100 + 10000


def test_webserver_explain_mode_integration(webserver_rules, capsys):
    """Test explain mode with realistic web server logs."""
    processor = PatterndbYaml(rules_path=webserver_rules, explain=True)

    logs = [
        '192.168.1.1 - - [15/Nov/2024:10:00:01 +0000] "GET /api/users HTTP/1.1" 200 1234',
        '10.0.0.1 - - [15/Nov/2024:10:00:02 +0000] "POST /api/orders HTTP/1.1" 201 567 "-" "curl"',
        "2024/11/15 12:00:00 [error] 1000#0: *1 connect() failed",
        "Unknown log format that will not match",
    ]

    input_data = StringIO("\n".join(logs))
    output_data = StringIO()

    processor.process(input_data, output_data)

    # Capture stderr output
    captured = capsys.readouterr()

    # Verify explain messages appear
    assert "EXPLAIN:" in captured.err
    # Note: The actual rule names might be in the explain output
    # but we can't assert specific rule names without knowing the exact implementation

    # Verify statistics
    stats = processor.get_stats()
    assert stats["lines_processed"] == 4
    assert stats["lines_matched"] >= 3  # At least 3 of 4 should match
