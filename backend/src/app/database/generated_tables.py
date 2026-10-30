from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import CITEXT, JSONB

metadata = MetaData()


t_conversation_shares = Table(
    "conversation_shares",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("source_conversation_id", Uuid, nullable=False),
    Column("workspace_id", Uuid, nullable=False),
    Column("created_by", Uuid, nullable=False),
    Column("mode", Text, nullable=False),
    Column("organization_id", Uuid),
    Column("link_token_hash", Text, nullable=False),
    Column("current_snapshot_id", Uuid),
    Column("expires_at", DateTime(True)),
    Column("revoked_at", DateTime(True)),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(True), nullable=False, server_default=text("now()")),
    CheckConstraint(
        "expires_at IS NULL OR expires_at > created_at",
        name="conversation_shares_check1",
    ),
    CheckConstraint(
        "link_token_hash ~ '^[a-f0-9]{64}$'::text",
        name="conversation_shares_link_token_hash_check",
    ),
    CheckConstraint(
        "mode = 'public'::text AND organization_id IS NULL OR mode = 'organization'::text AND organization_id IS NOT NULL",
        name="conversation_shares_check",
    ),
    CheckConstraint(
        "mode = ANY (ARRAY['public'::text, 'organization'::text])",
        name="conversation_shares_mode_check",
    ),
    ForeignKeyConstraint(
        ["created_by"],
        ["chat_app.users.id"],
        ondelete="RESTRICT",
        name="conversation_shares_created_by_fkey",
    ),
    ForeignKeyConstraint(
        ["id", "current_snapshot_id"],
        ["chat_app.share_snapshots.share_id", "chat_app.share_snapshots.id"],
        deferrable=True,
        initially="DEFERRED",
        name="conversation_shares_current_snapshot_fk",
    ),
    ForeignKeyConstraint(
        ["organization_id"],
        ["chat_app.organizations.id"],
        ondelete="RESTRICT",
        name="conversation_shares_organization_id_fkey",
    ),
    ForeignKeyConstraint(
        ["source_conversation_id", "workspace_id"],
        ["chat_app.conversations.id", "chat_app.conversations.workspace_id"],
        ondelete="RESTRICT",
        name="conversation_shares_source_conversation_id_workspace_id_fkey",
    ),
    ForeignKeyConstraint(
        ["workspace_id", "organization_id"],
        ["chat_app.workspaces.id", "chat_app.workspaces.organization_id"],
        ondelete="RESTRICT",
        name="conversation_shares_workspace_id_organization_id_fkey",
    ),
    PrimaryKeyConstraint("id", name="conversation_shares_pkey"),
    UniqueConstraint(
        "id", "workspace_id", name="conversation_shares_id_workspace_id_key"
    ),
    UniqueConstraint("link_token_hash", name="conversation_shares_link_token_hash_key"),
    Index("conversation_shares_creator_idx", "created_by"),
    Index("conversation_shares_organization_idx", "organization_id"),
    Index("conversation_shares_source_idx", "source_conversation_id", "workspace_id"),
    Index("conversation_shares_workspace_org_idx", "workspace_id", "organization_id"),
    schema="chat_app",
)

t_conversations = Table(
    "conversations",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("workspace_id", Uuid, nullable=False),
    Column("owner_user_id", Uuid, nullable=False),
    Column(
        "title",
        Text,
        nullable=False,
        server_default=text("'Cuộc trò chuyện mới'::text"),
    ),
    Column("current_message_id", Uuid),
    Column("deleted_at", DateTime(True)),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("pinned_at", DateTime(True)),
    Column("archived_at", DateTime(True)),
    Column("folder_id", Uuid),
    CheckConstraint("btrim(title) <> ''::text", name="conversations_title_check"),
    ForeignKeyConstraint(
        ["folder_id", "workspace_id", "owner_user_id"],
        [
            "chat_app.conversation_folders.id",
            "chat_app.conversation_folders.workspace_id",
            "chat_app.conversation_folders.owner_user_id",
        ],
        ondelete="SET NULL (folder_id)",
        name="conversations_folder_scope_fk",
    ),
    ForeignKeyConstraint(
        ["id", "current_message_id"],
        ["chat_app.messages.conversation_id", "chat_app.messages.id"],
        deferrable=True,
        initially="DEFERRED",
        name="conversations_current_message_fk",
    ),
    ForeignKeyConstraint(
        ["owner_user_id"],
        ["chat_app.users.id"],
        ondelete="RESTRICT",
        name="conversations_owner_user_id_fkey",
    ),
    ForeignKeyConstraint(
        ["workspace_id"],
        ["chat_app.workspaces.id"],
        ondelete="RESTRICT",
        name="conversations_workspace_id_fkey",
    ),
    PrimaryKeyConstraint("id", name="conversations_pkey"),
    UniqueConstraint(
        "id",
        "workspace_id",
        "owner_user_id",
        name="conversations_id_workspace_owner_key",
    ),
    UniqueConstraint("id", "workspace_id", name="conversations_id_workspace_id_key"),
    Index("conversations_folder_fk_idx", "folder_id", "workspace_id", "owner_user_id"),
    Index(
        "conversations_sidebar_idx",
        "owner_user_id",
        "workspace_id",
        "updated_at",
        "id",
        postgresql_where="(deleted_at IS NULL)",
    ),
    Index(
        "conversations_title_search_idx",
        postgresql_ops={"chat_app.search_key(title)": "gin_trgm_ops"},
        postgresql_using="gin",
    ),
    Index("conversations_workspace_idx", "workspace_id"),
    Index(
        "idx_conversations_folder",
        "workspace_id",
        "owner_user_id",
        "folder_id",
        "updated_at",
        "id",
        postgresql_where="((folder_id IS NOT NULL) AND (deleted_at IS NULL) AND (archived_at IS NULL))",
    ),
    Index(
        "idx_conversations_pinned",
        "workspace_id",
        "owner_user_id",
        "pinned_at",
        "id",
        postgresql_where="((pinned_at IS NOT NULL) AND (deleted_at IS NULL) AND (archived_at IS NULL))",
    ),
    schema="chat_app",
    comment="One owner per conversation; pin/archive/folder stored here. current_message_id is saved branch tip, not a live execution ID.",
)

