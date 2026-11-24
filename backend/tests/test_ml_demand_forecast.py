
import math

import pytest

from backend.app.ml_demand_forecast import (
    predict_demand_ml,
)


def test_ml_forecast_with_increasing_sales():
    result = predict_demand_ml(
        daily_sales=list(range(1, 15)),
        forecast_days=7,
    )

    assert result["forecast_method"] == "linear_regression"
    assert result["training_days"] == 14
    assert result["forecast_days"] == 7
    assert result["forecast_quantity"] == 126
    assert len(result["predicted_daily_sales"]) == 7


def test_ml_forecast_with_constant_sales():
    result = predict_demand_ml(
        daily_sales=[5] * 14,
        forecast_days=7,
    )

    assert result["forecast_quantity"] == 35
    assert all(
        value == pytest.approx(5.0)
        for value in result["predicted_daily_sales"]
    )


def test_ml_forecast_with_zero_sales():
    result = predict_demand_ml(
        daily_sales=[0] * 14,
        forecast_days=7,
    )

    assert result["forecast_quantity"] == 0
    assert result["predicted_daily_sales"] == [0.0] * 7


def test_ml_forecast_with_decreasing_sales():
    result = predict_demand_ml(
        daily_sales=list(range(14, 0, -1)),
        forecast_days=7,
    )

    assert result["forecast_quantity"] == 0
    assert all(
        value >= 0
        for value in result["predicted_daily_sales"]
    )


@pytest.mark.parametrize(
    "forecast_days",
    [0, -1, 366],
)
def test_ml_forecast_rejects_invalid_horizon(forecast_days):
    with pytest.raises(ValueError):
        predict_demand_ml(
            daily_sales=[5] * 14,
            forecast_days=forecast_days,
        )


def test_ml_forecast_requires_minimum_history():
    with pytest.raises(ValueError):
        predict_demand_ml(
            daily_sales=[5] * 13,
            forecast_days=7,
        )


@pytest.mark.parametrize(
    "daily_sales",
    [
        [-1] * 14,
        [float("nan")] * 14,
        [float("inf")] * 14,
        [[5] * 14],
    ],
)
def test_ml_forecast_rejects_invalid_sales(daily_sales):
    with pytest.raises(ValueError):
        predict_demand_ml(
            daily_sales=daily_sales,
            forecast_days=7,
        )


def test_ml_forecast_daily_predictions_are_finite():
    result = predict_demand_ml(
        daily_sales=[2, 3, 2, 4, 3, 5, 4, 6, 5, 7, 6, 8, 7, 9],
        forecast_days=7,
    )

    assert all(
        math.isfinite(value) and value >= 0
        for value in result["predicted_daily_sales"]
    )
