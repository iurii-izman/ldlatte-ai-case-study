# Synthetic examples

`bloggers-demo.xlsx` and `seed_annotations.json` are fictional inputs created solely for a
safe public demo. They contain no rows copied from the employer workbook and no real
profiles.

Run:

```powershell
python -m ldlatte_agent.cli --input examples/bloggers-demo.xlsx `
  --output results/demo.json
```

For a private run, provide your own XLSX and matching annotations explicitly:

```powershell
python -m ldlatte_agent.cli --input "docs\Блогеры.xlsx" `
  --annotations "data\private\seed_annotations.json" `
  --output "results\private.json"
```