t_messages = Table(
    "messages",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("conversation_id", Uuid, nullable=False),
    Column("parent_message_id", Uuid),
    Column("role", Text, nullable=False),
    Column(
        "content",
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
        comment="Ordered AG-UI Message[] for one logical user/assistant UI row; includes toolCalls and tool results, not raw SSE token events. Backend performs SDK validation and ID/call consistency checks.",
    ),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column(
        "attachments",
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
        comment="App-owned JSON metadata for citations, sources and artifacts. Full tool output MAY duplicate content by explicit product decision; model context uses content once.",
    ),
    Column(
        "status",
        Text,
        nullable=False,
        server_default=text("'pending'::text"),
        comment="pending/running/requires_action are nonterminal. Pause persists partial content and checkpoint atomically; completed/failed/cancelled are immutable.",
    ),
    Column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="Backend-owned action/checkpoint state and resolved interactions. No client-controlled checkpoint pointers or credentials. Terminal messages remain immutable.",
    ),
    CheckConstraint(
        "chat_app.valid_agui_bundle(role, content)", name="messages_content_check"
    ),
    CheckConstraint(
        "jsonb_typeof(attachments) = 'array'::text", name="messages_attachments_check"
    ),
    CheckConstraint(
        "jsonb_typeof(metadata) = 'object'::text", name="messages_metadata_object_check"
    ),
    CheckConstraint(
        "parent_message_id IS NULL OR parent_message_id <> id", name="messages_check"
    ),
    CheckConstraint(
        "role <> 'user'::text OR (status = ANY (ARRAY['pending'::text, 'completed'::text]))",
        name="messages_user_status_check",
    ),
    CheckConstraint(
        "role = ANY (ARRAY['user'::text, 'assistant'::text])",
        name="messages_role_check",
    ),
    CheckConstraint(
        "status = ANY (ARRAY['pending'::text, 'running'::text, 'requires_action'::text, 'completed'::text, 'failed'::text, 'cancelled'::text])",
        name="messages_status_check",
    ),
    ForeignKeyConstraint(
        ["conversation_id", "parent_message_id"],
        ["chat_app.messages.conversation_id", "chat_app.messages.id"],
        deferrable=True,
        initially="DEFERRED",
        name="messages_conversation_id_parent_message_id_fkey",
    ),
    ForeignKeyConstraint(
        ["conversation_id"],
        ["chat_app.conversations.id"],
        ondelete="CASCADE",
        name="messages_conversation_id_fkey",
    ),
    PrimaryKeyConstraint("id", name="messages_pkey"),
    UniqueConstraint("conversation_id", "id", name="messages_conversation_id_id_key"),
    Index("messages_history_idx", "conversation_id", "created_at", "id"),
    Index(
        "messages_one_active_assistant_idx",
        "conversation_id",
        postgresql_where="((role = 'assistant'::text) AND (status = ANY (ARRAY['pending'::text, 'running'::text, 'requires_action'::text])))",
        unique=True,
    ),
    Index("messages_parent_idx", "conversation_id", "parent_message_id"),
    Index(
        "messages_search_idx",
        postgresql_ops={
            "chat_app.search_key(chat_app.message_text(content))": "gin_trgm_ops"
        },
        postgresql_using="gin",
    ),
    schema="chat_app",
)

t_permissions = Table(
    "permissions",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("resource", Text, nullable=False),
    Column("action", Text, nullable=False),
    Column("description", Text),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    CheckConstraint(
        "action ~ '^[a-z][a-z0-9_]*$'::text", name="permissions_action_check"
    ),
    CheckConstraint(
        "resource ~ '^[a-z][a-z0-9_]*$'::text", name="permissions_resource_check"
    ),
    PrimaryKeyConstraint("id", name="permissions_pkey"),
    UniqueConstraint("resource", "action", name="permissions_resource_action_key"),
    schema="chat_app",
)

