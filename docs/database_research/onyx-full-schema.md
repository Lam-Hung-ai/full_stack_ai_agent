# Onyx — toàn bộ database schema

Ngày ghi: 2026-10-27. Nguồn: `/home/lamhung/code/onyx`, commit `03d0a7fcde658e6c27ce613b4b3cc7cf3da14b0b` (2026-10-22).

File gốc: [`backend/onyx/db/models.py`](/home/lamhung/code/onyx/backend/onyx/db/models.py) (7796 dòng), [`backend/onyx/db/enums.py`](/home/lamhung/code/onyx/backend/onyx/db/enums.py), và cây migration [`backend/alembic/versions/`](/home/lamhung/code/onyx/backend/alembic/versions/) (490 file) + [`backend/alembic_tenants/versions/`](/home/lamhung/code/onyx/backend/alembic_tenants/versions/) (12 file).

Onyx **không có trang docs schema công khai** như Open WebUI, nên tài liệu này dựng từ source. Đây là bản liệt kê toàn bộ bảng; phân tích riêng cho bài toán chat/branch/stream nằm ở [onyx.md](./onyx.md).

Phạm vi: mọi bảng do ORM định nghĩa, cộng ba bảng do `fastapi-users` tạo. Chưa chạy migration, chưa dump database thật, chưa benchmark.

---

## 1. Kiến trúc lưu trữ

### 1.1. Hai `DeclarativeBase`, hai cây migration

| Base | Schema | Cây Alembic | Nội dung |
|---|---|---|---|
| `Base` | Schema của **từng tenant** | `alembic/` | 155 bảng nghiệp vụ + 3 bảng `fastapi-users` |
| `PublicBase` | `public` (hoặc `POSTGRES_DEFAULT_SCHEMA` khi single-tenant) | `alembic_tenants/` | 9 bảng catalog dùng chung toàn hệ thống |

`PublicBase` được tách ra có chủ ý: cây migration per-tenant (`target_metadata = Base.metadata`) không bao giờ định tạo chúng bên trong schema tenant, còn cây `alembic_tenants` (`target_metadata = PublicBase.metadata`) mới autogenerate được. Chỉ truy cập qua `get_catalog_session()` — session scoped theo tenant sẽ rơi vào database mà tenant đó đang ở, vốn có thể là shard khác.

Onyx dùng **schema-per-tenant** trên PostgreSQL, và còn có **shard**: `tenant_shard` map tenant sang database vật lý. Tenant không có dòng ở đó thì nằm trên shard mặc định.

### 1.2. Kiểu cột đặc thù

| Kiểu | Hành vi |
|---|---|
| `EncryptedString` / `EncryptedJson` | `TypeDecorator` trên `LargeBinary`. Mã hóa khi ghi, trả về `SensitiveValue` khi đọc (`.get_value(apply_mask=False)` để lấy giá trị thật). Một mapper event tự bọc giá trị thô thành `SensitiveValue` khi gán |
| `NullFilteredString` | `String` nhưng loại bỏ ký tự `\x00` lúc bind, và ghi log cảnh báo |
| `PydanticType` / `PydanticListType` | Serialize model Pydantic vào JSONB |
| `GUID`, `TIMESTAMPAware` | Từ `fastapi_users_db_sqlalchemy.generics` |

### 1.3. `native_enum=False` ở gần như mọi enum

Hầu hết cột enum khai báo `Enum(X, native_enum=False)`, tức **lưu dạng VARCHAR kèm CHECK constraint** chứ không tạo kiểu ENUM của PostgreSQL. Ngoại lệ đáng chú ý: `embedding_provider.provider_type` dùng `Enum(EmbeddingProvider)` (native).

Mặc định SQLAlchemy lưu **tên member** (`PRESENT`), trừ khi có `values_callable=lambda x: [e.value for e in x]` thì lưu **giá trị** (`present`). Khác biệt này quan trọng khi truy vấn SQL thủ công — xem §15.

### 1.4. Timestamp

Khác hẳn Open WebUI: Onyx dùng `DateTime(timezone=True)` với `server_default=func.now()` và `onupdate=func.now()` ở hầu hết bảng, **không** dùng epoch integer. Một vài ngoại lệ dùng `BigInteger` cho số liệu (`*_duration_ms`, token count).

### 1.5. Tổng số bảng

| Nhóm | Số bảng |
|---|---|
| `Base` (per-tenant, có `__tablename__` trong models.py) | 155 |
| `PublicBase` (public schema) | 9 |
| `fastapi-users` (`user`, `oauth_account`, `accesstoken`) | 3 |
| **Tổng ORM** | **167** |
| Thêm: `alembic_version`, `alembic_version_tenants` | 2 |

---

## 2. Danh mục toàn bộ bảng theo nhóm

| § | Nhóm | Bảng |
|---|---|---|
| 3 | Người dùng & xác thực | `user`, `oauth_account`, `accesstoken`, `api_key`, `personal_access_token`, `oauth_provider_grant`, `oauth_provider_token`, `saml`, `sso_provider`, `notification`, `memory` |
| 4 | Connector & credential | `connector`, `credential`, `connector_credential_pair`, `credential_capability_report`, `capability_check_run`, `federated_connector`, `federated_connector_oauth_token`, `federated_connector__document_set` |
| 5 | Indexing & đồng bộ | `search_settings`, `index_attempt`, `index_attempt_errors`, `index_attempt_stage_metric`, `targeted_reindex_job`, `targeted_reindex_job_target`, `port_attempt`, `port_orphan_candidate`, `hierarchy_fetch_attempt`, `cc_pair_run_resolution`, `sync_record`, `embedding_provider` |
| 6 | Document & hierarchy | `document`, `chunk_stats`, `tag`, `document__tag`, `hierarchy_node`, `hierarchy_node_by_connector_credential_pair`, `document_by_connector_credential_pair`, `document_set`, `document_set__connector_credential_pair`, `document_set__user` |
| 7 | Knowledge Graph | `kg_entity_type`, `kg_entity`, `kg_entity_extraction_staging`, `kg_relationship_type`, `kg_relationship_type_extraction_staging`, `kg_relationship`, `kg_relationship_extraction_staging`, `kg_term` |
| 8 | Chat & message | `chat_session`, `chat_message`, `tool_call`, `search_doc`, `search_query`, `chat_message__search_doc`, `tool_call__search_doc`, `chat_feedback`, `document_retrieval_feedback`, `chat_message__standard_answer` |
| 9 | LLM & provider | `llm_provider`, `model_configuration`, `llm_model_flow`, `image_generation_config`, `voice_provider`, `internet_search_provider`, `internet_content_provider`, `tracing_provider_config`, `model_cost_override` |
| 10 | Persona, tool, skill, project | `persona`, `persona_label`, `persona__persona_label`, `persona__document_set`, `persona__tool`, `persona__user`, `persona__user_group`, `persona__user_file`, `persona__hierarchy_node`, `persona__document`, `user__pinned_persona`, `assistant__user_specific_config`, `tool`, `tool_user_preference`, `oauth_config`, `oauth_user_token`, `skill`, `skill__user`, `skill__user_group`, `user_skill_preference`, `inputprompt`, `inputprompt__user`, `user_project`, `user_file`, `project__user_file` |
| 11 | MCP | `mcp_server`, `mcp_connection_config`, `mcp_server_user_preference`, `mcp_server__user`, `mcp_server__user_group` |
| 12 | Bot (Slack / Discord) | `slack_bot`, `slack_channel_config`, `slack_channel_config__standard_answer_category`, `standard_answer`, `standard_answer_category`, `standard_answer__standard_answer_category`, `discord_bot_config`, `discord_guild_config`, `discord_channel_config` |
| 13 | EE: group, quyền, permission sync, SCIM, usage | `user_group`, `user__user_group`, `permission_grant`, `user_group__connector_credential_pair`, `user_group__cc_pair_data_access`, `llm_provider__persona`, `llm_provider__user_group`, `document_set__user_group`, `credential__user_group`, `token_rate_limit`, `token_rate_limit__user_group`, `doc_permission_sync_attempt`, `external_group_permission_sync_attempt`, `user__external_user_group_id`, `public_external_user_group`, `scim_token`, `scim_user_mapping`, `scim_group_mapping`, `license`, `tenant_usage`, `user_usage`, `usage_reports` |
| 14 | Build/Craft & external app | `build_session`, `build_message`, `sandbox`, `artifact`, `snapshot`, `action_receipt`, `action_approval`, `scheduled_task`, `scheduled_task_run`, `scheduled_task_enabled_app`, `scheduled_task_action_policy`, `external_app`, `external_app__skill`, `external_app_user_credential`, `gated_app`, `workspace_action_policy`, `user_action_policy` |
| 15 | Hệ thống & hạ tầng | `key_value_store`, `encrypted_key_value_store`, `cache_store`, `security_settings`, `file_record`, `file_content`, `task_queue_jobs`, `background_error`, `milestone`, `hook`, `hook_execution_log`, `code_interpreter_server` |
| 16 | Public schema (multi-tenant) | `user_tenant_mapping`, `user_tenant_mapping_oauth_account`, `available_tenant`, `tenant_schema_snapshot`, `tenant_anonymous_user_path`, `tenant_sso_domain`, `tenant_invite_counter`, `tenant_shard`, `oauth_provider_client` |

---

## 3. Người dùng và xác thực

### 3.1. `user`

Kế thừa `SQLAlchemyBaseUserTableUUID`. Cột nền do thư viện tạo (migration `6d387b3196c2`): `id` GUID PK, `email` String(320) NOT NULL (index **unique** `ix_user_email`), `hashed_password` String(1024) NOT NULL, `is_active`, `is_superuser`, `is_verified` Boolean NOT NULL.

Cột Onyx thêm vào:

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `role` | Enum `UserRole` (non-native) | nullable | **Cột bia mộ (tombstone)**: code không còn đọc/ghi. Giữ nullable để rollback thuần-code vẫn chạy |
| `account_type` | Enum `AccountType` | NOT NULL, default `STANDARD` | `STANDARD` / `BOT` / `EXT_PERM_USER` / `SERVICE_ACCOUNT` / `ANONYMOUS` |
| `craft_enabled` | Boolean | nullable, default `None` | Override Craft theo từng user; `None` = theo mặc định workspace. AND với cổng Craft cấp deployment |
| `prior_emails` | ARRAY(String) | NOT NULL, default `[]` | Địa chỉ user đã đổi đi. **Chúng vẫn khớp ACL đã index**, nên mỗi địa chỉ còn cấp quyền cho tới khi danh tính khác nhận địa chỉ đó |
| `temperature_override_enabled` | Boolean | nullable | |
| `temperature_default` | Float | nullable | Mặc định chat theo user; thiết lập per-model của admin ưu tiên hơn |
| `reasoning_effort_default` | Enum `ReasoningEffort` (lưu *value*) | nullable | |
| `auto_scroll` | Boolean | nullable | |
| `shortcut_enabled` | Boolean | default `False` | |
| `theme_preference` | Enum `ThemePreference` | nullable | `light`/`dark`/`system` |
| `language` | String | nullable | `None` = theo `Settings.default_language` |
| `chat_background` | String | nullable | |
| `default_app_mode` | Enum `DefaultAppMode` | NOT NULL, default `CHAT` | `AUTO`/`CHAT`/`SEARCH` |
| `personal_name`, `personal_role` | String | nullable | Tab "Personalization" |
| `use_memories` | Boolean | NOT NULL, default `True` | |
| `enable_memory_tool` | Boolean | NOT NULL, default `True` | |
| `user_preferences` | Text | nullable | |
| `chosen_assistants` | JSONB | nullable | |
| `visible_assistants`, `hidden_assistants` | JSONB | NOT NULL, default `[]` | |
| `effective_permissions` | JSONB | NOT NULL, server_default `'[]'::jsonb` | Danh sách permission đã tính sẵn |
| `is_group_manager` | Boolean | NOT NULL, server_default `false` | **Cache** để gate route không cần query; danh sách group quản lý vẫn tra live |
| `oidc_expiry` | TIMESTAMPAware(tz) | nullable | |
| `created_at`, `updated_at` | DateTime(tz) | NOT NULL, `now()` / `onupdate` | |
| `default_model` | Text | nullable | Dạng `displayName__provider__modelName` |
| `paste_as_tile` | Boolean | default `False` | |
| `voice_auto_send`, `voice_auto_playback` | Boolean | default `False` | |
| `voice_playback_speed` | Float | default `1.0` | |

Cần biết:

- `@validates("email")` hạ chữ thường email trước khi lưu.
- **Event `before_insert` / `before_update`**: khi một địa chỉ email được một danh tính nhận, hệ thống chạy `_release_prior_email_claim` để xóa địa chỉ đó khỏi `prior_emails` của **mọi user khác**. Đây là cơ chế thu hồi quyền alias.
- Property `live_oauth_token` chọn link OAuth có `expires_at` lớn nhất trên mọi provider; link không có hạn xếp thấp nhất. Cần load đầy đủ link, vì collection `load_only` sẽ lazy-load từng dòng.
- `password_configured` trả `True` khi user **không** có OAuth account nào (tên property ngược với trực giác).

### 3.2. `oauth_account`

Kế thừa `SQLAlchemyBaseOAuthAccountTableUUID`, có override.

| Cột | Kiểu | Ràng buộc |
|---|---|---|
| `id` | GUID | PK |
| `user_id` | GUID | FK `user.id` ON DELETE cascade, NOT NULL |
| `oauth_name` | String(100) | NOT NULL, index |
| `access_token` | **Text** | NOT NULL — Onyx override vì token Keycloak không vừa 1024 byte mặc định |
| `refresh_token` | **Text** | NOT NULL — cũng được override |
| `expires_at` | Integer | nullable |
| `account_id` | String(320) | NOT NULL, index |
| `account_email` | String(320) | NOT NULL |

Một user có thể giữ nhiều link cho cùng một provider (mỗi subject tái cấp một link).

### 3.3. `accesstoken`

Tên vật lý là `accesstoken` (không có dấu gạch dưới), từ `SQLAlchemyBaseAccessTokenTableUUID`.

| Cột | Kiểu | Ràng buộc |
|---|---|---|
| `token` | String(43) | PRIMARY KEY |
| `user_id` | GUID | FK `user.id` ON DELETE cascade, NOT NULL |
| `created_at` | TIMESTAMPAware(tz) | NOT NULL, index `ix_accesstoken_created_at` |

### 3.4. `api_key`

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `name` | String | nullable | |
| `hashed_api_key` | String | UNIQUE | |
| `api_key_display` | String | UNIQUE | Phần hiển thị trên UI |
| `user_id` | UUID | FK `user.id`, NOT NULL | ID của **"user" đại diện cho credential của API key** |
| `owner_id` | UUID | FK `user.id`, nullable | ID người **sở hữu** key |
| `created_at` | DateTime(tz) | `now()` | |

Hai cột user tách biệt: API key chạy dưới một user ảo riêng (`user_id`), còn `owner_id` là người tạo.

### 3.5. `personal_access_token`

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `name` | String | NOT NULL | Nhãn do user đặt |
| `hashed_token` | String(64) | UNIQUE, NOT NULL | SHA256 = 64 ký tự hex |
| `token_display` | String | NOT NULL | |
| `user_id` | UUID | FK `user.id` CASCADE, NOT NULL | |
| `expires_at` | DateTime(tz) | nullable, **index** | NULL = không hết hạn. Thu hồi = set `NOW()` để hết hạn tức thì |
| `created_at` | DateTime(tz) | `now()` | |
| `last_used_at` | DateTime(tz) | nullable | |
| `is_revoked` | Boolean | NOT NULL, server_default `false` | Phân biệt thu hồi chủ động với hết hạn tự nhiên |
| `pat_type` | Enum `PatType` | NOT NULL, server_default `USER` | `USER` / `CRAFT` |
| `scopes` | JSONB | nullable | Danh sách permission token được dùng. **NULL = không giới hạn** (toàn quyền user); **list rỗng = không cấp gì** (fail-closed) |

Index `ix_pat_user_created` trên (`user_id`, `created_at` DESC).

### 3.6. `oauth_provider_grant` và `oauth_provider_token`

Onyx **đóng vai OAuth provider** (cấp quyền cho client bên ngoài).

`oauth_provider_grant`:

