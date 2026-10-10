# CSV schema

Required exact column names: `timestamp` (unique, parseable dates); `irradiance_wm2` (W/m², 0 to 1400); `module_temp_c` (module °C, -30 to 110); `power_kw` (measured AC kW, nonnegative). Numeric values must be finite. Three or more samples, median sample interval at most one hour. Example:

```csv
timestamp,irradiance_wm2,module_temp_c,power_kw
2026-06-01 11:00:00,820,48,6.05
2026-06-01 11:15:00,840,49,6.10
2026-06-01 11:30:00,790,47,5.90
```

Use consistent timestamps. Energy from irregular measurements is an estimate. Do not upload confidential data to the public demonstration.
