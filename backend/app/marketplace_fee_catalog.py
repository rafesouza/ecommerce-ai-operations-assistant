
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class ReferralFeeRule:
    category: str
    rule_type: str
    rate: Decimal | None = None
    threshold: Decimal | None = None
    lower_rate: Decimal | None = None
    upper_rate: Decimal | None = None
    minimum_fee: Decimal = Decimal("0.30")


@dataclass(frozen=True)
class MarketplaceFeeCatalog:
    marketplace: str
    version: str
    effective_from: date
    source_url: str
    rules: dict[str, ReferralFeeRule]


AMAZON_FR_CATALOG = MarketplaceFeeCatalog(
    marketplace="amazon.fr",
    version="2026-10-initial",
    effective_from=date(2026, 10, 30),
    source_url="https://sell.amazon.fr/tarifs",
    rules={
        "home_products": ReferralFeeRule(
            category="home_products",
            rule_type="price_threshold",
            threshold=Decimal("20.00"),
            lower_rate=Decimal("0.08"),
            upper_rate=Decimal("0.15"),
        ),
        "backpacks": ReferralFeeRule(
            category="backpacks",
            rule_type="fixed",
            rate=Decimal("0.15"),
        ),
        "toys_games": ReferralFeeRule(
            category="toys_games",
            rule_type="fixed",
            rate=Decimal("0.15"),
        ),
        "handmade": ReferralFeeRule(
            category="handmade",
            rule_type="fixed",
            rate=Decimal("0.12"),
        ),
        "computers": ReferralFeeRule(
            category="computers",
            rule_type="fixed",
            rate=Decimal("0.07"),
        ),
    },
)

def get_catalog_for_date(
    catalogs: list[MarketplaceFeeCatalog],
    reference_date: date,
) -> MarketplaceFeeCatalog:
    eligible_catalogs = [
        catalog
        for catalog in catalogs
        if catalog.effective_from <= reference_date
    ]

    if not eligible_catalogs:
        raise ValueError(
            "No fee catalog available for the requested date"
        )

    return max(
        eligible_catalogs,
        key=lambda catalog: catalog.effective_from,
    )
