-- Phase 2 FINAL. PostgreSQL 18+. Apply ONCE after phase-1-schema.sql AND
-- phase-2-part-1-schema.sql. Historical scripts stay unchanged.
-- Empty-data design migration, NOT a production backfill.
BEGIN;
SET LOCAL search_path = chat_app, public;
LOCK TABLE conversations, messages, chat_files, files, stored_files,
    conversation_shares, share_snapshots, share_snapshot_messages,
    share_snapshot_files, share_snapshot_message_files,
    conversation_copy_jobs, conversation_copy_files, conversation_user_states
    IN ACCESS EXCLUSIVE MODE;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM messages) OR EXISTS (SELECT 1 FROM files)
       OR EXISTS (SELECT 1 FROM stored_files) OR EXISTS (SELECT 1 FROM conversation_shares)
       OR EXISTS (SELECT 1 FROM share_snapshots) OR EXISTS (SELECT 1 FROM conversation_copy_jobs) THEN
        RAISE EXCEPTION 'Phase 2 final requires empty message/file/share/copy data; prepare a separate explicit backfill';
    END IF;
END;
$$;

-- Sidebar: one owner per conversation; folders are private, flat, scope-bound.
ALTER TABLE conversations ADD COLUMN pinned_at timestamptz,
    ADD COLUMN archived_at timestamptz, ADD COLUMN folder_id uuid;
UPDATE conversations c SET pinned_at = s.pinned_at, archived_at = s.archived_at
FROM conversation_user_states s WHERE s.conversation_id = c.id;
DROP TABLE conversation_user_states;
CREATE TABLE conversation_folders (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE RESTRICT,
    owner_user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    name text NOT NULL CHECK (btrim(name) <> ''),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (id, workspace_id, owner_user_id)
);
CREATE UNIQUE INDEX conversation_folders_name_idx
    ON conversation_folders(workspace_id, owner_user_id, lower(btrim(name)));
CREATE INDEX conversation_folders_owner_idx ON conversation_folders(owner_user_id, workspace_id);
CREATE TRIGGER guard_scope BEFORE INSERT OR UPDATE ON conversation_folders
    FOR EACH ROW EXECUTE FUNCTION guard_conversation_scope();
CREATE TRIGGER touch_updated_at BEFORE UPDATE ON conversation_folders
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
ALTER TABLE conversations ADD CONSTRAINT conversations_folder_scope_fk
    FOREIGN KEY (folder_id, workspace_id, owner_user_id)
    REFERENCES conversation_folders(id, workspace_id, owner_user_id)
    ON DELETE SET NULL (folder_id);
CREATE INDEX idx_conversations_pinned
    ON conversations(workspace_id, owner_user_id, pinned_at DESC, id DESC)
    WHERE pinned_at IS NOT NULL AND deleted_at IS NULL AND archived_at IS NULL;
CREATE INDEX idx_conversations_folder
    ON conversations(workspace_id, owner_user_id, folder_id, updated_at DESC, id DESC)
    WHERE folder_id IS NOT NULL AND deleted_at IS NULL AND archived_at IS NULL;
-- Full FK access path also covers archived/deleted conversations during folder deletion.
CREATE INDEX conversations_folder_fk_idx ON conversations(folder_id, workspace_id, owner_user_id);
COMMENT ON TABLE conversation_folders IS 'Flat personal organization of chats inside one workspace; no parent_id, shared-folder ACL, instructions or RAG project behavior.';
COMMENT ON TABLE conversations IS 'One owner per conversation; pin/archive/folder stored here. current_message_id is saved branch tip, not a live execution ID.';

-- Message lifecycle. User pending is a staging state ONLY inside its creation
-- transaction: attach files, then set completed before commit. This gives both
-- user and assistant messages the same terminal attachment immutability rule.
ALTER TABLE messages ADD COLUMN status text NOT NULL DEFAULT 'pending',
    ADD CONSTRAINT messages_status_check CHECK (status IN ('pending','running','completed','failed','cancelled')),
    ADD CONSTRAINT messages_user_status_check CHECK (role <> 'user' OR status IN ('pending','completed'));
CREATE UNIQUE INDEX messages_one_active_assistant_idx ON messages(conversation_id)
    WHERE role = 'assistant' AND status IN ('pending','running');