| Cột | Kiểu | Ràng buộc |
|---|---|---|
| `id` | UUID | PK, default `uuid4` |
| `user_id` | UUID | FK `user.id` CASCADE, NOT NULL |
| `client_id` | String(2048) | NOT NULL |
| `client_name` | String(256) | NOT NULL |
| `resource` | String(2048) | NOT NULL |
| `scopes` | JSONB | NOT NULL |
| `created_at` | DateTime(tz) | NOT NULL, `now()` |
| `expires_at` | DateTime(tz) | NOT NULL, **index** |
| `revoked_at` | DateTime(tz) | nullable |

Index `ix_oauth_provider_grant_user_created` (`user_id`, `created_at`).

`oauth_provider_token`:

| Cột | Kiểu | Ràng buộc |
|---|---|---|
| `token_hash` | String(64) | **PRIMARY KEY** |
| `grant_id` | UUID | FK `oauth_provider_grant.id` CASCADE, NOT NULL, index |
| `kind` | String(7) | NOT NULL, CHECK `kind IN ('access','refresh')` (`ck_oauth_provider_token_kind`) |
| `expires_at` | DateTime(tz) | NOT NULL, index |
| `consumed_at` | DateTime(tz) | nullable |

Token lưu **chỉ hash**, không lưu bản rõ.

### 3.7. `saml`

| Cột | Kiểu | Ràng buộc |
|---|---|---|
| `id` | Integer | PK |
| `user_id` | FK `user.id` CASCADE | **UNIQUE** (mỗi user một dòng) |
| `encrypted_cookie` | Text | UNIQUE |
| `expires_at` | DateTime(tz) | |
| `updated_at` | DateTime(tz) | `now()` / `onupdate` |

### 3.8. `sso_provider`

Provider SSO là **dòng dữ liệu, không phải cấu hình lúc khởi động**: route đăng nhập tra dòng lúc request, nên thêm/sửa provider không cần restart.

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `name` | String | UNIQUE, NOT NULL | Path segment của route đăng nhập, đồng thời là `oauth_name` lưu trên link tài khoản. **Đổi tên provider sẽ làm mồ côi các link đó** |
| `display_name` | String | NOT NULL | |
| `provider_type` | Enum `SSOProviderType` | NOT NULL | `GOOGLE_OAUTH` / `OIDC` / `SAML` |
| `config` | **EncryptedJson** | NOT NULL | Client creds + discovery URL (GOOGLE/OIDC) hoặc IdP metadata (SAML). Validate theo `provider_type` lúc ghi |
| `allowed_email_domains` | ARRAY(String) | NOT NULL, default `[]` | Đã hạ chữ thường |
| `enabled` | Boolean | NOT NULL, default `True` | |
| `time_created`, `time_updated` | DateTime(tz) | NOT NULL | |

### 3.9. `notification`

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `notif_type` | Enum `NotificationType` | | 14 giá trị, xem §17 |
| `severity` | Enum `NotificationSeverity` | default `INFO` | `info`/`warning`/`error` |
| `user_id` | UUID | FK `user.id` CASCADE, nullable | NULL = thông báo toàn hệ thống |
| `dismissed` | Boolean | default `False` | |
| `last_shown`, `first_shown` | DateTime(tz) | | |
| `title` | String | | |
| `description` | String | nullable | |
| `additional_data` | JSONB | nullable | |

- Index `ix_notification_user_sort` trên (`user_id`, `dismissed`, `first_shown` DESC).
- UNIQUE `ix_notification_user_type_data` trên (`user_id`, `notif_type`, `additional_data`) để **khử trùng lặp khi insert theo lô** — định nghĩa trong migration `8405ca81cc83`, **không** trong model.

### 3.10. `memory`

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK, autoincrement | |
| `user_id` | UUID | FK `user.id` CASCADE, NOT NULL | |
| `memory_text` | Text | NOT NULL | |
| `conversation_id` | UUID | nullable | **Không phải FK** tới `chat_session` |
| `message_id` | Integer | nullable | **Không phải FK** tới `chat_message` |
| `created_at`, `updated_at` | DateTime(tz) | NOT NULL | |

Provenance (`conversation_id`, `message_id`) là liên kết logic, không có ràng buộc database — xóa chat không dọn memory qua FK.

---

## 4. Connector và credential

### 4.1. `connector`

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `name` | String | | |
| `source` | Enum `DocumentSource` | | Loại nguồn |
| `input_type` | Enum `InputType` | | `load_state`/`poll`/`event`/`slim_retrieval` |
| `connector_specific_config` | JSONB | | |
| `indexing_start` | DateTime (**không timezone**) | nullable | |
| `kg_processing_enabled` | Boolean | NOT NULL, default `False` | Có trích xuất entity knowledge graph không |
| `kg_coverage_days` | Integer | nullable | |
| `refresh_freq` | Integer | nullable | Giây; validator yêu cầu ≥ 60 |
| `prune_freq` | Integer | nullable | Giây; validator yêu cầu ≥ 300 |
| `check_freq` | Integer | nullable | Giây giữa các lần chạy connector check. `None` = chỉ chạy khi được yêu cầu; validator ≥ 300 |
| `time_created`, `time_updated` | DateTime(tz) | | |

Ba `validate_*` là **phương thức Python gọi thủ công**, không phải CHECK constraint của database.

### 4.2. `credential`

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `name` | String | nullable | |
| `source` | Enum `DocumentSource` | | |
| `credential_json` | **EncryptedJson** | | Bí mật, mã hóa at rest |
| `user_id` | UUID | FK `user.id` CASCADE, nullable | |
| `admin_public` | Boolean | default `True` | Mọi Admin truy cập được |
| `curator_public` | Boolean | default `False` | |
| `is_draft` | Boolean | default `False`, server_default `false` | Tài khoản mới trong form connector, chưa lưu cùng connector. Chỉ chủ sở hữu thấy; tạo connector xong thì xóa cờ, và một task định kỳ xóa draft bị bỏ lại |
| `time_created`, `time_updated` | DateTime(tz) | | |

Partial index `ix_credential_draft_time_updated` trên `time_updated` WHERE `is_draft`.

### 4.3. `connector_credential_pair` (cc_pair)

Bảng trung tâm của toàn bộ đường indexing. **PK là composite (`connector_id`, `credential_id`)**, còn `id` là cột `Sequence` riêng có UNIQUE — vì SQLAlchemy có vài điểm trục trặc khi dùng `autoincrement=True` trên cột không phải PK.

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | `Sequence("connector_credential_pair_id_seq")`, UNIQUE, NOT NULL | ID logic mà mọi bảng khác FK tới |
| `connector_id` | Integer | FK `connector.id`, **PK** | |
| `credential_id` | Integer | FK `credential.id`, **PK** | |
| `name` | String | NOT NULL | |
| `status` | Enum `ConnectorCredentialPairStatus` | NOT NULL | `SCHEDULED`/`INITIAL_INDEXING`/`ACTIVE`/`PAUSED`/`DELETING`/`INVALID` |
| `in_repeated_error_state` | Boolean | default `False` | Tách khỏi `status`: pair có thể vừa `ACTIVE` vừa lỗi lặp |
| `access_type` | Enum `AccessType` | NOT NULL | `public`/`private`/`sync`/`sync_restricted` |
| `deletion_failure_message` | String | nullable | |
| `auto_sync_options` | JSONB | nullable | Cấu hình perm sync theo từng nguồn |
| `last_time_perm_sync` | DateTime(tz) | nullable | |
| `last_time_external_group_sync` | DateTime(tz) | nullable | |
| `last_successful_index_time` | DateTime(tz) | nullable | **Thời điểm kết thúc**, không dùng để tính job nền (job dùng time started) |
| `last_pruned` | DateTime(tz) | nullable, **index** | |
| `last_time_hierarchy_fetch` | DateTime(tz) | nullable | |
| `total_docs_indexed` | Integer | default `0` | |
| `indexing_trigger` | Enum `IndexingMode` | nullable | `update`/`reindex` |
| `prune_requested_at` | DateTime(tz) | nullable | Prune đang chờ, beat chạy đúng một lần kể cả khi không có `prune_freq` |
| `prune_after_reindex_requested_at` | DateTime(tz) | nullable | Khi set, mọi attempt mới là full re-index |
| `full_reindex_requested_at` | DateTime(tz) | nullable | Khi set, mọi attempt mới trên search settings hiện tại là full re-index; xóa khi một attempt thành công |
| `perm_sync_pending_since` | DateTime(tz) | nullable | **Khi set, pair không cấp quyền gì lúc query** và guard ẩn document của nó. Xóa khi permission đã vào document index |
| `indexing_hold_released_at` | DateTime(tz) | nullable | Admin ép index bất chấp hold của connector check |
| `pending_backfills` | `PydanticListType(PendingBackfill)` | NOT NULL, server_default `'[]'::jsonb` | Hàng đợi backfill, cũ trước. Beat tạo từng cái một khi pair `ACTIVE` và không có attempt đang chạy; giữ request đến khi một attempt thành công |
| `processing_mode` | Enum `ProcessingMode` | NOT NULL, default `REGULAR` | `REGULAR` (chunk→embed→index), `FILE_SYSTEM` (deprecated), `RAW_BINARY` |
| `creator_id` | UUID | nullable, **không phải FK** | Quan hệ tới `User` qua `primaryjoin` thủ công |

### 4.4. `credential_capability_report`

Báo cáo capability-check mới nhất theo (credential, phạm vi connector). Một dòng credential-time (`connector_id` NULL) + mỗi connector gắn vào một dòng.

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `credential_id` | Integer | FK `credential.id` CASCADE, NOT NULL, index | |
| `connector_id` | Integer | FK `connector.id` CASCADE, nullable | NULL đánh dấu báo cáo credential-time không cần config |
| `source` | Enum `DocumentSource` | NOT NULL | Denormalize để hỗ trợ truy vấn support theo nguồn |
| `connector_config_hash` | String | nullable | sha256 config JSON chuẩn hóa; tín hiệu stale |
| `trigger` | Enum `CapabilityCheckTrigger` | NOT NULL | Last-write-wins |
| `report` | JSONB | nullable | Báo cáo COMPLETED gần nhất — giữ để **vẫn đọc được khi đang chạy lại** |
| `run_status` | Enum `CapabilityReportRunStatus` | NOT NULL | `running`/`completed`/`failed_to_run` |
| `run_started_at` | DateTime(tz) | nullable | |
| `run_id` | UUID | nullable | Attempt đang sở hữu vòng đời; các ghi terminal bị fence theo nó. NULL = không attempt nào sở hữu. **Không bao giờ được tra cứu, nên không có index** |
| `time_created`, `time_updated` | DateTime(tz) | | |

Hai partial unique index tạo ngữ nghĩa latest-only:

- `uq_capability_report_connector_scope` UNIQUE (`credential_id`, `connector_id`) WHERE `connector_id IS NOT NULL`
- `uq_capability_report_credential_scope` UNIQUE (`credential_id`) WHERE `connector_id IS NULL`

### 4.5. `capability_check_run`

Lịch sử từng lần chạy, giữ lại sau khi dòng report đã chuyển sang lần chạy khác.

| Cột | Kiểu | Ràng buộc |
|---|---|---|
| `id` | Integer | PK |
| `credential_id` | Integer | FK `credential.id` CASCADE, NOT NULL |
| `connector_id` | Integer | FK `connector.id` CASCADE, nullable |
| `run_id` | UUID | NOT NULL, **UNIQUE** |
| `trigger` | Enum `CapabilityCheckTrigger` | NOT NULL |
| `status` | Enum `CapabilityCheckRunStatus` | NOT NULL |
| `report` | JSONB | nullable |
| `error_message` | Text | nullable |
| `time_created` | DateTime(tz) | `now()` |
| `time_finished` | DateTime(tz) | nullable |

Index: `ix_capability_check_run_scope_time` (`credential_id`, `connector_id`, `time_created`); `ix_capability_check_run_connector_id` (phục vụ cascade khi xóa connector).

### 4.6. Federated connector

| Bảng | Cột | Ghi chú |
|---|---|---|
| `federated_connector` | `id` PK; `source` Enum `FederatedConnectorSource`; `credentials` **EncryptedJson** NOT NULL; `config` JSONB NOT NULL default `{}` | Hiện chỉ có `federated_slack` |
| `federated_connector_oauth_token` | `id` PK; `federated_connector_id` FK CASCADE NOT NULL; `user_id` FK `user.id` CASCADE NOT NULL; `token` **EncryptedString** NOT NULL; `expires_at` DateTime (**không tz**) nullable | Token OAuth theo từng user |
| `federated_connector__document_set` | `id` PK; `federated_connector_id` FK CASCADE; `document_set_id` FK CASCADE; `entities` JSONB NOT NULL; UNIQUE (`federated_connector_id`, `document_set_id`) | `entities` unique theo loại nguồn, validate trước khi insert |

---

## 5. Indexing và đồng bộ

### 5.1. `search_settings`

Mỗi dòng là một cấu hình embedding + index tương ứng. Trạng thái `PAST` / `PRESENT` / `FUTURE` điều khiển vòng đời reindex.

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `model_name` | String | | |
| `model_dim` | Integer | | |
| `normalize` | Boolean | | |
| `query_prefix`, `passage_prefix` | String | nullable | |
| `status` | Enum `IndexModelStatus` | | `PAST`/`PRESENT`/`FUTURE` |
| `index_name` | String | | |
| `provider_type` | FK `embedding_provider.provider_type` | nullable | |
| `switchover_type` | Enum `SwitchoverType` | default `REINDEX` | `reindex` (chờ mọi connector) / `active_only` (chỉ chờ connector không pause) / `instant` |
| `use_port_flow` | Boolean | NOT NULL, default `False` | Khi `True`, FUTURE được lấp bằng cách **port chunk từ PRESENT (re-embed)** thay vì chạy lại mọi connector |
| `port_backfill_source_id` | FK `search_settings.id` SET NULL | nullable | Do swap INSTANT đặt, trỏ tới index PAST mà port tiếp tục backfill sau promotion |
| `reclaim_status` | Enum `IndexReclaimStatus` | nullable | NULL = không theo dõi reclaim; set `PENDING` lúc submit reindex trên PRESENT hiện tại |
| `reclaim_stopped_reading_at` | DateTime(tz) | nullable | **Mốc soak là lúc ngừng được đọc, không phải lúc swap** — để backfill INSTANT (đọc PAST sau swap) neo đúng |
| `reclaim_attempts` | Integer | NOT NULL, default `0` | Số lần lỗi liên tiếp; dẫn tới `BLOCKED` |
| `reclaim_last_error` | String | nullable | |
| `pending_cc_pair_deletions` | ARRAY(Integer) | nullable | cc_pair đã đồng ý xóa khi port xong; **validate lại lúc thực thi** (chỉ xóa cái còn INVALID/PAUSED) |
| `vector_quantization` | Enum `VectorQuantization` | NOT NULL, default `NONE` | `none`/`scalar_7_bit`/`scalar_1_bit`. Thuộc index mapping của OpenSearch nên **cố định suốt đời index của dòng này** |
| `reduced_dimension` | Integer | nullable | Giảm chiều vector; hiện chỉ dùng được với model OpenAI |
| `multipass_indexing` | Boolean | default `True` | |
| `enable_contextual_rag` | Boolean | default `False` | |
| `contextual_rag_model_configuration_id` | FK `model_configuration.id` SET NULL | nullable | Thay cho các cột chuỗi đã deprecated |

Index:

- `ix_embedding_model_present_unique` UNIQUE (`status`) WHERE `status = PRESENT` — **tối đa một PRESENT**
- `ix_embedding_model_future_unique` UNIQUE (`status`) WHERE `status = FUTURE` — **tối đa một FUTURE**
- `ix_search_settings_reclaimable` (`reclaim_status`) WHERE `status = PAST`

