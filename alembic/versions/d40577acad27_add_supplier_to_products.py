
"""add supplier to products

Revision ID: d40577acad27
Revises: 8f8345b418d3
Create Date: 2026-10-29 17:07:46.925972
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d40577acad27"
down_revision: Union[str, Sequence[str], None] = "8f8345b418d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add optional supplier association to products."""

    op.add_column(
        "products",
        sa.Column(
            "supplier_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_products_supplier_id",
        "products",
        "suppliers",
        ["supplier_id"],
        ["id"],
    )


def downgrade() -> None:
    """Remove supplier association from products."""

    op.drop_constraint(
        "fk_products_supplier_id",
        "products",
        type_="foreignkey",
    )

    op.drop_column(
        "products",
        "supplier_id",
    )
