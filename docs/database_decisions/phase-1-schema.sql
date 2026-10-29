-- Phase 1: identity, workspace, organization RBAC, snapshot sharing and copying.
-- PostgreSQL 18+ (built-in uuidv7), UTF-8. Apply ONCE to a new database.
-- This is a reviewed baseline, not an upgrade migration or an auth server.
-- Scope, service transactions and operational limits: phase-1-decisions.md.
BEGIN;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE SCHEMA chat_app;
SET LOCAL search_path = chat_app, public;

CREATE FUNCTION touch_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at := clock_timestamp();
    RETURN NEW;
END;
$$;

CREATE TABLE users (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    name text NOT NULL CHECK (btrim(name) <> ''),
    email citext NOT NULL UNIQUE CHECK (email::text = btrim(email::text) AND email::text <> ''),
    email_verified boolean NOT NULL DEFAULT false,
    is_active boolean NOT NULL DEFAULT true,
    is_superuser boolean NOT NULL DEFAULT false,
    avatar_url text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
COMMENT ON COLUMN users.is_superuser IS 'Platform administration only; never an implicit right to read private chats/files.';

CREATE TABLE user_accounts (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider_id text NOT NULL CHECK (btrim(provider_id) <> ''),
    account_id text NOT NULL CHECK (btrim(account_id) <> ''),
    password_hash text,
    access_token_ciphertext text,
    refresh_token_ciphertext text,
    id_token_ciphertext text,
    access_token_expires_at timestamptz,
    refresh_token_expires_at timestamptz,
    scope text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (provider_id, account_id),
    CHECK (password_hash IS NULL OR btrim(password_hash) <> ''),
    CHECK ((provider_id = 'credential' AND password_hash IS NOT NULL)
        OR (provider_id <> 'credential' AND password_hash IS NULL))
);
CREATE INDEX user_accounts_user_idx ON user_accounts(user_id);
CREATE UNIQUE INDEX user_accounts_one_password_idx ON user_accounts(user_id) WHERE provider_id = 'credential';
COMMENT ON COLUMN user_accounts.provider_id IS 'Identifies an issuer/provider configuration, not just a vendor name; identity linking requires verification.';

CREATE TABLE refresh_tokens (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash text NOT NULL UNIQUE CHECK (btrim(token_hash) <> ''),
    family_id uuid NOT NULL DEFAULT uuidv7(),
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz,
    revoked_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (expires_at > created_at),
    CHECK (consumed_at IS NULL OR consumed_at >= created_at),
    CHECK (revoked_at IS NULL OR revoked_at >= created_at)
);
CREATE INDEX refresh_tokens_user_idx ON refresh_tokens(user_id);
CREATE INDEX refresh_tokens_family_idx ON refresh_tokens(family_id);
CREATE INDEX refresh_tokens_expiry_idx ON refresh_tokens(expires_at);
COMMENT ON TABLE refresh_tokens IS 'Global login session tokens; no organization binding. Rotation/reuse detection and family revocation require service transactions.';

CREATE TABLE verifications (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    identifier citext NOT NULL CHECK (btrim(identifier::text) <> ''),
    purpose text NOT NULL CHECK (purpose IN ('email_verify', 'password_reset')),
    token_hash text NOT NULL UNIQUE CHECK (btrim(token_hash) <> ''),
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (expires_at > created_at),
    CHECK (consumed_at IS NULL OR consumed_at >= created_at)
);
CREATE INDEX verifications_lookup_idx ON verifications(identifier, purpose);
CREATE INDEX verifications_expiry_idx ON verifications(expires_at);

CREATE TABLE organizations (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    name text NOT NULL CHECK (btrim(name) <> ''),
    created_by uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    is_active boolean NOT NULL DEFAULT true,
    metadata jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(metadata) = 'object'),
    avatar_url text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX organizations_creator_idx ON organizations(created_by);

CREATE TABLE workspaces (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    kind text NOT NULL CHECK (kind IN ('personal', 'organization')),
    personal_user_id uuid UNIQUE REFERENCES users(id) ON DELETE RESTRICT,
    organization_id uuid UNIQUE REFERENCES organizations(id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (id, organization_id),
    CHECK ((kind = 'personal' AND personal_user_id IS NOT NULL AND organization_id IS NULL)
        OR (kind = 'organization' AND personal_user_id IS NULL AND organization_id IS NOT NULL))
);
COMMENT ON TABLE workspaces IS 'Exactly one personal workspace per created user and one per created organization, provisioned by triggers. Workspace membership does not grant chat read access.';

CREATE TABLE organization_members (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    is_active boolean NOT NULL DEFAULT true,
    joined_at timestamptz NOT NULL DEFAULT now(),
    left_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (id, organization_id),
    UNIQUE (organization_id, user_id),
    CHECK (NOT is_active OR left_at IS NULL)
);
CREATE INDEX organization_members_user_idx ON organization_members(user_id, organization_id);

CREATE TABLE permissions (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    resource text NOT NULL CHECK (resource ~ '^[a-z][a-z0-9_]*$'),
    action text NOT NULL CHECK (action ~ '^[a-z][a-z0-9_]*$'),
    description text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (resource, action)
);

CREATE TABLE organization_roles (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name text NOT NULL CHECK (btrim(name) <> ''),
    role_key text CHECK (role_key ~ '^[a-z][a-z0-9_]*$'),
    description text,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (id, organization_id)
);
CREATE UNIQUE INDEX organization_roles_name_idx ON organization_roles(organization_id, lower(name));
CREATE UNIQUE INDEX organization_roles_key_idx ON organization_roles(organization_id, role_key) WHERE role_key IS NOT NULL;

CREATE TABLE role_permissions (
    role_id uuid NOT NULL REFERENCES organization_roles(id) ON DELETE CASCADE,
    permission_id uuid NOT NULL REFERENCES permissions(id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (role_id, permission_id)
);
CREATE INDEX role_permissions_permission_idx ON role_permissions(permission_id);

CREATE TABLE member_role_assignments (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    member_id uuid NOT NULL,
    role_id uuid NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, member_id, role_id),
    FOREIGN KEY (member_id, organization_id) REFERENCES organization_members(id, organization_id) ON DELETE CASCADE,
    FOREIGN KEY (role_id, organization_id) REFERENCES organization_roles(id, organization_id) ON DELETE RESTRICT
);
CREATE INDEX member_role_assignments_member_idx ON member_role_assignments(member_id, organization_id);
CREATE INDEX member_role_assignments_role_idx ON member_role_assignments(role_id, organization_id);

CREATE TABLE organization_invitations (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email citext NOT NULL CHECK (email::text = btrim(email::text) AND email::text <> ''),
    invited_by uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    token_hash text NOT NULL UNIQUE CHECK (btrim(token_hash) <> ''),
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'revoked', 'expired')),
    expires_at timestamptz NOT NULL,
    accepted_by uuid REFERENCES users(id) ON DELETE RESTRICT,
    accepted_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (expires_at > created_at),
    CHECK ((status = 'accepted' AND accepted_by IS NOT NULL AND accepted_at IS NOT NULL)
        OR (status <> 'accepted' AND accepted_by IS NULL AND accepted_at IS NULL))
);
CREATE UNIQUE INDEX organization_invitations_pending_idx ON organization_invitations(organization_id, email) WHERE status = 'pending';
CREATE INDEX organization_invitations_sender_idx ON organization_invitations(invited_by);
CREATE INDEX organization_invitations_acceptor_idx ON organization_invitations(accepted_by);
CREATE INDEX organization_invitations_expiry_idx ON organization_invitations(expires_at) WHERE status = 'pending';
COMMENT ON TABLE organization_invitations IS 'Acceptance must atomically verify pending/unexpired token and verified email, create/reactivate membership, assign member role, consume invitation. Mark expired pending rows before reinviting.';

