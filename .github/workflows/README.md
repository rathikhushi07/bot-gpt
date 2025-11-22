# GitHub Actions CI/CD

This directory contains GitHub Actions workflows for automated testing and code quality checks.

## Workflows

### `ci-cd.yml` - Main CI/CD Pipeline

**Triggers:**
- Push to `main`, `master`, or `develop` branches
- Pull requests to `main`, `master`, or `develop`

**Jobs:**

1. **Test** (Multi-Python Version)
   - Tests on Python 3.10, 3.11, 3.12
   - Runs linting (flake8)
   - Runs unit tests
   - Runs integration tests
   - Generates coverage reports
   - Uploads coverage to Codecov

2. **Code Quality**
   - Checks code formatting (Black)
   - Checks import sorting (isort)
   - Type checking (mypy)

3. **Security Scan**
   - Checks for known vulnerabilities (safety)
   - Security linting (Bandit)
   - Uploads results to GitHub Security

## Status Badge

Add this to your README.md:

```markdown
[![CI/CD](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci-cd.yml)
```

## Viewing Results

1. Go to your GitHub repository
2. Click on "Actions" tab
3. See all workflow runs and their status

## Local Testing

Run the same checks locally:

```bash
# Linting
pip install flake8
flake8 src/main/python/test_python_app

# Tests
pytest

# Code formatting
pip install black
black --check src/main/python/test_python_app

# Security
pip install safety bandit
safety check
bandit -r src/main/python/test_python_app
```

