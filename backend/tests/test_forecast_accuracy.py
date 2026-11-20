
import pytest

from backend.app.forecast_accuracy import (
    calculate_forecast_accuracy,
)


def test_forecast_accuracy_with_different_values():
    result = calculate_forecast_accuracy(
        actual_values=[18, 30, 12],
        predicted_values=[20, 25, 15],
    )

    assert result["observation_count"] == 3
    assert result["mae"] == pytest.approx(3.3333)
    assert result["wape"] == pytest.approx(16.67)
    assert result["total_actual"] == 60
    assert result["total_predicted"] == 60
    assert result["total_absolute_error"] == 10


def test_forecast_accuracy_with_perfect_predictions():
    result = calculate_forecast_accuracy(
        actual_values=[10, 20, 30],
        predicted_values=[10, 20, 30],
    )

    assert result["mae"] == 0
    assert result["wape"] == 0
    assert result["total_absolute_error"] == 0


def test_forecast_accuracy_with_zero_actual_demand():
    result = calculate_forecast_accuracy(
        actual_values=[0, 0, 0],
        predicted_values=[2, 3, 1],
    )

    assert result["mae"] == 2
    assert result["wape"] is None
    assert result["total_actual"] == 0
    assert result["total_absolute_error"] == 6


def test_forecast_accuracy_with_empty_values():
    with pytest.raises(ValueError):
        calculate_forecast_accuracy([], [])


def test_forecast_accuracy_with_different_lengths():
    with pytest.raises(ValueError):
        calculate_forecast_accuracy(
            actual_values=[10, 20],
            predicted_values=[10],
        )


@pytest.mark.parametrize(
    "actual,predicted",
    [
        ([-1, 5], [2, 5]),
        ([1, 5], [-2, 5]),
        ([float("nan")], [1]),
        ([1], [float("inf")]),
    ],
)
def test_forecast_accuracy_rejects_invalid_values(
    actual,
    predicted,
):
    with pytest.raises(ValueError):
        calculate_forecast_accuracy(
            actual_values=actual,
            predicted_values=predicted,
        )