-- These are the minimum chat/file structures needed to model shares and copies.
-- Agent/run/checkpointer tables are intentionally deferred to the next design discussion.
CREATE TABLE conversations (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE RESTRICT,
    owner_user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title text NOT NULL DEFAULT 'Cuộc trò chuyện mới' CHECK (btrim(title) <> ''),
    title_source text NOT NULL DEFAULT 'fallback' CHECK (title_source IN ('fallback', 'generated', 'user')),
    revision bigint NOT NULL DEFAULT 0 CHECK (revision >= 0),
    current_message_id uuid,
    status text NOT NULL DEFAULT 'ready' CHECK (status IN ('copying', 'ready', 'copy_failed')),
    deleted_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (id, workspace_id)
);
CREATE INDEX conversations_workspace_idx ON conversations(workspace_id);
CREATE INDEX conversations_sidebar_idx ON conversations(owner_user_id, workspace_id, updated_at DESC, id DESC) WHERE deleted_at IS NULL;

CREATE TABLE messages (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    parent_message_id uuid,
    position bigint NOT NULL CHECK (position >= 0),
    role text NOT NULL CHECK (role IN ('user', 'assistant', 'tool', 'system')),
    content jsonb NOT NULL CHECK (jsonb_typeof(content) IN ('string', 'array')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (conversation_id, id),
    UNIQUE (conversation_id, position),
    CHECK (parent_message_id IS NULL OR parent_message_id <> id),
    FOREIGN KEY (conversation_id, parent_message_id) REFERENCES messages(conversation_id, id) DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX messages_parent_idx ON messages(conversation_id, parent_message_id);
ALTER TABLE conversations ADD CONSTRAINT conversations_current_message_fk
    FOREIGN KEY (id, current_message_id) REFERENCES messages(conversation_id, id) DEFERRABLE INITIALLY DEFERRED;
COMMENT ON COLUMN messages.position IS 'Stable order across the tree; parent must have smaller position. Not a Redis cursor or run ownership generation.';

CREATE TABLE files (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE RESTRICT,
    owner_user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    filename text NOT NULL CHECK (btrim(filename) <> ''),
    content_type text NOT NULL CHECK (btrim(content_type) <> ''),
    byte_size bigint NOT NULL CHECK (byte_size >= 0),
    sha256 text NOT NULL CHECK (sha256 ~ '^[a-f0-9]{64}$'),
    storage_key text NOT NULL UNIQUE CHECK (btrim(storage_key) <> ''),
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'ready', 'failed')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (id, workspace_id)
);
CREATE INDEX files_owner_idx ON files(owner_user_id, workspace_id);
CREATE INDEX files_workspace_idx ON files(workspace_id);
COMMENT ON TABLE files IS 'Each row identifies an immutable blob version. Copies must have a NEW row and NEW storage key; cleanup must retain snapshot-referenced blobs.';

CREATE TABLE message_files (
    conversation_id uuid NOT NULL,
    message_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    file_id uuid NOT NULL,
    PRIMARY KEY (message_id, file_id),
    FOREIGN KEY (conversation_id, message_id) REFERENCES messages(conversation_id, id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id, workspace_id) REFERENCES conversations(id, workspace_id) ON DELETE CASCADE,
    FOREIGN KEY (file_id, workspace_id) REFERENCES files(id, workspace_id) ON DELETE RESTRICT
);
CREATE INDEX message_files_conversation_idx ON message_files(conversation_id, workspace_id);
CREATE INDEX message_files_file_idx ON message_files(file_id, workspace_id);

CREATE TABLE conversation_shares (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    source_conversation_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    created_by uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    mode text NOT NULL CHECK (mode IN ('public', 'organization')),
    organization_id uuid REFERENCES organizations(id) ON DELETE RESTRICT,
    -- Raw high-entropy URL token is generated by service; store SHA-256 only.
    link_token_hash text NOT NULL UNIQUE CHECK (link_token_hash ~ '^[a-f0-9]{64}$'),
    current_snapshot_id uuid,
    expires_at timestamptz,
    revoked_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (id, workspace_id),
    CHECK ((mode = 'public' AND organization_id IS NULL)
        OR (mode = 'organization' AND organization_id IS NOT NULL)),
    CHECK (expires_at IS NULL OR expires_at > created_at),
    FOREIGN KEY (source_conversation_id, workspace_id) REFERENCES conversations(id, workspace_id) ON DELETE RESTRICT,
    FOREIGN KEY (workspace_id, organization_id) REFERENCES workspaces(id, organization_id) ON DELETE RESTRICT
);
CREATE INDEX conversation_shares_source_idx ON conversation_shares(source_conversation_id, workspace_id);
CREATE INDEX conversation_shares_creator_idx ON conversation_shares(created_by);
CREATE INDEX conversation_shares_organization_idx ON conversation_shares(organization_id);
CREATE INDEX conversation_shares_workspace_org_idx ON conversation_shares(workspace_id, organization_id);

CREATE TABLE share_snapshots (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    share_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    version bigint NOT NULL CHECK (version > 0),
    title text NOT NULL CHECK (btrim(title) <> ''),
    current_message_id uuid,
    sealed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (share_id, id),
    UNIQUE (id, workspace_id),
    UNIQUE (share_id, version),
    FOREIGN KEY (share_id, workspace_id) REFERENCES conversation_shares(id, workspace_id) ON DELETE RESTRICT
);
ALTER TABLE conversation_shares ADD CONSTRAINT conversation_shares_current_snapshot_fk
    FOREIGN KEY (id, current_snapshot_id) REFERENCES share_snapshots(share_id, id) DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE share_snapshot_messages (
    snapshot_id uuid NOT NULL REFERENCES share_snapshots(id) ON DELETE RESTRICT,
    id uuid NOT NULL DEFAULT uuidv7(),
    parent_message_id uuid,
    position bigint NOT NULL CHECK (position >= 0),
    role text NOT NULL CHECK (role IN ('user', 'assistant', 'tool', 'system')),
    content jsonb NOT NULL CHECK (jsonb_typeof(content) IN ('string', 'array')),
    original_created_at timestamptz NOT NULL,
    PRIMARY KEY (snapshot_id, id),
    UNIQUE (snapshot_id, position),
    CHECK (parent_message_id IS NULL OR parent_message_id <> id),
    FOREIGN KEY (snapshot_id, parent_message_id) REFERENCES share_snapshot_messages(snapshot_id, id) DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX share_snapshot_messages_parent_idx ON share_snapshot_messages(snapshot_id, parent_message_id);
ALTER TABLE share_snapshots ADD CONSTRAINT share_snapshots_current_message_fk
    FOREIGN KEY (id, current_message_id) REFERENCES share_snapshot_messages(snapshot_id, id) DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE share_snapshot_files (
    snapshot_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    file_id uuid NOT NULL,
    PRIMARY KEY (snapshot_id, file_id),
    FOREIGN KEY (snapshot_id, workspace_id) REFERENCES share_snapshots(id, workspace_id) ON DELETE RESTRICT,
    FOREIGN KEY (file_id, workspace_id) REFERENCES files(id, workspace_id) ON DELETE RESTRICT
);
CREATE INDEX share_snapshot_files_file_idx ON share_snapshot_files(file_id, workspace_id);

CREATE TABLE share_snapshot_message_files (
    snapshot_id uuid NOT NULL,
    message_id uuid NOT NULL,
    file_id uuid NOT NULL,
    PRIMARY KEY (snapshot_id, message_id, file_id),
    FOREIGN KEY (snapshot_id, message_id) REFERENCES share_snapshot_messages(snapshot_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (snapshot_id, file_id) REFERENCES share_snapshot_files(snapshot_id, file_id) ON DELETE RESTRICT
);
CREATE INDEX share_snapshot_message_files_file_idx ON share_snapshot_message_files(snapshot_id, file_id);

CREATE TABLE conversation_copy_jobs (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    requested_by uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    snapshot_id uuid NOT NULL REFERENCES share_snapshots(id) ON DELETE RESTRICT,
    target_workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE RESTRICT,
    target_conversation_id uuid NOT NULL UNIQUE,
    client_request_id text NOT NULL CHECK (btrim(client_request_id) <> ''),
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'copying', 'completed', 'failed', 'cancelled')),
    lease_token uuid,
    lease_expires_at timestamptz,
    next_attempt_at timestamptz NOT NULL DEFAULT now(),
    attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    last_error text,
    completed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (requested_by, client_request_id),
    FOREIGN KEY (target_conversation_id, target_workspace_id) REFERENCES conversations(id, workspace_id) ON DELETE RESTRICT,
    CHECK ((lease_token IS NULL) = (lease_expires_at IS NULL)),
    CHECK ((status = 'completed') = (completed_at IS NOT NULL))
);
CREATE INDEX conversation_copy_jobs_snapshot_idx ON conversation_copy_jobs(snapshot_id);
CREATE INDEX conversation_copy_jobs_target_workspace_idx ON conversation_copy_jobs(target_workspace_id);
CREATE INDEX conversation_copy_jobs_pending_idx ON conversation_copy_jobs(next_attempt_at, id) WHERE status IN ('pending', 'copying');
COMMENT ON TABLE conversation_copy_jobs IS 'Fixed snapshot version per job; duplicates reuse request id, changed request payload must be rejected. Completed copies are private, owned by requester, and survive source/share revocation.';

CREATE TABLE conversation_copy_files (
    job_id uuid NOT NULL REFERENCES conversation_copy_jobs(id) ON DELETE RESTRICT,
    source_file_id uuid NOT NULL REFERENCES files(id) ON DELETE RESTRICT,
    target_file_id uuid NOT NULL UNIQUE REFERENCES files(id) ON DELETE RESTRICT,
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'copied', 'failed')),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (job_id, source_file_id),
    CHECK (source_file_id <> target_file_id)
);
CREATE INDEX conversation_copy_files_source_idx ON conversation_copy_files(source_file_id);