ALTER TABLE share_snapshot_messages ADD COLUMN status text NOT NULL DEFAULT 'completed',
    ADD CONSTRAINT snapshot_message_status_check CHECK (status IN ('completed','failed','cancelled')),
    ADD CONSTRAINT snapshot_user_status_check CHECK (role <> 'user' OR status = 'completed');
CREATE FUNCTION guard_message_lifecycle() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(hashtextextended(NEW.conversation_id::text, 42));
    IF TG_OP = 'UPDATE' THEN
        IF OLD.status IN ('completed','failed','cancelled') THEN
            RAISE EXCEPTION 'Terminal message is immutable; edit/regenerate creates a new branch';
        END IF;
        IF OLD.status = 'running' AND NEW.status = 'pending' THEN
            RAISE EXCEPTION 'Running message cannot return to pending';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER guard_lifecycle BEFORE INSERT OR UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION guard_message_lifecycle();
CREATE FUNCTION check_user_message_final() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM chat_app.messages WHERE id = NEW.id AND role = 'user' AND status <> 'completed') THEN
        RAISE EXCEPTION 'User message must be completed in the same transaction as creation and file links';
    END IF;
    RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER user_message_final AFTER INSERT OR UPDATE ON messages
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_user_message_final();
COMMENT ON COLUMN messages.status IS 'User: stage pending + attach files + completed in ONE transaction. Assistant: pending -> running -> completed/failed/cancelled. Persist partial output on caught error/stop. No crash recovery in phase 2.';

-- Remove both intermediary chat resource tables. Rewire all snapshot/copy FKs.
DROP TABLE chat_files;
DO $$
DECLARE r record;
BEGIN
    FOR r IN SELECT conrelid::regclass AS tbl, conname FROM pg_constraint
        WHERE contype = 'f' AND confrelid = 'chat_app.files'::regclass LOOP
        EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', r.tbl, r.conname);
    END LOOP;
END;
$$;
DROP TABLE files;
DROP FUNCTION guard_file_version();
DROP FUNCTION guard_chat_object();
ALTER TABLE stored_files ADD COLUMN metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    ADD CONSTRAINT stored_files_metadata_object_check CHECK (jsonb_typeof(metadata) = 'object');
COMMENT ON COLUMN stored_files.metadata IS 'Optional extensible object: image/extraction/preview/RAG descriptors. Not ACL; no secrets, presigned URLs, vectors or chunk corpus. No speculative GIN index.';
CREATE TABLE message_files (
    message_id uuid NOT NULL REFERENCES messages(id) ON DELETE RESTRICT,
    stored_file_id uuid NOT NULL REFERENCES stored_files(id) ON DELETE RESTRICT,
    PRIMARY KEY (message_id, stored_file_id)
);
CREATE INDEX message_files_stored_file_idx ON message_files(stored_file_id);
COMMENT ON TABLE message_files IS 'Authoritative many-to-many links. Resolve conversation/owner/workspace through messages. No extra files/chat_files table, kind or file status.';
ALTER TABLE share_snapshot_files RENAME COLUMN file_id TO stored_file_id;
ALTER TABLE share_snapshot_message_files RENAME COLUMN file_id TO stored_file_id;
ALTER TABLE conversation_copy_files RENAME COLUMN source_file_id TO source_stored_file_id;
ALTER TABLE conversation_copy_files RENAME COLUMN target_file_id TO target_stored_file_id;
ALTER TABLE share_snapshot_files ADD CONSTRAINT snapshot_stored_file_fk
    FOREIGN KEY (stored_file_id) REFERENCES stored_files(id) ON DELETE RESTRICT;
ALTER TABLE conversation_copy_files ADD CONSTRAINT copy_source_stored_file_fk
    FOREIGN KEY (source_stored_file_id) REFERENCES stored_files(id) ON DELETE RESTRICT,
    ADD CONSTRAINT copy_target_stored_file_fk
    FOREIGN KEY (target_stored_file_id) REFERENCES stored_files(id) ON DELETE RESTRICT;

