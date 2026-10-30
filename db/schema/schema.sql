CREATE SCHEMA chat_app;

COMMENT ON SCHEMA chat_app IS 'Phase 2 finalized: flat folders/pin, terminal message lifecycle, message_files -> stored_files(metadata). Service-only; no runtime RLS. See phase-2-decisions.md.';

CREATE SCHEMA langgraph_checkpoints;

COMMENT ON SCHEMA langgraph_checkpoints IS 'Private LangGraph saver storage; SDK-managed migrations/checkpoints/blobs/writes. Not public chat history or an automatic recovery scheduler.';

CREATE EXTENSION IF NOT EXISTS citext WITH SCHEMA public;

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;

CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA public;

CREATE FUNCTION chat_app.assert_chat_file_scope(p_file uuid, p_workspace uuid, p_owner uuid) RETURNS void
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

CREATE FUNCTION chat_app.assert_conversation_idle(p_conversation uuid) RETURNS void
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

CREATE FUNCTION chat_app.can_read_conversation(p_user uuid, p_conversation uuid) RETURNS boolean
    LANGUAGE sql STABLE
    AS $$
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

CREATE FUNCTION chat_app.can_read_conversation_file(p_user uuid, p_conversation uuid, p_file uuid) RETURNS boolean
    LANGUAGE sql STABLE
    AS $$
    SELECT chat_app.can_read_conversation(p_user, p_conversation) AND EXISTS (
        SELECT 1 FROM chat_app.message_files mf JOIN chat_app.messages m ON m.id = mf.message_id
        JOIN chat_app.stored_files f ON f.id = mf.stored_file_id AND f.deleted_at IS NULL
        WHERE m.conversation_id = p_conversation AND mf.stored_file_id = p_file
    );
$$;

CREATE FUNCTION chat_app.can_read_share(p_user uuid, p_share uuid) RETURNS boolean
    LANGUAGE sql STABLE
    AS $$
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

COMMENT ON FUNCTION chat_app.can_read_share(p_user uuid, p_share uuid) IS 'Eligibility after resolving link token. Org membership must be checked on every request. A share is NOT a grant to the live source conversation.';

CREATE FUNCTION chat_app.can_read_share_file(p_user uuid, p_share uuid, p_file uuid) RETURNS boolean
    LANGUAGE sql STABLE
    AS $$
    SELECT chat_app.can_read_share(p_user, p_share) AND EXISTS (
        SELECT 1 FROM chat_app.conversation_shares s
        JOIN chat_app.share_snapshot_message_files mf ON mf.snapshot_id = s.current_snapshot_id
        JOIN chat_app.stored_files f ON f.id = mf.stored_file_id AND f.deleted_at IS NULL
        WHERE s.id = p_share AND mf.stored_file_id = p_file
    );
$$;

CREATE FUNCTION chat_app.check_copy_completion() RETURNS trigger
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

CREATE FUNCTION chat_app.check_message_tree() RETURNS trigger
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

CREATE FUNCTION chat_app.check_organization_owner() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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

CREATE FUNCTION chat_app.check_snapshot_publication() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.current_snapshot_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM chat_app.share_snapshots ss
        WHERE ss.id = NEW.current_snapshot_id AND ss.share_id = NEW.id AND ss.sealed_at IS NOT NULL
    ) THEN RAISE EXCEPTION 'Only sealed snapshots may be published'; END IF;
    RETURN NULL;
END;
$$;

CREATE FUNCTION chat_app.check_user_message_final() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM chat_app.messages WHERE id = NEW.id AND role = 'user' AND status <> 'completed') THEN
        RAISE EXCEPTION 'User message must be completed in the same transaction as creation and file links';
    END IF;
    RETURN NULL;
END;
$$;

CREATE FUNCTION chat_app.forbid_message_delete() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    RAISE EXCEPTION 'Individual message deletion/truncation is disabled; conversation uses soft delete';
END;
$$;

CREATE FUNCTION chat_app.guard_conversation_scope() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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

CREATE FUNCTION chat_app.guard_copy_file() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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

CREATE FUNCTION chat_app.guard_copy_publication() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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

CREATE FUNCTION chat_app.guard_copy_scope() RETURNS trigger
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

CREATE FUNCTION chat_app.guard_message_file() RETURNS trigger
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

CREATE FUNCTION chat_app.guard_message_lifecycle() RETURNS trigger
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

CREATE FUNCTION chat_app.guard_share_scope() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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

CREATE FUNCTION chat_app.guard_snapshot_content() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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

CREATE FUNCTION chat_app.guard_snapshot_file() RETURNS trigger
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

CREATE FUNCTION chat_app.guard_snapshot_header() RETURNS trigger
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

CREATE FUNCTION chat_app.guard_snapshot_idle() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE cid uuid;
BEGIN
    SELECT s.source_conversation_id INTO cid FROM chat_app.conversation_shares s WHERE s.id = NEW.share_id;
    PERFORM chat_app.assert_conversation_idle(cid);
    RETURN NEW;
END;
$$;

CREATE FUNCTION chat_app.guard_stored_object() RETURNS trigger
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

CREATE FUNCTION chat_app.guard_workspace_identity() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF (NEW.kind, NEW.personal_user_id, NEW.organization_id) IS DISTINCT FROM
       (OLD.kind, OLD.personal_user_id, OLD.organization_id) THEN
        RAISE EXCEPTION 'Workspace identity is immutable';
    END IF;
    RETURN NEW;
END;
$$;

CREATE FUNCTION chat_app.lock_message_tree() RETURNS trigger
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

CREATE FUNCTION chat_app.lock_organization_mutation() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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

CREATE FUNCTION chat_app.message_text(p_content jsonb) RETURNS text
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

COMMENT ON FUNCTION chat_app.message_text(p_content jsonb) IS 'Searchable text of a message AG-UI bundle (C09): user/assistant text only, never reasoning or tool payloads.';

CREATE FUNCTION chat_app.provision_organization() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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

CREATE FUNCTION chat_app.provision_personal_workspace() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO chat_app.workspaces(kind, personal_user_id) VALUES ('personal', NEW.id);
    RETURN NEW;
END;
$$;

CREATE FUNCTION chat_app.revoke_deleted_conversation_shares() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE chat_app.conversation_shares SET revoked_at = COALESCE(revoked_at, clock_timestamp())
    WHERE source_conversation_id = NEW.id AND revoked_at IS NULL;
    RETURN NULL;
END;
$$;

CREATE FUNCTION chat_app.revoke_departed_member_shares() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE chat_app.conversation_shares SET revoked_at = COALESCE(revoked_at, clock_timestamp())
    WHERE organization_id = OLD.organization_id AND created_by = OLD.user_id AND revoked_at IS NULL;
    RETURN NULL;
END;
$$;

