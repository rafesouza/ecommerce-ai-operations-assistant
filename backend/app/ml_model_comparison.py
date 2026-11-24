
import math
from collections.abc import Sequence

from backend.app.forecast_accuracy import (
    calculate_forecast_accuracy,
)
from backend.app.ml_demand_forecast import (
    MIN_TRAINING_DAYS,
    predict_demand_ml,
)


def compare_forecast_models(
    daily_sales: Sequence[int | float],
    evaluation_days: int = 7,
) -> dict:
    """
    Compare linear regression against historical averages.

    The last evaluation_days observations are reserved
    exclusively for evaluation.
    """

    sales = list(daily_sales)

    if (
        not isinstance(evaluation_days, int)
        or isinstance(evaluation_days, bool)
        or evaluation_days < 1
    ):
        raise ValueError(
            "evaluation_days must be a positive integer."
        )

    if len(sales) < MIN_TRAINING_DAYS + evaluation_days:
        raise ValueError(
            "Insufficient sales history for training and evaluation."
        )

    training_sales = sales[:-evaluation_days]
    actual_sales = sales[-evaluation_days:]

    ml_result = predict_demand_ml(
        training_sales,
        forecast_days=evaluation_days,
    )

    historical_average = (
        sum(training_sales) / len(training_sales)
    )

    baseline_daily_predictions = [
        max(0.0, historical_average)
    ] * evaluation_days

    ml_daily_predictions = ml_result[
        "predicted_daily_sales"
    ]

    baseline_metrics = calculate_forecast_accuracy(
        actual_sales,
        baseline_daily_predictions,
    )

    ml_metrics = calculate_forecast_accuracy(
        actual_sales,
        ml_daily_predictions,
    )

    baseline_total = math.ceil(
        sum(baseline_daily_predictions)
    )

    ml_total = ml_result["forecast_quantity"]

    return {
        "training_days": len(training_sales),
        "evaluation_days": evaluation_days,
        "actual_total": sum(actual_sales),
        "baseline": {
            "forecast_method": "historical_daily_average",
            "forecast_quantity": baseline_total,
            "metrics": baseline_metrics,
        },
        "machine_learning": {
            "forecast_method": "linear_regression",
            "forecast_quantity": ml_total,
            "metrics": ml_metrics,
        },
    }
