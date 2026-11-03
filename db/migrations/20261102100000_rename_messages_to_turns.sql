-- migrate:up
-- A row of the conversation tree is a turn: one user question, or one AI
-- answer with its tool calls, reasoning and reply (QD-33). "Message" now
-- means only an AG-UI message inside a turn's content. Renamed in place:
-- ids, data and checkpoints are unchanged.

ALTER TABLE chat_app.share_snapshot_message_files RENAME TO share_snapshot_turn_files;
ALTER TABLE chat_app.share_snapshot_messages RENAME TO share_snapshot_turns;
ALTER TABLE chat_app.message_files RENAME TO turn_files;
ALTER TABLE chat_app.messages RENAME TO turns;

ALTER TABLE chat_app.turns RENAME COLUMN parent_message_id TO parent_turn_id;
ALTER TABLE chat_app.turn_files RENAME COLUMN message_id TO turn_id;
ALTER TABLE chat_app.share_snapshot_turns RENAME COLUMN parent_message_id TO parent_turn_id;
ALTER TABLE chat_app.share_snapshot_turn_files RENAME COLUMN message_id TO turn_id;
ALTER TABLE chat_app.conversations RENAME COLUMN current_message_id TO current_turn_id;
ALTER TABLE chat_app.share_snapshots RENAME COLUMN current_message_id TO current_turn_id;

DO $$
DECLARE r record;
BEGIN
    FOR r IN
        SELECT c.conrelid::regclass AS rel, c.conname
        FROM pg_constraint c
        WHERE c.conrelid IN (SELECT unnest(ARRAY['chat_app.turns', 'chat_app.turn_files', 'chat_app.share_snapshot_turns', 'chat_app.share_snapshot_turn_files', 'chat_app.conversations', 'chat_app.share_snapshots'])::regclass)
          AND c.conname ~ 'message'
    LOOP
        EXECUTE format('ALTER TABLE %s RENAME CONSTRAINT %I TO %I',
            r.rel, r.conname, regexp_replace(r.conname, 'message', 'turn', 'g'));
    END LOOP;
    FOR r IN
        SELECT i.indexname
        FROM pg_indexes i
        WHERE i.schemaname = 'chat_app' AND i.indexname ~ 'message'
    LOOP
        EXECUTE format('ALTER INDEX chat_app.%I RENAME TO %I',
            r.indexname, regexp_replace(r.indexname, 'message', 'turn', 'g'));
    END LOOP;
END
$$;

ALTER FUNCTION chat_app.check_message_tree() RENAME TO check_turn_tree;
ALTER FUNCTION chat_app.check_user_message_final() RENAME TO check_user_turn_final;
ALTER FUNCTION chat_app.forbid_message_delete() RENAME TO forbid_turn_delete;
ALTER FUNCTION chat_app.guard_message_file() RENAME TO guard_turn_file;
ALTER FUNCTION chat_app.guard_message_lifecycle() RENAME TO guard_turn_lifecycle;
ALTER FUNCTION chat_app.lock_message_tree() RENAME TO lock_turn_tree;

ALTER TRIGGER user_message_final ON chat_app.turns RENAME TO user_turn_final;
ALTER FUNCTION chat_app.message_text(jsonb) RENAME TO turn_text;

-- Function bodies are stored as text: rewrite every one naming the old objects.
CREATE OR REPLACE FUNCTION chat_app.assert_chat_file_scope(p_file uuid, p_workspace uuid, p_owner uuid) RETURNS void
    LANGUAGE plpgsql
    AS $$
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
        SELECT 1 FROM chat_app.turn_files mf JOIN chat_app.turns m ON m.id = mf.turn_id
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

CREATE OR REPLACE FUNCTION chat_app.assert_conversation_idle(p_conversation uuid) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(hashtextextended(p_conversation::text,42));
    IF EXISTS (SELECT 1 FROM chat_app.turns WHERE conversation_id=p_conversation
        AND status IN ('pending','running','requires_action')) THEN
        RAISE EXCEPTION 'Cannot build/publish snapshot while a response is unfinished';
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.can_read_conversation_file(p_user uuid, p_conversation uuid, p_file uuid) RETURNS boolean
    LANGUAGE sql STABLE
    AS $$
    SELECT chat_app.can_read_conversation(p_user, p_conversation) AND EXISTS (
        SELECT 1 FROM chat_app.turn_files mf JOIN chat_app.turns m ON m.id = mf.turn_id
        JOIN chat_app.stored_files f ON f.id = mf.stored_file_id AND f.deleted_at IS NULL
        WHERE m.conversation_id = p_conversation AND mf.stored_file_id = p_file
    );
