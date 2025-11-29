# Security: Log Aggregation & Analysis

## Overview

Security operations require correlating events across multiple systems: firewalls, IDS/IPS, application logs, and authentication systems. Each system logs in its own format, making correlation difficult. Normalizing all security logs into a unified format enables attack detection, incident response, and compliance reporting.

## Core Problem Statement

"Security events are scattered across systems with incompatible log formats." Detecting attacks requires correlating firewall blocks, IDS alerts, and authentication failures, but different formats prevent automated analysis.

## Example Scenario

Your security infrastructure includes:

- **Firewall**: Linux iptables logging kernel messages
- **IDS**: Snort-style alerts with ISO timestamps
- **Application**: Custom authentication logs

An attacker (198.51.100.23) attempts:

1. SQL injection against web server
2. SSH brute force
3. Multiple failed application logins

You need to correlate these events to detect the coordinated attack.

## Input Data

???+ note "Firewall Logs (iptables)"
    ```text
    --8<-- "use-cases/security/fixtures/firewall.log"
    ```

    Kernel-format firewall logs showing ACCEPT and DROP rules.

???+ note "IDS Alerts (Snort-style)"
    ```text
    --8<-- "use-cases/security/fixtures/ids.log"
    ```

    Intrusion detection alerts with timestamps and attack signatures.

???+ note "Application Authentication Logs"
    ```text
    --8<-- "use-cases/security/fixtures/app-auth.log"
    ```

    Application-level authentication events with user context.

## Normalization Rules

Create rules that extract security-relevant fields while normalizing format differences:

???+ note "Security Log Normalization Rules"
    ```yaml
    --8<-- "use-cases/security/fixtures/security-rules.yaml"
    ```

    Rules preserve: source IPs, destinations, attack types, user accounts, failure reasons.
    Rules ignore: timestamps (use log ingestion time), hostnames, interface names.

## Implementation

=== "CLI"

    ```bash
    # Combine all security logs
    cat firewall.log ids.log app-auth.log | \
        patterndb-yaml --rules security-rules.yaml \
            --quiet > unified-security.log

    # Correlate by source IP
    echo "Events by source IP:"
    grep -o 'src=[0-9.]*\|ip=[0-9.]*' unified-security.log | \
        sed 's/src=\|ip=//' | sort | uniq -c | sort -rn

    # Find coordinated attacks (same IP in multiple systems)
    echo "\nSuspicious IPs (multiple event types):"
    for ip in $(grep -o 'src=[0-9.]*\|ip=[0-9.]*' unified-security.log | \
                sed 's/src=\|ip=//' | sort -u); do
        event_types=$(grep "$ip" unified-security.log | \
                      grep -o '^\[[^:]*' | sort -u | wc -l)
        if [ "$event_types" -gt 2 ]; then
            echo "  $ip: $event_types different event types"
            grep "$ip" unified-security.log | head -5
        fi
    done
    ```