-- All file association writers acquire the object-row lock, then check scope.
-- Upload attribution is an extra guard, not an ACL; service authenticates user,
-- verifies upload workspace/token, actual S3 object and its bytes before linking.
CREATE FUNCTION assert_chat_file_scope(p_file uuid, p_workspace uuid, p_owner uuid) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE f chat_app.stored_files%ROWTYPE;
BEGIN
    SELECT * INTO f FROM chat_app.stored_files WHERE id = p_file FOR UPDATE;
    IF NOT FOUND OR f.visibility <> 'private' OR f.deleted_at IS NOT NULL THEN
        RAISE EXCEPTION 'Chat requires a non-deleted private stored object';
    END IF;
    IF f.uploaded_by IS DISTINCT FROM p_owner THEN
        RAISE EXCEPTION 'First-party chat object must be attributed to conversation owner; copies use new objects';
    END IF;
    IF EXISTS (
        SELECT 1 FROM chat_app.message_files mf JOIN chat_app.messages m ON m.id = mf.message_id
        JOIN chat_app.conversations c ON c.id = m.conversation_id
        WHERE mf.stored_file_id = p_file AND (c.workspace_id, c.owner_user_id) <> (p_workspace, p_owner)
    ) OR EXISTS (
        SELECT 1 FROM chat_app.share_snapshot_files sf
        JOIN chat_app.share_snapshots ss ON ss.id = sf.snapshot_id
        JOIN chat_app.conversation_shares s ON s.id = ss.share_id
        JOIN chat_app.conversations c ON c.id = s.source_conversation_id
        WHERE sf.stored_file_id = p_file AND (c.workspace_id, c.owner_user_id) <> (p_workspace, p_owner)
    ) OR EXISTS (
        SELECT 1 FROM chat_app.conversation_copy_files cf
        JOIN chat_app.conversation_copy_jobs j ON j.id = cf.job_id
        WHERE cf.target_stored_file_id = p_file
          AND (j.target_workspace_id, j.requested_by) <> (p_workspace, p_owner)
    ) THEN RAISE EXCEPTION 'Stored object cannot be reused across chat owners/workspaces'; END IF;
END;
$$;
CREATE FUNCTION guard_message_file() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE mid uuid; cid uuid; wid uuid; uid uuid; state text;
BEGIN
    IF TG_OP = 'UPDATE' THEN RAISE EXCEPTION 'Replace links with delete/insert while message is nonterminal'; END IF;
    mid := CASE WHEN TG_OP = 'DELETE' THEN OLD.message_id ELSE NEW.message_id END;
    SELECT conversation_id INTO cid FROM chat_app.messages WHERE id = mid;
    IF NOT FOUND THEN RAISE EXCEPTION 'Message not found'; END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(cid::text, 42));
    SELECT m.status, c.workspace_id, c.owner_user_id INTO state, wid, uid
        FROM chat_app.messages m JOIN chat_app.conversations c ON c.id = m.conversation_id
        WHERE m.id = mid FOR UPDATE OF m;
    IF state IN ('completed','failed','cancelled') THEN
        RAISE EXCEPTION 'Terminal message file links are immutable; attach before finalization';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    PERFORM chat_app.assert_chat_file_scope(NEW.stored_file_id, wid, uid);
    RETURN NEW;
END;
$$;
CREATE TRIGGER guard_link BEFORE INSERT OR UPDATE OR DELETE ON message_files
    FOR EACH ROW EXECUTE FUNCTION guard_message_file();
CREATE TRIGGER no_truncate BEFORE TRUNCATE ON message_files
    FOR EACH STATEMENT EXECUTE FUNCTION forbid_message_delete();
CREATE OR REPLACE FUNCTION guard_stored_object() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND (NEW.id, NEW.bucket, NEW.object_key, NEW.original_name, NEW.content_type, NEW.visibility, NEW.size_bytes)
        IS DISTINCT FROM (OLD.id, OLD.bucket, OLD.object_key, OLD.original_name, OLD.content_type, OLD.visibility, OLD.size_bytes) THEN
        RAISE EXCEPTION 'Stored object identity is immutable';
    END IF;
    IF TG_OP = 'UPDATE' AND OLD.checksum_sha256 IS NOT NULL
        AND NEW.checksum_sha256 IS DISTINCT FROM OLD.checksum_sha256 THEN
        RAISE EXCEPTION 'Verified checksum is immutable';
    END IF;
    IF TG_OP = 'DELETE' OR (NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL) THEN
        IF EXISTS (SELECT 1 FROM chat_app.message_files WHERE stored_file_id = OLD.id)
           OR EXISTS (SELECT 1 FROM chat_app.share_snapshot_files WHERE stored_file_id = OLD.id)
           OR EXISTS (SELECT 1 FROM chat_app.conversation_copy_files
               WHERE source_stored_file_id = OLD.id OR target_stored_file_id = OLD.id) THEN
            RAISE EXCEPTION 'Stored object still referenced by message/snapshot/copy';
        END IF;
    END IF;
    -- Metadata can evolve for processing; it must never carry access grants.
    -- Snapshot metadata is frozen separately below.
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$$;

