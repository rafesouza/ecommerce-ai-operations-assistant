import math
from collections.abc import Sequence


def calculate_forecast_accuracy(
    actual_values: Sequence[int | float],
    predicted_values: Sequence[int | float],
) -> dict:
    """
    Calculate forecast accuracy metrics.

    MAE: Mean Absolute Error.
    WAPE: Weighted Absolute Percentage Error.

    WAPE is unavailable when total actual demand is zero.
    """

    if len(actual_values) != len(predicted_values):
        raise ValueError(
            "Actual and predicted values must have the same length."
        )

    if not actual_values:
        raise ValueError(
            "At least one observation is required."
        )

    actual = [float(value) for value in actual_values]
    predicted = [float(value) for value in predicted_values]

    if any(
        not math.isfinite(value) or value < 0
        for value in actual + predicted
    ):
        raise ValueError(
            "Values must be finite and non-negative."
        )

    absolute_errors = [
        abs(observed - forecast)
        for observed, forecast in zip(actual, predicted)
    ]

    total_absolute_error = sum(absolute_errors)
    total_actual = sum(actual)

    mae = total_absolute_error / len(absolute_errors)

    wape = (
        (total_absolute_error / total_actual) * 100
        if total_actual > 0
        else None
    )

    return {
        "observation_count": len(actual),
        "mae": round(mae, 4),
        "wape": round(wape, 2) if wape is not None else None,
        "total_actual": round(total_actual, 4),
        "total_predicted": round(sum(predicted), 4),
        "total_absolute_error": round(total_absolute_error, 4),
    }
