# Thiết kế database: người dùng, tổ chức, hội thoại và lịch sử

Ngày: **27/10/2026**. Trạng thái: **đề xuất thiết kế kèm DDL đã chạy thử**. DDL ở mục 4 chạy sạch trên PostgreSQL 16.15, 9 bất biến đã kiểm bằng INSERT thật, 4 access path đã `EXPLAIN (ANALYZE, BUFFERS)` trên 100.000 item, chi phí fork đã đo (mục 9). Một vòng tự rà soát đã tìm và sửa 5 lỗi (mục 9.6); 5 nhóm bảng còn thiếu so với phạm vi được liệt kê ở mục 9.7. Chưa chạy test đồng thời, fault injection hoặc load test.

Phạm vi: identity, organization/membership/team, phân quyền tài nguyên, conversation, branch, transcript, history paging, chia sẻ, file và provenance memory. **Không** thay đổi phần đã chốt: FastAPI custom + LangGraph OSS + `ag_ui_langgraph.LangGraphAgent` + AG-UI SSE run/connect/stop, worker detached, journal commit trước SSE, Redis dựng lại được, native Saver/Store giữ nguyên.

Đầu vào: [Open WebUI](../database_research/open-webui-official-schema.md), [LibreChat](../database_research/librechat-full-schema.md), [Onyx](../database_research/onyx-full-schema.md), cộng [32 use case](./chat-use-cases-and-organization-access.md) và [review schema](./database-schema-review.md). Tài liệu này **cụ thể hóa** mục 5.1–5.2 và 5.5 của review thành DDL; các mục execution/stream/native của review và [thiết kế lưu trữ](./production-data-storage-design.md) vẫn giữ nguyên.

---

## 1. Vì sao vùng này chốt được DDL ngay

Phần execution (run/attempt/stream journal/checkpoint pin) phụ thuộc các ranh giới **chưa kiểm chứng**: `LangGraphAgent` có truyền được `durability` không, adapter có hỗ trợ fork checkpoint không, `AsyncPostgresSaver` ownership connection hoạt động ra sao dưới pooling. Vì vậy các tài liệu trước từ chối phát hành DDL cho chúng.

Vùng identity/org/chat/history **không có phụ thuộc đó**. Nó chỉ tham chiếu native storage bằng hai thứ mờ đục: `branch.native_thread_id` (text) và `checkpoint_ref` (jsonb). Không FK, không đọc bảng nội bộ thư viện. Nên vùng này viết migration được trước, và phần còn lại gắn vào sau.

---

## 2. Ba dự án dạy được gì

### 2.1. Đối chiếu nhanh

| Khía cạnh | Open WebUI (47 bảng) | LibreChat (53 model) | Onyx (167 bảng) | Chọn cho dự án |
|---|---|---|---|---|
| Engine | SQLite mặc định / PostgreSQL | MongoDB | PostgreSQL | PostgreSQL 16+ |
| Multi-tenant | Không có org; `group` lồng nhau | Cột `tenantId` + plugin tiêm filter | **Schema-per-tenant + shard** | Cột `org_id` + composite FK |
| Transcript | **Dual write**: JSON `chat.chat` *và* rows `chat_message` | Collection `messages` riêng | Rows `chat_message` | Rows, một nguồn canonical |
| Nhánh | `parent_id` + `chat.current_message_id` | `parentMessageId` | `parent_message_id` + `latest_child_message_id` + `preferred_response_id` | parent (lineage) + `branch_item.ordinal` (paging) |
| Đọc lịch sử | Load cả blob | Load cả hội thoại rồi dựng cây trong RAM | Load cả session (`ix_chat_message_chat_session_id`) | **Keyset theo ordinal** — khác cả ba |
| Phân quyền | `access_grant` generic `(resource_type, resource_id, principal_type, principal_id, permission)` | `aclentries` + `permBits` bitmask, **không unique**, quyền = hợp | Nhiều bảng nối typed, FK thật | Typed resource + `principal` registry |
| Quyền quản trị vs đọc | Một `permission` | `permBits` | **Hai bảng tách bạch**: `user_group__ccpair` (quản lý) vs `user_group__cc_pair_data_access` (đọc) | Tách, theo Onyx |
| Chia sẻ | `shared_chat` snapshot bất biến | `sharedlinks` + `fileSnapshots` metadata | `chat_session.shared_status` | Snapshot có version + audience grants |
| Trạng thái cá nhân | `pinned_note` (per-user) nhưng `chat.pinned` (cột) | `conversation.pinned` (cột) | `user__pinned_persona` (per-user) | `conversation_view` per-user |
| Approval/tool | — | `toolapprovalgrants` fencing 5 trục | **`action_approval` + `action_receipt`** | Theo Onyx + fencing LibreChat |
| Audit | — | `auditlogs` hash chain append-only | Rải rác | Append-only, label không FK |
| Timestamp | epoch `BigInteger`, **đơn vị không thống nhất** | `Date` | `timestamptz` | `timestamptz` |
| FK | Có, nhiều CASCADE | **Không có FK nào** | Có, CASCADE/SET NULL có chủ ý | Có, tách CASCADE/SET NULL |
| Migration | Alembic | **Không có cây migration** | 490 file Alembic, hai cây | Alembic một cây |