-- Preserve public-safe file metadata as part of the immutable share version.
-- Backend fills an allowlisted subset, not raw processing/sandbox metadata.
ALTER TABLE share_snapshot_files ADD COLUMN metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    ADD CONSTRAINT snapshot_file_metadata_object_check CHECK (jsonb_typeof(metadata) = 'object');
CREATE OR REPLACE FUNCTION guard_snapshot_file() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE wid uuid; uid uuid; cid uuid;
BEGIN
    SELECT c.workspace_id, c.owner_user_id, c.id INTO wid, uid, cid
        FROM chat_app.share_snapshots ss JOIN chat_app.conversation_shares s ON s.id = ss.share_id
        JOIN chat_app.conversations c ON c.id = s.source_conversation_id WHERE ss.id = NEW.snapshot_id;
    IF NOT FOUND OR wid <> NEW.workspace_id THEN RAISE EXCEPTION 'Snapshot file scope mismatch'; END IF;
    PERFORM chat_app.assert_chat_file_scope(NEW.stored_file_id, wid, uid);
    IF NOT EXISTS (SELECT 1 FROM chat_app.message_files mf JOIN chat_app.messages m ON m.id = mf.message_id
        WHERE mf.stored_file_id = NEW.stored_file_id AND m.conversation_id = cid) THEN
        RAISE EXCEPTION 'Snapshot file must belong to source conversation';
    END IF;
    RETURN NEW;
END;
$$;
CREATE OR REPLACE FUNCTION can_read_share_file(p_user uuid, p_share uuid, p_file uuid) RETURNS boolean
LANGUAGE sql STABLE AS $$
    SELECT chat_app.can_read_share(p_user, p_share) AND EXISTS (
        SELECT 1 FROM chat_app.conversation_shares s
        JOIN chat_app.share_snapshot_message_files mf ON mf.snapshot_id = s.current_snapshot_id
        JOIN chat_app.stored_files f ON f.id = mf.stored_file_id AND f.deleted_at IS NULL
        WHERE s.id = p_share AND mf.stored_file_id = p_file
    );
$$;
CREATE OR REPLACE FUNCTION can_read_conversation_file(p_user uuid, p_conversation uuid, p_file uuid) RETURNS boolean
LANGUAGE sql STABLE AS $$
    SELECT chat_app.can_read_conversation(p_user, p_conversation) AND EXISTS (
        SELECT 1 FROM chat_app.message_files mf JOIN chat_app.messages m ON m.id = mf.message_id
        JOIN chat_app.stored_files f ON f.id = mf.stored_file_id AND f.deleted_at IS NULL
        WHERE m.conversation_id = p_conversation AND mf.stored_file_id = p_file
    );
$$;

-- Serialize active execution and snapshot publication on the same conversation
-- lock as message creation/finalization. READ COMMITTED service locks BEFORE
-- reading the source tree. A published old snapshot stays readable during new runs.
CREATE FUNCTION assert_conversation_idle(p_conversation uuid) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(hashtextextended(p_conversation::text, 42));
    IF EXISTS (SELECT 1 FROM chat_app.messages WHERE conversation_id = p_conversation
        AND status IN ('pending','running')) THEN
        RAISE EXCEPTION 'Cannot build/publish snapshot while a message is pending/running';
    END IF;
END;
$$;
CREATE FUNCTION guard_snapshot_idle() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE cid uuid;
BEGIN
    SELECT s.source_conversation_id INTO cid FROM chat_app.conversation_shares s WHERE s.id = NEW.share_id;
    PERFORM chat_app.assert_conversation_idle(cid);
    RETURN NEW;
END;
$$;
CREATE TRIGGER guard_idle BEFORE INSERT OR UPDATE ON share_snapshots
    FOR EACH ROW EXECUTE FUNCTION guard_snapshot_idle();