### 5.2. `index_attempt`

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `connector_credential_pair_id` | Integer | FK, NOT NULL, index | |
| `search_settings_id` | Integer | FK `search_settings.id` **SET NULL**, nullable | |
| `from_beginning` | Boolean | | Chỉ `True` với attempt đánh dấu rõ qua API run-once |
| `targeted_reindex_job_id` | FK SET NULL | nullable, index | NULL trên attempt full-run. Nơi chỉ quan tâm full run thì lọc `IS NULL` |
| `is_synthetic_seed` | Boolean | NOT NULL, default `False` | Attempt "mồi" cho con trỏ poll FUTURE của port, không phải lần chạy connector |
| `is_backfill` | Boolean | NOT NULL, default `False` | Chạy một lần trên cửa sổ `poll_range_start..end` cố định. Là full run về mặt concurrency nhưng **nằm ngoài cursor tăng dần, checkpoint reuse, status và lịch của pair** |
| `connector_config_override` | JSONB | nullable | Config backfill dùng thay config đã lưu |
| `prune_after_reindex_requested_at` | DateTime(tz) | nullable | Copy từ pair lúc tạo; thành công thì biến thành prune request |
| `full_reindex_requested_at` | DateTime(tz) | nullable | Copy từ pair lúc tạo; thành công thì xóa trên pair |
| `status` | Enum `IndexingStatus` | | 7 giá trị |
| `new_docs_indexed`, `total_docs_indexed`, `docs_removed_from_index` | Integer | default `0` | |
| `error_msg`, `full_exception_trace` | Text | nullable | Chỉ điền khi `failed` |
| `poll_range_start`, `poll_range_end` | DateTime(tz) | nullable | |
| `checkpoint_pointer` | String | nullable | **Con trỏ sang FileStore**, giá trị checkpoint thật không nằm trong Postgres |
| `connector_config_hash` | String | nullable | sha256 config attempt đã chạy. Attempt sau **không tái dùng checkpoint/poll window** nếu hash khác. NULL không bao giờ chặn reuse |
| `celery_task_id` | String | nullable | Điều phối bằng database thay cho Redis fencing |
| `cancellation_requested` | Boolean | default `False` | |
| `total_batches` | Integer | nullable | Khi set, docfetching đã xong |
| `completed_batches` | Integer | default `0` | |
| `total_failures_batch_level` | Integer | default `0` | **Code ghi chú là không dùng, cần xóa** |
| `total_chunks` | Integer | default `0` | |
| `last_progress_time` | DateTime(tz) | nullable | Phát hiện stall |
| `last_batches_completed_count` | Integer | default `0` | |
| `heartbeat_counter`, `last_heartbeat_value` | Integer | default `0` | Phát hiện worker còn sống |
| `last_heartbeat_time` | DateTime(tz) | nullable | |
| `time_created` | DateTime(tz) | `now()`, index | |
| `time_started` | DateTime(tz) | nullable | **Dùng đồng hồ của api_server, không phải của DB** |
| `time_updated` | DateTime(tz) | `now()`/`onupdate` | |
| `time_finished` | DateTime(tz) | nullable | Không có trên attempt kết thúc trước khi cột này tồn tại |

Index: `ix_index_attempt_latest_for_connector_credential_pair` (cc_pair, time_created); `ix_index_attempt_ccpair_search_settings_time_updated`; `ix_index_attempt_cc_pair_settings_poll` (cc_pair, settings, status, time_updated DESC); `ix_index_attempt_active_coordination` (cc_pair, settings, status).

### 5.3. `port_attempt`

Một lần port chunk của cc_pair từ PRESENT sang FUTURE, re-embed theo settings FUTURE. **Cursor theo doc-id**, khác hẳn `IndexAttempt`.

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `cc_pair_id` | Integer | FK CASCADE, nullable, index | |
| `port_user_id` | UUID | FK `user.id` CASCADE, nullable, index | |
| `search_settings_id` | Integer | FK CASCADE, NOT NULL, index | Settings **FUTURE** |
| `status` | Enum `PortAttemptStatus` | NOT NULL, default `NOT_STARTED`, index | |
| `last_processed_doc_id` | String | nullable | Cursor resume, commit theo từng batch |
| `up_to_doc_id` | String | nullable | Cận trên (max `Document.id` lúc tạo attempt) để port phủ đúng backlog và **không đuổi theo doc thêm mới trong lúc chạy** — đó là việc của poll FUTURE. NULL = không giới hạn (attempt cũ) |
| `docs_ported` | Integer | NOT NULL, default `0` | |
| `last_progress_time` | DateTime(tz) | nullable | Watchdog fail attempt bị treo |
| `cancel_requested` | Boolean | NOT NULL, default `False` | **Yêu cầu hủy không terminal**: port vẫn active (waiter vẫn chặn) cho tới khi task tự chuyển `CANCELED` sau lần ghi cuối |
| `error_msg` | Text | nullable | |
| `celery_task_id` | String | nullable | |
| `time_created`, `time_started`, `time_updated`, `time_completed` | DateTime(tz) | | |

CHECK `ck_port_attempt_exactly_one_scope`: `num_nonnulls(cc_pair_id, port_user_id) = 1`.

Hai partial unique index tách theo scope vì **NULL là distinct trong PostgreSQL**:

- `ix_port_attempt_active_unique` UNIQUE (`cc_pair_id`, `search_settings_id`) WHERE status ∈ (NOT_STARTED, IN_PROGRESS) AND `cc_pair_id IS NOT NULL`
- `ix_port_attempt_active_unique_user` — tương tự cho `port_user_id`

### 5.4. `port_orphan_candidate`

Doc bị xóa trong lúc port đang lấp index đích, có thể đã "sống lại" ở đó do một bản copy create-only chạy đua. Sweep **chỉ xóa chunk do chính port ghi** (`written_by_port`), nên loại bỏ bản sống lại mà vẫn giữ nguyên doc thực sự được thêm lại.

| Cột | Kiểu | Ràng buộc |
|---|---|---|
| `id` | Integer | PK |
| `search_settings_id` | Integer | FK CASCADE, NOT NULL |
| `cc_pair_id` | Integer | FK CASCADE, nullable, index |
| `port_user_id` | UUID | FK CASCADE, nullable, index |
| `document_id` | String | NOT NULL |
| `created_at` | DateTime(tz) | `now()` |

CHECK `ck_port_orphan_candidate_exactly_one_scope`. Hai partial unique index `uq_port_orphan_candidate_connector` / `_user` cho insert idempotent.

### 5.5. Các bảng attempt / metric còn lại

| Bảng | Cột chính | Ghi chú |
|---|---|---|
| `hierarchy_fetch_attempt` | `id` UUID PK; `connector_credential_pair_id` FK CASCADE NOT NULL; `status` Enum `IndexingStatus` index; `nodes_fetched`, `nodes_updated`; `error_msg`, `full_exception_trace`; `time_created` index, `time_started`, `time_updated` | Index `ix_hierarchy_fetch_attempt_cc_pair` |
| `index_attempt_errors` | `id` PK; `index_attempt_id` FK index; `connector_credential_pair_id` FK index; `document_id`, `document_link`, `entity_id` nullable; `failed_time_range_start/end`; `failure_message` Text; `is_resolved` Boolean default `False`; `error_type`; `time_created` | Tên bảng số nhiều, khác quy ước phần còn lại |
| `cc_pair_run_resolution` | PK composite (`run_kind`, `attempt_id`); `cc_pair_id` FK CASCADE index; `resolved_at`; `resolved_by_user_id` FK SET NULL nullable | `run_kind` là giá trị `CCPairRunKind`; **ID lần chạy chỉ unique trong bảng của kind đó**. Dòng này chỉ đưa run ra khỏi danh sách lỗi đang mở, **không đổi status** |
| `index_attempt_stage_metric` | `id` PK; `index_attempt_id` FK CASCADE index; `stage` Enum `IndexAttemptStage(length=40)`; `event_count`, `total_duration_ms` BigInteger; `m2_duration_ms` Float; `min_duration_ms`, `max_duration_ms` BigInteger nullable; `time_first_event`, `time_last_event`; UNIQUE (`index_attempt_id`, `stage`) | Lưu **aggregate Welford/Chan** (count, sum, min, max, M2) để tính mean và stddev lúc đọc mà không lưu từng mẫu. `m2` là Float (DOUBLE PRECISION) để upsert SQL áp công thức kết hợp song song của Chan không bị trôi số |
| `sync_record` | `id` PK; `entity_id` Integer (**không phải FK** — là document set id / user group id / deletion id); `sync_type` Enum `SyncType`; `sync_status` Enum `SyncStatus`; `num_docs_synced`, `num_docs_failed`; `sync_start_time`, `sync_end_time`; `error_message` Text nullable (**chỉ prune ghi**) | Hai index theo (`entity_id`, `sync_type`, `sync_start_time`) và (`entity_id`, `sync_type`, `sync_status`) |

### 5.6. `targeted_reindex_job` và `targeted_reindex_job_target`

`targeted_reindex_job` — một dòng cho mỗi yêu cầu reindex của user, cho FE một handle ổn định để poll trạng thái tổng hợp qua nhiều tuple `(cc_pair, search_settings)`.

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `requested_by_user_id` | UUID | FK SET NULL, nullable, index | |
| `requested_at` | DateTime(tz) | NOT NULL, index | |
| `status` | Enum `IndexingStatus` | NOT NULL, default `NOT_STARTED`, index | |
| `celery_task_id` | Text | nullable | **UUID task celery cấp trước**, ghi trước `apply_async` để detector dọn được nếu enqueue lỗi sau INSERT, và để hủy có handle revoke |
| `resolved_count`, `still_failing_count`, `skipped_count` | Integer | NOT NULL, default `0` | |
| `resolved_summary` | JSONB | NOT NULL, default `[]` | Snapshot các dòng lỗi đã giải quyết, **sống lâu hơn** việc dọn dẹp `index_attempt_errors` sau này |
| `completed_at` | DateTime(tz) | nullable | |

`targeted_reindex_job_target` — một dòng cho mỗi doc mà job sẽ chạm. Tách bảng (thay vì JSONB trên job) để từng dòng FK được tới `IndexAttemptError` nguồn và tới `cc_pair` cho cascade.

PK composite (`targeted_reindex_job_id`, `cc_pair_id`, `document_id`); `source_error_id` FK `index_attempt_errors.id` SET NULL nullable index (NULL = reindex tùy ý, không có ngữ cảnh lỗi). Index `ix_targeted_reindex_job_target_cc_pair_doc`.

### 5.7. `embedding_provider`

| Cột | Kiểu | Ràng buộc |
|---|---|---|
| `provider_type` | Enum `EmbeddingProvider` (**native enum**) | PRIMARY KEY |
| `api_url`, `api_version`, `deployment_name` | String | nullable |
| `api_key` | **EncryptedString** | |
| `vertex_config` | JSONB | nullable |

Đây là một trong số rất ít enum của Onyx dùng kiểu ENUM thật của PostgreSQL.

---

## 6. Document và hierarchy

### 6.1. `document`

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | NullFilteredString | PK | ID document như Onyx truyền đi |
| `from_ingestion_api` | Boolean | default `False`, nullable | |
| `boost` | Integer | default `DEFAULT_BOOST` | 0 trung tính, dương = ủng hộ, âm = hạ |
| `hidden` | Boolean | default `False` | |
| `semantic_id` | NullFilteredString | | |
| `link` | NullFilteredString | nullable | Link của Section đầu tiên |
| `file_id` | String | nullable | |
| `doc_updated_at` | DateTime(tz) | nullable | TODO trong code: tên cột **trộn lẫn** thời gian doc ở nguồn với thời gian sửa đổi cục bộ |
| `doc_created_at` | DateTime(tz) | nullable | NULL với doc index trước khi có cột này |
| `chunk_count` | Integer | nullable | |
| `content_hash` | String | nullable | MD5 của title + section text lần index thành công gần nhất, để bỏ qua re-index khi nội dung không đổi |
| `last_modified` | DateTime(tz) | NOT NULL, index, default `now()` | Lần cuối metadata liên quan document index hoặc doc đổi; **không tính `last_synced`** |
| `last_synced` | DateTime(tz) | nullable, index | |
| `secondary_only_sync_pending` | Boolean | NOT NULL, server_default `false` | `True` khi metadata sync chạm PRESENT nhưng doc chưa có trong FUTURE (reindex port). Swap **chờ** các dòng này |
| `primary_owners`, `secondary_owners` | ARRAY(String) | nullable | Không gắn với `User` vì Onyx có thể không biết tài khoản |
| `external_user_emails` | ARRAY(String) | nullable | Permission sync ở mức document |
| `external_user_group_ids` | ARRAY(String) | nullable | Đã prefix theo loại nguồn |
| `is_public` | Boolean | default `False` | |
| `parent_hierarchy_node_id` | Integer | FK `hierarchy_node.id` **SET NULL**, nullable, index | |
| `kg_stage` | Enum `KGStage` | index | Trạng thái trích xuất knowledge graph |
| `kg_processing_time` | DateTime(tz) | nullable | |
| `doc_metadata` | JSONB | nullable | |

Hai partial index quan trọng:

- `ix_document_needs_sync` trên `id` WHERE `last_modified > last_synced OR last_synced IS NULL`
- `ix_document_secondary_only_sync_pending` trên `id` WHERE `secondary_only_sync_pending IS TRUE`

### 6.2. `hierarchy_node`

Node cấu trúc của nguồn (folder, drive, space, project, channel), **mang luôn thông tin permission** theo cùng mô hình với `Document`, để duyệt cây theo phạm vi của từng user.

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `raw_node_id` | String | NOT NULL | Định danh thô từ hệ nguồn. Với node `SOURCE` thì là tên nguồn |
| `display_name` | String | NOT NULL | |
| `link` | NullFilteredString | nullable | |
| `source` | Enum `DocumentSource` | NOT NULL | |
| `node_type` | Enum `HierarchyNodeType` | NOT NULL | 13 giá trị: `folder`, `source`, `stub`, `shared_drive`, `my_drive`, `space`, `page`, `project`, `database`, `workspace`, `site`, `drive`, `channel`, `mailbox` |
| `external_user_emails`, `external_user_group_ids` | ARRAY(String) | nullable | |
| `is_public` | Boolean | default `False` | Node `SOURCE` luôn public |
| `document_id` | String | FK `document.id` **SET NULL**, nullable, index | Với node vừa là document (ví dụ trang Confluence) |
| `parent_id` | Integer | FK `hierarchy_node.id` **SET NULL**, nullable, index | Cây tự tham chiếu; xóa cha thì **mồ côi con** để prune dọn sau |

UNIQUE `uq_hierarchy_node_raw_id_source` (`raw_node_id`, `source`); index `ix_hierarchy_node_source_type`.

### 6.3. Các bảng liên kết document

| Bảng | Khóa | Ghi chú |
|---|---|---|
| `chunk_stats` | `id` NullFilteredString PK (mặc định sinh từ `{document_id}__{chunk_in_doc_id}`); `document_id` FK NOT NULL index; `chunk_in_doc_id` Integer NOT NULL; `information_content_boost` Float nullable; `last_modified` NOT NULL index; `last_synced` nullable index | UNIQUE `uq_chunk_stats_doc_chunk`; index `ix_chunk_sync_status` (`last_modified`, `last_synced`) |
| `tag` | `id` PK; `tag_key`, `tag_value` String; `source` Enum; `is_list` Boolean NOT NULL default `False` | UNIQUE `_tag_key_value_source_list_uc` (`tag_key`,`tag_value`,`source`,`is_list`) |
| `document__tag` | PK (`document_id` FK, `tag_id` FK index) | |
| `document_by_connector_credential_pair` | PK (`id` FK `document.id`, `connector_id` FK CASCADE, `credential_id` FK CASCADE); `has_been_indexed` Boolean | TODO trong code: nên chuyển sang dùng thẳng `ConnectorCredentialPair.id`. `has_been_indexed` để doc thêm bởi permission sync **không bị đếm** vào số doc của connector cho tới khi index xong. Index `idx_document_cc_pair_connector_credential`, `idx_document_cc_pair_counts` |
| `hierarchy_node_by_connector_credential_pair` | PK (`hierarchy_node_id` FK CASCADE, `connector_id`, `credential_id`) + `ForeignKeyConstraint` composite tới (`connector_credential_pair.connector_id`, `.credential_id`) CASCADE on delete/update | Prune xóa entry stale của cc_pair hiện tại; node còn 0 entry thì bị xóa |

### 6.4. `document_set` và liên kết

| Bảng | Cột | Ghi chú |
|---|---|---|
| `document_set` | `id` PK; `name` String UNIQUE; `description`; `user_id` FK CASCADE nullable; `is_up_to_date` Boolean NOT NULL default `False`; `is_public` Boolean NOT NULL default `True`; `time_last_modified_by_user` | |
| `document_set__connector_credential_pair` | PK (`document_set_id`, `connector_credential_pair_id`, **`is_current`**) | `is_current=False` là **trạng thái cũ** của document set; phải bị xóa khi cập nhật, và không được tồn tại khi `is_up_to_date == True` |
| `document_set__user` | PK (`document_set_id` FK, `user_id` FK CASCADE nullable) | |
| `document_set__user_group` | PK (`document_set_id` FK CASCADE, `user_group_id` FK) | EE |