=== "Python"

    <!-- verify-file: output.txt expected: security-output-1.txt -->
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

    # Normalize all security logs
    processor = PatterndbYaml(rules_path=Path("security-rules.yaml"))

    # Combine all log sources
    all_logs = []
    for log_file in ["firewall.log", "ids.log", "app-auth.log"]:
        with open(log_file) as f:
            all_logs.extend(f.readlines())

    # Normalize combined logs
    from io import StringIO
    input_data = StringIO("".join(all_logs))
    output_data = StringIO()
    processor.process(input_data, output_data)

    # Parse normalized events
    output_data.seek(0)
    events = []
    for line in output_data:
        line = line.strip()
        if not line:
            continue

        # Extract event type and attributes
        match = re.match(r'\[([^:]+):(.+)\]', line)
        if match:
            event_type, attrs = match.groups()
            # Parse attributes
            attr_dict = {}
            for attr in attrs.split(','):
                if '=' in attr:
                    key, value = attr.split('=', 1)
                    attr_dict[key] = value

            events.append({
                'type': event_type,
                'attributes': attr_dict,
                'raw': line
            })

    # Correlate by source IP
    ip_events = defaultdict(list)
    for event in events:
        attrs = event['attributes']
        source_ip = attrs.get('src') or attrs.get('ip')
        if source_ip:
            ip_events[source_ip].append(event)

    # Detect coordinated attacks
    print("Coordinated Attack Detection:\n")
    for ip, ip_event_list in sorted(ip_events.items(),
                                     key=lambda x: len(x[1]),
                                     reverse=True):
        event_types = set(e['type'] for e in ip_event_list)

        if len(event_types) >= 3:
            print(f"⚠ HIGH PRIORITY: {ip}")
            print(f"  Event types: {', '.join(sorted(event_types))}")
            print(f"  Total events: {len(ip_event_list)}")
            print("  Timeline:")
            for event in ip_event_list[:5]:
                print(f"    - {event['raw']}")
            print()
        elif len(event_types) >= 2:
            print(f"⚠ MEDIUM: {ip} - {len(event_types)} event types")

    # Restore stdout and close output file
    sys.stdout = _original_stdout
    output_file.close()
    ```

## Expected Output

???+ success "Unified Security Log"
    ```text
    --8<-- "use-cases/security/fixtures/security-normalized.log"
    ```

    All security events normalized to consistent format for correlation.

### Attack Correlation

From the normalized logs, we can identify the attack pattern:

**Attacker: 198.51.100.23**
- `[firewall-drop:...]` - Blocked at firewall (port 22)
- `[ids-sqli:...]` - SQL injection attempt detected
- `[ids-bruteforce:...]` - Brute force attack on SSH
- `[auth-failure:...]` - Three failed application logins

**Attacker: 192.0.2.15**
- `[firewall-drop:...]` - Blocked suspicious source (port 3389)
- `[ids-portscan:...]` - Network port scan detected
- `[auth-failure:...]` - Failed login with disabled account

## Practical Workflows

### 1. Real-Time Attack Detection

Stream logs from multiple sources and detect attacks in real-time:

```bash
#!/bin/bash
# Tail all security log sources
tail -f /var/log/firewall.log /var/log/ids/alerts.log /var/log/app/auth.log | \
    patterndb-yaml --rules security-rules.yaml --quiet | \
    while read event; do
        # Extract source IP
        if [[ "$event" =~ src=([0-9.]+)|ip=([0-9.]+) ]]; then
            ip="${BASH_REMATCH[1]}${BASH_REMATCH[2]}"

            # Count recent events from this IP
            recent_count=$(grep "$ip" /tmp/recent-events.log \
                2>/dev/null | wc -l)

            # Alert on threshold
            if [ "$recent_count" -gt 5 ]; then
                echo "🚨 ALERT: Suspicious activity from $ip" \
                    "($recent_count events)"
                grep "$ip" /tmp/recent-events.log
            fi

            # Track event
            echo "$event" >> /tmp/recent-events.log
        fi

        # Rotate recent events (keep last 100)
        tail -100 /tmp/recent-events.log > /tmp/recent-events.tmp
        mv /tmp/recent-events.tmp /tmp/recent-events.log
    done
```

### 2. Incident Timeline Reconstruction

Build attack timeline from multiple sources:

<!-- verify-file: output.txt expected: security-output-2.txt -->
```python
import sys
from patterndb_yaml import PatterndbYaml
from pathlib import Path
from datetime import datetime
from io import StringIO
import re

# Redirect stdout to file for testing
_original_stdout = sys.stdout
output_file = open("output.txt", "w")
sys.stdout = output_file

processor = PatterndbYaml(rules_path=Path("security-rules.yaml"))

# Normalize logs from incident timeframe
incident_logs = [
    "firewall-incident.log",
    "ids-incident.log",
    "auth-incident.log"
]
all_events = []

for log_file in incident_logs:
    with open(log_file) as f:
        output = StringIO()
        processor.process(f, output)
        output.seek(0)
        all_events.extend([line.strip() for line in output if line.strip()])

# Filter by attacker IP
attacker_ip = "198.51.100.23"
attacker_events = [e for e in all_events if attacker_ip in e]

# Generate incident report
print(f"Incident Timeline for {attacker_ip}")
print("=" * 60)
for i, event in enumerate(attacker_events, 1):
    # Extract event type
    match = re.match(r'\[([^:]+):', event)
    if match:
        event_type = match.group(1)
        print(f"{i}. [{event_type.upper()}] {event}")

print(f"\nTotal events: {len(attacker_events)}")