### 2.2. Mười bài học lấy nguyên

1. **Normalize access control sớm.** Open WebUI đã phải refactor từ cột JSON `access_control` nhúng trong từng bảng resource sang bảng `access_grant`. Không lặp lại bước trung gian đó.
2. **Index ngược cho membership là bắt buộc.** Unique `(group_id, user_id)` của Open WebUI **không trả lời được** "user này thuộc group nào"; họ phải thêm `(user_id, group_id)` ở migration `1ce6ade7d93b`. Thiếu nó, *mọi* kiểm tra quyền quét toàn bảng membership của cả instance. Áp dụng cho `org_membership` và `team_membership`.
3. **Trạng thái cá nhân ra bảng riêng ngay.** Open WebUI bỏ `note.is_pinned` thay bằng `pinned_note` khi note trở nên chia sẻ được. Chat của dự án này chia sẻ được trong org **từ đầu**, nên pin/archive/last-read phải per-user từ đầu.
4. **Snapshot chia sẻ là bảng riêng, bất biến.** Open WebUI từng lưu chat chia sẻ thành "dòng ma" trong chính bảng `chat` với `user_id = shared-{chat_id}` rồi phải tách ra `shared_chat`.
5. **Unique phải chứa khóa tenant từ ngày đầu.** LibreChat phải drop unique cũ ở **13 collection** khi bật multi-tenancy vì unique toàn cục chặn ghi cùng giá trị ở tenant khác. Đây là migration đắt nhất có thể tránh miễn phí.
6. **Cột dùng để filter phải nằm trong index, không chỉ cột sort.** Comment của LibreChat trên index facet `endpoint`: thiếu nó thì engine phải đọc **mọi** dòng theo thứ tự danh sách chỉ để loại bỏ. Đúng y như vậy với PostgreSQL.
7. **Index compound chỉ cho thứ tự sort khi các khóa đứng trước bị ghim bằng equality.** LibreChat phải có index `{user, updatedAt, _id}` *riêng* bên cạnh hai index đã có `updatedAt` vì hai index kia ghim `chatProjectId` và `pinned`.
8. **Partial unique index thay lock ứng dụng.** Onyx nói thẳng trong code: "Database-based coordination fields (replacing Redis fencing)". LibreChat có 6 partial unique trên `agentqueuedturns`, mỗi cái một bất biến. Dự án đã dùng kỹ thuật này cho `run_one_open_per_conversation`; dùng tiếp.
9. **SET NULL để audit sống lâu hơn thực thể.** Onyx dùng SET NULL ở `chat_feedback`, `action_approval.gated_app_id`, `action_receipt.*`, `scheduled_task_run.session_id`. Ngược với thói quen CASCADE mọi thứ.
10. **Receipt ghi PENDING trước khi gọi ra ngoài, chỉ CONFIRMED mới là bằng chứng.** Onyx `action_receipt`: PENDING → CONFIRMED/FAILED → quét thành UNKNOWN khi mồ côi. `effect` được chụp lúc ghi để dòng **tự chứa** kể cả khi catalog phân loại lại sau. Cộng `operation_key` partial unique để một luồng nhiều request của provider gộp thành một receipt. Đây là lời giải trực tiếp cho T05 và luồng C ở mục 11 của use-case doc.

### 2.3. Ba điểm cố ý làm khác cả ba dự án

**a. Phân trang theo vị trí trên nhánh, không theo thời gian tuyến tính.**

*Đính chính 27/10/2026:* bản đầu của mục này viết "cả ba đều load toàn bộ hội thoại". Điều đó **sai với LibreChat** — đọc lại source cho thấy route `GET /api/messages` của họ dùng `getMessagesByCursor`, keyset trên `createdAt`, `pageSize` mặc định 25 ([librechat.md §12.1](../database_research/librechat.md)). Open WebUI (blob JSON `history.messages`) và Onyx (một index `ix_chat_message_chat_session_id`) thì đúng là load cả hội thoại.

Khác biệt thật nằm ở **đơn vị phân trang**, không phải ở chỗ có phân trang hay không:

| | Đơn vị cursor | Trả lời được câu hỏi |
|---|---|---|
| LibreChat | `createdAt` của conversation | "30 message gần nhất của hội thoại" |
| Thiết kế này | `(branch_id, ordinal)` | "30 item trước vị trí X **trên nhánh B**" |

Với cây message và nhánh chọn ở client (LibreChat giữ sibling index phía browser), phân trang theo thời gian tuyến tính không định vị được theo nhánh. Đó là lý do `branch_item` là thẩm quyền sắp xếp còn `parent_item_id` chỉ giữ lineage.