---

## 7. Knowledge Graph

Tám bảng, chia thành cặp **bản chính** và **bản staging** (`*_extraction_staging`) với cờ `transferred`.

| Bảng | Khóa chính | Cột đáng chú ý |
|---|---|---|
| `kg_entity_type` | `id_name` String PK | `description`, `grounding` NOT NULL, `attributes` JSONB (comment: "Filtering based on document attribute"), `occurrences` Integer default 1, `active` Boolean default `False`, `deep_extraction` Boolean default `False`, `grounded_source_name`, `entity_values` ARRAY(String), `clustering` JSONB NOT NULL; `time_created`, `time_updated` |
| `kg_entity` | `id_name` NullFilteredString PK | `name`, `entity_key`, `parent_key`, `name_trigrams` **ARRAY(String(3))**, `attributes` JSONB, `document_id` (**không phải FK**), `alternative_names` ARRAY, `entity_type_id_name` FK, `description`, `keywords` ARRAY, `occurrences`, `acl` **ARRAY(String)** (access control), `boosts` JSONB, `event_time` |
| `kg_entity_extraction_staging` | `id_name` PK | Như trên + `transferred_id_name` nullable; không có `name_trigrams`, không có `time_updated` |
| `kg_relationship_type` | `id_name` PK | `name`, `source_entity_type_id_name` FK, `target_entity_type_id_name` FK, `definition` Boolean, `clustering` JSONB, `type`, `active` default `True`, `occurrences` |
| `kg_relationship_type_extraction_staging` | `id_name` PK | Như trên + `transferred` Boolean |
| `kg_relationship` | **PK composite (`id_name`, `source_document`)** | `source_document` FK `document.id` **nullable** (nên PK có thành phần nullable); `source_node`/`target_node` FK `kg_entity.id_name`; `source_node_type`/`target_node_type` FK `kg_entity_type.id_name`; `type`; `relationship_type_id_name` FK; `occurrences`. UNIQUE `uq_kg_relationship_source_target_type` (`source_node`,`target_node`,`type`) |
| `kg_relationship_extraction_staging` | PK composite như trên | FK trỏ sang bảng staging; `transferred` Boolean. **UNIQUE trùng tên** `uq_kg_relationship_source_target_type` với bảng trên (tên constraint lặp giữa hai bảng) |
| `kg_term` | `id_term` PK | `entity_types` ARRAY(String) NOT NULL |

Lưu ý: `kg_relationship` và bản staging dùng `PrimaryKeyConstraint("id_name", "source_document")` trong khi `source_document` khai báo `nullable=True`. PostgreSQL sẽ ép NOT NULL cho cột PK, nên khai báo nullable ở ORM không phản ánh ràng buộc thật.

---

## 8. Chat và message

### 8.1. `chat_session`

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | UUID | PK, default `uuid4` | |
| `user_id` | UUID | FK `user.id` CASCADE, nullable | |
| `persona_id` | Integer | FK `persona.id`, nullable | |
| `description` | Text | nullable | |
| `onyxbot_flow` | Boolean | default `False` | Chat do OnyxBot tạo |
| `incognito_record_mode` | Enum `IncognitoRecordMode` (lưu *value*) | nullable | **Ghim lúc tạo**, nên đổi setting sau đó không ảnh hưởng session đang chạy. NULL = chat thường. Trong các mode incognito, **chỉ `full_history` mới ghi nội dung hội thoại vào message** |
| `deleted` | Boolean | default `False` | Chỉ set `True` khi hệ thống cấu hình không hard-delete chat |
| `shared_status` | Enum `ChatSessionSharedStatus` | default `PRIVATE` | `public`/`private` |
| `current_alternate_model` | String | nullable | |
| `slack_thread_id` | String | nullable | |
| `project_id` | Integer | FK `user_project.id`, nullable | |
| `llm_override` | `PydanticType(LLMOverride)` | nullable | Hiện chỉ dùng cho luồng chat seeding |
| `temperature_override` | Float | nullable | |
| `reasoning_effort_override` | Enum `ReasoningEffort` (lưu *value*) | nullable | NULL = không override; **`AUTO` không bao giờ được lưu** |
| `prompt_override` | `PydanticType(PromptOverride)` | nullable | |
| `time_created`, `time_updated` | DateTime(tz) | | |

Index `ix_chat_session_user_id_onyxbot_flow_time_updated` (`user_id`, `onyxbot_flow`, `time_updated` DESC) — đúng truy vấn sidebar lịch sử chat.

### 8.2. `chat_message`

Message đầu chuỗi **không có nội dung** — là node gốc rỗng, workaround để sửa được message đầu tiên của session. Mỗi user message thường đi kèm một LLM response, nhưng chúng là hai dòng riêng để mở đường cho agentification.

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `chat_session_id` | UUID | FK `chat_session.id` (**không CASCADE ở DB**; cascade do ORM) | |
| `parent_message_id` | Integer | FK `chat_message.id`, nullable | Con trỏ cây |
| `latest_child_message_id` | Integer | FK `chat_message.id`, nullable | **Chỉ map tới nhánh mới nhất** vì chỉ chuỗi đó mới cần; có thể cập nhật để lần theo nhánh khác |
| `last_summarized_message_id` | String | nullable | Đặt trên message tóm tắt: ID message cuối được phủ. `chat:<id>` nghĩa là phủ toàn bộ chat message có row ID đó |
| `preferred_response_id` | Integer | FK `chat_message.id` **SET NULL**, nullable | Với lượt đa-model: user message trỏ tới response assistant được chọn để tiếp tục |
| `model_display_name` | String | nullable | |
| `request_params` | JSONB | nullable | Reasoning effort yêu cầu + kwargs thực sự gửi provider |
| `reasoning_tokens` | Text | nullable | |
| `message` | Text | | |
| `token_count` | Integer | | |
| `message_type` | Enum `MessageType` | | `system`/`user`/`assistant`/`summary`/`tool_call_response`/`user_reminder` |
| `files` | JSONB (`list[FileDescriptor]`) | nullable | Khi parse vào history thì **thành một message riêng** |
| `citations` | JSONB `dict[int,int]` | nullable | Map số trích dẫn → `search_doc.id` |
| `error` | Text | nullable | |
| `time_sent` | DateTime(tz) | `now()` | |
| `is_clarification` | Boolean | default `False` | Câu hỏi làm rõ trong luồng deep research |
| `processing_duration_seconds` | Float | nullable | Chỉ message assistant |

Index duy nhất: `ix_chat_message_chat_session_id` — chống seq-scan cho mọi truy vấn theo session (replay history, kiểm tra session lỗi, xóa theo retention/GC, cascade xóa message của session).

### 8.3. `tool_call`

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `chat_session_id` | UUID | FK CASCADE | |
| `parent_chat_message_id` | Integer | FK `chat_message.id` CASCADE, nullable | **Khác NULL** = tool call cấp cao nhất từ user message; **NULL** = call cấp thấp từ tool/agent khác |
| `parent_tool_call_id` | Integer | FK `tool_call.id` CASCADE, nullable | Tool call lồng nhau |
| `turn_number` | Integer | | Cùng `turn_number` (và cùng parent) = **gọi song song**; khác = gọi tuần tự |
| `tab_index` | Integer | default `0` | Thứ tự index của tool call từ LLM khi gọi song song |
| `tool_id` | Integer | **không phải FK** | Cố ý: để xóa được tool mà không xóa dòng này |
| `tool_call_id` | String | | ID mà LLM kỳ vọng khớp giữa call và response |
| `reasoning_tokens` | Text | nullable | Reasoning đứng trước call này, **không nằm trong history** |
| `tool_call_arguments` | JSONB | | Với "Agent" như Research Agent, argument và báo cáo cuối được lưu ở đây và ở `tool_call_response` |
| `tool_call_response` | Text | | |
| `tool_call_tokens` | Integer | | **Chỉ đếm token của argument**, vì đó là tất cả những gì giữ cho history. Chỉ tool cấp cao (có `parent_chat_message_id`) mới tính vào tổng của session |
| `generated_images` | JSONB | nullable | Object `GeneratedImage` để replay tool sinh ảnh |

### 8.4. `search_doc` và liên kết

`search_doc` **khác** bảng `document`: nó lưu *trạng thái của một document tại thời điểm truy xuất*, để replay lại phiên chat. **Không chứa nội dung** của Document/Chunk — nếu chọn một `SearchDoc` đã lưu thì vẫn phải inference lại để lấy nội dung.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | Integer PK | |
| `document_id` | String | **Không phải FK** |
| `chunk_ind` | Integer | |
| `semantic_id`, `link`, `blurb` | String | |
| `boost` | Integer | |
| `source_type` | Enum `DocumentSource` | |
| `hidden` | Boolean | |
| `doc_metadata` | JSONB | |
| `score` | Float | |
| `match_highlights` | ARRAY(String) | |
| `updated_at` | DateTime(tz) nullable | Của **document**, không phải của dòng này |
| `primary_owners`, `secondary_owners` | ARRAY(String) nullable | |
| `is_internet` | Boolean default `False`, nullable | |
| `is_relevant` | Boolean nullable | |
| `relevance_explanation` | String nullable | |

Hai bảng nối: `chat_message__search_doc` (PK: `chat_message_id` FK CASCADE, `search_doc_id` FK CASCADE) và `tool_call__search_doc` (PK: `tool_call_id`, `search_doc_id`, cả hai CASCADE). Quan hệ ORM khai báo `cascade="all, delete-orphan", single_parent=True` — nghĩa là một `SearchDoc` thuộc về đúng một parent ở phía ORM.

### 8.5. `search_query`

Dành cho Search UI: không có followup và lưu ít hơn, vì chức năng "reply" chỉ là chạy lại truy vấn.

`id` UUID PK; `user_id` FK CASCADE; `query` String; `query_expansions` ARRAY(String) nullable; `created_at`.

### 8.6. Feedback

| Bảng | Cột |
|---|---|
| `chat_feedback` (model `ChatMessageFeedback`) | `id` PK; `chat_message_id` FK **SET NULL** nullable; `is_positive` Boolean nullable; `required_followup` Boolean nullable; `feedback_text` Text; `predefined_feedback` String |
| `document_retrieval_feedback` | `id` PK; `chat_message_id` FK **SET NULL** nullable; `document_id` FK `document.id`; `document_rank` Integer (1 = đầu tiên); `clicked` Boolean default `False`; `feedback` Enum `SearchFeedbackType` nullable (`endorse`/`reject`/`hide`/`unhide`) |

Cả hai dùng SET NULL để feedback **sống lâu hơn** message mà nó phản hồi.

---

## 9. LLM và provider

### 9.1. `llm_provider`

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `name` | String | nullable | |
| `provider` | String | | |
| `api_key` | **EncryptedString** | nullable | |
| `api_base`, `api_version` | String | nullable | |
| `zoom_voice_provider_id` | Integer | FK `voice_provider.id` **RESTRICT**, nullable, index, **UNIQUE** | |
| `custom_config` | JSONB | nullable | Ví dụ `AWS_ACCESS_KEY_ID` cho Bedrock |
| `default_model_name` | String | nullable | **Deprecated** — dùng `LLMModelFlow` với flow `CHAT` |
| `deployment_name` | String | nullable | |
| `is_default_provider` | Boolean | nullable | **Deprecated** — dùng `LLMModelFlow.is_default` flow `CHAT` |
| `is_default_vision_provider` | Boolean | | **Deprecated** |
| `default_vision_model` | String | nullable | **Deprecated** |
| `is_public` | Boolean | NOT NULL, default `True` | EE |
| `is_auto_mode` | Boolean | NOT NULL, default `False` | Model/visibility/default do config GitHub quản lý |

### 9.2. `model_configuration`

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `llm_provider_id` | Integer | FK CASCADE, NOT NULL | |
| `name` | String | NOT NULL | |
| `is_visible` | Boolean | NOT NULL, default `False` | Với "Custom LLM Provider" thì **luôn `True`** vì danh sách model do chính user cung cấp |
| `max_input_tokens` | Integer | nullable | |
| `supports_image_input` | Boolean | nullable | **Deprecated** — dùng `LLMModelFlow` flow `VISION` |
| `display_name` | String | nullable | Từ API nguồn với provider động (OpenRouter, Bedrock, Ollama); provider tĩnh có thể null rồi fallback LiteLLM |
| `custom_display_name` | String | nullable | Override của admin, **ưu tiên cao nhất** |
| `reasoning_effort_max`, `reasoning_effort_default` | Enum `ReasoningEffort` (lưu *value*) | nullable | **Không bao giờ lưu `AUTO`**: không set đã nghĩa là AUTO |
| `temperature_default` | Float | nullable | |
| `is_router` | Boolean | NOT NULL, default `False` | Entry ảo, ủy quyền chọn model cho lớp routing |

### 9.3. `llm_model_flow`

| Cột | Kiểu | Ràng buộc |
|---|---|---|
| `id` | Integer | PK |
| `llm_model_flow_type` | Enum `LLMModelFlowType` | NOT NULL |
| `model_configuration_id` | Integer | FK CASCADE, NOT NULL |
| `is_default` | Boolean | NOT NULL, default `False` |

- UNIQUE `uq_model_config_per_llm_model_flow_type` (`llm_model_flow_type`, `model_configuration_id`)
- **`ix_one_default_per_llm_model_flow` UNIQUE (`llm_model_flow_type`) WHERE `is_default = True`** — mỗi flow đúng một model mặc định ở mức database.

Tám flow: `chat`, `vision`, `contextual_rag`, `reasoning`, `chat_naming`, `search_selection`, `decision`, `craft`.

### 9.4. Các provider còn lại

| Bảng | Cột | Ràng buộc đáng chú ý |
|---|---|---|
| `image_generation_config` | `image_provider_id` String **PK**; `model_configuration_id` FK CASCADE NOT NULL; `is_default` Boolean | Index trên `is_default` và `model_configuration_id` (không unique) |
| `voice_provider` | `id` PK; `name` String UNIQUE; `provider_type` String (`openai`/`azure`/`elevenlabs`/`zoom`); `api_key`, `api_secret` **EncryptedString**; `api_base`; `custom_config` JSONB; `stt_model`, `tts_model`, `default_voice`; `is_default_stt`, `is_default_tts` Boolean NOT NULL | Hai partial unique index `ix_voice_provider_one_default_stt` / `_tts` → **đúng một default STT và một default TTS ở mức DB** |
| `internet_search_provider` | `id` PK; `name` UNIQUE NOT NULL; `provider_type` NOT NULL; `api_key` **EncryptedString**; `config` JSONB; `is_active` Boolean NOT NULL default `False`; timestamps | |
| `internet_content_provider` | Như trên nhưng `config` là `PydanticType(WebContentProviderConfig)` | |
| `tracing_provider_config` | `id` PK; `provider_type` String **UNIQUE** NOT NULL; `enabled` Boolean default `True`; `api_key` **EncryptedString**; `config` JSONB; `updated_by_user_id` FK SET NULL; timestamps | `api_key` giữ Braintrust API key / Langfuse secret key; thiết lập không bí mật (Braintrust project; Langfuse public_key, host) nằm trong `config` |
| `model_cost_override` | `id` PK; `model` String NOT NULL; `provider` String NOT NULL **default `''`**; `input_cost_per_mtok`, `output_cost_per_mtok` Numeric(18,6) NOT NULL; `cache_read_cost_per_mtok` nullable; timestamps; UNIQUE (`provider`,`model`) | Dùng `''` thay NULL để unique key chạy trên **mọi phiên bản PostgreSQL** mà không cần `NULLS NOT DISTINCT` (PG15+). Giá tính theo USD / triệu token; null ở cache-read nghĩa là tính theo giá input |

---

## 10. Persona, tool, skill, project

