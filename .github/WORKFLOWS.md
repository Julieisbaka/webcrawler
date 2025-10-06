# GitHub Actions Workflows Guide

This document explains the GitHub Actions workflows configured for this project.

## CI Workflow

**File**: `.github/workflows/ci.yml`

### Trigger Conditions
- Push to `master` or `main` branches
- Pull requests targeting `master` or `main` branches

### What it Does
1. **Multi-version Testing**: Tests the code across Python 3.8, 3.9, 3.10, 3.11, and 3.12
2. **Test Execution**: Runs pytest with coverage reporting
3. **Code Quality Checks**:
   - **Black**: Validates code formatting
   - **Isort**: Validates import sorting
   - **Pylint**: Performs static code analysis (non-blocking)
   - **Flake8**: Additional style checks (non-blocking)

### Local Testing

Before pushing, you can run the same checks locally:

```bash
# Install dev dependencies
pip install -e .[dev]

# Run tests with coverage
python -m pytest tests/ -v --cov=webcrawler --cov-report=term-missing

# Check formatting
python -m black --check webcrawler
python -m isort --check-only --profile black webcrawler

# Run linters
python -m pylint webcrawler --max-line-length=88 --disable=C0114,C0115,C0116,R0913,R0902,R0914,W0212
python -m flake8 webcrawler --max-line-length=88 --extend-ignore=E203,W503
```

### Fixing Issues

If the CI workflow fails:

```bash
# Auto-fix formatting
python -m black webcrawler
python -m isort --profile black webcrawler

# Check what pylint/flake8 are complaining about
python -m pylint webcrawler
python -m flake8 webcrawler --max-line-length=88
```

## PyPI Publish Workflow

**File**: `.github/workflows/publish.yml`

### Trigger Conditions
- **Automatic**: When a new GitHub release is published
- **Manual**: Via workflow_dispatch (for testing on Test PyPI)

### What it Does
1. Builds the Python package using `python -m build`
2. Validates the distribution with `twine check`
3. Publishes to PyPI (on release) or Test PyPI (on manual trigger)

### Prerequisites

Before using this workflow, you need to set up API tokens:

1. **For PyPI**: 
   - Create an API token at https://pypi.org/manage/account/token/
   - Add it to GitHub Secrets as `PYPI_API_TOKEN`

2. **For Test PyPI** (optional):
   - Create an API token at https://test.pypi.org/manage/account/token/
   - Add it to GitHub Secrets as `TEST_PYPI_API_TOKEN`

### Publishing a New Version

1. **Update Version Numbers**:
   - Edit `setup.py`: Update the `version` parameter
   - Edit `pyproject.toml`: Update the `version` field

2. **Create a Git Tag**:
   ```bash
   git tag -a v0.0.2 -m "Release version 0.0.2"
   git push origin v0.0.2
   ```

3. **Create a GitHub Release**:
   - Go to your repository on GitHub
   - Click "Releases" → "Create a new release"
   - Choose the tag you just created
   - Add release notes
   - Publish the release

4. **Automatic Publishing**:
   - The workflow will automatically trigger
   - It will build and publish to PyPI
   - Check the Actions tab to monitor progress

### Manual Testing (Test PyPI)

To test the publishing process without releasing to production PyPI:

1. Go to the "Actions" tab in your repository
2. Select "Publish to PyPI" workflow
3. Click "Run workflow"
4. Select the branch to test from
5. Click "Run workflow"

This will publish to Test PyPI (if the token is configured).

### Testing the Published Package

After publishing to Test PyPI:

```bash
# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ webcrawler

# Test the package
webcrawler --help
```

After publishing to PyPI:

```bash
pip install webcrawler
webcrawler --help
```

## Troubleshooting

### CI Workflow Issues

**Problem**: Tests fail in CI but pass locally
- Ensure you're using the correct Python version
- Check if there are environment-specific issues
- Review the full CI logs in the Actions tab

**Problem**: Black/Isort checks fail
- Run `black webcrawler` and `isort --profile black webcrawler` locally
- Commit the formatting changes

**Problem**: Pylint warnings
- These are non-blocking but should be addressed
- Review the specific warnings and fix code issues

### Publish Workflow Issues

**Problem**: Authentication errors
- Verify API tokens are correctly set in GitHub Secrets
- Ensure token names match exactly: `PYPI_API_TOKEN` and `TEST_PYPI_API_TOKEN`

**Problem**: Build fails
- Ensure `setup.py` and `pyproject.toml` are valid
- Test the build locally: `python -m build`

**Problem**: Version conflicts
- Ensure you've bumped the version number
- Check that the version doesn't already exist on PyPI

## Best Practices

1. **Always run tests locally** before pushing
2. **Use feature branches** for development
3. **Keep the main branch stable** - it triggers CI on every push
4. **Test on Test PyPI first** before releasing to production PyPI
5. **Write meaningful commit messages** for better CI logs
6. **Keep dependencies up to date** (Dependabot is configured)

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyPI Publishing Guide](https://packaging.python.org/tutorials/packaging-projects/)
- [Black Documentation](https://black.readthedocs.io/)
- [Isort Documentation](https://pycqa.github.io/isort/)
- [Pylint Documentation](https://pylint.pycqa.org/)
