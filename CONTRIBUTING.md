# Contributing

This is an evaluation case study, not a production outreach service. Contributions are
welcome when they improve reproducibility, evidence quality, testing, or documentation.

## Local setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-dev.txt
```

Run the quality gate:

```powershell
python -m ruff check .
python -m unittest discover -s tests -v
python -m ldlatte_agent.cli --input examples/bloggers-demo.xlsx `
  --output results/smoke.json
```

## Pull requests

- Start from an issue or a narrowly described problem.
- Use an `agent/<short-description>` branch.
- Keep demo mode deterministic and key-free.
- Add or update tests when behavior changes.
- Explain data provenance and privacy impact.
- Open a draft PR until all checks pass.

Never include employer source files, credentials, raw contacts, browser profiles, or
derived private seed annotations. See `AGENTS.md` for the complete data boundary.