$$;

CREATE OR REPLACE FUNCTION chat_app.can_read_share_file(p_user uuid, p_share uuid, p_file uuid) RETURNS boolean
    LANGUAGE sql STABLE
    AS $$
    SELECT chat_app.can_read_share(p_user, p_share) AND EXISTS (
        SELECT 1 FROM chat_app.conversation_shares s
        JOIN chat_app.share_snapshot_turn_files mf ON mf.snapshot_id = s.current_snapshot_id
        JOIN chat_app.stored_files f ON f.id = mf.stored_file_id AND f.deleted_at IS NULL
        WHERE s.id = p_share AND mf.stored_file_id = p_file
    );
$$;

CREATE OR REPLACE FUNCTION chat_app.check_copy_completion() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE state text; target uuid;
BEGIN
    SELECT status,target_conversation_id INTO state,target FROM chat_app.conversation_copy_jobs WHERE id=NEW.id;
    IF state='completed' AND EXISTS (
        SELECT 1 FROM chat_app.share_snapshot_files sf WHERE sf.snapshot_id=NEW.snapshot_id AND NOT EXISTS (
            SELECT 1 FROM chat_app.conversation_copy_files cf
            JOIN chat_app.turn_files mf ON mf.stored_file_id=cf.target_stored_file_id
            JOIN chat_app.turns m ON m.id=mf.turn_id AND m.conversation_id=target
            WHERE cf.job_id=NEW.id AND cf.source_stored_file_id=sf.stored_file_id AND cf.status='copied')
    ) THEN RAISE EXCEPTION 'Every snapshot file must be copied and attached to destination'; END IF;
    IF state='completed' AND EXISTS (SELECT 1 FROM chat_app.turns WHERE conversation_id=target
        AND status IN ('pending','running','requires_action')) THEN
        RAISE EXCEPTION 'Copy destination must contain only terminal turns';
    END IF;
    RETURN NULL;
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.check_turn_tree() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE bad boolean;
BEGIN
    IF TG_TABLE_NAME = 'turns' THEN
        WITH RECURSIVE ancestry AS (
            SELECT m.id, m.parent_turn_id, ARRAY[m.id] AS path, false AS cyclic
            FROM chat_app.turns m WHERE m.conversation_id = NEW.conversation_id AND m.id = NEW.id
            UNION ALL
            SELECT p.id, p.parent_turn_id, a.path || p.id, p.id = ANY(a.path)
            FROM ancestry a JOIN chat_app.turns p
              ON p.id = a.parent_turn_id AND p.conversation_id = NEW.conversation_id
            WHERE NOT a.cyclic
        ) SELECT EXISTS (SELECT 1 FROM ancestry WHERE cyclic) INTO bad;
    ELSE
        WITH RECURSIVE ancestry AS (
            SELECT m.id, m.parent_turn_id, ARRAY[m.id] AS path, false AS cyclic
            FROM chat_app.share_snapshot_turns m WHERE m.snapshot_id = NEW.snapshot_id AND m.id = NEW.id
            UNION ALL
            SELECT p.id, p.parent_turn_id, a.path || p.id, p.id = ANY(a.path)
            FROM ancestry a JOIN chat_app.share_snapshot_turns p
              ON p.id = a.parent_turn_id AND p.snapshot_id = NEW.snapshot_id
            WHERE NOT a.cyclic
        ) SELECT EXISTS (SELECT 1 FROM ancestry WHERE cyclic) INTO bad;
    END IF;
    IF bad THEN RAISE EXCEPTION 'Message parent cycle detected'; END IF;
    RETURN NULL;
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.check_user_turn_final() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM chat_app.turns WHERE id = NEW.id AND role = 'user' AND status <> 'completed') THEN
        RAISE EXCEPTION 'User turn must be completed in the same transaction as creation and file links';
    END IF;
    RETURN NULL;
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.forbid_turn_delete() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    RAISE EXCEPTION 'Individual turn deletion/truncation is disabled; conversation uses soft delete';
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.guard_copy_scope() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
    IF TG_OP = 'INSERT' AND (EXISTS (SELECT 1 FROM chat_app.turns WHERE conversation_id = NEW.target_conversation_id)
        OR EXISTS (SELECT 1 FROM chat_app.conversation_shares WHERE source_conversation_id = NEW.target_conversation_id)) THEN
        RAISE EXCEPTION 'Copy destination must start empty and unshared; create job before payload in same transaction';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.guard_turn_file() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE mid uuid; cid uuid; wid uuid; uid uuid; state text;
