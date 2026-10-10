# Security policy — early-stage prototype

This project is a research/demo prototype and has not undergone an independent security audit. It is **not approved** for production, remote control, energy trading, or safety-critical operations.

## How to report vulnerabilities

Please **do not post** API keys, passwords, private CSVs or exploit details in public issues. If GitHub private vulnerability reporting is enabled for this repository, use **Security → Report a vulnerability**. Otherwise contact the repository owner privately using contact details *they have explicitly published* on their GitHub profile.

There is no guaranteed security response time or supported-release policy at this stage.

## Data handling

- Data uploaded through the hosted Streamlit UI is handled by the hosting service.
- The optional Anthropic integration sends the generated report summary only when the user presses the request button.
- Store API keys in environment variables or an approved secrets facility, not in code or commits.
- Do not use this app with confidential plant or personally identifying data without appropriate authorization and deployment controls.
- Do not interpret alerts as verified causes of an electrical fault.