t_share_snapshot_messages = Table(
    "share_snapshot_messages",
    metadata,
    Column("snapshot_id", Uuid, primary_key=True),
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("parent_message_id", Uuid),
    Column("role", Text, nullable=False),
    Column("content", JSONB, nullable=False),
    Column("original_created_at", DateTime(True), nullable=False),
    Column(
        "attachments",
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
        comment="Snapshot must preserve both attachments and content and remap embedded file/message/tool IDs when copied.",
    ),
    Column("status", Text, nullable=False, server_default=text("'completed'::text")),
    CheckConstraint(
        "chat_app.valid_agui_bundle(role, content)",
        name="share_snapshot_messages_content_check",
    ),
    CheckConstraint(
        "jsonb_typeof(attachments) = 'array'::text",
        name="share_snapshot_messages_attachments_check",
    ),
    CheckConstraint(
        "parent_message_id IS NULL OR parent_message_id <> id",
        name="share_snapshot_messages_check",
    ),
    CheckConstraint(
        "role <> 'user'::text OR status = 'completed'::text",
        name="snapshot_user_status_check",
    ),
    CheckConstraint(
        "role = ANY (ARRAY['user'::text, 'assistant'::text])",
        name="share_snapshot_messages_role_check",
    ),
    CheckConstraint(
        "status = ANY (ARRAY['completed'::text, 'failed'::text, 'cancelled'::text])",
        name="snapshot_message_status_check",
    ),
    ForeignKeyConstraint(
        ["snapshot_id", "parent_message_id"],
        [
            "chat_app.share_snapshot_messages.snapshot_id",
            "chat_app.share_snapshot_messages.id",
        ],
        deferrable=True,
        initially="DEFERRED",
        name="share_snapshot_messages_snapshot_id_parent_message_id_fkey",
    ),
    ForeignKeyConstraint(
        ["snapshot_id"],
        ["chat_app.share_snapshots.id"],
        ondelete="RESTRICT",
        name="share_snapshot_messages_snapshot_id_fkey",
    ),
    PrimaryKeyConstraint("snapshot_id", "id", name="share_snapshot_messages_pkey"),
    Index(
        "share_snapshot_messages_history_idx",
        "snapshot_id",
        "original_created_at",
        "id",
    ),
    Index("share_snapshot_messages_parent_idx", "snapshot_id", "parent_message_id"),
    schema="chat_app",
)

t_share_snapshots = Table(
    "share_snapshots",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("share_id", Uuid, nullable=False),
    Column("workspace_id", Uuid, nullable=False),
    Column("version", BigInteger, nullable=False),
    Column("title", Text, nullable=False),
    Column("current_message_id", Uuid),
    Column("sealed_at", DateTime(True)),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    CheckConstraint("btrim(title) <> ''::text", name="share_snapshots_title_check"),
    CheckConstraint("version > 0", name="share_snapshots_version_check"),
    ForeignKeyConstraint(
        ["id", "current_message_id"],
        [
            "chat_app.share_snapshot_messages.snapshot_id",
            "chat_app.share_snapshot_messages.id",
        ],
        deferrable=True,
        initially="DEFERRED",
        name="share_snapshots_current_message_fk",
    ),
    ForeignKeyConstraint(
        ["share_id", "workspace_id"],
        [
            "chat_app.conversation_shares.id",
            "chat_app.conversation_shares.workspace_id",
        ],
        ondelete="RESTRICT",
        name="share_snapshots_share_id_workspace_id_fkey",
    ),
    PrimaryKeyConstraint("id", name="share_snapshots_pkey"),
    UniqueConstraint("id", "workspace_id", name="share_snapshots_id_workspace_id_key"),
    UniqueConstraint("share_id", "id", name="share_snapshots_share_id_id_key"),
    UniqueConstraint(
        "share_id", "version", name="share_snapshots_share_id_version_key"
    ),
    schema="chat_app",
)

t_users = Table(
    "users",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("name", Text, nullable=False),
    Column("email", CITEXT, nullable=False),
    Column("email_verified", Boolean, nullable=False, server_default=text("false")),
    Column("is_active", Boolean, nullable=False, server_default=text("true")),
    Column(
        "is_superuser",
        Boolean,
        nullable=False,
        server_default=text("false"),
        comment="Platform administration only; never an implicit right to read private chats/files.",
    ),
    Column("avatar_url", Text),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(True), nullable=False, server_default=text("now()")),
    CheckConstraint("btrim(name) <> ''::text", name="users_name_check"),
    CheckConstraint(
        "email::text = btrim(email::text) AND email::text <> ''::text",
        name="users_email_check",
    ),
    PrimaryKeyConstraint("id", name="users_pkey"),
    UniqueConstraint("email", name="users_email_key"),
    schema="chat_app",
)

t_verifications = Table(
    "verifications",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("identifier", CITEXT, nullable=False),
    Column("purpose", Text, nullable=False),
    Column("token_hash", Text, nullable=False),
    Column("expires_at", DateTime(True), nullable=False),
    Column("consumed_at", DateTime(True)),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(True), nullable=False, server_default=text("now()")),
    CheckConstraint(
        "btrim(identifier::text) <> ''::text", name="verifications_identifier_check"
    ),
    CheckConstraint(
        "btrim(token_hash) <> ''::text", name="verifications_token_hash_check"
    ),
    CheckConstraint(
        "consumed_at IS NULL OR consumed_at >= created_at", name="verifications_check1"
    ),
    CheckConstraint("expires_at > created_at", name="verifications_check"),
    CheckConstraint(
        "purpose = ANY (ARRAY['email_verify'::text, 'password_reset'::text])",
        name="verifications_purpose_check",
    ),
    PrimaryKeyConstraint("id", name="verifications_pkey"),
    UniqueConstraint("token_hash", name="verifications_token_hash_key"),
    Index("verifications_expiry_idx", "expires_at"),
    Index("verifications_lookup_idx", "identifier", "purpose"),
    schema="chat_app",
)