-- Serialize membership/role mutations per org, so concurrent removal of owners
-- cannot both pass the deferred invariant. Use this same lock in service operations.
CREATE FUNCTION lock_organization_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE org uuid;
BEGIN
    IF TG_OP = 'UPDATE' AND NEW.organization_id IS DISTINCT FROM OLD.organization_id THEN
        RAISE EXCEPTION 'organization_id is immutable';
    END IF;
    IF TG_OP = 'UPDATE' AND TG_TABLE_NAME = 'organization_members' THEN
        IF NEW.user_id IS DISTINCT FROM OLD.user_id THEN
            RAISE EXCEPTION 'Membership user is immutable';
        END IF;
    END IF;
    org := CASE WHEN TG_OP = 'DELETE' THEN OLD.organization_id ELSE NEW.organization_id END;
    PERFORM pg_advisory_xact_lock(hashtextextended(org::text, 0));
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$$;
CREATE FUNCTION check_organization_owner() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE org uuid;
BEGIN
    org := CASE WHEN TG_OP = 'DELETE' THEN OLD.organization_id ELSE NEW.organization_id END;
    IF EXISTS (SELECT 1 FROM chat_app.organizations WHERE id = org) AND NOT EXISTS (
        SELECT 1 FROM chat_app.organization_members m
        JOIN chat_app.member_role_assignments a ON a.member_id = m.id AND a.organization_id = m.organization_id
        JOIN chat_app.organization_roles r ON r.id = a.role_id AND r.organization_id = a.organization_id
        WHERE m.organization_id = org AND m.is_active AND a.is_active AND r.is_active AND r.role_key = 'owner'
    ) THEN RAISE EXCEPTION 'Organization must retain an active owner membership'; END IF;
    RETURN NULL;