Thêm một điều đáng mượn từ cùng chỗ đọc: cursor của LibreChat là **một trường duy nhất**, không có `_id` phá hòa, dù index của họ có `_id` — hai message cùng `createdAt` ở biên trang bị bỏ sót hoặc lặp ([§12.2](../database_research/librechat.md)). Cùng lớp lỗi với defect #2 ở mục 9.6. Quy tắc rút ra: **tiebreak duy nhất phải có ở cả khóa index lẫn predicate cursor.** Khóa `(branch_id, ordinal)` thỏa mãn vì `ordinal` đã duy nhất trong nhánh.

**b. Không cần node gốc rỗng.** Onyx để message đầu chuỗi **không có nội dung** — node gốc rỗng, workaround để sửa được message đầu tiên. Với `branch_item`, fork tại ordinal 0 là hợp lệ, không cần node giả.

**c. Share không tự sống qua thu hồi quyền nguồn.** `sharedLink.fileSnapshots` của LibreChat chụp metadata file để link chia sẻ **tiếp tục chạy mà không hỏi ACL sống của chủ sở hữu**. Dự án này đã chốt chính sách ngược lại ([use cases](./chat-use-cases-and-organization-access.md) mục 8): mất quyền nguồn thì không phục vụ lại phần dẫn xuất. Lấy **cơ chế** (snapshot bất biến, không copy byte) nhưng **giữ chính sách** (kiểm tra audience và dependency cả lúc publish lẫn lúc serve).

---

## 3. Bảy quyết định thiết kế

| # | Cần chốt | Khuyến nghị | Nếu chọn khác |
|---|---|---|---|
| 1 | Mô hình tenant | **Cột `org_id` + composite FK**, một cluster, một schema `app` | Schema-per-tenant kiểu Onyx bắt buộc thêm catalog `public` (`user_tenant_mapping`, `tenant_shard`) chỉ để trả lời "user này ở những org nào" — chi phí lớn cho yêu cầu một người nhiều org |
| 2 | Danh tính người dùng | **`(issuer, subject)` là khóa bền vững**; email chỉ là thuộc tính, unique theo `lower(email)` bằng partial index | Lấy email làm danh tính dẫn tới `prior_emails` + event ORM thu hồi alias như Onyx — logic bảo mật nằm ngoài database |
| 3 | Actor của run | **`membership_id`, không phải `user_id`** | Dùng `user_id` thì rời org hoặc xóa tài khoản làm lịch sử actor đổi nghĩa |
| 4 | Hình dạng grant | **Resource typed (FK thật) + `principal` registry (một FK cho mọi loại principal)** | `(resource_type, resource_id)` dạng text như Open WebUI mất toàn vẹn tham chiếu; bitmask `permBits` như LibreChat chỉ đáng khi có policy engine tổng quát |
| 5 | Hợp quyền | **Một dòng cho mỗi `(resource, principal, role_key)`, quyền hiệu lực = hợp các dòng** | LibreChat không có unique nào trên `aclentries` → thu hồi phải biết xóa dòng nào trong N dòng trùng |
| 6 | Đọc nhánh | **Copy *reference* prefix vào `branch_item` lúc fork**, chạy nền khi prefix dài (đo được ~37 µs/dòng: 1,9 s ở 50.000 item — xem mục 9.5) | Phương án thay thế: `branch` giữ chuỗi segment `(ancestor_branch_id, from_ordinal, to_ordinal)`, đọc vẫn là range scan trên PK cho page nằm trong một segment. Đổi sang khi dung lượng `branch_item` thành chi phí chính |
| 7 | Quyền admin org | **Không grant nội dung mặc định**; tách quyền cấp grant khỏi quyền quản trị membership | Muốn admin đọc được phải có workflow truy cập đặc biệt bật rõ + audit, không ẩn trong role |

Quyết định 6 là cái duy nhất cần số đo mới chốt dứt điểm; sáu cái còn lại là hệ quả của use case đã viết.

---

## 4. DDL đề xuất

Quy ước: schema `app`, `timestamptz`, `text` + CHECK cho status, `jsonb` cho content block/metadata không query, UUID do ứng dụng cấp (ưu tiên **UUIDv7** cho bảng ghi nhiều để B-tree có locality — sinh ở app, không phụ thuộc `uuidv7()` của PG18).

Mọi bảng tenant-bound có `UNIQUE (org_id, id)` *dư* bên cạnh PK. Đây là **chi phí có chủ ý**: nó là thứ cho phép composite FK chặn liên kết chéo org ở tầng database, không chỉ ở tầng ứng dụng.

### 4.1. Identity và tổ chức

```sql
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
```

### 4.2. Principal registry — một FK cho mọi loại principal

Đây là kỹ thuật `gated_app` của Onyx (một bảng đa hình, `CHECK num_nonnulls(...) = 1`, `kind` suy ra) nhưng áp cho **phía principal** thay vì phía resource. Kết quả: mọi bảng grant có đúng **một** FK principal với toàn vẹn tham chiếu thật, thay vì ba cột nullable lặp lại ở mỗi bảng grant, và thay vì `(principal_type, principal_id)` dạng text không FK như Open WebUI.

```sql
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
```

FK với cột NULL dùng `MATCH SIMPLE` (mặc định) nên thỏa mãn tự động — ba FK cùng tồn tại không xung đột với `CHECK` một-trong-ba.

