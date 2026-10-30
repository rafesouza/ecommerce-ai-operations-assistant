
from decimal import Decimal, ROUND_HALF_UP

from backend.app.marketplace_fee_catalog import (
    AMAZON_FR_CATALOG,
    MarketplaceFeeCatalog,
)


CENT = Decimal("0.01")

# Temporary compatibility placeholder.
# Calculations use the versioned catalog.
AMAZON_FR_REFERRAL_RULES = None


def calculate_referral_fee(
    category: str,
    price: Decimal,
    marketplace: str = "amazon.fr",
    custom_rate_percent: Decimal | None = None,
    catalog: MarketplaceFeeCatalog | None = None,
) -> Decimal:
    selected_catalog = (
        catalog if catalog is not None
        else AMAZON_FR_CATALOG
    )

    if marketplace != selected_catalog.marketplace:
        raise ValueError(
            f"Unsupported marketplace: {marketplace}"
        )

    if category not in selected_catalog.rules:
        raise ValueError(
            f"Unsupported category: {category}"
        )

    if not price.is_finite() or price < 0:
        raise ValueError(
            "Price cannot be negative or non-finite"
        )

    if custom_rate_percent is not None:
        if (
            not custom_rate_percent.is_finite()
            or custom_rate_percent < 0
            or custom_rate_percent > 100
        ):
            raise ValueError(
                "Custom rate must be between 0 and 100"
            )

    if price == 0:
        return Decimal("0.00")

    rule = selected_catalog.rules[category]

    if custom_rate_percent is not None:
        rate = custom_rate_percent / Decimal("100")

    elif rule.rule_type == "fixed":
        rate = rule.rate

    elif rule.rule_type == "price_threshold":
        if price <= rule.threshold:
            rate = rule.lower_rate
        else:
            rate = rule.upper_rate

    else:
        raise ValueError(
            f"Unsupported rule type: {rule.rule_type}"
        )

    fee = price * rate

    fee = max(
        fee,
        rule.minimum_fee,
    )

    return fee.quantize(
        CENT,
        rounding=ROUND_HALF_UP,
    )
