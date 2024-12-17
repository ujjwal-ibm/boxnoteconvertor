# Contributing to BoxToDocx

Thank you for your interest in contributing to BoxToDocx! This document provides guidelines for contributing.

## Development Setup

1. Clone the repository:
   ```bash
   git clone git@github.com:ujjwal-ibm/boxtodocx.git
   cd boxtodocx
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip3 install -r requirements-dev.txt
   ```

4. Install the package in editable mode:
   ```bash
   pip3 install -e .
   ```

## Core Dependencies

- python-docx>=0.8.11
- beautifulsoup4>=4.9.3
- click>=8.0.0
- requests>=2.25.1
- colorlog>=6.7.0
- selenium>=4.0.0
- Pillow>=10.0.0
- yattag>=1.16.0

## Code Style

- Use Black for code formatting
- Follow PEP 8 guidelines
- Add type hints to all new code
- Write docstrings for modules, classes, and functions

## Pull Request Process

1. Create a new branch for your feature/fix
2. Write tests for new functionality
3. Update documentation as needed
4. Ensure all tests pass
5. Submit a pull request with a clear description of changes

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