### 4.3. Conversation, branch, transcript

```sql
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
    CONSTRAINT branch_fork_pair_chk
        CHECK ((parent_branch_id IS NULL) = (fork_item_id IS NULL)),
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
    CONSTRAINT transcript_item_org_uq          UNIQUE (org_id, id),
    CONSTRAINT transcript_item_conversation_uq UNIQUE (conversation_id, id),
    FOREIGN KEY (org_id, conversation_id)           REFERENCES app.conversation (org_id, id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id, parent_item_id)   REFERENCES app.transcript_item (conversation_id, id),
    FOREIGN KEY (conversation_id, origin_branch_id) REFERENCES app.branch (conversation_id, id)
);
```

`UNIQUE (conversation_id, id)` trên `transcript_item` là thứ làm self-FK `(conversation_id, parent_item_id)` khả thi — database tự bảo đảm parent nằm **cùng conversation**, đúng yêu cầu "composite same-conversation parent FK" của review. Chống cycle vẫn thuộc tầng service.

```sql
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
```

PK `(branch_id, ordinal)` phục vụ cả hai chiều scan; không cần index phụ cho paging. `ordinal` có lỗ sau purge là chấp nhận được vì keyset dùng `ordinal <`.

```sql
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
```

### 4.4. Grant

```sql
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
```

Quyền hiệu lực = **hợp** các dòng khớp principal của actor (chính membership + mọi team chứa nó + service principal nếu có). Khác LibreChat ở chỗ unique `(resource, principal, role_key)` làm thu hồi là một DELETE xác định, không phải "xóa dòng nào trong N dòng trùng".

`source_grant`, `tool_action_grant`, `shared_result_grant` dùng đúng hình dạng này, mỗi cái FK typed tới resource của nó. **Không** gộp thành một bảng `grant(resource_type, resource_id, ...)`.

### 4.5. Chia sẻ

```sql
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
    status                  text        NOT NULL DEFAULT 'draft'
                            CHECK (status IN ('draft', 'published', 'revoked', 'expired')),
    published_at            timestamptz,
    published_by_membership_id uuid,
    CONSTRAINT shared_result_version_uq  UNIQUE (shared_result_id, version_no),
    CONSTRAINT shared_result_version_org UNIQUE (org_id, id),
    FOREIGN KEY (org_id, shared_result_id) REFERENCES app.shared_result (org_id, id) ON DELETE CASCADE
);
```

`shared_result_grant` cấp theo **version cụ thể**, không theo `shared_result`: version mới phải revalidate audience. `share_source_dependency (version_id, source_version_id)` là bảng typed để chặn publish khi audience thiếu quyền nguồn — cơ chế LibreChat, chính sách của dự án.

### 4.6. File

```sql
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
```

`object_id` **không** CASCADE: object có thể còn reference từ share version hoặc artifact. Xóa object là job có pin check.

### 4.7. Memory provenance và audit

```sql
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
    FOREIGN KEY (org_id, actor_membership_id) REFERENCES app.org_membership (org_id, id) ON DELETE SET NULL
);
CREATE INDEX audit_event_by_resource ON app.audit_event (org_id, resource_type, resource_label, occurred_at DESC);
CREATE INDEX audit_event_by_actor    ON app.audit_event (org_id, actor_membership_id, occurred_at DESC);
```

`details` **không bao giờ** chứa prompt thô, token hay tool output đầy đủ — comment của LibreChat `auditLog.metadata`. Nếu sau này cần tamper-evidence, thêm `chain_key`/`seq`/`prev_hash`/`hash` với unique `(chain_key, seq)` theo đúng mẫu của họ; chưa cần ngay.

---

## 5. Access path và index

| Truy vấn | Index | Ghi chú |
|---|---|---|
| Sidebar chat của tôi | `conversation (org_id, created_by_membership_id, activity_at DESC, id DESC) WHERE deleted_at IS NULL` | Keyset `(activity_at, id)`; không OFFSET |
| Sidebar được chia sẻ | `conversation_grant (principal_id, conversation_id)` → conversation PK | Tab riêng; **không** fanout activity tới cả team mỗi token |
| Lọc theo agent/trạng thái | Thêm cột lọc **vào trong khóa**, ví dụ `(org_id, created_by_membership_id, agent_key, activity_at DESC, id DESC)` | Bài học facet `endpoint` của LibreChat: thiếu cột lọc trong khóa thì phải đọc cả danh sách chỉ để loại bỏ |
| Pin/archive cá nhân | `conversation_view (membership_id, pinned_at DESC, conversation_id) WHERE pinned_at IS NOT NULL` | Index riêng vì `pinned_at` không thể dùng chung tiền tố với `activity_at` |
| Sort mặc định | Index **riêng** không ghim cột nào khác | Index compound chỉ cho thứ tự sort khi khóa đứng trước bị ghim bằng equality |
| Phân trang nhánh | PK `branch_item (branch_id, ordinal)` | Xem query bên dưới |
| Sibling / regenerate options | `transcript_item (conversation_id, parent_item_id, id)` | Không tải cả cây để hiện một nhóm sibling |
| "User này ở org nào" | `org_membership (user_id, org_id) WHERE status='active'` | Bắt buộc; xem mục 2.2 điểm 2 |
| "Team của membership này" | `team_membership (membership_id, team_id)` | Cùng lý do |
| Dọn object mồ côi | `stored_object (deletion_retry_at, id) WHERE status IN ('deleting','failed')` | Deadline, không phải cờ |