BEGIN
    IF TG_OP = 'UPDATE' THEN RAISE EXCEPTION 'Replace links with delete/insert while turn is nonterminal'; END IF;
    mid := CASE WHEN TG_OP = 'DELETE' THEN OLD.turn_id ELSE NEW.turn_id END;
    SELECT conversation_id INTO cid FROM chat_app.turns WHERE id = mid;
    IF NOT FOUND THEN RAISE EXCEPTION 'Message not found'; END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(cid::text, 42));
    SELECT m.status, c.workspace_id, c.owner_user_id INTO state, wid, uid
        FROM chat_app.turns m JOIN chat_app.conversations c ON c.id = m.conversation_id
        WHERE m.id = mid FOR UPDATE OF m;
    IF state IN ('completed','failed','cancelled') THEN
        RAISE EXCEPTION 'Terminal turn file links are immutable; attach before finalization';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    PERFORM chat_app.assert_chat_file_scope(NEW.stored_file_id, wid, uid);
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.guard_turn_lifecycle() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(hashtextextended(NEW.conversation_id::text, 42));
    IF TG_OP = 'UPDATE' THEN
        IF OLD.status IN ('completed','failed','cancelled') THEN
            RAISE EXCEPTION 'Terminal turn is immutable; edit/regenerate creates a new branch';
        END IF;
        IF OLD.status = 'running' AND NEW.status = 'pending' THEN
            RAISE EXCEPTION 'Running turn cannot return to pending';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.guard_snapshot_file() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE wid uuid; uid uuid; cid uuid;
BEGIN
    SELECT c.workspace_id, c.owner_user_id, c.id INTO wid, uid, cid
        FROM chat_app.share_snapshots ss JOIN chat_app.conversation_shares s ON s.id = ss.share_id
        JOIN chat_app.conversations c ON c.id = s.source_conversation_id WHERE ss.id = NEW.snapshot_id;
    IF NOT FOUND OR wid <> NEW.workspace_id THEN RAISE EXCEPTION 'Snapshot file scope mismatch'; END IF;
    PERFORM chat_app.assert_chat_file_scope(NEW.stored_file_id, wid, uid);
    IF NOT EXISTS (SELECT 1 FROM chat_app.turn_files mf JOIN chat_app.turns m ON m.id = mf.turn_id
        WHERE mf.stored_file_id = NEW.stored_file_id AND m.conversation_id = cid) THEN
        RAISE EXCEPTION 'Snapshot file must belong to source conversation';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.guard_snapshot_header() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
        NEW.current_turn_id IS NULL OR NOT EXISTS (
            SELECT 1 FROM chat_app.share_snapshot_turns WHERE snapshot_id = NEW.id)
    ) THEN RAISE EXCEPTION 'A sealed snapshot needs turns and an active turn'; END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.guard_stored_object() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
        IF EXISTS (SELECT 1 FROM chat_app.turn_files WHERE stored_file_id = OLD.id)
           OR EXISTS (SELECT 1 FROM chat_app.share_snapshot_files WHERE stored_file_id = OLD.id)
           OR EXISTS (SELECT 1 FROM chat_app.conversation_copy_files
               WHERE source_stored_file_id = OLD.id OR target_stored_file_id = OLD.id) THEN
            RAISE EXCEPTION 'Stored object still referenced by turn/snapshot/copy';
        END IF;
    END IF;
    -- Metadata can evolve for processing; it must never carry access grants.
    -- Snapshot metadata is frozen separately below.
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.lock_turn_tree() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND (NEW.id, NEW.conversation_id, NEW.parent_turn_id, NEW.role, NEW.created_at)
        IS DISTINCT FROM (OLD.id, OLD.conversation_id, OLD.parent_turn_id, OLD.role, OLD.created_at) THEN
        RAISE EXCEPTION 'Message identity, parent, role and creation time are immutable; create a new branch';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(NEW.conversation_id::text, 42));
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.turn_text(p_content jsonb) RETURNS text
    LANGUAGE sql IMMUTABLE PARALLEL SAFE
    AS $$
    SELECT coalesce(string_agg(part, ' '), '')
    FROM (
        SELECT m.value ->> 'content' AS part
        FROM jsonb_array_elements(
            CASE WHEN jsonb_typeof(p_content) = 'array' THEN p_content ELSE '[]'::jsonb END
        ) AS m
        WHERE m.value ->> 'role' IN ('user', 'assistant')
          AND jsonb_typeof(m.value -> 'content') = 'string'
        UNION ALL
        SELECT p.value ->> 'text'
        FROM jsonb_array_elements(
            CASE WHEN jsonb_typeof(p_content) = 'array' THEN p_content ELSE '[]'::jsonb END
        ) AS m
        CROSS JOIN LATERAL jsonb_array_elements(
            CASE WHEN jsonb_typeof(m.value -> 'content') = 'array' THEN m.value -> 'content' ELSE '[]'::jsonb END
        ) AS p
        WHERE m.value ->> 'role' = 'user' AND p.value ->> 'type' = 'text'
    ) AS parts;
