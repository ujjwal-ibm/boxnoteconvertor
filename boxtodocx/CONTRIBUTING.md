# Contributing to BoxNote to DOCX Converter

Thank you for your interest in contributing to BoxNote to DOCX Converter! This document provides guidelines and instructions for contributing.

## Development Setup

1. Clone the repository:
   ```bash
   git clone git@github.com:ujjwal-ibm/boxnoteconvertor.git
   cd boxnoteconvertor/boxnotetodocx
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip3 install -r requirements-dev.txt
   ```

4. Install the package in editable mode:
   ```bash
   pip3 install -e .
   ```


## Core Dependencies

| Library | Version |
|---------|---------|
| python-docx | >=0.8.11 |
| beautifulsoup4 | >=4.9.3 |
| click | >=8.0.0 |
| requests | >=2.25.1 |
| colorlog | >=6.7.0 |


## Testing

Run tests with pytest:
```bash
pytest
```

For test coverage:
```bash
pytest --cov=boxnotetodocx
```

## Pull Request Process

1. Create a new branch for your feature/fix
2. Write tests for new functionality
3. Update documentation as needed
4. Ensure all tests pass and code style checks pass
5. Submit a pull request with a clear description of changes


## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms.