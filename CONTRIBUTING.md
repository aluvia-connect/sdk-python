# Contributing to Aluvia Python SDK

Thank you for your interest in contributing to the Aluvia Python SDK!

## Development Setup

1. Clone the repository:

```bash
git clone https://github.com/aluvia-connect/sdk-python.git
cd sdk-python
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:

```bash
pip install -e ".[dev]"
```

## Running Tests

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=aluvia_sdk --cov-report=html
```

## Code Quality

Format code with black:

```bash
black aluvia_sdk tests examples
```

Sort imports with isort:

```bash
isort aluvia_sdk tests examples
```

Type check with mypy:

```bash
mypy aluvia_sdk
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linters
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Code Style

- Follow PEP 8
- Use type hints for all functions and methods
- Write docstrings for public APIs
- Keep line length to 100 characters
- Use async/await for asynchronous code

## Testing Guidelines

- Write tests for new features
- Maintain test coverage above 80%
- Use descriptive test names
- Mock external API calls in tests

## Questions?

Feel free to open an issue for any questions or concerns.