END;
$$;
DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['organization_members', 'organization_roles', 'member_role_assignments'] LOOP
        EXECUTE format('CREATE TRIGGER lock_org BEFORE INSERT OR UPDATE OR DELETE ON chat_app.%I FOR EACH ROW EXECUTE FUNCTION chat_app.lock_organization_mutation()', t);
        EXECUTE format('CREATE CONSTRAINT TRIGGER retain_owner AFTER INSERT OR UPDATE OR DELETE ON chat_app.%I DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION chat_app.check_organization_owner()', t);
    END LOOP;
END;
$$;

INSERT INTO permissions(resource, action, description) VALUES
    ('organization', 'manage', 'Quản trị tổ chức; không cấp quyền đọc chat riêng'),
    ('member', 'manage', 'Mời, khóa và quản lý thành viên'),
    ('role', 'manage', 'Quản lý vai trò và gán quyền'),
    ('conversation', 'create', 'Tạo conversation riêng'),
    ('conversation', 'share', 'Chia sẻ snapshot của conversation do mình sở hữu');

CREATE FUNCTION provision_personal_workspace() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO chat_app.workspaces(kind, personal_user_id) VALUES ('personal', NEW.id);
    RETURN NEW;
END;
$$;
CREATE TRIGGER provision_workspace AFTER INSERT ON users FOR EACH ROW EXECUTE FUNCTION provision_personal_workspace();

