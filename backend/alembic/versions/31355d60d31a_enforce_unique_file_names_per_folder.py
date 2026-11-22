"""enforce unique file names per folder

Revision ID: 31355d60d31a
Revises: 728279b38ff3
Create Date: 2026-11-21 01:26:18.368130

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '31355d60d31a'
down_revision: Union[str, Sequence[str], None] = '728279b38ff3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Root entries share a null parent_id and must have distinct names.
    op.create_unique_constraint(
        "uq_files_sibling_name",
        "files",
        ["project_id", "parent_id", "name"],
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_files_sibling_name", "files", type_="unique")
