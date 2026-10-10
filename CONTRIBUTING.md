# Contributing to AtlasPV AI

Thanks for helping improve transparent PV monitoring tools.

## Before contributing

1. Open an issue to describe the bug, proposal, or missing test. Never share credentials, private customer datasets, or sensitive PV plant details in public issues.
2. Please do not present synthetic demonstration signals as observations from a real PV plant.
3. For security-related concerns, use the private route described in `SECURITY.md`.

## Development

```bash
python -m venv .venv
# Activate .venv for your operating system
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
streamlit run app.py
```

- Keep physics and alert calculations in `pv_core.py`; keep UI specifics in `app.py`.
- Add a test for any rule/validation change.
- Prefer deterministic synthetic fixtures; real site data should not be published without explicit permission and sanitization.
- Document changed thresholds, units, and limitations.
- Explain what you tested and what remains unverified in your PR description.

## Pull request checklist

- [ ] Clear problem statement and scope
- [ ] Passing local unit tests
- [ ] Appropriate test additions for changed behavior
- [ ] Updated documentation for changed settings, data fields, or formulas
- [ ] No secrets, personal information or confidential field data

The maintainer may need time to review contributions; no response-time guarantee is offered. Contributions are accepted under the project's [MIT License](LICENSE). By submitting a contribution, you confirm that you have the right to share it under these terms.