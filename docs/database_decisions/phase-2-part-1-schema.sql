-- Phase 2 / part 1: approved conversation/message changes and storage mapping.
-- PostgreSQL 18+. Apply ONCE AFTER phase-1-schema.sql on a scratch/design DB.
-- Guarded baseline evolution: existing message/file/snapshot data needs a separate
-- backfill plan (S3 bucket and AG-UI IDs cannot be guessed). No CASCADE drops.
BEGIN;
SET LOCAL search_path = chat_app, public;
LOCK TABLE conversations, messages, files, message_files, conversation_shares,
    share_snapshots, share_snapshot_messages, conversation_copy_jobs IN ACCESS EXCLUSIVE MODE;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM chat_app.messages)
       OR EXISTS (SELECT 1 FROM chat_app.files)
       OR EXISTS (SELECT 1 FROM chat_app.share_snapshots)
       OR EXISTS (SELECT 1 FROM chat_app.conversation_copy_jobs)
       OR EXISTS (SELECT 1 FROM chat_app.conversations WHERE status <> 'ready') THEN
        RAISE EXCEPTION 'Phase 2 baseline requires empty message/file/snapshot/copy data; prepare an explicit backfill migration first';
    END IF;
END;
$$;

-- User-approved removals. Phase 1 did not contain title_revision, so do not add it.
ALTER TABLE conversations DROP COLUMN title_source, DROP COLUMN revision;
ALTER TABLE conversations DROP COLUMN status;
COMMENT ON TABLE conversations IS 'Conversation identity/title/active branch only. Copy visibility comes from conversation_copy_jobs; no transcript blob or message ID array.';

DROP TRIGGER valid_tree ON messages;
DROP TRIGGER valid_tree ON share_snapshot_messages;
ALTER TABLE messages DROP COLUMN position;
ALTER TABLE share_snapshot_messages DROP COLUMN position;
ALTER TABLE messages DROP CONSTRAINT messages_role_check, DROP CONSTRAINT messages_content_check;
ALTER TABLE share_snapshot_messages DROP CONSTRAINT share_snapshot_messages_role_check,
    DROP CONSTRAINT share_snapshot_messages_content_check;
ALTER TABLE messages ADD CONSTRAINT messages_role_check CHECK (role IN ('user', 'assistant'));
ALTER TABLE share_snapshot_messages ADD CONSTRAINT share_snapshot_messages_role_check CHECK (role IN ('user', 'assistant'));
ALTER TABLE messages ALTER COLUMN content SET DEFAULT '[]'::jsonb;
ALTER TABLE messages ADD COLUMN attachments jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(attachments) = 'array');
ALTER TABLE share_snapshot_messages ADD COLUMN attachments jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(attachments) = 'array');

-- Logical UI row has 2 roles; its JSON contains full AG-UI Message objects.
-- This is a shallow DB shape check. Pin SDK and validate full union in backend.
CREATE FUNCTION valid_agui_bundle(p_role text, payload jsonb) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE item jsonb; internal_role text;
BEGIN
    IF jsonb_typeof(payload) IS DISTINCT FROM 'array' THEN RETURN false; END IF;
    IF p_role = 'user' AND jsonb_array_length(payload) <> 1 THEN RETURN false; END IF;
    FOR item IN SELECT value FROM jsonb_array_elements(payload) LOOP
        IF jsonb_typeof(item) IS DISTINCT FROM 'object'
            OR jsonb_typeof(item->'id') IS DISTINCT FROM 'string'
            OR btrim(item->>'id') = ''
            OR jsonb_typeof(item->'role') IS DISTINCT FROM 'string' THEN RETURN false; END IF;
        internal_role := item->>'role';
        IF p_role = 'user' AND internal_role <> 'user' THEN RETURN false; END IF;
        IF p_role = 'assistant' AND internal_role NOT IN ('assistant', 'tool', 'reasoning', 'activity') THEN RETURN false; END IF;
    END LOOP;
    IF EXISTS (SELECT 1 FROM jsonb_array_elements(payload) x GROUP BY x->>'id' HAVING count(*) > 1) THEN RETURN false; END IF;
    RETURN true;
