"""
fotos_id_actividad_url_text

Revision ID: c4e1b0d92a53
Revises: b3f8c2a91d04
Create Date: 2026-04-15

Changes:
- Change fotos_servicio.url_foto from String(500) to Text (supports base64 images)
- Add fotos_servicio.id_actividad (nullable UUID, links photo to a specific checklist item)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'c4e1b0d92a53'
down_revision = 'b3f8c2a91d04'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # fotos_servicio: url_foto → Text (for base64 image storage)
    # ------------------------------------------------------------------ #
    op.alter_column(
        'fotos_servicio', 'url_foto',
        existing_type=sa.String(500),
        type_=sa.Text(),
        nullable=False,
    )

    # ------------------------------------------------------------------ #
    # fotos_servicio: add id_actividad (nullable UUID, no FK for flexibility)
    # ------------------------------------------------------------------ #
    op.add_column(
        'fotos_servicio',
        sa.Column('id_actividad', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_fotos_servicio_actividad', 'fotos_servicio', ['id_actividad'])


def downgrade() -> None:
    op.drop_index('ix_fotos_servicio_actividad', 'fotos_servicio')
    op.drop_column('fotos_servicio', 'id_actividad')
    op.alter_column(
        'fotos_servicio', 'url_foto',
        existing_type=sa.Text(),
        type_=sa.String(500),
        nullable=False,
    )