```sql
-- Phân trang nhánh, sau khi service đã authorize và resolve branch.
SELECT bi.ordinal, i.id, i.role, i.kind, i.content, i.status, i.content_revision
FROM   app.branch_item     AS bi
JOIN   app.transcript_item AS i
       ON  i.conversation_id = bi.conversation_id
       AND i.id              = bi.item_id
WHERE  bi.branch_id = $1
  AND  bi.ordinal   < $2
ORDER  BY bi.ordinal DESC
LIMIT  $3;
```

Cursor là `(branch_id, ordinal)`, kiểm tra scope mỗi request. Client đảo thứ tự page để render tăng dần. Append vào nhánh không làm ordinal cũ đổi, nên page đã tải không trượt — khác hẳn phân trang theo `updated_at` của sidebar.

**Chưa thêm**: GIN trên `transcript_item.content`, full-text tiếng Việt, partition. Full-text cần đánh giá tokenizer/dấu thật; `simple`/`trigram` không đồng nghĩa có chất lượng tìm kiếm. Partition cần đo trước, và nếu partition theo thời gian thì unique phải chứa partition key.

---

## 6. Chính sách xóa: CASCADE cho nội dung, SET NULL cho bằng chứng

Onyx dùng SET NULL ở `chat_feedback`, `action_approval.gated_app_id`, `action_receipt.*`, `scheduled_task_run.session_id` để bằng chứng sống lâu hơn thực thể. Lấy nguyên tắc đó thành quy tắc rõ:

| Quan hệ | Chính sách | Lý do |
|---|---|---|
| `conversation` → `branch`, `transcript_item`, `branch_item`, `conversation_view`, `conversation_grant` | CASCADE | Nội dung thuộc conversation |
| `transcript_item` → `conversation_object.item_id` | SET NULL | Object còn reference khác |
| `conversation` → `audit_event` | **Không FK** (nhãn) | Audit phải sống qua purge |
| `membership` → `audit_event.actor_membership_id` | SET NULL | `actor_label` giữ nghĩa |
| `membership` → `conversation.created_by` | NO ACTION | Membership không bao giờ hard-delete |
| `stored_object` ← `conversation_object` | NO ACTION | Xóa object là job có pin check |
| App → native `lg_state`/`lg_memory` | **Không FK** | Không FK vào bảng nội bộ thư viện |

Xóa conversation là tombstone (`deleted_at`) chặn đọc/run mới, rồi job purge nhiều bước có trạng thái: hủy run đang chạy → chờ nhả ownership → xóa native thread qua API của saver → dọn journal/Redis/object → audit. **Không giả định CASCADE SQL dọn được native hoặc object storage.**

---

## 7. Không sao chép

| Từ | Thứ không lấy | Lý do |
|---|---|---|
| Open WebUI | Dual write JSON `chat.chat` + rows `chat_message` | Họ vẫn đang trả giá: chat search đọc tập store **khác nhau** giữa PostgreSQL và SQLite |
| Open WebUI | `access_grant` với `resource_type`/`resource_id` dạng text | Không có FK thật; review của dự án đã loại bỏ hình dạng này |
| Open WebUI | Epoch `BigInteger` | Đơn vị không thống nhất giữa các bảng (channel/calendar ghi rõ nanosecond, chat không ghi rõ). Dùng `timestamptz` |
| Open WebUI | Các cột có trong schema nhưng không code path nào ghi | `presence_state`, `channel.archived_*`, `channel_member.role='manager'`, `api_key.expires_at`… Đừng copy cột chết |
| LibreChat | Không có FK | Họ phải tạo hẳn các collection dọn dẹp (`skillDeletion`, `triggerUserPurge`, `code_environment_tombstones`) để làm việc mà FK làm giúp |
| LibreChat | Không có cây migration; index build lúc startup | Build index nền **thất bại im lặng** nếu thiếu listener; trên DocumentDB <5.0 partial unique bị từ chối và bất biến mất hiệu lực mà không lỗi gì |
| LibreChat | Membership là mảng nhúng (`group.memberIds`) | Trần 16 MB mỗi document |
| LibreChat | Hai field gần tên nhau cùng bảng (`expiresAt` vs `expiredAt`) | Chính tài liệu nguồn gọi đây là chỗ dễ đọc nhầm nhất |
| Onyx | Schema-per-tenant + `tenant_shard` | Phải thêm catalog `public` riêng chỉ để trả lời "user ở org nào" — ngược với yêu cầu một người nhiều org |
| Onyx | Enum lưu lúc NAME lúc VALUE | Tài liệu của chính họ nói "viết SQL thủ công phải kiểm tra từng cột". Dùng `text` + CHECK thống nhất |
| Onyx | Logic bảo mật trong event ORM (`prior_emails`) | Ghi thẳng SQL bỏ qua nó. Bất biến phân quyền phải ở database hoặc ở một service duy nhất |
| Onyx | `latest_child_message_id` denormalize | Cần bảo trì tay; `branch.head_item_id` đã đủ và có `branch_item` kiểm chứng |
| Cả ba | Load toàn bộ hội thoại để dựng cây | Không đạt mục tiêu 100.000 item |