END;
$$;
ALTER TABLE messages ADD CONSTRAINT messages_content_check CHECK (valid_agui_bundle(role, content));
ALTER TABLE share_snapshot_messages ADD CONSTRAINT share_snapshot_messages_content_check CHECK (valid_agui_bundle(role, content));
COMMENT ON COLUMN messages.content IS 'Ordered AG-UI Message[] for one logical user/assistant UI row; includes toolCalls and tool results, not raw SSE token events. Backend performs SDK validation and ID/call consistency checks.';
COMMENT ON COLUMN messages.attachments IS 'App-owned JSON metadata for citations, sources and artifacts. Full tool output MAY duplicate content by explicit product decision; model context uses content once.';
COMMENT ON COLUMN share_snapshot_messages.attachments IS 'Snapshot must preserve both attachments and content and remap embedded file/message/tool IDs when copied.';
CREATE INDEX messages_history_idx ON messages(conversation_id, created_at, id);
CREATE INDEX share_snapshot_messages_history_idx ON share_snapshot_messages(snapshot_id, original_created_at, id);

-- Preserve parent topology after creation. User edits/regenerate insert siblings.
-- The same advisory lock must be acquired by service before reading a snapshot.
CREATE FUNCTION lock_message_tree() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND (NEW.id, NEW.conversation_id, NEW.parent_message_id, NEW.role, NEW.created_at)
        IS DISTINCT FROM (OLD.id, OLD.conversation_id, OLD.parent_message_id, OLD.role, OLD.created_at) THEN
        RAISE EXCEPTION 'Message identity, parent, role and creation time are immutable; create a new branch';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(NEW.conversation_id::text, 42));
    RETURN NEW;
END;
$$;
CREATE TRIGGER lock_tree BEFORE INSERT OR UPDATE ON messages FOR EACH ROW EXECUTE FUNCTION lock_message_tree();

CREATE OR REPLACE FUNCTION check_message_tree() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE bad boolean;
BEGIN
    IF TG_TABLE_NAME = 'messages' THEN
        WITH RECURSIVE ancestry AS (
            SELECT m.id, m.parent_message_id, ARRAY[m.id] AS path, false AS cyclic
            FROM chat_app.messages m WHERE m.conversation_id = NEW.conversation_id AND m.id = NEW.id
            UNION ALL
            SELECT p.id, p.parent_message_id, a.path || p.id, p.id = ANY(a.path)
            FROM ancestry a JOIN chat_app.messages p
              ON p.id = a.parent_message_id AND p.conversation_id = NEW.conversation_id
            WHERE NOT a.cyclic
        ) SELECT EXISTS (SELECT 1 FROM ancestry WHERE cyclic) INTO bad;
    ELSE
        WITH RECURSIVE ancestry AS (
            SELECT m.id, m.parent_message_id, ARRAY[m.id] AS path, false AS cyclic
            FROM chat_app.share_snapshot_messages m WHERE m.snapshot_id = NEW.snapshot_id AND m.id = NEW.id
            UNION ALL
            SELECT p.id, p.parent_message_id, a.path || p.id, p.id = ANY(a.path)
            FROM ancestry a JOIN chat_app.share_snapshot_messages p
              ON p.id = a.parent_message_id AND p.snapshot_id = NEW.snapshot_id
            WHERE NOT a.cyclic
        ) SELECT EXISTS (SELECT 1 FROM ancestry WHERE cyclic) INTO bad;
    END IF;
    IF bad THEN RAISE EXCEPTION 'Message parent cycle detected'; END IF;
    RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER valid_tree AFTER INSERT OR UPDATE ON messages
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_message_tree();
CREATE CONSTRAINT TRIGGER valid_tree AFTER INSERT OR UPDATE ON share_snapshot_messages
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_message_tree();
CREATE FUNCTION forbid_message_delete() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Individual message deletion/truncation is disabled; conversation uses soft delete';
END;
$$;
CREATE TRIGGER no_delete BEFORE DELETE ON messages FOR EACH ROW EXECUTE FUNCTION forbid_message_delete();
CREATE TRIGGER no_truncate BEFORE TRUNCATE ON messages FOR EACH STATEMENT EXECUTE FUNCTION forbid_message_delete();

