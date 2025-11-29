# Testing: API Contract Testing

## Overview

API contract testing verifies that different API implementations (versions, rewrites, microservices) adhere to the same contract. Request/response logs contain dynamic data (timestamps, tokens, IDs) that changes with every execution. Normalizing API logs reveals whether the contract is preserved across implementations.

## Core Problem Statement

"API implementations change but contracts should remain stable." You need to verify that API v2 provides the same endpoints, status codes, and response structures as v1, despite different logging formats, performance characteristics, and dynamic data.

## Example Scenario

Your e-commerce API is being rewritten from v1 to v2. The new version:

- Uses structured logging instead of plain text
- Includes performance metrics (duration)
- Adds API version to responses
- Uses different auth token format

You need to verify that v2 implements the same contract as v1: same endpoints, same HTTP methods, same status codes, same response shapes.

## Input Data

???+ note "API v1 Logs (Original Implementation)"
    ```text
    --8<-- "use-cases/testing/fixtures/api-v1-requests.log"
    ```

    Original API logs with bearer tokens and plain JSON responses.

???+ note "API v2 Logs (Rewritten Implementation)"
    ```text
    --8<-- "use-cases/testing/fixtures/api-v2-requests.log"
    ```

    New API logs with structured format, performance metrics, and API version field.

## Normalization Rules

Create rules that extract contract-relevant information while ignoring implementation details:

???+ note "API Contract Normalization Rules"
    ```yaml
    --8<-- "use-cases/testing/fixtures/api-contract-rules.yaml"
    ```

    Rules preserve: HTTP method, endpoint path, status code, response shape (field names).
    Rules ignore: timestamps, auth tokens, field values, performance metrics, API version markers.

## Implementation

=== "CLI"

    ```bash
    # Normalize both API versions
    patterndb-yaml --rules api-contract-rules.yaml api-v1-requests.log \
        --quiet > v1-contract.log

    patterndb-yaml --rules api-contract-rules.yaml api-v2-requests.log \
        --quiet > v2-contract.log

    # Verify contract compliance
    if diff -q v1-contract.log v2-contract.log; then
        echo "✓ API v2 implements the same contract as v1"
    else
        echo "✗ API contract violations detected:"
        diff v1-contract.log v2-contract.log
    fi

    # Analyze endpoint coverage
    echo "\nEndpoint coverage:"
    grep '^\[GET:' v2-contract.log | wc -l
    grep '^\[POST:' v2-contract.log | wc -l
    grep '^\[PUT:' v2-contract.log | wc -l
    grep '^\[DELETE:' v2-contract.log | wc -l
    ```

=== "Python"

    <!-- verify-file: output.txt expected: api-contract-output-1.txt -->
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

    # Normalize both API versions
    processor = PatterndbYaml(rules_path=Path("api-contract-rules.yaml"))

    def extract_contract(log_file):
        """Extract API contract from log file"""
        with open(log_file) as f:
            from io import StringIO
            output = StringIO()
            processor.process(f, output)
            output.seek(0)
            return [line.strip() for line in output if line.strip()]

    v1_contract = extract_contract("api-v1-requests.log")
    v2_contract = extract_contract("api-v2-requests.log")

    # Compare contracts
    if v1_contract == v2_contract:
        print("✓ API v2 implements the same contract as v1\n")

        # Analyze contract
        print("Contract Summary:")
        print(f"  Total operations: {len(v1_contract)}")

        # Count by type
        requests = [
            line for line in v1_contract
            if not line.startswith('[RESPONSE')
        ]
        responses = [
            line for line in v1_contract
            if line.startswith('[RESPONSE')
        ]

        print(f"  Requests: {len(requests)}")
        print(f"  Responses: {len(responses)}")

        # Count by method
        methods = Counter()
        for req in requests:
            if match := re.match(r'\[(\w+):', req):
                methods[match.group(1)] += 1

        print("\n  HTTP Methods:")
        for method, count in sorted(methods.items()):
            print(f"    {method}: {count}")

        # List endpoints
        print("\n  Endpoints:")
        for req in requests:
            if match := re.match(r'\[(\w+):([^,]+),', req):
                method, path = match.groups()
                print(f"    {method} {path}")

    else:
        print("✗ API contract violations detected\n")

        # Find differences
        v1_set = set(v1_contract)
        v2_set = set(v2_contract)

        missing = v1_set - v2_set
        added = v2_set - v1_set

        if missing:
            print("Missing in v2 (breaking changes):")
            for item in sorted(missing):
                print(f"  - {item}")

        if added:
            print("\nAdded in v2 (new operations):")
            for item in sorted(added):
                print(f"  + {item}")

    # Restore stdout and close output file
    sys.stdout = _original_stdout
    output_file.close()
    ```

## Expected Output

???+ success "Normalized API Contract (Both Versions)"
    ```text
    --8<-- "use-cases/testing/fixtures/api-contract-normalized.log"
    ```

    Both API v1 and v2 produce identical normalized contract, confirming compatibility.

### Contract Elements

The normalized contract captures:

- **Endpoints**: All HTTP methods and paths
- **Status Codes**: Expected response codes (200, 201, 204, etc.)
- **Response Shapes**: Field names in each response type

Dynamic data ignored:

- Timestamps and durations
- Auth tokens
- Field values (IDs, emails, amounts)
- API version markers

## Practical Workflows

### 1. Continuous Contract Validation

Integrate into CI/CD to verify contract compliance:

```bash
#!/bin/bash
# Run integration tests against both versions
run-api-tests --version=v1 --log=v1-test.log
run-api-tests --version=v2 --log=v2-test.log

