# Security policy

## Supported version

Only the latest commit on `main` is maintained.

## Reporting

Please do not open a public issue for leaked credentials, personal data, or a vulnerability
that could enable abusive outreach. Report it privately to the repository owner through
the contact method on the GitHub profile.

Include the affected commit, a concise reproduction, impact, and suggested mitigation.
Do not include real secrets or unnecessary personal data.

## Security boundaries

- Demo mode must not make paid or mutating external calls.
- Outreach is never sent automatically.
- Secrets are loaded only from local environment variables.
- Employer inputs and their derived seed annotations are excluded from Git.
- Public candidate evidence is a dated research snapshot, not a live authorization signal.
