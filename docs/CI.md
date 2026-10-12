# CI/CD Pipeline Documentation

This document describes the Continuous Integration and Continuous Deployment pipeline for YNAB Data Collector.

## Overview

The CI pipeline runs on every push to `main` and `develop` branches, and on all pull requests targeting these branches.

## Pipeline Jobs

### 1. Lint (`lint`)

**Purpose**: Ensure code quality and consistency

**Tools**:
- **Black**: Code formatting (line length: 127)
- **isort**: Import sorting (Black-compatible)
- **flake8**: Style and error checking (complexity: 10)
- **mypy**: Static type checking (strict mode)

**Runs on**: Python 3.12

### 2. Test (`test`)

**Purpose**: Run unit tests across Python versions

**Matrix**: Python 3.12

**Tools**:
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities

**Output**: Coverage reports uploaded to Codecov (on Python 3.12)

### 3. Coverage (`coverage`)

**Purpose**: Enforce minimum test coverage

**Threshold**: 95%

**Output**: HTML coverage report (artifact, 14-day retention)

### 4. Security (`security`)

**Purpose**: Scan for security vulnerabilities

**Tools**:
- **bandit**: Static security analysis (medium+ severity)
- **pip-audit**: Dependency vulnerability scanning

### 5. Validate Config (`validate-config`)

**Purpose**: Validate configuration files

**Checks**:
- YAML syntax validation
- Python syntax validation

### 6. Build Status (`build-status`)

**Purpose**: Aggregate all job results

**Depends on**: lint, test, coverage, security, validate-config

## Secret Scanning (gitleaks)

`.github/workflows/gitleaks.yml` runs the standardized `Secret Scanning` job on
`[self-hosted, fargate]`. It downloads gitleaks 8.30.1 and verifies the pinned
Linux x64 archive SHA-256 before execution.

Pull requests scan `base.sha..head.sha`. Pushes and manual runs scan the event
commit's full reachable history. Both include first-parent merge patches;
sibling branch refs are outside the scan scope. The job validates the revisions
and complete Git traversal, then fails on scanner errors even if gitleaks
returns zero.

Reports use `--redact=100`. The job uploads redacted SARIF as an artifact and
attempts GitHub code scanning ingestion when supported. Findings fail the job;
real credentials require approved remediation. Any false-positive exclusion
must be verified, justified in its PR, and restricted to an exact fingerprint.

This workflow is byte-identical to the reviewed template in
[automation#1020](https://github.com/amendez13/automation/pull/1020), delivered
under [automation#376](https://github.com/amendez13/automation/issues/376).
After merge, confirm a green Secret Scanning run on main. Roll back through a
reviewed revert PR if needed.

## Running Locally

### Pre-commit Hooks

Install and run pre-commit hooks locally:

```bash
# Install hooks
pre-commit install

# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
```

### Individual Checks

```bash
# Formatting
black --check --diff src/
isort --check-only --diff src/

# Linting
flake8 src/ --max-complexity=10 --max-line-length=127

# Type checking
mypy src/ --strict

# Tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=95

# Security
bandit -r src/ -ll
pip-audit --requirement requirements.txt
```

## Troubleshooting

### Common Issues

**Black/isort conflicts**:
- Run `black src/` then `isort src/`
- isort uses Black-compatible profile

**Coverage below threshold**:
- Check `htmlcov/index.html` for uncovered lines
- Add tests for uncovered code paths
- Use `# pragma: no cover` sparingly for untestable code

**Type errors**:
- Add type hints to function signatures
- Use `# type: ignore` sparingly with explanation

**Security warnings**:
- Use `# nosec` comment for false positives
- Document security decisions in code comments

## Configuration Files

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | Main CI workflow |
| `.github/workflows/gitleaks.yml` | Secret scanning (gitleaks, Fargate) |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `pyproject.toml` | Tool configurations |
| `.flake8` | flake8 settings |
| `.pylintrc` | pylint settings |
