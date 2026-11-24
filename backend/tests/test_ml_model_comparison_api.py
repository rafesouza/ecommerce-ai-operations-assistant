
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)

ENDPOINT = "/analytics/ml-model-comparison"


def test_ml_comparison_api_with_linear_growth():
    response = client.post(
        ENDPOINT,
        json={
            "daily_sales": list(range(1, 22)),
            "evaluation_days": 7,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["training_days"] == 14
    assert data["evaluation_days"] == 7
    assert data["actual_total"] == 126

    assert data["baseline"]["forecast_quantity"] == 53
    assert data["machine_learning"]["forecast_quantity"] == 126

    assert data["machine_learning"]["metrics"]["mae"] == 0
    assert data["machine_learning"]["metrics"]["wape"] == 0


def test_ml_comparison_api_with_constant_sales():
    response = client.post(
        ENDPOINT,
        json={
            "daily_sales": [5] * 21,
            "evaluation_days": 7,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["baseline"]["forecast_quantity"] == 35
    assert data["machine_learning"]["forecast_quantity"] == 35


def test_ml_comparison_api_rejects_insufficient_training():
    response = client.post(
        ENDPOINT,
        json={
            "daily_sales": [5] * 15,
            "evaluation_days": 7,
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "evaluation_days",
    [0, -1, 366, 1.5, True],
)
def test_ml_comparison_api_rejects_invalid_horizon(
    evaluation_days,
):
    response = client.post(
        ENDPOINT,
        json={
            "daily_sales": [5] * 30,
            "evaluation_days": evaluation_days,
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "daily_sales",
    [
        [-1] * 21,
        [5] * 14,
        [],
        [[5] * 21],
    ],
)
def test_ml_comparison_api_rejects_invalid_sales(
    daily_sales,
):
    response = client.post(
        ENDPOINT,
        json={
            "daily_sales": daily_sales,
            "evaluation_days": 7,
        },
    )

    assert response.status_code == 422


def test_ml_comparison_api_rejects_missing_sales():
    response = client.post(
        ENDPOINT,
        json={"evaluation_days": 7},
    )

    assert response.status_code == 422


def test_ml_comparison_api_rejects_extra_fields():
    response = client.post(
        ENDPOINT,
        json={
            "daily_sales": [5] * 21,
            "evaluation_days": 7,
            "unexpected_field": "test",
        },
    )

    assert response.status_code == 422