$$;

COMMENT ON SCHEMA chat_app IS 'Phase 2 finalized: flat folders/pin, terminal turn lifecycle, turn_files -> stored_files(metadata). Service-only; no runtime RLS. See phase-2-decisions.md.';
COMMENT ON FUNCTION chat_app.turn_text(p_content jsonb) IS 'Searchable text of a turn AG-UI bundle (C09): user/assistant text only, never reasoning or tool payloads.';
COMMENT ON TABLE chat_app.conversations IS 'One owner per conversation; pin/archive/folder stored here. current_turn_id is saved branch tip, not a live execution ID.';
COMMENT ON TABLE chat_app.turn_files IS 'Authoritative many-to-many links. Resolve conversation/owner/workspace through turns. No extra files/chat_files table, kind or file status.';
COMMENT ON COLUMN chat_app.turns.content IS 'Ordered AG-UI Message[] for one logical user/assistant UI row; includes toolCalls and tool results, not raw SSE token events. Backend performs SDK validation and ID/call consistency checks.';
COMMENT ON COLUMN chat_app.turns.attachments IS 'App-owned JSON metadata for citations, sources and artifacts. Full tool output MAY duplicate content by explicit product decision; model context uses content once.';
COMMENT ON COLUMN chat_app.turns.status IS 'pending/running/requires_action are nonterminal. Pause persists partial content and checkpoint atomically; completed/failed/cancelled are immutable.';
COMMENT ON COLUMN chat_app.turns.metadata IS 'Backend-owned action/checkpoint state and resolved interactions. No client-controlled checkpoint pointers or credentials. Terminal turns remain immutable.';
COMMENT ON COLUMN chat_app.share_snapshot_turns.attachments IS 'Snapshot must preserve both attachments and content and remap embedded file/turn/tool IDs when copied.';

-- migrate:down
ALTER TABLE chat_app.turns RENAME COLUMN parent_turn_id TO parent_message_id;
ALTER TABLE chat_app.turn_files RENAME COLUMN turn_id TO message_id;
ALTER TABLE chat_app.share_snapshot_turns RENAME COLUMN parent_turn_id TO parent_message_id;
ALTER TABLE chat_app.share_snapshot_turn_files RENAME COLUMN turn_id TO message_id;
ALTER TABLE chat_app.conversations RENAME COLUMN current_turn_id TO current_message_id;
ALTER TABLE chat_app.share_snapshots RENAME COLUMN current_turn_id TO current_message_id;

ALTER TABLE chat_app.turns RENAME TO messages;
ALTER TABLE chat_app.turn_files RENAME TO message_files;
ALTER TABLE chat_app.share_snapshot_turns RENAME TO share_snapshot_messages;
ALTER TABLE chat_app.share_snapshot_turn_files RENAME TO share_snapshot_message_files;

DO $$
DECLARE r record;
BEGIN
    FOR r IN
        SELECT c.conrelid::regclass AS rel, c.conname
        FROM pg_constraint c
        WHERE c.conrelid IN (SELECT unnest(ARRAY['chat_app.messages', 'chat_app.message_files', 'chat_app.share_snapshot_messages', 'chat_app.share_snapshot_message_files', 'chat_app.conversations', 'chat_app.share_snapshots'])::regclass)
          AND c.conname ~ 'turn'
    LOOP
        EXECUTE format('ALTER TABLE %s RENAME CONSTRAINT %I TO %I',
            r.rel, r.conname, regexp_replace(r.conname, 'turn', 'message', 'g'));
    END LOOP;
    FOR r IN
        SELECT i.indexname
        FROM pg_indexes i
        WHERE i.schemaname = 'chat_app' AND i.indexname ~ 'turn'
    LOOP
        EXECUTE format('ALTER INDEX chat_app.%I RENAME TO %I',
            r.indexname, regexp_replace(r.indexname, 'turn', 'message', 'g'));
    END LOOP;
