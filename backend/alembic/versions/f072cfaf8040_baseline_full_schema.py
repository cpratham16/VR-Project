"""baseline full schema

Revision ID: f072cfaf804041029a46ca7b7f71c971
Revises:
Create Date: 2026-08-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f072cfaf804041029a46ca7b7f71c971"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users (referenced by most tables)
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=True),
        sa.Column("state", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "vr_scenarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("phobia_type", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "clinical_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["doctor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "community_posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_pseudonym", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_flagged", sa.Boolean(), nullable=False),
        sa.Column("moderation_status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "consent_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("consent_version", sa.String(), nullable=False),
        sa.Column("agreed_to_ai_processing", sa.Boolean(), nullable=False),
        sa.Column("agreed_to_data_usage", sa.Boolean(), nullable=False),
        sa.Column("agreed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "mood_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mood_score", sa.Integer(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("journal_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "patient_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pseudonym", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "risk_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("trigger_source", sa.String(), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("acknowledged_by_doctor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["acknowledged_by_doctor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "screening_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("screening_type", sa.String(), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("severity_band", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["doctor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "community_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_pseudonym", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_flagged", sa.Boolean(), nullable=False),
        sa.Column("moderation_status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["post_id"], ["community_posts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "vr_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("intensity_level", sa.String(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("exposure_steps", sa.Integer(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("suds_pre", sa.Integer(), nullable=True),
        sa.Column("suds_post", sa.Integer(), nullable=True),
        sa.Column("patient_feedback", sa.Text(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["doctor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["scenario_id"], ["vr_scenarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("risk_flag", sa.Boolean(), nullable=False),
        sa.Column("rag_context_used", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "vr_telemetry",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("heart_rate", sa.Float(), nullable=True),
        sa.Column("hrv_rmssd", sa.Float(), nullable=True),
        sa.Column("stress_index", sa.Float(), nullable=True),
        sa.Column("scene_stage", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["vr_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "regional_aggregates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("region", sa.String(), nullable=False),
        sa.Column("period", sa.String(), nullable=False),
        sa.Column("total_patients", sa.Integer(), nullable=False),
        sa.Column("screening_count", sa.Integer(), nullable=False),
        sa.Column("phq9_minimal", sa.Integer(), nullable=False),
        sa.Column("phq9_mild", sa.Integer(), nullable=False),
        sa.Column("phq9_moderate", sa.Integer(), nullable=False),
        sa.Column("phq9_moderately_severe", sa.Integer(), nullable=False),
        sa.Column("phq9_severe", sa.Integer(), nullable=False),
        sa.Column("gad7_minimal", sa.Integer(), nullable=False),
        sa.Column("gad7_mild", sa.Integer(), nullable=False),
        sa.Column("gad7_moderate", sa.Integer(), nullable=False),
        sa.Column("gad7_severe", sa.Integer(), nullable=False),
        sa.Column("avg_mood_score", sa.Float(), nullable=False),
        sa.Column("mood_entry_count", sa.Integer(), nullable=False),
        sa.Column("risk_alert_count", sa.Integer(), nullable=False),
        sa.Column("vr_sessions_completed", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("regional_aggregates")
    op.drop_table("vr_telemetry")
    op.drop_table("chat_messages")
    op.drop_table("vr_sessions")
    op.drop_table("community_comments")
    op.drop_table("appointments")
    op.drop_table("screening_results")
    op.drop_table("risk_alerts")
    op.drop_table("patient_profiles")
    op.drop_table("mood_entries")
    op.drop_table("consent_records")
    op.drop_table("community_posts")
    op.drop_table("clinical_notes")
    op.drop_table("chat_sessions")
    op.drop_table("vr_scenarios")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