CREATE FUNCTION provision_organization() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE m uuid; owner_role uuid;
BEGIN
    INSERT INTO chat_app.workspaces(kind, organization_id) VALUES ('organization', NEW.id);
    INSERT INTO chat_app.organization_members(organization_id, user_id) VALUES (NEW.id, NEW.created_by) RETURNING id INTO m;
    INSERT INTO chat_app.organization_roles(organization_id, name, role_key)
        VALUES (NEW.id, 'Owner', 'owner') RETURNING id INTO owner_role;
    INSERT INTO chat_app.organization_roles(organization_id, name, role_key)
        VALUES (NEW.id, 'Admin', 'admin'), (NEW.id, 'Member', 'member');
    INSERT INTO chat_app.role_permissions(role_id, permission_id)
        SELECT r.id, p.id FROM chat_app.organization_roles r CROSS JOIN chat_app.permissions p
        WHERE r.organization_id = NEW.id AND (r.role_key IN ('owner', 'admin') OR p.resource = 'conversation');
    INSERT INTO chat_app.member_role_assignments(organization_id, member_id, role_id) VALUES (NEW.id, m, owner_role);
    RETURN NEW;
END;
$$;
CREATE TRIGGER provision_org AFTER INSERT ON organizations FOR EACH ROW EXECUTE FUNCTION provision_organization();

-- Personal and organization domains never change after creation.
CREATE FUNCTION guard_workspace_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF (NEW.kind, NEW.personal_user_id, NEW.organization_id) IS DISTINCT FROM
       (OLD.kind, OLD.personal_user_id, OLD.organization_id) THEN
        RAISE EXCEPTION 'Workspace identity is immutable';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER guard_identity BEFORE UPDATE ON workspaces FOR EACH ROW EXECUTE FUNCTION guard_workspace_identity();

CREATE FUNCTION guard_conversation_scope() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND (NEW.workspace_id, NEW.owner_user_id) IS DISTINCT FROM (OLD.workspace_id, OLD.owner_user_id) THEN
        RAISE EXCEPTION 'Conversation workspace and owner are immutable';
    END IF;
    IF TG_OP = 'INSERT' AND NOT EXISTS (
        SELECT 1 FROM chat_app.workspaces w
        WHERE w.id = NEW.workspace_id AND (
            w.personal_user_id = NEW.owner_user_id OR EXISTS (
                SELECT 1 FROM chat_app.organization_members m
                JOIN chat_app.organizations o ON o.id = m.organization_id
                WHERE m.organization_id = w.organization_id AND m.user_id = NEW.owner_user_id AND m.is_active AND o.is_active
            ))
    ) THEN RAISE EXCEPTION 'Conversation owner must belong to workspace'; END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER guard_scope BEFORE INSERT OR UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION guard_conversation_scope();
CREATE TRIGGER guard_owner_scope BEFORE INSERT ON files FOR EACH ROW EXECUTE FUNCTION guard_conversation_scope();

CREATE FUNCTION guard_share_scope() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND (NEW.source_conversation_id, NEW.workspace_id, NEW.created_by, NEW.mode, NEW.organization_id)
        IS DISTINCT FROM (OLD.source_conversation_id, OLD.workspace_id, OLD.created_by, OLD.mode, OLD.organization_id) THEN
        RAISE EXCEPTION 'Share source, creator and audience scope are immutable';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM chat_app.workspaces w JOIN chat_app.conversations c ON c.workspace_id = w.id
        WHERE c.id = NEW.source_conversation_id AND c.owner_user_id = NEW.created_by AND w.id = NEW.workspace_id
          AND ((w.kind = 'personal' AND NEW.mode = 'public') OR
               (w.kind = 'organization' AND NEW.mode = 'organization' AND w.organization_id = NEW.organization_id))
    ) THEN RAISE EXCEPTION 'Share must be created by chat owner and match personal/public or organization/internal'; END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER guard_scope BEFORE INSERT OR UPDATE ON conversation_shares FOR EACH ROW EXECUTE FUNCTION guard_share_scope();

