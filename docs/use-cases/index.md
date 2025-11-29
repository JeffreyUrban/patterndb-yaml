# Use Cases

Real-world examples demonstrating how to use patterndb-yaml to solve common log analysis challenges.

## Testing

**Verify behavior, detect regressions, ensure quality**

- **[Application Version Comparison](testing/version-comparison.md)** - Compare log formats between application versions to verify identical behavior
- **[API Contract Testing](testing/api-contract.md)** - Verify API implementations maintain contracts across versions and rewrites
- **[Performance Regression Detection](testing/performance-regression.md)** - Detect performance issues via structural metrics (cache misses, query counts)
- **[Golden Master Testing](testing/golden-master.md)** - Safely refactor legacy code by capturing and comparing behavior

## DevOps

**Build reliability, deployment validation, CI/CD**

- **[CI/CD Build Reproducibility](devops/build-reproducibility.md)** - Verify builds are reproducible by filtering ephemeral data (timestamps, PIDs)

## Operations

**Monitor, troubleshoot, validate deployments**

- **[Multi-Environment Validation](operations/multi-environment.md)** - Ensure dev, staging, and production environments behave consistently
- **[Distributed Systems Troubleshooting](operations/distributed-troubleshooting.md)** - Correlate events across microservices using correlation IDs

## Security

**Aggregate logs, detect attacks, compliance**

- **[Security Log Aggregation](security/security-aggregation.md)** - Normalize firewall, IDS, and authentication logs for attack correlation

## Data

**Migrations, transformations, data quality**

- **[Database Migration Validation](data/migration-validation.md)** - Verify database migrations (MySQL to PostgreSQL) preserve application behavior

## See Also

- **[Common Patterns](../guides/common-patterns.md)** - Reusable pattern techniques
- **[Rules Documentation](../features/rules/rules.md)** - Complete pattern syntax reference
- **[Troubleshooting](../guides/troubleshooting.md)** - Debugging pattern matching issues
