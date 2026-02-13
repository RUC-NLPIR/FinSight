# Contributing to FinSight

Thank you for your interest in contributing to FinSight! This guide covers the development setup, testing, and PR workflow.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/RUC-NLPIR/FinSight.git
cd FinSight

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov hypothesis ruff
```

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_async_bridge.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing
```

## Code Style

- We use **ruff** for linting. Run `ruff check src/ tests/` before submitting.
- Follow existing code patterns — new tools should subclass `Tool` from `src/tools/base.py`.
- Use type hints for function signatures.
- Write docstrings for public methods.

## Adding a New Tool

1. Create your tool class in the appropriate directory under `src/tools/`.
2. Subclass `Tool` and implement `__init__`, `prepare_params`, and `api_function`.
3. `api_function` must return a `list[ToolResult]`.
4. The tool will be auto-discovered and registered by `_auto_register_tools()`.
5. Write tests in `tests/` — include both metadata and integration tests.

## Pull Request Guidelines

- One logical change per PR.
- Include tests for new functionality.
- Ensure all tests pass locally before submitting.
- Update documentation if adding new features.
- Reference relevant issues in the PR description.

## License

By contributing, you agree that your contributions will be licensed under the GPL-3.0 License.