CREATE OR REPLACE FUNCTION guard_copy_publication() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    -- Revocation/expiry maintenance remains possible during an active answer.
    IF TG_OP = 'INSERT' OR NEW.current_snapshot_id IS DISTINCT FROM OLD.current_snapshot_id THEN
        PERFORM chat_app.assert_conversation_idle(NEW.source_conversation_id);
        IF EXISTS (SELECT 1 FROM chat_app.conversation_copy_jobs j
            WHERE j.target_conversation_id = NEW.source_conversation_id AND j.status <> 'completed') THEN
            RAISE EXCEPTION 'Incomplete copy cannot be shared';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
CREATE OR REPLACE FUNCTION guard_copy_file() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE wid uuid; uid uuid;
BEGIN
    IF TG_OP = 'UPDATE' AND (NEW.job_id, NEW.source_stored_file_id, NEW.target_stored_file_id)
        IS DISTINCT FROM (OLD.job_id, OLD.source_stored_file_id, OLD.target_stored_file_id) THEN
        RAISE EXCEPTION 'Copy mapping is immutable';
    END IF;
    SELECT target_workspace_id, requested_by INTO wid, uid FROM chat_app.conversation_copy_jobs WHERE id = NEW.job_id;
    PERFORM chat_app.assert_chat_file_scope(NEW.target_stored_file_id, wid, uid);
    IF NOT EXISTS (
        SELECT 1 FROM chat_app.conversation_copy_jobs j
        JOIN chat_app.share_snapshot_files sf ON sf.snapshot_id = j.snapshot_id AND sf.stored_file_id = NEW.source_stored_file_id
        JOIN chat_app.stored_files src ON src.id = sf.stored_file_id AND src.deleted_at IS NULL
        JOIN chat_app.stored_files dst ON dst.id = NEW.target_stored_file_id AND dst.deleted_at IS NULL
        WHERE j.id = NEW.job_id AND src.id <> dst.id AND (src.bucket, src.object_key) <> (dst.bucket, dst.object_key)
          AND src.size_bytes = dst.size_bytes AND src.original_name = dst.original_name AND src.content_type = dst.content_type
          AND (NEW.status <> 'copied' OR (src.checksum_sha256 IS NOT NULL AND src.checksum_sha256 = dst.checksum_sha256))
    ) THEN RAISE EXCEPTION 'Copy requires independent stored object and matching verified bytes'; END IF;
    RETURN NEW;
END;
$$;
CREATE OR REPLACE FUNCTION check_copy_completion() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE state text; target uuid;
BEGIN
    -- Deferred trigger checks final row, not an intermediate status from earlier
    -- UPDATE events queued in this transaction.
    SELECT status, target_conversation_id INTO state, target FROM chat_app.conversation_copy_jobs WHERE id = NEW.id;
    IF state = 'completed' AND EXISTS (
        SELECT 1 FROM chat_app.share_snapshot_files sf WHERE sf.snapshot_id = NEW.snapshot_id AND NOT EXISTS (
            SELECT 1 FROM chat_app.conversation_copy_files cf
            JOIN chat_app.message_files mf ON mf.stored_file_id = cf.target_stored_file_id
            JOIN chat_app.messages m ON m.id = mf.message_id AND m.conversation_id = target
            WHERE cf.job_id = NEW.id AND cf.source_stored_file_id = sf.stored_file_id AND cf.status = 'copied')
    ) THEN RAISE EXCEPTION 'Every snapshot file must be copied and attached to destination'; END IF;
    IF state = 'completed' AND EXISTS (SELECT 1 FROM chat_app.messages WHERE conversation_id = target AND status IN ('pending','running')) THEN
        RAISE EXCEPTION 'Copy destination must contain only terminal transcript messages';
    END IF;
    RETURN NULL;
END;
$$;
COMMENT ON TABLE share_snapshot_files IS 'Immutable snapshot file manifest; stored_file_id -> stored_files, metadata is backend-allowlisted snapshot, never live raw metadata.';
COMMENT ON TABLE conversation_copy_files IS 'Physical copy mapping between stored_files rows. Worker copies S3 bytes to a NEW object key; DB cannot verify remote bytes itself. Separate from LLM execution.';
COMMENT ON SCHEMA chat_app IS 'Phase 2 finalized: flat folders/pin, terminal message lifecycle, message_files -> stored_files(metadata). Service-only; no runtime RLS. See phase-2-decisions.md.';
COMMIT;