-- Only approved sidebar fields. Folder hierarchy and folder_id remain deferred.
ALTER TABLE conversations ADD CONSTRAINT conversations_id_workspace_owner_key UNIQUE (id, workspace_id, owner_user_id);
CREATE TABLE conversation_user_states (
    conversation_id uuid NOT NULL,
    user_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    pinned_at timestamptz,
    archived_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (conversation_id, user_id),
    FOREIGN KEY (conversation_id, workspace_id, user_id)
        REFERENCES conversations(id, workspace_id, owner_user_id) ON DELETE CASCADE
);
CREATE INDEX conversation_user_states_sidebar_idx ON conversation_user_states(user_id, workspace_id, archived_at, pinned_at DESC, conversation_id);
CREATE INDEX conversation_user_states_scope_idx ON conversation_user_states(conversation_id, workspace_id, user_id);
CREATE TRIGGER touch_updated_at BEFORE UPDATE ON conversation_user_states FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
COMMENT ON TABLE conversation_user_states IS 'Owner-only sidebar preferences, not an access grant. No last_read_at, last_opened_at, tags or folder_id in this approved subset.';

-- User-provided S3 metadata schema, with a real uploader FK.
CREATE TABLE stored_files (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    bucket text NOT NULL,
    object_key text NOT NULL,
    original_name text NOT NULL,
    content_type text NOT NULL,
    visibility text NOT NULL,
    size_bytes bigint NOT NULL,
    checksum_sha256 text,
    uploaded_by uuid REFERENCES users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT uq_stored_files_bucket_object_key UNIQUE (bucket, object_key),
    CONSTRAINT ck_stored_files_bucket CHECK (length(bucket) BETWEEN 3 AND 63
        AND bucket ~ '^[a-z0-9][a-z0-9.-]*[a-z0-9]$' AND bucket !~ '\.\.'),
    CONSTRAINT ck_stored_files_checksum_sha256 CHECK (checksum_sha256 IS NULL OR checksum_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_stored_files_content_type CHECK (btrim(content_type) <> '' AND length(content_type) <= 255),
    CONSTRAINT ck_stored_files_deleted_at CHECK (deleted_at IS NULL OR deleted_at >= created_at),
    CONSTRAINT ck_stored_files_object_key CHECK (octet_length(object_key) BETWEEN 1 AND 1024
        AND object_key !~ '(^|/)\.\.?(/|$)'),
    CONSTRAINT ck_stored_files_original_name CHECK (btrim(original_name) <> '' AND octet_length(original_name) <= 1024),
    CONSTRAINT ck_stored_files_size CHECK (size_bytes >= 0),
    CONSTRAINT ck_stored_files_visibility CHECK (visibility IN ('public','private')),
    CONSTRAINT ck_stored_files_visibility_key CHECK (
        (visibility = 'public' AND object_key LIKE 'public/%') OR
        (visibility = 'private' AND object_key LIKE 'private/%'))
);
CREATE INDEX idx_stored_files_uploaded_by ON stored_files(uploaded_by) WHERE uploaded_by IS NOT NULL;
COMMENT ON TABLE stored_files IS 'S3-compatible object metadata, not ACL. Backend/storage must validate actual object/checksum and enforce no overwrite. Bucket checks are basic application checks, not full vendor validation.';

-- Keep phase-1 files as the workspace resource layer; move physical metadata to
-- stored_files so owner/workspace does not depend on the uploader identity.
DROP TRIGGER immutable_version ON files;
ALTER TABLE files ADD COLUMN stored_file_id uuid NOT NULL UNIQUE REFERENCES stored_files(id) ON DELETE RESTRICT;
ALTER TABLE files DROP COLUMN filename, DROP COLUMN content_type, DROP COLUMN byte_size,
    DROP COLUMN sha256, DROP COLUMN storage_key;
COMMENT ON TABLE files IS 'Workspace-owned chat file resource -> immutable stored_files object. Uploader may differ from resource owner. One object has one chat resource to prevent accidental cross-workspace aliasing.';
CREATE OR REPLACE FUNCTION guard_file_version() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF (NEW.workspace_id, NEW.owner_user_id, NEW.stored_file_id)
        IS DISTINCT FROM (OLD.workspace_id, OLD.owner_user_id, OLD.stored_file_id) THEN
        RAISE EXCEPTION 'File scope and stored object are immutable; create a new resource';
    END IF;
    IF OLD.status = 'ready' AND NEW.status <> 'ready' THEN RAISE EXCEPTION 'Ready file cannot become unready'; END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER immutable_version BEFORE UPDATE ON files FOR EACH ROW EXECUTE FUNCTION guard_file_version();
CREATE FUNCTION guard_chat_object() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE visibility_value text; deleted_value timestamptz;
BEGIN
    SELECT visibility, deleted_at INTO visibility_value, deleted_value FROM chat_app.stored_files
        WHERE id = NEW.stored_file_id FOR SHARE;
    IF NOT FOUND OR visibility_value <> 'private' OR deleted_value IS NOT NULL THEN
        RAISE EXCEPTION 'Chat resource requires a non-deleted private stored object';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER guard_object BEFORE INSERT OR UPDATE ON files FOR EACH ROW EXECUTE FUNCTION guard_chat_object();
CREATE FUNCTION guard_stored_object() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND (
        (NEW.id, NEW.bucket, NEW.object_key, NEW.original_name, NEW.content_type, NEW.visibility, NEW.size_bytes)
        IS DISTINCT FROM
        (OLD.id, OLD.bucket, OLD.object_key, OLD.original_name, OLD.content_type, OLD.visibility, OLD.size_bytes)) THEN
        RAISE EXCEPTION 'Stored object version is immutable';
    END IF;
    IF TG_OP = 'UPDATE' AND OLD.checksum_sha256 IS NOT NULL
       AND NEW.checksum_sha256 IS DISTINCT FROM OLD.checksum_sha256 THEN
        RAISE EXCEPTION 'Verified checksum is immutable';
    END IF;
    -- Metadata soft deletion cannot bypass live/snapshot/job references. Cleanup
    -- removes unreferenced resources first; physical S3 deletion is a separate job.
    IF TG_OP = 'DELETE' OR (NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL) THEN
        IF EXISTS (SELECT 1 FROM chat_app.files WHERE stored_file_id = OLD.id) THEN
            RAISE EXCEPTION 'Stored object is still referenced by a chat resource';
        END IF;
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER immutable_version BEFORE UPDATE OR DELETE ON stored_files FOR EACH ROW EXECUTE FUNCTION guard_stored_object();

ALTER TABLE message_files RENAME TO chat_files;
ALTER TABLE chat_files ADD COLUMN id uuid NOT NULL DEFAULT uuidv7() UNIQUE;
ALTER TABLE chat_files ADD COLUMN kind text NOT NULL DEFAULT 'input' CHECK (kind IN ('input','output'));
ALTER TABLE chat_files ADD COLUMN created_at timestamptz NOT NULL DEFAULT now();
COMMENT ON TABLE chat_files IS 'File links per message, UNIQUE(message_id,file_id); same file can appear on several messages. file_id references files, then stored_file_id resolves S3 metadata. kind is input or output.';

-- Copy availability lives exclusively on copy jobs after removing conversation status.
CREATE OR REPLACE FUNCTION can_read_conversation(p_user uuid, p_conversation uuid) RETURNS boolean LANGUAGE sql STABLE AS $$
    SELECT EXISTS (
        SELECT 1 FROM chat_app.conversations c JOIN chat_app.workspaces w ON w.id = c.workspace_id
        JOIN chat_app.users u ON u.id = p_user AND u.is_active
        WHERE c.id = p_conversation AND c.owner_user_id = p_user AND c.deleted_at IS NULL
          AND NOT EXISTS (SELECT 1 FROM chat_app.conversation_copy_jobs j
              WHERE j.target_conversation_id = c.id AND j.status <> 'completed')
          AND (w.personal_user_id = p_user OR EXISTS (
              SELECT 1 FROM chat_app.organization_members m JOIN chat_app.organizations o ON o.id = m.organization_id
              WHERE m.organization_id = w.organization_id AND m.user_id = p_user AND m.is_active AND o.is_active))
    );
$$;
CREATE OR REPLACE FUNCTION can_read_share_file(p_user uuid, p_share uuid, p_file uuid) RETURNS boolean LANGUAGE sql STABLE AS $$
    SELECT chat_app.can_read_share(p_user, p_share) AND EXISTS (
        SELECT 1 FROM chat_app.conversation_shares s
        JOIN chat_app.share_snapshot_message_files mf ON mf.snapshot_id = s.current_snapshot_id
        JOIN chat_app.files f ON f.id = mf.file_id AND f.status = 'ready'
        JOIN chat_app.stored_files sf ON sf.id = f.stored_file_id AND sf.deleted_at IS NULL
        WHERE s.id = p_share AND mf.file_id = p_file
    );
$$;
CREATE OR REPLACE FUNCTION can_read_conversation_file(p_user uuid, p_conversation uuid, p_file uuid) RETURNS boolean LANGUAGE sql STABLE AS $$
    SELECT chat_app.can_read_conversation(p_user, p_conversation) AND EXISTS (
        SELECT 1 FROM chat_app.chat_files cf
        JOIN chat_app.files f ON f.id = cf.file_id AND f.status = 'ready'
        JOIN chat_app.stored_files sf ON sf.id = f.stored_file_id AND sf.deleted_at IS NULL
        WHERE cf.conversation_id = p_conversation AND cf.file_id = p_file
    );
$$;
CREATE OR REPLACE FUNCTION guard_copy_scope() RETURNS trigger LANGUAGE plpgsql AS $$
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
          AND c.owner_user_id = NEW.requested_by AND c.deleted_at IS NULL
          AND chat_app.can_read_share(NEW.requested_by, s.id)
          AND ((s.mode = 'public' AND w.kind = 'personal' AND w.personal_user_id = NEW.requested_by)
            OR (s.mode = 'organization' AND w.kind = 'organization' AND w.organization_id = s.organization_id))
    ) THEN RAISE EXCEPTION 'Copy not allowed across workspace domains or share unavailable'; END IF;
    IF TG_OP = 'INSERT' AND (EXISTS (SELECT 1 FROM chat_app.messages WHERE conversation_id = NEW.target_conversation_id)
        OR EXISTS (SELECT 1 FROM chat_app.conversation_shares WHERE source_conversation_id = NEW.target_conversation_id)) THEN
        RAISE EXCEPTION 'Copy destination must start empty and unshared; create job before payload in same transaction';
    END IF;
    RETURN NEW;