t_organizations = Table(
    "organizations",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("name", Text, nullable=False),
    Column("created_by", Uuid, nullable=False),
    Column("is_active", Boolean, nullable=False, server_default=text("true")),
    Column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("avatar_url", Text),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(True), nullable=False, server_default=text("now()")),
    CheckConstraint("btrim(name) <> ''::text", name="organizations_name_check"),
    CheckConstraint(
        "jsonb_typeof(metadata) = 'object'::text", name="organizations_metadata_check"
    ),
    ForeignKeyConstraint(
        ["created_by"],
        ["chat_app.users.id"],
        ondelete="RESTRICT",
        name="organizations_created_by_fkey",
    ),
    PrimaryKeyConstraint("id", name="organizations_pkey"),
    Index("organizations_creator_idx", "created_by"),
    schema="chat_app",
)

t_refresh_tokens = Table(
    "refresh_tokens",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("user_id", Uuid, nullable=False),
    Column("token_hash", Text, nullable=False),
    Column("family_id", Uuid, nullable=False, server_default=text("uuidv7()")),
    Column("expires_at", DateTime(True), nullable=False),
    Column("consumed_at", DateTime(True)),
    Column("revoked_at", DateTime(True)),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(True), nullable=False, server_default=text("now()")),
    CheckConstraint(
        "btrim(token_hash) <> ''::text", name="refresh_tokens_token_hash_check"
    ),
    CheckConstraint(
        "consumed_at IS NULL OR consumed_at >= created_at", name="refresh_tokens_check1"
    ),
    CheckConstraint("expires_at > created_at", name="refresh_tokens_check"),
    CheckConstraint(
        "revoked_at IS NULL OR revoked_at >= created_at", name="refresh_tokens_check2"
    ),
    ForeignKeyConstraint(
        ["user_id"],
        ["chat_app.users.id"],
        ondelete="CASCADE",
        name="refresh_tokens_user_id_fkey",
    ),
    PrimaryKeyConstraint("id", name="refresh_tokens_pkey"),
    UniqueConstraint("token_hash", name="refresh_tokens_token_hash_key"),
    Index("refresh_tokens_expiry_idx", "expires_at"),
    Index("refresh_tokens_family_idx", "family_id"),
    Index("refresh_tokens_user_idx", "user_id"),
    schema="chat_app",
    comment="Global login session tokens; no organization binding. Rotation/reuse detection and family revocation require service transactions.",
)

t_stored_files = Table(
    "stored_files",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("bucket", Text, nullable=False),
    Column("object_key", Text, nullable=False),
    Column("original_name", Text, nullable=False),
    Column("content_type", Text, nullable=False),
    Column("visibility", Text, nullable=False),
    Column("size_bytes", BigInteger, nullable=False),
    Column("checksum_sha256", Text),
    Column("uploaded_by", Uuid),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("deleted_at", DateTime(True)),
    Column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="Optional extensible object: image/extraction/preview/RAG descriptors. Not ACL; no secrets, presigned URLs, vectors or chunk corpus. No speculative GIN index.",
    ),
    CheckConstraint(
        "btrim(content_type) <> ''::text AND length(content_type) <= 255",
        name="ck_stored_files_content_type",
    ),
    CheckConstraint(
        "btrim(original_name) <> ''::text AND octet_length(original_name) <= 1024",
        name="ck_stored_files_original_name",
    ),
    CheckConstraint(
        "checksum_sha256 IS NULL OR checksum_sha256 ~ '^[0-9a-f]{64}$'::text",
        name="ck_stored_files_checksum_sha256",
    ),
    CheckConstraint(
        "deleted_at IS NULL OR deleted_at >= created_at",
        name="ck_stored_files_deleted_at",
    ),
    CheckConstraint(
        "jsonb_typeof(metadata) = 'object'::text",
        name="stored_files_metadata_object_check",
    ),
    CheckConstraint(
        "length(bucket) >= 3 AND length(bucket) <= 63 AND bucket ~ '^[a-z0-9][a-z0-9.-]*[a-z0-9]$'::text AND bucket !~ '\\.\\.'::text",
        name="ck_stored_files_bucket",
    ),
    CheckConstraint(
        "octet_length(object_key) >= 1 AND octet_length(object_key) <= 1024 AND object_key !~ '(^|/)\\.\\.?(/|$)'::text",
        name="ck_stored_files_object_key",
    ),
    CheckConstraint("size_bytes >= 0", name="ck_stored_files_size"),
    CheckConstraint(
        "visibility = 'public'::text AND object_key ~~ 'public/%%'::text OR visibility = 'private'::text AND object_key ~~ 'private/%%'::text",
        name="ck_stored_files_visibility_key",
    ),
    CheckConstraint(
        "visibility = ANY (ARRAY['public'::text, 'private'::text])",
        name="ck_stored_files_visibility",
    ),
    ForeignKeyConstraint(
        ["uploaded_by"],
        ["chat_app.users.id"],
        ondelete="SET NULL",
        name="stored_files_uploaded_by_fkey",
    ),
    PrimaryKeyConstraint("id", name="stored_files_pkey"),
    UniqueConstraint("bucket", "object_key", name="uq_stored_files_bucket_object_key"),
    Index(
        "idx_stored_files_uploaded_by",
        "uploaded_by",
        postgresql_where="(uploaded_by IS NOT NULL)",
    ),
    schema="chat_app",
    comment="S3-compatible object metadata, not ACL. Backend/storage must validate actual object/checksum and enforce no overwrite. Bucket checks are basic application checks, not full vendor validation.",
)

