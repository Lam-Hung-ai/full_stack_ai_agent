-- Phase 4: approved durable pause/resume on messages. PostgreSQL 18+.
-- Apply ONCE after phase-2-final-schema.sql. Phase 3 has no SQL.
-- Does not rewrite old payloads or deploy application/runtime integrations.
BEGIN;
SET LOCAL search_path=chat_app,public;
ALTER TABLE messages ADD COLUMN metadata jsonb NOT NULL DEFAULT '{}'::jsonb
    CONSTRAINT messages_metadata_object_check CHECK (jsonb_typeof(metadata)='object');
ALTER TABLE messages DROP CONSTRAINT messages_status_check;
ALTER TABLE messages ADD CONSTRAINT messages_status_check
    CHECK (status IN ('pending','running','requires_action','completed','failed','cancelled'));
DROP INDEX messages_one_active_assistant_idx;
CREATE UNIQUE INDEX messages_one_active_assistant_idx ON messages(conversation_id)
    WHERE role='assistant' AND status IN ('pending','running','requires_action');
CREATE OR REPLACE FUNCTION assert_conversation_idle(p_conversation uuid) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(hashtextextended(p_conversation::text,42));
    IF EXISTS (SELECT 1 FROM chat_app.messages WHERE conversation_id=p_conversation
        AND status IN ('pending','running','requires_action')) THEN
        RAISE EXCEPTION 'Cannot build/publish snapshot while a response is unfinished';
    END IF;
END;
$$;
-- Same phase-2 copy completion check, adding the new nonterminal status.
CREATE OR REPLACE FUNCTION check_copy_completion() RETURNS trigger LANGUAGE plpgsql AS $$
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
-- Native saver tables are created/migrated by the pinned SDK's setup(), not
-- duplicated as handwritten application DDL. Use this schema in saver connections.
CREATE SCHEMA langgraph_checkpoints;
COMMENT ON COLUMN messages.metadata IS 'Backend-owned action/checkpoint state and resolved interactions. No client-controlled checkpoint pointers or credentials. Terminal messages remain immutable.';
COMMENT ON COLUMN messages.status IS 'pending/running/requires_action are nonterminal. Pause persists partial content and checkpoint atomically; completed/failed/cancelled are immutable.';
COMMENT ON SCHEMA langgraph_checkpoints IS 'Private LangGraph saver storage; SDK-managed migrations/checkpoints/blobs/writes. Not public chat history or an automatic recovery scheduler.';
COMMIT;
