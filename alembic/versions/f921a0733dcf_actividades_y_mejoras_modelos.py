"""
actividades_y_mejoras_modelos

Revision ID: f921a0733dcf
Revises:
Create Date: 2026-02-26

Changes:
- Create 'actividades' table (individual service activities)
- Create 'plan_actividades' M2M association table
- Drop 'servicios_asociados' from 'planes', add 'tipo_plan'
- Add 'area_m2' and 'area_ft2' to 'ubicacion_servicio'
- Add 'respondida_por' (FK) and 'fecha_respuesta' to 'pqrs'
- Generalize 'notificaciones_servicio': nullable id_reserva, add id_pqrs/tipo/canal/id_usuario_destino, drop id_cliente/tipo_notificacion
- Add 'metodo_pago' and 'fecha_pago' to 'reservas'
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'f921a0733dcf'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # actividades
    # ------------------------------------------------------------------ #
    op.create_table(
        'actividades',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('nombre', sa.String(150), nullable=False),
        sa.Column('descripcion', sa.Text, nullable=True),
        sa.Column('precio_unitario', sa.Numeric(10, 2), nullable=True),
        sa.Column('duracion_estimada_minutos', sa.Integer, nullable=True),
        sa.Column('activa', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ------------------------------------------------------------------ #
    # plan_actividades (M2M)
    # ------------------------------------------------------------------ #
    op.create_table(
        'plan_actividades',
        sa.Column('id_plan', postgresql.UUID(as_uuid=True), sa.ForeignKey('planes.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('id_actividad', postgresql.UUID(as_uuid=True), sa.ForeignKey('actividades.id', ondelete='CASCADE'), primary_key=True),
    )

    # ------------------------------------------------------------------ #
    # planes: drop servicios_asociados, add tipo_plan
    # ------------------------------------------------------------------ #
    op.drop_column('planes', 'servicios_asociados')
    op.add_column('planes', sa.Column('tipo_plan', sa.String(20), nullable=True, server_default='full'))

    # ------------------------------------------------------------------ #
    # ubicacion_servicio: add area_m2 and area_ft2
    # ------------------------------------------------------------------ #
    op.add_column('ubicacion_servicio', sa.Column('area_m2', sa.Numeric(10, 2), nullable=True))
    op.add_column('ubicacion_servicio', sa.Column('area_ft2', sa.Numeric(10, 2), nullable=True))

    # ------------------------------------------------------------------ #
    # pqrs: add respondida_por FK and fecha_respuesta
    # ------------------------------------------------------------------ #
    op.add_column('pqrs', sa.Column('respondida_por', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('pqrs', sa.Column('fecha_respuesta', sa.DateTime, nullable=True))
    op.create_foreign_key('fk_pqrs_respondida_por', 'pqrs', 'usuarios', ['respondida_por'], ['id'])

    # ------------------------------------------------------------------ #
    # notificaciones_servicio: generalize schema
    # ------------------------------------------------------------------ #
    op.drop_constraint('notificaciones_servicio_id_reserva_fkey', 'notificaciones_servicio', type_='foreignkey')
    op.drop_constraint('notificaciones_servicio_id_cliente_fkey', 'notificaciones_servicio', type_='foreignkey')
    op.drop_column('notificaciones_servicio', 'tipo_notificacion')
    op.alter_column('notificaciones_servicio', 'id_reserva', nullable=True)
    op.alter_column('notificaciones_servicio', 'id_cliente', new_column_name='id_usuario_destino')
    op.add_column('notificaciones_servicio', sa.Column('id_pqrs', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('notificaciones_servicio', sa.Column('tipo', sa.String(30), nullable=False, server_default='sistema'))
    op.add_column('notificaciones_servicio', sa.Column('canal', sa.String(10), nullable=False, server_default='in_app'))
    op.create_foreign_key('notificaciones_servicio_id_reserva_fkey', 'notificaciones_servicio', 'reservas', ['id_reserva'], ['id'])
    op.create_foreign_key('notificaciones_servicio_id_usuario_destino_fkey', 'notificaciones_servicio', 'usuarios', ['id_usuario_destino'], ['id'])
    op.create_foreign_key('notificaciones_servicio_id_pqrs_fkey', 'notificaciones_servicio', 'pqrs', ['id_pqrs'], ['id'])

    # ------------------------------------------------------------------ #
    # reservas: add metodo_pago and fecha_pago
    # ------------------------------------------------------------------ #
    op.add_column('reservas', sa.Column('metodo_pago', sa.String(30), nullable=True))
    op.add_column('reservas', sa.Column('fecha_pago', sa.DateTime, nullable=True))

    # ------------------------------------------------------------------ #
    # usuarios: drop password column (contraseñas gestionadas por Supabase Auth)
    # ------------------------------------------------------------------ #
    op.drop_column('usuarios', 'password')


def downgrade() -> None:
    # usuarios: restaurar columna password
    op.add_column('usuarios', sa.Column('password', sa.String(128), nullable=True))

    # reservas
    op.drop_column('reservas', 'fecha_pago')
    op.drop_column('reservas', 'metodo_pago')

    # notificaciones_servicio (revert generalization)
    op.drop_constraint('notificaciones_servicio_id_pqrs_fkey', 'notificaciones_servicio', type_='foreignkey')
    op.drop_constraint('notificaciones_servicio_id_usuario_destino_fkey', 'notificaciones_servicio', type_='foreignkey')
    op.drop_constraint('notificaciones_servicio_id_reserva_fkey', 'notificaciones_servicio', type_='foreignkey')
    op.drop_column('notificaciones_servicio', 'canal')
    op.drop_column('notificaciones_servicio', 'tipo')
    op.drop_column('notificaciones_servicio', 'id_pqrs')
    op.alter_column('notificaciones_servicio', 'id_usuario_destino', new_column_name='id_cliente')
    op.alter_column('notificaciones_servicio', 'id_reserva', nullable=False)
    op.add_column('notificaciones_servicio', sa.Column('tipo_notificacion', sa.String(30), nullable=False, server_default='sistema'))
    op.create_foreign_key('notificaciones_servicio_id_cliente_fkey', 'notificaciones_servicio', 'usuarios', ['id_cliente'], ['id'])
    op.create_foreign_key('notificaciones_servicio_id_reserva_fkey', 'notificaciones_servicio', 'reservas', ['id_reserva'], ['id'])

    # pqrs
    op.drop_constraint('fk_pqrs_respondida_por', 'pqrs', type_='foreignkey')
    op.drop_column('pqrs', 'fecha_respuesta')
    op.drop_column('pqrs', 'respondida_por')

    # ubicacion_servicio
    op.drop_column('ubicacion_servicio', 'area_ft2')
    op.drop_column('ubicacion_servicio', 'area_m2')

    # planes
    op.drop_column('planes', 'tipo_plan')
    op.add_column('planes', sa.Column('servicios_asociados', postgresql.ARRAY(sa.String(200)), nullable=True))

    # plan_actividades
    op.drop_table('plan_actividades')

    # actividades
    op.drop_table('actividades')