t_user_accounts = Table(
    "user_accounts",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("user_id", Uuid, nullable=False),
    Column(
        "provider_id",
        Text,
        nullable=False,
        comment="Identifies an issuer/provider configuration, not just a vendor name; identity linking requires verification.",
    ),
    Column("account_id", Text, nullable=False),
    Column("password_hash", Text),
    Column("access_token_ciphertext", Text),
    Column("refresh_token_ciphertext", Text),
    Column("id_token_ciphertext", Text),
    Column("access_token_expires_at", DateTime(True)),
    Column("refresh_token_expires_at", DateTime(True)),
    Column("scope", Text),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(True), nullable=False, server_default=text("now()")),
    CheckConstraint(
        "btrim(account_id) <> ''::text", name="user_accounts_account_id_check"
    ),
    CheckConstraint(
        "btrim(provider_id) <> ''::text", name="user_accounts_provider_id_check"
    ),
    CheckConstraint(
        "password_hash IS NULL OR btrim(password_hash) <> ''::text",
        name="user_accounts_password_hash_check",
    ),
    CheckConstraint(
        "provider_id = 'credential'::text AND password_hash IS NOT NULL OR provider_id <> 'credential'::text AND password_hash IS NULL",
        name="user_accounts_check",
    ),
    ForeignKeyConstraint(
        ["user_id"],
        ["chat_app.users.id"],
        ondelete="CASCADE",
        name="user_accounts_user_id_fkey",
    ),
    PrimaryKeyConstraint("id", name="user_accounts_pkey"),
    UniqueConstraint(
        "provider_id", "account_id", name="user_accounts_provider_id_account_id_key"
    ),
    Index(
        "user_accounts_one_password_idx",
        "user_id",
        postgresql_where="(provider_id = 'credential'::text)",
        unique=True,
    ),
    Index("user_accounts_user_idx", "user_id"),
    schema="chat_app",
)

t_message_files = Table(
    "message_files",
    metadata,
    Column("message_id", Uuid, primary_key=True),
    Column("stored_file_id", Uuid, primary_key=True),
    ForeignKeyConstraint(
        ["message_id"],
        ["chat_app.messages.id"],
        ondelete="RESTRICT",
        name="message_files_message_id_fkey",
    ),
    ForeignKeyConstraint(
        ["stored_file_id"],
        ["chat_app.stored_files.id"],
        ondelete="RESTRICT",
        name="message_files_stored_file_id_fkey",
    ),
    PrimaryKeyConstraint("message_id", "stored_file_id", name="message_files_pkey"),
    Index("message_files_stored_file_idx", "stored_file_id"),
    schema="chat_app",
    comment="Authoritative many-to-many links. Resolve conversation/owner/workspace through messages. No extra files/chat_files table, kind or file status.",
)

t_organization_invitations = Table(
    "organization_invitations",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("organization_id", Uuid, nullable=False),
    Column("email", CITEXT, nullable=False),
    Column("invited_by", Uuid, nullable=False),
    Column("token_hash", Text, nullable=False),
    Column("status", Text, nullable=False, server_default=text("'pending'::text")),
    Column("expires_at", DateTime(True), nullable=False),
    Column("accepted_by", Uuid),
    Column("accepted_at", DateTime(True)),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(True), nullable=False, server_default=text("now()")),
    CheckConstraint(
        "btrim(token_hash) <> ''::text",
        name="organization_invitations_token_hash_check",
    ),
    CheckConstraint(
        "email::text = btrim(email::text) AND email::text <> ''::text",
        name="organization_invitations_email_check",
    ),
    CheckConstraint("expires_at > created_at", name="organization_invitations_check"),
    CheckConstraint(
        "status = 'accepted'::text AND accepted_by IS NOT NULL AND accepted_at IS NOT NULL OR status <> 'accepted'::text AND accepted_by IS NULL AND accepted_at IS NULL",
        name="organization_invitations_check1",
    ),
    CheckConstraint(
        "status = ANY (ARRAY['pending'::text, 'accepted'::text, 'revoked'::text, 'expired'::text])",
        name="organization_invitations_status_check",
    ),
    ForeignKeyConstraint(
        ["accepted_by"],
        ["chat_app.users.id"],
        ondelete="RESTRICT",
        name="organization_invitations_accepted_by_fkey",
    ),
    ForeignKeyConstraint(
        ["invited_by"],
        ["chat_app.users.id"],
        ondelete="RESTRICT",
        name="organization_invitations_invited_by_fkey",
    ),
    ForeignKeyConstraint(
        ["organization_id"],
        ["chat_app.organizations.id"],
        ondelete="CASCADE",
        name="organization_invitations_organization_id_fkey",
    ),
    PrimaryKeyConstraint("id", name="organization_invitations_pkey"),
    UniqueConstraint("token_hash", name="organization_invitations_token_hash_key"),
    Index("organization_invitations_acceptor_idx", "accepted_by"),
    Index(
        "organization_invitations_expiry_idx",
        "expires_at",
        postgresql_where="(status = 'pending'::text)",
    ),
    Index(
        "organization_invitations_pending_idx",
        "organization_id",
        "email",
        postgresql_where="(status = 'pending'::text)",
        unique=True,
    ),
    Index("organization_invitations_sender_idx", "invited_by"),
    schema="chat_app",
    comment="Acceptance must atomically verify pending/unexpired token and verified email, create/reactivate membership, assign member role, consume invitation. Mark expired pending rows before reinviting.",
)