# Normalize and compare contracts
patterndb-yaml --rules api-contract-rules.yaml v1-test.log --quiet > v1-norm.log
patterndb-yaml --rules api-contract-rules.yaml v2-test.log --quiet > v2-norm.log

# Fail build if contracts differ
if ! diff -q v1-norm.log v2-norm.log; then
    echo "ERROR: API v2 breaks contract compatibility"
    diff v1-norm.log v2-norm.log
    exit 1
fi

echo "✓ API v2 maintains contract compatibility"
```

### 2. Contract Coverage Analysis

Verify test coverage against API specification:

<!-- verify-file: output.txt expected: api-contract-output-2.txt -->
```python
import sys
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import re

# Redirect stdout to file for testing
_original_stdout = sys.stdout
output_file = open("output.txt", "w")
sys.stdout = output_file

# Expected endpoints from API spec
API_SPEC = {
    "GET /api/users/{id}": "200",
    "GET /api/orders/{id}": "200",
    "POST /api/orders": "201",
    "PUT /api/orders/{id}": "200",
    "DELETE /api/cart/items/{id}": "204",
}

processor = PatterndbYaml(rules_path=Path("api-contract-rules.yaml"))

# Extract tested endpoints
with open("api-test.log") as f:
    from io import StringIO
    output = StringIO()
    processor.process(f, output)
    output.seek(0)

    tested_endpoints = {}
    for line in output:
        if match := re.match(r'\[(\w+):([^,]+),status:(\d+)\]', line):
            method, path, status = match.groups()
            # Normalize path parameters
            normalized_path = re.sub(r'/\d+', '/{id}', path)
            endpoint = f"{method} {normalized_path}"
            tested_endpoints[endpoint] = status

# Compare with spec
print("Contract Coverage Analysis:\n")
for endpoint, expected_status in sorted(API_SPEC.items()):
    if endpoint in tested_endpoints:
        actual_status = tested_endpoints[endpoint]
        if actual_status == expected_status:
            print(f"✓ {endpoint} → {actual_status}")
        else:
            print(f"✗ {endpoint} → Expected {expected_status}, "
                  f"got {actual_status}")
    else:
        print(f"⚠ {endpoint} → NOT TESTED")

# Find extra endpoints (not in spec)
extra = set(tested_endpoints.keys()) - set(API_SPEC.keys())
if extra:
    print("\nExtra endpoints (not in spec):")
    for endpoint in sorted(extra):
        print(f"  + {endpoint}")

# Restore stdout and close output file
sys.stdout = _original_stdout
output_file.close()
```

### 3. Breaking Change Detection

Detect API changes that break backward compatibility:

```bash
# Capture baseline contract from production
patterndb-yaml --rules api-contract-rules.yaml prod-api.log \
    --quiet | sort > baseline-contract.txt

# Test new version
patterndb-yaml --rules api-contract-rules.yaml new-api.log \
    --quiet | sort > new-contract.txt

# Find breaking changes (removed operations)
echo "Breaking Changes (removed):"
comm -23 baseline-contract.txt new-contract.txt

# Find additions (new operations)
echo "\nNew Operations:"
comm -13 baseline-contract.txt new-contract.txt

