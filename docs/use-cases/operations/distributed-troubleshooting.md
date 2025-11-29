# Operations: Distributed Systems Troubleshooting

## Overview

Distributed systems scatter request handling across multiple services, each with its own log format and conventions. Troubleshooting requires correlating events across services using correlation IDs (request_id, trace_id). Normalizing logs from all services into a unified format enables request tracing and root cause analysis.

## Core Problem Statement

"Distributed requests span multiple services with incompatible log formats." To understand why a request failed, you need to follow it through the gateway, order service, and payment service, but each logs differently and uses different field names for correlation IDs.

## Example Scenario

Your e-commerce platform has three services:

- **API Gateway**: Routes requests, logs `request_id`
- **Order Service**: Manages orders, logs `trace_id`
- **Payment Service**: Processes payments, logs `correlation_id`

All three refer to the same correlation ID but use different names and formats. A request fails with "Payment service unavailable" and you need to trace the full flow to understand what happened.

## Input Data

???+ note "API Gateway Logs"
    ```text
    --8<-- "use-cases/operations/fixtures/api-gateway.log"
    ```

    Gateway logs with `request_id` and upstream service responses.

???+ note "Order Service Logs"
    ```text
    --8<-- "use-cases/operations/fixtures/order-service.log"
    ```

    Order service logs with `trace_id` and business events.

???+ note "Payment Service Logs"
    ```text
    --8<-- "use-cases/operations/fixtures/payment-service.log"
    ```

    Payment service logs with `correlation_id` and payment processing events.

## Normalization Rules

Create rules that extract events and normalize correlation ID names:

???+ note "Distributed Tracing Rules"
    ```yaml
    --8<-- "use-cases/operations/fixtures/distributed-rules.yaml"
    ```

    Rules preserve: correlation ID (normalized across services), service name, event type.
    Rules ignore: timestamps, durations, transaction IDs, error messages (extract separately).

## Implementation

=== "CLI"

    ```bash
    # Combine logs from all services
    cat api-gateway.log order-service.log payment-service.log | \
        patterndb-yaml --rules distributed-rules.yaml --quiet > combined.log

    # Trace a specific request
    request_id="req-abc123"
    echo "Request trace for $request_id:"
    grep "^\[$request_id\]" combined.log

    # Find failed requests
    echo "\nFailed requests:"
    grep 'error\|failed' combined.log | cut -d']' -f1 | sort -u | \
        while read req_id; do
            echo "\n$req_id]:"
            grep "^$req_id\]" combined.log
        done

    # Analyze error distribution
    echo "\nError types:"
    grep 'error\|failed' combined.log | cut -d' ' -f2 | sort | uniq -c
    ```

=== "Python"

    <!-- verify-file: output.txt expected: distributed-output-0.txt -->
    ```python
    import sys
    from patterndb_yaml import PatterndbYaml
    from pathlib import Path
    from collections import defaultdict
    import re

    # Redirect stdout to file for testing
    _original_stdout = sys.stdout
    output_file = open("output.txt", "w")
    sys.stdout = output_file

    # Combine and normalize all service logs
    processor = PatterndbYaml(rules_path=Path("distributed-rules.yaml"))

    log_files = ["api-gateway.log", "order-service.log", "payment-service.log"]

    all_events = []
    for log_file in log_files:
        with open(log_file) as f:
            from io import StringIO
            output = StringIO()
            processor.process(f, output)
            output.seek(0)

            for line in output:
                line = line.strip()
                if line:
                    # Extract correlation ID and event
                    if match := re.match(r'\[([^\]]+)\] (.+)', line):
                        correlation_id, event = match.groups()
                        all_events.append({
                            'correlation_id': correlation_id,
                            'event': event,
                            'raw': line
                        })

    # Group by correlation ID
    traces = defaultdict(list)
    for event in all_events:
        traces[event['correlation_id']].append(event)

    # Analyze traces
    print("Distributed Request Analysis:\n")

    for correlation_id, events in sorted(traces.items()):
        # Check for errors
        has_error = any('error' in e['event'] or 'failed' in e['event']
                       for e in events)

        status = "✗ FAILED" if has_error else "✓ SUCCESS"
        print(f"{status} {correlation_id} ({len(events)} events)")

        # Show trace
        for event in events:
            has_issue = 'error' in event['event'] or \
                'failed' in event['event']
            prefix = "  ⚠" if has_issue else "   "
            print(f"{prefix} {event['event']}")

        print()

    # Restore stdout and close output file
    sys.stdout = _original_stdout
    output_file.close()
    ```

## Expected Output