t_organization_members = Table(
    "organization_members",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("organization_id", Uuid, nullable=False),
    Column("user_id", Uuid, nullable=False),
    Column("is_active", Boolean, nullable=False, server_default=text("true")),
    Column("joined_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("left_at", DateTime(True)),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(True), nullable=False, server_default=text("now()")),
    CheckConstraint(
        "NOT is_active OR left_at IS NULL", name="organization_members_check"
    ),
    ForeignKeyConstraint(
        ["organization_id"],
        ["chat_app.organizations.id"],
        ondelete="CASCADE",
        name="organization_members_organization_id_fkey",
    ),
    ForeignKeyConstraint(
        ["user_id"],
        ["chat_app.users.id"],
        ondelete="RESTRICT",
        name="organization_members_user_id_fkey",
    ),
    PrimaryKeyConstraint("id", name="organization_members_pkey"),
    UniqueConstraint(
        "id", "organization_id", name="organization_members_id_organization_id_key"
    ),
    UniqueConstraint(
        "organization_id",
        "user_id",
        name="organization_members_organization_id_user_id_key",
    ),
    Index("organization_members_user_idx", "user_id", "organization_id"),
    schema="chat_app",
)

t_organization_roles = Table(
    "organization_roles",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("organization_id", Uuid, nullable=False),
    Column("name", Text, nullable=False),
    Column("role_key", Text),
    Column("description", Text),
    Column("is_active", Boolean, nullable=False, server_default=text("true")),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(True), nullable=False, server_default=text("now()")),
    CheckConstraint("btrim(name) <> ''::text", name="organization_roles_name_check"),
    CheckConstraint(
        "role_key ~ '^[a-z][a-z0-9_]*$'::text", name="organization_roles_role_key_check"
    ),
    ForeignKeyConstraint(
        ["organization_id"],
        ["chat_app.organizations.id"],
        ondelete="CASCADE",
        name="organization_roles_organization_id_fkey",
    ),
    PrimaryKeyConstraint("id", name="organization_roles_pkey"),
    UniqueConstraint(
        "id", "organization_id", name="organization_roles_id_organization_id_key"
    ),
    Index(
        "organization_roles_key_idx",
        "organization_id",
        "role_key",
        postgresql_where="(role_key IS NOT NULL)",
        unique=True,
    ),
    Index("organization_roles_name_idx", "organization_id", unique=True),
    schema="chat_app",
)

t_share_snapshot_files = Table(
    "share_snapshot_files",
    metadata,
    Column("snapshot_id", Uuid, primary_key=True),
    Column("workspace_id", Uuid, nullable=False),
    Column("stored_file_id", Uuid, primary_key=True),
    Column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    CheckConstraint(
        "jsonb_typeof(metadata) = 'object'::text",
        name="snapshot_file_metadata_object_check",
    ),
    ForeignKeyConstraint(
        ["snapshot_id", "workspace_id"],
        ["chat_app.share_snapshots.id", "chat_app.share_snapshots.workspace_id"],
        ondelete="RESTRICT",
        name="share_snapshot_files_snapshot_id_workspace_id_fkey",
    ),
    ForeignKeyConstraint(
        ["stored_file_id"],
        ["chat_app.stored_files.id"],
        ondelete="RESTRICT",
        name="snapshot_stored_file_fk",
    ),
    PrimaryKeyConstraint(
        "snapshot_id", "stored_file_id", name="share_snapshot_files_pkey"
    ),
    Index("share_snapshot_files_file_idx", "stored_file_id", "workspace_id"),
    schema="chat_app",
    comment="Immutable snapshot file manifest; stored_file_id -> stored_files, metadata is backend-allowlisted snapshot, never live raw metadata.",
)

t_workspaces = Table(
    "workspaces",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("kind", Text, nullable=False),
    Column("personal_user_id", Uuid),
    Column("organization_id", Uuid),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(True), nullable=False, server_default=text("now()")),
    CheckConstraint(
        "kind = 'personal'::text AND personal_user_id IS NOT NULL AND organization_id IS NULL OR kind = 'organization'::text AND personal_user_id IS NULL AND organization_id IS NOT NULL",
        name="workspaces_check",
    ),
    CheckConstraint(
        "kind = ANY (ARRAY['personal'::text, 'organization'::text])",
        name="workspaces_kind_check",
    ),
    ForeignKeyConstraint(
        ["organization_id"],
        ["chat_app.organizations.id"],
        ondelete="RESTRICT",
        name="workspaces_organization_id_fkey",
    ),
    ForeignKeyConstraint(
        ["personal_user_id"],
        ["chat_app.users.id"],
        ondelete="RESTRICT",
        name="workspaces_personal_user_id_fkey",
    ),
    PrimaryKeyConstraint("id", name="workspaces_pkey"),
    UniqueConstraint("id", "organization_id", name="workspaces_id_organization_id_key"),
    UniqueConstraint("organization_id", name="workspaces_organization_id_key"),
    UniqueConstraint("personal_user_id", name="workspaces_personal_user_id_key"),
    schema="chat_app",
    comment="Exactly one personal workspace per created user and one per created organization, provisioned by triggers. Workspace membership does not grant chat read access.",
)

