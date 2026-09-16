from __future__ import annotations

from dataclasses import dataclass


MIN_AGE = 7
MAX_AGE = 120
MIN_BEATS_15_SECONDS = 1
MAX_BEATS_15_SECONDS = 100


@dataclass(frozen=True)
class PulseMeasurements:
    """Pulse counts collected during three 15-second intervals."""

    rest: int
    after_load: int
    after_recovery: int

    def __post_init__(self) -> None:
        for field_name, value in (
            ("rest", self.rest),
            ("after_load", self.after_load),
            ("after_recovery", self.after_recovery),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field_name} must be an integer")
            if not MIN_BEATS_15_SECONDS <= value <= MAX_BEATS_15_SECONDS:
                raise ValueError(
                    f"{field_name} must be between {MIN_BEATS_15_SECONDS} "
                    f"and {MAX_BEATS_15_SECONDS}"
                )


@dataclass(frozen=True)
class RuffierAssessment:
    index: float
    category: str
    title: str
    explanation: str
    color: str
    rest_bpm: int
    after_load_bpm: int
    after_recovery_bpm: int


@dataclass(frozen=True)
class _Category:
    key: str
    title: str
    explanation: str
    color: str


_CATEGORIES = {
    "excellent": _Category(
        key="excellent",
        title="Высокий уровень адаптации",
        explanation=(
            "Сердечно-сосудистая система быстро реагирует на нагрузку и "
            "восстанавливается после неё."
        ),
        color="#087F5B",
    ),
    "good": _Category(
        key="good",
        title="Уровень выше среднего",
        explanation=(
            "Реакция на нагрузку и темп восстановления находятся в хорошем диапазоне."
        ),
        color="#2B8A3E",
    ),
    "average": _Category(
        key="average",
        title="Средний уровень адаптации",
        explanation=(
            "Результат соответствует среднему диапазону для указанного возраста."
        ),
        color="#B26A00",
    ),
    "below_average": _Category(
        key="below_average",
        title="Уровень ниже среднего",
        explanation=(
            "Восстановление после нагрузки занимает больше времени, чем ожидается "
            "для указанного возраста."
        ),
        color="#D9480F",
    ),
    "low": _Category(
        key="low",
        title="Низкий уровень адаптации",
        explanation=(
            "Результат заметно выходит за ориентировочный возрастной диапазон. "
            "Не увеличивайте нагрузку без консультации со специалистом."
        ),
        color="#C92A2A",
    ),
}


def validate_age(age: int) -> int:
    if isinstance(age, bool) or not isinstance(age, int):
        raise TypeError("age must be an integer")
    if not MIN_AGE <= age <= MAX_AGE:
        raise ValueError(f"age must be between {MIN_AGE} and {MAX_AGE}")
    return age


def calculate_index(measurements: PulseMeasurements) -> float:
    """Return the Ruffier index for pulse counts measured over 15 seconds."""

    value = (4 * (measurements.rest + measurements.after_load + measurements.after_recovery) - 200) / 10
    return round(value, 1)


def low_level_threshold(age: int) -> float:
    """Return the age-adjusted lower boundary of the low adaptation range."""

    validate_age(age)
    age_band = min(max((age - 7) // 2, 0), 4)
    return 21.0 - 1.5 * age_band


def classify_index(index: float, age: int) -> _Category:
    threshold = low_level_threshold(age)
    if index >= threshold:
        return _CATEGORIES["low"]
    if index >= threshold - 4.0:
        return _CATEGORIES["below_average"]
    if index >= threshold - 9.0:
        return _CATEGORIES["average"]
    if index >= threshold - 14.5:
        return _CATEGORIES["good"]
    return _CATEGORIES["excellent"]


def assess(measurements: PulseMeasurements, age: int) -> RuffierAssessment:
    validate_age(age)
    index = calculate_index(measurements)
    category = classify_index(index, age)
    return RuffierAssessment(
        index=index,
        category=category.key,
        title=category.title,
        explanation=category.explanation,
        color=category.color,
        rest_bpm=measurements.rest * 4,
        after_load_bpm=measurements.after_load * 4,
        after_recovery_bpm=measurements.after_recovery * 4,
    )