---

## 8. Thứ tự triển khai

1. **Migration 1 — identity/org**: `app_user`, `organization`, `org_membership`, `team`, `team_membership`, `service_principal`, `principal`. Test: deny theo org, membership revoke, index ngược có được dùng (`EXPLAIN`).
2. **Migration 2 — chat core**: `conversation`, `branch`, `transcript_item`, `branch_item`, `conversation_view`. Test: parent FK chặn cross-conversation, fork tại ordinal 0, paging keyset.
3. **Migration 3 — grant + share + file**: `conversation_grant`, `shared_result*`, `stored_object`, `conversation_object`.
4. **Migration 4 — execution**: `run`, `run_invocation`, `run_attempt`, `stream_head/event/snapshot`, `checkpoint_pin` theo [review](./database-schema-review.md) mục 5.3. **Chỉ sau khi** đã kiểm chứng ranh giới `LangGraphAgent`/saver.
5. **Migration 5 — tool/approval/source**: theo review mục 5.4–5.5, lấy mô hình `action_approval`/`action_receipt` của Onyx.
6. `memory_provenance` và `audit_event` đi kèm từ migration 1 (audit) và migration 4 (memory).

Mỗi bước expand → backfill batch có giới hạn → verify → switch reads → contract.

### Điều kiện nghiệm thu cho vùng này

- `EXPLAIN (ANALYZE, BUFFERS)` trên sidebar, paging nhánh, sibling lookup, grant lookup với fixture: org 10/1.000 thành viên, conversation 100/10.000/100.000 item, fork sâu 10 cấp, content 1 KB/100 KB/1 MB. *(Đã làm một phần ở mục 9.3–9.4: paging nhánh và sidebar trên 100.000 item + 5.000 conversation.)*
- Race: hai tab cùng fork, rename thắng title job, revoke membership giữa lúc đọc history, grant và revoke đồng thời.
- Deny: user org khác không list/đọc được bằng ID; shared viewer không gọi được API history của nhánh khác; admin không có grant không đọc được chat riêng.
- Fork: prefix copy đúng, ordinal không trùng, branch `preparing` không chạy được, native fork hỏng thì branch không ready. *(Chi phí prefix copy đã đo ở mục 9.5; tính đúng đắn đồng thời thì chưa.)*
- Purge: tombstone chặn đọc, job purge idempotent, audit còn nguyên sau khi conversation biến mất.

---

## 9. Kết quả kiểm chứng đã chạy

Môi trường: `postgres:16-alpine` (PostgreSQL 16.15) trong container, cấu hình mặc định, một connection, `synchronous_commit` mặc định, disk local. **Đây là sanity check về tính đúng đắn và access path, không phải benchmark capacity.**

### 9.1. DDL chạy sạch

Toàn bộ DDL ở mục 4 chạy hết trên PostgreSQL 16 với `ON_ERROR_STOP=1`: 19 bảng, không lỗi cú pháp, không lỗi thứ tự phụ thuộc. FK trễ `conversation_default_branch_fk` (vòng conversation ↔ branch) tạo được bằng `ALTER TABLE ... DEFERRABLE INITIALLY DEFERRED`.

### 9.2. Chín bất biến, kiểm bằng INSERT thật

| # | Thử | Kết quả |
|---|---|---|
| T1 | Tạo user thứ hai với `lan@EXAMPLE.com` khi đã có `Lan@Example.com` | Bị chặn — `Key (lower(email))=(lan@example.com) already exists` ✅ |
| T2 | `conversation` của org A trỏ `created_by_membership_id` của org B | Bị chặn — composite FK `(org_id, created_by_membership_id)` ✅ |
| T3 | Conversation + branch + 2 item + 2 branch_item hợp lệ | Chấp nhận ✅ |
| T4 | `parent_item_id` trỏ sang item của **conversation khác** | Bị chặn — composite FK `(conversation_id, parent_item_id)` ✅ |
| T5 | Hai item cùng `ordinal` trên một branch | Bị chặn — PK `(branch_id, ordinal)` ✅ |
| T6 | `principal` có cả `membership_id` và `team_id` | Bị chặn — `CHECK num_nonnulls(...) = 1` ✅ |
| T7 | `principal` hợp lệ; `kind` suy ra | `kind = 'member'` tự sinh ✅. `principal` của org B trỏ team của org A bị chặn ✅ |
| T8 | `branch` có `parent_branch_id` nhưng thiếu `fork_item_id` | Bị chặn — `branch_fork_pair_chk` ✅ |
| T9 | `conversation_grant` của org B trỏ conversation của org A | Bị chặn — composite FK ✅ |

