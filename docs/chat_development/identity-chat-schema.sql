-- Sinh từ docs/chat_development/identity-chat-database-design.md muc 4.
-- Da chay sach tren PostgreSQL 16.15 voi ON_ERROR_STOP=1 (xem muc 9).
-- Vung execution/stream/tool/source CHUA co trong file nay.

CREATE SCHEMA app;

CREATE TABLE app.app_user (
    id            uuid PRIMARY KEY,
    issuer        text        NOT NULL,
    subject       text        NOT NULL,
    email         text,
    display_name  text        NOT NULL,
    status        text        NOT NULL DEFAULT 'active'
                  CHECK (status IN ('active', 'suspended', 'deleted')),
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT app_user_identity_uq UNIQUE (issuer, subject)
);

-- Open WebUI: unique email phải không phân biệt hoa thường, và phải là
-- functional index; model khai unique=True nhưng database chỉ có index này.
CREATE UNIQUE INDEX app_user_email_lower_uq
    ON app.app_user (lower(email))
    WHERE email IS NOT NULL AND status <> 'deleted';

CREATE TABLE app.organization (
    id               uuid PRIMARY KEY,
    slug             text        NOT NULL UNIQUE,
    name             text        NOT NULL,
    status           text        NOT NULL DEFAULT 'active'
                     CHECK (status IN ('active', 'suspended', 'deleted')),
    policy_revision  bigint      NOT NULL DEFAULT 1,
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now()
);

-- Dòng membership KHÔNG BAO GIỜ bị hard-delete: revoke đổi status.
-- Đây là điều kiện để FK từ conversation/run/audit tới actor luôn resolve được.
CREATE TABLE app.org_membership (
    id          uuid PRIMARY KEY,
    org_id      uuid        NOT NULL REFERENCES app.organization (id),
    user_id     uuid        NOT NULL REFERENCES app.app_user (id),
    org_role    text        NOT NULL CHECK (org_role IN ('owner', 'admin', 'member')),
    status      text        NOT NULL DEFAULT 'invited'
                CHECK (status IN ('invited', 'active', 'suspended', 'revoked')),
    revision    bigint      NOT NULL DEFAULT 1,
    joined_at   timestamptz,
    revoked_at  timestamptz,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT org_membership_uq     UNIQUE (org_id, user_id),
    CONSTRAINT org_membership_org_uq UNIQUE (org_id, id)
);

-- Bài học Open WebUI migration 1ce6ade7d93b: unique dẫn đầu bằng org_id
-- không trả lời được "user này ở org nào". Thiếu index này thì mọi request
-- quét toàn bảng membership của cả deployment.
CREATE INDEX org_membership_by_user
    ON app.org_membership (user_id, org_id)
    WHERE status = 'active';

CREATE TABLE app.team (
    id          uuid PRIMARY KEY,
    org_id      uuid        NOT NULL REFERENCES app.organization (id) ON DELETE CASCADE,
    name        text        NOT NULL,
    description text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT team_org_uq UNIQUE (org_id, id)
);
CREATE UNIQUE INDEX team_name_uq ON app.team (org_id, lower(name));

-- Membership là bảng nối, KHÔNG phải mảng trên team.
-- LibreChat group.memberIds là mảng nhúng -> chạm trần 16 MB mỗi document.
CREATE TABLE app.team_membership (
    org_id        uuid NOT NULL,
    team_id       uuid NOT NULL,
    membership_id uuid NOT NULL,
    added_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (team_id, membership_id),
    FOREIGN KEY (org_id, team_id)       REFERENCES app.team (org_id, id)           ON DELETE CASCADE,
    FOREIGN KEY (org_id, membership_id) REFERENCES app.org_membership (org_id, id) ON DELETE CASCADE
);
CREATE INDEX team_membership_by_member ON app.team_membership (membership_id, team_id);