END
$$;

ALTER FUNCTION chat_app.check_turn_tree() RENAME TO check_message_tree;
ALTER FUNCTION chat_app.check_user_turn_final() RENAME TO check_user_message_final;
ALTER FUNCTION chat_app.forbid_turn_delete() RENAME TO forbid_message_delete;
ALTER FUNCTION chat_app.guard_turn_file() RENAME TO guard_message_file;
ALTER FUNCTION chat_app.guard_turn_lifecycle() RENAME TO guard_message_lifecycle;
ALTER FUNCTION chat_app.lock_turn_tree() RENAME TO lock_message_tree;

ALTER TRIGGER user_turn_final ON chat_app.messages RENAME TO user_message_final;
ALTER FUNCTION chat_app.turn_text(jsonb) RENAME TO message_text;

CREATE OR REPLACE FUNCTION chat_app.assert_chat_file_scope(p_file uuid, p_workspace uuid, p_owner uuid) RETURNS void
    LANGUAGE plpgsql
    AS $$
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

CREATE OR REPLACE FUNCTION chat_app.assert_conversation_idle(p_conversation uuid) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(hashtextextended(p_conversation::text,42));
    IF EXISTS (SELECT 1 FROM chat_app.messages WHERE conversation_id=p_conversation
        AND status IN ('pending','running','requires_action')) THEN
        RAISE EXCEPTION 'Cannot build/publish snapshot while a response is unfinished';
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.can_read_conversation_file(p_user uuid, p_conversation uuid, p_file uuid) RETURNS boolean
    LANGUAGE sql STABLE
    AS $$
    SELECT chat_app.can_read_conversation(p_user, p_conversation) AND EXISTS (
        SELECT 1 FROM chat_app.message_files mf JOIN chat_app.messages m ON m.id = mf.message_id
        JOIN chat_app.stored_files f ON f.id = mf.stored_file_id AND f.deleted_at IS NULL
        WHERE m.conversation_id = p_conversation AND mf.stored_file_id = p_file
    );
$$;

CREATE OR REPLACE FUNCTION chat_app.can_read_share_file(p_user uuid, p_share uuid, p_file uuid) RETURNS boolean
    LANGUAGE sql STABLE
    AS $$
    SELECT chat_app.can_read_share(p_user, p_share) AND EXISTS (
        SELECT 1 FROM chat_app.conversation_shares s
        JOIN chat_app.share_snapshot_message_files mf ON mf.snapshot_id = s.current_snapshot_id
        JOIN chat_app.stored_files f ON f.id = mf.stored_file_id AND f.deleted_at IS NULL
        WHERE s.id = p_share AND mf.stored_file_id = p_file
    );
$$;

CREATE OR REPLACE FUNCTION chat_app.check_copy_completion() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE state text; target uuid;
BEGIN
    SELECT status,target_conversation_id INTO state,target FROM chat_app.conversation_copy_jobs WHERE id=NEW.id;
    IF state='completed' AND EXISTS (
        SELECT 1 FROM chat_app.share_snapshot_files sf WHERE sf.snapshot_id=NEW.snapshot_id AND NOT EXISTS (
            SELECT 1 FROM chat_app.conversation_copy_files cf
            JOIN chat_app.message_files mf ON mf.stored_file_id=cf.target_stored_file_id
            JOIN chat_app.messages m ON m.id=mf.message_id AND m.conversation_id=target
            WHERE cf.job_id=NEW.id AND cf.source_stored_file_id=sf.stored_file_id AND cf.status='copied')
    ) THEN RAISE EXCEPTION 'Every snapshot file must be copied and attached to destination'; END IF;
    IF state='completed' AND EXISTS (SELECT 1 FROM chat_app.messages WHERE conversation_id=target
        AND status IN ('pending','running','requires_action')) THEN
        RAISE EXCEPTION 'Copy destination must contain only terminal messages';
    END IF;
    RETURN NULL;
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.check_message_tree() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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