CREATE FUNCTION chat_app.search_key(p_text text) RETURNS text
    LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE
    SET search_path TO 'public', 'pg_catalog'
    AS $$
    SELECT lower(unaccent('unaccent'::regdictionary, p_text));
$$;

COMMENT ON FUNCTION chat_app.search_key(p_text text) IS 'Lower-case, accent-free form compared by chat search (C09). Change it only together with the indexes built on it.';

CREATE FUNCTION chat_app.touch_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at := clock_timestamp();
    RETURN NEW;
END;
$$;

CREATE FUNCTION chat_app.valid_agui_bundle(p_role text, payload jsonb) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE
    AS $$
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

CREATE TABLE chat_app.conversation_copy_files (
    job_id uuid NOT NULL,
    source_stored_file_id uuid CONSTRAINT conversation_copy_files_source_file_id_not_null NOT NULL,
    target_stored_file_id uuid CONSTRAINT conversation_copy_files_target_file_id_not_null NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT conversation_copy_files_check CHECK ((source_stored_file_id <> target_stored_file_id)),
    CONSTRAINT conversation_copy_files_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'copied'::text, 'failed'::text])))
);

COMMENT ON TABLE chat_app.conversation_copy_files IS 'Physical copy mapping between stored_files rows. Worker copies S3 bytes to a NEW object key; DB cannot verify remote bytes itself. Separate from LLM execution.';

CREATE TABLE chat_app.conversation_copy_jobs (
    id uuid DEFAULT uuidv7() NOT NULL,
    requested_by uuid NOT NULL,
    snapshot_id uuid NOT NULL,
    target_workspace_id uuid NOT NULL,
    target_conversation_id uuid NOT NULL,
    client_request_id text NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    lease_token uuid,
    lease_expires_at timestamp with time zone,
    next_attempt_at timestamp with time zone DEFAULT now() NOT NULL,
    attempts integer DEFAULT 0 NOT NULL,
    last_error text,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT conversation_copy_jobs_attempts_check CHECK ((attempts >= 0)),
    CONSTRAINT conversation_copy_jobs_check CHECK (((lease_token IS NULL) = (lease_expires_at IS NULL))),
    CONSTRAINT conversation_copy_jobs_check1 CHECK (((status = 'completed'::text) = (completed_at IS NOT NULL))),
    CONSTRAINT conversation_copy_jobs_client_request_id_check CHECK ((btrim(client_request_id) <> ''::text)),
    CONSTRAINT conversation_copy_jobs_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'copying'::text, 'completed'::text, 'failed'::text, 'cancelled'::text])))
);

COMMENT ON TABLE chat_app.conversation_copy_jobs IS 'Fixed snapshot version per job; duplicates reuse request id, changed request payload must be rejected. Completed copies are private, owned by requester, and survive source/share revocation.';

CREATE TABLE chat_app.conversation_folders (
    id uuid DEFAULT uuidv7() NOT NULL,
    workspace_id uuid NOT NULL,
    owner_user_id uuid NOT NULL,
    name text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT conversation_folders_name_check CHECK ((btrim(name) <> ''::text))
);

COMMENT ON TABLE chat_app.conversation_folders IS 'Flat personal organization of chats inside one workspace; no parent_id, shared-folder ACL, instructions or RAG project behavior.';

CREATE TABLE chat_app.conversation_shares (
    id uuid DEFAULT uuidv7() NOT NULL,
    source_conversation_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    created_by uuid NOT NULL,
    mode text NOT NULL,
    organization_id uuid,
    link_token_hash text NOT NULL,
    current_snapshot_id uuid,
    expires_at timestamp with time zone,
    revoked_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT conversation_shares_check CHECK ((((mode = 'public'::text) AND (organization_id IS NULL)) OR ((mode = 'organization'::text) AND (organization_id IS NOT NULL)))),
    CONSTRAINT conversation_shares_check1 CHECK (((expires_at IS NULL) OR (expires_at > created_at))),
    CONSTRAINT conversation_shares_link_token_hash_check CHECK ((link_token_hash ~ '^[a-f0-9]{64}$'::text)),
    CONSTRAINT conversation_shares_mode_check CHECK ((mode = ANY (ARRAY['public'::text, 'organization'::text])))
);

CREATE TABLE chat_app.conversations (
    id uuid DEFAULT uuidv7() NOT NULL,
    workspace_id uuid NOT NULL,
    owner_user_id uuid NOT NULL,
    title text DEFAULT 'Cuộc trò chuyện mới'::text NOT NULL,
    current_message_id uuid,
    deleted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    pinned_at timestamp with time zone,
    archived_at timestamp with time zone,
    folder_id uuid,
    CONSTRAINT conversations_title_check CHECK ((btrim(title) <> ''::text))
);

COMMENT ON TABLE chat_app.conversations IS 'One owner per conversation; pin/archive/folder stored here. current_message_id is saved branch tip, not a live execution ID.';

CREATE TABLE chat_app.member_role_assignments (
    id uuid DEFAULT uuidv7() NOT NULL,
    organization_id uuid NOT NULL,
    member_id uuid NOT NULL,
    role_id uuid NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE chat_app.message_files (
    message_id uuid NOT NULL,
    stored_file_id uuid NOT NULL
);

COMMENT ON TABLE chat_app.message_files IS 'Authoritative many-to-many links. Resolve conversation/owner/workspace through messages. No extra files/chat_files table, kind or file status.';

CREATE TABLE chat_app.messages (
    id uuid DEFAULT uuidv7() NOT NULL,
    conversation_id uuid NOT NULL,
    parent_message_id uuid,
    role text NOT NULL,
    content jsonb DEFAULT '[]'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    attachments jsonb DEFAULT '[]'::jsonb NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    CONSTRAINT messages_attachments_check CHECK ((jsonb_typeof(attachments) = 'array'::text)),
    CONSTRAINT messages_check CHECK (((parent_message_id IS NULL) OR (parent_message_id <> id))),
    CONSTRAINT messages_content_check CHECK (chat_app.valid_agui_bundle(role, content)),
    CONSTRAINT messages_metadata_object_check CHECK ((jsonb_typeof(metadata) = 'object'::text)),
    CONSTRAINT messages_role_check CHECK ((role = ANY (ARRAY['user'::text, 'assistant'::text]))),
    CONSTRAINT messages_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'running'::text, 'requires_action'::text, 'completed'::text, 'failed'::text, 'cancelled'::text]))),
    CONSTRAINT messages_user_status_check CHECK (((role <> 'user'::text) OR (status = ANY (ARRAY['pending'::text, 'completed'::text]))))
);

COMMENT ON COLUMN chat_app.messages.content IS 'Ordered AG-UI Message[] for one logical user/assistant UI row; includes toolCalls and tool results, not raw SSE token events. Backend performs SDK validation and ID/call consistency checks.';

COMMENT ON COLUMN chat_app.messages.attachments IS 'App-owned JSON metadata for citations, sources and artifacts. Full tool output MAY duplicate content by explicit product decision; model context uses content once.';