### 10.1. `persona`

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | Integer | PK | |
| `user_id` | UUID | FK `user.id` **SET NULL**, nullable | **Cố ý SET NULL** thay vì CASCADE: xóa user thì persona **mồ côi về tay admin**, không bị hủy |
| `owner_group_id` | Integer | FK `user_group.id` SET NULL, nullable | EE. Loại trừ nhau với `user_id` |
| `name`, `description` | String | | |
| `default_model_configuration_id` | Integer | FK `model_configuration.id` SET NULL, nullable | **Chỉ áp dụng khi sinh câu trả lời thật**, không dùng cho time filter / relevance filter tự phát hiện |
| `starter_messages` | `PydanticListType(StarterMessage)` | nullable | |
| `search_start_date` | DateTime(tz) | nullable | |
| `builtin_persona` | Boolean | default `False` | Cấu hình từ backend lúc deploy, user không sửa được |
| `is_featured` | Boolean | default `False` | |
| `is_listed` | Boolean | default `True` | |
| `display_priority` | Integer | nullable | Cao hơn hiển thị trước; hòa thì ID nhỏ hơn trước |
| `deleted` | Boolean | default `False` | |
| `system_prompt` | String(5_000_000) | nullable | `PROMPT_LENGTH = 5_000_000` |
| `replace_base_system_prompt` | Boolean | default `False` | |
| `task_prompt` | String(5_000_000) | nullable | |
| `datetime_aware` | Boolean | default `True` | |
| `uploaded_image_id`, `icon_name` | String | nullable | |
| `is_public` | Boolean | NOT NULL, default `True` | EE |
| `public_permission` | Enum `PersonaSharePermission` | NOT NULL, default `VIEWER` | Mức cấp cho cả tổ chức khi `is_public` |

- Partial unique `_builtin_persona_name_idx` trên `name` WHERE `builtin_persona = True`.
- **CHECK `ck_persona_single_owner`: `user_id IS NULL OR owner_group_id IS NULL`** — persona thuộc đúng một user XOR một group; cả hai NULL trên persona không builtin nghĩa là mồ côi, thuộc về admin.

### 10.2. `tool` và `oauth_config`

| Bảng | Cột | Ghi chú |
|---|---|---|
| `tool` | `id` PK; `name` NOT NULL (tên LLM nhìn thấy); `description` Text nullable; `in_code_tool_id` String nullable (chỉ tool trong code; tool tạo qua UI là None); `display_name`; `openapi_schema` JSONB (chỉ tool định nghĩa qua UI); `mcp_input_schema` JSONB (chỉ tool MCP); `custom_headers` JSONB; `user_id` FK CASCADE nullable (None với tool built-in); `passthrough_auth` Boolean default `False` (chuyển tiếp OAuth token của user làm header Authorization); `mcp_server_id` FK CASCADE nullable; `oauth_config_id` FK SET NULL nullable; `enabled` Boolean NOT NULL default `True` | |
| `tool_user_preference` | PK (`user_id` FK CASCADE, `tool_id` FK CASCADE); `enabled_in_chat` Boolean NOT NULL default `True` | |
| `oauth_config` | `id` PK; `name` UNIQUE NOT NULL; `authorization_url`, `token_url` Text NOT NULL; `client_id`, `client_secret` **EncryptedString** NOT NULL; `scopes` JSONB nullable; `additional_params` JSONB nullable; `supports_pkce` Boolean NOT NULL default `False`; timestamps | Dùng chung cho nhiều tool |
| `oauth_user_token` | `id` PK; `oauth_config_id` FK CASCADE NOT NULL; `user_id` FK CASCADE NOT NULL; `token_data` **EncryptedJson** NOT NULL; timestamps; UNIQUE `uq_oauth_user_token` (`oauth_config_id`,`user_id`) | `token_data` chứa access_token, refresh_token, token_type, expires_at, scope |

### 10.3. `skill`

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | UUID | PK, default `uuid4` | |
| `name` | String(64) | NOT NULL | **Bất biến**: vừa là tên Agent Skills vừa là tên thư mục sandbox |
| `description` | Text | NOT NULL | |
| `built_in_skill_id` | String | nullable | **Discriminator**: khi set, định nghĩa lấy từ `BUILT_IN_SKILLS` trong code |
| `bundle_file_id` | String | nullable | Bytes bundle cho skill custom; NULL với built-in (file nguồn nằm trên đĩa) |
| `bundle_sha256` | String(64) | nullable | |
| `is_valid` | Boolean | nullable | Dòng custom có sẵn được phân loại lười trước khi hydrate sandbox |
| `author_user_id` | UUID | FK SET NULL, nullable | |
| `public_permission` | Enum `SkillSharePermission` | nullable | |
| `installation_policy` | Enum `SkillInstallationPolicy` | NOT NULL, default `AVAILABLE` | `AVAILABLE`/`DEFAULT`/`REQUIRED` |
| `created_at`, `updated_at` | DateTime(tz) | NOT NULL | |

Ràng buộc:

- Partial unique `uq_skill_automatic_name` trên `name` WHERE `installation_policy <> 'AVAILABLE'`
- UNIQUE `uq_skill_name_id` (`name`, `id`) — tồn tại để `user_skill_preference` FK composite được
- CHECK `ck_skill_definition_source`: `(built_in_skill_id IS NULL) <> (bundle_file_id IS NULL)` — **đúng một trong hai**
- CHECK `ck_private_skill_has_owner`: `built_in_skill_id IS NOT NULL OR public_permission IS NOT NULL OR author_user_id IS NOT NULL`

### 10.4. `user_skill_preference`

Ví dụ hiếm gặp về **FK composite tới một cặp (name, id) được denormalize**:

| Cột | Kiểu | Ràng buộc |
|---|---|---|
| `user_id` | UUID | FK CASCADE, **PK** |
| `skill_id` | UUID | **PK** (không khai FK đơn) |
| `name` | String(64) | NOT NULL — denormalize để enforce unique theo tên |
| `enabled` | Boolean | NOT NULL, default `True` |

- `ForeignKeyConstraint(["name","skill_id"] → ["skill.name","skill.id"])` CASCADE — giữ `name` luôn chính xác.
- Partial unique `uq_user_skill_preference_name` (`user_id`, `name`) WHERE `enabled` — một user không thể bật hai skill trùng tên.

### 10.5. `user_project`, `user_file`

| Bảng | Cột | Ghi chú |
|---|---|---|
| `user_project` | `id` PK autoincrement; `user_id` FK **nullable=False** nhưng type `UUID \| None`; `name` NOT NULL; `description` nullable; `created_at`; `instructions` String | |
| `project__user_file` | PK (`project_id` FK, `user_file_id` FK); `created_at` | Index `ix_project__user_file_project_id_created_at` (`project_id`, `created_at` DESC) |
| `user_file` | xem dưới | |

`user_file`:

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK `user.id`, NOT NULL | |
| `file_id` | String | NOT NULL | Trỏ sang `file_record` (**không phải FK**) |
| `name`, `file_type` | String | NOT NULL | |
| `created_at` | DateTime | default Python `datetime.now(utc)` (**không server_default**) | |
| `token_count`, `chunk_count` | Integer | nullable | |
| `status` | Enum `UserFileStatus` | NOT NULL, default `PROCESSING` | 7 giá trị |
| `incognito` | Boolean | NOT NULL, default `False` | **Quyết định lúc upload từ trạng thái toggle**, nên attachment tạo trước khi session tồn tại đã là private |
| `incognito_session_id` | UUID | nullable, **không FK** | Session nào dọn nó. **Cố ý không FK**: dòng session bị xóa trước và các dòng này phải sống lâu hơn để được sweep |
| `needs_project_sync`, `needs_persona_sync` | Boolean | NOT NULL, default `False` | |
| `secondary_reconcile_pending` | Boolean | NOT NULL, default `False` | Dirty bit reindex-port: index phụ stale/thiếu (nội dung và/hoặc ACL). Rộng hơn `document.secondary_only_sync_pending` (vốn chỉ ACL) |
| `last_project_sync_at`, `last_accessed_at` | DateTime(tz) | nullable | |
| `link_url`, `content_type` | String | nullable | |

Bốn index, trong đó ba là partial:

- `ix_user_file_incognito_sweep` (`incognito_session_id`, `status`, `last_accessed_at`) WHERE `incognito`
- `ix_user_file_secondary_reconcile_pending` (`id`) WHERE `secondary_reconcile_pending IS TRUE`
- `ix_user_file_user_status_id` (`user_id`, `status`, `id`)
- `ix_user_file_user_id_completed` (`user_id`) WHERE `status = 'COMPLETED'`

Comment trong code nêu rõ index được khai cả ở đây lẫn trong migration **để autogenerate không đề xuất drop nhầm**.

### 10.6. Bảng nối của Persona / Skill / InputPrompt

| Bảng | Khóa | Cột thêm |
|---|---|---|
| `persona__document_set` | (`persona_id`, `document_set_id`) | |
| `persona__tool` | (`persona_id` CASCADE, `tool_id` CASCADE) | Dòng ở đây nghĩa là tool **khả dụng** cho persona, **không** đảm bảo dùng được (ví dụ tool sinh ảnh chưa được bật) |
| `persona__persona_label` | (`persona_id`, `persona_label_id` CASCADE) | |
| `persona__user` | (`persona_id`, `user_id` CASCADE nullable) | `permission` Enum `PersonaSharePermission` NOT NULL default `VIEWER` |
| `persona__user_group` | (`persona_id`, `user_group_id`) | `permission` Enum `PersonaSharePermission` |
| `persona__user_file` | (`persona_id` CASCADE, `user_file_id` CASCADE) | |
| `persona__hierarchy_node` | (`persona_id` CASCADE, `hierarchy_node_id` CASCADE) | Gắn folder/space cho tìm kiếm theo phạm vi |
| `persona__document` | (`persona_id` CASCADE, `document_id` CASCADE) | Gắn từng document riêng lẻ |
| `user__pinned_persona` | (`user_id` CASCADE, `persona_id` CASCADE) | `display_order` Integer NOT NULL. Thay cho mảng JSONB cũ; **dense**: mọi đường ghi thay toàn bộ tập của user và đánh số 0..n-1 |
| `assistant__user_specific_config` | (`assistant_id` FK `persona.id` CASCADE, `user_id` CASCADE) | `disabled_tool_ids` ARRAY(Integer) NOT NULL |
| `persona_label` | `id` PK; `name` String UNIQUE | |
| `skill__user` | (`skill_id` CASCADE, `user_id` CASCADE) | `permission` Enum `SkillSharePermission`; index `ix_skill__user_user_id` |
| `skill__user_group` | (`skill_id` CASCADE, `user_group_id` CASCADE) | `permission` Enum `SkillSharePermission` |
| `inputprompt` | `id` PK autoincrement; `prompt`, `content` String; `active` Boolean; `is_public` Boolean NOT NULL default `True`; `user_id` FK CASCADE nullable | UNIQUE `uq_inputprompt_prompt_user_id` (`prompt`,`user_id`) + partial unique `uq_inputprompt_prompt_public` (`prompt`) WHERE `user_id IS NULL` |
| `inputprompt__user` | (`input_prompt_id`, `user_id`) | `disabled` Boolean NOT NULL default `False` |

---

## 11. MCP

| Bảng | Cột | Ghi chú |
|---|---|---|
| `mcp_server` | `id` PK; `owner` String NOT NULL (**email**, không phải FK); `name` NOT NULL; `description`; `server_url` NOT NULL; `transport` Enum `MCPTransport` nullable; `auth_type` Enum `MCPAuthenticationType` nullable; `auth_performer` Enum `MCPAuthenticationPerformer` nullable; `oauth_provider_mode` Enum NOT NULL server_default `AUTO_DISCOVERY`; `oauth_authorization_endpoint`, `oauth_token_endpoint` Text; `oauth_scopes_override` JSONB; `oauth_additional_auth_params` JSONB; `oauth_cimd_enabled` Boolean NOT NULL default `True`; `status` Enum `MCPServerStatus` NOT NULL server_default `CREATED`; `available_in_craft` Boolean NOT NULL default `False`; `admin_connection_config_id` FK `mcp_connection_config.id` SET NULL; `is_public` Boolean NOT NULL default `True`; `created_at`, `updated_at`, `last_refreshed_at` | `oauth_cimd_enabled` bật thì authorization server fetch client metadata document của deployment; tắt thì auto-discovery đăng ký qua DCR |
| `mcp_connection_config` | `id` PK; `mcp_server_id` FK CASCADE nullable (NULL cho config template); `user_email` String NOT NULL default `''` (rỗng cho config admin và template); `config` **EncryptedJson** NOT NULL default `{}`; timestamps | Index `ix_mcp_connection_config_user_email`, `ix_mcp_connection_config_server_user`. `config` chứa refresh/access token, headers, header_template, api_token, client_id/secret, registration token/URI |
| `mcp_server_user_preference` | PK (`user_id` CASCADE, `mcp_server_id` CASCADE); `enabled_in_chat`, `enabled_in_craft` Boolean NOT NULL default `True` | |
| `mcp_server__user` | PK (`mcp_server_id` CASCADE, `user_id` CASCADE) | |
| `mcp_server__user_group` | PK (`mcp_server_id`, `user_group_id`) | **Không** có CASCADE |

Vòng FK: `mcp_server.admin_connection_config_id` → `mcp_connection_config.id`, và `mcp_connection_config.mcp_server_id` → `mcp_server.id`. Hai chiều đều nullable nên không khóa chết insert.

---

## 12. Bot Slack và Discord

| Bảng | Cột | Ghi chú |
|---|---|---|
| `slack_bot` | `id` PK; `name` String; `enabled` Boolean default `True`; `bot_token`, `app_token` **EncryptedString UNIQUE**; `user_token` **EncryptedString** nullable | UNIQUE trên cột mã hóa: so sánh trên **bytes ciphertext** |
| `slack_channel_config` | `id` PK; `slack_bot_id` FK NOT NULL; `persona_id` FK nullable; `channel_config` JSONB NOT NULL (`ChannelConfig` TypedDict); `enable_auto_filters` Boolean NOT NULL default `False`; `is_default` Boolean NOT NULL server_default `false` | Trong **database** chỉ có partial unique `ix_slack_channel_config_slack_bot_id_default` (`slack_bot_id`,`is_default`) WHERE `is_default IS TRUE` (migration `eaa3b5593925`) → **tối đa một config mặc định mỗi bot**. `UniqueConstraint` cùng tên khai trong model **không được migration nào tạo** — xem §19 |
| `slack_channel_config__standard_answer_category` | PK (`slack_channel_config_id`, `standard_answer_category_id`) | |
| `standard_answer` | `id` PK; `keyword`, `answer` String; `active`, `match_regex`, `match_any_keywords` Boolean | Partial unique `unique_keyword_active` (`keyword`,`active`) WHERE `active = True` |
| `standard_answer_category` | `id` PK; `name` String UNIQUE | |
| `standard_answer__standard_answer_category` | PK (`standard_answer_id`, `standard_answer_category_id`) | |
| `chat_message__standard_answer` | PK (`chat_message_id` CASCADE, `standard_answer_id`) | |
| `discord_bot_config` | `id` String PK **server_default `'SINGLETON'`**; `bot_token` **EncryptedString** NOT NULL; `created_at` | CHECK `ck_discord_bot_config_singleton` (`id = 'SINGLETON'`) **có trong database** (migration `8b5ce697290e`) nhưng **model không khai lại** — một dòng mỗi tenant |
| `discord_guild_config` | `id` PK; `guild_id` BigInteger nullable **UNIQUE** (snowflake, NULL tới khi admin chạy `!register`); `guild_name` String(256); `registration_key` String UNIQUE NOT NULL (dạng `discord_<tenant_id>.<random>`); `registered_at`; `default_persona_id` FK SET NULL; `enabled` Boolean server_default `true` | |
| `discord_channel_config` | `id` PK; `guild_config_id` FK CASCADE NOT NULL; `channel_id` BigInteger NOT NULL; `channel_name` String NOT NULL; `channel_type` String(20) server_default `'text'`; `is_private` Boolean server_default `false`; `thread_only_mode` Boolean server_default `false`; `require_bot_invocation` Boolean server_default **`true`**; `persona_override_id` FK SET NULL; `enabled` Boolean server_default **`false`** | UNIQUE `uq_discord_channel_guild_channel` (`guild_config_id`,`channel_id`) |

`ChannelConfig` (TypedDict lưu trong JSONB): `channel_name`, `respond_tag_only`, `respond_to_bots`, `is_ephemeral`, `respond_member_group_list`, `answer_filters` (`well_answered_postfilter` / `questionmark_prefilter`), `follow_up_tags` (None = không follow up, list rỗng = follow up không tag), `show_continue_in_web_ui`, `disabled`.

---

## 13. Enterprise: group, quyền, permission sync, SCIM, usage

### 13.1. `user_group` và thành viên

