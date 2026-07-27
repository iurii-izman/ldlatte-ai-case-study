# ADR 0001: Public data boundary

- Status: accepted
- Date: 2026-07-27

## Context

The prototype was validated against an employer-provided workbook. A public portfolio
repository must remain runnable without publishing that source or a reversible derivative
of its seed list.

## Decision

The repository tracks synthetic inputs under `examples/`. Employer source files remain
local and are ignored. Derived seed annotations live under `data/private/` and are also
ignored. Approved research outputs, prompts, aggregate findings, and candidate snapshots
may be public when they are required to demonstrate the solution and contain source links.

The application defaults to synthetic data. Private input and annotations must be passed
explicitly.

## Consequences

- A fresh clone runs without secrets or private files.
- Public CI validates the real loading and ranking path with fictional seed profiles.
- Exact private-run counts in the report are evidence from the completed evaluation run,
  not data reconstructed from the public fixture.
- Maintainers must review new artifacts for provenance before staging.
