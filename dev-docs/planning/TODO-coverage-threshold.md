# TODO: Increase coverage threshold

The test coverage threshold is currently set to 30% in `.github/workflows/test.yml`.

As the project matures and test coverage increases, this should be raised progressively:
- Current: 30%
- Target: 85%

Update the threshold in: `.github/workflows/test.yml` line 41:
```yaml
pytest --cov=src/patterndb_yaml --cov-report=xml --cov-report=term --cov-fail-under=30
```

Increment by 5-10% each time significant tests are added.