| Bảng | Cột | Ghi chú |
|---|---|---|
| `user_group` | `id` PK; `name` String UNIQUE; `is_up_to_date` Boolean NOT NULL default `False`; `is_up_for_deletion` Boolean NOT NULL default `False`; `is_default` Boolean NOT NULL default `False` (group mặc định như "Basic", "Admins" không xóa được); `incognito_enabled` Boolean NOT NULL default `False`; `time_last_modified_by_user` | |
| `user__user_group` | PK (`user_group_id` FK, `user_id` FK CASCADE **nullable**); `is_curator` Boolean NOT NULL default `False`; `is_manager` Boolean NOT NULL server_default `false` | Index `ix_user__user_group_user_id` |
| `permission_grant` | `id` PK autoincrement; `group_id` FK CASCADE NOT NULL; `permission` Enum `Permission` (lưu *value*) NOT NULL; `grant_source` Enum `GrantSource` NOT NULL; `granted_by` FK SET NULL nullable; `granted_at` NOT NULL; `is_deleted` Boolean NOT NULL server_default `false` | UNIQUE `uq_permission_grant_group_permission` (`group_id`,`permission`). **Validator Python** chặn cấp trực tiếp permission thuộc `Permission.IMPLIED` |
| `user_group__connector_credential_pair` | PK (`user_group_id`, `cc_pair_id`, **`is_current`**); `role` Enum `ConnectorManageRole` NOT NULL | Ai **quản lý** được pair. `is_current=False` là trạng thái cũ |
| `user_group__cc_pair_data_access` | PK (`cc_pair_id` CASCADE, `user_group_id` CASCADE index) | Ai **đọc document** của pair. Pair `PRIVATE` → thành viên thấy mọi document; pair `SYNC_RESTRICTED` → chỉ thấy phần permission của nguồn cho phép. **Tách bạch với bảng trên** |
| `llm_provider__persona` | PK (`llm_provider_id` CASCADE, `persona_id` CASCADE) | **Không có dòng nào** cho một provider = provider đó mọi persona dùng được |
| `llm_provider__user_group` | PK (`llm_provider_id`, `user_group_id`) | |
| `credential__user_group` | PK (`credential_id`, `user_group_id`) | |
| `token_rate_limit__user_group` | PK (`rate_limit_id`, `user_group_id`) | |

### 13.2. `token_rate_limit`

| Cột | Kiểu | Ràng buộc |
|---|---|---|
| `id` | Integer | PK |
| `enabled` | Boolean | NOT NULL, default `True` |
| `token_budget` | Integer | nullable |
| `cost_budget_cents` | Numeric(18,6) | nullable — USD cents, 6 chữ số thập phân cho delta dưới-cent theo token |
| `period_hours` | Integer | NOT NULL |
| `scope` | Enum `TokenRateLimitScope` | `user`/`user_group`/`global` |
| `created_at` | DateTime(tz) | |

CHECK `ck_token_rate_limit_budget_set`: `token_budget IS NOT NULL OR cost_budget_cents IS NOT NULL` — phía NULL bỏ qua cổng của nó, nhưng phải có ít nhất một.

### 13.3. Permission sync

| Bảng | Cột | Khóa/Index |
|---|---|---|
| `doc_permission_sync_attempt` | `id` PK; `connector_credential_pair_id` FK NOT NULL; `status` Enum `PermissionSyncStatus` (index); `total_docs_synced`, `docs_with_permission_errors`; `error_message`, `full_exception_trace`; `time_created` index, `time_started`, `time_finished`; `heartbeat_at` (**lease worker gia hạn; reaper fail attempt khi hết hạn**); `last_progress_at`; `celery_task_id` | **`uq_doc_permission_sync_attempt_open_cc_pair` UNIQUE (`cc_pair_id`) WHERE status IN ('NOT_STARTED','IN_PROGRESS')** — chính là *lock* doc permission sync. Thêm `ix_permission_sync_attempt_latest_for_cc_pair`, `ix_permission_sync_attempt_status_time` |
| `external_group_permission_sync_attempt` | Như trên nhưng `connector_credential_pair_id` **nullable** (cho group sync toàn cục); counts là `total_users_processed`, `total_groups_processed`, `total_group_memberships_synced` | `uq_group_sync_attempt_open_cc_pair` UNIQUE WHERE status mở — lock group sync |
| `user__external_user_group_id` | PK (`user_id` FK, `external_user_group_id` String, `cc_pair_id` FK); `stale` Boolean NOT NULL default `False` | Index `ix_user_external_group_cc_pair_stale`, `ix_user_external_group_stale`. `stale` đánh dấu group cần dọn cuối lần group sync |
| `public_external_user_group` | PK (`external_user_group_id` String, `cc_pair_id` FK CASCADE); `stale` Boolean | Ví dụ folder Google Drive "Anyone with the link" / "Anyone in the domain" |

### 13.4. SCIM

| Bảng | Cột | Ràng buộc |
|---|---|---|
| `scim_token` | `id` PK; `name` NOT NULL; `hashed_token` String(64) UNIQUE NOT NULL (SHA256); `token_display` NOT NULL (4 ký tự cuối); `created_by_id` FK CASCADE NOT NULL; `is_active` Boolean server_default `true`; `created_at`; `last_used_at` | |
| `scim_user_mapping` | `id` PK; `external_id` String UNIQUE index nullable; `user_id` FK CASCADE **UNIQUE** NOT NULL; `scim_username`; `department`; `manager`; `given_name`; `family_name`; `scim_emails_json` Text; timestamps | Index unique `uq_scim_user_mapping_scim_username_lower` trên `lower(scim_username)` |
| `scim_group_mapping` | `id` PK; `external_id` String UNIQUE index; `user_group_id` FK CASCADE **UNIQUE** NOT NULL; timestamps | |

### 13.5. Usage và license

| Bảng | Cột | Ghi chú |
|---|---|---|
| `license` | `id` PK; `license_data` Text NOT NULL; timestamps | **Singleton** bằng `Index("idx_license_singleton", text("(true)"), unique=True)` — unique index trên hằng số |
| `tenant_usage` | `id` PK; `window_start` DateTime(tz) NOT NULL index; `llm_cost_cents` Float; `chunks_indexed`, `api_calls`, `non_streaming_api_calls` Integer; `updated_at` | UNIQUE `uq_tenant_usage_window` (`window_start`) — **tenant_id nằm trong tên schema** nên không cần cột |
| `user_usage` | xem dưới | Tên vật lý `user_usage` là **tên cũ giữ lại cho tương thích deployment**; bảng giờ gộp cả usage của hệ thống |
| `usage_reports` | `id` PK; `report_name` FK `file_record.file_id`; `requestor_user_id` FK CASCADE nullable (None = tự sinh); `time_created`; `period_from`, `period_to` | File zip báo cáo nằm trong FileStore |

`user_usage` — rollup LLM theo ngày:

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | Integer PK | |
| `user_id` | FK SET NULL nullable | **Không `index=True`**: `uq_user_usage_dims` (dẫn đầu bằng user_id) đã phủ tra cứu theo user |
| `actor_kind` | Enum `UsageActorKind` NOT NULL default `USER` | `USER`/`SYSTEM` |
| `system_attribution` | Enum `SystemUsageAttribution` nullable | `ATTRIBUTED`/`UNATTRIBUTED` |
| `window_start` | DateTime(tz) NOT NULL index | |
| `model`, `flow` | String NOT NULL | |
| `provider` | String NOT NULL default `''` | `''` chứ không NULL: unique index khử trùng được trên PostgreSQL < 15 |
| `incognito` | Boolean NOT NULL default `False` | Chi tiêu của lượt incognito **tích lũy ở dòng riêng** để báo cáo gán nhãn được; bộ đọc budget cộng cả hai |
| `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_creation_tokens` | BigInteger NOT NULL | |
| `cost_cents` | Numeric(18,6) NOT NULL | |

CHECK `ck_user_usage_actor` ép: `USER` → `system_attribution IS NULL`; `SYSTEM` → `user_id IS NULL`, `system_attribution` ∈ (ATTRIBUTED, UNATTRIBUTED), và `incognito = false`.

Hai partial unique index cho hai khóa tích lũy: `uq_user_usage_dims` (user_id, window_start, model, flow, provider, incognito) WHERE `actor_kind='USER'`; `uq_system_usage_dims` (system_attribution, window_start, model, flow, provider) WHERE `actor_kind='SYSTEM'`.

---

## 14. Build / Craft và external app

### 14.1. `build_session`

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK CASCADE, nullable | |
| `name` | String | nullable | |
| `status` | Enum `BuildSessionStatus` | NOT NULL, default `ACTIVE` | `initializing`/`active`/`idle`/`failed` |
| `created_at`, `last_activity_at` | DateTime(tz) | NOT NULL | |
| `nextjs_port` | Integer | nullable | |
| `sharing_scope` | **String** (không Enum) | NOT NULL, default `PRIVATE`, server_default `private` | `private`/`public_org` |
| `origin` | Enum `SessionOrigin` | NOT NULL, default `INTERACTIVE` | Phân biệt session do user mở với session do executor scheduled-task / Slack bot tạo. Sidebar Craft lọc `origin == INTERACTIVE` |
| `opencode_session_id` | String | nullable | Điền lười ở message đầu |
| `agent_provider`, `agent_model` | String | nullable | |
| `skills_hash`, `mcp_config_hash` | String(64) | nullable | |

Index, gồm một partial unique đáng chú ý:

- `ix_build_session_user_origin_created` (`user_id`, `origin`, `created_at` DESC)
- `ix_build_session_status`
- **`uq_build_session_nextjs_port` UNIQUE (`user_id`, `nextjs_port`) WHERE `nextjs_port IS NOT NULL`** — *đặt chỗ cổng bền vững*: cấp phát retry khi va chạm thay vì tin vào quét ở tầng ứng dụng. Scope theo user vì cổng chỉ va chạm trong sandbox của một user.

### 14.2. `sandbox`

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | FK CASCADE, NOT NULL, **UNIQUE** | Một sandbox mỗi user |
| `container_id` | String | nullable | |
| `status` | Enum `SandboxStatus` | NOT NULL, default `PROVISIONING` | `provisioning`/`running`/`sleeping`/`terminated`/`failed` |
| `created_at` | DateTime(tz) | NOT NULL | |
| `last_heartbeat` | DateTime(tz) | nullable | |
| `skills_hash`, `mcp_config_hash` | String(64) | nullable | |
| `encrypted_pat` | **EncryptedString** | nullable | |
| `provisioning_attempt_number` | Integer | NOT NULL, default `0` | Tăng dưới lock đặt chỗ mỗi lần một attempt provisioning được phép. **Mọi lần ghi status nêu rõ attempt của nó và chỉ áp dụng khi dòng còn giữ số đó**, nên attempt cũ không ghi đè kết quả attempt mới |
| `provisioning_started_at` | DateTime(tz) | nullable | Dòng `PROVISIONING` đã commit mà attempt cũ hơn thời gian chờ có giới hạn của manager thì coi là chết và có thể bị tiếp quản. **Chẩn đoán lỗi nằm ở log**, không ở đây |

### 14.3. `artifact`, `snapshot`, `build_message`

| Bảng | Cột | Index |
|---|---|---|
| `artifact` | `id` UUID PK; `session_id` FK CASCADE NOT NULL; `type` Enum `ArtifactType` NOT NULL (14 giá trị); `path` String NOT NULL (tương đối `outputs/`); `name` NOT NULL; `turn_index` Integer nullable; `size_bytes` BigInteger nullable; `source_revision` String nullable (**định danh metadata từ inventory sandbox, không phải content hash**); `viewed_revision` Integer nullable; `version` Integer NOT NULL server_default `1`; `deleted` Boolean NOT NULL server_default `false` (**giữ dòng để card cũ xám đi thay vì 404**); `archive_file_id` String nullable (dành sẵn, NULL tới khi có archive); timestamps | `ix_artifact_session_created`; `ix_artifact_type`; **`uq_artifact_session_path` UNIQUE (`session_id`,`path`)** — khóa upsert, sửa file thì update tại chỗ |
| `snapshot` | `id` UUID PK; `session_id` FK CASCADE NOT NULL; `storage_path` String NOT NULL; `size_bytes` BigInteger NOT NULL default `0`; `created_at` | `ix_snapshot_session_created` |
| `build_message` | `id` UUID PK; `session_id` FK CASCADE NOT NULL; `turn_index` Integer NOT NULL; `type` Enum `MessageType` NOT NULL; `message_metadata` **JSONB NOT NULL**; `created_at` | `ix_build_message_session_turn` (`session_id`,`turn_index`,`created_at`) |

`build_message` lưu **toàn bộ dữ liệu message trong `message_metadata`** (gói event thô từ sandbox): `user_message`, `agent_message` (gộp từ chunk), `agent_thought` (gộp từ chunk), `tool_call_progress` (chỉ `completed`), `agent_plan_update` (upsert, chỉ bản mới nhất).

### 14.4. `action_approval` và `action_receipt`

`action_approval` — một yêu cầu bị gate do agent khởi tạo, và quyết định của nó.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `approval_id` | UUID PK | |
| `session_id` | FK `build_session.id` CASCADE NOT NULL | |
| `actions` | JSONB NOT NULL | **List không rỗng** các dict hình `MatchedAction`, sắp xếp policy nghiêm nhất trước; `actions[0]` là cái quyết định việc gating |
| `app_name` | String NOT NULL | |
| `payload` | JSONB NOT NULL | |
| `created_at` | DateTime(tz) NOT NULL | |
| `decision` | Enum `ApprovalDecision` nullable | **NULL = đang chờ** (hoặc mồ côi do proxy crash) |
| `decided_at` | DateTime(tz) nullable | |
| `decided_via` | Enum `ApprovalDecidedVia` nullable | `USER`/`PRE_APPROVAL`/`SESSION_GRANT` |
| `gated_app_id` | FK `gated_app.id` **SET NULL** nullable | Xóa target thì về NULL, dòng đã quyết định **ở lại làm audit record** |

`action_receipt` — ghi nhận một hành động ra ngoài mà session đã thực hiện. Ghi `PENDING` **trước khi** thực thi, chốt `CONFIRMED`/`FAILED` theo response, quét thành `UNKNOWN` khi mồ côi. **Chỉ dòng `CONFIRMED` mới được trình ra làm bằng chứng.**

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | UUID PK | |
| `session_id` | FK CASCADE NOT NULL | |
| `gated_app_id` | FK SET NULL nullable | |
| `approval_id` | FK `action_approval.approval_id` SET NULL nullable | |
| `action_type` | String NOT NULL | Ví dụ `slack.messages.write` hoặc tên tool MCP |
| `effect` | String NOT NULL | Kind read/write chụp lúc ghi, để dòng **tự chứa** kể cả khi catalog phân loại lại sau |
| `destination` | String NOT NULL | Ví dụ `#exec-team` |
| `link` | String nullable | |
| `operation_key` | String nullable | Khóa gộp để luồng nhiều request của provider (upload Slack trải nhiều request) **gộp thành một receipt** |
| `status` | Enum `ReceiptStatus` NOT NULL, server_default **`ReceiptStatus.PENDING.name`** | Comment nêu rõ: non-native enum lưu **NAME**, nên default phải khớp NAME |
| `created_at` | DateTime(tz) NOT NULL | |

Partial unique `uq_action_receipt_session_operation` (`session_id`,`operation_key`) WHERE `operation_key IS NOT NULL` — khóa NULL vẫn là dòng độc lập.

### 14.5. `scheduled_task` và `scheduled_task_run`

| Bảng | Cột | Index |
|---|---|---|
| `scheduled_task` | `id` UUID PK; `user_id` FK CASCADE NOT NULL; `name` NOT NULL; `prompt` Text NOT NULL; `cron_expression` String NOT NULL (**cron 5 trường chuẩn**; cả ba chế độ editor đều compile về chuỗi này); `editor_mode` String NOT NULL (chỉ là gợi ý UI, cron mới là nguồn sự thật); `status` Enum `ScheduledTaskStatus` NOT NULL default `ACTIVE`; `next_run_at` DateTime(tz) nullable (**trường duy nhất dispatcher đọc**; NULL khi paused; tính lại mỗi lần fire và mỗi lần sửa lịch; lưu UTC); `deleted` Boolean NOT NULL; timestamps | `ix_scheduled_task_dispatch` (`status`,`deleted`,`next_run_at`); `ix_scheduled_task_user_created` |
| `scheduled_task_run` | `id` UUID PK; `task_id` FK CASCADE NOT NULL; `session_id` FK `build_session.id` **SET NULL** nullable; `status` Enum `ScheduledTaskRunStatus` NOT NULL default `QUEUED`; `trigger_source` Enum `ScheduledTaskTriggerSource` NOT NULL; `skip_reason` String nullable; `error_class` String nullable; `error_detail` Text nullable; `started_at` NOT NULL; `finished_at` nullable; `summary` String nullable (**snippet ~120 ký tự** của message agent cuối) | `ix_scheduled_task_run_task_started`; `ix_scheduled_task_run_status`; `ix_scheduled_task_run_session` |

