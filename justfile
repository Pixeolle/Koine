set windows-shell := ["powershell.exe", "-c"]
set shell := ["sh", "-c"]

# Format code using Ruff.
fmt:
 uv run ruff format .

# Lint code using Ruff without fixing it.
lint:
 uv run ruff check .

# Lint and fix code using Ruff.
lint-fix:
 uv run ruff check --fix .