t_conversation_copy_jobs = Table(
    "conversation_copy_jobs",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("requested_by", Uuid, nullable=False),
    Column("snapshot_id", Uuid, nullable=False),
    Column("target_workspace_id", Uuid, nullable=False),
    Column("target_conversation_id", Uuid, nullable=False),
    Column("client_request_id", Text, nullable=False),
    Column("status", Text, nullable=False, server_default=text("'pending'::text")),
    Column("lease_token", Uuid),
    Column("lease_expires_at", DateTime(True)),
    Column(
        "next_attempt_at", DateTime(True), nullable=False, server_default=text("now()")
    ),
    Column("attempts", Integer, nullable=False, server_default=text("0")),
    Column("last_error", Text),
    Column("completed_at", DateTime(True)),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(True), nullable=False, server_default=text("now()")),
    CheckConstraint(
        "(lease_token IS NULL) = (lease_expires_at IS NULL)",
        name="conversation_copy_jobs_check",
    ),
    CheckConstraint(
        "(status = 'completed'::text) = (completed_at IS NOT NULL)",
        name="conversation_copy_jobs_check1",
    ),
    CheckConstraint("attempts >= 0", name="conversation_copy_jobs_attempts_check"),
    CheckConstraint(
        "btrim(client_request_id) <> ''::text",
        name="conversation_copy_jobs_client_request_id_check",
    ),
    CheckConstraint(
        "status = ANY (ARRAY['pending'::text, 'copying'::text, 'completed'::text, 'failed'::text, 'cancelled'::text])",
        name="conversation_copy_jobs_status_check",
    ),
    ForeignKeyConstraint(
        ["requested_by"],
        ["chat_app.users.id"],
        ondelete="RESTRICT",
        name="conversation_copy_jobs_requested_by_fkey",
    ),
    ForeignKeyConstraint(
        ["snapshot_id"],
        ["chat_app.share_snapshots.id"],
        ondelete="RESTRICT",
        name="conversation_copy_jobs_snapshot_id_fkey",
    ),
    ForeignKeyConstraint(
        ["target_conversation_id", "target_workspace_id"],
        ["chat_app.conversations.id", "chat_app.conversations.workspace_id"],
        ondelete="RESTRICT",
        name="conversation_copy_jobs_target_conversation_id_target_works_fkey",
    ),
    ForeignKeyConstraint(
        ["target_workspace_id"],
        ["chat_app.workspaces.id"],
        ondelete="RESTRICT",
        name="conversation_copy_jobs_target_workspace_id_fkey",
    ),
    PrimaryKeyConstraint("id", name="conversation_copy_jobs_pkey"),
    UniqueConstraint(
        "requested_by",
        "client_request_id",
        name="conversation_copy_jobs_requested_by_client_request_id_key",
    ),
    UniqueConstraint(
        "target_conversation_id",
        name="conversation_copy_jobs_target_conversation_id_key",
    ),
    Index(
        "conversation_copy_jobs_pending_idx",
        "next_attempt_at",
        "id",
        postgresql_where="(status = ANY (ARRAY['pending'::text, 'copying'::text]))",
    ),
    Index("conversation_copy_jobs_snapshot_idx", "snapshot_id"),
    Index("conversation_copy_jobs_target_workspace_idx", "target_workspace_id"),
    schema="chat_app",
    comment="Fixed snapshot version per job; duplicates reuse request id, changed request payload must be rejected. Completed copies are private, owned by requester, and survive source/share revocation.",
)

t_conversation_folders = Table(
    "conversation_folders",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("workspace_id", Uuid, nullable=False),
    Column("owner_user_id", Uuid, nullable=False),
    Column("name", Text, nullable=False),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(True), nullable=False, server_default=text("now()")),
    CheckConstraint("btrim(name) <> ''::text", name="conversation_folders_name_check"),
    ForeignKeyConstraint(
        ["owner_user_id"],
        ["chat_app.users.id"],
        ondelete="RESTRICT",
        name="conversation_folders_owner_user_id_fkey",
    ),
    ForeignKeyConstraint(
        ["workspace_id"],
        ["chat_app.workspaces.id"],
        ondelete="RESTRICT",
        name="conversation_folders_workspace_id_fkey",
    ),
    PrimaryKeyConstraint("id", name="conversation_folders_pkey"),
    UniqueConstraint(
        "id",
        "workspace_id",
        "owner_user_id",
        name="conversation_folders_id_workspace_id_owner_user_id_key",
    ),
    Index(
        "conversation_folders_name_idx", "workspace_id", "owner_user_id", unique=True
    ),
    Index("conversation_folders_owner_idx", "owner_user_id", "workspace_id"),
    schema="chat_app",
    comment="Flat personal organization of chats inside one workspace; no parent_id, shared-folder ACL, instructions or RAG project behavior.",
)