Điểm đáng ghi: **T2/T4/T7/T9 bị chặn ở tầng database, không cần tầng ứng dụng**. Đây là thứ mà `(resource_type, resource_id)` dạng text của Open WebUI và việc không có FK của LibreChat đều không làm được.

### 9.3. Access path, 100.000 item + 5.000 conversation

```
### Paging nhánh (branch_item 100.002 dòng, page 30 ở ordinal 50.000)
Limit  (actual time=0.041..0.098 rows=30)
  Buffers: shared hit=127 read=1
  ->  Nested Loop
        ->  Index Scan Backward using branch_item_pkey  (rows=30)  Buffers: shared hit=8
              Index Cond: (branch_id = ... AND ordinal < 50000)
        ->  Index Scan using transcript_item_pkey  (loops=30)       Buffers: shared hit=119
Execution Time: 0.119 ms
```

Không có Sort, không có Seq Scan. 8 buffer cho phần sắp xếp, 119 buffer cho 30 lần tra PK lấy content — **N+1 bị chặn trong một page**, đúng như thiết kế. Kết quả độc lập với vị trí page: index scan ngược trên PK.

```
### Sidebar keyset (5.000 conversation)
Limit  ->  Index Scan using conversation_sidebar   Buffers: shared hit=4
Execution Time: 0.057 ms
```

### 9.4. Bài học facet của LibreChat chuyển sang PostgreSQL nguyên vẹn

Cùng một truy vấn sidebar có thêm điều kiện `agent_key = 'rare'` (52/5.000 dòng khớp):

| | Buffers | Plan | Thời gian |
|---|---|---|---|
| **A.** `agent_key` **không** trong khóa index | 108 | Seq Scan + **Sort**, `Rows Removed by Filter: 4950` | 0.657 ms |
| **B.** `agent_key` **trong** khóa index | 5 | Index Scan, không Sort | 0.057 ms |

Một filter khớp **1% dòng** mà vẫn đọc toàn bộ danh sách — chính xác điều comment của LibreChat mô tả. Chênh lệch ~11× ở 5.000 dòng và **tăng tuyến tính theo độ dài danh sách**. Hệ quả cho thiết kế: mỗi facet sidebar được phép bật phải có index riêng chứa cột facet, hoặc không bật facet đó.

### 9.5. Chi phí fork — câu trả lời cho quyết định 6

Copy reference prefix vào `branch_item`, một INSERT…SELECT:

| Fork tại ordinal | Số dòng copy | Thời gian |
|---|---|---|
| 50.000 | 50.000 | **1.854 ms** |
| 100.002 | 100.002 | **3.907 ms** |

Tuyến tính, khoảng **37–39 µs/dòng**. Dung lượng: `branch_item` 250.004 dòng chiếm **46 MB** kể cả index, tức **~192 byte/dòng** — trong khi `transcript_item` với 100.002 dòng content ~800 ký tự chiếm 114 MB.

**Kết luận cho quyết định 6:**

- Dưới ~5.000 item, fork đồng bộ trong request HTTP là chấp nhận được (< 200 ms).
- Từ ~10.000 item trở lên, fork **phải** chạy trong job nền. Thiết kế đã sẵn sàng cho điều này: `branch.status = 'preparing'` → `'ready'`, và branch không được chạy khi chưa ready. Không cần đổi schema, chỉ cần API fork trả `202` và UI hiện trạng thái chuẩn bị.
- Ngưỡng chuyển sang chuỗi segment: khi `độ dài conversation p95 × số fork trung bình` làm dung lượng `branch_item` trở thành chi phí chính, hoặc khi cần fork có độ trễ < 100 ms ở conversation dài. Đọc theo segment **không đắt hơn** cho page nằm gọn trong một segment — vẫn là một range scan trên PK — nên đó là đường nâng cấp không phá access path.

Các số trên đo trên cấu hình mặc định, không đồng thời, không WAL tuning. Dùng làm **bậc độ lớn để chọn đồng bộ hay nền**, không phải SLA.

### 9.6. Tự rà soát: năm lỗi đã tìm ra và sửa

Rà lại chính file DDL sau khi giao, đối chiếu với tiêu chuẩn của mục 7:

| # | Lỗi | Sửa | Kiểm chứng |
|---|---|---|---|
| 1 | 7 cột `updated_at`, **0 trigger** — `DEFAULT now()` chỉ chạy lúc INSERT, nên cột không bao giờ đổi. Đúng loại "cột có trong schema nhưng không code path nào ghi" mà mục 7 dùng để loại bỏ cột của Open WebUI | `app.touch_updated_at()` + trigger `BEFORE UPDATE` sinh tự động cho mọi bảng có cột này | `UPDATE` rồi `updated_at > created_at` ✅ |
| 2 | `audit_event_by_resource` và `..._by_actor` sort `occurred_at DESC` **không có `id DESC`** — keyset trên khóa không duy nhất bỏ sót hoặc lặp dòng. Mọi index sidebar đều có tiebreak, hai index audit thì quên | Thêm `id DESC` vào cả hai | `indexdef ~ 'id DESC'` ✅ |
| 3 | **0 ràng buộc kích thước**. `content` jsonb không giới hạn → một tool trả 2 MB thành một dòng 2 MB và dòng đó vào mọi snapshot. Review §4 của dự án yêu cầu "CHECK… payload size" | CHECK `pg_column_size` trên `transcript_item.content` (1 MiB), `shared_result_version.payload` (8 MiB), `audit_event.details` (64 KiB), `length(title) <= 512` | INSERT 2 MB bị chặn ✅ |
| 4 | `branch_fork_pair_chk` chỉ kiểm `parent_branch_id` ↔ `fork_item_id`, bỏ sót `fork_ordinal` → branch fork có thể không biết copy prefix tới đâu | `branch_fork_triple_chk`: `num_nonnulls(parent_branch_id, fork_item_id, fork_ordinal) IN (0, 3)` | Fork thiếu `fork_ordinal` bị chặn ✅ |
| 5 | Không gì bảo đảm membership active có dòng `app.principal`. Thiếu nó thì không cấp grant được mà database im lặng | Trigger `AFTER INSERT` trên `org_membership`/`team`/`service_principal` tạo principal tương ứng | Insert membership → principal `kind='member'` tự có ✅ |

Lỗi 1 và 3 là tiêu chuẩn tôi tự đặt ra ở mục 7 rồi tự vi phạm. Lỗi 2 cho kết quả sai, không chỉ chậm.

Sau khi sửa: **19 bảng, 10 trigger, 26 CHECK**, chạy sạch trên PostgreSQL 16.15.

### 9.7. Còn thiếu so với phạm vi (chưa làm)

Những thứ cả ba dự án tham chiếu đều có, nằm trong phạm vi chat/history, và schema này **chưa** có:

| Thiếu | Use case liên quan | Các dự án làm gì |
|---|---|---|
| **Tìm kiếm lịch sử chat** | C09 (bắt buộc) | LibreChat mirror MeiliSearch + search-token plugin; Open WebUI chat search; Onyx vector stack |
| **Feedback trên item** | Chưa có ID riêng | Onyx `chat_feedback` + `document_retrieval_feedback`, cả hai SET NULL để sống lâu hơn message; Open WebUI `feedback` có snapshot |
| **Lớp nhóm trên conversation** (folder/tag/project) | C09 | Open WebUI `folder` + `tag`; LibreChat `chatprojects` (có `instructions`, `file_ids`, `contextRevision`) + `conversationtags`; Onyx `user_project` |
| **Pipeline xử lý file** | D01 ("đang xử lý → sẵn sàng hoặc lỗi có retry") | Onyx `user_file` 7 trạng thái + `needs_project_sync` + 4 index (3 partial); Open WebUI `file.data.status` + partial index |
| **Usage/token accounting** | Chưa có use case nhưng sản phẩm agent cần | Onyx `user_usage` (partial unique theo `actor_kind`) + `token_rate_limit`; LibreChat `balances`/`transactions` |

`item_feedback` và `run_usage` có trong bảng catalogue của [review](./database-schema-review.md) §5.2 và §5.3 nhưng **không được đưa vào DDL này** — đó là thiếu sót về phạm vi, không phải quyết định.

---

## 10. Giới hạn

- Đã chạy: DDL, 9 bất biến, `EXPLAIN (ANALYZE, BUFFERS)` trên 4 truy vấn, đo chi phí fork. **Chưa chạy**: test đồng thời, race condition, fault injection, Redis/native integration, restore drill, đo dưới tải nhiều connection.
- Fixture mới chỉ một hình dạng: một org, một conversation dài, 5.000 conversation ngắn. Chưa có org 1.000 thành viên, chưa có fork sâu nhiều cấp, chưa có nhiều grant/dependency, chưa đo cold cache.
- Phần execution/stream/tool/source chỉ được tham chiếu. Chúng vẫn chờ kiểm chứng ranh giới `LangGraphAgent` (durability, fork checkpoint, ownership connection) trước khi viết DDL.
- Các quyết định ở mục 3 là khuyến nghị kèm lý do, chưa phải đã được chốt cùng sản phẩm. Quyết định 1–5 và 7 là hệ quả của use case đã viết; quyết định 6 giờ đã có số đo nhưng ngưỡng cuối phụ thuộc hình dạng dữ liệu thật.
- Ba tài liệu nguồn đều tự khai giới hạn: Open WebUI là community contribution tới v0.12.0, không đọc source; LibreChat liệt kê index **khai báo trong source**, không phải index đang tồn tại trên database thật; Onyx dựng từ `models.py` và có ít nhất hai chỗ model lệch schema thật. Các bài học ở mục 2 là mẫu thiết kế, không phải xác nhận hành vi runtime của sản phẩm đó.
- Tài liệu này không thiết kế RBAC engine, không viết authorization service, không có kiểm thử bảo mật.
