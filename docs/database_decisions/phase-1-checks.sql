-- Regression checks for a scratch database after phase-1-schema.sql.
-- All fixtures roll back. Never run against a production database.
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
    EXCEPTION WHEN integrity_constraint_violation OR raise_exception THEN
        rejected := true;
    END;
    IF NOT rejected THEN RAISE EXCEPTION 'FAIL (accepted invalid data): %', label; END IF;
    RAISE NOTICE 'PASS: %', label;
END;
$$;
DO $$
DECLARE
    alice uuid; bob uuid; outsider uuid; org uuid; org2 uuid;
    personal uuid; bob_personal uuid; org_ws uuid; org2_ws uuid;
    c uuid; oc uuid; msg uuid; branch uuid; alternative uuid; f uuid;
    sh uuid; ss uuid; sm uuid; sm2 uuid; sm3 uuid; osh uuid; oss uuid;
    target uuid; target2 uuid; job uuid; new_file uuid;
    alice_member uuid; bob_member uuid; owner_role uuid;
BEGIN
    INSERT INTO users(name, email) VALUES ('Alice', 'alice@example.test') RETURNING id INTO alice;
    INSERT INTO users(name, email, is_superuser) VALUES ('Bob', 'bob@example.test', true) RETURNING id INTO bob;
    INSERT INTO users(name, email) VALUES ('Outsider', 'outside@example.test') RETURNING id INTO outsider;
    SELECT id INTO personal FROM workspaces WHERE personal_user_id = alice;
    SELECT id INTO bob_personal FROM workspaces WHERE personal_user_id = bob;
    PERFORM pg_temp.assert_true(personal IS NOT NULL AND bob_personal IS NOT NULL, 'automatic personal workspaces');
    PERFORM pg_temp.expect_failure($q$INSERT INTO users(name,email) VALUES ('Duplicate','ALICE@example.test')$q$, 'case-insensitive email uniqueness');
    INSERT INTO organizations(name, created_by) VALUES ('Org A', alice) RETURNING id INTO org;
    INSERT INTO organizations(name, created_by) VALUES ('Org B', outsider) RETURNING id INTO org2;
    SELECT id INTO org_ws FROM workspaces WHERE organization_id = org;
    SELECT id INTO org2_ws FROM workspaces WHERE organization_id = org2;
    SELECT id INTO alice_member FROM organization_members WHERE organization_id = org AND user_id = alice;
    SELECT id INTO owner_role FROM organization_roles WHERE organization_id = org AND role_key = 'owner';
    PERFORM pg_temp.assert_true((SELECT count(*) = 3 FROM organization_roles WHERE organization_id = org), 'organization provisions three default roles');
    SET CONSTRAINTS ALL IMMEDIATE;
    SET CONSTRAINTS ALL DEFERRED;
    PERFORM pg_temp.expect_failure(format('UPDATE organization_members SET is_active=false WHERE id=%L', alice_member), 'cannot deactivate last owner membership');
    PERFORM pg_temp.expect_failure(format('UPDATE organization_roles SET is_active=false WHERE id=%L', owner_role), 'cannot disable last owner role');
    INSERT INTO organization_members(organization_id,user_id) VALUES (org,bob) RETURNING id INTO bob_member;
    PERFORM pg_temp.expect_failure(format('INSERT INTO member_role_assignments(organization_id,member_id,role_id) VALUES (%L,%L,%L)', org2,bob_member,owner_role), 'cross-organization role assignment rejected');
    PERFORM pg_temp.expect_failure(format('UPDATE workspaces SET personal_user_id=%L WHERE id=%L', outsider,personal), 'workspace ownership cannot move');
    INSERT INTO conversations(workspace_id,owner_user_id,title) VALUES (personal,alice,'Original') RETURNING id INTO c;
    INSERT INTO conversations(workspace_id,owner_user_id,title) VALUES (org_ws,alice,'Org private') RETURNING id INTO oc;
    PERFORM pg_temp.assert_true(NOT can_read_conversation(bob,c) AND NOT can_read_conversation(bob,oc), 'platform admin and org member cannot read others private chat');
    INSERT INTO messages(conversation_id,position,role,content) VALUES (c,0,'user','"Question"') RETURNING id INTO msg;
    INSERT INTO messages(conversation_id,parent_message_id,position,role,content) VALUES (c,msg,1,'assistant','"Answer"') RETURNING id INTO branch;
    INSERT INTO messages(conversation_id,parent_message_id,position,role,content) VALUES (c,msg,2,'assistant','"Alternative"') RETURNING id INTO alternative;
    UPDATE conversations SET current_message_id=alternative WHERE id=c;
    SET CONSTRAINTS ALL IMMEDIATE;
    SET CONSTRAINTS ALL DEFERRED;
    PERFORM pg_temp.expect_failure(format('UPDATE messages SET parent_message_id=%L WHERE id=%L', branch,msg), 'message cycles rejected');
    PERFORM pg_temp.expect_failure(format('UPDATE conversations SET current_message_id=%L WHERE id=%L', msg,oc), 'current message must belong to its conversation');
    INSERT INTO files(workspace_id,owner_user_id,filename,content_type,byte_size,sha256,storage_key,status)
        VALUES (personal,alice,'test.txt','text/plain',3,repeat('a',64),'alice/source-v1','ready') RETURNING id INTO f;
    INSERT INTO message_files VALUES (c,msg,personal,f);
    PERFORM pg_temp.expect_failure(format('INSERT INTO message_files VALUES (%L,%L,%L,%L)', c,msg,org_ws,f), 'attachment cannot cross workspace');
    INSERT INTO conversation_shares(source_conversation_id,workspace_id,created_by,mode,link_token_hash)
        VALUES (c,personal,alice,'public',repeat('b',64)) RETURNING id INTO sh;
    PERFORM pg_temp.expect_failure(format('INSERT INTO conversation_shares(source_conversation_id,workspace_id,created_by,mode,link_token_hash) VALUES (%L,%L,%L,''public'',%L)', oc,org_ws,alice,repeat('c',64)), 'organization cannot publish public share');
    INSERT INTO share_snapshots(share_id,workspace_id,version,title) VALUES (sh,personal,1,'Original') RETURNING id INTO ss;
    INSERT INTO share_snapshot_messages(snapshot_id,position,role,content,original_created_at) VALUES (ss,0,'user','"Question"',now()) RETURNING id INTO sm;
    INSERT INTO share_snapshot_messages(snapshot_id,parent_message_id,position,role,content,original_created_at) VALUES (ss,sm,1,'assistant','"Answer"',now()) RETURNING id INTO sm2;
    INSERT INTO share_snapshot_messages(snapshot_id,parent_message_id,position,role,content,original_created_at) VALUES (ss,sm,2,'assistant','"Alternative"',now()) RETURNING id INTO sm3;
    INSERT INTO share_snapshot_files VALUES (ss,personal,f);
    INSERT INTO share_snapshot_message_files VALUES (ss,sm,f);
    UPDATE share_snapshots SET current_message_id=sm3 WHERE id=ss;
    PERFORM pg_temp.expect_failure(format('UPDATE conversation_shares SET current_snapshot_id=%L WHERE id=%L', ss,sh), 'cannot publish unsealed snapshot');
    UPDATE share_snapshots SET sealed_at=now() WHERE id=ss;
    UPDATE conversation_shares SET current_snapshot_id=ss WHERE id=sh;
    SET CONSTRAINTS ALL IMMEDIATE;
    SET CONSTRAINTS ALL DEFERRED;
    PERFORM pg_temp.assert_true(can_read_share(NULL,sh), 'anonymous viewer can open public snapshot');
    PERFORM pg_temp.assert_true(can_read_share_file(NULL,sh,f) AND NOT can_read_share_file(NULL,sh,uuidv7()), 'public file access limited to snapshot attachments');
    PERFORM pg_temp.assert_true(NOT can_read_conversation_file(bob,c,f), 'admin cannot download private source attachment');
    PERFORM pg_temp.assert_true((SELECT count(*)=3 FROM share_snapshot_messages WHERE snapshot_id=ss), 'snapshot retains both branches');
    PERFORM pg_temp.expect_failure(format('UPDATE share_snapshot_messages SET content=''"Tampered"'' WHERE snapshot_id=%L', ss), 'sealed snapshot content immutable');
    PERFORM pg_temp.expect_failure(format('UPDATE files SET storage_key=''replaced'' WHERE id=%L', f), 'snapshot file bytes reference immutable');
    UPDATE messages SET content='"Edited later"' WHERE id=msg;
    PERFORM pg_temp.assert_true((SELECT content='"Question"' FROM share_snapshot_messages WHERE snapshot_id=ss AND id=sm), 'source editing does not change snapshot');
    INSERT INTO conversations(workspace_id,owner_user_id,status) VALUES (bob_personal,bob,'copying') RETURNING id INTO target;
    INSERT INTO conversation_copy_jobs(requested_by,snapshot_id,target_workspace_id,target_conversation_id,client_request_id)
        VALUES (bob,ss,bob_personal,target,'copy-1') RETURNING id INTO job;
    PERFORM pg_temp.expect_failure(format('INSERT INTO conversation_copy_jobs(requested_by,snapshot_id,target_workspace_id,target_conversation_id,client_request_id) VALUES (%L,%L,%L,%L,''copy-1'')', bob,ss,bob_personal,target), 'copy request is idempotent');
    INSERT INTO conversations(workspace_id,owner_user_id,status) VALUES (org_ws,bob,'copying') RETURNING id INTO target2;
    PERFORM pg_temp.expect_failure(format('INSERT INTO conversation_copy_jobs(requested_by,snapshot_id,target_workspace_id,target_conversation_id,client_request_id) VALUES (%L,%L,%L,%L,''cross-copy'')', bob,ss,org_ws,target2), 'personal share cannot copy into organization');
    PERFORM pg_temp.expect_failure(format('UPDATE conversation_copy_jobs SET status=''completed'',completed_at=now() WHERE id=%L', job), 'incomplete copy cannot complete');
    INSERT INTO files(workspace_id,owner_user_id,filename,content_type,byte_size,sha256,storage_key,status)
        VALUES (bob_personal,bob,'test.txt','text/plain',3,repeat('a',64),'bob/copied-v1','ready') RETURNING id INTO new_file;
    INSERT INTO conversation_copy_files(job_id,source_file_id,target_file_id,status) VALUES (job,f,new_file,'copied');
    INSERT INTO messages(conversation_id,position,role,content) VALUES (target,0,'user','"Question"') RETURNING id INTO msg;
    INSERT INTO messages(conversation_id,parent_message_id,position,role,content) VALUES (target,msg,1,'assistant','"Answer"');
    INSERT INTO messages(conversation_id,parent_message_id,position,role,content) VALUES (target,msg,2,'assistant','"Alternative"') RETURNING id INTO alternative;
    INSERT INTO message_files VALUES (target,msg,bob_personal,new_file);
    UPDATE conversations SET current_message_id=alternative,status='ready' WHERE id=target;
    UPDATE conversation_copy_jobs SET status='completed',completed_at=now() WHERE id=job;
    SET CONSTRAINTS ALL IMMEDIATE;
    SET CONSTRAINTS ALL DEFERRED;
    UPDATE conversations SET deleted_at=now() WHERE id=c;
    PERFORM pg_temp.assert_true(NOT can_read_share(NULL,sh), 'source deletion revokes public share');
    PERFORM pg_temp.assert_true(can_read_conversation(bob,target) AND (SELECT status='ready' FROM files WHERE id=new_file), 'completed copy survives source deletion with independent files');
    INSERT INTO messages(conversation_id,position,role,content) VALUES (oc,0,'user','"Org question"') RETURNING id INTO msg;
    INSERT INTO conversation_shares(source_conversation_id,workspace_id,created_by,mode,organization_id,link_token_hash)
        VALUES (oc,org_ws,alice,'organization',org,repeat('d',64)) RETURNING id INTO osh;
    INSERT INTO share_snapshots(share_id,workspace_id,version,title) VALUES (osh,org_ws,1,'Org private') RETURNING id INTO oss;
    INSERT INTO share_snapshot_messages(snapshot_id,position,role,content,original_created_at) VALUES (oss,0,'user','"Org question"',now()) RETURNING id INTO sm;
    UPDATE share_snapshots SET current_message_id=sm,sealed_at=now() WHERE id=oss;
    UPDATE conversation_shares SET current_snapshot_id=oss WHERE id=osh;
    PERFORM pg_temp.assert_true(can_read_share(bob,osh) AND NOT can_read_share(outsider,osh) AND NOT can_read_share(NULL,osh), 'org link requires active membership of same org');
    INSERT INTO member_role_assignments(organization_id,member_id,role_id) VALUES (org,bob_member,owner_role);
    UPDATE organization_members SET is_active=false,left_at=now() WHERE id=alice_member;
    PERFORM pg_temp.assert_true(NOT can_read_share(bob,osh), 'creator departure revokes org share');
    UPDATE organization_members SET is_active=true,left_at=NULL WHERE id=alice_member;
    PERFORM pg_temp.assert_true(NOT can_read_share(bob,osh), 'rejoining does not revive revoked share');
    SET CONSTRAINTS ALL IMMEDIATE;
END;
$$;
ROLLBACK;