t_member_role_assignments = Table(
    "member_role_assignments",
    metadata,
    Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
    Column("organization_id", Uuid, nullable=False),
    Column("member_id", Uuid, nullable=False),
    Column("role_id", Uuid, nullable=False),
    Column("is_active", Boolean, nullable=False, server_default=text("true")),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(True), nullable=False, server_default=text("now()")),
    ForeignKeyConstraint(
        ["member_id", "organization_id"],
        [
            "chat_app.organization_members.id",
            "chat_app.organization_members.organization_id",
        ],
        ondelete="CASCADE",
        name="member_role_assignments_member_id_organization_id_fkey",
    ),
    ForeignKeyConstraint(
        ["organization_id"],
        ["chat_app.organizations.id"],
        ondelete="CASCADE",
        name="member_role_assignments_organization_id_fkey",
    ),
    ForeignKeyConstraint(
        ["role_id", "organization_id"],
        [
            "chat_app.organization_roles.id",
            "chat_app.organization_roles.organization_id",
        ],
        ondelete="RESTRICT",
        name="member_role_assignments_role_id_organization_id_fkey",
    ),
    PrimaryKeyConstraint("id", name="member_role_assignments_pkey"),
    UniqueConstraint(
        "organization_id",
        "member_id",
        "role_id",
        name="member_role_assignments_organization_id_member_id_role_id_key",
    ),
    Index("member_role_assignments_member_idx", "member_id", "organization_id"),
    Index("member_role_assignments_role_idx", "role_id", "organization_id"),
    schema="chat_app",
)

t_role_permissions = Table(
    "role_permissions",
    metadata,
    Column("role_id", Uuid, primary_key=True),
    Column("permission_id", Uuid, primary_key=True),
    Column("created_at", DateTime(True), nullable=False, server_default=text("now()")),
    ForeignKeyConstraint(
        ["permission_id"],
        ["chat_app.permissions.id"],
        ondelete="RESTRICT",
        name="role_permissions_permission_id_fkey",
    ),
    ForeignKeyConstraint(
        ["role_id"],
        ["chat_app.organization_roles.id"],
        ondelete="CASCADE",
        name="role_permissions_role_id_fkey",
    ),
    PrimaryKeyConstraint("role_id", "permission_id", name="role_permissions_pkey"),
    Index("role_permissions_permission_idx", "permission_id"),
    schema="chat_app",
)

t_share_snapshot_message_files = Table(
    "share_snapshot_message_files",
    metadata,
    Column("snapshot_id", Uuid, primary_key=True),
    Column("message_id", Uuid, primary_key=True),
    Column("stored_file_id", Uuid, primary_key=True),
    ForeignKeyConstraint(
        ["snapshot_id", "message_id"],
        [
            "chat_app.share_snapshot_messages.snapshot_id",
            "chat_app.share_snapshot_messages.id",
        ],
        ondelete="RESTRICT",
        name="share_snapshot_message_files_snapshot_id_message_id_fkey",
    ),
    ForeignKeyConstraint(
        ["snapshot_id", "stored_file_id"],
        [
            "chat_app.share_snapshot_files.snapshot_id",
            "chat_app.share_snapshot_files.stored_file_id",
        ],
        ondelete="RESTRICT",
        name="share_snapshot_message_files_snapshot_id_file_id_fkey",
    ),
    PrimaryKeyConstraint(
        "snapshot_id",
        "message_id",
        "stored_file_id",
        name="share_snapshot_message_files_pkey",
    ),
    Index("share_snapshot_message_files_file_idx", "snapshot_id", "stored_file_id"),
    schema="chat_app",
)

t_conversation_copy_files = Table(
    "conversation_copy_files",
    metadata,
    Column("job_id", Uuid, primary_key=True),
    Column("source_stored_file_id", Uuid, primary_key=True),
    Column("target_stored_file_id", Uuid, nullable=False),
    Column("status", Text, nullable=False, server_default=text("'pending'::text")),
    Column("updated_at", DateTime(True), nullable=False, server_default=text("now()")),
    CheckConstraint(
        "source_stored_file_id <> target_stored_file_id",
        name="conversation_copy_files_check",
    ),
    CheckConstraint(
        "status = ANY (ARRAY['pending'::text, 'copied'::text, 'failed'::text])",
        name="conversation_copy_files_status_check",
    ),
    ForeignKeyConstraint(
        ["job_id"],
        ["chat_app.conversation_copy_jobs.id"],
        ondelete="RESTRICT",
        name="conversation_copy_files_job_id_fkey",
    ),
    ForeignKeyConstraint(
        ["source_stored_file_id"],
        ["chat_app.stored_files.id"],
        ondelete="RESTRICT",
        name="copy_source_stored_file_fk",
    ),
    ForeignKeyConstraint(
        ["target_stored_file_id"],
        ["chat_app.stored_files.id"],
        ondelete="RESTRICT",
        name="copy_target_stored_file_fk",
    ),
    PrimaryKeyConstraint(
        "job_id", "source_stored_file_id", name="conversation_copy_files_pkey"
    ),
    UniqueConstraint(
        "target_stored_file_id", name="conversation_copy_files_target_file_id_key"
    ),
    Index("conversation_copy_files_source_idx", "source_stored_file_id"),
    schema="chat_app",
    comment="Physical copy mapping between stored_files rows. Worker copies S3 bytes to a NEW object key; DB cannot verify remote bytes itself. Separate from LLM execution.",
)
