# Contributing to DevPulse

Thank you for considering contributing to DevPulse! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/devpulse/devpulse.git
   cd devpulse
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

4. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Running Tests

Run the tests using the provided script:

```bash
python run_tests.py
```

Or use pytest directly:

```bash
pytest
```

## Code Style

We follow PEP 8 style guidelines. Use tools like flake8 and black to ensure your code meets these standards:

```bash
flake8 src tests
black src tests
```

## Pull Request Process

1. Fork the repository and create a new branch for your feature or bug fix.
2. Write tests for your changes.
3. Ensure all tests pass.
4. Update documentation if necessary.
5. Submit a pull request with a clear description of the changes.

## Feature Requests and Bug Reports

Please use the GitHub issue tracker to submit feature requests and bug reports.

## License

By contributing to DevPulse, you agree that your contributions will be licensed under the project's license.