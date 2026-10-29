-- Run after phase 1 + phase 2 / part 1 on an isolated scratch database.
-- Fixture transaction rolls back. Full AG-UI/S3 execution belongs to integration tests.
\set ON_ERROR_STOP on
BEGIN;
SET LOCAL search_path = chat_app, public;
CREATE FUNCTION pg_temp.assert_true(ok boolean, label text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    IF ok IS DISTINCT FROM true THEN RAISE EXCEPTION 'FAIL: %', label; END IF;
    RAISE NOTICE 'PASS: %', label;
END;
$$;
CREATE FUNCTION pg_temp.expect_failure(statement text, label text) RETURNS void LANGUAGE plpgsql AS $$
DECLARE rejected boolean := false;
BEGIN
    BEGIN
        EXECUTE statement;
        SET CONSTRAINTS ALL IMMEDIATE;
    EXCEPTION WHEN integrity_constraint_violation OR raise_exception THEN rejected := true;
    END;
    IF NOT rejected THEN RAISE EXCEPTION 'FAIL (invalid data accepted): %', label; END IF;
    RAISE NOTICE 'PASS: %', label;
END;
$$;
DO $$
DECLARE
    a uuid; b uuid; outsider uuid; aw uuid; bw uuid; org uuid; ow uuid;
    c uuid; other_c uuid; oc uuid; m uuid; answer uuid; branch uuid;
    cyc1 uuid := uuidv7(); cyc2 uuid := uuidv7();
    sf uuid; f uuid; new_sf uuid; new_f uuid;
    sh uuid; ss uuid; sm uuid; sm_a uuid; sm_b uuid;
    target uuid; bad_target uuid; job uuid; org_share uuid; org_snap uuid;
    payload jsonb := '[{"id":"agui-u1","role":"user","content":"Question"}]';
    result jsonb := '[{"id":"agui-a1","role":"assistant","toolCalls":[{"id":"call-1","type":"function","function":{"name":"search","arguments":"{}"}}]},{"id":"agui-t1","role":"tool","toolCallId":"call-1","content":"Tool output"},{"id":"agui-a2","role":"assistant","content":"Answer"}]';
    extra jsonb := '[{"type":"file_search","toolCallId":"call-1","output":"Tool output","sources":[]}]';
BEGIN
    PERFORM pg_temp.assert_true(NOT EXISTS (
        SELECT 1 FROM information_schema.columns WHERE table_schema='chat_app' AND
        ((table_name='conversations' AND column_name IN ('title_source','revision','status','availability_status'))
        OR (table_name='messages' AND column_name IN ('position','revision','finish_reason','error_code','error_message','origin','completed_at'))
        OR (table_name='conversation_user_states' AND column_name IN ('last_read_at','last_opened_at')))
    ), 'removed fields absent');
    PERFORM pg_temp.assert_true(to_regclass('chat_app.conversation_tags') IS NULL
        AND to_regclass('chat_app.conversation_tag_assignments') IS NULL, 'tag tables not created');
    INSERT INTO users(name,email) VALUES ('A','p2-a@example.test') RETURNING id INTO a;
    INSERT INTO users(name,email,is_superuser) VALUES ('B','p2-b@example.test',true) RETURNING id INTO b;
    INSERT INTO users(name,email) VALUES ('Outside','p2-outside@example.test') RETURNING id INTO outsider;
    SELECT id INTO aw FROM workspaces WHERE personal_user_id=a;
    SELECT id INTO bw FROM workspaces WHERE personal_user_id=b;
    INSERT INTO organizations(name,created_by) VALUES ('P2 organization',a) RETURNING id INTO org;
    SELECT id INTO ow FROM workspaces WHERE organization_id=org;
    INSERT INTO organization_members(organization_id,user_id) VALUES (org,b);
    INSERT INTO conversations(workspace_id,owner_user_id) VALUES (aw,a) RETURNING id INTO c;
    INSERT INTO conversations(workspace_id,owner_user_id) VALUES (aw,a) RETURNING id INTO other_c;
    INSERT INTO conversations(workspace_id,owner_user_id) VALUES (ow,a) RETURNING id INTO oc;
    INSERT INTO messages(conversation_id,role,content) VALUES (c,'user',payload) RETURNING id INTO m;
    INSERT INTO messages(conversation_id,parent_message_id,role,content,attachments) VALUES (c,m,'assistant',result,extra) RETURNING id INTO answer;
    INSERT INTO messages(conversation_id,parent_message_id,role,content) VALUES (c,m,'assistant','[{"id":"agui-alt","role":"assistant","content":"Alternative"}]') RETURNING id INTO branch;
    UPDATE conversations SET current_message_id=branch WHERE id=c;
    SET CONSTRAINTS ALL IMMEDIATE;
    SET CONSTRAINTS ALL DEFERRED;
    PERFORM pg_temp.assert_true((SELECT count(*)=2 FROM messages WHERE parent_message_id=m), 'regenerate preserves sibling branches without position');
    PERFORM pg_temp.assert_true((SELECT content=result AND attachments=extra FROM messages WHERE id=answer), 'AG-UI tool calls/results and duplicated attachment output preserved');
    PERFORM pg_temp.expect_failure(format('INSERT INTO messages(conversation_id,role,content) VALUES (%L,''tool'',''[]'')', c), 'only user/assistant SQL roles');
    PERFORM pg_temp.expect_failure(format('INSERT INTO messages(conversation_id,role,content) VALUES (%L,''user'',''"plain old string"'')', c), 'raw content string rejected in favor of AG-UI bundle');
    PERFORM pg_temp.expect_failure(format('INSERT INTO messages(conversation_id,role,content) VALUES (%L,''assistant'',''[{"id":"s","role":"system","content":"secret"}]'')',c), 'system prompt excluded from product transcript bundle');
    PERFORM pg_temp.expect_failure(format('INSERT INTO messages(conversation_id,parent_message_id,role,content) VALUES (%L,%L,''user'',%L)',other_c,m,payload), 'parent cannot cross conversations');
    PERFORM pg_temp.expect_failure(format('UPDATE messages SET parent_message_id=%L WHERE id=%L',branch,m), 'existing message cannot be reparented');
    PERFORM pg_temp.expect_failure(format('INSERT INTO messages(id,conversation_id,parent_message_id,role,content) VALUES (%L,%L,%L,''assistant'',''[]''),(%L,%L,%L,''assistant'',''[]'')',cyc1,c,cyc2,cyc2,c,cyc1), 'deferred multi-row cycle rejected without position');
    PERFORM pg_temp.expect_failure(format('DELETE FROM messages WHERE id=%L',m), 'individual message deletion rejected');
    PERFORM pg_temp.expect_failure('TRUNCATE messages CASCADE', 'message truncation rejected');
    INSERT INTO conversation_user_states(conversation_id,user_id,workspace_id,pinned_at) VALUES (c,a,aw,now());
    PERFORM pg_temp.expect_failure(format('INSERT INTO conversation_user_states(conversation_id,user_id,workspace_id) VALUES (%L,%L,%L)',c,b,aw), 'sidebar state does not grant outsider ownership');
    PERFORM pg_temp.assert_true(NOT can_read_conversation(b,c), 'superuser still cannot read private chat');
    INSERT INTO stored_files(bucket,object_key,original_name,content_type,visibility,size_bytes,checksum_sha256,uploaded_by)
        VALUES ('chat-test','private/a/report.pdf','report.pdf','application/pdf','private',10,repeat('a',64),a) RETURNING id INTO sf;
    INSERT INTO files(workspace_id,owner_user_id,stored_file_id,status) VALUES (aw,a,sf,'ready') RETURNING id INTO f;
    INSERT INTO chat_files(conversation_id,message_id,workspace_id,file_id,kind) VALUES (c,m,aw,f,'input'),(c,answer,aw,f,'output');
    PERFORM pg_temp.assert_true((SELECT count(*)=2 FROM chat_files WHERE file_id=f), 'one file may attach to multiple messages');
    PERFORM pg_temp.expect_failure(format('INSERT INTO chat_files(conversation_id,message_id,workspace_id,file_id) VALUES (%L,%L,%L,%L)',c,m,aw,f), 'duplicate file within one message rejected');
    PERFORM pg_temp.expect_failure(format('INSERT INTO chat_files(conversation_id,message_id,workspace_id,file_id) VALUES (%L,%L,%L,%L)',c,m,ow,f), 'file link cannot cross workspace');
    PERFORM pg_temp.expect_failure(format('UPDATE stored_files SET object_key=''private/replaced'' WHERE id=%L',sf), 'stored object identity immutable');
    PERFORM pg_temp.expect_failure(format('UPDATE stored_files SET deleted_at=now() WHERE id=%L',sf), 'referenced object cannot be soft-deleted');
    INSERT INTO conversation_shares(source_conversation_id,workspace_id,created_by,mode,link_token_hash)
        VALUES (c,aw,a,'public',repeat('b',64)) RETURNING id INTO sh;
    INSERT INTO share_snapshots(share_id,workspace_id,version,title) VALUES (sh,aw,1,'Snapshot') RETURNING id INTO ss;
    INSERT INTO share_snapshot_messages(snapshot_id,role,content,original_created_at) VALUES (ss,'user',payload,now()) RETURNING id INTO sm;
    INSERT INTO share_snapshot_messages(snapshot_id,parent_message_id,role,content,attachments,original_created_at)
        VALUES (ss,sm,'assistant',result,extra,now()) RETURNING id INTO sm_a;
    INSERT INTO share_snapshot_messages(snapshot_id,parent_message_id,role,content,original_created_at)
        VALUES (ss,sm,'assistant','[{"id":"agui-alt","role":"assistant","content":"Alternative"}]',now()) RETURNING id INTO sm_b;
    INSERT INTO share_snapshot_files VALUES (ss,aw,f);
    INSERT INTO share_snapshot_message_files VALUES (ss,sm,f);
    UPDATE share_snapshots SET current_message_id=sm_b,sealed_at=now() WHERE id=ss;
    UPDATE conversation_shares SET current_snapshot_id=ss WHERE id=sh;
    SET CONSTRAINTS ALL IMMEDIATE;
    SET CONSTRAINTS ALL DEFERRED;
    PERFORM pg_temp.assert_true(can_read_share(NULL,sh) AND can_read_share_file(NULL,sh,f), 'anonymous public snapshot file access preserved');
    PERFORM pg_temp.assert_true(NOT can_read_conversation_file(b,c,f), 'public snapshot does not grant live source file access');
    PERFORM pg_temp.assert_true((SELECT attachments=extra FROM share_snapshot_messages WHERE id=sm_a), 'snapshot retains duplicated attachment output');
    PERFORM pg_temp.expect_failure(format('UPDATE share_snapshot_messages SET attachments=''[]'' WHERE snapshot_id=%L',ss), 'sealed snapshot attachments immutable');
    INSERT INTO conversations(workspace_id,owner_user_id) VALUES (bw,b) RETURNING id INTO target;
    INSERT INTO conversation_copy_jobs(requested_by,snapshot_id,target_workspace_id,target_conversation_id,client_request_id)
        VALUES (b,ss,bw,target,'p2-copy') RETURNING id INTO job;
    PERFORM pg_temp.assert_true(NOT can_read_conversation(b,target), 'unfinished copy hidden without conversation availability_status');
    PERFORM pg_temp.expect_failure(format('INSERT INTO conversation_shares(source_conversation_id,workspace_id,created_by,mode,link_token_hash) VALUES (%L,%L,%L,''public'',%L)',target,bw,b,repeat('c',64)), 'unfinished copy cannot be shared');
    INSERT INTO conversations(workspace_id,owner_user_id) VALUES (ow,b) RETURNING id INTO bad_target;
    PERFORM pg_temp.expect_failure(format('INSERT INTO conversation_copy_jobs(requested_by,snapshot_id,target_workspace_id,target_conversation_id,client_request_id) VALUES (%L,%L,%L,%L,''cross'')',b,ss,ow,bad_target), 'personal snapshot cannot copy into organization');
    PERFORM pg_temp.expect_failure(format('UPDATE conversation_copy_jobs SET status=''completed'',completed_at=now() WHERE id=%L',job), 'missing copied files prevents completion');
    INSERT INTO stored_files(bucket,object_key,original_name,content_type,visibility,size_bytes,checksum_sha256,uploaded_by)
        VALUES ('chat-test','private/b/copied-report.pdf','report.pdf','application/pdf','private',10,repeat('a',64),b) RETURNING id INTO new_sf;
    INSERT INTO files(workspace_id,owner_user_id,stored_file_id,status) VALUES (bw,b,new_sf,'ready') RETURNING id INTO new_f;
    INSERT INTO conversation_copy_files(job_id,source_file_id,target_file_id,status) VALUES (job,f,new_f,'copied');
    INSERT INTO messages(conversation_id,role,content) VALUES (target,'user',payload) RETURNING id INTO m;
    INSERT INTO messages(conversation_id,parent_message_id,role,content,attachments) VALUES (target,m,'assistant',result,extra) RETURNING id INTO answer;
    INSERT INTO chat_files(conversation_id,message_id,workspace_id,file_id) VALUES (target,m,bw,new_f);
    UPDATE conversations SET current_message_id=answer WHERE id=target;
    UPDATE conversation_copy_jobs SET status='completed',completed_at=now() WHERE id=job;
    SET CONSTRAINTS ALL IMMEDIATE;
    SET CONSTRAINTS ALL DEFERRED;
    PERFORM pg_temp.assert_true(can_read_conversation(b,target) AND can_read_conversation_file(b,target,new_f), 'completed copy readable with independent stored file');
    UPDATE conversations SET deleted_at=now() WHERE id=c;
    PERFORM pg_temp.assert_true(NOT can_read_share(NULL,sh) AND can_read_conversation(b,target), 'source soft delete revokes share but preserves completed copy');
    INSERT INTO messages(conversation_id,role,content) VALUES (oc,'user',payload) RETURNING id INTO m;
    INSERT INTO conversation_shares(source_conversation_id,workspace_id,created_by,mode,organization_id,link_token_hash)
        VALUES (oc,ow,a,'organization',org,repeat('d',64)) RETURNING id INTO org_share;
    INSERT INTO share_snapshots(share_id,workspace_id,version,title) VALUES (org_share,ow,1,'Org snapshot') RETURNING id INTO org_snap;
    INSERT INTO share_snapshot_messages(snapshot_id,role,content,original_created_at) VALUES (org_snap,'user',payload,now()) RETURNING id INTO sm;
    UPDATE share_snapshots SET current_message_id=sm,sealed_at=now() WHERE id=org_snap;
    UPDATE conversation_shares SET current_snapshot_id=org_snap WHERE id=org_share;
    PERFORM pg_temp.assert_true(can_read_share(b,org_share) AND NOT can_read_share(NULL,org_share)
        AND NOT can_read_share(outsider,org_share), 'org snapshot remains same-organization only');
    SET CONSTRAINTS ALL IMMEDIATE;
END;
$$;
ROLLBACK;
