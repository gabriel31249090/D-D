"""Initial local combat core. Existing data is never dropped by upgrade."""
from alembic import op
import sqlalchemy as sa

revision = "0001_local_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("characters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("sheet", sa.JSON(), nullable=False),
        sa.Column("max_hp", sa.Integer(), nullable=False),
        sa.Column("current_hp", sa.Integer(), nullable=False),
        sa.Column("active_combat_id", sa.String(36), nullable=True))
    op.create_table("parties", sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("name", sa.String(100), nullable=False))
    op.create_table("party_members",
        sa.Column("party_id", sa.String(36), sa.ForeignKey("parties.id"), primary_key=True),
        sa.Column("character_id", sa.String(36), sa.ForeignKey("characters.id"), primary_key=True))
    op.create_table("combats", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("party_id", sa.String(36), sa.ForeignKey("parties.id"), nullable=False),
        sa.Column("rule_set", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("current_actor_id", sa.String(36), nullable=True),
        sa.Column("winner", sa.String(10), nullable=True))
    op.create_table("combatants", sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("combat_id", sa.String(36), sa.ForeignKey("combats.id"), nullable=False),
        sa.Column("character_id", sa.String(36), sa.ForeignKey("characters.id"), nullable=True),
        sa.Column("profile", sa.JSON(), nullable=False),
        sa.Column("team", sa.String(10), nullable=False),
        sa.Column("max_hp", sa.Integer(), nullable=False),
        sa.Column("current_hp", sa.Integer(), nullable=False),
        sa.Column("initiative", sa.Integer(), nullable=False),
        sa.Column("initiative_roll", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("action_available", sa.Boolean(), nullable=False))
    op.create_index("ix_combatants_combat_id", "combatants", ["combat_id"])
    op.create_table("combat_events", sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("combat_id", sa.String(36), sa.ForeignKey("combats.id"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.UniqueConstraint("combat_id", "sequence"))
    op.create_index("ix_combat_events_combat_id", "combat_events", ["combat_id"])
    op.create_table("dice_logs", sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
                    sa.Column("result", sa.JSON(), nullable=False))


def downgrade():
    raise RuntimeError("Automatic downgrade is disabled: back up and explicitly review data removal first")

