# shinyjson
Shiny UI using vercel-labs/json-render

## Development

### Setup

```bash
# Install Python dependencies
uv sync --all-extras --all-groups

# Install JS dependencies
make js-setup

# Install pre-commit hooks
pre-commit install
```

### Common commands

```bash
# Build JS assets and copy to packages
make update-dist

# Run Python checks (formatting, tests, types for current Python only)
make py-check

# Run Python checks (formatting, tests, types across Python 3.10–3.14)
make py-check-tox

# Run R checks
make r-check

# Format Python code
make py-format
```

Run `make help` to see all available targets.
