
import pytest

from backend.app.ml_model_comparison import (
    compare_forecast_models,
)


def test_ml_outperforms_baseline_on_linear_growth():
    result = compare_forecast_models(
        daily_sales=list(range(1, 22)),
        evaluation_days=7,
    )

    assert result["training_days"] == 14
    assert result["evaluation_days"] == 7
    assert result["actual_total"] == 126

    assert result["baseline"]["forecast_quantity"] == 53
    assert result["machine_learning"]["forecast_quantity"] == 126

    assert result["machine_learning"]["metrics"]["mae"] == 0
    assert (
        result["machine_learning"]["metrics"]["wape"]
        < result["baseline"]["metrics"]["wape"]
    )


def test_models_match_on_constant_sales():
    result = compare_forecast_models(
        daily_sales=[5] * 21,
        evaluation_days=7,
    )

    assert result["actual_total"] == 35
    assert result["baseline"]["forecast_quantity"] == 35
    assert result["machine_learning"]["forecast_quantity"] == 35
    assert result["baseline"]["metrics"]["mae"] == 0
    assert result["machine_learning"]["metrics"]["mae"] == 0


def test_baseline_outperforms_ml_when_trend_reverses():
    sales = list(range(1, 15)) + [5] * 7

    result = compare_forecast_models(
        daily_sales=sales,
        evaluation_days=7,
    )

    assert (
        result["baseline"]["metrics"]["mae"]
        < result["machine_learning"]["metrics"]["mae"]
    )


def test_comparison_requires_sufficient_history():
    with pytest.raises(ValueError):
        compare_forecast_models(
            daily_sales=[5] * 20,
            evaluation_days=7,
        )


@pytest.mark.parametrize(
    "evaluation_days",
    [0, -1, 1.5, True],
)
def test_comparison_rejects_invalid_evaluation_days(
    evaluation_days,
):
    with pytest.raises(ValueError):
        compare_forecast_models(
            daily_sales=[5] * 30,
            evaluation_days=evaluation_days,
        )


def test_comparison_with_zero_actual_demand():
    result = compare_forecast_models(
        daily_sales=[5] * 14 + [0] * 7,
        evaluation_days=7,
    )

    assert result["actual_total"] == 0
    assert result["baseline"]["metrics"]["wape"] is None
    assert result["machine_learning"]["metrics"]["wape"] is None


def test_comparison_rejects_invalid_sales_values():
    with pytest.raises(ValueError):
        compare_forecast_models(
            daily_sales=[5] * 14 + [-1] * 7,
            evaluation_days=7,
        )