-- Validate tree using positions: a parent always precedes its child => no cycles.
CREATE FUNCTION check_message_tree() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE bad boolean;
BEGIN
    IF TG_TABLE_NAME = 'messages' THEN
        SELECT EXISTS (SELECT 1 FROM chat_app.messages c JOIN chat_app.messages p
            ON p.conversation_id = c.conversation_id AND p.id = c.parent_message_id
            WHERE c.conversation_id = NEW.conversation_id AND p.position >= c.position) INTO bad;
    ELSE
        SELECT EXISTS (SELECT 1 FROM chat_app.share_snapshot_messages c JOIN chat_app.share_snapshot_messages p
            ON p.snapshot_id = c.snapshot_id AND p.id = c.parent_message_id
            WHERE c.snapshot_id = NEW.snapshot_id AND p.position >= c.position) INTO bad;
    END IF;
    IF bad THEN RAISE EXCEPTION 'Parent message must precede child'; END IF;
    RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER valid_tree AFTER INSERT OR UPDATE ON messages DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_message_tree();
CREATE CONSTRAINT TRIGGER valid_tree AFTER INSERT OR UPDATE ON share_snapshot_messages DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_message_tree();

-- Explicit access predicates for API/service queries. Not SECURITY DEFINER, not
-- an alternative to endpoint authorization or RLS; never grant clients table access.
CREATE FUNCTION can_read_conversation(p_user uuid, p_conversation uuid) RETURNS boolean LANGUAGE sql STABLE AS $$
    SELECT EXISTS (
        SELECT 1 FROM chat_app.conversations c JOIN chat_app.workspaces w ON w.id = c.workspace_id
        JOIN chat_app.users u ON u.id = p_user AND u.is_active
        WHERE c.id = p_conversation AND c.owner_user_id = p_user AND c.deleted_at IS NULL AND c.status = 'ready'
          AND (w.personal_user_id = p_user OR EXISTS (
              SELECT 1 FROM chat_app.organization_members m JOIN chat_app.organizations o ON o.id = m.organization_id
              WHERE m.organization_id = w.organization_id AND m.user_id = p_user AND m.is_active AND o.is_active))
    );
$$;
CREATE FUNCTION can_read_share(p_user uuid, p_share uuid) RETURNS boolean LANGUAGE sql STABLE AS $$
    SELECT EXISTS (
        SELECT 1 FROM chat_app.conversation_shares s
        JOIN chat_app.conversations c ON c.id = s.source_conversation_id
        JOIN chat_app.users creator ON creator.id = s.created_by AND creator.is_active
        WHERE s.id = p_share AND s.revoked_at IS NULL AND (s.expires_at IS NULL OR s.expires_at > now())
          AND c.deleted_at IS NULL AND s.current_snapshot_id IS NOT NULL
          AND (s.mode = 'public' OR (
              EXISTS (SELECT 1 FROM chat_app.organizations o WHERE o.id = s.organization_id AND o.is_active)
              AND EXISTS (SELECT 1 FROM chat_app.organization_members m
                  JOIN chat_app.users u ON u.id = m.user_id AND u.is_active
                  WHERE m.organization_id = s.organization_id AND m.user_id = p_user AND m.is_active)
              AND EXISTS (SELECT 1 FROM chat_app.organization_members m
                  WHERE m.organization_id = s.organization_id AND m.user_id = s.created_by AND m.is_active)))
    );
$$;
COMMENT ON FUNCTION can_read_share(uuid, uuid) IS 'Eligibility after resolving link token. Org membership must be checked on every request. A share is NOT a grant to the live source conversation.';

-- Authorize downloads via the specific view, never by a file id alone.
CREATE FUNCTION can_read_share_file(p_user uuid, p_share uuid, p_file uuid) RETURNS boolean LANGUAGE sql STABLE AS $$
    SELECT chat_app.can_read_share(p_user, p_share) AND EXISTS (
        SELECT 1 FROM chat_app.conversation_shares s
        JOIN chat_app.share_snapshot_message_files mf ON mf.snapshot_id = s.current_snapshot_id
        JOIN chat_app.files f ON f.id = mf.file_id AND f.status = 'ready'
        WHERE s.id = p_share AND mf.file_id = p_file
    );
$$;
CREATE FUNCTION can_read_conversation_file(p_user uuid, p_conversation uuid, p_file uuid) RETURNS boolean LANGUAGE sql STABLE AS $$
    SELECT chat_app.can_read_conversation(p_user, p_conversation) AND EXISTS (
        SELECT 1 FROM chat_app.message_files mf JOIN chat_app.files f ON f.id = mf.file_id AND f.status = 'ready'
        WHERE mf.conversation_id = p_conversation AND mf.file_id = p_file
    );
$$;