# Restore stdout and close output file
sys.stdout = _original_stdout
output_file.close()
```

### 3. Compliance Reporting (Failed Access Attempts)

Generate compliance reports for failed access attempts:

```bash
# Normalize security logs
cat firewall.log ids.log app-auth.log | \
    patterndb-yaml --rules security-rules.yaml --quiet > unified.log

# Extract failed access attempts
echo "Failed Access Attempts Report"
echo "=============================="
echo

echo "Firewall Blocks:"
grep '^\[firewall-drop:' unified.log | wc -l
grep '^\[firewall-drop:' unified.log | head -10

echo "\nAuthentication Failures:"
grep '^\[auth-failure:' unified.log | wc -l
grep '^\[auth-failure:' unified.log

echo "\nIntrusion Attempts:"
grep '^\[ids-' unified.log | wc -l
grep '^\[ids-' unified.log
```

### 4. Threat Intelligence Enrichment

Correlate with threat intelligence feeds:

<!-- verify-file: output.txt expected: security-output-3.txt -->
```python
import sys
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import re

# Redirect stdout to file for testing
_original_stdout = sys.stdout
output_file = open("output.txt", "w")
sys.stdout = output_file

# Known malicious IPs (from threat feed)
threat_ips = {"198.51.100.23", "192.0.2.15"}

processor = PatterndbYaml(rules_path=Path("security-rules.yaml"))

# Normalize logs
with open("combined-security.log") as f:
    from io import StringIO
    output = StringIO()
    processor.process(f, output)
    output.seek(0)
    events = [line.strip() for line in output if line.strip()]

# Check against threat feed
print("Threat Intelligence Matches:\n")
for event in events:
    # Extract IPs from event
    ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', event)

    for ip in ips:
        if ip in threat_ips:
            print(f"⚠ KNOWN THREAT: {ip}")
            print(f"  Event: {event}")
            print()

# Restore stdout and close output file
sys.stdout = _original_stdout
output_file.close()
```

### 5. SIEM Integration

Export normalized logs to SIEM in CEF format:

<!-- verify-file: output.txt expected: security-output-4.txt -->
```python
import sys
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import re

# Redirect stdout to file for testing
_original_stdout = sys.stdout
output_file = open("output.txt", "w")
sys.stdout = output_file

processor = PatterndbYaml(rules_path=Path("security-rules.yaml"))

def to_cef(event):
    """Convert normalized event to CEF format"""
    match = re.match(r'\[([^:]+):(.+)\]', event)
    if not match:
        return None

    event_type, attrs = match.groups()

    # Parse attributes
    attr_dict = {}
    for attr in attrs.split(','):
        if '=' in attr:
            key, value = attr.split('=', 1)
            attr_dict[key] = value

    # Map to CEF fields
    severity = 5 if 'drop' in event_type or 'failure' in event_type else 3
    src_ip = attr_dict.get('src', attr_dict.get('ip', ''))
    dst_ip = attr_dict.get('dst', '').split(':')[0]

    # CEF format:
    # CEF:Version|Device Vendor|Device Product|Device Version|
    # Signature ID|Name|Severity|Extension
    return (
        f"CEF:0|PatternDB|SecurityAggregator|1.0|"
        f"{event_type}|{event_type}|{severity}|"
        f"src={src_ip} dst={dst_ip} act={event_type}"
    )

# Process and export
with open("combined-security.log") as f:
    from io import StringIO
    output = StringIO()
    processor.process(f, output)
    output.seek(0)

    with open("security-cef.log", "w") as cef_out:
        for line in output:
            line = line.strip()
            if line:
                cef_event = to_cef(line)
                if cef_event:
                    cef_out.write(cef_event + "\n")

# Print the generated CEF log for verification
with open("security-cef.log") as f:
    print(f.read(), end='')

# Restore stdout and close output file
sys.stdout = _original_stdout
output_file.close()
```

## Key Benefits

- **Unified visibility**: Single view across all security systems
- **Attack correlation**: Connect events from firewall, IDS, and application logs
- **Rapid incident response**: Quickly identify coordinated attacks
- **Compliance reporting**: Aggregate failed access attempts across systems
- **SIEM integration**: Export normalized logs in standard formats

## Related Topics

- [Rules](../../features/rules/rules.md) - Pattern matching and normalization
- [Statistics](../../features/stats/stats.md) - Measure match coverage
- [Explain Mode](../../features/explain/explain.md) - Debug pattern matching
