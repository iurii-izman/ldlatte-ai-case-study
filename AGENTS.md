# AGENTS.md

## Purpose

This repository is a public, evaluation-oriented AI case study for LD LATTE. Agents may
improve the code, tests, documentation, and synthetic examples, but must preserve the
privacy boundary between public artifacts and employer-provided source data.

## Non-negotiable data rules

- Never read, print, stage, commit, upload, or summarize values from `.env`.
- Never commit files from `private/`, `data/private/`, or employer source files under
  `docs/*.xlsx`, `docs/*.xls`, `docs/*.csv`, and `docs/*.pdf`.
- Treat derived seed annotations, contact exports, raw scraping results, and browser
  profiles as private unless they are explicitly synthetic or already approved outputs.
- Public tests and demos must use `examples/bloggers-demo.xlsx` and
  `examples/seed_annotations.json`.
- Before every push, run the secret scan and inspect `git diff --cached`.

## Product guardrails

- Do not auto-send collaboration offers. A human approval gate is required.
- Missing metrics are unknown, not zero.
- Candidate claims need a URL, observation date, and confidence level.
- Do not silently merge conflicting metrics from different sources.
- Do not present public-directory data as an official platform API response.
- Legal review is required before production outreach, ad labelling, or personal-data
  processing.

## Agent responsibilities

### Maintainer agent

Owns repository structure, dependency hygiene, releases, and GitHub settings. It keeps CI
green and does not bypass branch protection.

### Data steward agent

Classifies inputs as private, synthetic, or approved public output. It blocks publication
when provenance is unclear and maintains the allowlist in `.gitignore`.

### Pipeline agent

Changes ingestion, portraiting, discovery, scoring, and offer generation. It preserves
deterministic demo mode and adds tests for every behavioral change.

### Research agent

Collects only publicly accessible evidence, records source URLs and observation dates, and
flags uncertainty. It never treats a search snippet as definitive proof.

### Review agent

Checks privacy, reproducibility, factual support, failure behavior, and documentation. It
must reject any change that enables automatic outreach without explicit human approval.

One person or coding agent may perform several roles, but the review checklist still
applies.

## Repository map

- `ldlatte_agent/` — application and pipeline code.
- `tests/` — deterministic unit and integration tests.
- `examples/` — synthetic, safe-to-publish demo inputs.
- `data/candidates.json` — approved reproducible candidate snapshot.
- `prompts/` — versioned prompt contracts.
- `docs/` — assignment navigator, reports, architecture, and decisions.
- `.github/` — CI, maintenance automation, ownership, and contribution templates.

## Working agreement

1. Create a branch named `agent/<short-description>` for changes after the initial
   repository bootstrap.
2. Keep changes narrowly scoped; do not rewrite unrelated user work.
3. Update tests and documentation together with behavior.
4. Run:

   ```powershell
   python -m ruff check .
   python -m unittest discover -s tests -v
   python -m ldlatte_agent.cli --input examples/bloggers-demo.xlsx `
     --output results/smoke.json
   ```

5. Inspect staged files and scan for secret-like values before committing.
6. Use a draft pull request unless the owner explicitly requests otherwise.

## Definition of done

- Public clone runs without private files or API keys.
- Demo mode makes no paid or mutating external calls.
- Tests and lint pass.
- `python scripts/evaluate_demo.py` passes with exit code 0.
- New claims are sourced and uncertainty is visible.
- README and relevant docs match actual behavior.
- No ignored or private data is staged.