CREATE FUNCTION guard_copy_scope() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND (NEW.requested_by, NEW.snapshot_id, NEW.target_workspace_id, NEW.target_conversation_id, NEW.client_request_id)
        IS DISTINCT FROM (OLD.requested_by, OLD.snapshot_id, OLD.target_workspace_id, OLD.target_conversation_id, OLD.client_request_id) THEN
        RAISE EXCEPTION 'Copy source, destination and requester are immutable';
    END IF;
    IF TG_OP = 'INSERT' AND NOT EXISTS (
        SELECT 1 FROM chat_app.share_snapshots ss
        JOIN chat_app.conversation_shares s ON s.id = ss.share_id
        JOIN chat_app.workspaces w ON w.id = NEW.target_workspace_id
        JOIN chat_app.conversations c ON c.id = NEW.target_conversation_id AND c.workspace_id = w.id
        JOIN chat_app.users u ON u.id = NEW.requested_by AND u.is_active
        WHERE ss.id = NEW.snapshot_id AND ss.id = s.current_snapshot_id
          AND c.owner_user_id = NEW.requested_by AND c.status = 'copying'
          AND chat_app.can_read_share(NEW.requested_by, s.id)
          AND ((s.mode = 'public' AND w.kind = 'personal' AND w.personal_user_id = NEW.requested_by)
            OR (s.mode = 'organization' AND w.kind = 'organization' AND w.organization_id = s.organization_id))
    ) THEN RAISE EXCEPTION 'Copy not allowed across workspace domains or share unavailable'; END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER guard_scope BEFORE INSERT OR UPDATE ON conversation_copy_jobs FOR EACH ROW EXECUTE FUNCTION guard_copy_scope();

CREATE FUNCTION guard_file_version() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF (NEW.workspace_id, NEW.owner_user_id, NEW.filename, NEW.content_type, NEW.byte_size, NEW.sha256, NEW.storage_key)
        IS DISTINCT FROM (OLD.workspace_id, OLD.owner_user_id, OLD.filename, OLD.content_type, OLD.byte_size, OLD.sha256, OLD.storage_key) THEN
        RAISE EXCEPTION 'File version is immutable; create a new file row';
    END IF;
    IF OLD.status = 'ready' AND NEW.status <> 'ready' THEN
        RAISE EXCEPTION 'A ready immutable file version cannot become unready';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER immutable_version BEFORE UPDATE ON files FOR EACH ROW EXECUTE FUNCTION guard_file_version();

-- Permanent revocation when creator leaves: rejoining must not revive old links.
CREATE FUNCTION revoke_departed_member_shares() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    UPDATE chat_app.conversation_shares SET revoked_at = COALESCE(revoked_at, clock_timestamp())
    WHERE organization_id = OLD.organization_id AND created_by = OLD.user_id AND revoked_at IS NULL;
    RETURN NULL;
END;
$$;
CREATE TRIGGER revoke_shares AFTER UPDATE OF is_active ON organization_members FOR EACH ROW
    WHEN (OLD.is_active AND NOT NEW.is_active) EXECUTE FUNCTION revoke_departed_member_shares();
CREATE TRIGGER revoke_shares_on_delete AFTER DELETE ON organization_members FOR EACH ROW EXECUTE FUNCTION revoke_departed_member_shares();
CREATE FUNCTION revoke_deleted_conversation_shares() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    UPDATE chat_app.conversation_shares SET revoked_at = COALESCE(revoked_at, clock_timestamp())
    WHERE source_conversation_id = NEW.id AND revoked_at IS NULL;
    RETURN NULL;
END;
$$;
CREATE TRIGGER revoke_shares AFTER UPDATE OF deleted_at ON conversations FOR EACH ROW
    WHEN (OLD.deleted_at IS NULL AND NEW.deleted_at IS NOT NULL) EXECUTE FUNCTION revoke_deleted_conversation_shares();

DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['users','user_accounts','refresh_tokens','verifications','organizations','workspaces',
        'organization_members','organization_roles','member_role_assignments','organization_invitations',
        'conversations','messages','files','conversation_shares','conversation_copy_jobs','conversation_copy_files'] LOOP
        EXECUTE format('CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.%I FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at()', t);
    END LOOP;
END;
$$;

-- Build snapshots in one DB transaction, then seal and publish. Published content
-- cannot be edited in place; updating a share creates another snapshot version.
CREATE FUNCTION guard_snapshot_header() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.sealed_at IS NOT NULL THEN RAISE EXCEPTION 'Build snapshot before sealing'; END IF;
        RETURN NEW;
    END IF;
    IF OLD.sealed_at IS NOT NULL THEN RAISE EXCEPTION 'Sealed snapshot is immutable'; END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    IF (NEW.id, NEW.share_id, NEW.workspace_id, NEW.version) IS DISTINCT FROM
        (OLD.id, OLD.share_id, OLD.workspace_id, OLD.version) THEN
        RAISE EXCEPTION 'Snapshot identity is immutable';
    END IF;
    IF NEW.sealed_at IS NOT NULL AND (
        NEW.current_message_id IS NULL OR NOT EXISTS (
            SELECT 1 FROM chat_app.share_snapshot_messages WHERE snapshot_id = NEW.id)
    ) THEN RAISE EXCEPTION 'A sealed snapshot needs messages and an active message'; END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER guard_header BEFORE INSERT OR UPDATE OR DELETE ON share_snapshots
    FOR EACH ROW EXECUTE FUNCTION guard_snapshot_header();

