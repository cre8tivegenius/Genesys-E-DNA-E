# Contributing to Genesys-E-DNA-E

Thank you for your interest in contributing to this AI Safety Governance Framework!

## Development Setup

### Prerequisites
- Python 3.12+
- pip/poetry for package management
- Git

### Local Installation

```bash
git clone https://github.com/cre8tivegenius/Genesys-E-DNA-E.git
cd Genesys-E-DNA-E

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Full test suite
pytest tests/ -v

# With coverage report
pytest tests/ --cov=src/bodhisattva --cov-report=html

# Specific test file
pytest tests/unit/test_invariant.py -v

# Run property-based tests (with Hypothesis)
pytest tests/property/ -v
```

### Code Quality

```bash
# Format code
ruff format src/ tests/

# Type checking
mypy src/

# Linting
ruff check src/ tests/
```

## Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Follow existing code style
   - Add tests for new functionality
   - Ensure all tests pass: `pytest tests/`

3. **Commit with clear messages:**
   ```bash
   git commit -m "Add descriptive commit message"
   ```

4. **Push and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Key Areas for Contribution

### Core Framework
- `src/bodhisattva/core/` - Invariant computation, gate logic
- Improvements to mathematical precision
- Performance optimization of index calculation

### Testing
- `tests/` - Unit, integration, and property-based tests
- Additional adversarial scenarios
- Edge case coverage

### Documentation
- Framework specification and examples
- API documentation
- Use case studies

### Features
- New compliance rules in `src/bodhisattva/regulatory/`
- Additional adversarial test scenarios
- Extended firmware constraint models

## Design Principles

1. **Invariant Integrity** - The Bodhisattva Index must remain mathematically sound
2. **Coupled Constraints** - Multiplicative coupling prevents single-axis exploits
3. **Transparency** - All decisions must be auditable with full reasoning
4. **Reversibility** - Decisions should enable course correction
5. **Empiricism** - Property-based testing validates all claims

## Testing Requirements

All contributions must:
- Pass all existing tests
- Include tests for new functionality (target >80% coverage)
- Validate against property-based tests
- Pass type checking (`mypy`)

## Commit Message Guidelines

```
[TYPE] Brief description (50 chars max)

More detailed explanation if needed. Reference issues:
Closes #123
Related to #456
```

Types: `feat`, `fix`, `test`, `docs`, `refactor`, `perf`

## Questions?

- Open an issue for bugs or features
- Check existing documentation in UNIFIED_FRAMEWORK_SUMMARY.md
- Review test examples for API usage

## License

By contributing, you agree your work is available under the same terms as this project.

---

Thank you for helping build ethical AI systems! 🙏
