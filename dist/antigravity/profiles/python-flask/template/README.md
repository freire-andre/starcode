# {{name}}

{{description}}

## Gates

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src`
- `uv run pytest -v`

Os testes marcados `integration` ficam fora do `pytest` padrão; rodam com `-m integration`.
