import unittest

from ruffier.domain import (
    PulseMeasurements,
    assess,
    calculate_index,
    classify_index,
    low_level_threshold,
    validate_age,
)


class PulseMeasurementsTests(unittest.TestCase):
    def test_rejects_non_integer_values(self) -> None:
        with self.assertRaises(TypeError):
            PulseMeasurements(rest=20.5, after_load=30, after_recovery=25)  # type: ignore[arg-type]

    def test_rejects_values_outside_measurement_range(self) -> None:
        with self.assertRaises(ValueError):
            PulseMeasurements(rest=0, after_load=30, after_recovery=25)
        with self.assertRaises(ValueError):
            PulseMeasurements(rest=20, after_load=101, after_recovery=25)


class RuffierCalculationTests(unittest.TestCase):
    def test_calculates_index_from_15_second_counts(self) -> None:
        measurements = PulseMeasurements(rest=20, after_load=30, after_recovery=25)
        self.assertEqual(calculate_index(measurements), 10.0)

    def test_converts_measurements_to_beats_per_minute(self) -> None:
        result = assess(PulseMeasurements(18, 27, 21), age=16)
        self.assertEqual((result.rest_bpm, result.after_load_bpm, result.after_recovery_bpm), (72, 108, 84))

    def test_uses_age_adjusted_thresholds(self) -> None:
        self.assertEqual(low_level_threshold(7), 21.0)
        self.assertEqual(low_level_threshold(10), 19.5)
        self.assertEqual(low_level_threshold(12), 18.0)
        self.assertEqual(low_level_threshold(14), 16.5)
        self.assertEqual(low_level_threshold(15), 15.0)
        self.assertEqual(low_level_threshold(45), 15.0)

    def test_classifies_all_ranges_for_age_15_plus(self) -> None:
        self.assertEqual(classify_index(15.0, 15).key, "low")
        self.assertEqual(classify_index(11.0, 15).key, "below_average")
        self.assertEqual(classify_index(6.0, 15).key, "average")
        self.assertEqual(classify_index(0.5, 15).key, "good")
        self.assertEqual(classify_index(0.4, 15).key, "excellent")

    def test_rejects_unsupported_age(self) -> None:
        for age in (6, 121):
            with self.subTest(age=age), self.assertRaises(ValueError):
                validate_age(age)


if __name__ == "__main__":
    unittest.main()

