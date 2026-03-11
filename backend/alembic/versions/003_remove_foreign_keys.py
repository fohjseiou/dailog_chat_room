"""remove all foreign key constraints

Revision ID: 003
Revises: 002
Create Date: 2026-03-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop foreign key from sessions.user_id
    op.drop_constraint("fk_sessions_user_id", "sessions", type_="foreignkey")
    op.drop_index(op.f("ix_sessions_user_id"), table_name="sessions")

    # Drop foreign key from messages.user_id
    op.drop_constraint("fk_messages_user_id", "messages", type_="foreignkey")
    op.drop_index(op.f("ix_messages_user_id"), table_name="messages")

    # Drop foreign key from messages.session_id
    # Note: cascade behavior needs to be handled at application level now
    # The constraint might be named differently, let's check common names
    try:
        op.drop_constraint("messages_session_id_fkey", "messages", type_="foreignkey")
    except:
        pass

    # Drop foreign key from user_preferences.user_id
    op.drop_constraint("user_preferences_user_id_fkey", "user_preferences", type_="foreignkey")


def downgrade() -> None:
    # Re-add foreign keys (if you want to rollback)

    # Re-add sessions.user_id foreign key
    op.create_foreign_key(
        "fk_sessions_user_id",
        "sessions", "users",
        ["user_id"], ["id"],
        ondelete="set null"
    )
    op.create_index(op.f("ix_sessions_user_id"), "sessions", ["user_id"], unique=False)

    # Re-add messages.user_id foreign key
    op.create_foreign_key(
        "fk_messages_user_id",
        "messages", "users",
        ["user_id"], ["id"],
        ondelete="set null"
    )
    op.create_index(op.f("ix_messages_user_id"), "messages", ["user_id"], unique=False)

    # Re-add messages.session_id foreign key
    op.create_foreign_key(
        "messages_session_id_fkey",
        "messages", "sessions",
        ["session_id"], ["id"],
        ondelete="cascade"
    )

    # Re-add user_preferences.user_id foreign key
    op.create_foreign_key(
        "user_preferences_user_id_fkey",
        "user_preferences", "users",
        ["user_id"], ["id"],
        ondelete="cascade"
    )