END;
$$;
CREATE OR REPLACE FUNCTION guard_copy_file() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND (NEW.job_id, NEW.source_file_id, NEW.target_file_id)
        IS DISTINCT FROM (OLD.job_id, OLD.source_file_id, OLD.target_file_id) THEN RAISE EXCEPTION 'Copy file mapping is immutable'; END IF;
    IF NOT EXISTS (
        SELECT 1 FROM chat_app.conversation_copy_jobs j
        JOIN chat_app.share_snapshot_files sf ON sf.snapshot_id = j.snapshot_id AND sf.file_id = NEW.source_file_id
        JOIN chat_app.files src ON src.id = sf.file_id
        JOIN chat_app.files dst ON dst.id = NEW.target_file_id
        JOIN chat_app.stored_files so ON so.id = src.stored_file_id AND so.deleted_at IS NULL
        JOIN chat_app.stored_files dof ON dof.id = dst.stored_file_id AND dof.deleted_at IS NULL
        WHERE j.id = NEW.job_id AND dst.workspace_id = j.target_workspace_id AND dst.owner_user_id = j.requested_by
          AND so.id <> dof.id AND (so.bucket, so.object_key) <> (dof.bucket, dof.object_key)
          AND so.size_bytes = dof.size_bytes AND so.original_name = dof.original_name AND so.content_type = dof.content_type
          AND (NEW.status <> 'copied' OR (dst.status = 'ready' AND so.checksum_sha256 IS NOT NULL
              AND so.checksum_sha256 = dof.checksum_sha256))
    ) THEN RAISE EXCEPTION 'Copy requires independent stored object and verified matching file content'; END IF;
    RETURN NEW;
