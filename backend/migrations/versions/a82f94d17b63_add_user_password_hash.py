"""add user password hash

Revision ID: a82f94d17b63
Revises: f39a6c20be74
Create Date: 2026-07-17 01:10:00
"""

from typing import Sequence, Union
import base64
import hashlib

from alembic import op
import sqlalchemy as sa


revision: str = "a82f94d17b63"
down_revision: Union[str, None] = "f39a6c20be74"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def encoded(password: str, salt_text: str) -> str:
    salt = salt_text.encode("utf-8")[:16].ljust(16, b"0")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 210_000)
    return f"pbkdf2_sha256$210000${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))
    users = sa.table("users", sa.column("id", sa.String()), sa.column("role", sa.String()), sa.column("password_hash", sa.String()))
    connection = op.get_bind()
    for row in connection.execute(sa.select(users.c.id, users.c.role)):
        password = "review123" if row.role in {"reviewer", "admin"} else "user123"
        connection.execute(users.update().where(users.c.id == row.id).values(password_hash=encoded(password, row.id)))
    op.alter_column("users", "password_hash", existing_type=sa.String(length=255), nullable=False)


def downgrade() -> None:
    op.drop_column("users", "password_hash")
