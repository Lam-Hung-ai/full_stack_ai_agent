-- Run AFTER phase 1 -> phase 2 part 1 -> phase 2 final, on a scratch DB.
-- Fixtures and pg_temp helpers are rolled back. No real S3/LLM integration.
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
    SET CONSTRAINTS ALL DEFERRED;
    RAISE NOTICE 'PASS: %', label;
END;
$$;
CREATE FUNCTION pg_temp.user_message(cid uuid, payload jsonb, fs uuid[] DEFAULT '{}') RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE mid uuid; fid uuid;
BEGIN
    INSERT INTO chat_app.messages(conversation_id,role,content) VALUES (cid,'user',payload) RETURNING id INTO mid;
    FOREACH fid IN ARRAY fs LOOP INSERT INTO chat_app.message_files VALUES (mid,fid); END LOOP;
    UPDATE chat_app.messages SET status='completed' WHERE id=mid;
    RETURN mid;
END;
$$;
DO $$
DECLARE
    a uuid; b uuid; stranger uuid; aw uuid; bw uuid; org uuid; ow uuid;
    c uuid; c2 uuid; bc uuid; oc uuid; folder uuid; bf uuid; ofolder uuid;
    u uuid; ans uuid; failed uuid; cancelled uuid; pending uuid;
    f uuid; f2 uuid; public_f uuid; copied_f uuid;
    sh uuid; ss uuid; su uuid; sa uuid; target uuid; tu uuid; ta uuid; job uuid;
    cyc1 uuid:=uuidv7(); cyc2 uuid:=uuidv7();
    payload jsonb := '[{"id":"u1","role":"user","content":"Question"}]';
    output jsonb := '[{"id":"a1","role":"assistant","toolCalls":[{"id":"call-1","type":"function","function":{"name":"search","arguments":"{}"}}]},{"id":"t1","role":"tool","toolCallId":"call-1","content":"Tool output"},{"id":"a2","role":"assistant","content":"Answer"}]';
    extra jsonb := '[{"type":"file_search","toolCallId":"call-1","output":"Tool output"}]';
