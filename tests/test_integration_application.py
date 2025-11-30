"""Integration tests for multi-service application logs with realistic synthetic data."""

import tempfile
from io import StringIO
from pathlib import Path

import pytest
import yaml

from patterndb_yaml import PatterndbYaml


@pytest.fixture
def application_rules():
    """Rules for normalizing logs from multiple microservices."""
    rules = {
        "rules": [
            # API Gateway logs
            {
                "name": "api_gateway",
                "pattern": [
                    {"field": "timestamp"},
                    {"text": " [API-GATEWAY] "},
                    {"field": "level"},
                    {"text": ": "},
                    {"field": "method"},
                    {"text": " "},
                    {"field": "endpoint"},
                    {"text": " -> "},
                    {"field": "status"},
                    {"text": " ("},
                    {"field": "duration"},
                    {"text": "ms)"},
                ],
                "output": "[GATEWAY|{method}:{endpoint}|{status}]",
            },
            # Order Service logs
            {
                "name": "order_service",
                "pattern": [
                    {"field": "timestamp"},
                    {"text": " [ORDER-SVC] "},
                    {"field": "level"},
                    {"text": " order_id="},
                    {"field": "order_id"},
                    {"text": " action="},
                    {"field": "action"},
                    {"text": " user="},
                    {"field": "user"},
                ],
                "output": "[ORDER|{action}|user:{user}]",
            },
            # Payment Service logs
            {
                "name": "payment_service",
                "pattern": [
                    {"field": "timestamp"},
                    {"text": " [PAYMENT-SVC] "},
                    {"field": "level"},
                    {"text": " transaction="},
                    {"field": "txn_id"},
                    {"text": " status="},
                    {"field": "status"},
                    {"text": " amount=$"},
                    {"field": "amount"},
                ],
                "output": "[PAYMENT|{status}]",
            },
            # Database Query logs
            {
                "name": "db_query",
                "pattern": [
                    {"field": "timestamp"},
                    {"text": " [DATABASE] "},
                    {"field": "query_type"},
                    {"text": " table="},
                    {"field": "table"},
                    {"text": " duration="},
                    {"field": "duration"},
                    {"text": "ms"},
                ],
                "output": "[DB|{query_type}:{table}]",
            },
            # Error logs (all services)
            {
                "name": "service_error",
                "pattern": [
                    {"field": "timestamp"},
                    {"text": " ["},
                    {"field": "service"},
                    {"text": "] ERROR: "},
                    {"field": "error_msg"},
                ],
                "output": "[ERROR|{service}] {error_msg}",
            },
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(rules, f)
        return Path(f.name)


@pytest.fixture
def realistic_application_logs():
    """Generate realistic synthetic application logs from microservices (2000 lines)."""
    logs = []

    # API Gateway logs (600 lines)
    endpoints = ["/api/v1/users", "/api/v1/orders", "/api/v1/products", "/api/v1/payments"]
    methods = ["GET", "POST", "PUT", "DELETE"]
    statuses = ["200", "201", "400", "401", "404", "500", "503"]

    for i in range(600):
        timestamp = f"2024-11-15T10:{i % 60:02d}:{i % 60:02d}.{i % 1000:03d}Z"
        level = "INFO" if i % 10 != 0 else "WARN"
        method = methods[i % len(methods)]
        endpoint = endpoints[i % len(endpoints)]
        status = statuses[i % len(statuses)]
        duration = 10 + (i * 7) % 500

        logs.append(
            f"{timestamp} [API-GATEWAY] {level}: {method} {endpoint} -> {status} ({duration}ms)"
        )

    # Order Service logs (500 lines)
    actions = ["created", "updated", "cancelled", "completed", "failed"]
    users = [f"user_{i}" for i in range(100)]

    for i in range(500):
        timestamp = f"2024-11-15T10:{i % 60:02d}:{i % 60:02d}.{i % 1000:03d}Z"
        level = "INFO" if i % 15 != 0 else "WARN"
        order_id = f"ORD{1000 + i}"
        action = actions[i % len(actions)]
        user = users[i % len(users)]

        logs.append(
            f"{timestamp} [ORDER-SVC] {level} order_id={order_id} action={action} user={user}"
        )

    # Payment Service logs (400 lines)
    payment_statuses = ["approved", "declined", "pending", "refunded", "failed"]

    for i in range(400):
        timestamp = f"2024-11-15T10:{i % 60:02d}:{i % 60:02d}.{i % 1000:03d}Z"
        level = "INFO" if i % 10 != 0 else "ERROR"
        txn_id = f"TXN{2000 + i}"
        status = payment_statuses[i % len(payment_statuses)]
        amount = f"{(i % 500) + 10}.{i % 100:02d}"

        logs.append(
            f"{timestamp} [PAYMENT-SVC] {level} transaction={txn_id} status={status} amount=${amount}"
        )

    # Database Query logs (400 lines)
    query_types = ["SELECT", "INSERT", "UPDATE", "DELETE"]
    tables = ["users", "orders", "products", "payments", "inventory"]

    for i in range(400):
        timestamp = f"2024-11-15T10:{i % 60:02d}:{i % 60:02d}.{i % 1000:03d}Z"
        query_type = query_types[i % len(query_types)]
        table = tables[i % len(tables)]
        duration = 1 + (i * 3) % 200

        logs.append(f"{timestamp} [DATABASE] {query_type} table={table} duration={duration}ms")

    # Error logs from various services (100 lines)
    services = ["API-GATEWAY", "ORDER-SVC", "PAYMENT-SVC", "DATABASE"]
    error_messages = [
        "Connection timeout to downstream service",
        "Invalid request payload",
        "Database connection pool exhausted",
        "Rate limit exceeded",
        "Authentication failed",
    ]

    for i in range(100):
        timestamp = f"2024-11-15T10:{i % 60:02d}:{i % 60:02d}.{i % 1000:03d}Z"
        service = services[i % len(services)]
        error_msg = error_messages[i % len(error_messages)]

        logs.append(f"{timestamp} [{service}] ERROR: {error_msg}")

    return "\n".join(logs)


def test_application_integration_large_scale(application_rules, realistic_application_logs):
    """Test normalization of 2000 lines of multi-service application logs."""
    processor = PatterndbYaml(rules_path=application_rules)

    input_data = StringIO(realistic_application_logs)
    output_data = StringIO()

    # Process all logs
    processor.process(input_data, output_data)

    # Check statistics
    stats = processor.get_stats()
    assert stats["lines_processed"] == 2000
    assert stats["lines_matched"] >= 1990  # Should match almost all
    assert stats["match_rate"] >= 0.995  # 99.5% (match_rate is 0-1, not 0-100)

    # Verify output
    output_data.seek(0)
    normalized_lines = output_data.readlines()
    assert len(normalized_lines) == 2000


def test_application_service_distribution(application_rules, realistic_application_logs):
    """Test that logs from all services are correctly normalized."""
    processor = PatterndbYaml(rules_path=application_rules)

    input_data = StringIO(realistic_application_logs)
    output_data = StringIO()
    processor.process(input_data, output_data)

    output_data.seek(0)
    normalized = output_data.read()

    # Verify all service types present
    assert "[GATEWAY|" in normalized
    assert "[ORDER|" in normalized
    assert "[PAYMENT|" in normalized
    assert "[DB|" in normalized
    assert "[ERROR|" in normalized


def test_application_order_lifecycle(application_rules):
    """Test tracking an order through its lifecycle."""
    processor = PatterndbYaml(rules_path=application_rules)

    # Simulate order lifecycle
    order_logs = [
        "2024-11-15T10:00:01.000Z [ORDER-SVC] INFO order_id=ORD123 action=created user=user_1",
        "2024-11-15T10:00:02.000Z [PAYMENT-SVC] INFO transaction=TXN456 status=pending amount=$99.99",
        "2024-11-15T10:00:03.000Z [PAYMENT-SVC] INFO transaction=TXN456 status=approved amount=$99.99",
        "2024-11-15T10:00:04.000Z [ORDER-SVC] INFO order_id=ORD123 action=completed user=user_1",
    ]

    input_data = StringIO("\n".join(order_logs))
    output_data = StringIO()
    processor.process(input_data, output_data)

    output_data.seek(0)
    normalized = output_data.readlines()

    # Verify lifecycle stages
    assert normalized[0].strip() == "[ORDER|created|user:user_1]"
    assert normalized[1].strip() == "[PAYMENT|pending]"
    assert normalized[2].strip() == "[PAYMENT|approved]"
    assert normalized[3].strip() == "[ORDER|completed|user:user_1]"


def test_application_error_aggregation(application_rules, realistic_application_logs):
    """Test aggregating errors across all services."""
    processor = PatterndbYaml(rules_path=application_rules)

    input_data = StringIO(realistic_application_logs)
    output_data = StringIO()
    processor.process(input_data, output_data)

    output_data.seek(0)
    normalized_lines = output_data.readlines()

    # Count error lines
    error_lines = [line for line in normalized_lines if line.startswith("[ERROR|")]

    # Should have ~100 error lines
    assert len(error_lines) >= 95
    assert len(error_lines) <= 105

    # Verify errors from different services
    error_text = "".join(error_lines)
    assert "[ERROR|API-GATEWAY]" in error_text
    assert "[ERROR|ORDER-SVC]" in error_text
    assert "[ERROR|PAYMENT-SVC]" in error_text


def test_application_database_operations(application_rules):
    """Test database operation normalization."""
    processor = PatterndbYaml(rules_path=application_rules)

    db_logs = [
        "2024-11-15T10:00:01.000Z [DATABASE] SELECT table=users duration=5ms",
        "2024-11-15T10:00:02.000Z [DATABASE] INSERT table=orders duration=12ms",
        "2024-11-15T10:00:03.000Z [DATABASE] UPDATE table=products duration=8ms",
        "2024-11-15T10:00:04.000Z [DATABASE] DELETE table=inventory duration=3ms",
    ]

    input_data = StringIO("\n".join(db_logs))
    output_data = StringIO()
    processor.process(input_data, output_data)

    output_data.seek(0)
    normalized = output_data.readlines()

    assert normalized[0].strip() == "[DB|SELECT:users]"
    assert normalized[1].strip() == "[DB|INSERT:orders]"
    assert normalized[2].strip() == "[DB|UPDATE:products]"
    assert normalized[3].strip() == "[DB|DELETE:inventory]"


def test_application_high_frequency_scenario(application_rules):
    """Test high-frequency log scenario (bursts of similar logs)."""
    processor = PatterndbYaml(rules_path=application_rules)

    # Simulate burst of identical requests
    burst_log = "2024-11-15T10:00:01.000Z [API-GATEWAY] INFO: GET /api/v1/health -> 200 (5ms)"
    logs = [burst_log] * 5000  # 5000 identical health checks

    input_data = StringIO("\n".join(logs))
    output_data = StringIO()
    processor.process(input_data, output_data)

    # Check cache effectiveness
    cache_info = processor.norm_engine.normalize_cached.cache_info()

    # Should have very high cache hit rate
    total = cache_info.hits + cache_info.misses
    hit_rate = cache_info.hits / total if total > 0 else 0
    assert hit_rate >= 0.999  # > 99.9% cache hits

    # Verify output
    stats = processor.get_stats()
    assert stats["lines_processed"] == 5000
    assert stats["lines_matched"] == 5000


def test_application_mixed_timestamp_formats(application_rules):
    """Test handling of various timestamp formats across services."""
    processor = PatterndbYaml(rules_path=application_rules)

    # Different but similar timestamps
    logs = [
        "2024-11-15T10:00:01.123Z [API-GATEWAY] INFO: GET /api/v1/users -> 200 (10ms)",
        "2024-11-15T10:00:02.456Z [API-GATEWAY] INFO: GET /api/v1/users -> 200 (11ms)",
        "2024-11-15T10:00:03.789Z [API-GATEWAY] INFO: GET /api/v1/users -> 200 (12ms)",
    ]

    input_data = StringIO("\n".join(logs))
    output_data = StringIO()
    processor.process(input_data, output_data)

    # All should match and normalize identically (timestamps ignored)
    output_data.seek(0)
    normalized_lines = [line.strip() for line in output_data.readlines()]

    for line in normalized_lines:
        assert line == "[GATEWAY|GET:/api/v1/users|200]"


def test_application_partial_failure_scenario(application_rules):
    """Test scenario where some services fail while others succeed."""
    processor = PatterndbYaml(rules_path=application_rules)

    failure_scenario = [
        "2024-11-15T10:00:01.000Z [API-GATEWAY] INFO: POST /api/v1/orders -> 200 (15ms)",
        "2024-11-15T10:00:02.000Z [ORDER-SVC] INFO order_id=ORD999 action=created user=user_1",
        "2024-11-15T10:00:03.000Z [PAYMENT-SVC] ERROR transaction=TXN999 status=failed amount=$50.00",
        "2024-11-15T10:00:04.000Z [PAYMENT-SVC] ERROR: Payment gateway timeout",
        "2024-11-15T10:00:05.000Z [ORDER-SVC] INFO order_id=ORD999 action=failed user=user_1",
    ]

    input_data = StringIO("\n".join(failure_scenario))
    output_data = StringIO()
    processor.process(input_data, output_data)

    output_data.seek(0)
    normalized = output_data.readlines()

    # Verify failure path
    assert normalized[0].strip() == "[GATEWAY|POST:/api/v1/orders|200]"
    assert normalized[1].strip() == "[ORDER|created|user:user_1]"
    assert normalized[2].strip() == "[PAYMENT|failed]"
    assert normalized[3].strip() == "[ERROR|PAYMENT-SVC] Payment gateway timeout"
    assert normalized[4].strip() == "[ORDER|failed|user:user_1]"


def test_application_multi_tenant_isolation(application_rules):
    """Test that user/tenant information is properly extracted and normalized."""
    processor = PatterndbYaml(rules_path=application_rules)

    multi_tenant_logs = [
        "2024-11-15T10:00:01.000Z [ORDER-SVC] INFO order_id=ORD1 action=created user=tenant_a_user1",
        "2024-11-15T10:00:02.000Z [ORDER-SVC] INFO order_id=ORD2 action=created user=tenant_b_user1",
        "2024-11-15T10:00:03.000Z [ORDER-SVC] INFO order_id=ORD3 action=created user=tenant_a_user2",
    ]

    input_data = StringIO("\n".join(multi_tenant_logs))
    output_data = StringIO()
    processor.process(input_data, output_data)

    output_data.seek(0)
    normalized = output_data.readlines()

    # Verify tenant information is normalized identically
    assert normalized[0].strip() == "[ORDER|created|user:tenant_a_user1]"
    assert normalized[1].strip() == "[ORDER|created|user:tenant_b_user1]"
    assert normalized[2].strip() == "[ORDER|created|user:tenant_a_user2]"


def test_application_throughput_benchmark(application_rules):
    """Benchmark processing throughput with application logs."""
    processor = PatterndbYaml(rules_path=application_rules)

    # Generate 20,000 log lines
    log_template = "2024-11-15T10:00:{second:02d}.{ms:03d}Z [API-GATEWAY] INFO: GET /api/v1/health -> 200 (5ms)\n"
    logs = []
    for i in range(20000):
        logs.append(log_template.format(second=i % 60, ms=i % 1000))

    input_data = StringIO("".join(logs))
    output_data = StringIO()

    import time

    start = time.time()
    processor.process(input_data, output_data)
    elapsed = time.time() - start

    stats = processor.get_stats()
    assert stats["lines_processed"] == 20000

    # Calculate throughput
    throughput = stats["lines_processed"] / elapsed if elapsed > 0 else 0
    assert throughput > 1000  # At least 1k lines/sec

    print(f"\nApplication log throughput: {throughput:.0f} lines/sec")
