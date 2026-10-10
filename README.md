# ☀️ AtlasPV AI — Transparent PV Monitoring & Maintenance Support

**AtlasPV AI** is an early-stage, Python-based photovoltaic monitoring prototype built with Streamlit. It compares imported AC power measurements with a simple irradiance-and-temperature baseline, highlights sustained underperformance, and produces maintenance summaries.

**[Launch live demo](https://atlaspv-ai-oussama.streamlit.app/)** · **[Read the technical architecture](docs/ARCHITECTURE.md)** · **[Understand CSV inputs](docs/DATA_SCHEMA.md)**

> **Project status — prototype, not a certified monitoring product.** The built-in demonstration dataset is **100% synthetic**. The current anomaly detection relies on engineering rules, **not a trained AI/ML model**. There are no claims of real-world performance validation, live inverter integration, customers, or industrial certification. Claude reporting is optional and requires the user's own API access.

## What it does

| Feature | Current implementation |
| --- | --- |
| Interactive monitoring | Streamlit dashboard with Plotly power and energy charts |
| CSV analysis | Reads timestamp, plane-of-array irradiance, module temperature and AC power |
| Explainable baseline | Calculates a simple expected PV output from irradiance and temperature |
| Alerts | Flags a sustained deficit for at least three eligible measurements |
| Maintenance summary | Downloadable local Markdown and CSV exports |
| Optional LLM summary | Claude API can rewrite the aggregated report; no trained fault model |
| Demonstration | Reproducible 7-day synthetic dataset with two injected loss episodes |

## Live demo

Open https://atlaspv-ai-oussama.streamlit.app/ (a sleeping Streamlit Community Cloud app may take a moment to wake). The dashboard has **Tableau de bord**, **Historique**, **Alertes**, and **Rapport et Claude** tabs. Select **Démonstration simulée** to use example data, or upload a compatible CSV. The sidebar lets you adjust capacity, global performance factor, deficit threshold, and minimum irradiance.

## Quick start

Requires **Python 3.10+**. From this repository directory:

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

### Run tests

```bash
python -m unittest discover -s tests -v
```

CI runs the same tests on push and pull requests using GitHub Actions. It does not currently include end-to-end browser tests or hardware-in-the-loop validation.

## Sample data

The built-in synthetic generator produces reproducible example data. Required headers:

```csv
timestamp,irradiance_wm2,module_temp_c,power_kw
2026-06-01 11:00:00,820,48.0,6.05
```

- `timestamp`: timestamp of each measurement (consistent time zone / local time interpretation).
- `irradiance_wm2`: **plane-of-array** irradiance, W/m².
- `module_temp_c`: **PV module** temperature in °C, not ambient temperature.
- `power_kw`: measured **AC active power** in kW, not accumulated energy.

Details, data quality constraints, and file format: [docs/DATA_SCHEMA.md](docs/DATA_SCHEMA.md).

## Transparent detection formula

```text
P_expected = P_installed(kWp) × irradiance_POA / 1000
             × [1 + gamma × (module_temperature − 25°C)]
             × global_performance_factor
```

Default parameters: `gamma = -0.004 /°C`, `global_performance_factor = 0.90`, minimum irradiance `250 W/m²`, deficit threshold `22%`, at least `3` consecutive eligible samples. These are **configurable engineering assumptions**, not calibrated fault detection. Integration uses sample intervals with a cap for missing-data gaps; results are estimated and sensitive to sampling quality.

A positive alert does **not** identify a failure cause. Professionals must confirm findings on site, and electrical inspections require qualified staff.

## Optional Claude reports

Without external API access, the local maintenance report works at no API cost. Claude reporting is optional and may incur costs. Users provide their own Anthropic API key and model ID. The app sends a structured *summary report* when explicitly requested; it does not send full raw measurements through the built-in integration. User-supplied files are processed in the Streamlit hosting environment. Do not upload confidential or personally identifying data to a public deployment.

Never commit secrets. See `.env.example` and [SECURITY.md](SECURITY.md). No affiliation with or endorsement by Anthropic or OpenAI is implied.

## Structure

```text
AtlasPV_AI/
├── app.py                         # Streamlit UI
├── pv_core.py                     # Physics baseline and explainable alerts
├── requirements.txt
├── tests/test_pv_core.py
├── docs/ARCHITECTURE.md
├── docs/DATA_SCHEMA.md
├── docs/ROADMAP.md
├── .github/workflows/python-tests.yml
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
├── LICENSE                       # MIT open-source license
└── .env.example
```

## Contributing, security, and roadmap

Contributions are welcome; start with [CONTRIBUTING.md](CONTRIBUTING.md) and the [roadmap](docs/ROADMAP.md). For sensitive vulnerabilities, see [SECURITY.md](SECURITY.md). The project is maintained as an early-stage prototype; response-time and support guarantees are not offered.

## License

AtlasPV AI is released under the [MIT License](LICENSE). Copyright (c) 2026 Oussama Bouanani. You may use, modify, redistribute, or include the code in commercial projects provided you preserve the license and copyright notice. This is an early-stage prototype, offered without warranty.

## Project maintainer

Repository: [oussama-bouanani/atlaspv-ai](https://github.com/oussama-bouanani/atlaspv-ai). See GitHub commit history and issues for **verifiable** maintenance history; demo metrics and synthetic test output are not usage/adoption statistics.