COMMENT ON COLUMN chat_app.messages.status IS 'pending/running/requires_action are nonterminal. Pause persists partial content and checkpoint atomically; completed/failed/cancelled are immutable.';

COMMENT ON COLUMN chat_app.messages.metadata IS 'Backend-owned action/checkpoint state and resolved interactions. No client-controlled checkpoint pointers or credentials. Terminal messages remain immutable.';

CREATE TABLE chat_app.organization_invitations (
    id uuid DEFAULT uuidv7() NOT NULL,
    organization_id uuid NOT NULL,
    email citext NOT NULL,
    invited_by uuid NOT NULL,
    token_hash text NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    accepted_by uuid,
    accepted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT organization_invitations_check CHECK ((expires_at > created_at)),
    CONSTRAINT organization_invitations_check1 CHECK ((((status = 'accepted'::text) AND (accepted_by IS NOT NULL) AND (accepted_at IS NOT NULL)) OR ((status <> 'accepted'::text) AND (accepted_by IS NULL) AND (accepted_at IS NULL)))),
    CONSTRAINT organization_invitations_email_check CHECK ((((email)::text = btrim((email)::text)) AND ((email)::text <> ''::text))),
    CONSTRAINT organization_invitations_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'accepted'::text, 'revoked'::text, 'expired'::text]))),
    CONSTRAINT organization_invitations_token_hash_check CHECK ((btrim(token_hash) <> ''::text))
);

COMMENT ON TABLE chat_app.organization_invitations IS 'Acceptance must atomically verify pending/unexpired token and verified email, create/reactivate membership, assign member role, consume invitation. Mark expired pending rows before reinviting.';

CREATE TABLE chat_app.organization_members (
    id uuid DEFAULT uuidv7() NOT NULL,
    organization_id uuid NOT NULL,
    user_id uuid NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    joined_at timestamp with time zone DEFAULT now() NOT NULL,
    left_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT organization_members_check CHECK (((NOT is_active) OR (left_at IS NULL)))
);

CREATE TABLE chat_app.organization_roles (
    id uuid DEFAULT uuidv7() NOT NULL,
    organization_id uuid NOT NULL,
    name text NOT NULL,
    role_key text,
    description text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT organization_roles_name_check CHECK ((btrim(name) <> ''::text)),
    CONSTRAINT organization_roles_role_key_check CHECK ((role_key ~ '^[a-z][a-z0-9_]*$'::text))
);

CREATE TABLE chat_app.organizations (
    id uuid DEFAULT uuidv7() NOT NULL,
    name text NOT NULL,
    created_by uuid NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    avatar_url text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT organizations_metadata_check CHECK ((jsonb_typeof(metadata) = 'object'::text)),
    CONSTRAINT organizations_name_check CHECK ((btrim(name) <> ''::text))
);

CREATE TABLE chat_app.permissions (
    id uuid DEFAULT uuidv7() NOT NULL,
    resource text NOT NULL,
    action text NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT permissions_action_check CHECK ((action ~ '^[a-z][a-z0-9_]*$'::text)),
    CONSTRAINT permissions_resource_check CHECK ((resource ~ '^[a-z][a-z0-9_]*$'::text))
);

CREATE TABLE chat_app.refresh_tokens (
    id uuid DEFAULT uuidv7() NOT NULL,
    user_id uuid NOT NULL,
    token_hash text NOT NULL,
    family_id uuid DEFAULT uuidv7() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    consumed_at timestamp with time zone,
    revoked_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT refresh_tokens_check CHECK ((expires_at > created_at)),
    CONSTRAINT refresh_tokens_check1 CHECK (((consumed_at IS NULL) OR (consumed_at >= created_at))),
    CONSTRAINT refresh_tokens_check2 CHECK (((revoked_at IS NULL) OR (revoked_at >= created_at))),
    CONSTRAINT refresh_tokens_token_hash_check CHECK ((btrim(token_hash) <> ''::text))
);

COMMENT ON TABLE chat_app.refresh_tokens IS 'Global login session tokens; no organization binding. Rotation/reuse detection and family revocation require service transactions.';

