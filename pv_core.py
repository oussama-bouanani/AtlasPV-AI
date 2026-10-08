"""Transparent rule-based PV monitoring calculations for the AtlasPV AI prototype.

Not a fault diagnosis, yield guarantee, or certified design tool.
"""
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ("timestamp", "irradiance_wm2", "module_temp_c", "power_kw")


@dataclass(frozen=True)
class PVConfig:
    capacity_kwp: float = 10.0
    performance_factor: float = 0.90
    temperature_coefficient: float = -0.004
    min_irradiance_wm2: float = 250.0
    deficit_threshold: float = 0.22
    minimum_consecutive_points: int = 3

    def validate(self) -> None:
        if not (0 < self.capacity_kwp <= 1_000_000):
            raise ValueError("La puissance installée doit être positive.")
        if not (0 < self.performance_factor <= 1):
            raise ValueError("Le facteur global doit être entre 0 et 1.")
        if not (-0.02 <= self.temperature_coefficient <= 0):
            raise ValueError("Le coefficient thermique doit être entre -0.02 et 0.")
        if not (0 <= self.min_irradiance_wm2 <= 1400):
            raise ValueError("Seuil d'irradiance invalide.")
        if not (0.01 <= self.deficit_threshold <= 0.95):
            raise ValueError("Seuil de baisse invalide.")
        if self.minimum_consecutive_points < 1:
            raise ValueError("Le nombre minimal de points doit être >= 1.")


def prepare_data(raw: pd.DataFrame, config: Optional[PVConfig] = None) -> pd.DataFrame:
    """Normalize data and flag sustained underperformance at sufficiently high irradiance.

    Assumes calibrated AC-power measurements and irradiance measured in panel plane;
    the expectation is a simple temperature-adjusted physical baseline, *not* ML.
    """
    cfg = config or PVConfig()
    cfg.validate()
    missing = [name for name in REQUIRED_COLUMNS if name not in raw.columns]
    if missing:
        raise ValueError("Colonnes manquantes : " + ", ".join(missing))
    df = raw.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for column in ("irradiance_wm2", "module_temp_c", "power_kw"):
        df[column] = pd.to_numeric(df[column], errors="coerce")
    if df[[*REQUIRED_COLUMNS]].isna().any().any():
        raise ValueError("Valeurs manquantes ou non valides dans les colonnes obligatoires.")
    if df.empty or len(df) < 3:
        raise ValueError("Il faut au moins 3 mesures valides.")
    if (df["irradiance_wm2"] < 0).any() or (df["irradiance_wm2"] > 1400).any():
        raise ValueError("L'irradiance doit être entre 0 et 1 400 W/m².")
    if (df["power_kw"] < 0).any():
        raise ValueError("La puissance mesurée ne peut pas être négative.")
    if ((df["module_temp_c"] < -30) | (df["module_temp_c"] > 110)).any():
        raise ValueError("La température des modules semble incorrecte.")
    df = df.sort_values("timestamp").reset_index(drop=True)
    if df["timestamp"].duplicated().any():
        raise ValueError("Les horodatages doivent être uniques.")

    gaps_hr = df["timestamp"].diff().dt.total_seconds().div(3600)
    if (gaps_hr.dropna() <= 0).any():
        raise ValueError("L'horodatage doit être croissant.")
    # Cap missing-data gaps: never assume the last power value persisted for hours.
    regular_gaps = gaps_hr.dropna()
    interval_h = float(regular_gaps.median())
    if not 0 < interval_h <= 1:
        raise ValueError("Fréquence d'échantillonnage requise : au moins une mesure/heure.")
    df["duration_h"] = gaps_hr.fillna(interval_h).clip(upper=interval_h * 1.5)
    df.loc[0, "duration_h"] = interval_h

    irradiance = df["irradiance_wm2"]
    thermal_factor = (1 + cfg.temperature_coefficient * (df["module_temp_c"] - 25)).clip(lower=0)
    df["expected_kw"] = (cfg.capacity_kwp * (irradiance / 1000) * thermal_factor * cfg.performance_factor).clip(lower=0)
    df["performance_ratio"] = np.where(df["expected_kw"] > 0.1,
                                       df["power_kw"] / df["expected_kw"], np.nan)
    df["deficit_pct"] = np.where(df["expected_kw"] > 0.1,
                                 100 * (1 - df["power_kw"] / df["expected_kw"]), np.nan)
    under = ((irradiance >= cfg.min_irradiance_wm2)
             & (df["expected_kw"] > 0.1)
             & (df["performance_ratio"] < (1 - cfg.deficit_threshold)))

    # A gap above 1.5 nominal intervals splits the sequence; avoid connecting separate days.
    segmented = (under != under.shift(fill_value=False)) | (gaps_hr > interval_h * 1.5).fillna(False)
    group_id = segmented.cumsum()
    group_counts = under.groupby(group_id).transform("sum")
    df["is_anomaly"] = under & (group_counts >= cfg.minimum_consecutive_points)
    df["measured_kwh"] = df["power_kw"] * df["duration_h"]
    df["expected_kwh"] = df["expected_kw"] * df["duration_h"]
    # An estimate, not a measured financial loss or a yield guarantee.
    df["estimated_gap_kwh"] = (df["expected_kw"] - df["power_kw"]).clip(lower=0) * df["duration_h"]
    return df