???+ success "Normalized Distributed Trace"
    ```text
    --8<-- "use-cases/operations/fixtures/distributed-normalized.log"
    ```

    All services unified with correlation IDs, showing complete request flows.

### Request Flows

**req-abc123** (Success):
1. Gateway receives POST /orders
2. Order service creates order 5001
3. Order service calls payment
4. Payment service processes payment
5. Payment service authorizes payment
6. Order service receives payment success
7. Gateway returns 200

**req-def456** (Success):
1. Gateway receives GET /orders/5001
2. Order service looks up order
3. Order service finds order (status=paid)
4. Gateway returns 200

**req-ghi789** (Failure):
1. Gateway receives POST /orders
2. Order service creates order 5002
3. Order service calls payment
4. Payment service processes payment
5. **Payment service error** (timeout)
6. Order service receives payment failure
7. Gateway returns 500

## Practical Workflows

### 1. Root Cause Analysis

Trace failed requests to find root cause:

<!-- verify-file: output.txt expected: distributed-output-1.txt -->
```python
import sys
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import re

# Redirect stdout to file for testing
_original_stdout = sys.stdout
output_file = open("output.txt", "w")
sys.stdout = output_file

processor = PatterndbYaml(rules_path=Path("distributed-rules.yaml"))

# Combine logs
log_files = ["api-gateway.log", "order-service.log", "payment-service.log"]
combined_logs = []

for log_file in log_files:
    with open(log_file) as f:
        combined_logs.extend(f.readlines())

# Normalize
from io import StringIO
input_data = StringIO("".join(combined_logs))
output_data = StringIO()
processor.process(input_data, output_data)
output_data.seek(0)

# Find failed requests
failed_requests = set()
for line in output_data:
    if 'error' in line.lower() or 'failed' in line.lower():
        if match := re.match(r'\[([^\]]+)\]', line):
            failed_requests.add(match.group(1))

# Analyze each failure
output_data.seek(0)
print("Root Cause Analysis:\n")

for request_id in sorted(failed_requests):
    print(f"Request: {request_id}")
    print("Timeline:")

    output_data.seek(0)
    for line in output_data:
        if line.startswith(f"[{request_id}]"):
            # Highlight errors
            if 'error' in line.lower() or 'failed' in line.lower():
                print(f"  → {line.strip()}  <-- ROOT CAUSE")
            else:
                print(f"    {line.strip()}")

    print()

# Restore stdout and close output file
sys.stdout = _original_stdout
output_file.close()
```

### 2. Service Dependency Mapping

Identify service call patterns:

<!-- verify-file: output.txt expected: distributed-output-2.txt -->
```python
import sys
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import re

# Redirect stdout to file for testing
_original_stdout = sys.stdout
output_file = open("output.txt", "w")
sys.stdout = output_file

processor = PatterndbYaml(rules_path=Path("distributed-rules.yaml"))

# Process all logs
log_files = ["api-gateway.log", "order-service.log", "payment-service.log"]
events = []

for log_file in log_files:
    with open(log_file) as f:
        from io import StringIO
        output = StringIO()
        processor.process(f, output)
        output.seek(0)

        for line in output:
            if match := re.match(r'\[([^\]]+)\] ([^:]+):(.+)', line.strip()):
                req_id, service, event = match.groups()
                events.append((req_id, service, event))

# Build dependency graph
from collections import defaultdict
dependencies = defaultdict(set)

# Group events by request
from itertools import groupby
events.sort(key=lambda x: x[0])

for req_id, group in groupby(events, key=lambda x: x[0]):
    services_in_request = []
    for _, service, _ in group:
        if service not in services_in_request:
            services_in_request.append(service)

    # Record dependencies (sequential calls)
    for i in range(len(services_in_request) - 1):
        dependencies[services_in_request[i]].add(services_in_request[i+1])

# Display dependency graph
print("Service Dependency Map:\n")
for caller, callees in sorted(dependencies.items()):
    print(f"{caller} →")
    for callee in sorted(callees):
        print(f"    {callee}")

# Restore stdout and close output file
sys.stdout = _original_stdout
output_file.close()
```

### 3. Latency Bottleneck Detection

Find slow services in request path:

```bash
# Extract service events with timing (requires raw logs for timestamps)
cat api-gateway.log order-service.log payment-service.log | \
    patterndb-yaml --rules distributed-rules.yaml --quiet > normalized.log

# For each request, calculate service-level latency
# (This example assumes normalized output preserves original timestamps)

grep '^\[req-' normalized.log | \
    while read line; do
        req_id=$(echo "$line" | grep -o '^\[[^]]*\]')
        service=$(echo "$line" | cut -d' ' -f2 | cut -d':' -f1)
        echo "$req_id $service"
    done | \
    sort | uniq -c | \
    awk '{print $2 " " $3 ": " $1 " events"}'
```

