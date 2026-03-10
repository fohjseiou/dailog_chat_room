"""add user support

Revision ID: 002
Revises: 001
Create Date: 2026-03-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("last_login", sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="uq_users_username")
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # Create user_preferences table
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.String(500), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="cascade"),
        sa.UniqueConstraint("user_id", "key", name="uq_user_preferences_user_id_key")
    )
    op.create_index(op.f("ix_user_preferences_user_id_key"), "user_preferences", ["user_id", "key"], unique=True)

    # Add user_id column to sessions table
    op.add_column(
        "sessions",
        sa.Column("user_id", sa.String(36), nullable=True)
    )
    op.create_foreign_key(
        "fk_sessions_user_id",
        "sessions", "users",
        ["user_id"], ["id"],
        ondelete="set null"
    )
    op.create_index(op.f("ix_sessions_user_id"), "sessions", ["user_id"], unique=False)

    # Add user_id column to messages table
    op.add_column(
        "messages",
        sa.Column("user_id", sa.String(36), nullable=True)
    )
    op.create_foreign_key(
        "fk_messages_user_id",
        "messages", "users",
        ["user_id"], ["id"],
        ondelete="set null"
    )
    op.create_index(op.f("ix_messages_user_id"), "messages", ["user_id"], unique=False)


def downgrade() -> None:
    # Remove user_id from messages table
    op.drop_index(op.f("ix_messages_user_id"), table_name="messages")
    op.drop_constraint("fk_messages_user_id", "messages", type_="foreignkey")
    op.drop_column("messages", "user_id")

    # Remove user_id from sessions table
    op.drop_index(op.f("ix_sessions_user_id"), table_name="sessions")
    op.drop_constraint("fk_sessions_user_id", "sessions", type_="foreignkey")
    op.drop_column("sessions", "user_id")

    # Drop user_preferences table
    op.drop_index(op.f("ix_user_preferences_user_id_key"), table_name="user_preferences")
    op.drop_table("user_preferences")

    # Drop users table
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
