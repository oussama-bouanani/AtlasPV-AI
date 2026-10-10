import unittest
import pandas as pd
from pv_core import PVConfig, make_demo_data, prepare_data, summarize, create_alerts

class TestPVMonitoring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = prepare_data(make_demo_data())

    def test_expected_energy(self):
        summary = summarize(self.df)
        self.assertGreater(summary['measured_kwh'], 50)
        self.assertGreater(summary['expected_kwh'], summary['measured_kwh'])

    def test_two_injected_alerts(self):
        alerts = create_alerts(self.df)
        self.assertEqual(len(alerts), 2)
        self.assertIn('Critique', set(alerts['Priorité']))

    def test_no_nighttime_alert(self):
        self.assertFalse(self.df.loc[self.df.irradiance_wm2 < 10, 'is_anomaly'].any())

    def test_missing_column(self):
        with self.assertRaisesRegex(ValueError, 'Colonnes manquantes'):
            prepare_data(pd.DataFrame({'timestamp': ['2026-06-01']}))

    def test_duplicate_timestamps(self):
        df = make_demo_data(days=1)
        df.loc[1, 'timestamp'] = df.loc[0, 'timestamp']
        with self.assertRaises(ValueError):
            prepare_data(df)

    def test_negative_power(self):
        df = make_demo_data(days=1)
        df.loc[2, 'power_kw'] = -1.0
        with self.assertRaises(ValueError):
            prepare_data(df)

    def test_infinite_power(self):
        df = make_demo_data(days=1)
        df.loc[2, 'power_kw'] = float('inf')
        with self.assertRaises(ValueError):
            prepare_data(df)

    def test_infinite_irradiance(self):
        df = make_demo_data(days=1)
        df.loc[2, 'irradiance_wm2'] = float('inf')
        with self.assertRaises(ValueError):
            prepare_data(df)

    def test_no_fault_day(self):
        self.assertEqual(len(create_alerts(prepare_data(make_demo_data(days=1)))), 0)

    def test_sampling_too_sparse(self):
        df = make_demo_data(days=1).iloc[::8]
        with self.assertRaises(ValueError):
            prepare_data(df)

    def test_custom_capacity(self):
        df = prepare_data(make_demo_data(days=1, capacity_kwp=5), PVConfig(capacity_kwp=5))
        self.assertGreater(df['expected_kw'].max(), 2)

    def test_alert_estimated_gap(self):
        stats = summarize(self.df)
        self.assertGreater(stats['estimated_gap_kwh'], 0)

if __name__ == '__main__':
    unittest.main()