def summarize(df: pd.DataFrame) -> dict:
    actual = float(df["measured_kwh"].sum())
    expected = float(df["expected_kwh"].sum())
    return {
        "measured_kwh": actual,
        "expected_kwh": expected,
        "ratio_pct": round(100 * actual / expected, 1) if expected > 0 else 0.0,
        "estimated_gap_kwh": float(df.loc[df["is_anomaly"], "estimated_gap_kwh"].sum()),
        "anomaly_points": int(df["is_anomaly"].sum()),
        "samples": len(df),
    }


def create_alerts(df: pd.DataFrame) -> pd.DataFrame:
    """Find contiguous alert episodes, without asserting a certain root cause."""
    flagged = df[df["is_anomaly"]].copy()
    output_cols = ["Début", "Fin", "Priorité", "Baisse moyenne (%)", "Énergie non produite estimée (kWh)", "Piste de vérification"]
    if flagged.empty:
        return pd.DataFrame(columns=output_cols)
    typical_gap = df["timestamp"].diff().dropna().median()
    new_run = (flagged.index.to_series().diff().fillna(1).ne(1)
               | flagged["timestamp"].diff().gt(typical_gap * 1.5).fillna(False))
    rows = []
    for _, segment in flagged.groupby(new_run.cumsum()):
        ratio = float(segment["performance_ratio"].median())
        severity = "Critique" if ratio < 0.25 else "À vérifier"
        suggestion = (
            "Contrôler onduleur, alimentation AC, protections et acquisition de données"
            if severity == "Critique" else
            "Vérifier ombrage, salissures, connexions et capteur d'irradiance"
        )
        rows.append({
            "Début": segment["timestamp"].iloc[0],
            "Fin": segment["timestamp"].iloc[-1],
            "Priorité": severity,
            "Baisse moyenne (%)": round(float(segment["deficit_pct"].mean()), 1),
            "Énergie non produite estimée (kWh)": round(float(segment["estimated_gap_kwh"].sum()), 2),
            "Piste de vérification": suggestion,
        })
    return pd.DataFrame(rows, columns=output_cols)


def make_demo_data(days: int = 7, capacity_kwp: float = 10.0, seed: int = 23) -> pd.DataFrame:
    """Reproducible, explicitly *synthetic* measurements for a demo, not field data."""
    if not (1 <= days <= 60):
        raise ValueError("Nombre de jours hors limite (1 à 60).")
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2026-06-01", periods=days * 96, freq="15min")
    hour = dates.hour.to_numpy() + dates.minute.to_numpy() / 60
    sun = np.clip(np.sin(np.pi * (hour - 6) / 12), 0, None)
    cloud = rng.uniform(0.92, 1.02, size=len(dates))
    irradiance = np.clip(950 * (sun ** 1.3) * cloud, 0, 1200)
    ambient = 24 + 7 * sun + rng.normal(0, 0.5, len(dates))
    module_temp = ambient + irradiance * 0.025
    expected = (capacity_kwp * irradiance / 1000
                * (1 - 0.004 * (module_temp - 25)) * 0.90)
    measured = expected * rng.normal(0.985, 0.025, len(dates))
    scenario = np.full(len(dates), "Fonctionnement normal", dtype=object)
    # Synthetic example: intermittent afternoon shading / dirt on day 4.
    if days >= 4:
        m = (dates.day == 4) & (hour >= 11) & (hour < 15)
        measured[m] *= 0.65
        scenario[m] = "Déficit simulé (ombrage/salissure)"
    # Synthetic example: severe loss on day 6.
    if days >= 6:
        m = (dates.day == 6) & (hour >= 10) & (hour < 13)
        measured[m] *= 0.12
        scenario[m] = "Déficit simulé (type onduleur)"
    return pd.DataFrame({
        "timestamp": dates,
        "irradiance_wm2": np.round(irradiance, 1),
        "module_temp_c": np.round(module_temp, 1),
        "power_kw": np.round(np.clip(measured, 0, None), 3),
        "ambient_temp_c": np.round(ambient, 1),
        "scenario_demo": scenario,
    })