CREATE FUNCTION guard_snapshot_content() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE sid uuid; sealed timestamptz;
BEGIN
    IF TG_OP = 'UPDATE' AND NEW.snapshot_id IS DISTINCT FROM OLD.snapshot_id THEN
        RAISE EXCEPTION 'Snapshot scope is immutable';
    END IF;
    sid := CASE WHEN TG_OP = 'DELETE' THEN OLD.snapshot_id ELSE NEW.snapshot_id END;
    -- Serialize seal vs payload writes, including concurrent transactions.
    SELECT sealed_at INTO sealed FROM chat_app.share_snapshots WHERE id = sid FOR UPDATE;
    IF sealed IS NOT NULL THEN RAISE EXCEPTION 'Sealed snapshot content is immutable'; END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER guard_content BEFORE INSERT OR UPDATE OR DELETE ON share_snapshot_messages
    FOR EACH ROW EXECUTE FUNCTION guard_snapshot_content();
CREATE TRIGGER guard_content BEFORE INSERT OR UPDATE OR DELETE ON share_snapshot_files
    FOR EACH ROW EXECUTE FUNCTION guard_snapshot_content();
CREATE TRIGGER guard_content BEFORE INSERT OR UPDATE OR DELETE ON share_snapshot_message_files
    FOR EACH ROW EXECUTE FUNCTION guard_snapshot_content();

CREATE FUNCTION check_snapshot_publication() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.current_snapshot_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM chat_app.share_snapshots ss
        WHERE ss.id = NEW.current_snapshot_id AND ss.share_id = NEW.id AND ss.sealed_at IS NOT NULL
    ) THEN RAISE EXCEPTION 'Only sealed snapshots may be published'; END IF;
    RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER valid_publication AFTER INSERT OR UPDATE ON conversation_shares
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_snapshot_publication();

CREATE FUNCTION guard_snapshot_file() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM chat_app.files f WHERE f.id = NEW.file_id AND f.status = 'ready') THEN
        RAISE EXCEPTION 'Snapshot attachments must be ready';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER guard_file BEFORE INSERT OR UPDATE ON share_snapshot_files
    FOR EACH ROW EXECUTE FUNCTION guard_snapshot_file();

CREATE FUNCTION guard_copy_file() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND (NEW.job_id, NEW.source_file_id, NEW.target_file_id) IS DISTINCT FROM
        (OLD.job_id, OLD.source_file_id, OLD.target_file_id) THEN RAISE EXCEPTION 'Copy file mapping is immutable'; END IF;
    IF NOT EXISTS (
        SELECT 1 FROM chat_app.conversation_copy_jobs j
        JOIN chat_app.share_snapshot_files sf ON sf.snapshot_id = j.snapshot_id AND sf.file_id = NEW.source_file_id
        JOIN chat_app.files src ON src.id = sf.file_id
        JOIN chat_app.files dst ON dst.id = NEW.target_file_id
        WHERE j.id = NEW.job_id AND dst.workspace_id = j.target_workspace_id AND dst.owner_user_id = j.requested_by
          AND src.storage_key <> dst.storage_key AND src.sha256 = dst.sha256 AND src.byte_size = dst.byte_size
          AND src.filename = dst.filename AND src.content_type = dst.content_type
          AND (NEW.status <> 'copied' OR dst.status = 'ready')
    ) THEN RAISE EXCEPTION 'Copy needs independent file in destination with matching content'; END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER guard_mapping BEFORE INSERT OR UPDATE ON conversation_copy_files
    FOR EACH ROW EXECUTE FUNCTION guard_copy_file();

CREATE FUNCTION check_copy_completion() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.status = 'completed' THEN
        IF EXISTS (
            SELECT 1 FROM chat_app.share_snapshot_files sf
            WHERE sf.snapshot_id = NEW.snapshot_id AND NOT EXISTS (
                SELECT 1 FROM chat_app.conversation_copy_files cf
                WHERE cf.job_id = NEW.id AND cf.source_file_id = sf.file_id AND cf.status = 'copied')
        ) OR NOT EXISTS (SELECT 1 FROM chat_app.conversations c
            WHERE c.id = NEW.target_conversation_id AND c.status = 'ready') THEN
            RAISE EXCEPTION 'Complete copies require every file copied and destination ready';
        END IF;
    END IF;
    RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER valid_completion AFTER INSERT OR UPDATE ON conversation_copy_jobs
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_copy_completion();

COMMENT ON SCHEMA chat_app IS 'Phase 1 baseline. Use service-only DB access; no implicit admin chat read. See phase-1-decisions.md for required auth, snapshot publication and blob-copy transactions.';
COMMIT;