### 4. Error Rate by Service

Calculate error rates for each service:

<!-- verify-file: output.txt expected: distributed-output-3.txt -->
```python
import sys
from patterndb_yaml import PatterndbYaml
from pathlib import Path
from collections import Counter
import re

# Redirect stdout to file for testing
_original_stdout = sys.stdout
output_file = open("output.txt", "w")
sys.stdout = output_file

processor = PatterndbYaml(rules_path=Path("distributed-rules.yaml"))

# Process logs
log_files = ["api-gateway.log", "order-service.log", "payment-service.log"]
service_events = Counter()
service_errors = Counter()

for log_file in log_files:
    with open(log_file) as f:
        from io import StringIO
        output = StringIO()
        processor.process(f, output)
        output.seek(0)

        for line in output:
            if match := re.match(r'\[([^\]]+)\] ([^:]+):(.+)', line.strip()):
                _, service, event = match.groups()
                service_events[service] += 1

                if 'error' in event.lower() or 'failed' in event.lower():
                    service_errors[service] += 1

# Calculate error rates
print("Error Rates by Service:\n")
print(f"{'Service':<20} {'Total':<10} {'Errors':<10} {'Rate':<10}")
print("-" * 50)

for service in sorted(service_events.keys()):
    total = service_events[service]
    errors = service_errors[service]
    rate = (errors / total * 100) if total > 0 else 0

    status = "⚠" if rate > 10 else "✓"
    print(f"{status} {service:<18} {total:<10} {errors:<10} {rate:>6.1f}%")

# Restore stdout and close output file
sys.stdout = _original_stdout
output_file.close()
```

### 5. Request Correlation Dashboard

Generate summary of all requests:

<!-- verify-file: output.txt expected: distributed-output-4.txt -->
```python
import sys
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import re

# Redirect stdout to file for testing
_original_stdout = sys.stdout
output_file = open("output.txt", "w")
sys.stdout = output_file

processor = PatterndbYaml(rules_path=Path("distributed-rules.yaml"))

# Combine and process
log_files = ["api-gateway.log", "order-service.log", "payment-service.log"]
all_logs = []
for log_file in log_files:
    with open(log_file) as f:
        all_logs.extend(f.readlines())

from io import StringIO
output = StringIO()
processor.process(StringIO("".join(all_logs)), output)
output.seek(0)

# Group by request
from collections import defaultdict
requests = defaultdict(
    lambda: {'services': set(), 'events': [], 'status': 'unknown'}
)

for line in output:
    if match := re.match(r'\[([^\]]+)\] ([^:]+):(.+)', line.strip()):
        req_id, service, event = match.groups()
        requests[req_id]['services'].add(service)
        requests[req_id]['events'].append(f"{service}:{event}")

        # Determine status
        if 'error' in event.lower() or 'failed' in event.lower():
            requests[req_id]['status'] = 'failed'
        elif requests[req_id]['status'] == 'unknown':
            requests[req_id]['status'] = 'success'

# Display dashboard
print("Request Dashboard:\n")
print(f"{'Request ID':<15} {'Status':<10} {'Services':<8} {'Events':<8}")
print("-" * 50)

for req_id in sorted(requests.keys()):
    req = requests[req_id]
    status_icon = "✓" if req['status'] == 'success' else "✗"
    service_count = len(req['services'])
    event_count = len(req['events'])

    print(f"{req_id:<15} {status_icon} {req['status']:<9} "
          f"{service_count:<8} {event_count:<8}")

# Summary stats
total = len(requests)
failed = sum(1 for r in requests.values() if r['status'] == 'failed')
success = total - failed
failure_pct = failed / total * 100

print(f"\nSummary: {total} requests, {success} success, "
      f"{failed} failed ({failure_pct:.0f}% failure rate)")

# Restore stdout and close output file
sys.stdout = _original_stdout
output_file.close()
```

## Key Benefits

- **End-to-end tracing**: Follow requests across all services
- **Root cause identification**: Pinpoint which service caused failures
- **Service dependency mapping**: Understand service call patterns
- **Error correlation**: Link errors across service boundaries
- **Performance analysis**: Identify bottlenecks in distributed flows

## Related Topics

- [Rules](../../features/rules/rules.md) - Pattern matching and normalization
- [Statistics](../../features/stats/stats.md) - Measure match coverage
- [Explain Mode](../../features/explain/explain.md) - Debug pattern matching
