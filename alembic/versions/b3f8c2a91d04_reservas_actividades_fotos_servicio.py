"""
reservas_actividades_fotos_servicio

Revision ID: b3f8c2a91d04
Revises: f921a0733dcf
Create Date: 2026-04-13

Changes:
- Create 'reservas_actividades' table (checklist per reservation)
- Create 'fotos_servicio' table (photos per reservation)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'b3f8c2a91d04'
down_revision = 'f921a0733dcf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # reservas_actividades
    # ------------------------------------------------------------------ #
    op.create_table(
        'reservas_actividades',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('id_reserva', postgresql.UUID(as_uuid=True), sa.ForeignKey('reservas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('id_actividad', postgresql.UUID(as_uuid=True), sa.ForeignKey('actividades.id', ondelete='CASCADE'), nullable=False),
        sa.Column('programada', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('ejecutada', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('notas', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_reservas_actividades_reserva', 'reservas_actividades', ['id_reserva'])
    op.create_index('ix_reservas_actividades_actividad', 'reservas_actividades', ['id_actividad'])

    # ------------------------------------------------------------------ #
    # fotos_servicio
    # ------------------------------------------------------------------ #
    op.create_table(
        'fotos_servicio',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('id_reserva', postgresql.UUID(as_uuid=True), sa.ForeignKey('reservas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('url_foto', sa.String(500), nullable=False),
        sa.Column('descripcion', sa.Text, nullable=True),
        sa.Column('tipo', sa.String(20), nullable=True, server_default='durante'),
        sa.Column('subida_por', postgresql.UUID(as_uuid=True), sa.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True, server_default=sa.func.now()),
    )
    op.create_index('ix_fotos_servicio_reserva', 'fotos_servicio', ['id_reserva'])


def downgrade() -> None:
    op.drop_index('ix_fotos_servicio_reserva', 'fotos_servicio')
    op.drop_table('fotos_servicio')
    op.drop_index('ix_reservas_actividades_actividad', 'reservas_actividades')
    op.drop_index('ix_reservas_actividades_reserva', 'reservas_actividades')
    op.drop_table('reservas_actividades')
