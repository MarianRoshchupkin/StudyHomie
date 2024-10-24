"""Update check_resource_type to Russian

Revision ID: a1b2c3d4e5f6
Revises: 5ef5d5ac9789
Create Date: 2024-XX-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5ef5d5ac9789'
down_revision = '67e95507dff4'
branch_labels = None
depends_on = None


def upgrade():
    # Удаляем старое ограничение
    op.drop_constraint('check_resource_type', 'resources', type_='check')
    # Создаём новое ограничение с русскими значениями
    op.create_check_constraint(
        'check_resource_type',
        'resources',
        "type IN ('Статья', 'Видео', 'Туториал')"
    )


def downgrade():
    # Удаляем новое ограничение
    op.drop_constraint('check_resource_type', 'resources', type_='check')
    # Восстанавливаем старое ограничение с английскими значениями
    op.create_check_constraint(
        'check_resource_type',
        'resources',
        "type IN ('Article', 'Video', 'Tutorial')"
    )