END;
$$;
CREATE OR REPLACE FUNCTION check_copy_completion() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.status = 'completed' AND EXISTS (
        SELECT 1 FROM chat_app.share_snapshot_files sf
        WHERE sf.snapshot_id = NEW.snapshot_id AND NOT EXISTS (
            SELECT 1 FROM chat_app.conversation_copy_files cf
            WHERE cf.job_id = NEW.id AND cf.source_file_id = sf.file_id AND cf.status = 'copied')
    ) THEN RAISE EXCEPTION 'Complete copies require every snapshot file copied'; END IF;
    RETURN NULL;
END;
$$;

-- A destination of an unfinished copy cannot be shared via raw service writes.
CREATE FUNCTION guard_copy_publication() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM chat_app.conversation_copy_jobs j
        WHERE j.target_conversation_id = NEW.source_conversation_id AND j.status <> 'completed') THEN
        RAISE EXCEPTION 'Incomplete copy cannot be shared';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER guard_copy_publication BEFORE INSERT OR UPDATE ON conversation_shares
    FOR EACH ROW EXECUTE FUNCTION guard_copy_publication();
COMMENT ON SCHEMA chat_app IS 'Phase 1 + approved phase 2 part 1. Service-only access; no automatic auth/RLS. See phase-2-part-1-decisions.md for partial scope and integration duties.';
COMMIT;