CREATE TABLE chat_app.role_permissions (
    role_id uuid NOT NULL,
    permission_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE chat_app.share_snapshot_files (
    snapshot_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    stored_file_id uuid CONSTRAINT share_snapshot_files_file_id_not_null NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    CONSTRAINT snapshot_file_metadata_object_check CHECK ((jsonb_typeof(metadata) = 'object'::text))
);

COMMENT ON TABLE chat_app.share_snapshot_files IS 'Immutable snapshot file manifest; stored_file_id -> stored_files, metadata is backend-allowlisted snapshot, never live raw metadata.';

CREATE TABLE chat_app.share_snapshot_message_files (
    snapshot_id uuid NOT NULL,
    message_id uuid NOT NULL,
    stored_file_id uuid CONSTRAINT share_snapshot_message_files_file_id_not_null NOT NULL
);

CREATE TABLE chat_app.share_snapshot_messages (
    snapshot_id uuid NOT NULL,
    id uuid DEFAULT uuidv7() NOT NULL,
    parent_message_id uuid,
    role text NOT NULL,
    content jsonb NOT NULL,
    original_created_at timestamp with time zone NOT NULL,
    attachments jsonb DEFAULT '[]'::jsonb NOT NULL,
    status text DEFAULT 'completed'::text NOT NULL,
    CONSTRAINT share_snapshot_messages_attachments_check CHECK ((jsonb_typeof(attachments) = 'array'::text)),
    CONSTRAINT share_snapshot_messages_check CHECK (((parent_message_id IS NULL) OR (parent_message_id <> id))),
    CONSTRAINT share_snapshot_messages_content_check CHECK (chat_app.valid_agui_bundle(role, content)),
    CONSTRAINT share_snapshot_messages_role_check CHECK ((role = ANY (ARRAY['user'::text, 'assistant'::text]))),
    CONSTRAINT snapshot_message_status_check CHECK ((status = ANY (ARRAY['completed'::text, 'failed'::text, 'cancelled'::text]))),
    CONSTRAINT snapshot_user_status_check CHECK (((role <> 'user'::text) OR (status = 'completed'::text)))
);

COMMENT ON COLUMN chat_app.share_snapshot_messages.attachments IS 'Snapshot must preserve both attachments and content and remap embedded file/message/tool IDs when copied.';

CREATE TABLE chat_app.share_snapshots (
    id uuid DEFAULT uuidv7() NOT NULL,
    share_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    version bigint NOT NULL,
    title text NOT NULL,
    current_message_id uuid,
    sealed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT share_snapshots_title_check CHECK ((btrim(title) <> ''::text)),
    CONSTRAINT share_snapshots_version_check CHECK ((version > 0))
);

CREATE TABLE chat_app.stored_files (
    id uuid DEFAULT uuidv7() NOT NULL,
    bucket text NOT NULL,
    object_key text NOT NULL,
    original_name text NOT NULL,
    content_type text NOT NULL,
    visibility text NOT NULL,
    size_bytes bigint NOT NULL,
    checksum_sha256 text,
    uploaded_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_at timestamp with time zone,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    CONSTRAINT ck_stored_files_bucket CHECK (((length(bucket) >= 3) AND (length(bucket) <= 63) AND (bucket ~ '^[a-z0-9][a-z0-9.-]*[a-z0-9]$'::text) AND (bucket !~ '\.\.'::text))),
    CONSTRAINT ck_stored_files_checksum_sha256 CHECK (((checksum_sha256 IS NULL) OR (checksum_sha256 ~ '^[0-9a-f]{64}$'::text))),
    CONSTRAINT ck_stored_files_content_type CHECK (((btrim(content_type) <> ''::text) AND (length(content_type) <= 255))),
    CONSTRAINT ck_stored_files_deleted_at CHECK (((deleted_at IS NULL) OR (deleted_at >= created_at))),
    CONSTRAINT ck_stored_files_object_key CHECK (((octet_length(object_key) >= 1) AND (octet_length(object_key) <= 1024) AND (object_key !~ '(^|/)\.\.?(/|$)'::text))),
    CONSTRAINT ck_stored_files_original_name CHECK (((btrim(original_name) <> ''::text) AND (octet_length(original_name) <= 1024))),
    CONSTRAINT ck_stored_files_size CHECK ((size_bytes >= 0)),
    CONSTRAINT ck_stored_files_visibility CHECK ((visibility = ANY (ARRAY['public'::text, 'private'::text]))),
    CONSTRAINT ck_stored_files_visibility_key CHECK ((((visibility = 'public'::text) AND (object_key ~~ 'public/%'::text)) OR ((visibility = 'private'::text) AND (object_key ~~ 'private/%'::text)))),
    CONSTRAINT stored_files_metadata_object_check CHECK ((jsonb_typeof(metadata) = 'object'::text))
);

COMMENT ON TABLE chat_app.stored_files IS 'S3-compatible object metadata, not ACL. Backend/storage must validate actual object/checksum and enforce no overwrite. Bucket checks are basic application checks, not full vendor validation.';

COMMENT ON COLUMN chat_app.stored_files.metadata IS 'Optional extensible object: image/extraction/preview/RAG descriptors. Not ACL; no secrets, presigned URLs, vectors or chunk corpus. No speculative GIN index.';

CREATE TABLE chat_app.user_accounts (
    id uuid DEFAULT uuidv7() NOT NULL,
    user_id uuid NOT NULL,
    provider_id text NOT NULL,
    account_id text NOT NULL,
    password_hash text,
    access_token_ciphertext text,
    refresh_token_ciphertext text,
    id_token_ciphertext text,
    access_token_expires_at timestamp with time zone,
    refresh_token_expires_at timestamp with time zone,
    scope text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT user_accounts_account_id_check CHECK ((btrim(account_id) <> ''::text)),
    CONSTRAINT user_accounts_check CHECK ((((provider_id = 'credential'::text) AND (password_hash IS NOT NULL)) OR ((provider_id <> 'credential'::text) AND (password_hash IS NULL)))),
    CONSTRAINT user_accounts_password_hash_check CHECK (((password_hash IS NULL) OR (btrim(password_hash) <> ''::text))),
    CONSTRAINT user_accounts_provider_id_check CHECK ((btrim(provider_id) <> ''::text))
);

COMMENT ON COLUMN chat_app.user_accounts.provider_id IS 'Identifies an issuer/provider configuration, not just a vendor name; identity linking requires verification.';

CREATE TABLE chat_app.users (
    id uuid DEFAULT uuidv7() NOT NULL,
    name text NOT NULL,
    email citext NOT NULL,
    email_verified boolean DEFAULT false NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    is_superuser boolean DEFAULT false NOT NULL,
    avatar_url text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT users_email_check CHECK ((((email)::text = btrim((email)::text)) AND ((email)::text <> ''::text))),
    CONSTRAINT users_name_check CHECK ((btrim(name) <> ''::text))
);

COMMENT ON COLUMN chat_app.users.is_superuser IS 'Platform administration only; never an implicit right to read private chats/files.';

CREATE TABLE chat_app.verifications (
    id uuid DEFAULT uuidv7() NOT NULL,
    identifier citext NOT NULL,
    purpose text NOT NULL,
    token_hash text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    consumed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT verifications_check CHECK ((expires_at > created_at)),
    CONSTRAINT verifications_check1 CHECK (((consumed_at IS NULL) OR (consumed_at >= created_at))),
    CONSTRAINT verifications_identifier_check CHECK ((btrim((identifier)::text) <> ''::text)),
    CONSTRAINT verifications_purpose_check CHECK ((purpose = ANY (ARRAY['email_verify'::text, 'password_reset'::text]))),
    CONSTRAINT verifications_token_hash_check CHECK ((btrim(token_hash) <> ''::text))
);

CREATE TABLE chat_app.workspaces (
    id uuid DEFAULT uuidv7() NOT NULL,
    kind text NOT NULL,
    personal_user_id uuid,
    organization_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT workspaces_check CHECK ((((kind = 'personal'::text) AND (personal_user_id IS NOT NULL) AND (organization_id IS NULL)) OR ((kind = 'organization'::text) AND (personal_user_id IS NULL) AND (organization_id IS NOT NULL)))),
    CONSTRAINT workspaces_kind_check CHECK ((kind = ANY (ARRAY['personal'::text, 'organization'::text])))
);

COMMENT ON TABLE chat_app.workspaces IS 'Exactly one personal workspace per created user and one per created organization, provisioned by triggers. Workspace membership does not grant chat read access.';

ALTER TABLE ONLY chat_app.conversation_copy_files
    ADD CONSTRAINT conversation_copy_files_pkey PRIMARY KEY (job_id, source_stored_file_id);

ALTER TABLE ONLY chat_app.conversation_copy_files
    ADD CONSTRAINT conversation_copy_files_target_file_id_key UNIQUE (target_stored_file_id);

ALTER TABLE ONLY chat_app.conversation_copy_jobs
    ADD CONSTRAINT conversation_copy_jobs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.conversation_copy_jobs
    ADD CONSTRAINT conversation_copy_jobs_requested_by_client_request_id_key UNIQUE (requested_by, client_request_id);

ALTER TABLE ONLY chat_app.conversation_copy_jobs
    ADD CONSTRAINT conversation_copy_jobs_target_conversation_id_key UNIQUE (target_conversation_id);

ALTER TABLE ONLY chat_app.conversation_folders
    ADD CONSTRAINT conversation_folders_id_workspace_id_owner_user_id_key UNIQUE (id, workspace_id, owner_user_id);

ALTER TABLE ONLY chat_app.conversation_folders
    ADD CONSTRAINT conversation_folders_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.conversation_shares
    ADD CONSTRAINT conversation_shares_id_workspace_id_key UNIQUE (id, workspace_id);

ALTER TABLE ONLY chat_app.conversation_shares
    ADD CONSTRAINT conversation_shares_link_token_hash_key UNIQUE (link_token_hash);

ALTER TABLE ONLY chat_app.conversation_shares
    ADD CONSTRAINT conversation_shares_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.conversations
    ADD CONSTRAINT conversations_id_workspace_id_key UNIQUE (id, workspace_id);

ALTER TABLE ONLY chat_app.conversations
    ADD CONSTRAINT conversations_id_workspace_owner_key UNIQUE (id, workspace_id, owner_user_id);

ALTER TABLE ONLY chat_app.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.member_role_assignments
    ADD CONSTRAINT member_role_assignments_organization_id_member_id_role_id_key UNIQUE (organization_id, member_id, role_id);

ALTER TABLE ONLY chat_app.member_role_assignments
    ADD CONSTRAINT member_role_assignments_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.message_files
    ADD CONSTRAINT message_files_pkey PRIMARY KEY (message_id, stored_file_id);

ALTER TABLE ONLY chat_app.messages
    ADD CONSTRAINT messages_conversation_id_id_key UNIQUE (conversation_id, id);

ALTER TABLE ONLY chat_app.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.organization_invitations
    ADD CONSTRAINT organization_invitations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.organization_invitations
    ADD CONSTRAINT organization_invitations_token_hash_key UNIQUE (token_hash);

ALTER TABLE ONLY chat_app.organization_members
    ADD CONSTRAINT organization_members_id_organization_id_key UNIQUE (id, organization_id);

ALTER TABLE ONLY chat_app.organization_members
    ADD CONSTRAINT organization_members_organization_id_user_id_key UNIQUE (organization_id, user_id);

ALTER TABLE ONLY chat_app.organization_members
    ADD CONSTRAINT organization_members_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.organization_roles
    ADD CONSTRAINT organization_roles_id_organization_id_key UNIQUE (id, organization_id);

ALTER TABLE ONLY chat_app.organization_roles
    ADD CONSTRAINT organization_roles_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.permissions
    ADD CONSTRAINT permissions_resource_action_key UNIQUE (resource, action);

ALTER TABLE ONLY chat_app.refresh_tokens
    ADD CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.refresh_tokens
    ADD CONSTRAINT refresh_tokens_token_hash_key UNIQUE (token_hash);

ALTER TABLE ONLY chat_app.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (role_id, permission_id);

ALTER TABLE ONLY chat_app.share_snapshot_files
    ADD CONSTRAINT share_snapshot_files_pkey PRIMARY KEY (snapshot_id, stored_file_id);

ALTER TABLE ONLY chat_app.share_snapshot_message_files
    ADD CONSTRAINT share_snapshot_message_files_pkey PRIMARY KEY (snapshot_id, message_id, stored_file_id);

ALTER TABLE ONLY chat_app.share_snapshot_messages
    ADD CONSTRAINT share_snapshot_messages_pkey PRIMARY KEY (snapshot_id, id);

ALTER TABLE ONLY chat_app.share_snapshots
    ADD CONSTRAINT share_snapshots_id_workspace_id_key UNIQUE (id, workspace_id);

ALTER TABLE ONLY chat_app.share_snapshots
    ADD CONSTRAINT share_snapshots_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.share_snapshots
    ADD CONSTRAINT share_snapshots_share_id_id_key UNIQUE (share_id, id);

ALTER TABLE ONLY chat_app.share_snapshots
    ADD CONSTRAINT share_snapshots_share_id_version_key UNIQUE (share_id, version);

ALTER TABLE ONLY chat_app.stored_files
    ADD CONSTRAINT stored_files_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.stored_files
    ADD CONSTRAINT uq_stored_files_bucket_object_key UNIQUE (bucket, object_key);

ALTER TABLE ONLY chat_app.user_accounts
    ADD CONSTRAINT user_accounts_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.user_accounts
    ADD CONSTRAINT user_accounts_provider_id_account_id_key UNIQUE (provider_id, account_id);

ALTER TABLE ONLY chat_app.users
    ADD CONSTRAINT users_email_key UNIQUE (email);

ALTER TABLE ONLY chat_app.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.verifications
    ADD CONSTRAINT verifications_pkey PRIMARY KEY (id);

ALTER TABLE ONLY chat_app.verifications
    ADD CONSTRAINT verifications_token_hash_key UNIQUE (token_hash);

ALTER TABLE ONLY chat_app.workspaces
    ADD CONSTRAINT workspaces_id_organization_id_key UNIQUE (id, organization_id);

ALTER TABLE ONLY chat_app.workspaces
    ADD CONSTRAINT workspaces_organization_id_key UNIQUE (organization_id);

ALTER TABLE ONLY chat_app.workspaces
    ADD CONSTRAINT workspaces_personal_user_id_key UNIQUE (personal_user_id);

ALTER TABLE ONLY chat_app.workspaces
    ADD CONSTRAINT workspaces_pkey PRIMARY KEY (id);

CREATE INDEX conversation_copy_files_source_idx ON chat_app.conversation_copy_files USING btree (source_stored_file_id);

CREATE INDEX conversation_copy_jobs_pending_idx ON chat_app.conversation_copy_jobs USING btree (next_attempt_at, id) WHERE (status = ANY (ARRAY['pending'::text, 'copying'::text]));

CREATE INDEX conversation_copy_jobs_snapshot_idx ON chat_app.conversation_copy_jobs USING btree (snapshot_id);

CREATE INDEX conversation_copy_jobs_target_workspace_idx ON chat_app.conversation_copy_jobs USING btree (target_workspace_id);

CREATE UNIQUE INDEX conversation_folders_name_idx ON chat_app.conversation_folders USING btree (workspace_id, owner_user_id, lower(btrim(name)));

CREATE INDEX conversation_folders_owner_idx ON chat_app.conversation_folders USING btree (owner_user_id, workspace_id);

CREATE INDEX conversation_shares_creator_idx ON chat_app.conversation_shares USING btree (created_by);

CREATE INDEX conversation_shares_organization_idx ON chat_app.conversation_shares USING btree (organization_id);

CREATE INDEX conversation_shares_source_idx ON chat_app.conversation_shares USING btree (source_conversation_id, workspace_id);

CREATE INDEX conversation_shares_workspace_org_idx ON chat_app.conversation_shares USING btree (workspace_id, organization_id);

CREATE INDEX conversations_folder_fk_idx ON chat_app.conversations USING btree (folder_id, workspace_id, owner_user_id);

CREATE INDEX conversations_sidebar_idx ON chat_app.conversations USING btree (owner_user_id, workspace_id, updated_at DESC, id DESC) WHERE (deleted_at IS NULL);

CREATE INDEX conversations_title_search_idx ON chat_app.conversations USING gin (chat_app.search_key(title) gin_trgm_ops);

CREATE INDEX conversations_workspace_idx ON chat_app.conversations USING btree (workspace_id);

CREATE INDEX idx_conversations_folder ON chat_app.conversations USING btree (workspace_id, owner_user_id, folder_id, updated_at DESC, id DESC) WHERE ((folder_id IS NOT NULL) AND (deleted_at IS NULL) AND (archived_at IS NULL));

CREATE INDEX idx_conversations_pinned ON chat_app.conversations USING btree (workspace_id, owner_user_id, pinned_at DESC, id DESC) WHERE ((pinned_at IS NOT NULL) AND (deleted_at IS NULL) AND (archived_at IS NULL));

CREATE INDEX idx_stored_files_uploaded_by ON chat_app.stored_files USING btree (uploaded_by) WHERE (uploaded_by IS NOT NULL);

CREATE INDEX member_role_assignments_member_idx ON chat_app.member_role_assignments USING btree (member_id, organization_id);

CREATE INDEX member_role_assignments_role_idx ON chat_app.member_role_assignments USING btree (role_id, organization_id);

CREATE INDEX message_files_stored_file_idx ON chat_app.message_files USING btree (stored_file_id);

CREATE INDEX messages_history_idx ON chat_app.messages USING btree (conversation_id, created_at, id);

CREATE UNIQUE INDEX messages_one_active_assistant_idx ON chat_app.messages USING btree (conversation_id) WHERE ((role = 'assistant'::text) AND (status = ANY (ARRAY['pending'::text, 'running'::text, 'requires_action'::text])));

CREATE INDEX messages_parent_idx ON chat_app.messages USING btree (conversation_id, parent_message_id);

CREATE INDEX messages_search_idx ON chat_app.messages USING gin (chat_app.search_key(chat_app.message_text(content)) gin_trgm_ops);

CREATE INDEX organization_invitations_acceptor_idx ON chat_app.organization_invitations USING btree (accepted_by);

CREATE INDEX organization_invitations_expiry_idx ON chat_app.organization_invitations USING btree (expires_at) WHERE (status = 'pending'::text);

CREATE UNIQUE INDEX organization_invitations_pending_idx ON chat_app.organization_invitations USING btree (organization_id, email) WHERE (status = 'pending'::text);

CREATE INDEX organization_invitations_sender_idx ON chat_app.organization_invitations USING btree (invited_by);

CREATE INDEX organization_members_user_idx ON chat_app.organization_members USING btree (user_id, organization_id);

CREATE UNIQUE INDEX organization_roles_key_idx ON chat_app.organization_roles USING btree (organization_id, role_key) WHERE (role_key IS NOT NULL);

CREATE UNIQUE INDEX organization_roles_name_idx ON chat_app.organization_roles USING btree (organization_id, lower(name));

CREATE INDEX organizations_creator_idx ON chat_app.organizations USING btree (created_by);

CREATE INDEX refresh_tokens_expiry_idx ON chat_app.refresh_tokens USING btree (expires_at);

CREATE INDEX refresh_tokens_family_idx ON chat_app.refresh_tokens USING btree (family_id);

CREATE INDEX refresh_tokens_user_idx ON chat_app.refresh_tokens USING btree (user_id);

CREATE INDEX role_permissions_permission_idx ON chat_app.role_permissions USING btree (permission_id);

CREATE INDEX share_snapshot_files_file_idx ON chat_app.share_snapshot_files USING btree (stored_file_id, workspace_id);

CREATE INDEX share_snapshot_message_files_file_idx ON chat_app.share_snapshot_message_files USING btree (snapshot_id, stored_file_id);

CREATE INDEX share_snapshot_messages_history_idx ON chat_app.share_snapshot_messages USING btree (snapshot_id, original_created_at, id);

CREATE INDEX share_snapshot_messages_parent_idx ON chat_app.share_snapshot_messages USING btree (snapshot_id, parent_message_id);

CREATE UNIQUE INDEX user_accounts_one_password_idx ON chat_app.user_accounts USING btree (user_id) WHERE (provider_id = 'credential'::text);

CREATE INDEX user_accounts_user_idx ON chat_app.user_accounts USING btree (user_id);

CREATE INDEX verifications_expiry_idx ON chat_app.verifications USING btree (expires_at);

CREATE INDEX verifications_lookup_idx ON chat_app.verifications USING btree (identifier, purpose);

CREATE TRIGGER guard_content BEFORE INSERT OR DELETE OR UPDATE ON chat_app.share_snapshot_files FOR EACH ROW EXECUTE FUNCTION chat_app.guard_snapshot_content();

CREATE TRIGGER guard_content BEFORE INSERT OR DELETE OR UPDATE ON chat_app.share_snapshot_message_files FOR EACH ROW EXECUTE FUNCTION chat_app.guard_snapshot_content();

CREATE TRIGGER guard_content BEFORE INSERT OR DELETE OR UPDATE ON chat_app.share_snapshot_messages FOR EACH ROW EXECUTE FUNCTION chat_app.guard_snapshot_content();

CREATE TRIGGER guard_copy_publication BEFORE INSERT OR UPDATE ON chat_app.conversation_shares FOR EACH ROW EXECUTE FUNCTION chat_app.guard_copy_publication();

CREATE TRIGGER guard_file BEFORE INSERT OR UPDATE ON chat_app.share_snapshot_files FOR EACH ROW EXECUTE FUNCTION chat_app.guard_snapshot_file();

CREATE TRIGGER guard_header BEFORE INSERT OR DELETE OR UPDATE ON chat_app.share_snapshots FOR EACH ROW EXECUTE FUNCTION chat_app.guard_snapshot_header();

CREATE TRIGGER guard_identity BEFORE UPDATE ON chat_app.workspaces FOR EACH ROW EXECUTE FUNCTION chat_app.guard_workspace_identity();

CREATE TRIGGER guard_idle BEFORE INSERT OR UPDATE ON chat_app.share_snapshots FOR EACH ROW EXECUTE FUNCTION chat_app.guard_snapshot_idle();

CREATE TRIGGER guard_lifecycle BEFORE INSERT OR UPDATE ON chat_app.messages FOR EACH ROW EXECUTE FUNCTION chat_app.guard_message_lifecycle();

CREATE TRIGGER guard_link BEFORE INSERT OR DELETE OR UPDATE ON chat_app.message_files FOR EACH ROW EXECUTE FUNCTION chat_app.guard_message_file();

CREATE TRIGGER guard_mapping BEFORE INSERT OR UPDATE ON chat_app.conversation_copy_files FOR EACH ROW EXECUTE FUNCTION chat_app.guard_copy_file();

CREATE TRIGGER guard_scope BEFORE INSERT OR UPDATE ON chat_app.conversation_copy_jobs FOR EACH ROW EXECUTE FUNCTION chat_app.guard_copy_scope();

CREATE TRIGGER guard_scope BEFORE INSERT OR UPDATE ON chat_app.conversation_folders FOR EACH ROW EXECUTE FUNCTION chat_app.guard_conversation_scope();

CREATE TRIGGER guard_scope BEFORE INSERT OR UPDATE ON chat_app.conversation_shares FOR EACH ROW EXECUTE FUNCTION chat_app.guard_share_scope();

CREATE TRIGGER guard_scope BEFORE INSERT OR UPDATE ON chat_app.conversations FOR EACH ROW EXECUTE FUNCTION chat_app.guard_conversation_scope();

CREATE TRIGGER immutable_version BEFORE DELETE OR UPDATE ON chat_app.stored_files FOR EACH ROW EXECUTE FUNCTION chat_app.guard_stored_object();

CREATE TRIGGER lock_org BEFORE INSERT OR DELETE OR UPDATE ON chat_app.member_role_assignments FOR EACH ROW EXECUTE FUNCTION chat_app.lock_organization_mutation();

CREATE TRIGGER lock_org BEFORE INSERT OR DELETE OR UPDATE ON chat_app.organization_members FOR EACH ROW EXECUTE FUNCTION chat_app.lock_organization_mutation();

CREATE TRIGGER lock_org BEFORE INSERT OR DELETE OR UPDATE ON chat_app.organization_roles FOR EACH ROW EXECUTE FUNCTION chat_app.lock_organization_mutation();

CREATE TRIGGER lock_tree BEFORE INSERT OR UPDATE ON chat_app.messages FOR EACH ROW EXECUTE FUNCTION chat_app.lock_message_tree();

CREATE TRIGGER no_delete BEFORE DELETE ON chat_app.messages FOR EACH ROW EXECUTE FUNCTION chat_app.forbid_message_delete();

CREATE TRIGGER no_truncate BEFORE TRUNCATE ON chat_app.message_files FOR EACH STATEMENT EXECUTE FUNCTION chat_app.forbid_message_delete();

CREATE TRIGGER no_truncate BEFORE TRUNCATE ON chat_app.messages FOR EACH STATEMENT EXECUTE FUNCTION chat_app.forbid_message_delete();

CREATE TRIGGER provision_org AFTER INSERT ON chat_app.organizations FOR EACH ROW EXECUTE FUNCTION chat_app.provision_organization();

CREATE TRIGGER provision_workspace AFTER INSERT ON chat_app.users FOR EACH ROW EXECUTE FUNCTION chat_app.provision_personal_workspace();

CREATE CONSTRAINT TRIGGER retain_owner AFTER INSERT OR DELETE OR UPDATE ON chat_app.member_role_assignments DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION chat_app.check_organization_owner();

CREATE CONSTRAINT TRIGGER retain_owner AFTER INSERT OR DELETE OR UPDATE ON chat_app.organization_members DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION chat_app.check_organization_owner();

CREATE CONSTRAINT TRIGGER retain_owner AFTER INSERT OR DELETE OR UPDATE ON chat_app.organization_roles DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION chat_app.check_organization_owner();

CREATE TRIGGER revoke_shares AFTER UPDATE OF deleted_at ON chat_app.conversations FOR EACH ROW WHEN (((old.deleted_at IS NULL) AND (new.deleted_at IS NOT NULL))) EXECUTE FUNCTION chat_app.revoke_deleted_conversation_shares();

CREATE TRIGGER revoke_shares AFTER UPDATE OF is_active ON chat_app.organization_members FOR EACH ROW WHEN ((old.is_active AND (NOT new.is_active))) EXECUTE FUNCTION chat_app.revoke_departed_member_shares();

CREATE TRIGGER revoke_shares_on_delete AFTER DELETE ON chat_app.organization_members FOR EACH ROW EXECUTE FUNCTION chat_app.revoke_departed_member_shares();

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.conversation_copy_files FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.conversation_copy_jobs FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.conversation_folders FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.conversation_shares FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.conversations FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.member_role_assignments FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.messages FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.organization_invitations FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.organization_members FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.organization_roles FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.organizations FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.refresh_tokens FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.user_accounts FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.users FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.verifications FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.workspaces FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

CREATE CONSTRAINT TRIGGER user_message_final AFTER INSERT OR UPDATE ON chat_app.messages DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION chat_app.check_user_message_final();

CREATE CONSTRAINT TRIGGER valid_completion AFTER INSERT OR UPDATE ON chat_app.conversation_copy_jobs DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION chat_app.check_copy_completion();

CREATE CONSTRAINT TRIGGER valid_publication AFTER INSERT OR UPDATE ON chat_app.conversation_shares DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION chat_app.check_snapshot_publication();

CREATE CONSTRAINT TRIGGER valid_tree AFTER INSERT OR UPDATE ON chat_app.messages DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION chat_app.check_message_tree();

CREATE CONSTRAINT TRIGGER valid_tree AFTER INSERT OR UPDATE ON chat_app.share_snapshot_messages DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION chat_app.check_message_tree();

ALTER TABLE ONLY chat_app.conversation_copy_files
    ADD CONSTRAINT conversation_copy_files_job_id_fkey FOREIGN KEY (job_id) REFERENCES chat_app.conversation_copy_jobs(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.conversation_copy_jobs
    ADD CONSTRAINT conversation_copy_jobs_requested_by_fkey FOREIGN KEY (requested_by) REFERENCES chat_app.users(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.conversation_copy_jobs
    ADD CONSTRAINT conversation_copy_jobs_snapshot_id_fkey FOREIGN KEY (snapshot_id) REFERENCES chat_app.share_snapshots(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.conversation_copy_jobs
    ADD CONSTRAINT conversation_copy_jobs_target_conversation_id_target_works_fkey FOREIGN KEY (target_conversation_id, target_workspace_id) REFERENCES chat_app.conversations(id, workspace_id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.conversation_copy_jobs
    ADD CONSTRAINT conversation_copy_jobs_target_workspace_id_fkey FOREIGN KEY (target_workspace_id) REFERENCES chat_app.workspaces(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.conversation_folders
    ADD CONSTRAINT conversation_folders_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES chat_app.users(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.conversation_folders
    ADD CONSTRAINT conversation_folders_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES chat_app.workspaces(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.conversation_shares
    ADD CONSTRAINT conversation_shares_created_by_fkey FOREIGN KEY (created_by) REFERENCES chat_app.users(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.conversation_shares
    ADD CONSTRAINT conversation_shares_current_snapshot_fk FOREIGN KEY (id, current_snapshot_id) REFERENCES chat_app.share_snapshots(share_id, id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE ONLY chat_app.conversation_shares
    ADD CONSTRAINT conversation_shares_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES chat_app.organizations(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.conversation_shares
    ADD CONSTRAINT conversation_shares_source_conversation_id_workspace_id_fkey FOREIGN KEY (source_conversation_id, workspace_id) REFERENCES chat_app.conversations(id, workspace_id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.conversation_shares
    ADD CONSTRAINT conversation_shares_workspace_id_organization_id_fkey FOREIGN KEY (workspace_id, organization_id) REFERENCES chat_app.workspaces(id, organization_id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.conversations
    ADD CONSTRAINT conversations_current_message_fk FOREIGN KEY (id, current_message_id) REFERENCES chat_app.messages(conversation_id, id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE ONLY chat_app.conversations
    ADD CONSTRAINT conversations_folder_scope_fk FOREIGN KEY (folder_id, workspace_id, owner_user_id) REFERENCES chat_app.conversation_folders(id, workspace_id, owner_user_id) ON DELETE SET NULL (folder_id);

ALTER TABLE ONLY chat_app.conversations
    ADD CONSTRAINT conversations_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES chat_app.users(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.conversations
    ADD CONSTRAINT conversations_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES chat_app.workspaces(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.conversation_copy_files
    ADD CONSTRAINT copy_source_stored_file_fk FOREIGN KEY (source_stored_file_id) REFERENCES chat_app.stored_files(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.conversation_copy_files
    ADD CONSTRAINT copy_target_stored_file_fk FOREIGN KEY (target_stored_file_id) REFERENCES chat_app.stored_files(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.member_role_assignments
    ADD CONSTRAINT member_role_assignments_member_id_organization_id_fkey FOREIGN KEY (member_id, organization_id) REFERENCES chat_app.organization_members(id, organization_id) ON DELETE CASCADE;

ALTER TABLE ONLY chat_app.member_role_assignments
    ADD CONSTRAINT member_role_assignments_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES chat_app.organizations(id) ON DELETE CASCADE;

ALTER TABLE ONLY chat_app.member_role_assignments
    ADD CONSTRAINT member_role_assignments_role_id_organization_id_fkey FOREIGN KEY (role_id, organization_id) REFERENCES chat_app.organization_roles(id, organization_id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.message_files
    ADD CONSTRAINT message_files_message_id_fkey FOREIGN KEY (message_id) REFERENCES chat_app.messages(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.message_files
    ADD CONSTRAINT message_files_stored_file_id_fkey FOREIGN KEY (stored_file_id) REFERENCES chat_app.stored_files(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.messages
    ADD CONSTRAINT messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES chat_app.conversations(id) ON DELETE CASCADE;

ALTER TABLE ONLY chat_app.messages
    ADD CONSTRAINT messages_conversation_id_parent_message_id_fkey FOREIGN KEY (conversation_id, parent_message_id) REFERENCES chat_app.messages(conversation_id, id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE ONLY chat_app.organization_invitations
    ADD CONSTRAINT organization_invitations_accepted_by_fkey FOREIGN KEY (accepted_by) REFERENCES chat_app.users(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.organization_invitations
    ADD CONSTRAINT organization_invitations_invited_by_fkey FOREIGN KEY (invited_by) REFERENCES chat_app.users(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.organization_invitations
    ADD CONSTRAINT organization_invitations_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES chat_app.organizations(id) ON DELETE CASCADE;

ALTER TABLE ONLY chat_app.organization_members
    ADD CONSTRAINT organization_members_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES chat_app.organizations(id) ON DELETE CASCADE;

ALTER TABLE ONLY chat_app.organization_members
    ADD CONSTRAINT organization_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES chat_app.users(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.organization_roles
    ADD CONSTRAINT organization_roles_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES chat_app.organizations(id) ON DELETE CASCADE;

ALTER TABLE ONLY chat_app.organizations
    ADD CONSTRAINT organizations_created_by_fkey FOREIGN KEY (created_by) REFERENCES chat_app.users(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.refresh_tokens
    ADD CONSTRAINT refresh_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES chat_app.users(id) ON DELETE CASCADE;

ALTER TABLE ONLY chat_app.role_permissions
    ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES chat_app.permissions(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.role_permissions
    ADD CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES chat_app.organization_roles(id) ON DELETE CASCADE;

ALTER TABLE ONLY chat_app.share_snapshot_files
    ADD CONSTRAINT share_snapshot_files_snapshot_id_workspace_id_fkey FOREIGN KEY (snapshot_id, workspace_id) REFERENCES chat_app.share_snapshots(id, workspace_id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.share_snapshot_message_files
    ADD CONSTRAINT share_snapshot_message_files_snapshot_id_file_id_fkey FOREIGN KEY (snapshot_id, stored_file_id) REFERENCES chat_app.share_snapshot_files(snapshot_id, stored_file_id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.share_snapshot_message_files
    ADD CONSTRAINT share_snapshot_message_files_snapshot_id_message_id_fkey FOREIGN KEY (snapshot_id, message_id) REFERENCES chat_app.share_snapshot_messages(snapshot_id, id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.share_snapshot_messages
    ADD CONSTRAINT share_snapshot_messages_snapshot_id_fkey FOREIGN KEY (snapshot_id) REFERENCES chat_app.share_snapshots(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.share_snapshot_messages
    ADD CONSTRAINT share_snapshot_messages_snapshot_id_parent_message_id_fkey FOREIGN KEY (snapshot_id, parent_message_id) REFERENCES chat_app.share_snapshot_messages(snapshot_id, id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE ONLY chat_app.share_snapshots
    ADD CONSTRAINT share_snapshots_current_message_fk FOREIGN KEY (id, current_message_id) REFERENCES chat_app.share_snapshot_messages(snapshot_id, id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE ONLY chat_app.share_snapshots
    ADD CONSTRAINT share_snapshots_share_id_workspace_id_fkey FOREIGN KEY (share_id, workspace_id) REFERENCES chat_app.conversation_shares(id, workspace_id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.share_snapshot_files
    ADD CONSTRAINT snapshot_stored_file_fk FOREIGN KEY (stored_file_id) REFERENCES chat_app.stored_files(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.stored_files
    ADD CONSTRAINT stored_files_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES chat_app.users(id) ON DELETE SET NULL;

ALTER TABLE ONLY chat_app.user_accounts
    ADD CONSTRAINT user_accounts_user_id_fkey FOREIGN KEY (user_id) REFERENCES chat_app.users(id) ON DELETE CASCADE;

ALTER TABLE ONLY chat_app.workspaces
    ADD CONSTRAINT workspaces_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES chat_app.organizations(id) ON DELETE RESTRICT;

ALTER TABLE ONLY chat_app.workspaces
    ADD CONSTRAINT workspaces_personal_user_id_fkey FOREIGN KEY (personal_user_id) REFERENCES chat_app.users(id) ON DELETE RESTRICT;
