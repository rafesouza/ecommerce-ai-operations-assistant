
from decimal import Decimal
from datetime import date
from dataclasses import replace
import pytest

from backend.app.marketplace_fees import calculate_referral_fee


@pytest.mark.parametrize(
    "category, price, expected_fee",
    [
        ("home_products", "19.90", "1.59"),
        ("home_products", "20.00", "1.60"),
        ("home_products", "20.01", "3.00"),
        ("backpacks", "109.00", "16.35"),
        ("toys_games", "24.90", "3.74"),
        ("handmade", "29.90", "3.59"),
        ("computers", "100.00", "7.00"),
        ("backpacks", "1.00", "0.30"),
    ],
)
def test_amazon_fr_referral_fee(
    category,
    price,
    expected_fee,
):
    fee = calculate_referral_fee(
        category=category,
        price=Decimal(price),
        marketplace="amazon.fr",
    )

    assert fee == Decimal(expected_fee)

def test_referral_fee_unknown_category():
    with pytest.raises(
        ValueError,
        match="Unsupported category",
    ):
        calculate_referral_fee(
            category="unknown_category",
            price=Decimal("29.90"),
        )


def test_referral_fee_negative_price():
    with pytest.raises(
        ValueError,
        match="Price cannot be negative",
    ):
        calculate_referral_fee(
            category="backpacks",
            price=Decimal("-10.00"),
        )


def test_referral_fee_unsupported_marketplace():
    with pytest.raises(
        ValueError,
        match="Unsupported marketplace",
    ):
        calculate_referral_fee(
            category="backpacks",
            price=Decimal("29.90"),
            marketplace="amazon.com",
        )


def test_referral_fee_zero_price():
    fee = calculate_referral_fee(
        category="backpacks",
        price=Decimal("0.00"),
    )

    assert fee == Decimal("0.00")

def test_referral_fee_custom_rate():
    fee = calculate_referral_fee(
        category="backpacks",
        price=Decimal("100.00"),
        custom_rate_percent=Decimal("12.00"),
    )

    assert fee == Decimal("12.00")


def test_referral_fee_custom_rate_does_not_change_default():
    custom_fee = calculate_referral_fee(
        category="backpacks",
        price=Decimal("100.00"),
        custom_rate_percent=Decimal("10.00"),
    )

    default_fee = calculate_referral_fee(
        category="backpacks",
        price=Decimal("100.00"),
    )

    assert custom_fee == Decimal("10.00")
    assert default_fee == Decimal("15.00")


@pytest.mark.parametrize(
    "invalid_rate",
    [
        Decimal("-1"),
        Decimal("101"),
    ],
)
def test_referral_fee_invalid_custom_rate(invalid_rate):
    with pytest.raises(
        ValueError,
        match="Custom rate must be between 0 and 100",
    ):
        calculate_referral_fee(
            category="backpacks",
            price=Decimal("100.00"),
            custom_rate_percent=invalid_rate,
        )

from datetime import date

from backend.app.marketplace_fee_catalog import (
    AMAZON_FR_CATALOG,
)


def test_marketplace_catalog_metadata():
    assert AMAZON_FR_CATALOG.marketplace == "amazon.fr"
    assert AMAZON_FR_CATALOG.version == "2026-10-initial"
    assert AMAZON_FR_CATALOG.effective_from == date(2026, 10, 30)
    assert AMAZON_FR_CATALOG.source_url == (
        "https://sell.amazon.fr/tarifs"
    )


def test_marketplace_catalog_categories():
    expected_categories = {
        "home_products",
        "backpacks",
        "toys_games",
        "handmade",
        "computers",
    }

    assert set(AMAZON_FR_CATALOG.rules) == expected_categories


def test_referral_fee_uses_versioned_catalog(monkeypatch):
    from backend.app import marketplace_fees

    def fail_if_legacy_rules_are_used(*args, **kwargs):
        raise AssertionError(
            "Legacy fee rules should not be used"
        )

    monkeypatch.setattr(
        marketplace_fees,
        "AMAZON_FR_REFERRAL_RULES",
        fail_if_legacy_rules_are_used,
    )

    fee = marketplace_fees.calculate_referral_fee(
        category="backpacks",
        price=Decimal("100.00"),
    )

    assert fee == Decimal("15.00")

def test_marketplace_catalog_version_selection():
    from backend.app.marketplace_fee_catalog import (
        get_catalog_for_date,
    )

    old_catalog = replace(
        AMAZON_FR_CATALOG,
        version="2026-10",
        effective_from=date(2026, 10, 30),
    )

    new_catalog = replace(
        AMAZON_FR_CATALOG,
        version="2027-01",
        effective_from=date(2027, 1, 1),
    )

    catalogs = [old_catalog, new_catalog]

    selected_2026 = get_catalog_for_date(
        catalogs,
        date(2026, 12, 15),
    )

    selected_2027 = get_catalog_for_date(
        catalogs,
        date(2027, 2, 1),
    )

    assert selected_2026.version == "2026-10"
    assert selected_2027.version == "2027-01"

from dataclasses import replace

from backend.app.marketplace_fee_catalog import (
    get_catalog_for_date,
)


def test_catalog_selection_before_first_version():
    with pytest.raises(
        ValueError,
        match="No fee catalog available",
    ):
        get_catalog_for_date(
            [AMAZON_FR_CATALOG],
            date(2025, 1, 1),
        )


def test_catalog_selection_empty_list():
    with pytest.raises(
        ValueError,
        match="No fee catalog available",
    ):
        get_catalog_for_date(
            [],
            date(2026, 12, 1),
        )


def test_catalog_selection_unsorted_versions():
    old_catalog = replace(
        AMAZON_FR_CATALOG,
        version="2026-10",
        effective_from=date(2026, 10, 30),
    )

    new_catalog = replace(
        AMAZON_FR_CATALOG,
        version="2027-01",
        effective_from=date(2027, 1, 1),
    )

    selected = get_catalog_for_date(
        [new_catalog, old_catalog],
        date(2026, 12, 15),
    )

    assert selected.version == "2026-10"

def test_referral_fee_with_historical_catalog():
    old_catalog = replace(
        AMAZON_FR_CATALOG,
        version="2026-10",
        effective_from=date(2026, 10, 30),
    )

    new_rules = dict(AMAZON_FR_CATALOG.rules)

    new_rules["backpacks"] = replace(
        new_rules["backpacks"],
        rate=Decimal("0.12"),
    )

    new_catalog = replace(
        AMAZON_FR_CATALOG,
        version="2027-01",
        effective_from=date(2027, 1, 1),
        rules=new_rules,
    )

    catalogs = [old_catalog, new_catalog]

    selected_old = get_catalog_for_date(
        catalogs,
        date(2026, 12, 15),
    )

    selected_new = get_catalog_for_date(
        catalogs,
        date(2027, 2, 1),
    )

    old_fee = calculate_referral_fee(
        category="backpacks",
        price=Decimal("100.00"),
        catalog=selected_old,
    )

    new_fee = calculate_referral_fee(
        category="backpacks",
        price=Decimal("100.00"),
        catalog=selected_new,
    )

    assert old_fee == Decimal("15.00")
    assert new_fee == Decimal("12.00")

    assert (
        AMAZON_FR_CATALOG.rules["backpacks"].rate
        == Decimal("0.15")
    )
