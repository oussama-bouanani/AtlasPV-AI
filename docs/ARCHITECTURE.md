# Architecture

`pv_core.py` validates measurements and computes an irradiance-and-temperature baseline; `app.py` renders the Streamlit interface. The pipeline is CSV or seeded synthetic data → validation → expected AC power → sustained-deficit rules → estimated energy and maintenance alerts → optional user-triggered Claude summary.

Formula: `P_expected = max(0, capacity_kWp * irradiance_Wm2/1000 * max(0, 1 + gamma*(module_temperature_C - 25)) * performance_factor)`.

This is a simplified physical model, NOT trained machine learning, a diagnostic guarantee, or a calibrated plant digital twin. Irradiance must be plane-of-array, and the temperature is PV module temperature. Alert episodes show inspection priorities rather than verified causes. Uploaded CSVs are processed on the deployed Streamlit host. The optional LLM request sends a report summary when activated.