`session_id` nullable cho khoảng ngắn giữa lúc dispatcher insert dòng và lúc executor tạo `BuildSession`. SET NULL để dòng run **sống sót** khi session bị xóa.

### 14.6. `external_app` và `gated_app`

| Bảng | Cột | Ghi chú |
|---|---|---|
| `external_app` | `id` PK; `name` String NOT NULL; `app_type` Enum `ExternalAppType` NOT NULL default `CUSTOM`; `enabled` Boolean NOT NULL default `True`; `upstream_url_patterns` ARRAY(String) NOT NULL default `[]`; `auth_template` JSONB NOT NULL default `{}`; `organization_credentials` **EncryptedJson** NOT NULL default `{}`; timestamps | `app_type` **cố ý KHÔNG unique**: GitLab/Jira self-hosted có thể có nhiều instance, mỗi cái client_id + base URL riêng. Chống trùng cho trường hợp "một Slack" làm ở tầng UI. `CUSTOM` lưu URL **glob** (dịch sang regex lúc match); provider built-in lưu regex dùng thẳng |
| `external_app__skill` | PK (`external_app_id` CASCADE, `skill_id` CASCADE); UNIQUE `uq_external_app__skill_skill_id` (`skill_id`) | Unique trên `skill_id` giữ mô hình phụ thuộc ban đầu ở mức **nhiều nhất một external app cho mỗi skill** |
| `external_app_user_credential` | `id` PK; `external_app_id` FK CASCADE NOT NULL; `user_id` FK CASCADE NOT NULL index; `user_credentials` **EncryptedJson** NOT NULL; `granted_scopes` ARRAY(String) nullable; timestamps; UNIQUE (`external_app_id`,`user_id`) | **NULL `granted_scopes` nghĩa là không có ghi nhận đáng tin** về grant (provider không báo scope, hoặc tra cứu best-effort thất bại); list khác NULL là tập chính xác user đã cấp. **Bên tiêu thụ phải phân biệt hai trường hợp** |
| `gated_app` | `id` PK; `external_app_id` FK CASCADE nullable; `mcp_server_id` FK CASCADE nullable; `users_can_manage_policies` Boolean NOT NULL default `True` | **Danh tính đa hình cho một đích egress bị gate**. UNIQUE `uq_gated_app_external_app`, `uq_gated_app_mcp_server`; CHECK `ck_gated_app_single_target`: `num_nonnulls(external_app_id, mcp_server_id) = 1`. `kind` là **property Python** suy ra từ FK nào được điền, nên mismatch kind/cột là không thể biểu diễn |

Thiết kế `gated_app` giải quyết bài toán: pipeline approval (action policy, approval row, permission của scheduled task) tham chiếu **một id duy nhất** thay vì FK riêng cho từng catalog — thêm loại đích mới chỉ cần một cột nullable ở đây, không phải một cột ở **mọi** bảng tiêu thụ.

### 14.7. Action policy

| Bảng | Khóa | Cột |
|---|---|---|
| `workspace_action_policy` | `id` PK; UNIQUE `uq_workspace_action_policy` (`gated_app_id`, `action_id`) | `gated_app_id` FK CASCADE NOT NULL; `action_id` Text NOT NULL (catalog id với external app, tên tool với MCP server); `policy` Enum `ActionPolicy` NOT NULL; timestamps |
| `user_action_policy` | PK (`user_id` CASCADE, `gated_app_id` CASCADE, `action_id` Text) | `policy` Enum `ActionPolicy` NOT NULL; index `ix_user_action_policy_gated_app` |
| `scheduled_task_enabled_app` | PK (`scheduled_task_id` CASCADE, `gated_app_id` CASCADE) | **Không có dòng = chặn mọi action của app đó** |
| `scheduled_task_action_policy` | PK (`scheduled_task_id` CASCADE, `gated_app_id` CASCADE, `action_id` Text) | `policy` Enum `ActionPolicy` NOT NULL; index `ix_scheduled_task_action_policy_gated_app`. **Action vắng mặt = cần approval** |

`workspace_action_policy` là **sparse**: chỉ lưu action admin đã set; action thiếu dùng default của catalog provider, còn tool MCP mặc định `ASK`.

`ActionPolicy`: `ALWAYS` (tự duyệt), `ASK` (hỏi trong session), `DENY` (chặn thẳng).

---

## 15. Hệ thống và hạ tầng

### 15.1. Key-value và cache

| Bảng | Cột | Ghi chú |
|---|---|---|
| `key_value_store` | `key` String PK; `value` JSONB nullable; `encrypted_value` **EncryptedJson** nullable, **`deferred=True`** | `encrypted_value` là **legacy, không ghi nữa**. Người đọc duy nhất là fallback của `load()` cho dòng ghi trước khi bỏ cờ encrypt, khi `value` còn null. Đã lên lịch drop ở release sau; `deferred` để **không bao giờ bị SELECT eager**, chính điều đó làm việc drop an toàn |
| `encrypted_key_value_store` | `key` String PK; `value` **EncryptedJson** NOT NULL | Bí mật ở mức instance. **Postgres-only, không bao giờ cache**, để secret không lọt vào Redis |
| `cache_store` | `key` String PK; `value` **LargeBinary** nullable; `expires_at` DateTime(tz) nullable | Backend của `PostgresCacheBackend`, thay Redis khi `CACHE_BACKEND=postgres` (deploy NO_VECTOR_DB). **Cố ý tách khỏi `KVStore`**: lưu bytes thô (khớp ngữ nghĩa Redis) thay vì JSONB, có TTL, chứa dữ liệu ephemeral (token, stop signal, trạng thái lock) nên dọn dẹp có thể mạnh tay |

### 15.2. `security_settings`

Override runtime theo tenant cho các thiết lập bảo mật vốn lấy từ env. **Dòng singleton**: PK là Boolean ghim `true` qua CHECK. Mọi cột đều là override — `None` nghĩa là "dùng mặc định từ env".

| Cột | Kiểu |
|---|---|
| `id` | Boolean PK, default `True`, server_default `true()` |
| `user_directory_admin_only` | Boolean nullable |
| `track_external_idp_expiry` | Boolean nullable |
| `incognito_availability` | Enum `IncognitoAvailability` (lưu *value*) nullable — `off`/`everyone`/`groups` |
| `incognito_record_mode` | Enum `IncognitoRecordMode` (lưu *value*) nullable — mặc định về `usage_only` |
| `ssrf_protection_level` | Enum `SSRFProtectionLevel` (lưu *value*) nullable |
| `mask_credential_prefix` | Boolean nullable |
| `llm_custom_config_env_injection` | Boolean nullable |
| `allow_connector_group_restrictions` | Boolean nullable |
| `allow_connector_check_findings` | Boolean nullable |
| `valid_email_domains` | ARRAY(String) nullable |
| `password_min_length`, `password_max_length` | Integer nullable |
| `password_require_uppercase` / `_lowercase` / `_digit` / `_special_char` | Boolean nullable |
| `jwt_public_key_url`, `jwt_expected_audience`, `jwt_expected_issuer` | String nullable |

Hai CHECK:

- `ck_security_settings_singleton`: `id = true`
- `ck_security_settings_pw_length_range`: `min IS NULL OR max IS NULL OR min <= max` — comment nêu rõ **chỉ bắt được trường hợp cả hai cùng override**; trường hợp trộn với env phải enforce ở tầng ứng dụng.

### 15.3. File store

| Bảng | Cột | Ghi chú |
|---|---|---|
| `file_record` | `file_id` String **PK**; `display_name` nullable; `file_origin` Enum `FileOrigin`; `file_type` String default `text/plain`; `file_metadata` JSONB nullable; `bucket_name`, `object_key` String; `file_size` BigInteger nullable; `created_at`, `updated_at` | `file_size`: **NULL** = dòng ghi trước khi có cột (không biết size nếu không tra object store); **`-1`** = object nền đã xác nhận mất lúc tra cứu (**terminal** — listing ngừng probe lại). Index `ix_file_record_bucket_name_object_key`; partial index `ix_file_record_staged_connector_files` trên `created_at` WHERE `file_metadata ? 'staged_for_cc_pair_id'` |
| `file_content` | `file_id` FK `file_record.file_id` CASCADE **PK**; `lobj_oid` BigInteger NOT NULL; `file_size` BigInteger NOT NULL default `0` | Dùng **PostgreSQL Large Object** (`pg_largeobject`) khi `FILE_STORE_BACKEND=postgres`, để không cần S3/MinIO |

### 15.4. Hook

| Bảng | Cột | Ghi chú |
|---|---|---|
| `hook` | `id` PK; `name` NOT NULL; `hook_point` Enum `HookPoint` NOT NULL (`document_ingestion`/`document_push`/`query_processing`); `endpoint_url` Text nullable; `api_key` **EncryptedString** nullable; `is_reachable` Boolean nullable (**null = chưa validate bao giờ**, true = lần kiểm tra cuối đạt, false = lần cuối hỏng); `fail_strategy` Enum `HookFailStrategy` NOT NULL default `HARD`; `timeout_seconds` Float NOT NULL default `30.0`; `is_active` Boolean NOT NULL default `False`; `deleted` Boolean NOT NULL default `False`; `creator_id` FK SET NULL; timestamps | Partial unique `ix_hook_one_non_deleted_per_point` trên `hook_point` WHERE `deleted = False` → **tối đa một hook chưa xóa cho mỗi HookPoint** |
| `hook_execution_log` | `id` PK; `hook_id` FK CASCADE NOT NULL index; `is_success` Boolean NOT NULL default `False`; `error_message` Text; `status_code` Integer; `duration_ms` Integer; `created_at` NOT NULL index | Hiện **chỉ log thất bại**; cột `is_success` tồn tại sẵn để thêm log thành công sau này mà không phải đổi schema. Retention: task Celery hằng đêm xóa dòng quá 30 ngày |

`HookFailStrategy`: `HARD` (exception lan ra, pipeline abort) / `SOFT` (log lỗi, trả input gốc, pipeline tiếp tục).

### 15.5. Còn lại

| Bảng | Cột | Ghi chú |
|---|---|---|
| `task_queue_jobs` (model `TaskQueueState`) | `id` PK; `task_id` String (**hiện chỉ để đọc/chẩn đoán**); `task_name` String; `status` Enum `TaskStatus`; `start_time` DateTime(tz) nullable; `register_time` DateTime(tz) | Comment: **nếu task chết thì status chưa chắc được đánh `FAILED` đúng** |
| `background_error` | `id` PK; `message` String; `time_created`; `cc_pair_id` FK CASCADE nullable | Mục đích: giữ log quan trọng không mất khi rotate/restart container, và tạo dấu vết sự kiện tín hiệu cao |
| `milestone` | `id` UUID PK; `user_id` FK CASCADE nullable; `event_type` **String** (type hint là `MilestoneRecordType` nhưng cột là String thuần); `event_tracker` JSONB nullable; `time_created` | UNIQUE `uq_milestone_event_type` (`event_type`) — **một dòng cho mỗi loại sự kiện trên toàn tenant**. Bảng hiện không phục vụ tính năng nào |
| `code_interpreter_server` | `id` PK; `server_enabled` Boolean NOT NULL default `True` | |

---

## 16. Public schema (multi-tenant catalog)

Chín bảng `PublicBase`, nằm ở schema `public` (hoặc `POSTGRES_DEFAULT_SCHEMA` cho `oauth_provider_client` khi single-tenant). Chỉ truy cập qua `get_catalog_session()`.

| Bảng | Cột | Ghi chú |
|---|---|---|
| `user_tenant_mapping` | PK composite (`email`, `tenant_id`); `active` Boolean NOT NULL default `True` | `@validates("email")` hạ chữ thường |
| `user_tenant_mapping_oauth_account` | PK composite (`oauth_name` String(100), `account_id` String(320)); `email`, `tenant_id` String NOT NULL | Bản sao **subject** của `OAuthAccount`, **sống sót qua việc đổi email ở provider**. PK giữ một mapping cho mỗi subject. FK composite (`email`,`tenant_id`) → `public.user_tenant_mapping` với **ON UPDATE CASCADE** (theo rekey email) và ON DELETE CASCADE. Độ rộng cột mirror cột nguồn. Index `ix_user_tenant_mapping_oauth_account_mapping` |
| `available_tenant` | `tenant_id` String PK; `alembic_version` String NOT NULL; `date_created` DateTime NOT NULL; `shard_name` String nullable | Dòng **tồn tại tạm thời**, để user mới nhặt lúc đăng ký. Tenant pool bị **ràng vào shard nó được tạo trên đó** và không thể trao đi như thể nằm nơi khác |
| `tenant_schema_snapshot` | `id` PK; `shard_name`, `alembic_revision` String NOT NULL; `dump` Text NOT NULL; `created_at`; UNIQUE (`shard_name`,`alembic_revision`) | SQL dump schema template của một shard ở một head revision, do job rollout ghi. `apply_snapshot` dựng schema tenant từ nó thay vì replay chuỗi migration. **Giữ hai bản mới nhất mỗi shard** để image đang bị thay vẫn giữ snapshot của nó tới khi rollout xong |
| `tenant_anonymous_user_path` | `tenant_id` String PK; `anonymous_user_path` String NOT NULL **UNIQUE** | |
| `tenant_sso_domain` | PK composite (`tenant_id`, `domain`); `verified_at` DateTime(tz) nullable | Map email domain → workspace để trang login cloud định tuyến người **chưa có tài khoản**. Chiếu từ `allowed_email_domains` của từng provider (vốn per-tenant, nên không đọc được trước khi biết workspace). **Dòng chỉ định tuyến khi `verified_at` được set** — workspace phải chứng minh kiểm soát domain bằng bản ghi DNS TXT. Partial unique `uq_tenant_sso_domain_verified` (`domain`) WHERE `verified_at IS NOT NULL`: **chỉ một workspace giữ domain ở trạng thái VERIFIED**, nhưng nhiều workspace được giữ pending, nên kẻ chiếm chỗ không chặn được chủ thật đi verify |
| `tenant_invite_counter` | `tenant_id` String PK; `total_invites_sent` Integer NOT NULL default `0`; `updated_at` | Bộ đếm **trọn đời**, tăng atomic mỗi lần đặt chỗ invite, **không bao giờ giảm** — xóa người không hoàn lại quota, nên vòng lặp invite → remove → invite không lách được trần trial |
| `tenant_shard` | `tenant_id` String PK; `shard_name` String NOT NULL; `updated_at` | Tenant **không có dòng** ở đây nằm trên shard mặc định, nên bảng này rỗng cho tới khi thật sự di chuyển tenant — **không cần backfill** |
| `oauth_provider_client` | `client_id` String(64) PK; `client_metadata` JSONB NOT NULL; `created_at` NOT NULL; `last_used_at` NOT NULL **index** | Schema `public` khi multi-tenant, `POSTGRES_DEFAULT_SCHEMA` khi single-tenant |

---

## 17. Enum

### 17.1. Enum trong `onyx/db/enums.py`

