
import math
from collections.abc import Sequence

import numpy as np
from sklearn.linear_model import LinearRegression


MIN_TRAINING_DAYS = 14


def predict_demand_ml(
    daily_sales: Sequence[int | float],
    forecast_days: int = 14,
) -> dict:
    """
    Forecast future demand using linear regression.

    Training observations must be ordered chronologically,
    from oldest to newest.

    Predictions are non-negative and represent estimated
    demand, not guaranteed future sales.
    """

    if forecast_days < 1 or forecast_days > 365:
        raise ValueError(
            "forecast_days must be between 1 and 365."
        )

    sales = np.asarray(daily_sales, dtype=float)

    if sales.ndim != 1:
        raise ValueError(
            "daily_sales must be a one-dimensional sequence."
        )

    if len(sales) < MIN_TRAINING_DAYS:
        raise ValueError(
            f"At least {MIN_TRAINING_DAYS} days of sales are required."
        )

    if not np.all(np.isfinite(sales)) or np.any(sales < 0):
        raise ValueError(
            "Daily sales must be finite and non-negative."
        )

    # Training uses historical observations only.
    days = np.arange(len(sales)).reshape(-1, 1)

    model = LinearRegression()
    model.fit(days, sales)

    # Predict dates strictly after the historical period.
    future_days = np.arange(
        len(sales),
        len(sales) + forecast_days,
    ).reshape(-1, 1)

    raw_predictions = model.predict(future_days)

    # Demand cannot be negative.
    daily_predictions = np.maximum(raw_predictions, 0.0)

    # Remove negligible floating-point residuals near zero.
    daily_predictions[
        np.isclose(daily_predictions, 0.0, atol=1e-10)
    ] = 0.0

    predicted_total = int(
        math.ceil(float(np.sum(daily_predictions)))
    )
    return {
        "forecast_method": "linear_regression",
        "training_days": len(sales),
        "forecast_days": forecast_days,
        "forecast_quantity": predicted_total,
        "predicted_daily_sales": [
            round(float(value), 4)
            for value in daily_predictions
        ],
    }