# Find preserved operations
preserved=$(comm -12 baseline-contract.txt new-contract.txt | wc -l)
total=$(wc -l < baseline-contract.txt)
percentage=$((preserved * 100 / total))

echo "\nBackward Compatibility: $percentage% " \
    "($preserved/$total operations preserved)"
```

### 4. Microservices Contract Testing

Verify multiple microservices implement consistent contracts:

<!-- verify-file: output.txt expected: api-contract-output-3.txt -->
```python
import sys
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import re
from collections import defaultdict

# Redirect stdout to file for testing
_original_stdout = sys.stdout
output_file = open("output.txt", "w")
sys.stdout = output_file

processor = PatterndbYaml(rules_path=Path("api-contract-rules.yaml"))

# Services implementing the same API
services = ["orders-service", "orders-v2-service", "orders-lambda"]

contracts = {}
for service in services:
    with open(f"{service}-api.log") as f:
        from io import StringIO
        output = StringIO()
        processor.process(f, output)
        output.seek(0)
        contracts[service] = set(
            line.strip() for line in output if line.strip()
        )

# Find common contract
common_contract = set.intersection(*contracts.values())

print("Microservices Contract Analysis:\n")
print(f"Common operations: {len(common_contract)}")

# Find service-specific operations
for service in services:
    unique = contracts[service] - common_contract
    if unique:
        print(f"\n{service} unique operations:")
        for op in sorted(unique):
            print(f"  + {op}")
    else:
        print(f"\n{service}: ✓ implements only common contract")

# Verify all services implement core endpoints
core_endpoints = {
    "[GET:/api/orders/{id},status:200]",
    "[POST:/api/orders,status:201]",
}

print("\nCore Endpoint Coverage:")
for service in services:
    missing = core_endpoints - contracts[service]
    if missing:
        print(f"✗ {service} missing:")
        for ep in sorted(missing):
            print(f"    {ep}")
    else:
        print(f"✓ {service} implements all core endpoints")

# Restore stdout and close output file
sys.stdout = _original_stdout
output_file.close()
```

### 5. Consumer-Driven Contract Testing

Verify API meets consumer expectations:

<!-- verify-file: output.txt expected: api-contract-output-4.txt -->
```python
import sys
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import re

# Redirect stdout to file for testing
_original_stdout = sys.stdout
output_file = open("output.txt", "w")
sys.stdout = output_file

processor = PatterndbYaml(rules_path=Path("api-contract-rules.yaml"))

# Consumer expectations (from consumer test suite)
CONSUMER_EXPECTATIONS = {
    "mobile-app": {
        "[GET:/api/users/{id},status:200]",
        "[GET:/api/orders/{id},status:200]",
    },
    "web-app": {
        "[GET:/api/users/{id},status:200]",
        "[POST:/api/orders,status:201]",
        "[PUT:/api/orders/{id},status:200]",
    },
}

# Extract actual API contract
with open("api-provider.log") as f:
    from io import StringIO
    output = StringIO()
    processor.process(f, output)
    output.seek(0)

    actual_contract = set()
    for line in output:
        # Normalize IDs in paths
        normalized = re.sub(
            r':/api/(\w+)/\d+,', r':/api/\1/{id},', line.strip()
        )
        if normalized:
            actual_contract.add(normalized)

# Verify each consumer's expectations
print("Consumer-Driven Contract Verification:\n")
for consumer, expectations in CONSUMER_EXPECTATIONS.items():
    missing = expectations - actual_contract
    if missing:
        print(f"✗ {consumer} expectations NOT MET:")
        for exp in sorted(missing):
            print(f"    Missing: {exp}")
    else:
        print(f"✓ {consumer} expectations satisfied "
              f"({len(expectations)} operations)")

# Restore stdout and close output file
sys.stdout = _original_stdout
output_file.close()
```

## Key Benefits

- **Verify API compatibility**: Ensure new versions maintain existing contracts
- **Detect breaking changes**: Find removed endpoints or changed status codes
- **Contract coverage**: Verify test coverage against API specification
- **Microservices consistency**: Ensure multiple services implement same contract
- **Consumer protection**: Validate API meets consumer expectations

## Related Topics

- [Rules](../../features/rules/rules.md) - Pattern matching and normalization
- [Statistics](../../features/stats/stats.md) - Measure match coverage
- [Explain Mode](../../features/explain/explain.md) - Debug pattern matching
