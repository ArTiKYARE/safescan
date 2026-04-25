"""Initial database schema — all SafeScan models

Revision ID: 001_initial
Revises:
Create Date: 2026-04-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types safely (ignore if already exist)
    for enum_name, values in [
        ("user_role", "'viewer', 'operator', 'admin', 'security_auditor'"),
        ("verification_method", "'dns', 'file', 'email', 'api_token'"),
        ("scan_type", "'full', 'quick', 'custom'"),
        (
            "scan_status",
            "'pending', 'queued', 'running', 'completed', 'failed', 'cancelled'",
        ),
        (
            "notification_type",
            "'scan_completed', 'vulnerability_found', 'critical_finding', 'verification_required', 'account_security'",
        ),
        ("notification_channel", "'email', 'webhook', 'slack'"),
        (
            "transaction_type",
            "'deposit', 'yookassa', 'scan_cost', 'admin_adjustment', 'refund'",
        ),
        ("transaction_status", "'pending', 'completed', 'failed', 'refunded'"),
    ]:
        op.execute(
            f"""
            DO $$ BEGIN
                CREATE TYPE {enum_name} AS ENUM ({values});
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """
        )

    # ── organizations ──
    op.create_table(
        "organizations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("max_domains", sa.Integer(), nullable=False, server_default="5"),
        sa.Column(
            "max_concurrent_scans", sa.Integer(), nullable=False, server_default="10"
        ),
        sa.Column(
            "data_processing_agreement",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("gdpr_consent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── users ──
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("email", sa.String(255), nullable=False, index=True, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("mfa_secret", sa.String(255), nullable=True),
        sa.Column(
            "email_verified", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("email_verification_token", sa.String(255), nullable=True),
        sa.Column(
            "email_verification_expires", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "role",
            sa.Enum(
                "viewer",
                "operator",
                "admin",
                "security_auditor",
                name="user_role",
                create_type=False,
            ),
            nullable=False,
            server_default="viewer",
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("blocked_reason", sa.String(500), nullable=True),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "failed_login_attempts", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("balance", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "free_scans_remaining", sa.Integer(), nullable=False, server_default="5"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── domains ──
    op.create_table(
        "domains",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("domain", sa.String(255), nullable=False, index=True),
        sa.Column(
            "verification_method",
            sa.Enum(
                "dns",
                "file",
                "email",
                "api_token",
                name="verification_method",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("verification_token", sa.String(255), nullable=True),
        sa.Column(
            "api_verification_token",
            sa.String(255),
            nullable=True,
            unique=True,
            index=True,
        ),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_reverification", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "reverification_required",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("dns_record_name", sa.String(100), nullable=True),
        sa.Column("dns_record_value", sa.String(255), nullable=True),
        sa.Column("verification_file_path", sa.String(255), nullable=True),
        sa.Column("verification_email_sent_to", sa.String(255), nullable=True),
        sa.Column(
            "verification_email_sent_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "scan_consent_required", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column("custom_user_agent", sa.String(255), nullable=True),
        sa.Column("excluded_paths", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── scans ──
    op.create_table(
        "scans",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "domain_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("domains.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=False,
        ),
        sa.Column(
            "scan_type",
            sa.Enum("full", "quick", "custom", name="scan_type", create_type=False),
            nullable=False,
            server_default="full",
        ),
        sa.Column("modules_enabled", postgresql.JSONB(), nullable=True),
        sa.Column("modules_disabled", postgresql.JSONB(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "queued",
                "running",
                "completed",
                "failed",
                "cancelled",
                name="scan_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
            index=True,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_completion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_module", sa.String(100), nullable=True),
        sa.Column(
            "progress_percentage", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("pages_crawled", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requests_made", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_findings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("critical_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("high_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("medium_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("low_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("info_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("grade", sa.String(2), nullable=True),
        sa.Column(
            "consent_acknowledged", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("consent_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("report_json_path", sa.String(500), nullable=True),
        sa.Column("report_pdf_path", sa.String(500), nullable=True),
        sa.Column("report_html_path", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── vulnerabilities ──
    op.create_table(
        "vulnerabilities",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "scan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("scans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("module", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, index=True),
        sa.Column("cvss_score", sa.Float(), nullable=True),
        sa.Column("cvss_vector", sa.String(100), nullable=True),
        sa.Column("affected_url", sa.String(500), nullable=True),
        sa.Column("affected_parameter", sa.String(255), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("request_data", sa.Text(), nullable=True),
        sa.Column("response_data", sa.Text(), nullable=True),
        sa.Column("remediation", sa.Text(), nullable=True),
        sa.Column("remediation_priority", sa.String(50), nullable=True),
        sa.Column("cwe_id", sa.String(20), nullable=True),
        sa.Column("cwe_name", sa.String(255), nullable=True),
        sa.Column("owasp_category", sa.String(50), nullable=True),
        sa.Column("owasp_name", sa.String(255), nullable=True),
        sa.Column("nist_control", sa.String(50), nullable=True),
        sa.Column("pci_dss_req", sa.String(50), nullable=True),
        sa.Column(
            "false_positive", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── audit_log ──
    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(100), nullable=False, index=True),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("prev_hash", sa.String(64), nullable=True),
        sa.Column("row_hash", sa.String(64), nullable=True, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── api_keys ──
    op.create_table(
        "api_keys",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key_prefix", sa.String(12), nullable=False, index=True),
        sa.Column("key_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("secret", sa.String(255), nullable=True),
        sa.Column("scopes", sa.String(255), nullable=True, server_default="read"),
        sa.Column("allowed_ips", sa.String(500), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── notifications ──
    op.create_table(
        "notifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "notification_type",
            sa.Enum(
                "scan_completed",
                "vulnerability_found",
                "critical_finding",
                "verification_required",
                "account_security",
                name="notification_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "channel",
            sa.Enum(
                "email",
                "webhook",
                "slack",
                name="notification_channel",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("config", postgresql.JSONB(), nullable=True),
        sa.Column("last_delivery_status", sa.String(20), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── transactions ──
    op.create_table(
        "transactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="'RUB'"),
        sa.Column(
            "type",
            sa.Enum(
                "deposit",
                "yookassa",
                "scan_cost",
                "admin_adjustment",
                "refund",
                name="transaction_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "completed",
                "failed",
                "refunded",
                name="transaction_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
            index=True,
        ),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column("payment_id", sa.String(255), nullable=True),
        sa.Column("confirmation_url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("transactions")
    op.drop_table("notifications")
    op.drop_table("api_keys")
    op.drop_table("audit_log")
    op.drop_table("vulnerabilities")
    op.drop_table("scans")
    op.drop_table("domains")
    op.drop_table("users")
    op.drop_table("organizations")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS transaction_status")
    op.execute("DROP TYPE IF EXISTS transaction_type")
    op.execute("DROP TYPE IF EXISTS notification_channel")
    op.execute("DROP TYPE IF EXISTS notification_type")
    op.execute("DROP TYPE IF EXISTS scan_status")
    op.execute("DROP TYPE IF EXISTS scan_type")
    op.execute("DROP TYPE IF EXISTS verification_method")
    op.execute("DROP TYPE IF EXISTS user_role")