BEGIN
    PERFORM pg_temp.assert_true(to_regclass('chat_app.files') IS NULL AND to_regclass('chat_app.chat_files') IS NULL
        AND to_regclass('chat_app.conversation_user_states') IS NULL, 'redundant file/sidebar tables removed');
    PERFORM pg_temp.assert_true(NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='chat_app' AND
        ((table_name='conversation_folders' AND column_name='parent_id') OR
         (table_name='conversations' AND column_name IN ('title_source','revision','status','availability_status')) OR
         (table_name='messages' AND column_name IN ('position','revision','finish_reason','error_code','error_message','origin','completed_at')))),
        'flat folders and previously removed columns stay removed');
    INSERT INTO users(name,email) VALUES ('Final A','final-a@example.test') RETURNING id INTO a;
    INSERT INTO users(name,email,is_superuser) VALUES ('Final B','final-b@example.test',true) RETURNING id INTO b;
    INSERT INTO users(name,email) VALUES ('Outside','final-outside@example.test') RETURNING id INTO stranger;
    SELECT id INTO aw FROM workspaces WHERE personal_user_id=a;
    SELECT id INTO bw FROM workspaces WHERE personal_user_id=b;
    INSERT INTO organizations(name,created_by) VALUES ('Final organization',a) RETURNING id INTO org;
    SELECT id INTO ow FROM workspaces WHERE organization_id=org;
    INSERT INTO organization_members(organization_id,user_id) VALUES (org,b);
    INSERT INTO conversations(workspace_id,owner_user_id) VALUES (aw,a) RETURNING id INTO c;
    INSERT INTO conversations(workspace_id,owner_user_id) VALUES (aw,a) RETURNING id INTO c2;
    INSERT INTO conversations(workspace_id,owner_user_id) VALUES (bw,b) RETURNING id INTO bc;
    INSERT INTO conversations(workspace_id,owner_user_id) VALUES (ow,a) RETURNING id INTO oc;
    INSERT INTO conversation_folders(workspace_id,owner_user_id,name) VALUES (aw,a,'Reports') RETURNING id INTO folder;
    INSERT INTO conversation_folders(workspace_id,owner_user_id,name) VALUES (bw,b,'Reports') RETURNING id INTO bf;
    INSERT INTO conversation_folders(workspace_id,owner_user_id,name) VALUES (ow,a,'Reports') RETURNING id INTO ofolder;
    UPDATE conversations SET folder_id=folder,pinned_at=now() WHERE id=c;
    PERFORM pg_temp.assert_true((SELECT pinned_at IS NOT NULL AND folder_id=folder FROM conversations WHERE id=c), 'pin and folder coexist directly on conversation');
    PERFORM pg_temp.expect_failure(format('INSERT INTO conversation_folders(workspace_id,owner_user_id,name) VALUES (%L,%L,'' reports '')',aw,a), 'duplicate normalized folder name rejected');
    PERFORM pg_temp.expect_failure(format('UPDATE conversations SET folder_id=%L WHERE id=%L',bf,c), 'folder cannot cross owner');
    PERFORM pg_temp.expect_failure(format('UPDATE conversations SET folder_id=%L WHERE id=%L',ofolder,c), 'folder cannot cross workspace');
    DELETE FROM conversation_folders WHERE id=folder;
    PERFORM pg_temp.assert_true((SELECT folder_id IS NULL AND pinned_at IS NOT NULL FROM conversations WHERE id=c), 'deleting folder preserves conversation and pin');
    PERFORM pg_temp.assert_true((SELECT count(*)=2 FROM pg_indexes WHERE schemaname='chat_app' AND indexname IN ('idx_conversations_pinned','idx_conversations_folder')), 'pin/folder partial indexes present');
    INSERT INTO stored_files(bucket,object_key,original_name,content_type,visibility,size_bytes,checksum_sha256,uploaded_by)
        VALUES ('chat-test','private/a/report.pdf','report.pdf','application/pdf','private',10,repeat('a',64),a) RETURNING id INTO f;
    INSERT INTO stored_files(bucket,object_key,original_name,content_type,visibility,size_bytes,uploaded_by)
        VALUES ('chat-test','private/a/second.pdf','second.pdf','application/pdf','private',5,a) RETURNING id INTO f2;
    PERFORM pg_temp.assert_true((SELECT metadata='{}'::jsonb FROM stored_files WHERE id=f), 'metadata defaults to empty object');
    UPDATE stored_files SET metadata='{"extraction":{"page_count":24},"rag":{"parser":"docling"}}' WHERE id=f;
    PERFORM pg_temp.expect_failure(format('UPDATE stored_files SET metadata=''[]'' WHERE id=%L',f), 'metadata array rejected');
    u := pg_temp.user_message(c,payload,ARRAY[f,f2]);
    SET CONSTRAINTS ALL IMMEDIATE;
    SET CONSTRAINTS ALL DEFERRED;
    PERFORM pg_temp.assert_true((SELECT status='completed' FROM messages WHERE id=u)
        AND (SELECT count(*)=2 FROM message_files WHERE message_id=u), 'user plus multiple files committed atomically');
    PERFORM pg_temp.expect_failure(format('INSERT INTO messages(conversation_id,role,content) VALUES (%L,''user'',%L)',c,payload), 'user cannot remain pending at commit');
    PERFORM pg_temp.expect_failure(format('UPDATE messages SET content=%L WHERE id=%L',payload,u), 'completed user content immutable');
    INSERT INTO messages(conversation_id,parent_message_id,role) VALUES (c,u,'assistant') RETURNING id INTO ans;
    PERFORM pg_temp.assert_true((SELECT status='pending' FROM messages WHERE id=ans), 'assistant starts pending');
    PERFORM pg_temp.expect_failure(format('INSERT INTO messages(conversation_id,parent_message_id,role) VALUES (%L,%L,''assistant'')',c,u), 'one active assistant per conversation');
    UPDATE messages SET status='running' WHERE id=ans;
    PERFORM pg_temp.expect_failure(format('UPDATE messages SET status=''pending'' WHERE id=%L',ans), 'running cannot return to pending');
    INSERT INTO message_files VALUES (ans,f);
    PERFORM pg_temp.expect_failure(format('INSERT INTO message_files VALUES (%L,%L)',ans,f), 'duplicate message-file pair rejected');
    UPDATE messages SET content=output,attachments=extra,status='completed' WHERE id=ans;
    UPDATE conversations SET current_message_id=ans WHERE id=c;
    PERFORM pg_temp.assert_true((SELECT content=output AND attachments=extra FROM messages WHERE id=ans), 'AG-UI and duplicated tool output retained at finalization');
    PERFORM pg_temp.expect_failure(format('UPDATE messages SET attachments=''[]'' WHERE id=%L',ans), 'terminal attachments immutable');
    PERFORM pg_temp.expect_failure(format('UPDATE messages SET status=''running'' WHERE id=%L',ans), 'terminal message cannot restart');
    PERFORM pg_temp.expect_failure(format('INSERT INTO message_files VALUES (%L,%L)',ans,f2), 'cannot add terminal file link');
    PERFORM pg_temp.expect_failure(format('DELETE FROM message_files WHERE message_id=%L',ans), 'cannot remove terminal file link');
    PERFORM pg_temp.expect_failure(format('DELETE FROM messages WHERE id=%L',ans), 'individual message deletion disabled');
    PERFORM pg_temp.expect_failure('TRUNCATE message_files', 'terminal links cannot be truncated');
    INSERT INTO messages(conversation_id,parent_message_id,role) VALUES (c,u,'assistant') RETURNING id INTO failed;
    UPDATE messages SET status='running' WHERE id=failed;
    UPDATE messages SET content='[{"id":"partial-f","role":"assistant","content":"Partial before error"}]',status='failed' WHERE id=failed;
    INSERT INTO messages(conversation_id,parent_message_id,role) VALUES (c,u,'assistant') RETURNING id INTO cancelled;
    UPDATE messages SET content='[{"id":"partial-c","role":"assistant","content":"Partial before stop"}]',status='cancelled' WHERE id=cancelled;
    PERFORM pg_temp.assert_true((SELECT count(*)=3 FROM messages WHERE parent_message_id=u)
        AND (SELECT content->0->>'content'='Partial before error' FROM messages WHERE id=failed)
        AND (SELECT content->0->>'content'='Partial before stop' FROM messages WHERE id=cancelled), 'regenerate keeps branches and failed/cancelled partial text');
    PERFORM pg_temp.expect_failure(format('INSERT INTO messages(conversation_id,role,status) VALUES (%L,''assistant'',''streaming'')',c), 'unsupported status rejected');
    PERFORM pg_temp.expect_failure(format('INSERT INTO messages(conversation_id,role,content) VALUES (%L,''tool'',''[]'')',c), 'SQL roles remain user/assistant');
    PERFORM pg_temp.expect_failure(format('INSERT INTO messages(conversation_id,role,content) VALUES (%L,''assistant'',''[{"id":"s","role":"system"}]'')',c), 'internal system prompts excluded');
    PERFORM pg_temp.expect_failure(format('INSERT INTO messages(conversation_id,parent_message_id,role,content) VALUES (%L,%L,''assistant'',''[]'')',c2,u), 'parent cannot cross conversation');
    PERFORM pg_temp.expect_failure(format('INSERT INTO messages(id,conversation_id,parent_message_id,role,status) VALUES (%L,%L,%L,''assistant'',''failed''),(%L,%L,%L,''assistant'',''failed'')',cyc1,c,cyc2,cyc2,c,cyc1), 'deferred message cycles still rejected');
    pending := pg_temp.user_message(c2,payload,ARRAY[f]);
    PERFORM pg_temp.assert_true((SELECT count(*)=3 FROM message_files WHERE stored_file_id=f), 'same file reused within same owner/workspace');
    PERFORM pg_temp.expect_failure(format('SELECT pg_temp.user_message(%L,%L,ARRAY[%L::uuid])',oc,payload,f), 'object cannot cross personal/organization scope');
    PERFORM pg_temp.expect_failure(format('SELECT pg_temp.user_message(%L,%L,ARRAY[%L::uuid])',bc,payload,f), 'object cannot cross owner');
    INSERT INTO stored_files(bucket,object_key,original_name,content_type,visibility,size_bytes,uploaded_by)
        VALUES ('chat-test','public/a.pdf','a.pdf','application/pdf','public',1,a) RETURNING id INTO public_f;
    PERFORM pg_temp.expect_failure(format('SELECT pg_temp.user_message(%L,%L,ARRAY[%L::uuid])',c2,payload,public_f), 'chat rejects public storage objects');
    PERFORM pg_temp.expect_failure(format('UPDATE stored_files SET object_key=''private/replaced'' WHERE id=%L',f), 'object identity immutable');
    PERFORM pg_temp.expect_failure(format('UPDATE stored_files SET deleted_at=now() WHERE id=%L',f), 'referenced stored object cannot be soft deleted');
    PERFORM pg_temp.assert_true(can_read_conversation_file(a,c,f) AND NOT can_read_conversation_file(b,c,f), 'owner-only live file access with no superuser bypass');
    INSERT INTO messages(conversation_id,parent_message_id,role) VALUES (c,u,'assistant') RETURNING id INTO pending;
    PERFORM pg_temp.expect_failure(format('INSERT INTO conversation_shares(source_conversation_id,workspace_id,created_by,mode,link_token_hash) VALUES (%L,%L,%L,''public'',%L)',c,aw,a,repeat('1',64)), 'cannot create share while pending');
    UPDATE messages SET status='cancelled' WHERE id=pending;
    INSERT INTO conversation_shares(source_conversation_id,workspace_id,created_by,mode,link_token_hash)
        VALUES (c,aw,a,'public',repeat('1',64)) RETURNING id INTO sh;
    INSERT INTO share_snapshots(share_id,workspace_id,version,title) VALUES (sh,aw,1,'Snapshot') RETURNING id INTO ss;
    INSERT INTO share_snapshot_messages(snapshot_id,role,content,original_created_at)
        VALUES (ss,'user',payload,now()) RETURNING id INTO su;
    INSERT INTO share_snapshot_messages(snapshot_id,parent_message_id,role,content,attachments,status,original_created_at)
        VALUES (ss,su,'assistant',output,extra,'completed',now()) RETURNING id INTO sa;
    INSERT INTO share_snapshot_files(snapshot_id,workspace_id,stored_file_id,metadata)
        SELECT ss,aw,id,'{"extraction":{"page_count":24}}'::jsonb FROM stored_files WHERE id=f;
    INSERT INTO share_snapshot_message_files VALUES (ss,su,f);
    UPDATE share_snapshots SET current_message_id=sa,sealed_at=now() WHERE id=ss;
    UPDATE conversation_shares SET current_snapshot_id=ss WHERE id=sh;
    SET CONSTRAINTS ALL IMMEDIATE;
    SET CONSTRAINTS ALL DEFERRED;
    PERFORM pg_temp.assert_true(can_read_share(NULL,sh) AND can_read_share_file(NULL,sh,f), 'public snapshot grants anonymous file download only through link');
    PERFORM pg_temp.assert_true(NOT can_read_share_file(NULL,sh,f2), 'file omitted from snapshot cannot be downloaded via share');
    UPDATE stored_files SET metadata='{"extraction":{"page_count":25}}' WHERE id=f;
    PERFORM pg_temp.assert_true((SELECT metadata#>>'{extraction,page_count}'='24' FROM share_snapshot_files WHERE snapshot_id=ss AND stored_file_id=f), 'snapshot metadata independent of later processing');
    PERFORM pg_temp.expect_failure(format('UPDATE share_snapshot_files SET metadata=''{}'' WHERE snapshot_id=%L',ss), 'sealed snapshot file metadata immutable');
    INSERT INTO messages(conversation_id,parent_message_id,role,status) VALUES (c,u,'assistant','running') RETURNING id INTO pending;
    PERFORM pg_temp.assert_true(can_read_share_file(NULL,sh,f), 'old snapshot stays readable during new running answer');
    PERFORM pg_temp.expect_failure(format('INSERT INTO share_snapshots(share_id,workspace_id,version,title) VALUES (%L,%L,2,''Blocked'')',sh,aw), 'cannot update snapshot while running');
    UPDATE messages SET status='failed' WHERE id=pending;
    INSERT INTO conversations(workspace_id,owner_user_id) VALUES (bw,b) RETURNING id INTO target;
    INSERT INTO conversation_copy_jobs(requested_by,snapshot_id,target_workspace_id,target_conversation_id,client_request_id)
        VALUES (b,ss,bw,target,'final-copy') RETURNING id INTO job;
    PERFORM pg_temp.assert_true(NOT can_read_conversation(b,target), 'unfinished physical copy hidden');
    PERFORM pg_temp.expect_failure(format('UPDATE conversation_copy_jobs SET status=''completed'',completed_at=now() WHERE id=%L',job), 'copy cannot finish without files');
    INSERT INTO stored_files(bucket,object_key,original_name,content_type,visibility,size_bytes,checksum_sha256,uploaded_by,metadata)
        VALUES ('chat-test','private/b/copied.pdf','report.pdf','application/pdf','private',10,repeat('a',64),b,'{"extraction":{"page_count":24}}') RETURNING id INTO copied_f;
    INSERT INTO conversation_copy_files(job_id,source_stored_file_id,target_stored_file_id,status) VALUES (job,f,copied_f,'copied');
    tu := pg_temp.user_message(target,payload,ARRAY[copied_f]);
    INSERT INTO messages(conversation_id,parent_message_id,role,content,attachments,status)
        VALUES (target,tu,'assistant',output,extra,'completed') RETURNING id INTO ta;
    UPDATE conversations SET current_message_id=ta WHERE id=target;
    UPDATE conversation_copy_jobs SET status='completed',completed_at=now() WHERE id=job;
    SET CONSTRAINTS ALL IMMEDIATE;
    SET CONSTRAINTS ALL DEFERRED;
    PERFORM pg_temp.assert_true(can_read_conversation_file(b,target,copied_f)
        AND NOT can_read_conversation_file(b,target,f), 'completed copy uses independent stored file');
    PERFORM pg_temp.assert_true((SELECT folder_id IS NULL AND pinned_at IS NULL AND archived_at IS NULL FROM conversations WHERE id=target), 'copy does not inherit sidebar organization');
    UPDATE conversations SET deleted_at=now() WHERE id=c;
    PERFORM pg_temp.assert_true(NOT can_read_share_file(NULL,sh,f) AND can_read_conversation_file(b,target,copied_f), 'source deletion revokes share but preserves copy');
    u := pg_temp.user_message(oc,payload);
    INSERT INTO conversation_shares(source_conversation_id,workspace_id,created_by,mode,organization_id,link_token_hash)
        VALUES (oc,ow,a,'organization',org,repeat('2',64)) RETURNING id INTO sh;
    INSERT INTO share_snapshots(share_id,workspace_id,version,title) VALUES (sh,ow,1,'Org snapshot') RETURNING id INTO ss;
    INSERT INTO share_snapshot_messages(snapshot_id,role,content,original_created_at) VALUES (ss,'user',payload,now()) RETURNING id INTO su;
    UPDATE share_snapshots SET current_message_id=su,sealed_at=now() WHERE id=ss;
    UPDATE conversation_shares SET current_snapshot_id=ss WHERE id=sh;
    SET CONSTRAINTS ALL IMMEDIATE;
    PERFORM pg_temp.assert_true(can_read_share(b,sh) AND NOT can_read_share(NULL,sh)
        AND NOT can_read_share(stranger,sh), 'organization sharing stays internal');
END;
$$;
ROLLBACK;
