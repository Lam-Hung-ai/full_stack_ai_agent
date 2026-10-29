-- Run after phase 1 -> phase 2 part 1 -> phase 2 final -> phase 4.
\set ON_ERROR_STOP on
BEGIN;
SET LOCAL search_path=chat_app,public;
CREATE FUNCTION pg_temp.ok(v boolean,label text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN IF v IS DISTINCT FROM true THEN RAISE EXCEPTION 'FAIL: %',label; END IF; RAISE NOTICE 'PASS: %',label; END;
$$;
CREATE FUNCTION pg_temp.reject(q text,label text) RETURNS void LANGUAGE plpgsql AS $$
DECLARE rejected boolean:=false;
BEGIN
    BEGIN EXECUTE q; SET CONSTRAINTS ALL IMMEDIATE;
    EXCEPTION WHEN integrity_constraint_violation OR raise_exception THEN rejected:=true; END;
    IF NOT rejected THEN RAISE EXCEPTION 'FAIL: invalid operation accepted: %',label; END IF;
    SET CONSTRAINTS ALL DEFERRED;
    RAISE NOTICE 'PASS: %',label;
END;
$$;
DO $$
DECLARE u uuid; w uuid; c uuid; m uuid; sh uuid; ss uuid; sm uuid; target uuid; job uuid;
    payload jsonb:='[{"id":"intro","role":"assistant","content":"Bạn muốn xuất CSV hay Excel?"},{"id":"interaction:1","role":"activity","activityType":"user_interaction","content":{"status":"waiting","kind":"user_question"}}]';
BEGIN
    INSERT INTO users(name,email) VALUES ('Phase4','phase4@example.test') RETURNING id INTO u;
    SELECT id INTO w FROM workspaces WHERE personal_user_id=u;
    INSERT INTO conversations(workspace_id,owner_user_id) VALUES (w,u) RETURNING id INTO c;
    INSERT INTO messages(conversation_id,role) VALUES (c,'assistant') RETURNING id INTO m;
    PERFORM pg_temp.ok((SELECT metadata='{}'::jsonb FROM messages WHERE id=m),'metadata defaults to object');
    PERFORM pg_temp.reject(format('UPDATE messages SET metadata=''[]'' WHERE id=%L',m),'metadata must be object');
    UPDATE messages SET status='running' WHERE id=m;
    UPDATE messages SET status='requires_action',content=payload,metadata='{"pending_action":{"action_id":"a1","expires_at":null}}' WHERE id=m;
    PERFORM pg_temp.ok((SELECT status='requires_action' AND content=payload FROM messages WHERE id=m),'pause saves partial text and activity');
    PERFORM pg_temp.reject(format('INSERT INTO messages(conversation_id,role) VALUES (%L,''assistant'')',c),'waiting counts as active assistant');
    PERFORM pg_temp.reject(format('SELECT assert_conversation_idle(%L)',c),'waiting blocks snapshot construction');
    PERFORM pg_temp.reject(format('INSERT INTO conversation_shares(source_conversation_id,workspace_id,created_by,mode,link_token_hash) VALUES (%L,%L,%L,''public'',%L)',c,w,u,repeat('c',64)),'waiting blocks new share');
    UPDATE messages SET status='running' WHERE id=m;
    UPDATE messages SET status='completed',metadata='{"actions":[{"response":"CSV"}]}' WHERE id=m;
    PERFORM pg_temp.reject(format('UPDATE messages SET metadata=''{}'' WHERE id=%L',m),'terminal metadata immutable');
    INSERT INTO conversation_shares(source_conversation_id,workspace_id,created_by,mode,link_token_hash)
        VALUES (c,w,u,'public',repeat('c',64)) RETURNING id INTO sh;
    INSERT INTO share_snapshots(share_id,workspace_id,version,title) VALUES (sh,w,1,'Phase4') RETURNING id INTO ss;
    INSERT INTO share_snapshot_messages(snapshot_id,role,content,original_created_at) VALUES (ss,'assistant',payload,now()) RETURNING id INTO sm;
    UPDATE share_snapshots SET current_message_id=sm,sealed_at=now() WHERE id=ss;
    UPDATE conversation_shares SET current_snapshot_id=ss WHERE id=sh;
    SET CONSTRAINTS ALL IMMEDIATE;
    SET CONSTRAINTS ALL DEFERRED;
    INSERT INTO messages(conversation_id,role,status) VALUES (c,'assistant','requires_action') RETURNING id INTO m;
    PERFORM pg_temp.ok(can_read_share(NULL,sh),'old snapshot stays readable during new pause');
    PERFORM pg_temp.reject(format('INSERT INTO share_snapshots(share_id,workspace_id,version,title) VALUES (%L,%L,2,''Blocked'')',sh,w),'new snapshot version blocked while waiting');
    UPDATE messages SET status='cancelled' WHERE id=m;
    INSERT INTO conversations(workspace_id,owner_user_id) VALUES (w,u) RETURNING id INTO target;
    INSERT INTO conversation_copy_jobs(requested_by,snapshot_id,target_workspace_id,target_conversation_id,client_request_id)
        VALUES (u,ss,w,target,'phase4-copy') RETURNING id INTO job;
    INSERT INTO messages(conversation_id,role,status) VALUES (target,'assistant','requires_action') RETURNING id INTO m;
    PERFORM pg_temp.reject(format('UPDATE conversation_copy_jobs SET status=''completed'',completed_at=now() WHERE id=%L',job),'copy cannot complete with waiting message');
    UPDATE messages SET status='cancelled' WHERE id=m;
    PERFORM pg_temp.reject(format('UPDATE messages SET status=''running'' WHERE id=%L',m),'cancelled message cannot resume');
    PERFORM pg_temp.reject(format('INSERT INTO messages(conversation_id,role,status,content) VALUES (%L,''user'',''requires_action'',''[{"id":"u","role":"user","content":"x"}]'')',c),'user cannot wait for action');
    PERFORM pg_temp.ok(to_regnamespace('langgraph_checkpoints') IS NOT NULL,'dedicated native checkpoint schema exists');
    PERFORM pg_temp.ok(to_regclass('chat_app.message_pending_actions') IS NULL AND to_regclass('chat_app.conversation_runs') IS NULL,'no action/run application table introduced');
    SET CONSTRAINTS ALL IMMEDIATE;
END;
$$;
ROLLBACK;