CREATE TABLE app.service_principal (
    id          uuid PRIMARY KEY,
    org_id      uuid        NOT NULL REFERENCES app.organization (id) ON DELETE CASCADE,
    name        text        NOT NULL,
    status      text        NOT NULL DEFAULT 'active'
                CHECK (status IN ('active', 'disabled')),
    created_at  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT service_principal_org_uq UNIQUE (org_id, id)
);
CREATE TABLE app.principal (
    id                    uuid PRIMARY KEY,
    org_id                uuid NOT NULL REFERENCES app.organization (id) ON DELETE CASCADE,
    membership_id         uuid,
    team_id               uuid,
    service_principal_id  uuid,
    kind                  text GENERATED ALWAYS AS (
                              CASE
                                  WHEN membership_id        IS NOT NULL THEN 'member'
                                  WHEN team_id              IS NOT NULL THEN 'team'
                                  ELSE                                       'service'
                              END) STORED,
    created_at            timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT principal_single_target
        CHECK (num_nonnulls(membership_id, team_id, service_principal_id) = 1),
    CONSTRAINT principal_org_uq UNIQUE (org_id, id),
    FOREIGN KEY (org_id, membership_id)        REFERENCES app.org_membership (org_id, id)    ON DELETE CASCADE,
    FOREIGN KEY (org_id, team_id)              REFERENCES app.team (org_id, id)              ON DELETE CASCADE,
    FOREIGN KEY (org_id, service_principal_id) REFERENCES app.service_principal (org_id, id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX principal_member_uq  ON app.principal (membership_id)        WHERE membership_id        IS NOT NULL;
CREATE UNIQUE INDEX principal_team_uq    ON app.principal (team_id)              WHERE team_id              IS NOT NULL;
CREATE UNIQUE INDEX principal_service_uq ON app.principal (service_principal_id) WHERE service_principal_id IS NOT NULL;
CREATE TABLE app.conversation (
    id                        uuid PRIMARY KEY,
    org_id                    uuid        NOT NULL REFERENCES app.organization (id),
    created_by_membership_id  uuid        NOT NULL,   -- lịch sử actor, bất biến
    custodian_membership_id   uuid        NOT NULL,   -- trách nhiệm quản lý hiện tại
    agent_key                 text        NOT NULL DEFAULT 'handy',
    agent_version             text        NOT NULL,   -- ghim lúc tạo (Onyx: incognito_record_mode)
    default_branch_id         uuid,
    title                     text,
    title_source              text        NOT NULL DEFAULT 'pending'
                              CHECK (title_source IN ('pending', 'fallback', 'auto', 'user')),
    title_revision            bigint      NOT NULL DEFAULT 0,
    visibility                text        NOT NULL DEFAULT 'private'
                              CHECK (visibility IN ('private', 'org')),
    activity_at               timestamptz NOT NULL DEFAULT now(),
    revision                  bigint      NOT NULL DEFAULT 1,
    deleted_at                timestamptz,
    CONSTRAINT conversation_title_len_chk CHECK (title IS NULL OR length(title) <= 512),
    created_at                timestamptz NOT NULL DEFAULT now(),
    updated_at                timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT conversation_org_uq UNIQUE (org_id, id),
    FOREIGN KEY (org_id, created_by_membership_id) REFERENCES app.org_membership (org_id, id),
    FOREIGN KEY (org_id, custodian_membership_id)  REFERENCES app.org_membership (org_id, id)
);

CREATE TABLE app.branch (
    id                   uuid PRIMARY KEY,
    org_id               uuid        NOT NULL,
    conversation_id      uuid        NOT NULL,
    parent_branch_id     uuid,
    fork_item_id         uuid,
    fork_ordinal         bigint,
    head_item_id         uuid,
    next_ordinal         bigint      NOT NULL DEFAULT 1 CHECK (next_ordinal >= 1),
    native_thread_id     text        NOT NULL,   -- reference mờ đục, KHÔNG FK vào lg_state
    graph_version        text        NOT NULL,
    fork_checkpoint_ref  jsonb,
    status               text        NOT NULL DEFAULT 'preparing'
                         CHECK (status IN ('preparing', 'ready', 'failed', 'retired')),
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT branch_org_uq           UNIQUE (org_id, id),
    CONSTRAINT branch_conversation_uq  UNIQUE (conversation_id, id),
    CONSTRAINT branch_native_thread_uq UNIQUE (native_thread_id),
    CONSTRAINT branch_fork_triple_chk
        CHECK (num_nonnulls(parent_branch_id, fork_item_id, fork_ordinal) IN (0, 3)),
    FOREIGN KEY (org_id, conversation_id)        REFERENCES app.conversation (org_id, id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id, parent_branch_id) REFERENCES app.branch (conversation_id, id)
);

ALTER TABLE app.conversation
    ADD CONSTRAINT conversation_default_branch_fk
    FOREIGN KEY (id, default_branch_id) REFERENCES app.branch (conversation_id, id)
    DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE app.transcript_item (
    id                   uuid PRIMARY KEY,
    org_id               uuid        NOT NULL,
    conversation_id      uuid        NOT NULL,
    origin_branch_id     uuid        NOT NULL,
    origin_run_id        uuid,       -- NULL cho item nhập/import ngoài run
    parent_item_id       uuid,
    role                 text        NOT NULL
                         CHECK (role IN ('user', 'assistant', 'tool', 'system')),
    kind                 text        NOT NULL,
    content              jsonb       NOT NULL DEFAULT '[]'::jsonb,  -- danh sách content block
    content_revision     bigint      NOT NULL DEFAULT 1,
    status               text        NOT NULL
                         CHECK (status IN ('pending', 'streaming', 'completed',
                                           'interrupted', 'replaced', 'failed')),
    checkpoint_boundary  jsonb,
    created_at           timestamptz NOT NULL DEFAULT now(),
    completed_at         timestamptz,
    -- Bien tren cung. Ngan sach that (coalesce batch, snapshot) o tang app.
    CONSTRAINT transcript_item_content_size_chk CHECK (pg_column_size(content) <= 1048576),
    CONSTRAINT transcript_item_org_uq          UNIQUE (org_id, id),
    CONSTRAINT transcript_item_conversation_uq UNIQUE (conversation_id, id),
    FOREIGN KEY (org_id, conversation_id)           REFERENCES app.conversation (org_id, id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id, parent_item_id)   REFERENCES app.transcript_item (conversation_id, id),
    FOREIGN KEY (conversation_id, origin_branch_id) REFERENCES app.branch (conversation_id, id)
);
-- Thẩm quyền sắp xếp để phân trang. ordinal cấp từ branch.next_ordinal
-- trong cùng transaction append (row lock trên branch serialize append/nhánh).
CREATE TABLE app.branch_item (
    org_id          uuid   NOT NULL,
    conversation_id uuid   NOT NULL,
    branch_id       uuid   NOT NULL,
    ordinal         bigint NOT NULL CHECK (ordinal > 0),
    item_id         uuid   NOT NULL,
    PRIMARY KEY (branch_id, ordinal),
    CONSTRAINT branch_item_uq UNIQUE (branch_id, item_id),
    FOREIGN KEY (conversation_id, branch_id) REFERENCES app.branch (conversation_id, id)          ON DELETE CASCADE,
    FOREIGN KEY (conversation_id, item_id)   REFERENCES app.transcript_item (conversation_id, id) ON DELETE CASCADE
);
-- Trạng thái cá nhân. Dòng này KHÔNG CẤP QUYỀN.
CREATE TABLE app.conversation_view (
    org_id             uuid NOT NULL,
    membership_id      uuid NOT NULL,
    conversation_id    uuid NOT NULL,
    selected_branch_id uuid,
    last_seen_item_id  uuid,
    last_seen_at       timestamptz,
    pinned_at          timestamptz,
    archived_at        timestamptz,
    updated_at         timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (membership_id, conversation_id),
    FOREIGN KEY (org_id, membership_id)   REFERENCES app.org_membership (org_id, id) ON DELETE CASCADE,
    FOREIGN KEY (org_id, conversation_id) REFERENCES app.conversation (org_id, id)   ON DELETE CASCADE,
    FOREIGN KEY (conversation_id, selected_branch_id) REFERENCES app.branch (conversation_id, id)
);
CREATE TABLE app.conversation_grant (
    id                        uuid PRIMARY KEY,
    org_id                    uuid        NOT NULL,
    conversation_id           uuid        NOT NULL,
    principal_id              uuid        NOT NULL,
    role_key                  text        NOT NULL
                              CHECK (role_key IN ('viewer', 'collaborator')),
    granted_by_membership_id  uuid        NOT NULL,
    granted_at                timestamptz NOT NULL DEFAULT now(),
    expires_at                timestamptz,
    CONSTRAINT conversation_grant_uq UNIQUE (conversation_id, principal_id, role_key),
    FOREIGN KEY (org_id, conversation_id)          REFERENCES app.conversation (org_id, id)      ON DELETE CASCADE,
    FOREIGN KEY (org_id, principal_id)             REFERENCES app.principal (org_id, id)         ON DELETE CASCADE,
    FOREIGN KEY (org_id, granted_by_membership_id) REFERENCES app.org_membership (org_id, id)
);
CREATE INDEX conversation_grant_by_principal
    ON app.conversation_grant (principal_id, conversation_id);
CREATE TABLE app.shared_result (
    id                       uuid PRIMARY KEY,
    org_id                   uuid        NOT NULL,
    conversation_id          uuid        NOT NULL,
    created_by_membership_id uuid        NOT NULL,
    current_version_no       integer     NOT NULL DEFAULT 0,
    created_at               timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT shared_result_org_uq UNIQUE (org_id, id),
    FOREIGN KEY (org_id, conversation_id) REFERENCES app.conversation (org_id, id) ON DELETE CASCADE
);

CREATE TABLE app.shared_result_version (
    id                      uuid PRIMARY KEY,
    org_id                  uuid        NOT NULL,
    shared_result_id        uuid        NOT NULL,
    version_no              integer     NOT NULL CHECK (version_no > 0),
    boundary_branch_id      uuid        NOT NULL,
    boundary_ordinal        bigint      NOT NULL,
    payload                 jsonb       NOT NULL,   -- snapshot bất biến, KHÔNG copy byte file
    payload_hash            text        NOT NULL,
    CONSTRAINT shared_result_payload_size_chk CHECK (pg_column_size(payload) <= 8388608),
    status                  text        NOT NULL DEFAULT 'draft'
                            CHECK (status IN ('draft', 'published', 'revoked', 'expired')),
    published_at            timestamptz,
    published_by_membership_id uuid,
    CONSTRAINT shared_result_version_uq  UNIQUE (shared_result_id, version_no),
    CONSTRAINT shared_result_version_org UNIQUE (org_id, id),
    FOREIGN KEY (org_id, shared_result_id) REFERENCES app.shared_result (org_id, id) ON DELETE CASCADE
);
CREATE TABLE app.stored_object (
    id                        uuid PRIMARY KEY,
    org_id                    uuid        NOT NULL REFERENCES app.organization (id),
    bucket                    text        NOT NULL,
    object_key                text        NOT NULL,
    object_version            text        NOT NULL DEFAULT '',
    checksum                  text,
    byte_size                 bigint      CHECK (byte_size >= 0),
    mime_type                 text,
    status                    text        NOT NULL DEFAULT 'uploading'
                              CHECK (status IN ('uploading', 'scanning', 'ready',
                                                'failed', 'deleting', 'deleted')),
    created_by_membership_id  uuid,
    created_at                timestamptz NOT NULL DEFAULT now(),
    -- "Một deadline, không bao giờ là một cờ" (LibreChat file.deletionRetryAt):
    -- dòng bị tái dùng có thể bị trì hoãn, không bị mắc kẹt.
    deletion_retry_at         timestamptz,
    deletion_attempts         integer     NOT NULL DEFAULT 0,
    CONSTRAINT stored_object_key_uq UNIQUE (bucket, object_key, object_version),
    CONSTRAINT stored_object_org_uq UNIQUE (org_id, id)
);
CREATE INDEX stored_object_deletion_sweep
    ON app.stored_object (deletion_retry_at, id)
    WHERE status IN ('deleting', 'failed');

-- Open WebUI chat_file: bảng nối tồn tại để tìm mọi file trong một chat
-- mà không phải duyệt từng message, và để unique ở mức database.
CREATE TABLE app.conversation_object (
    org_id          uuid NOT NULL,
    conversation_id uuid NOT NULL,
    object_id       uuid NOT NULL,
    item_id         uuid,
    purpose         text NOT NULL CHECK (purpose IN ('attachment', 'artifact')),
    created_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (conversation_id, object_id, purpose),
    FOREIGN KEY (org_id, conversation_id) REFERENCES app.conversation (org_id, id)             ON DELETE CASCADE,
    FOREIGN KEY (org_id, object_id)       REFERENCES app.stored_object (org_id, id),
    FOREIGN KEY (conversation_id, item_id) REFERENCES app.transcript_item (conversation_id, id) ON DELETE SET NULL
);
CREATE INDEX conversation_object_by_object ON app.conversation_object (object_id);
CREATE INDEX conversation_object_by_item   ON app.conversation_object (item_id) WHERE item_id IS NOT NULL;
-- Native Store giữ value. App chỉ giữ provenance + policy.
-- Onyx memory.conversation_id/message_id cố ý KHÔNG FK -> xóa chat không dọn
-- memory. Ở đây FK thật về phía app, còn phía native dọn bằng job có trạng thái.
CREATE TABLE app.memory_provenance (
    id                 uuid PRIMARY KEY,
    org_id             uuid        NOT NULL,
    membership_id      uuid        NOT NULL,
    native_namespace   text        NOT NULL,
    native_key         text        NOT NULL,
    value_revision     bigint      NOT NULL DEFAULT 1,
    value_hash         text        NOT NULL,
    source_item_id     uuid,
    status             text        NOT NULL DEFAULT 'active'
                       CHECK (status IN ('active', 'superseded', 'deleting', 'deleted')),
    created_at         timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT memory_provenance_key_uq UNIQUE (native_namespace, native_key, value_revision),
    FOREIGN KEY (org_id, membership_id) REFERENCES app.org_membership (org_id, id),
    FOREIGN KEY (source_item_id)        REFERENCES app.transcript_item (id) ON DELETE SET NULL
);

-- Append-only. Đây là CHỖ DUY NHẤT (resource_type, resource_id) dạng nhãn
-- là đúng: resource được phép bị purge, audit phải sống lâu hơn nó.
CREATE TABLE app.audit_event (
    id                  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    org_id              uuid        NOT NULL REFERENCES app.organization (id),
    occurred_at         timestamptz NOT NULL DEFAULT now(),
    actor_membership_id uuid,
    actor_label         text        NOT NULL,
    action              text        NOT NULL,
    resource_type       text        NOT NULL,
    resource_label      text        NOT NULL,
    outcome             text        NOT NULL CHECK (outcome IN ('allowed', 'denied', 'error')),
    policy_revision     bigint,
    details             jsonb       NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT audit_event_details_size_chk CHECK (pg_column_size(details) <= 65536),
    FOREIGN KEY (org_id, actor_membership_id) REFERENCES app.org_membership (org_id, id) ON DELETE SET NULL
);
CREATE INDEX audit_event_by_resource ON app.audit_event (org_id, resource_type, resource_label, occurred_at DESC, id DESC);
CREATE INDEX audit_event_by_actor    ON app.audit_event (org_id, actor_membership_id, occurred_at DESC, id DESC);
-- Phân trang nhánh, sau khi service đã authorize và resolve branch.


-- ---------------------------------------------------------------------------
-- (1) updated_at phai thuc su cap nhat. DEFAULT now() chi chay luc INSERT.
-- ---------------------------------------------------------------------------
CREATE FUNCTION app.touch_updated_at() RETURNS trigger LANGUAGE plpgsql AS $fn$
BEGIN NEW.updated_at := now(); RETURN NEW; END $fn$;

DO $do$
DECLARE t text;
BEGIN
  FOR t IN SELECT c.relname FROM pg_class c
           JOIN pg_namespace n ON n.oid = c.relnamespace
           JOIN pg_attribute a ON a.attrelid = c.oid
           WHERE n.nspname = 'app' AND c.relkind = 'r' AND a.attname = 'updated_at'
  LOOP
    EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE ON app.%I
                    FOR EACH ROW EXECUTE FUNCTION app.touch_updated_at()', t || '_touch', t);
  END LOOP;
END $do$;

-- ---------------------------------------------------------------------------
-- (5) Moi membership/team/service principal co dung mot dong app.principal.
--     Thieu dong nay thi khong cap grant duoc ma database khong bao gi.
-- ---------------------------------------------------------------------------
CREATE FUNCTION app.ensure_principal() RETURNS trigger LANGUAGE plpgsql AS $fn$
BEGIN
  IF TG_TABLE_NAME = 'org_membership' THEN
    INSERT INTO app.principal (id, org_id, membership_id)
    VALUES (gen_random_uuid(), NEW.org_id, NEW.id) ON CONFLICT DO NOTHING;
  ELSIF TG_TABLE_NAME = 'team' THEN
    INSERT INTO app.principal (id, org_id, team_id)
    VALUES (gen_random_uuid(), NEW.org_id, NEW.id) ON CONFLICT DO NOTHING;
  ELSE
    INSERT INTO app.principal (id, org_id, service_principal_id)
    VALUES (gen_random_uuid(), NEW.org_id, NEW.id) ON CONFLICT DO NOTHING;
  END IF;
  RETURN NEW;
END $fn$;

CREATE TRIGGER org_membership_principal AFTER INSERT ON app.org_membership
  FOR EACH ROW EXECUTE FUNCTION app.ensure_principal();
CREATE TRIGGER team_principal AFTER INSERT ON app.team
  FOR EACH ROW EXECUTE FUNCTION app.ensure_principal();
CREATE TRIGGER service_principal_principal AFTER INSERT ON app.service_principal
  FOR EACH ROW EXECUTE FUNCTION app.ensure_principal();