| Enum | Giá trị |
|---|---|
| `AccountType` | STANDARD, BOT, EXT_PERM_USER, SERVICE_ACCOUNT, ANONYMOUS |
| `GrantSource` | USER, SCIM, SYSTEM |
| `IndexingStatus` | not_started, in_progress, success, canceled, interrupted, failed, completed_with_errors |
| `NotificationSeverity` | info, warning, error |
| `PermissionSyncStatus` | not_started, in_progress, success, canceled, failed, completed_with_errors |
| `CCPairRunKind` | indexing, doc_permission_sync, group_sync, pruning, checks |
| `CCPairRunStatusGroup` | running, succeeded, failed, canceled |
| `CCPairRunErrors` | unresolved, resolved, none |
| `PortAttemptStatus` | NOT_STARTED, IN_PROGRESS, SUCCESS, FAILED, CANCELED, PAUSED |
| `IndexingMode` | update, reindex |
| `ProcessingMode` | REGULAR, FILE_SYSTEM (deprecated), RAW_BINARY |
| `SyncType` | document_set, user_group, connector_deletion, pruning, external_permissions, external_group |
| `SyncStatus` | in_progress, success, failed, canceled |
| `MCPAuthenticationType` | NONE, API_TOKEN, OAUTH, PT_OAUTH |
| `MCPOAuthProviderMode` | AUTO_DISCOVERY, KNOWN_PROVIDER |
| `MCPTransport` | STDIO (chưa hỗ trợ), SSE (deprecated), STREAMABLE_HTTP |
| `MCPAuthenticationPerformer` | ADMIN, PER_USER |
| `MCPServerStatus` | CREATED, AWAITING_AUTH, FETCHING_TOOLS, CONNECTED, DISCONNECTED |
| `TaskStatus` | PENDING, STARTED, SUCCESS, FAILURE |
| `IndexModelStatus` | PAST, PRESENT, FUTURE |
| `IndexReclaimStatus` | PENDING, SOAKING, DELETING, RECLAIMED, BLOCKED |
| `ChatSessionSharedStatus` | public, private |
| `ConnectorCredentialPairStatus` | SCHEDULED, INITIAL_INDEXING, ACTIVE, PAUSED, DELETING, INVALID |
| `ConnectorManageRole` | editor, operator |
| `AccessType` | public, private, sync, sync_restricted |
| `EmbeddingPrecision` | bfloat16, float |
| `VectorQuantization` | none, scalar_7_bit, scalar_1_bit |
| `UserFileStatus` | PROCESSING, INDEXING, COMPLETED, SKIPPED, FAILED, CANCELED, DELETING |
| `ThemePreference` | light, dark, system |
| `SupportedLanguage` | en, es, pt, fr, de, ja, zh, ko, ar |
| `DefaultAppMode` | AUTO, CHAT, SEARCH |
| `SwitchoverType` | reindex, active_only, instant |
| `BuildSessionStatus` | initializing, active, idle, failed |
| `SessionOrigin` | INTERACTIVE, SCHEDULED, SLACK |
| `SharingScope` | private, public_org |
| `ApprovalDecision` | APPROVED, REJECTED, EXPIRED |
| `ApprovalDecidedVia` | USER, PRE_APPROVAL, SESSION_GRANT |
| `ScheduledTaskStatus` | ACTIVE, PAUSED |
| `ScheduledTaskRunStatus` | QUEUED, RUNNING, SUCCEEDED, FAILED, SKIPPED, AWAITING_APPROVAL |
| `ScheduledTaskTriggerSource` | SCHEDULED, MANUAL_RUN_NOW |
| `ScheduledTaskErrorClass` | task_missing, sandbox_wake_failed, executor_error, timeout, stuck, agent_exception, agent_permission_required |
| `ScheduledTaskSkipReason` | prior_in_flight, owner_craft_disabled |
| `SandboxStatus` | provisioning, running, sleeping, terminated, failed |
| `ExternalAppType` | GOOGLE_CALENDAR, GOOGLE_DRIVE, GMAIL, SLACK, LINEAR, GITHUB, HUBSPOT, NOTION, ZENDESK, CUSTOM |
| `ActionPolicy` | ALWAYS, ASK, DENY |
| `GatedAppKind` | EXTERNAL_APP, MCP_SERVER |
| `PatType` | USER, CRAFT |
| `ArtifactType` | web_app, pptx, docx, image, markdown, excel, pdf, csv, code, directory, audio, video, archive, file |
| `ReceiptStatus` | pending, confirmed, failed, unknown |
| `HierarchyNodeType` | folder, source, stub, shared_drive, my_drive, space, page, project, database, workspace, site, drive, channel, mailbox |
| `LLMModelFlowType` | chat, vision, contextual_rag, reasoning, chat_naming, search_selection, decision, craft |
| `HookPoint` | document_ingestion, document_push, query_processing |
| `HookFailStrategy` | hard, soft |
| `PersonaSharePermission` / `SkillSharePermission` | EDITOR, VIEWER |
| `PersonaAccessLevel` / `SkillAccessLevel` | OWNER, EDITOR, VIEWER |
| `PersonaSharingStatus` | PRIVATE, SHARED, PUBLIC |
| `SSOProviderType` | GOOGLE_OAUTH, OIDC, SAML |
| `SystemUsageAttribution` | ATTRIBUTED, UNATTRIBUTED |
| `UsageActorKind` | USER, SYSTEM |
| `IncognitoRecordMode` | full_history, usage_only |
| `CapabilityCheckTrigger` | manual, credential_created, cc_pair_validation, indexing_attempt, perm_sync_attempt, connector_config_update, scheduled |
| `CapabilityCheckRunStatus` | running, passed, failed, failed_to_run |
| `CapabilityReportRunStatus` | running, completed, failed_to_run |
| `SkillInstallationPolicy` | AVAILABLE, DEFAULT, REQUIRED |

`Permission` (27 giá trị, lưu *value*): basic, read:connectors, read:document_sets, read:agents, read:users, read:user_groups, read:search, read:chat, write:chat, read:admin, generate:image, use:llm_gateway, add:agents, manage:agents, manage:document_sets, manage:connectors, manage:llms, read:agent_analytics, manage:actions, manage:skills, read:query_history, manage:user_groups, create:user_api_keys, manage:service_account_api_keys, manage:bots, craft_sandbox, admin.

### 17.2. Enum từ module khác

| Enum | Nguồn | Giá trị |
|---|---|---|
| `UserRole` | `onyx/auth/schemas.py` | limited, basic, admin, curator, global_curator, slack_user, ext_perm_user |
| `MessageType` | `onyx/configs/constants.py` | system, user, assistant, summary, tool_call_response, user_reminder |
| `NotificationType` | như trên | reindex, persona_shared, two_day_trial_ending, release_notes, assistant_files_ready, feature_announcement, system_announcement, connector_repeated_errors, connector_invalid, license_expiry_warning, scheduled_task_failed, scheduled_task_awaiting_approval, scheduled_task_pre_approved_action, approval_requested |
| `SearchFeedbackType` | như trên | endorse, reject, hide, unhide |
| `TokenRateLimitScope` | như trên | user, user_group, global |
| `FileOrigin` | như trên | chat_upload, chat_image_gen, connector, connector_file_upload, connector_metadata, generated_report, indexing_checkpoint, indexing_staging, log_export, plaintext_cache, other, query_history_csv, sandbox_snapshot, skill_bundle, user_file |
| `MilestoneRecordType` | như trên | tenant_created, user_signed_up, visited_admin_page, created_connector, connector_succeeded, ran_query, user_message_sent, multiple_assistants, created_assistant, created_onyx_bot, requested_connector |
| `FederatedConnectorSource` | như trên | federated_slack |
| `InputType` | `onyx/connectors/models.py` | load_state, poll, event, slim_retrieval |
| `KGStage` | `onyx/kg/models.py` | extracted, normalized, failed, skipped, not_started, extracting, do_not_extract |
| `ReasoningEffort` | `onyx/llm/models.py` | auto, off, low, medium, high, xhigh |
| `SSRFProtectionLevel` | `onyx/server/security/models.py` | validate_all, validate_llm, allow_private_network, disabled |
| `IncognitoAvailability` | như trên | off, everyone, groups |
| `EmbeddingProvider` | `shared_configs/enums.py` | openai, cohere, voyage, google, litellm, azure, bifrost |
| `IndexAttemptStage` | `onyx/db/index_attempt_metrics_models.py` | 27 stage: CONNECTOR_VALIDATION, PERMISSION_VALIDATION, CHECKPOINT_LOAD, CONNECTOR_FETCH, HIERARCHY_UPSERT, DOC_BATCH_STORE, DOC_BATCH_ENQUEUE, QUEUE_WAIT, DOCPROCESSING_SETUP, BATCH_LOAD, DOC_DB_PREPARE, IMAGE_PROCESSING, CHUNKING, CONTEXTUAL_RAG, EMBEDDING, EMBEDDING_RATE_LIMIT_WAIT, EMBEDDING_PROVIDER_THROTTLE_WAIT, DOC_LOCK_ACQUIRE_WAIT, ENRICHMENT_PREP, VECTOR_DB_WRITE, POST_INDEX_DB_UPDATE, COORD_LOCK_ACQUIRE_WAIT, COORDINATION_UPDATE, FINALIZATION, GC_COLLECT, BATCH_UNACCOUNTED, BATCH_TOTAL |
| `DocumentSource` | `onyx/configs/constants.py` | Danh sách dài các nguồn connector (google_drive, confluence, slack, …) — không liệt kê hết ở đây |

---

## 18. Mẫu thiết kế đáng chú ý

Những điểm Onyx làm khác và đáng cân nhắc khi thiết kế schema của mình:

1. **Partial unique index thay cho lock ứng dụng.** `uq_doc_permission_sync_attempt_open_cc_pair`, `uq_group_sync_attempt_open_cc_pair`, `ix_port_attempt_active_unique` — mỗi cái cưỡng chế "tối đa một lần chạy đang mở cho mỗi cc_pair" **ở mức database**, không cần Redis fence. Đây là thay thế trực tiếp cho fencing bằng Redis, và code nói rõ như vậy ở `index_attempt` ("Database-based coordination fields (replacing Redis fencing)").

2. **Partial unique index để ép singleton/default.** `ix_embedding_model_present_unique`, `ix_one_default_per_llm_model_flow`, `ix_voice_provider_one_default_stt/tts`, `ix_hook_one_non_deleted_per_point`, `idx_license_singleton` (unique trên `text("(true)")`), `ck_security_settings_singleton` (PK Boolean ghim `true`). Năm kỹ thuật khác nhau cho cùng một ý.

3. **NULL là distinct trong PostgreSQL** → phải tách index theo scope. Thấy ở `port_attempt`, `port_orphan_candidate`, `credential_capability_report`. Và cách né khác: dùng `''` thay NULL (`user_usage.provider`, `model_cost_override.provider`) để unique key chạy trên PostgreSQL < 15 mà không cần `NULLS NOT DISTINCT`.

4. **Fencing bằng `run_id` / `attempt_number`.** `credential_capability_report.run_id` và `sandbox.provisioning_attempt_number`: mọi lần ghi terminal chỉ áp dụng khi dòng còn giữ đúng định danh attempt, nên attempt cũ không ghi đè kết quả attempt mới. Đây là generation fencing thực thi bằng cột, không phải bằng lock.

5. **SET NULL để dữ liệu audit sống lâu hơn thực thể.** `chat_feedback.chat_message_id`, `document_retrieval_feedback.chat_message_id`, `action_approval.gated_app_id`, `action_receipt.*`, `scheduled_task_run.session_id`, `persona.user_id`. Ngược hẳn với thói quen CASCADE mọi thứ.

6. **Cố ý không đặt FK.** `tool_call.tool_id` (để xóa được tool), `user_file.incognito_session_id` (dòng session bị xóa trước, file phải sống sót để sweep), `memory.conversation_id/message_id`, `sync_record.entity_id`, `search_doc.document_id`, `connector_credential_pair.creator_id`. Mỗi trường hợp đều có comment giải thích.

7. **Danh tính đa hình gom về một bảng** (`gated_app`) thay vì nhiều cột FK trên mọi bảng tiêu thụ, với CHECK `num_nonnulls(...) = 1` và `kind` là property suy ra. Cùng kỹ thuật ở `port_attempt`/`port_orphan_candidate` (cc_pair XOR user).

8. **FK composite tới cặp đã denormalize** (`user_skill_preference` → `skill(name, id)`) để enforce unique trên tên trong khi vẫn giữ tên luôn đúng.

9. **`is_current` nằm trong PRIMARY KEY** (`document_set__connector_credential_pair`, `user_group__connector_credential_pair`) để trạng thái cũ và mới cùng tồn tại trong thời gian propagate.

10. **Tách "ai quản lý" khỏi "ai đọc được"**: `user_group__connector_credential_pair` (có cột `role`) vs `user_group__cc_pair_data_access`.

11. **Aggregate thống kê ngay trong bảng** (`index_attempt_stage_metric` với Welford/Chan M2) thay vì lưu từng mẫu — đổi độ chính xác lấy dung lượng cố định cho mỗi (attempt, stage).

12. **Cột legacy được `deferred`** (`key_value_store.encrypted_value`) để drop migration an toàn sau khi mọi pod đã lên release mới.

13. **Cột tombstone giữ nullable** (`user.role`) để rollback thuần-code vẫn chạy.

14. **Event SQLAlchemy làm nghiệp vụ**: `before_insert`/`before_update` trên `User` thu hồi alias email khỏi `prior_emails` của user khác. Logic bảo mật nằm ở tầng ORM, **không ở database** — truy vấn/ghi thẳng SQL sẽ bỏ qua nó.

---

## 19. Giới hạn và điểm cần lưu ý

- **Chưa chạy migration, chưa dump database thật, chưa benchmark, chưa EXPLAIN.** Tài liệu dựng từ đọc `models.py` + enums + đối chiếu migration.

- **Model ORM không luôn bằng schema thật.** Ví dụ đã xác nhận: UNIQUE `ix_notification_user_type_data` tồn tại trong migration `8405ca81cc83` nhưng model chỉ ghi chú bằng comment. Ngược lại, `kg_relationship.source_document` khai `nullable=True` nhưng nằm trong `PrimaryKeyConstraint`, nên database sẽ ép NOT NULL. Khi cần DDL chính xác, đọc migration chứ không đọc model.

- **`slack_channel_config`: model và schema thật lệch nhau.** Model khai `UniqueConstraint("slack_bot_id","is_default", name="uq_slack_channel_config_slack_bot_id_default")` **cộng** một `Index` cùng cặp cột với `postgresql_where=(is_default is True)`. Trong database (migration `eaa3b5593925`) chỉ tồn tại **một** đối tượng: index `ix_slack_channel_config_slack_bot_id_default`, UNIQUE, `postgresql_where=sa.text("is_default IS TRUE")`. Hai hệ quả: (a) `UniqueConstraint` của model không có trong schema — và nếu có thì nó sẽ sai, vì sẽ chỉ cho phép **một** config *không* mặc định mỗi bot; (b) `postgresql_where=(is_default is True)` trong model là lỗi Python — `is` trên một `Column` trả về `False` chứ không phải biểu thức SQL (các chỗ khác trong cùng file viết đúng là `(is_default == True)  # noqa: E712`). Lỗi này vô hại vì index thật đến từ migration, nhưng khiến autogenerate không đáng tin cho bảng này.

- **`discord_bot_config`: constraint có thật nhưng model không khai.** Migration `8b5ce697290e` tạo `CheckConstraint("id = 'SINGLETON'", name="ck_discord_bot_config_singleton")`; model chỉ có `server_default='SINGLETON'` trên PK. Docstring của model mô tả đúng hành vi database, model thì không.

- **Ba bảng `fastapi-users`** (`user`, `oauth_account`, `accesstoken`) có cột nền do thư viện định nghĩa; phần liệt kê ở §3 lấy từ migration `6d387b3196c2` và `2666d766cb9b`, cộng các override trong `models.py`. Lưu ý tên vật lý là **`accesstoken`**, không phải `access_token`.

- **Enum lưu NAME hay VALUE là không thống nhất.** Mặc định SQLAlchemy lưu *tên member*; chỉ những cột khai `values_callable` mới lưu *giá trị*. Trong file này: `ReasoningEffort`, `IncognitoRecordMode`, `IncognitoAvailability`, `SSRFProtectionLevel`, `Permission` lưu value; phần lớn còn lại lưu name. `action_receipt.status` có comment nhắc đúng điều này. **Viết SQL thủ công phải kiểm tra từng cột.**

- **Nhiều cột được code đánh dấu deprecated nhưng vẫn còn**: `llm_provider.default_model_name`, `is_default_provider`, `is_default_vision_provider`, `default_vision_model`; `model_configuration.supports_image_input`; `index_attempt.total_failures_batch_level` ("unused, remove this column"); `user.role`; `key_value_store.encrypted_value`; `ProcessingMode.FILE_SYSTEM`. Đừng sao chép chúng như thể đang hoạt động.

- **Tài liệu này không mô tả vector store.** Chunk và embedding nằm ở Vespa/OpenSearch, ngoài PostgreSQL. `search_settings.index_name`, `vector_quantization` là cấu hình trỏ sang đó.

- Phân tích riêng cho chat/branch/stream/reload và các kết luận cần sửa so với khảo sát cũ: xem [onyx.md](./onyx.md) và [README.md](./README.md).
