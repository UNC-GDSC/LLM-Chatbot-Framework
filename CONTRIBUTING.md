# Contributing to LLM Chatbot Framework

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive criticism
- Help each other learn and grow

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/yourusername/LLM-Chatbot-Framework.git
cd LLM-Chatbot-Framework
```

### 2. Set Up Development Environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

## Development Guidelines

### Code Style

We follow PEP 8 with these tools:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run formatters:
```bash
black app/ tests/
isort app/ tests/
flake8 app/ tests/
mypy app/
```

### Type Hints

Always use type hints:

```python
def process_message(user_id: str, message: str) -> dict:
    """Process a chat message."""
    pass
```

### Documentation

- Add docstrings to all functions, classes, and modules
- Use Google-style docstrings
- Update README.md for new features
- Add examples to EXAMPLES.md

Example docstring:
```python
def create_user(email: str, username: str, password: str) -> User:
    """Create a new user account.

    Args:
        email: User's email address
        username: Unique username
        password: Plain text password (will be hashed)

    Returns:
        Created User object

    Raises:
        ValueError: If username already exists
    """
    pass
```

### Testing

- Write tests for all new features
- Maintain test coverage above 80%
- Use pytest for testing

Run tests:
```bash
pytest
pytest --cov=app tests/  # With coverage
```

### Commit Messages

Use conventional commits:

```
type(scope): subject

body

footer
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance

Examples:
```
feat(chat): add streaming response support

Implement WebSocket-based streaming for real-time chat responses.
Includes connection management and error handling.

Closes #123
```

```
fix(auth): resolve token expiration bug

Fixed issue where tokens were expiring prematurely due to
incorrect timezone handling.
```

## Pull Request Process

### 1. Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Added tests for new features
- [ ] Updated documentation
- [ ] No merge conflicts

### 2. Submit PR

1. Push your branch
2. Create pull request on GitHub
3. Fill out PR template
4. Link related issues

### 3. PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### 4. Review Process

- Maintainers will review within 3-5 days
- Address review comments
- Keep PR updated with main branch

## Feature Requests

Create an issue with:
- Clear description
- Use case
- Expected behavior
- Alternative solutions considered

## Bug Reports

Include:
- Description
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details
- Screenshots (if applicable)

Template:
```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
1. Step 1
2. Step 2
3. ...

**Expected behavior**
What should happen

**Actual behavior**
What actually happens

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.10]
- Package version: [e.g., 1.0.0]

**Additional context**
Any other relevant information
```

## Project Structure

```
app/
├── api/              # API endpoints
│   └── v1/
├── core/             # Core configuration
├── models/           # Database models
├── schemas/          # Pydantic schemas
├── services/         # Business logic
├── middleware/       # Custom middleware
└── utils/            # Utilities

tests/                # Test suite
docs/                 # Documentation
```

## Adding New Features

### 1. LLM Provider

To add a new LLM provider:

1. Update `app/services/llm_service.py`
2. Add provider initialization method
3. Handle provider-specific configuration
4. Add tests
5. Update documentation

### 2. API Endpoint

1. Create route in appropriate file
2. Define Pydantic schemas
3. Implement service logic
4. Add authentication if needed
5. Write tests
6. Update OpenAPI docs

### 3. Database Model

1. Create model in `app/models/`
2. Add relationships
3. Create migration (if using Alembic)
4. Update schemas
5. Add service methods
6. Write tests

## Development Tools

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pre-commit install
```

### Running Locally

```bash
uvicorn app.main:app --reload
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_auth.py

# With coverage
pytest --cov=app --cov-report=html

# Watch mode
pytest-watch
```

### Database Migrations

If using Alembic:
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Questions?

- Open an issue for questions
- Check existing issues and PRs
- Join our community discussions

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

## Recognition

Contributors will be added to CONTRIBUTORS.md.

Thank you for contributing! 🎉