CREATE OR REPLACE FUNCTION chat_app.check_user_message_final() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM chat_app.messages WHERE id = NEW.id AND role = 'user' AND status <> 'completed') THEN
        RAISE EXCEPTION 'User message must be completed in the same transaction as creation and file links';
    END IF;
    RETURN NULL;
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.forbid_message_delete() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    RAISE EXCEPTION 'Individual message deletion/truncation is disabled; conversation uses soft delete';
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.guard_copy_scope() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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

CREATE OR REPLACE FUNCTION chat_app.guard_message_file() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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

CREATE OR REPLACE FUNCTION chat_app.guard_message_lifecycle() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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

CREATE OR REPLACE FUNCTION chat_app.guard_snapshot_file() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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

CREATE OR REPLACE FUNCTION chat_app.guard_snapshot_header() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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

CREATE OR REPLACE FUNCTION chat_app.guard_stored_object() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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

CREATE OR REPLACE FUNCTION chat_app.lock_message_tree() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND (NEW.id, NEW.conversation_id, NEW.parent_message_id, NEW.role, NEW.created_at)
        IS DISTINCT FROM (OLD.id, OLD.conversation_id, OLD.parent_message_id, OLD.role, OLD.created_at) THEN
        RAISE EXCEPTION 'Message identity, parent, role and creation time are immutable; create a new branch';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(NEW.conversation_id::text, 42));
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION chat_app.message_text(p_content jsonb) RETURNS text
    LANGUAGE sql IMMUTABLE PARALLEL SAFE
    AS $$
    SELECT coalesce(string_agg(part, ' '), '')
    FROM (
        SELECT m.value ->> 'content' AS part
        FROM jsonb_array_elements(
            CASE WHEN jsonb_typeof(p_content) = 'array' THEN p_content ELSE '[]'::jsonb END
        ) AS m
        WHERE m.value ->> 'role' IN ('user', 'assistant')
          AND jsonb_typeof(m.value -> 'content') = 'string'
        UNION ALL
        SELECT p.value ->> 'text'
        FROM jsonb_array_elements(
            CASE WHEN jsonb_typeof(p_content) = 'array' THEN p_content ELSE '[]'::jsonb END
        ) AS m
        CROSS JOIN LATERAL jsonb_array_elements(
            CASE WHEN jsonb_typeof(m.value -> 'content') = 'array' THEN m.value -> 'content' ELSE '[]'::jsonb END
        ) AS p
        WHERE m.value ->> 'role' = 'user' AND p.value ->> 'type' = 'text'
    ) AS parts;
$$;

COMMENT ON SCHEMA chat_app IS 'Phase 2 finalized: flat folders/pin, terminal message lifecycle, message_files -> stored_files(metadata). Service-only; no runtime RLS. See phase-2-decisions.md.';
COMMENT ON FUNCTION chat_app.message_text(p_content jsonb) IS 'Searchable text of a message AG-UI bundle (C09): user/assistant text only, never reasoning or tool payloads.';
COMMENT ON TABLE chat_app.conversations IS 'One owner per conversation; pin/archive/folder stored here. current_message_id is saved branch tip, not a live execution ID.';
COMMENT ON TABLE chat_app.message_files IS 'Authoritative many-to-many links. Resolve conversation/owner/workspace through messages. No extra files/chat_files table, kind or file status.';
COMMENT ON COLUMN chat_app.messages.content IS 'Ordered AG-UI Message[] for one logical user/assistant UI row; includes toolCalls and tool results, not raw SSE token events. Backend performs SDK validation and ID/call consistency checks.';
COMMENT ON COLUMN chat_app.messages.attachments IS 'App-owned JSON metadata for citations, sources and artifacts. Full tool output MAY duplicate content by explicit product decision; model context uses content once.';
COMMENT ON COLUMN chat_app.messages.status IS 'pending/running/requires_action are nonterminal. Pause persists partial content and checkpoint atomically; completed/failed/cancelled are immutable.';
COMMENT ON COLUMN chat_app.messages.metadata IS 'Backend-owned action/checkpoint state and resolved interactions. No client-controlled checkpoint pointers or credentials. Terminal messages remain immutable.';
COMMENT ON COLUMN chat_app.share_snapshot_messages.attachments IS 'Snapshot must preserve both attachments and content and remap embedded file/message/tool IDs when copied.';
