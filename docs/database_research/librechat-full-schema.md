# LibreChat — toàn bộ database schema

Ngày ghi: 2026-10-27. Nguồn: `/home/lamhung/code/LibreChat`, commit `8d3da9bbb220a0a96be9330a2e1cbd385fb786d5` (2026-10-26), `package.json` version `v0.8.9-rc1`.

File gốc: [`packages/data-schemas/src/schema/`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/) (56 file schema, 6159 dòng, cộng 9 file spec), [`packages/data-schemas/src/models/`](/home/lamhung/code/LibreChat/packages/data-schemas/src/models/) (nơi đăng ký model và gắn plugin), [`packages/data-schemas/src/migrations/`](/home/lamhung/code/LibreChat/packages/data-schemas/src/migrations/), và các collection thao tác bằng raw driver trong [`packages/api/src/agents/checkpoints/`](/home/lamhung/code/LibreChat/packages/api/src/agents/checkpoints/) + [`packages/data-schemas/src/methods/`](/home/lamhung/code/LibreChat/packages/data-schemas/src/methods/).

LibreChat **không có trang docs schema công khai**; tài liệu này dựng từ source, cùng snapshot commit với [librechat.md](./librechat.md) (phân tích riêng cho bài toán chat/branch/stream/resume).

Phạm vi: mọi collection MongoDB mà ứng dụng tạo — 53 model Mongoose, 9 collection thao tác trực tiếp qua driver, cùng các collection legacy. Chưa chạy migration, chưa dump database thật, chưa benchmark.

---

## 1. Kiến trúc lưu trữ

### 1.1. MongoDB + Mongoose, không có migration framework

| Khía cạnh | LibreChat | Đối chiếu |
|---|---|---|
| Engine | **MongoDB** (`MONGO_URI`, mặc định `mongodb://127.0.0.1:27017/LibreChat`). Hỗ trợ Amazon DocumentDB như target hạng hai | Onyx: PostgreSQL. Open WebUI: SQLite/PostgreSQL |
| ORM/ODM | Mongoose, schema khai báo bằng TypeScript | Onyx: SQLAlchemy 2.0 + Alembic |
| Migration | **Không có cây migration tuần tự.** Schema là nguồn sự thật; index được build lúc `createModels()` chạy. Thư mục `migrations/` chỉ chứa vài tác vụ one-shot (drop index cũ, backfill) gọi tay | Onyx: 490 file Alembic. Open WebUI: Alembic + `migrate_history` |
| Timestamp | `{ timestamps: true }` → `createdAt`/`updatedAt` kiểu `Date`. Vài schema cố ý bỏ (`auditLog` không có `updatedAt`) | Onyx: `DateTime(timezone=True)`. Open WebUI: epoch `BigInteger` |
| Khóa ngoại | **Không có FK cấp database.** `ref: 'User'` chỉ là metadata cho `populate()`; không có cascade, không có ràng buộc tham chiếu | Onyx: FK + `ON DELETE` thật |

Hệ quả quan trọng của ô cuối: **mọi quan hệ trong tài liệu này là quan hệ logic**. Xóa cascade được viết tay ở tầng ứng dụng, và nhiều collection (`skillDeletion`, `triggerUserPurge`, `code_environment_tombstones`) tồn tại chính là để làm việc dọn dẹp mà FK sẽ làm giúp ở PostgreSQL.

Việc không có migration tuần tự còn có một hệ quả vận hành: thay đổi index chỉ xảy ra khi process khởi động lại. [`models/index.ts:166-181`](/home/lamhung/code/LibreChat/packages/data-schemas/src/models/index.ts) gắn listener `'index'` cho mọi model vì **build index nền thất bại im lặng nếu không có listener** — ví dụ DocumentDB <5.0 từ chối `partialFilterExpression`, và khi đó unique constraint không được thực thi mà log không ghi gì.

### 1.2. Multi-tenancy bằng cột `tenantId` + plugin query

Khác hoàn toàn Onyx (schema-per-tenant). LibreChat dùng **một database, một collection, phân biệt bằng cột `tenantId: String`** cộng một Mongoose plugin tiêm filter.

[`models/plugins/tenantIsolation.ts:124-220`](/home/lamhung/code/LibreChat/packages/data-schemas/src/models/plugins/tenantIsolation.ts) đăng ký middleware `pre` cho 12 phép đọc/ghi (`find`, `findOne`, `distinct`, `findOneAndUpdate`, `findOneAndDelete`, `findOneAndReplace`, `updateOne`, `updateMany`, `deleteOne`, `deleteMany`, `countDocuments`, `replaceOne`), cho `aggregate` (unshift `$match` vào đầu pipeline), và cho `save`.

| Trạng thái context | Hành vi |
|---|---|
| Có `tenantId` | Tiêm vào mọi query filter |
| `tenantId === SYSTEM_TENANT_ID` (`'__SYSTEM__'`, [`config/tenantContext.ts:12`](/home/lamhung/code/LibreChat/packages/data-schemas/src/config/tenantContext.ts)) | **Bỏ qua** — thao tác cross-tenant tường minh |
| Không có + `TENANT_ISOLATION_STRICT=true` | **Throw** (fail-closed) |
| Không có + strict tắt | Cho qua (chế độ chuyển tiếp / chưa bật tenancy) |

Ngoài ra `updateGuard` chặn update/replace tự sửa `tenantId`; nếu update rỗng sau khi lọc thì nó ép `{ _id: { $in: [] } }` và tắt `upsert` thay vì để query chạy không điều kiện.

**43/53 model áp plugin này. 7 model cố ý không áp:**

| Model không isolation | Lý do đọc được từ code |
|---|---|
| `AuditLog` | Tự quản lý phân vùng bằng `chainKey`; entry platform-level **phải vắng** `tenantId` (không phải `null`) |
| `SystemGrant` | Như trên — query platform-level dùng `{ tenantId: { $exists: false } }` |
| `ResourceLock`, `OpenIDRefreshFlight`, `RefreshTokenBridge` | Hạ tầng; `RefreshTokenBridge` vẫn có cột `tenantId` trong unique key |
| `SkillSyncCredential` | Credential cấp deployment, không có cột `tenantId` |
| `SkillSyncStatus` | Có cột `tenantId` trong unique index nhưng không áp plugin |

Hai bảng `AuditLog` và `SystemGrant` có **validator cấm `tenantId: null`** ngay trong schema, với comment giải thích: `{ tenantId: { $exists: false } }` khớp field vắng mặt chứ **không** khớp `null`, nên một document lưu `null` sẽ không khớp cả truy vấn platform-level lẫn tenant-scoped — tức biến mất khỏi mọi đường đọc.

### 1.3. Di sản của việc bật tenancy sau khi đã chạy production

[`migrations/tenantIndexes.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/migrations/tenantIndexes.ts) liệt kê 13 collection có index unique cũ **phải drop** trước khi multi-tenancy chạy được, vì unique toàn cục chặn ghi cùng giá trị ở tenant khác:

| Collection | Index bị thay thế |
|---|---|
| `users` | `email_1`, `googleId_1`, `facebookId_1`, `openidId_1`, `openidId_1_tenantId_1`, `samlId_1`, `ldapId_1`, `githubId_1`, `discordId_1`, `appleId_1` |
| `roles` | `name_1` |
| `agents` | `id_1` |
| `conversations` | `conversationId_1`, `conversationId_1_user_1` |
| `messages` | `messageId_1`, `messageId_1_user_1` |
| `presets` | `presetId_1` |
| `agentcategories` | `value_1` |
| `accessroles` | `accessRoleId_1` |
| `conversationtags` | `tag_1_user_1` |
| `mcpservers` | `serverName_1` |
| `files` | `filename_1_conversationId_1_context_1` |
| `groups` | `idOnTheSource_1_source_1` |
| `skillsyncstatuses` | `provider_1_sourceId_1` |

Index không-unique được mở rộng thêm `tenantId` thì **không** nằm trong danh sách — comment nói rõ chúng vô hại, chỉ làm plan kém tối ưu hơn một chút.

### 1.4. Hai store ngoài MongoDB

| Store | Vai trò | Bằng chứng |
|---|---|---|
| **MeiliSearch** | Mirror tìm kiếm cho `conversations` (index `convos`, primary key `conversationId`) và `messages` (index `messages`, primary key `messageId`). Chỉ bật khi có `MEILI_HOST` + `MEILI_MASTER_KEY` | [`models/convo.ts:11-22`](/home/lamhung/code/LibreChat/packages/data-schemas/src/models/convo.ts), [`models/message.ts:9-18`](/home/lamhung/code/LibreChat/packages/data-schemas/src/models/message.ts) |
| **RAG API + vector DB** | `RAG_API_URL`; vector nằm ngoài MongoDB. `file.metadata.embeddedEntities` chỉ ghi namespace đã embed | `.env.example:843` |
| **Redis** | `REDIS_URI`, tùy chọn; cache/stream/job — xem [librechat.md](./librechat.md) | `.env.example:1361` |

Plugin `mongoMeili` tiêm field bookkeeping ẩn vào document: `_meiliIndex`, `_meiliIndexAttempted`, `_meiliIndexVersion`, `_meiliIndexSchemaVersion`, `_meiliCleanupVersion`. Chỉ `_meiliIndex` được khai trong `messageSchema` (`select: false`); số còn lại do plugin ghi lúc runtime. Cả hai schema có index `{ _meiliIndex: 1, isTemporary: 1, expiredAt: 1 }` phục vụ job đồng bộ.

Hai collection **loại trừ một nhánh khỏi index tìm kiếm** qua `excludeFromIndexPath`: conversation có `subagentThread` (thread con) và message có `subagentTask` không được đẩy lên Meili.

### 1.5. Tên collection

Mongoose suy tên collection bằng `pluralize(modelName)` viết thường. Các tên **đã xác nhận trong source** (xuất hiện trong `migrations/tenantIndexes.ts`, `migrations/mcpAuthorityIndexes.ts` hoặc [`packages/api/src/db/utils.ts:37-45`](/home/lamhung/code/LibreChat/packages/api/src/db/utils.ts)): `users`, `roles`, `agents`, `conversations`, `messages`, `presets`, `agentcategories`, `accessroles`, `conversationtags`, `mcpservers`, `files`, `groups`, `skillsyncstatuses`, `aclentries`, `promptgroups`, `assistants`, `prompts`, `sharedlinks`, `tokens`, `configs`, `projects`.

Một trường hợp khai tường minh: `ChatProject` → `'chatprojects'` ([`models/chatProject.ts:12`](/home/lamhung/code/LibreChat/packages/data-schemas/src/models/chatProject.ts)), vì pluralize mặc định sẽ cho ra tên khác. Các tên còn lại trong tài liệu này suy từ quy tắc pluralize, chưa đối chiếu được với source.

---

## 2. Danh mục đầy đủ

### 2.1. 53 model Mongoose

Đăng ký tại [`models/index.ts:56-170`](/home/lamhung/code/LibreChat/packages/data-schemas/src/models/index.ts). Cột **TI** = có áp `applyTenantIsolation`.

| # | Model | TI | Nhóm | Vai trò |
|---|---|---|---|---|
| 1 | `User` | ✔ | Auth | Tài khoản, OAuth id, 2FA, personalization, favorites |
| 2 | `Session` | ✔ | Auth | Refresh token đã hash, TTL theo `expiration` |
| 3 | `Token` | ✔ | Auth | Token dùng một lần: verify email, reset password, invite |
| 4 | `Passkey` | ✔ | Auth | WebAuthn credential |
| 5 | `RefreshTokenBridge` | ✘ | Auth | Cầu nối refresh token cũ→mới khi rotate |
| 6 | `OpenIDRefreshFlight` | ✘ | Auth | Chống refresh đồng thời ở nhiều replica |
| 7 | `AgentApiKey` | ✔ | Auth | API key cho agent, hash + prefix |
| 8 | `Balance` | ✔ | Billing | Credit, auto-refill, reservation |
| 9 | `Transaction` | ✔ | Billing | Sổ cái token/credit |
| 10 | `Conversation` | ✔ | Chat | Hội thoại + preset + toàn bộ máy móc event-actor |
| 11 | `Message` | ✔ | Chat | Message tree, content parts, subagent projection |
| 12 | `SubagentContent` | ✔ | Chat | Transcript thread con cắt mảnh, có commit record |
| 13 | `ToolCall` | ✔ | Chat | Kết quả tool tách khỏi message |
| 14 | `ToolApprovalGrant` | ✔ | Chat | Ghi nhớ "luôn cho phép tool X" theo generation |
| 15 | `ConversationTag` | ✔ | Chat | Bookmark |
| 16 | `SharedLink` | ✔ | Chat | Snapshot chia sẻ hội thoại + file snapshot |
| 17 | `ChatProject` | ✔ | Chat | Nhóm hội thoại + instruction + file dùng chung |
| 18 | `Preset` | ✔ | Chat | Cấu hình endpoint lưu sẵn |
| 19 | `Agent` | ✔ | Agent | Định nghĩa agent, tools, skills, edges, versions |
| 20 | `AgentCategory` | ✔ | Agent | Danh mục marketplace |
| 21 | `Assistant` | ✔ | Agent | Metadata OpenAI Assistants |
| 22 | `Action` | ✔ | Agent | OpenAPI action + OAuth cho agent/assistant |
| 23 | `MCPServer` | ✔ | Agent | Cấu hình MCP server do user tạo |
| 24 | `MemoryEntry` | ✔ | Agent | Memory key/value, phân vùng theo `agentId` |
| 25 | `CodeEnvironment` | ✔ | Agent | Sandbox code, lease cho mọi pha vòng đời |
| 26 | `Skill` | ✔ | Skill | SKILL.md + frontmatter |
| 27 | `SkillFile` | ✔ | Skill | File đính kèm skill |
| 28 | `SkillDeletion` | ✔ | Skill | Nhật ký xóa skill có retry |
| 29 | `SkillUploadIntent` | ✔ | Skill | Ý định upload, chống rò blob |
| 30 | `SkillSyncCredential` | ✘ | Skill | Token GitHub để sync skill |
| 31 | `SkillSyncStatus` | ✘ | Skill | Trạng thái + lock mỗi nguồn sync |
| 32 | `Prompt` | ✔ | Prompt | Một phiên bản prompt |
| 33 | `PromptGroup` | ✔ | Prompt | Nhóm prompt, trỏ `productionId`, mirror Langfuse |
| 34 | `File` | ✔ | File | Metadata file + provenance + vòng đời xóa |
| 35 | `ToolFavorite` | ✔ | UI | Favorite tool/agent |
| 36 | `Banner` | ✔ | UI | Banner/popup thông báo |
| 37 | `Role` | ✔ | Quyền | Role + ma trận permission |
| 38 | `AccessRole` | ✔ | Quyền | Vai trò ACL theo loại tài nguyên, `permBits` |
| 39 | `AclEntry` | ✔ | Quyền | Grant ACL principal→resource |
| 40 | `SystemGrant` | ✘ | Quyền | Capability cấp platform/tenant |
| 41 | `Group` | ✔ | Quyền | Nhóm user, local hoặc Entra |
| 42 | `Config` | ✔ | Quyền | Override cấu hình theo principal, có `priority` |
| 43 | `AuditLog` | ✘ | Quyền | Append-only, hash chain |
| 44 | `AgentTriggerDelivery` | ✔ | Trigger | Hàng đợi sự kiện bền vững, lease + batch + dead letter |
| 45 | `AgentTriggerLaneSequence` | ✔ | Trigger | Bộ cấp số thứ tự mỗi lane |
| 46 | `AgentTriggerUserPurge` | ✔ | Trigger | Hàng rào khi xóa tài khoản |
| 47 | `AgentQueuedTurn` | ✔ | Queue | Lượt chat xếp hàng, slot + lane + admission |
| 48 | `AgentQueuedTurnSequence` | ✔ | Queue | Bộ cấp số thứ tự cho queued turn |
| 49 | `Schedule` | ✔ | Schedule | Lịch chạy định kỳ |
| 50 | `ScheduleRun` | ✔ | Schedule | Một lần chạy, capacity slot |
| 51 | `Key` | ✔ | Hạ tầng | API key người dùng nhập |
| 52 | `PluginAuth` | ✔ | Hạ tầng | Credential plugin/tool |
| 53 | `ResourceLock` | ✘ | Hạ tầng | Lock phân tán chung |

### 2.2. 9 collection thao tác bằng raw driver

Không có Mongoose model; index tạo thủ công qua `createIndex`.

| Collection | Nguồn | Vai trò |
|---|---|---|
| `agent_checkpoints` | [`agents/checkpoints/config.ts:4`](/home/lamhung/code/LibreChat/packages/api/src/agents/checkpoints/config.ts) | Checkpoint LangGraph (`MongoDBSaver`) |
| `agent_checkpoint_writes` | cùng file, dòng 5 | Pending write của checkpoint |
| `agent_checkpoint_stores` | [`checkpoints/storage.ts:8`](/home/lamhung/code/LibreChat/packages/api/src/agents/checkpoints/storage.ts) | Descriptor: owner nào dùng store nào |
| `agent_checkpoint_deletions` | [`checkpoints/deletion.ts:28`](/home/lamhung/code/LibreChat/packages/api/src/agents/checkpoints/deletion.ts) | Ý định xóa bền vững, sống qua việc topology biến mất |
| `browser_setup_sessions` | [`methods/browserSetup.ts:69`](/home/lamhung/code/LibreChat/packages/data-schemas/src/methods/browserSetup.ts) | Phiên setup browser, TTL `deleteAfter` |
| `browser_setup_budget` | cùng file, dòng 70 | Singleton `_id: 'global'`, chặn cấp phát ẩn danh |
| `browser_setup_requests` | cùng file, dòng 71 | Singleton `_id: 'global'`, rate budget |
| `code_environment_tombstones` | [`methods/codeEnvironment.ts:16`](/home/lamhung/code/LibreChat/packages/data-schemas/src/methods/codeEnvironment.ts) | Bia mộ sandbox đã xóa |
| `mcp_authorization_fence_retries` | [`methods/mcpAuthorizationFenceRetry.ts:5`](/home/lamhung/code/LibreChat/packages/data-schemas/src/methods/mcpAuthorizationFenceRetry.ts) | Replay fence ủy quyền MCP |

Ngoài ra: `projects` là collection **legacy**, chỉ còn được `ensureRequiredCollectionsExist` tạo và một migration đọc; `conformances` chỉ dùng trong test harness tenancy ([`tenant/harness.ts:24`](/home/lamhung/code/LibreChat/packages/data-schemas/src/tenant/harness.ts)).

### 2.3. Schema khai nhưng không có model

`categoriesSchema` ([`schema/categories.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/categories.ts)) được export từ `schema/index.ts` nhưng **không có hàm `create…Model` nào dùng**. Nó khai hai unique index `{label, tenantId}` và `{value, tenantId}`. Vai trò của nó dường như đã bị `AgentCategory` thay thế.

---

## 3. Auth và người dùng

### 3.1. `users` — [`schema/user.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/user.ts)

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `name` | String | |
| `username` | String | `lowercase`, default `''` |
| `email` | String | `required`, `lowercase`, regex `/\S+@\S+\.\S+/`, `index: true` |
| `emailVerified` | Boolean | `required`, default `false` |
| `emailChangedAt` | Date | Đặt khi đổi email thành công; reset password dùng nó để **từ chối token legacy không mang địa chỉ** |
| `password` | String | `select: false`, `minlength: 8`, `maxlength: 128`, `trim` |
| `avatar` | String | |
| `provider` | String | `required`, default `'local'` |
| `role` | String | default `SystemRoles.USER` |
| `googleId`, `facebookId`, `openidId`, `samlId`, `ldapId`, `githubId`, `discordId`, `appleId` | String | 8 OAuth id, mỗi cái một partial unique index |
| `openidIssuer` | String | Đi kèm `openidId` trong unique key |
| `plugins` | Array | |
| `twoFactorEnabled` | Boolean | default `false` |
| `twoFactorEnrolledAt` | Date | default `null` |
| `totpSecret` | String | `select: false` |
| `backupCodes` | `[{codeHash, used, usedAt}]` | `select: false`, sub-schema `_id: false` |
| `pendingTotpSecret`, `pendingBackupCodes` | | `select: false` — pha enroll chưa xác nhận |
| `credentialsChangedAt` | Date | Access token phát hành trước mốc này **bị từ chối lúc verify JWT** |
| `twoFactorAcknowledgementNonceHash`, `twoFactorFinalizationNonceHash` | String | `select: false`, default `null` |
| `refreshToken` | `[{refreshToken}]` | **Mảng nhúng, song song với collection `sessions`** — xem §19 |
| `expiresAt` | Date | **`expires: 604800`** — TTL 7 ngày ở cấp MongoDB |
| `termsAccepted` | Boolean | default `false` |
| `termsAcceptedAt` | Date | default `null` |
| `termsAcceptedSource` | String | enum `['migration']` — chỉ đặt khi giá trị được backfill |
| `agentTriggerDeletionStartedAt` | Date | `select: false` |
| `subagentAdmissionFences` | `[{token, expiresAt}]` | `select: false`, `_id: false` |
| `personalization` | `{memories: Boolean, statefulCodeEnvironment: String}` | default `{}`, enum `STATEFUL_CODE_ENVIRONMENTS`, default `'user'` |
| `favorites` | `[{agentId, model, endpoint, spec}]` | mỗi field `maxlength: 256`, `_id: false` |
| `pinnedOrder` | `[String]` | `select: false` **có chủ ý**: mọi request auth đều load user document, để selected sẽ kéo theo hàng trăm KB trên đường không đọc tới nó |
| `skillStates` | `Map<String, Boolean>` | default map rỗng |
| `idOnTheSource` | String | `sparse` — khớp schema `TPrincipal` |
| `tenantId` | String | `index` |
| `nameTokens`, `emailTokens`, `usernameTokens` | `[String]` | **Do plugin `applySearchTokens` thêm**, `select: false`, bị strip khỏi `toJSON`/`toObject` |

**Index:**

| Index | Tính chất |
|---|---|
| `{email: 1, tenantId: 1}` | unique |
| `{role: 1, tenantId: 1}` | |
| `{idOnTheSource: 1, openidIssuer: 1, tenantId: 1}` | |
| `{tenantId: 1, 'favorites.agentId': 1}` | **tenant đứng trước có chủ ý** — multikey existence field ở vị trí dẫn đầu không seek được vào một tenant |
| `{openidId: 1, openidIssuer: 1, tenantId: 1}` | unique, partial `openidId: {$exists: true}` |
| `{<oauthField>: 1, tenantId: 1}` × 7 | unique, partial `{$exists: true}` mỗi field |
| `{tenantId: 1, <tokens>: 1}` và `{<tokens>: 1, tenantId: 1}` × 3 | Do plugin search-token sinh, **cả hai thứ tự khóa** |

Ba chi tiết đáng chú ý:

1. **`expiresAt` là TTL người dùng.** `createUser(data, balanceConfig, disableTTL = true)` chỉ đặt nó khi gọi với `disableTTL: false`. Nhưng `updateUser` mặc định `$unset: { expiresAt: '' }` ([`methods/user.ts:428`](/home/lamhung/code/LibreChat/packages/data-schemas/src/methods/user.ts)) — tức **bất kỳ cập nhật nào cũng gỡ TTL**, trừ khi truyền `preserveExpiresAt`. Đây là cơ chế "xác nhận tài khoản bằng cách chạm vào nó", không phải một cờ tường minh.
2. **Search token là format lưu trữ, không phải index tính toán lại được.** [`utils/search.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/utils/search.ts) nói rõ: đổi quy tắc tách token thì phải chạy lại backfill, nên các giới hạn (`MAX_SEARCH_TOKEN_LENGTH = 64`, `MAX_SEARCH_VALUE_LENGTH = 256`, `MAX_SEARCH_TOKENS = 32`, `MAX_SEARCH_QUERY_TOKENS = 16`) là hằng số chứ không phải cấu hình. Tìm kiếm là **prefix theo từ**, có anchor, không khớp giữa từ (`"ohn"` không ra `"John"`) — giá phải trả để query bị chặn bởi index.
3. Plugin search-token **không chạy với `bulkWrite`**. Comment trong [`plugins/searchTokens.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/models/plugins/searchTokens.ts) yêu cầu caller tự gọi `withSearchTokens`. Một đường ghi quên điều này sẽ làm user biến mất khỏi kết quả tìm kiếm mà không lỗi gì.

### 3.2. `sessions`, `tokens`, `passkeys`

| Collection | Trường | Index |
|---|---|---|
| `sessions` | `refreshTokenHash` (required), `expiration` (required, **`expires: 0`** → TTL), `user` (ObjectId→User, required), `tenantId` | `{user, refreshTokenHash}` unique |
| `tokens` | `userId` (ObjectId, ref `'user'` — **viết thường**), `email` (`lowercase` + `trim`), `type`, `scope`, `identifier`, `token` (required), `createdAt`, `expiresAt` (required), `metadata` (`Map<Mixed>`), `tenantId` | `{expiresAt}` TTL 0; `{scope}` unique sparse tên `unique_token_scope`; `{userId, type, identifier, tenantId}` |
| `passkeys` | `user` (ObjectId→User, index), `credentialId` (**unique**, không ghép tenant), `publicKey` (Buffer), `counter`, `transports [String]`, `deviceType` enum `['singleDevice','multiDevice']`, `backedUp`, `name` (required, `maxlength: 60`), `lastUsedAt`, `tenantId` | chỉ các index inline |

`token.email` có comment dài giải thích vì sao phải `trim` **và** `lowercase`: `findToken`/`deleteTokens` đều `.trim().toLowerCase()` trước khi query, nên đường ghi phải khớp cả hai — một lời mời gửi tới `User@Example.com` từng không bao giờ redeem được. Lưu ý `User.email` chỉ có `lowercase`, không `trim`.

`passkey.credentialId` là **unique toàn cục, không ghép `tenantId`** — khác với mọi unique key khác trong hệ. Hợp lý về mặt WebAuthn (credential ID vốn là duy nhất toàn cầu), nhưng nó là một ngoại lệ trong mẫu đặt index.

### 3.3. `refreshtokenbridges` và `openidrefreshflights`

Hai collection giải cùng một lớp bài toán: nhiều replica cùng refresh một token.

| Collection | Trường | Cơ chế |
|---|---|---|
| `refreshtokenbridges` | `oldRefreshTokenHash`, `encryptedNewRefreshToken`, `userId`, `tenantId`, `openidIssuer`, `version`, `createdAt`, `expiresAt` | Unique `{oldRefreshTokenHash, userId, tenantId}` + TTL `expiresAt`. Request đến với token cũ vẫn lấy được token mới trong cửa sổ TTL |
| `openidrefreshflights` | `key` (**unique**), `ownerId`, `status` enum `['pending','completed','failed','revoked']`, `encryptedResult`, `errorMessage`, `deliveryId`, `deliveryExpiresAt`, `revocationRequestedAt`, `createdAt`, `updatedAt`, `lockExpiresAt` (index), `expiresAt` | Unique `key` = lock; `lockExpiresAt` cho phép cướp lock đã hết hạn; TTL `expiresAt` |

Cả hai **không** áp tenant isolation; `refreshtokenbridges` vẫn mang `tenantId` trong unique key, `openidrefreshflights` thì không có cột đó.

### 3.4. `agentapikeys`

`userId` (ObjectId→User), `name` (`maxlength: 100`), `keyHash` (`select: false`, index), `keyPrefix` (index), `lastUsedAt`, `expiresAt`, `tenantId`. Index `{userId, name, tenantId}` (**không unique**) và `{expiresAt}` TTL 0.

Comment trên TTL nói thẳng điều đánh đổi: key hết hạn bị **xóa vĩnh viễn**, không soft-delete; cần audit trail thì phải bỏ index này và kiểm tra hạn ở tầng ứng dụng.

---

## 4. `conversations` — [`schema/convo.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/convo.ts)

493 dòng, là schema lớn nhất. Chia làm bốn lớp: định danh hội thoại, khối preset dùng chung, máy móc thread con / event-actor, và các trường phục vụ sidebar.

### 4.1. Định danh và nội dung

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `conversationId` | String | `required`, `index`, `meiliIndex` |
| `title` | String | default `'New Chat'`, `meiliIndex` |
| `titleSetByUser` | Boolean | |
| `titleRevision` | Number | |
| `user` | String | `index`, `meiliIndex`. **Là String, không phải ObjectId** |
| `messages` | `[ObjectId→Message]` | Mảng tham chiếu; song song với `message.conversationId` |
| `isTemporary` | Boolean | default `false` |
| `tags` | `[String]` | default `[]`, `meiliIndex` |
| `chatProjectId` | String | default `null`, `index` |
| `files` | `[String]` | |
| `agent_id` | String | Agent **hiện tại** (có thể đổi) |
| `initial_agent_id` | String | `select: false` — agent gốc, **bất biến**; Insights quy trách nhiệm theo field này và chỉ fallback sang `agent_id` cho dòng legacy |
| `expiredAt` | Date | TTL `expireAfterSeconds: 0` |
| `tenantId` | String | `index` |

### 4.2. Khối `conversationPreset` — [`schema/defaults.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/defaults.ts)

Spread vào **cả `conversations` và `presets`**, nên hai collection chia sẻ chính xác cùng một tập tham số: `endpoint` (required, default `null`), `endpointType`, `model`, `region`, `chatGptLabel`, `examples`, `modelLabel`, `promptPrefix`, `temperature`, `top_p`, `topP`, `topK`, `maxOutputTokens`, `maxTokens`, `presence_penalty`, `frequency_penalty`, `file_ids`, `resendImages` (**deprecated**), `promptCache`, `promptCacheTtl`, `thinking`, `thinkingBudget`, `thinkingLevel`, `effort`, `system`, `resendFiles`, `imageDetail`, `agent_id`, `codeApprovalMode`, `codeEnvironmentMode`, `codeWorkspaces`, `assistant_id`, `instructions`, `stop`, `isArchived` (default `false`), `iconURL`, `greeting`, `spec`, `tags`, `tools`, `maxContextTokens`, `max_tokens`, `useResponsesApi`, `web_search`, `url_context`, `disableStreaming`, `fileTokenLimit`, `reasoning_effort`, `reasoning_summary`, `reasoning_mode`, `reasoning_context`, `verbosity`.

`codeWorkspaces` là mảng `{environmentId, workspaceId, checkout, agentIds}` với `_id: false`.

Lưu ý `agent_id` xuất hiện **hai lần** trong `convoSchema`: một lần tường minh ở thân schema, một lần qua spread `conversationPreset`. Spread đứng trước khai báo tường minh nên khai báo sau thắng; cả hai đều là `{ type: String }` nên không có khác biệt hành vi, nhưng đây là trùng lặp thật trong source.

### 4.3. Code lane và workspace (đều `select: false`)

| Trường | Mục đích |
|---|---|
| `codeEnvironmentRevision` | Number |
| `toolApprovalAllows` | `[String]` — tên tool chủ hội thoại tự phê duyệt; chỉ server ghi, qua `addConvoToolApprovalAllows` |
| `laneGit` | `{branch, head, repo, pullRequest, seq}` — trạng thái git worker báo về |
| `laneGitSeq` | Bộ đếm phát `laneGit.seq`, **dùng chung mọi replica**, chặn báo cáo cũ ghi đè |
| `codeAttachmentEpoch` | Đếm số lần chủ sở hữu move/detach workspace. Báo cáo lane mang giá trị đọc được lúc tool tạo ra và **chỉ áp dụng khi còn khớp** — rời đi rồi quay lại không hồi sinh được báo cáo cũ |

### 4.4. Thread con

| Trường | Kiểu |
|---|---|
| `subagentThread` | `{rootConversationId, parentConversationId, parentMessageId, parentToolCallId, parentAgentId, subagentType, subagentKind: enum['agent','graph'], depth: min 1}`, `_id: false` |
| `subagentThreadLease` | `{token, taskId, expiresAt}`, `select: false` — lease tiếp tục chạy **dùng chung mọi API replica**, lưu trong Mongo |

`subagentThread` là nhánh bị loại khỏi index MeiliSearch.

### 4.5. Máy móc event-actor

Đây là phần chiếm quá nửa schema. Toàn bộ `select: false`.

| Trường | Nội dung |
|---|---|
| `agentEventBinding` | `{bindingId, sourceKeyId, actorId}`. Nguồn sự kiện đã xác thực địa chỉ actor con **qua binding mờ đục này**; nguồn không bao giờ tự cung cấp agent/thread đích |
| `agentEventActor` | Trạng thái actor đã commit: `generation` (min 1), `checkpoint {threadId, checkpointId, checkpointNs}`, `contextFingerprint {algorithm:'sha256', version, digest}`, `skillManifest [{id,name,version,contentDigest}]`, `discoveredToolNames [String]`, `summary {text, tokenCount, version}`, `contextMeta {calibrationRatio 0.5–5, encoding, fading…}`, `compactionSemanticIndex`, `previousCheckpoint`, `requiresColdStart` |
| `agentEventActorCleanup` | `[{threadId, checkpointId, checkpointNs}]` — bằng chứng invocation fail-closed |
| `agentEventActorReconciliations` | `[{invocationId, actionAdmitted, status, checkpoint, action, error, resolution, observedAt}]`, `status` ∈ 7 giá trị từ `invocation_pending` → `settled` |
| `agentEventActorEpoch` | Number — **tăng bởi mọi sự kiện đường legacy**, để một fork đang chuẩn bị không commit vượt qua một lần vô hiệu hóa mà riêng các head field không thể hiện được |
| `agentEventActorLegacyTurn` | `{token, startedAt}` — lượt legacy đang chạy. Chặn fork thực thi/commit cho tới khi lịch sử bền vững; **crash để lại field này, fail closed** |
| `agentEventActorSuspension` | `{suspension: Mixed, kind, appliedAction, handlingGenerationCreatedAt, actionId, jobCreatedAt, status, resumeAttemptId, outcome, closedAt, observedAt}` |

Mọi mảng đều có validator chặn trên: `MAX_AGENT_EVENT_ACTOR_SKILLS`, `MAX_AGENT_EVENT_ACTOR_DISCOVERED_TOOLS`, `MAX_COMPACTION_SEMANTIC_INDEX_ENTRIES`, và `maxlength` trên từng chuỗi.

`agentEventActorSuspension.suspension` giữ kiểu `Mixed` **có chủ ý**: evidence do SDK ký, cần giữ nguyên JSON có version để round-trip chính xác; các field host bên cạnh là bản mirror cung cấp predicate CAS có biên.

`compactionSemanticIndex` lưu `entries[]` với `type ∈ ['tool_intent','tool_outcome','activity_phase','reasoning_label']`, `status ∈ ['committed','pending']`, cùng `sourceMessageId` + `sourceContentIndex` + `revision` — tức là **chỉ mục ngữ nghĩa của lịch sử đã nén, trỏ ngược về message gốc**, có validator toàn cục `isCompactionSemanticIndexProjection`.

`contextMeta.fading` / `fadingTiers` đến từ [`schema/fading.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/fading.ts), dùng chung với `messageSchema` để **hai nơi lưu đúng cùng một hình dạng**: `{v: enum[1,2], budgetTokens: min 1, masked: Boolean}`, bản per-agent thêm `agentId`.

### 4.6. Sidebar, lưu trữ, chưa đọc

| Trường | Ghi chú |
|---|---|
| `pinned` | Boolean |
| `archivedAt` | Date — **vắng mặt trên hội thoại lưu trữ trước khi field này ra đời** và trên mọi hội thoại chưa lưu trữ, nên reader fallback về `createdAt` |
| `lastResponseAt` | Date |
| `lastResponseMessageId` | messageId bền vững của reply mà `lastResponseAt` trỏ tới |
| `lastResponseIsManual` | **Chỉ true cho marker chưa-đọc tổng hợp**; reply thật xóa cờ này |
| `isMarkedUnread` | Boolean |
| `lastSeenAt` | Date |

### 4.7. 22 index

| Index | Vai trò |
|---|---|
| `{expiredAt}` TTL 0 | Hội thoại tạm |
| `{createdAt, updatedAt}` | |
| `{conversationId, user, tenantId}` **unique** | Khóa logic thật |
| `{tenantId, isTemporary, createdAt desc, _id desc}` | Insights |
| `{tenantId, isTemporary, initial_agent_id, createdAt desc, _id desc}` | Insights theo agent gốc |
| `{tenantId, isTemporary, agent_id, createdAt desc, _id desc}` | Insights theo agent hiện tại (dòng legacy) |
| `{user, _id}` | |
| `{user, chatProjectId, updatedAt desc, _id desc}` / `{user, chatProjectId, createdAt desc, _id desc}` | Danh sách trong project |
| `{user, isArchived, archivedAt desc, createdAt desc, _id desc}` | Trang lưu trữ — khóa giữa mang nhóm legacy (thiếu `archivedAt`) |
| `{user, isArchived, updatedAt desc, _id desc}` | Sidebar, sort mặc định |
| `{user, isArchived, createdAt desc, updatedAt desc, _id desc}` | Sidebar, sort theo ngày tạo |
| `{user, isArchived, title, updatedAt, _id}` | Sidebar, sort theo tên |
| `{user, isArchived, endpoint, updatedAt desc, _id desc}` | **Facet endpoint** |
| `{user, pinned, updatedAt desc, _id desc}` | Mục ghim |
| `{user, updatedAt desc, _id desc}` | Danh sách mặc định + poll 30 giây |
| `{user, isTemporary, expiredAt}` | |
| `{user, 'subagentThread.parentConversationId'}` | Cascade xóa thread con |
| `{user, 'subagentThreadLease.expiresAt'}` | |
| `{'agentEventBinding.bindingId'}` **unique sparse**, tên `agent_event_binding_unique` | |
| `{'agentEventActorReconciliations.status', …observedAt}` sparse, tên `agent_event_actor_reconciliation_metrics` | |
| `{_meiliIndex, isTemporary, expiredAt}` | Đồng bộ Meili |

Hai comment trong source đáng chép lại vì chúng là bài học thiết kế index, không phải ghi chú vụn:

> **Facet endpoint:** thiếu `endpoint` trong khóa thì MongoDB phải fetch **mọi** document theo thứ tự danh sách của user chỉ để loại bỏ, nên một filter khớp ít dòng lại đọc cả danh sách. Có nó thì scan nằm trong index. Facet khoảng-ngày **không cần index riêng**: chúng chỉ là biên trên khóa sort mà các index trên đã dẫn đầu.

> **Vì sao cần `{user, updatedAt desc, _id desc}` riêng:** index compound chỉ cung cấp thứ tự sort khi các khóa đứng trước bị ghim bằng equality, mà hai index `updatedAt` kia ghim `chatProjectId` và `pinned`.

---

## 5. `messages` — [`schema/message.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/message.ts)

### 5.1. Trường cốt lõi

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `messageId` | String | `required`, `index`, `meiliIndex` |
| `conversationId` | String | `required`, `index`, `meiliIndex` |
| `user` | String | `required`, default `null`, `index`, `meiliIndex` |
| `parentMessageId` | String | **Không index riêng** — cây message dựa vào index `{conversationId, user, createdAt, _id}` |
| `model`, `endpoint` | String | |
| `conversationSignature`, `clientId`, `invocationId` | | Di sản Bing |
| `tokenCount`, `summaryTokenCount` | Number | |
| `sender` | String | `meiliIndex` |
| `text` | String | `meiliIndex` |
| `summary` | String | |
| `privateText` | String | `select: false` |
| `privacyRevision` | String | |
| `privateTextTokens` | `[String]` | `select: false` |
| `isCreatedByUser` | Boolean | `required`, default `false` |
| `isUserSubmitted` | Boolean | |
| `userSubmittedPaths` | `[String]` | |
| `userSubmittedMessageFieldPaths` | `[{path, field: enum['answer','decision_response','decision_reason']}]` | |
| `isTemporary`, `unfinished`, `error` | Boolean | default `false` |
| `finish_reason` | String | |
| `feedback` | `{rating: enum['thumbsUp','thumbsDown'], tag: Mixed, text}` | |
| `langfuseSampled`, `langfuseDestinationIds`, `langfuseRunId` | | Tracing |
| `_meiliIndex` | Boolean | `select: false`, default `false` |
| `files` | `[Mixed]` | |
| `content` | `[Mixed]` | **Content parts**, `meiliIndex` |
| `thread_id` | String | |
| `iconURL` | String | |
| `metadata` | Mixed | |
| `attachments` | `[Mixed]` | Có một khối khai báo chi tiết **bị comment out** ngay bên dưới |
| `contextMeta` | `{calibrationRatio, encoding, fading, fadingTiers}` | Dùng chung `fading.ts` với conversation |
| `manualSkills` | `[String]` | Skill user gọi tay bằng `$` — **chỉ metadata UI** |
| `alwaysAppliedSkills` | `[String]` | Skill tự prime vì `always-apply: true`. Lưu lúc chạy chứ không dựng lại lúc render, **vì `Skill.alwaysApply` có thể đổi** — admin tắt cờ sau này thì lịch sử vẫn phải hiển thị đúng cái đã chạy |
| `quotes` | `[String]` | Trích dẫn user chọn. Đã được merge vào text gửi model, **nên không nhân đôi vào `text` lưu trữ** |
| `reasoningOverride` | `{key: enum[4], value: Mixed}` | |
| `expiredAt` | Date | TTL 0 |
| `addedConvo` | Boolean | |
| `tenantId` | String | `index` |

### 5.2. Năm khối subagent (đều `select: false`)

| Trường | Nội dung |
|---|---|
| `subagentContent` | `{version: enum[1], throughSequence, deleted}` — con trỏ tới collection `subagentcontents` |
| `subagentTranscript` | `{taskId, mode: enum['append','replace'], messagesJson}` |
| `subagentActivityProjection` | `{taskId, version: enum[1,2], activityJson, truncated}` |
| `subagentTriggerProjection` | `{version: enum[1], eventType, sourceType, occurredAt, expectedActionToolName}` — định danh an toàn để hiển thị cho lượt con do sự kiện tạo ra |
| `subagentTask` | `{attemptKey, parentRunId, requestFingerprint, status: enum['running','completed','error','cancelled'], resultClaim {kind: enum['manual','wakeup'], claimId, claimedAt}, controlReceipts[]}` — **marker server-only để retry detached là at-most-once** |

`controlReceipts[]` là nhật ký điều khiển: `{invocationId, fingerprint, controlId, action: enum['steer','queue','interrupt','cancel','cancel_message'], status: enum['reserved','accepted','applied','rejected','failed'], createdAt, updatedAt, boundary: enum['preempt','tool','turn'], reason, message, messageTruncated}`.

Lưu ý: `subagentTranscript` và `subagentActivityProjection` lưu JSON **dưới dạng chuỗi** (`messagesJson`, `activityJson`), không phải document lồng nhau — tránh giới hạn độ sâu và giữ payload mờ đục với Mongoose.

### 5.3. Index

| Index | Vai trò |
|---|---|
| `{expiredAt}` TTL 0 | |
| `{createdAt}` | |
| `{messageId, user, tenantId}` **unique** | Khóa logic |
| `{tenantId, isTemporary, createdAt desc, _id desc}` | Insights |
| `{tenantId, isTemporary, isCreatedByUser, model, createdAt desc, _id desc}` | Insights theo model |
| `{tenantId, isTemporary, isCreatedByUser, user, createdAt desc, _id desc}` | Insights theo user |
| `{conversationId, user, createdAt, _id}` | **Đường đọc hội thoại chính** |
| `{user, conversationId, createdAt desc, _id desc}` tên `subagent_thread_latest_message` | Đọc task mới nhất theo batch cho thread con |
| `{user, 'subagentTask.parentRunId', 'subagentTask.status', updatedAt desc, _id desc}` tên `subagent_parent_run_status_updated`, partial `parentRunId: {$exists: true}` | |
| `{_meiliIndex, isTemporary, expiredAt}` | |

Comment trên index chính giải thích một quyết định ngược trực giác:

> `tenantId` **cố ý không nằm ở giữa**: deployment không bật tenant không phát predicate `tenantId` nào, và một lỗ hổng trong prefix sẽ đẩy sort về in-memory cho họ.

Đây là trường hợp mẫu thiết kế multi-tenant bằng cột va chạm với thực tế có cả deployment chưa bật tenancy — và họ chọn ưu tiên nhóm sau cho đường đọc nóng nhất.

---

## 6. Phụ trợ hội thoại

### 6.1. `subagentcontents` — [`models/subagentContent.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/models/subagentContent.ts)

Schema khai **trong file model**, không ở thư mục `schema/`. `versionKey: false`, `_id` là String do ứng dụng cấp.

| Trường | Kiểu |
|---|---|
| `_id` | String, required |
| `user`, `tenantId` | String |
| `parentConversationId`, `conversationId`, `taskId` | String, required |
| `revision`, `fragment`, `fragments`, `fromSequence`, `throughSequence` | Number, required |
| `digest` | String, required |
| `payload` | String |
| `expiredAt` | Date |

**`fragment = -1` là bản ghi commit, chỉ được publish sau khi mọi mảnh payload đã tồn tại.** Đây là commit protocol hai pha trên một collection: ghi các mảnh (`fragment ≥ 0`), rồi ghi bản ghi `-1` làm điểm nhìn thấy.

| Index | Tính chất |
|---|---|
| `{tenantId, user, conversationId, taskId, revision, fragment}` | **unique** |
| `{tenantId, user, parentConversationId, conversationId, taskId, throughSequence}` tên `subagent_content_sequence` | partial `fragment: -1` — **chỉ index bản ghi commit** |
| `{expiredAt}` | TTL 0 |

### 6.2. `toolcalls`

`conversationId`, `messageId`, `toolId` (cả ba required), `user` (ObjectId→User, required), `result` (Mixed), `attachments` (Mixed), `blockIndex`, `partIndex`, `tenantId`, `expiredAt`. Index: `{expiredAt}` TTL 0, `{messageId, user, tenantId}`, `{conversationId, user, tenantId}`.

`blockIndex`/`partIndex` định vị tool call trong mảng `content` của message — tức kết quả tool được **tách khỏi message** nhưng vẫn neo vào vị trí trong đó.

### 6.3. `toolapprovalgrants` — [`models/toolApprovalGrant.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/models/toolApprovalGrant.ts)

Cũng khai trong file model. `user`, `agentId`, `toolName` (required), `conversationId` (default `''`), `tenantId`, `binding`, `revocation`, `generation`, `approvedAgentGeneration`, `approvedToolGeneration`, `approvedRevocation`, `oauthEpoch` (default `null`).

| Index | Tính chất |
|---|---|
| `{user, tenantId, agentId, toolName, conversationId}` | **unique** |
| `{user, tenantId, binding, conversationId}` | |

`conversationId: default ''` thay vì `null` hay vắng mặt là một thủ thuật quen thuộc: MongoDB coi `null` và field-vắng-mặt là khác nhau trong unique index, nên dùng chuỗi rỗng làm giá trị "phạm vi toàn cục" giữ cho unique key luôn đầy đủ. (Onyx dùng đúng thủ thuật này với `''` để tương thích PostgreSQL <15 — xem [onyx-full-schema.md](./onyx-full-schema.md) §18.)

Ba cột generation (`generation`, `approvedAgentGeneration`, `approvedToolGeneration`) cộng `approvedRevocation` và `oauthEpoch` là **fencing nhiều chiều**: phê duyệt mất hiệu lực khi agent đổi, khi tool đổi, khi có revocation, hoặc khi OAuth epoch xoay.

### 6.4. `conversationtags`

`tag` (index), `user` (index), `description` (index), `count` (default 0), `position` (default 0, index), `tenantId`. Unique `{tag, user, tenantId}`.

### 6.5. `sharedlinks` — [`schema/share.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/share.ts)

| Trường | Ghi chú |
|---|---|
| `conversationId` | required |
| `title`, `user`, `shareId`, `targetMessageId` | đều `index` |
| `messages` | `[ObjectId→Message]` |
| `tenantId` | index |
| `expiredAt` | TTL 0 |
| `snapshotFiles` | Boolean |
| `fileSnapshots` | `[{file_id, source, storageKey, filepath, type, filename, bytes, width, height, model, llmDeliveryPath, previewRevision, sourceDispatchedAt, tenantId}]`, `_id: false` |

`fileSnapshots` là **ảnh chụp bất biến của metadata file**, cố ý không copy byte: route file theo share stream/preview được file mà **không hỏi ACL file sống của chủ sở hữu**. Đây là lời giải cho bài toán "link chia sẻ phải tiếp tục hoạt động sau khi quyền của chủ thay đổi" mà không nhân bản dữ liệu.

Index: `{expiredAt}` TTL 0; `{conversationId, user, targetMessageId, tenantId}`; `{user, conversationId}`; `{updatedAt desc}`.

Comment giải thích vì sao cần cả hai index đầu: filter "shared" trên sidebar hỏi câu ngược lại — *user này đã chia sẻ những hội thoại nào* — mà index kia dẫn đầu bằng `conversationId`, nên truy vấn theo user sẽ quét mọi link trong deployment.

### 6.6. `chatprojects`

`name` (required, `maxlength: 100`, index), `description` (`maxlength` theo `MAX_CHAT_PROJECT_DESCRIPTION_LENGTH_CEILING`), `instructions` (`MAX_CHAT_PROJECT_INSTRUCTIONS_LENGTH_CEILING`), `contextRevision` (default 0), `file_ids [String]`, `user` (String, required, index), `conversationCount` (default 0), `lastConversationAt` (index), `lastConversationId`, `tenantId`.

Index: `{user, name, _id}`, `{user, createdAt desc, _id desc}`, `{user, lastConversationAt desc, _id desc}`.

`conversationCount` và `lastConversationAt`/`lastConversationId` là **denormalize**: cập nhật ở tầng ứng dụng, không có trigger database nào giữ chúng đúng.

### 6.7. `presets`

`presetId` (required, index), `title` (default `'New Chat'`, `meiliIndex` — **nhưng `presets` không gắn plugin Meili**, nên cờ này vô hiệu), `user` (String, default `null`), `defaultPreset` (Boolean), `order` (Number), toàn bộ `conversationPreset`, `tenantId`. Unique `{presetId, tenantId}`.

Đáng chú ý: `defaultPreset` **không có partial unique index** nào đảm bảo mỗi user chỉ có một preset mặc định — khác với cách `scheduleRun.capacitySlot` hay `schedule.slot` được bảo vệ. Việc "chỉ một mặc định" nằm hoàn toàn ở tầng ứng dụng.

---

## 7. `files` — [`schema/file.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/file.ts)

### 7.1. Trường

| Trường | Ghi chú |
|---|---|
| `user` | ObjectId→User, required, index |
| `conversationId` | String, `ref: 'Conversation'`, index |
| `messageId` | String, index |
| `file_id` | String, required, index |
| `temp_file_id` | String |
| `bytes`, `filename`, `filepath` | required |
| `storageKey`, `storageRegion` | |
| `storageOperations` | `{provisioning: [String], deleting: String, deletionPending: Boolean}` |
| `object` | required, default `'file'` |
| `embedded` | Boolean |
| `embeddingOwnersTrackedAt` | Date, **`immutable: true`** |
| `embeddingOwnersComplete` | Boolean |
| `type` | required — MIME |
| `text` | String — nội dung trích xuất |
| `textFormat` | enum `['html','text']` |
| `status` | enum `['pending','ready','failed']`, index |
| `previewError` | `maxlength: 200` |
| `previewRevision` | String |
| `context`, `usage` (default 0), `source` (default `local`), `model`, `width`, `height` | |
| `metadata.runFile` | sub-schema `RunFileProvenance`, **`immutable: true`** |
| `metadata.codeEnvRef` / `codeEnvRefs` | Xem §7.3 |
| `metadata.sourceDispatchedAt` | Number — dấu thứ tự dispatch của writer cuối |
| `metadata.embeddedEntities` | `[String]` — namespace vector đã embed |
| `metadata.codeDestination`, `searchDestination`, `destinationChosen`, `routingMimeType` | |
| `metadata.workspaceImports` | Mixed — bản sao đặt trong workspace, khóa bằng digest mờ đục |
| `llmDeliveryPath` | enum `['provider','text','none']` |
| `expiresAt` | **`expires: 3600`** — TTL upload ngắn hạn do MongoDB quản |
| `expiredAt` | Hạn lưu trữ, **do code quét sau khi xóa storage thành công** |
| `deletionAttempts`, `deletionRetryAt` | Backoff khi sweep xóa thất bại |
| `tenantId` | index |

**`expiresAt` và `expiredAt` là hai thứ hoàn toàn khác nhau** và cùng tồn tại trên collection này — một cái TTL 1 giờ của MongoDB cho upload dở, một cái là hạn lưu trữ do application sweep xử lý sau khi xóa được byte ở storage. Đây là chỗ dễ đọc nhầm nhất trong toàn bộ schema LibreChat.

Comment trên `deletionRetryAt` nêu một nguyên tắc đáng mượn:

> Điểm giữ duy nhất của sweep: **một deadline, không bao giờ là một cờ**, để một bản ghi bị tái dùng cho nội dung khác có thể bị trì hoãn chứ không bị mắc kẹt.

### 7.2. Index

| Index | Tính chất |
|---|---|
| `{expiredAt}` | **không** phải TTL — chỉ để sweep quét |
| `{user, tenantId, context, _id desc}` tên `project_file_picker` | partial `embedded: true` |
| `{user, tenantId, context, _id desc}` tên `project_file_picker_search_destination` | partial `metadata.searchDestination: true` |
| `{createdAt, updatedAt}` | |
| `{filename, conversationId, context, tenantId}` | **unique**, partial `context: execute_code` |
| `{user, tenantId, conversationId, metadata.runFile.{runId,executionId,agentId,sourceFileId}}` tên `run_artifact_identity` | **unique**, partial `context: run_artifact` |

Hai index cùng khóa `{user, tenantId, context, _id}` nhưng khác `partialFilterExpression` là một mẫu đáng chú ý: cùng một hình dạng truy vấn, hai tập con tài liệu rời nhau, hai index hẹp thay vì một index rộng.

### 7.3. `codeEnvRef` — [`schema/codeEnvRef.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/codeEnvRef.ts)

`{kind: enum['skill','agent','user'], id, storage_session_id, file_id, version, executionProfile: enum['default','stateful'], executionRouteKey, provisionedAt, sandboxFilename}`, `_id: false`.

`codeEnvRefMapSchema` **chỉ là `Schema.Types.Mixed`**. Comment giải thích: route key có dạng `stateful:<deployment hash>`, tức khóa động chứa dấu chấm; `Mixed` giữ chúng như object thường, còn Mongoose `Map` sẽ buộc mọi reader document đã hydrate chuyển từ truy cập bằng ngoặc sang `.get()`. Field số ít (`codeEnvRef`) vẫn được validate đầy đủ bằng schema.

Cùng lý do được dùng lại cho `file.metadata.workspaceImports`.

---

## 8. Agent, assistant, action, MCP

### 8.1. `agents` — [`schema/agent.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/agent.ts)

| Trường | Ghi chú |
|---|---|
| `id` | String, required — **định danh nghiệp vụ, khác `_id`** |
| `name`, `description`, `instructions` | |
| `avatar` | Mixed |
| `provider`, `model` | required |
| `model_parameters` | Object |
| `artifacts` | String |
| `access_level` | Number |
| `recursion_limit` | Number |
| `tools` | `[String]` |
| `skills`, `skills_enabled`, `skill_authoring_enabled`, `skills_scope` (enum `SkillsScope`) | |
| `tool_kwargs` | `[Mixed]` |
| `actions` | `[String]` |
| `author` | ObjectId→User, required |
| `authorName` | String — denormalize |
| `hide_sequential_outputs`, `end_after_tools` | Boolean |
| `stateful_code_sessions` | Boolean |
| `stateful_code_environment` | enum `['user','agent-user','conversation']` |
| `code_environment_id`, `code_workspace_id`, `code_environment_ids` | |
| `repositoryInstructions` | enum `['prefer','defer','off']` |
| `instructionsPrompt` | `{source: enum['native'], groupId, selection: {type: enum['production','exact'], promptId}}` — **trỏ sang `promptgroups`** |
| `git_identity` | `{name, email}` |
| `agent_ids` | `[String]` — **`@deprecated`, dùng `edges`** |
| `edges` | `[Mixed]`, default `[]` |
| `conversation_starters` | `[String]` |
| `tool_resources` | Mixed, default `{}` |
| `versions` | `[Mixed]`, default `[]` — **lịch sử phiên bản nhúng ngay trong document** |
| `category` | default `'general'`, index |
| `support_contact` | Mixed |
| `is_promoted` | Boolean, default `false`, index |
| `mcpServerNames` | `[String]`, default `[]` — **denormalize từ `tools` để query được** |
| `tool_options` | Mixed — `defer_loading`, `allowed_callers`, `run_in_background`, `describe_intent` |
| `subagents` | Mixed |
| `memory_scope` | enum `['user','agent']` |
| `tenantId` | index |

Index: `{id, tenantId}` **unique**, `{mcpServerNames, tenantId}`, `{updatedAt desc, _id}`, `{tenantId, updatedAt desc, _id}`, `{createdAt desc, _id}`, `{tenantId, createdAt desc, _id}`, `{'edges.to'}`.

Comment trên cặp index `createdAt`: *"phục vụ cả quét mới nhất và cũ nhất; chiều cũ nhất đảo ngược toàn bộ key pattern"* — tức một index phục vụ hai chiều sort nhờ MongoDB đọc index ngược được, miễn là **đảo toàn bộ** chứ không đảo một phần.

`versions: [Mixed]` nhúng trong chính document agent đáng lưu ý khi so với Onyx: ở đó lịch sử là bảng riêng. Cách của LibreChat giữ atomic đọc/ghi nhưng để document lớn dần không có biên.

### 8.2. `agentcategories` và `assistants`

`agentcategories`: `value` (required, `trim`, `lowercase`, index), `label` (required), `description`, `order` (default 0, index), `isActive` (default true, index), `custom` (default false), `tenantId`. Unique `{value, tenantId}`, cộng `{isActive, order}` và `{order, label}`.

`assistants`: `user` (ObjectId→User, required), `assistant_id` (required, index), `endpoint`, `avatar` (Mixed), `conversation_starters` (default `[]`), `access_level`, `file_ids`, `actions`, `append_current_datetime` (default false), `tenantId`. Index duy nhất ngoài inline: `{tenantId, 'avatar.filepath'}` — **không có unique nào trên `assistant_id`**.

### 8.3. `actions`

`user` (ObjectId→User, required, index), `action_id` (required, index), `type` (default `'action_prototype'`), `settings` (Mixed), `agent_id` (index), `assistant_id` (index), `tenantId` (index), và `metadata` gồm `{api_key, auth, domain (required), privacy_policy_url, raw_spec, oauth_client_id, oauth_client_secret}`.

`auth` là sub-schema `_id: false`: `{authorization_type, custom_auth_header, type: enum['service_http','oauth','none'], authorization_content_type, authorization_url, client_url, scope, token_exchange_method: enum['default_post','basic_auth_header', null]}`.

`metadata.api_key` và `metadata.oauth_client_secret` **là String thường, không `select: false`** — mã hóa (nếu có) xảy ra ở tầng ứng dụng, không ở schema.

### 8.4. `mcpservers`

`serverName` (required, index), `normalizedServerName` (required), `config` (Mixed, required), `author` (ObjectId→User, required, index), `tenantId`.

Hook `pre('validate')` tự sinh `normalizedServerName = normalizeServerName(serverName)`. Index: `{serverName, tenantId}` unique; `{normalizedServerName, tenantId}` unique partial `$exists`; `{updatedAt desc, _id}`.

Cặp unique kép này là cách chặn hai tên khác nhau chuẩn hóa về cùng một tên — một dạng "unique theo dạng chuẩn hóa" mà PostgreSQL sẽ làm bằng expression index (so sánh: Open WebUI dùng `uq_user_email_lower` trên `lower(email)`).

Có một migration riêng [`migrations/mcpServerNames.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/migrations/mcpServerNames.ts) để backfill cột này, với error type riêng `MCPServerNameMigrationError`.

### 8.5. `memoryentries`

`userId` (ObjectId→User, required, index), `key` (required, validator `/^[a-z_]+$/`), `value` (String, required), `agentId` (**null/vắng = pool cá nhân dùng chung**), `tokenCount` (default 0), `updated_at` (default `Date.now`), `tenantId`. Index `{userId, agentId, key}` — **không unique**.

Hai điểm: `updated_at` dùng snake_case và tự quản (schema **không** bật `timestamps`), còn việc không có unique nghĩa là trùng `(userId, agentId, key)` được database cho phép; dedupe nằm ở tầng ứng dụng.

### 8.6. `codeenvironments` — [`schema/codeEnvironment.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/codeEnvironment.ts)

| Nhóm | Trường |
|---|---|
| Định danh | `environmentId` (required), `name` (required), `type` enum `['managed','attached']`, `baseURL` (required), `controlPlaneId` (required), `createdBy` (ObjectId→User, index), `ownerSlot` (Number, min 0) |
| Setup | `setupAttemptId`, `setupRequestHash`, `setupDiscardedAt` |
| Tham chiếu | `pendingAgentReferences: [{reservationId, expiresAt}]` |
| Xóa | `deletionStartedAt`, `deletionLeaseId`, `deletionLeaseExpiresAt`, `deletionCommittedAt` |
| Đăng ký | `registrationPendingAt`, `registrationLeaseId`, `registrationLeaseExpiresAt`, `registrationReconcileAfter` |
| Thu hồi | `revocationPendingAt`, `revocationAttempts`, `revocationLastError`, `revocationReconcileAfter`, `revocationLeaseId`, `revocationLeaseExpiresAt` |
| Worker | `workerId`, `revocationTokenEnv`, `workerPrincipal: {type: enum['deployment','tenant','user','role','group'], id}` |
| Cấu hình | `settings.permissions.{fileWrite, commandExecution}` enum `['allow','ask','deny']` |

Index: `{environmentId, tenantId}` unique; `{createdBy, ownerSlot, tenantId}` unique partial `ownerSlot: {$type: 'number'}`; `{setupAttemptId, tenantId}` unique partial `$type: 'string'`; `{updatedAt desc, _id}`.

**Ba pha vòng đời, mỗi pha một bộ lease riêng** (`*LeaseId` + `*LeaseExpiresAt` + `*ReconcileAfter`) là mẫu lặp lại: không chia sẻ lease giữa registration, revocation và deletion, vì chúng có thể chồng lấn và việc một pha cướp lease của pha khác sẽ mất tính đúng đắn.

`ownerSlot` dùng partial unique để **giới hạn số sandbox mỗi chủ sở hữu bằng database** — cùng kỹ thuật với `schedule.slot` và `scheduleRun.capacitySlot` (§12).

---

## 9. Skill

### 9.1. `skills` — [`schema/skill.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/skill.ts)

| Trường | Ràng buộc |
|---|---|
| `name` | required, index, `maxlength: 64`, pattern `/^[a-z0-9][a-z0-9-]*$/`, **cấm prefix `anthropic-`/`claude-`** và 9 từ khóa CLI (`help`, `clear`, `compact`, `model`, `exit`, `quit`, `settings`, `anthropic`, `claude`) |
| `displayTitle` | `maxlength: 128` — **chỉ cho UI, không gửi cho model, không dùng để trigger** |
| `description` | required, `maxlength: 1024` — field quyết định độ chính xác trigger |
| `body` | default `''`, `maxlength: 100_000` |
| `frontmatter` | Mixed, default `{}` |
| `disableModelInvocation` | default `false` — **không index**, lọc ở tầng ứng dụng sau `listSkillsByAccess` |
| `userInvocable` | default `true` |
| `allowedTools` | `[String]`, **`default: undefined` chứ không `[]`**, để phân biệt "tác giả không khai" với "tác giả khai rõ là không có" |
| `category` | default `''`, index |
| `author` | ObjectId→User, required, index |
| `authorName` | required |
| `version` | Number, default 1, min 1 |
| `source` | enum `['inline','github','notion']`, default `'inline'` |
| `sourceMetadata` | Mixed |
| `fileCount` | default 0 |
| `deletingAt` | **Ẩn ngay khi bắt đầu xóa; giữ lại tới khi dọn dẹp phụ thuộc xong** |
| `deletionNeedsJournal`, `deletionJournalAttemptAt` | |
| `alwaysApply` | default `false`, **index** — để `listAlwaysApplySkills` ở đầu mọi request là lookup có index chứ không quét frontmatter |
| `tenantId` | index |

Index: `{author, tenantId}`; `{category, updatedAt desc}`; `{updatedAt desc, _id}`; `{deletionNeedsJournal, deletionJournalAttemptAt, deletingAt}` sparse; `{name, author, tenantId}` **unique**; `{source, 'sourceMetadata.upstreamId', tenantId}`; `{source, 'sourceMetadata.sourceId', tenantId}`.

Lưu ý unique key là `(name, author, tenantId)` — **tên skill chỉ duy nhất trong phạm vi một tác giả**, không phải toàn tenant.

Danh sách tên cấm được comment yêu cầu **giữ đồng bộ thủ công** với `RESERVED_NAME_PREFIXES`/`RESERVED_NAME_WORDS` trong `methods/skill.ts` — hai bản sao của cùng một quy tắc, không có kiểm tra tự động.

### 9.2. `skillfiles`

`skillId` (ObjectId→Skill, required, index), `relativePath` (required, `maxlength: 500`, validator chặn đường dẫn tuyệt đối, `.`/`..`, ký tự ngoài `[a-zA-Z0-9._\-/]`, và **cấm `SKILL.md`**), `file_id` (required, index), `filename`, `filepath`, `storageKey`, `storageRegion`, `source` (required), `sourceMetadata` (Mixed), `mimeType` (required), `bytes` (required, min 0), `category` enum `['script','reference','asset','other']`, `isExecutable`, `author` (ObjectId→User), `tenantId`, `content`, `isBinary`, `codeEnvRef`, `codeEnvRefs`.

Unique `{skillId, relativePath}` — **không có `tenantId`**, vì `skillId` đã là ObjectId duy nhất toàn cục. Thêm `{skillId, category}`.

### 9.3. Ba collection vòng đời xóa/upload

| Collection | Trường | Index |
|---|---|---|
| `skilldeletions` | `skillId` (**unique**), `author`, `tenantId`, `startedAt` (required), `lastAttemptAt`, `completedAt`, `nextCheckAt`, `claimOwner`, `claimExpiresAt` | `{lastAttemptAt, startedAt, claimExpiresAt}`, `{completedAt, nextCheckAt}`, `{nextCheckAt}` |
| `skilluploadintents` | `skillId` (index), `fileId` (**unique**), `source`, `storageKey`, `author`, `tenantId`, `writerId`, `state` enum `['uploading','committing','committed','abandoned']`, `cleanupHoldOwner`, `cleanupRequestedAt`, `cleanedAt`, `nextCheckAt`, `lastCleanupAttemptAt`, `claimOwner`, `claimExpiresAt` | 6 index, trong đó `committed_cleanup_candidates` partial `{state: 'committed', cleanupRequestedAt: {$exists: true}}` |
| `skillsynccredentials` | `provider` enum `['github']`, `credentialKey` (`maxlength: 64`, pattern), `encryptedToken` (**`select: false`**), `tokenHash` (**`select: false`**), `createdBy`, `updatedBy` | `{provider, credentialKey}` **unique**. **Không có `tenantId`** |

`skilldeletions` và `skilluploadintents` tồn tại vì MongoDB không có FK cascade: chúng là **nhật ký công việc dọn dẹp có retry**, với claim lease (`claimOwner` + `claimExpiresAt`) và rotation (`lastAttemptAt`) để một dòng không drain được không làm đói các dòng sau.

Index `committed_cleanup_candidates` có comment nêu đúng lý do nó tồn tại: nhánh dọn `committed` **không được phép quét các upload đang sống khỏe mạnh chỉ để giữ thứ tự**.

### 9.4. `skillsyncstatuses`

`provider` enum `['github']` (index), `sourceId` (required, `maxlength: 128`, index), `tenantId`, `status` enum `['idle','running','succeeded','partial','failed','skipped']`, `credentialKey`, `owner`, `repo`, `ref`, `paths [String]`, `startedAt`, `finishedAt`, `lastSuccessAt`, `lastFailureAt`, `errorCode`, `errorMessage`, sáu bộ đếm (`syncedSkillCount`, `syncedFileCount`, `deletedSkillCount`, `deletedFileCount`, `skippedSkillCount`, `skippedFileCount`), hai mảng chi tiết (`skippedSkills`, `skippedFiles`), `lockOwner`, `lockExpiresAt` (index). Unique `{provider, sourceId, tenantId}`.

`skippedSkills[].path` và `skippedFiles[].skillPath` dùng `validate` kiểm tra `typeof === 'string'` **thay vì `required: true`**, với comment giải thích: skill mirror từ gốc repository có path rỗng, mà `required` từ chối chuỗi rỗng. Đây là bẫy Mongoose kinh điển và họ ghi lại nó ngay tại chỗ.

---

## 10. Prompt và UI

### 10.1. `prompts` và `promptgroups`

`prompts`: `groupId` (ObjectId→PromptGroup, required, index), `author` (ObjectId→User, required, index), `prompt` (String, required), `type` enum `['text','chat']` (required), `tenantId`. Index `{createdAt, updatedAt}`.

`promptgroups`:

| Trường | Ghi chú |
|---|---|
| `name` | required, index |
| `numberOfGenerations` | default 0 |
| `oneliner`, `category` (index) | |
| `productionId` | ObjectId→Prompt, **`required` có điều kiện**: chỉ bắt buộc khi `source` là `native` |
| `author` (ObjectId→User), `authorName` | required |
| `command` | index, validator `/^[a-z0-9-]+$/` hoặc rỗng, `maxlength: Constants.COMMANDS_MAX_LENGTH` |
| `source` | enum `PromptGroupSources`, default `native` — `native` hoặc `langfuse` |
| `sourcePromptName`, `sourceProjectId`, `sourceDestination` | **`required` có điều kiện**: bắt buộc khi `source === 'langfuse'` |
| `tenantId` | index |

Index: `{numberOfGenerations desc, updatedAt desc, _id}`; `{tenantId, sourceDestination, sourceProjectId, sourcePromptName}` **unique** partial `sourcePromptName: {$exists: true}`; và **bản không tenant** `{sourceDestination, sourceProjectId, sourcePromptName}` partial cùng điều kiện, cho đường sync chạy ở chế độ env (tenantId không đặt).

`required` dạng hàm theo `source` là cách dùng một collection cho hai loại provenance mà không tách bảng — tương đương một `CHECK (num_nonnulls(...) = 1)` trong PostgreSQL, nhưng **chỉ được Mongoose thực thi**, raw driver bỏ qua hoàn toàn.

Còn có [`migrations/promptGroupIndexes.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/migrations/promptGroupIndexes.ts) export `dropSupersededPromptGroupIndexes` cho index cũ.

### 10.2. `toolfavorites` và `banners`

`toolfavorites`: `user` (ObjectId→User, required, index), `itemType` enum `FAVORITE_ITEM_TYPES` (required), `itemId` (required, `maxlength: 256`), `tenantId`. Unique `{user, itemType, itemId}`.

Comment giải thích vì sao unique này **cố ý loại `tenantId`**: ObjectId của user là duy nhất toàn cục, nên bộ ba không thể va chạm hợp lệ giữa các tenant, và đọc theo tenant vẫn được index dẫn đầu bằng user phục vụ. Đây là ngoại lệ có lý lẽ rõ ràng giữa một schema mà mọi unique khác đều ghép `tenantId`.

`banners`: `bannerId` (required), `message` (required), `displayFrom` (required, default now), `displayTo`, `type` enum `['banner','popup']` default `banner`, `isPublic` default false, `persistable` default false, `tenantId`. **Không có index nào ngoài `tenantId` inline** — kể cả trên `bannerId`.

---

## 11. Quyền, cấu hình, audit

### 11.1. `roles`

`name` (required, index), `description` (default `''`), `permissions` (sub-schema `_id: false`), `tenantId`. Unique `{name, tenantId}`.

`rolePermissionsSchema` là ma trận hai tầng `PermissionTypes × Permissions`, mọi ô kiểu Boolean:

| PermissionType | Permissions |
|---|---|
| `BOOKMARKS`, `MULTI_CONVO`, `TEMPORARY_CHAT`, `RUN_CODE`, `WEB_SEARCH`, `MARKETPLACE`, `FILE_SEARCH`, `FILE_CITATIONS` | `USE` |
| `PROMPTS`, `AGENTS`, `REMOTE_AGENTS`, `SKILLS` | `USE`, `CREATE`, `SHARE`, `SHARE_PUBLIC` |
| `MEMORIES` | `USE`, `CREATE`, `UPDATE`, `READ`, `OPT_OUT` |
| `PEOPLE_PICKER` | `VIEW_USERS`, `VIEW_GROUPS`, `VIEW_ROLES` |
| `MCP_SERVERS` | `USE`, `CREATE`, `SHARE`, `SHARE_PUBLIC`, `CONFIGURE_OBO` |
| `SHARED_LINKS` | `CREATE`, `SHARE`, `SHARE_PUBLIC` |
| `SCHEDULES` | `USE`, `CREATE` |

Mọi ô là `{ type: Boolean }` **không default** — nghĩa là ba trạng thái: `true`, `false`, và vắng mặt (thừa kế / chưa cấu hình).

### 11.2. `accessroles` và `aclentries`

`accessroles`: `accessRoleId` (required, index), `name` (required), `description`, `resourceType` enum 9 giá trị (`agent`, `codeEnvironment`, `project`, `file`, `promptGroup`, `mcpServer`, `remoteAgent`, `skill`, `sharedLink`) default `agent`, `permBits` (Number, required), `tenantId`. Unique `{accessRoleId, tenantId}`.

`aclentries`:

| Trường | Ghi chú |
|---|---|
| `principalType` | enum `PrincipalType`, required |
| `principalId` | **Mixed** — ObjectId cho user/group, String cho role. `required` trừ khi `principalType === PUBLIC` |
| `principalModel` | enum `PrincipalModel`, cùng điều kiện required |
| `resourceType` | enum `ResourceType`, required |
| `resourceId` | ObjectId, required, index |
| `permBits` | Number, default 1, min 0, max `MAX_PERM_BITS`, validator `Number.isInteger` |
| `roleId` | ObjectId→AccessRole |
| `inheritedFrom` | ObjectId, sparse, index |
| `grantedBy` | ObjectId→User |
| `grantedAt` | default now |
| `expiredAt` | Date |
| `tenantId` | index |

Index: `{principalId, principalType, resourceType, resourceId, tenantId}`; `{resourceId, principalType, principalId, tenantId}`; `{principalId, permBits, resourceType, tenantId}`; `{principalType, resourceType, permBits, resourceId}` (**không tenant** — phục vụ `findPublicResourceIds`); `{expiredAt}` TTL 0.

**Không có unique nào trên `aclentries`.** Một principal có thể có nhiều entry cho cùng resource; quyền hiệu lực là hợp của `permBits`, không phải một dòng duy nhất.

### 11.3. `systemgrants`

`principalType` (enum, required), `principalId` (Mixed, required), `capability` (String, required, validator `isValidCapability`), `tenantId` (**validator cấm `null` và `''`**), `grantedBy`, `grantedAt`, `expiresAt` (**"dành cho TTL tương lai — chưa được thực thi"**).

Unique `{principalType, principalId, capability, tenantId}`, cộng `{capability, tenantId}` và `{principalType, capability, tenantId}`.

Comment trên schema nói rõ: **mọi ghi PHẢI qua `grantCapability`**, vì không có hook chuẩn hóa `principalId` (String → ObjectId cho USER/GROUP) ở cấp schema. `Model.create()` hay `save()` trực tiếp sẽ lưu sai kiểu và dòng đó không bao giờ khớp truy vấn.

### 11.4. `groups`

`name` (required, index), `description`, `email` (index), `avatar`, `memberIds [String]`, `source` enum `['local','entra']` default `local`, `idOnTheSource` (sparse, index, **`required` khi `source !== 'local'`**), `tenantId`. Cộng `nameTokens`/`emailTokens` do plugin search-token thêm.

Index: `{idOnTheSource, source, tenantId}` unique partial `$exists`; `{memberIds, tenantId}`; cộng 4 index search-token.

`memberIds` là mảng String (không ObjectId), và tư cách thành viên **nằm trên group**, không có collection membership riêng — nghĩa là số thành viên bị chặn bởi giới hạn 16 MB mỗi document.

### 11.5. `configs`

`principalType` (enum, required, index), `principalId` (String, `refPath: 'principalModel'`, required, index), `principalModel` (enum, required), `priority` (Number, required, index), `overrides` (Mixed, default `{}`), `tombstones [String]` (default `[]`), `isActive` (default true, index), `configVersion` (Number, default 0), `keyEncoding` (Number — **đặt một lần khi khóa của `overrides` đã được encode; document không có nó thì đọc nguyên văn**), `tenantId`.

Index: `{principalType, principalId, tenantId}` **unique** (1:1 principal–config mỗi tenant); `{principalType, principalId, isActive, tenantId}`; `{priority, isActive, tenantId}`.

`tombstones` là danh sách khóa bị **xóa tường minh** ở tầng này — cần thiết vì `overrides` là merge theo `priority`, và "không có khóa" khác với "khóa bị gỡ".

### 11.6. `auditlogs` — [`schema/auditLog.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/auditLog.ts)

Collection duy nhất trong hệ được thiết kế **append-only có bằng chứng chống sửa**.

| Trường | Ghi chú |
|---|---|
| `schemaVersion` | Number, required, `immutable` |
| `category`, `action`, `outcome`, `severity` | enum từ `types/admin`, required, `immutable` |
| `actor` | `{type: enum AUDIT_ACTOR_TYPES, id, name}` — mọi field `immutable` |
| `target` | `{type, id, name}` — `immutable` |
| `metadata` | Mixed, `immutable`. Comment: **không bao giờ lưu prompt thô, secret, hay output tool đầy đủ** |
| `context` | `{requestId, ip, userAgent, sessionId}`, `immutable` |
| `tenantId` | `immutable`, validator bắt buộc chuỗi không rỗng **hoặc vắng hoàn toàn** |
| `chainKey` | required, `immutable` — `'__platform__'` cho entry cấp platform |
| `seq` | Number, required, `immutable` |
| `prevHash`, `hash` | required, `immutable` — `GENESIS_HASH` = 64 số `0` |
| `createdAt` | **Do writer đặt tường minh, không phải `timestamps`**, để nó nằm trong phạm vi hash |

**Không có `updatedAt`** — comment nói thẳng: một timestamp thay đổi được sẽ hàm ý rằng sửa đổi là hợp lệ.

Bảy hook chặn mọi đường ghi không phải insert mới:

1. `pre(['updateOne','updateMany','findOneAndUpdate','findOneAndReplace','replaceOne'])` — chặn update cấp query
2. `pre(['deleteOne','deleteMany','findOneAndDelete'])` — chặn delete cấp query
3. `pre('deleteOne', {document: true, query: false})` — **bịt lối thoát** `Document.prototype.deleteOne()`
4. `pre('updateOne', {document: true, query: false})` — tương tự cho `Document.prototype.updateOne()`
5. `pre('save')` — chỉ cho qua khi `isNew`
6. `pre('bulkWrite')` — chặn hoàn toàn; `bulkWrite` đi thẳng raw driver, bỏ qua middleware, và insert hàng loạt cũng phá chuỗi hash
7. `pre('insertMany')` — chặn, vì nó có thể chèn dòng với `seq`/`prevHash`/`hash` do kẻ tấn công chọn

Index: `{chainKey, seq}` **unique** — comment gọi đây là *"cả khóa phân trang keyset lẫn lớp dự phòng toàn vẹn: các lần append đồng thời đua nhau giành `seq` tiếp theo, một bên thắng, bên thua retry — nên chuỗi không bao giờ phân nhánh"*. Cộng `{chainKey, createdAt desc, seq desc}`, `{chainKey, category, createdAt desc}`, `{chainKey, 'target.type', 'target.id', createdAt desc}`.

Lưu ý giới hạn tự thú trong comment: tamper-evidence **vượt ngoài các guard tầng ứng dụng** chỉ đến từ chuỗi hash; purge lưu trữ có đặc quyền dùng `Model.collection` và không bị các hook này chạm tới.

---

## 12. Hàng đợi, trigger, lịch

### 12.1. `agentqueuedturns` — [`schema/queuedTurn.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/queuedTurn.ts)

Lượt chat của user xếp hàng khi một generation đang chạy.

| Nhóm | Trường |
|---|---|
| Định danh | `user` (ObjectId, index), `tenantId`, `conversationId`, `agentId`, `parentMessageId`, `clientRequestId` (`maxlength: 128`), `fingerprint` (`minlength: 43, maxlength: 64`), `laneId` |
| Thứ tự / slot | `sequence` (min 1), `reservationWriterId`, `activeSlot` (0–99), `admissionSlot` (Boolean) |
| Trạng thái | `status` enum `['reserving','queued','claimed','admitted','cancelled','dead']` default `reserving`, `priority` (Boolean) |
| Nội dung | `text` (required, `maxlength: 32_768`), `files [fileRef]`, `quotes`, `manualSkills`, `codeApprovalMode`, `reasoningOverride` |
| Fencing | `expectedPredecessorCreatedAt`, `attempts`, `availableAt` (required) |
| Delivery | `deliveryKey`, `deliveryState` enum `['pending','publishing','published','retiring','retired']`, `scheduledAt` |
| Claim | `claimId`, `claimBy`, `claimUntil` |
| Admission | `admissionStartedAt`, `admissionId`, `admissionEffectivePredecessorCreatedAt`, `admissionLineagePredecessorId`, `admissionProtocolVersion` (enum `[2]`) |
| Reconcile | `reconciliationAvailableAt`, `reconciliationClaimId`, `reconciliationClaimBy`, `reconciliationClaimUntil`, `reconciliationAttempts` |
| Kết thúc | `terminalReceipt {outcome: enum['admitted','cancelled','dead'], settledAt, admissionId, admissionMode: enum['warm','ordinary'], generationId, generationCreatedAt, effectivePredecessorCreatedAt, lineagePredecessorId, rootPredecessor: enum[true], failure}` |

**Sáu unique index, mỗi cái thực thi một bất biến khác nhau:**

| Index | Partial filter | Bất biến |
|---|---|---|
| `{tenantId, user, conversationId, clientRequestId}` | — | Idempotency của create |
| `agent_queued_turn_sequence` | `sequence: {$exists: true}` | Số thứ tự không trùng |
| `agent_queued_turn_active_capacity` | `activeSlot: {$exists: true}` | Giới hạn số lượt hoạt động mỗi hội thoại |
| `agent_queued_turn_claim_lane` | `status: 'claimed'` | **Tối đa một lượt `claimed` mỗi lane** |
| `agent_queued_turn_admission_started_lane` | `admissionStartedAt: {$exists: true}` | Hàng rào xuyên phiên bản sau khi claim vượt ranh giới provider |
| `agent_queued_turn_admission_slot` | `admissionSlot: true` | Tối đa một admission mỗi lane |

Comment trên index thứ năm đáng chú ý: `admissionStartedAt` được **cả worker cũ và mới ghi**, và sống sót qua trạng thái cách ly `dead/ADMISSION_INDETERMINATE` của worker cũ — nên nó được chọn làm hàng rào, chứ không phải `status`.

Thêm 6 index không-unique phục vụ claim (`agent_queued_turn_claim`), danh sách active (`agent_queued_turn_active`), hết hạn claim, quét theo trạng thái, reconcile, và lịch chạy.

`agentqueuedturnsequences`: `_id` String do ứng dụng cấp, `user`, `tenantId`, `conversationId`, `laneId`, `value` (min 0), `reservationId` (`maxlength: 24`), `writerId`, `writerUntil`, `retiredAt`, `expiresAt`. Chỉ một index: `{expiresAt}` TTL 0.

### 12.2. `agenttriggerdeliveries` — [`schema/triggerDelivery.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/triggerDelivery.ts)

Hàng đợi sự kiện bền vững. 300 dòng, 10 trạng thái, 19 index.

`status` enum: `staging`, `capability_staging`, `batched`, `pending`, `capability_pending`, `leased`, `capability_leased`, `succeeded`, `capability_dead`, `dead`. Có **hai trục trạng thái song song** — trục thường và trục `capability_*` cho delivery cần worker có năng lực riêng, với bộ lease riêng (`capabilityStatus`, `capabilityLeaseBy`, `capabilityLeaseUntil`, `capabilityClaimToken`).

| Nhóm | Trường |
|---|---|
| Định danh | `deliveryKey` (**unique**), `fingerprint`, `orderingKey`, `laneSequence` (min 0; **0 dành riêng cho dòng staging nhìn thấy được trước khi cấp số**) |
| Payload | `envelope` (Mixed, required), `envelopeBytes`, `result` (Mixed) |
| Chủ sở hữu | `user` (ObjectId, index), `tenantId` |
| Lease | `leaseBy`, `leaseUntil`, `claimToken`, `producerLeaseUntil` (**`select: false`** — heartbeat riêng của process, không lộ cho consumer cũ) |
| Coalesce / batch | `coalesceKey`, `coalesceFrom`, `coalesceUntil`, `batchSize`, `batchBytes`, `batchMemberIds []`, `batchRootId`, `batchRootRequeueCount`, `batchMembersSettledAt` |
| Kết quả nền | `backgroundToolResult {status, output (maxlength hằng số), settledAt, resultClaim}`, `backgroundToolResultBatch {...}`, `backgroundToolResultErasedAt`, `backgroundToolResultDeletionPendingAt` — tất cả `select: false` |
| Xử lý | `handling {status: enum 5, conversationId, streamId, generationCreatedAt, startedAt, settledAt, error, action}`, `awaitTerminalHandling` |
| Actor | `actorReceipt`, `actorDetachedAction`, `actorDetachedActionHistory []`, `actorActionAdmittedAt`, `actorActionAdmissionId`, `actorActionAdmissionClosedAt` — đều `select: false` |
| Retry | `attempts`, `availableAt` (required), `claimAvailableAt`, `requeueCount`, `lastError`, `history [{attempt, outcome, at, workerId, error}]` |
| Vòng đời | `settledAt`, `expiresAt` (TTL 0), `deadLetterExpiresAt`, `stagingRecoveryAt`, `laneCleanupPendingAt`, `wakeRequestedAt` |

`actorDetachedAction` là sub-schema đầy đủ nhất: `{version: enum[1], invocationId, expectedToolName, toolName, toolCallId, turnId, taskId, idempotencyKey (minlength=maxlength=64), launchAttempt (0–15), status: enum['reserved','running','launch_indeterminate','succeeded','failed','cancelled'], reservedAt, observedAt, recoveryAfter, launchedAt, settledAt, result (maxlength 32_768), error}`.

Trạng thái `launch_indeterminate` là thứ đáng học: nó thừa nhận tường minh rằng **"đã gọi hay chưa" có thể không biết được**, và `idempotencyKey` cố định 64 ký tự cùng `recoveryAfter` là cách đi tiếp từ trạng thái đó.

19 index chia làm bốn nhóm: claim theo trạng thái (`{status, availableAt, createdAt}`, `{status, leaseUntil, createdAt}`, `{status, claimAvailableAt, createdAt}`), claim theo capability (2 index), thứ tự lane (`{orderingKey, status, laneSequence}` và một index 6 khóa cho terminal handling), và các sparse index quét dọn (`stagingRecoveryAt`, `laneCleanupPendingAt`, `backgroundToolResultDeletionPendingAt`, `actorReceipt.resolution`, `{user, actorActionAdmittedAt}`).

### 12.3. `agenttriggerlanesequences` và `agenttriggeruserpurges`

`agenttriggerlanesequences`: `_id` String, `value` (min 1), `user`, `tenantId`, `tailDeliveryId`, `publisherDeliveryId`, `publisherRequeueCount`, `publisherStartedAt`, `cleanupRequestedAt` (index). Index sparse `{publisherStartedAt}` — comment: field publisher **chỉ tồn tại khi có lane admission đang bay**, nên sparse giữ cho scan phục hồi tỉ lệ với số publisher bị bỏ rơi thay vì toàn bộ lịch sử lane (và được DocumentDB 3.6+ hỗ trợ).

`agenttriggeruserpurges`: `_id` là **ObjectId của User** (`ref: 'User'`), `fenceStartedAt` (required), `tenantId`. Dùng `_id` làm khóa ngoại là cách lấy unique miễn phí.

### 12.4. `schedules` — [`schema/schedule.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/schema/schedule.ts)

| Nhóm | Trường |
|---|---|
| Định danh | `id` (required, index), `user` (ObjectId, index), `tenantId`, `name` (`maxlength: 256`), `prompt` (`maxlength: 32000`), `agent_id` (required) |
| Lịch | `cadence.frequency` enum `['hourly','daily','weekdays','weekly','cron']`, `cadence.hour` (0–23), `cadence.minute` (0–59), `cadence.daysOfWeek []`, `cadence.expression` (`maxlength: SCHEDULE_CRON_MAX_LENGTH`), `timezone` (required), `cron` |
| Mục tiêu | `target` enum `['new']`, `chatProjectId`, `file_ids`, `tools`, `mcpConsent` (Mixed + zod validate) |
| Trạng thái | `enabled` (required, default true), `disabledReason` enum 10 giá trị |
| Chạy | `nextRunAt`, `leaseUntil`, `leaseBy`, `claimToken`, `configRevision` (default 0) |
| Xóa | `deleting` (default false), `deletionSuspension {token, enabled, nextRunAt}`, `erased`, `erasedAt`, `eraseAttemptedAt` |
| Idempotency | `slot` (min 0), `clientRequestId`, `clientRequestDigest` |
| Thống kê | `lastRun {conversationId, status, error, mcp[], firedAt, scheduledFor}`, `runCount`, `countedFor [Date]`, `countersAsOf`, `failureCount`, `balanceSkipCount` |

Index:

| Index | Tính chất |
|---|---|
| `{erasedAt}` | TTL **24 giờ**, partial `erased: true` — dòng sống không bao giờ khớp |
| `{id, tenantId}` | unique |
| `{enabled, nextRunAt}` | Engine quét |
| `{user, slot}` | **unique**, partial `{deleting: false, slot: {$exists: true}}` |
| `{user, clientRequestId}` | **unique**, partial `clientRequestId: {$exists: true}` |
| `{deleting, eraseAttemptedAt}` | Rotation khi quét xóa |

Bốn comment trong file này là tài liệu thiết kế đúng nghĩa:

- **`isStructuredCadence` phải là hàm nhận `this` là DOCUMENT, không phải object cadence.** `cadence` là nested path chứ không phải subdocument, nên validator trên `cadence.hour` nhận document; đọc `this.frequency` ở đó luôn `undefined`, khiến mọi cadence trông như structured và **mọi lần ghi cron đều bị từ chối**. Đây là bug thật đã được sửa và ghi lại.
- **`slot` là hạn mức create mỗi user do database thực thi.** Hai lần create đồng thời giành cùng slot thì va chạm trên index, một bên retry slot trống kế tiếp — thay vì đếm rồi so sánh (racy). Slot được giải phóng (loại khỏi index) khi schedule `deleting`.
- **`clientRequestId` cố ý KHÔNG lọc theo `deleting`.** Một key phải giữ nguyên trong lúc dòng của nó đang bị xóa, nếu không một retry đến giữa chừng sẽ tạo bản sao sống lâu hơn cả bản gốc.
- **`countedFor` + `countersAsOf` là hai lớp khác nhau.** `countedFor` (mảng Date có `$slice`) làm việc đếm idempotent **theo từng lần xảy ra**; `countersAsOf` làm nó **có thứ tự**, để một lần xảy ra cũ settle muộn không dựng lại streak mà một lần mới hơn đã xóa. Dòng ghi trước khi field này tồn tại thì hàng rào tắt.

### 12.5. `scheduleruns`

`scheduleId` (required), `user` (ObjectId, index), `tenantId`, `scheduledFor` (required), `firedAt`, `conversationId`, `checkpointNamespace` (`select: false`), `deliveryKey`, `chatProjectId`, `resumeClaimedAt`, `status` enum `['started','requires_action','success','error','interrupted','skipped_overlap','skipped_balance']`, `error` (`maxlength: 2048`), `mcp []`, `droppedFileIds`, `durationMs`, `bookkept`, `settledAt`, `capacitySlot`, `admissionOnly`, `abortRequestedAt`, `abortSource` enum `['stop','deletion']`, `abortPersistedAt`, `reconciledAt`, `configRevision`.

| Index | Tính chất |
|---|---|
| `{scheduleId, scheduledFor}` | **unique** — một lần xảy ra chỉ một dòng |
| `{settledAt}` | TTL 90 ngày, **TTL thuần, không partial** |
| `{scheduleId}` | **unique**, partial `status: 'started'` — **tối đa một run đang chạy mỗi schedule** |
| `{capacitySlot}` | **unique**, partial `{status: 'started', capacitySlot: {$exists: true}}` — **fireConcurrency TOÀN CỤC do database thực thi** |
| `{scheduleId, firedAt desc}` | |
| `{status, firedAt}` | |
| `{status, reconciledAt, firedAt}` | Round-robin reconcile |
| `{user, tenantId, conversationId}` | |

Comment trên TTL `settledAt` là một bài học riêng về DocumentDB:

> Retention chỉ áp cho dòng **đã settle**: một cửa sổ phê duyệt dài hơn thời gian retention sẽ khiến Mongo hết hạn một run `requires_action` còn sống — job được giữ lại khi đó resume mà không có dòng run (không bookkeeping), và việc quiesce khi xóa không còn khám phá hay abort nó được. Diễn đạt bằng **TTL thuần trên `settledAt`** (chỉ được ghi bởi các lần ghi terminal): TTL bỏ qua document thiếu trường date, nên dòng sống không hết hạn mà **không cần `partialFilterExpression`** — mà predicate `$in` của nó thì **Amazon DocumentDB 5.0 không build được**, và điều đó sẽ khiến `initializeScheduleEngine` từ chối khởi động trên target đó.

Đây là mẫu đáng mượn nguyên vẹn: **dùng sự vắng mặt của trường TTL làm điều kiện lọc, thay vì partial index.**

---

## 13. Billing

### 13.1. `balances`

`user` (ObjectId→User, required, index), `tokenCredits` (default 0 — **1000 tokenCredits = 1 mill = $0.001**), `autoRefillEnabled` (default false), `refillIntervalValue` (default 30), `refillIntervalUnit` (enum `REFILL_INTERVAL_UNITS`, default `days`), `lastRefill` (default now), `refillAmount` (default 0), `refillMode` (enum `BALANCE_REFILL_MODES`, default `add`), `tenantId`.

Ba trường `select: false` xử lý đồng thời:

| Trường | Vai trò |
|---|---|
| `reservations` | `[{id, amount, expiresAt}]` — credit bị giữ bởi request đang bay; nhả khi request settle, hoặc bị dọn khi hết hạn |
| `reservedCredits` | Tổng đã giữ |
| `pendingRefill` | `{transactionId (ObjectId), rawAmount, context: enum['autoRefill','balanceReset']}` |

`reservations` có `expiresAt` **nhưng không có TTL index** — một request chết không tự nhả credit; việc dọn do ứng dụng làm. **Không có index nào ngoài `user` và `tenantId`.**

### 13.2. `transactions`

`user` (ObjectId→User, required, index), `conversationId` (String, `ref: 'Conversation'`, index), `tokenType` enum `['prompt','completion','credits']` (required), `model` (index), `context`, `valueKey`, `rate`, `rawAmount`, `tokenValue`, `inputTokens`, `writeTokens`, `readTokens`, `messageId`, `tenantId` (index). Không có index compound nào.

`writeTokens`/`readTokens` là token cache ghi/đọc (prompt caching). `messageId` là String không index — truy vết ngược từ message về chi phí phải quét.

---

## 14. Hạ tầng

| Collection | Trường | Index |
|---|---|---|
| `keys` | `userId` (ObjectId→User, required), `name` (required), `value` (required), `expiresAt`, `tenantId` | `{expiresAt}` TTL 0; `{userId, name, tenantId}` **không unique** — comment: *"database cũ có thể đang giữ dòng trùng cho một user và một tên key"* |
| `pluginauths` | `authField` (required), `value` (required), `userId` (**String**, required), `pluginKey`, `tenantId` | `{userId, pluginKey, authField, tenantId}` không unique |
| `resourcelocks` | `key` (**unique**), `ownerId` (required), `expiresAt` (required) | `{expiresAt}` TTL 0. **Không có `tenantId`** |

`resourcelocks` là lock phân tán tổng quát duy nhất trong hệ: unique trên `key` để giành lock, TTL để tự nhả khi process chết. Mọi lock khác (schedule lease, code environment lease, skill sync lock, delivery lease) đều **nhúng vào chính document của tài nguyên** thay vì dùng collection này.

`pluginauths.userId` là String trong khi hầu hết nơi khác dùng ObjectId — một điểm không nhất quán về kiểu khi join.

---

## 15. Collection không qua Mongoose

### 15.1. Checkpoint LangGraph

> **Bổ sung 27/10/2026:** tầng agent của LibreChat là ba lớp — LangGraph → `@librechat/agents` (package riêng của họ) → app. Bên dưới là `StateGraph` thật với topology agent loop kinh điển; code production của LibreChat **không** import graph API LangGraph ở đâu cả. Chi tiết và bằng chứng ở [librechat.md §11](./librechat.md).

Bốn collection, thao tác qua raw driver, **không chịu tenant isolation plugin**.

| Collection | Shape |
|---|---|
| `agent_checkpoints` | `{thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, lc_owner, type, checkpoint: Binary, metadata: Binary, metadata_search: CheckpointMetadata}` |
| `agent_checkpoint_writes` | `{thread_id, checkpoint_ns, checkpoint_id, task_id, idx, channel, type, value: Binary, lc_owner}` |
| `agent_checkpoint_stores` | `{_id: String, owner, storage: {type, checkpointCollectionName, checkpointWritesCollectionName}}` |
| `agent_checkpoint_deletions` | `{_id, version, threadId, checkpoint?, userId, tenantId, storage}` |

Tên hai collection đầu **cấu hình được** qua `endpoints.agents.checkpointer.checkpointCollectionName` / `checkpointWritesCollectionName`; mặc định như trên ([`checkpoints/config.ts`](/home/lamhung/code/LibreChat/packages/api/src/agents/checkpoints/config.ts)). `type` có thể là `'mongo'` hoặc `'memory'`.

**Index:** `MongoDBSaver.setup()` tạo index compound + TTL trên `upserted_at` với `ttl = ttlSeconds` (mặc định `DEFAULT_CHECKPOINT_TTL_SECONDS = 24 * 60 * 60`, tức **24 giờ** — [`stream/checkpoints.ts:3`](/home/lamhung/code/LibreChat/packages/api/src/stream/checkpoints.ts)). LibreChat tạo thêm hai index mỗi collection: `{checkpoint_ns: 1}` và `{lc_owner: 1, thread_id: 1}`.

`lc_owner` và hai khóa config `__librechat_checkpoint_owner` / `__librechat_legacy_checkpoint_id` là phần LibreChat **thêm vào** trên cấu trúc của `@langchain/langgraph-checkpoint-mongodb`, để có thể xóa checkpoint theo chủ sở hữu mà thư viện gốc không hỗ trợ.

Hai ghi chú vận hành trong [`agents/checkpointer.ts:879-900`](/home/lamhung/code/LibreChat/packages/api/src/agents/checkpointer.ts):

- `MongoDBSaver.setup()` khởi động các build index **song song** và **báo lỗi thay vì throw**. Amazon DocumentDB chỉ cho một build index mỗi collection tại một thời điểm, nên ở đó build thứ hai của mỗi cặp bị từ chối (code 40333) và saver sẽ chạy **thiếu index TTL — checkpoint khi đó không bao giờ hết hạn**. Cách xử lý: `setup()` idempotent, nên chạy lại nhiều lần cho tới khi đủ index, với deadline `CHECKPOINT_INDEX_BUILD_DEADLINE_MS = 120_000`.
- Saver phải được bind vào **đúng database mà Mongoose đã chọn** (`dbName: mongoose.connection.db?.databaseName`). Không truyền thì `MongoClient.db()` lấy database mặc định từ URI, có thể khác database Mongoose dùng — và khi đó một lần pause được ghi vào một database còn LibreChat tìm ở database khác.

`agent_checkpoint_deletions` có comment nêu rõ vai trò: bản ghi **không chứa payload checkpoint** và chỉ tồn tại trong lúc xóa, không phải mỗi generation một dòng; chúng phải sống tới khi cả drain lẫn cleanup thành công.

### 15.2. Browser setup

| Collection | Shape | Index |
|---|---|---|
| `browser_setup_sessions` | `BrowserSetupSession & {_id: String, nonces: [{nonce, expiresAt}], operations, deleteAfter, allocationReleased, reconciledAt}` | `{deleteAfter}` TTL 0; `{reconciledAt, expiresAt, _id}` |
| `browser_setup_budget` | `{_id: 'global', allocations: [{attemptId, ipHash, expiresAt, session}]}` | — |
| `browser_setup_requests` | `{_id: 'global', expiresAt, count, peers: Record<String, Number>}` | — |

Hai collection sau là **singleton document `_id: 'global'`**, upsert bằng `$setOnInsert`, có bắt lỗi duplicate key (11000) khi khởi tạo đua nhau. Comment giải thích mục đích: *"singleton chặn trạng thái cấp phát ẩn danh, kể cả khi IP do kẻ tấn công kiểm soát là nhiều địa chỉ khác nhau"* — tức gom hạn mức vào một document để kẻ tấn công không thể làm phình số dòng bằng cách đổi IP.

### 15.3. Hai collection dọn dẹp

`code_environment_tombstones`: `{_id, tenantId, environmentId, deletedAt, setupBinding, setupResourceId}`. `_id` là SHA-256 của `(environmentId, tenantId)` — **khóa tất định thay cho unique index**.

`mcp_authorization_fence_retries`: `{_id, userId, serverName, tenantId, version, createdAt, updatedAt}`. `_id` = `JSON.stringify([tenantId ?? '', userId, serverName, version])` — cũng là khóa tất định. Index duy nhất `{updatedAt: 1}` tên `updatedAt_1`, tạo lười và có retry.

Cả hai đều dùng cùng kỹ thuật: **nhét khóa logic vào `_id`** để lấy upsert idempotent mà không cần unique index phụ. Với `code_environment_tombstones` còn một lý do nữa — hash che `environmentId` thật khỏi `_id`.

---

## 16. Mẫu thiết kế đáng chú ý

1. **Partial unique index làm hạn mức và lock.** Năm chỗ dùng cùng kỹ thuật: `schedule.slot` (hạn mức create mỗi user), `scheduleRun.capacitySlot` (fireConcurrency toàn cục), `scheduleRun {scheduleId}` partial `status:'started'` (một run hoạt động mỗi schedule), `codeEnvironment.ownerSlot` (hạn mức sandbox mỗi chủ), `agentQueuedTurn.activeSlot`/`admissionSlot`/`claim_lane`. Trong mọi trường hợp lý lẽ giống nhau: **thay "đọc rồi so sánh" (racy) bằng một va chạm duplicate-key nguyên tử**.

2. **TTL thuần thay partial index để tương thích DocumentDB.** `scheduleRun.settledAt` chỉ được ghi bởi các lần ghi terminal, nên TTL trên nó tự động bỏ qua dòng sống. Lý do kỹ thuật: predicate `$in` trong `partialFilterExpression` không build được trên DocumentDB 5.0, và sự cố đó sẽ chặn engine khởi động.

3. **Khóa tất định trong `_id`.** `code_environment_tombstones` (SHA-256), `mcp_authorization_fence_retries` (JSON tuple), `agentTriggerUserPurge` (`_id` = ObjectId của User), `subagentContent`, `agentQueuedTurnSequence`, `agentTriggerLaneSequence` (đều `_id: String`). Upsert idempotent miễn phí, không cần index phụ.

4. **Chuỗi hash + unique `(chainKey, seq)` cho append-only.** `auditLog` dùng unique index làm cả khóa phân trang keyset lẫn cơ chế chống phân nhánh chuỗi.

5. **Bịt mọi lối thoát middleware.** `auditLog` đăng ký 7 hook, bao gồm cả biến thể `{document: true, query: false}` (vì Mongoose mặc định đăng ký `deleteOne`/`updateOne` là query middleware, để hở `Document.prototype.*`) và chặn `bulkWrite` + `insertMany` vì chúng đi thẳng raw driver.

6. **`select: false` như biện pháp hiệu năng, không chỉ bảo mật.** `user.pinnedOrder` có comment nói rõ: mọi request xác thực đều load user document, để field này selected sẽ kéo hàng trăm KB trên những đường không bao giờ đọc nó.

7. **Hai index cùng khóa, khác `partialFilterExpression`.** `files` có `project_file_picker` (partial `embedded: true`) và `project_file_picker_search_destination` (partial `metadata.searchDestination: true`) — cùng hình dạng truy vấn, hai tập con rời nhau, hai index hẹp thay vì một index rộng.

8. **Denormalize có chủ đích, kèm lý do viết ra.** `agent.mcpServerNames` (trích từ `tools` để query được), `agent.authorName`, `promptGroup.authorName`, `chatProject.conversationCount`/`lastConversationAt`, `conversation.lastResponseMessageId`. Không có trigger nào giữ chúng đúng.

9. **Generation fencing nhiều chiều.** `toolApprovalGrant` có `generation` + `approvedAgentGeneration` + `approvedToolGeneration` + `approvedRevocation` + `oauthEpoch`: phê duyệt mất hiệu lực theo năm trục độc lập. `schedule.claimToken` (xoay mỗi lần claim **và** mỗi lần chủ sửa) tách khỏi `schedule.configRevision` (chỉ tăng khi chủ sửa) — run bắt `configRevision` lúc claim nên bookkeeping cuối không hành động trên config nó chưa từng chạy dưới.

10. **Trạng thái "không biết được" là trạng thái hạng nhất.** `actorDetachedAction.status` có `launch_indeterminate`; `agentEventActorReconciliations.status` có `commit_indeterminate`; `agentQueuedTurn` có hàng rào riêng cho `dead/ADMISSION_INDETERMINATE` của worker cũ. Kèm theo luôn là `idempotencyKey` cố định 64 ký tự và `recoveryAfter`.

11. **Commit hai pha trên một collection.** `subagentContent` ghi các mảnh `fragment ≥ 0` rồi publish bản ghi `fragment = -1` làm điểm nhìn thấy; partial index `subagent_content_sequence` chỉ index bản ghi commit.

12. **Lease riêng cho từng pha vòng đời.** `codeEnvironment` có ba bộ `*LeaseId`/`*LeaseExpiresAt`/`*ReconcileAfter` riêng cho registration, revocation và deletion — vì chúng chồng lấn được và một pha cướp lease của pha khác sẽ mất tính đúng đắn.

13. **Snapshot bất biến thay vì tra ACL sống.** `sharedLink.fileSnapshots` chép metadata file (không chép byte) để link chia sẻ hoạt động mà không hỏi quyền file của chủ sở hữu.

14. **`''` thay `null` trong unique key.** `toolApprovalGrant.conversationId` default `''` để unique key luôn đầy đủ — MongoDB phân biệt `null` với field vắng mặt trong index.

15. **Rotation chống đói.** `skillDeletion.lastAttemptAt`, `skillUploadIntent.lastCleanupAttemptAt`, `schedule.eraseAttemptedAt`, `scheduleRun.reconciledAt`, `browser_setup_sessions.reconciledAt` — cùng một mẫu: sắp xếp theo "lần thử gần nhất" để một dòng không drain được không chặn cả hàng đợi.

16. **"Một deadline, không bao giờ là một cờ."** Comment trên `file.deletionRetryAt`: bản ghi bị tái dùng cho nội dung khác có thể bị trì hoãn nhưng không bị mắc kẹt.

---

## 17. Giới hạn và điểm cần lưu ý

### 17.1. Phát hiện trong schema

**`users.refreshToken` tồn tại song song với collection `sessions`.** `userSchema` có mảng nhúng `refreshToken: [{refreshToken: String}]` (token thô), còn `sessionSchema` lưu `refreshTokenHash` trong collection riêng với unique `{user, refreshTokenHash}` và TTL trên `expiration`. Đường đăng xuất trong [`AuthService.js:236-239`](/home/lamhung/code/LibreChat/api/server/services/AuthService.js) dùng `findSession`, tức collection `sessions`. Tìm `$push`/`$pull` trên `refreshToken` trong toàn bộ `api/` và `packages/` chỉ ra **một kết quả duy nhất, nằm trong file test**. Mảng trên user document do đó là **di sản chưa gỡ**: nó không có TTL, không có hash, và nếu dữ liệu cũ còn sót thì đó là refresh token thô nằm trong document được load trên mọi request xác thực.

**`users.expiresAt` bị gỡ bởi mọi `updateUser` mặc định.** `createUser(..., disableTTL = true)` chỉ đặt TTL 7 ngày khi gọi tường minh với `false`, còn `updateUser` mặc định `$unset: { expiresAt: '' }`. Hệ quả: "xác nhận tài khoản" là tác dụng phụ của bất kỳ cập nhật nào, không phải một hành động tường minh. Caller muốn giữ TTL phải truyền `preserveExpiresAt`.

**`conversations.messages` được ghi lại toàn bộ mỗi lần `saveConvo`.** `saveConvo` với `appendMessageIds == null` chạy `update.messages = await getMessages({conversationId, user}, '_id')` — truy vấn lại mọi `_id` rồi ghi đè cả mảng, O(n) đọc + O(n) ghi. Đường đọc production tìm được đúng một chỗ, làm fallback. Xem [librechat.md §12.3](./librechat.md).

**`conversations.agent_id` khai hai lần.** Một lần qua spread `conversationPreset` (dòng ~44), một lần tường minh (dòng ~74). Cùng kiểu nên không đổi hành vi, nhưng là trùng lặp thật.

**`presets.title` có `meiliIndex: true` nhưng `presets` không gắn plugin Meili.** Chỉ `conversations` và `messages` gọi `schema.plugin(mongoMeili, ...)`. Cờ này vô hiệu.

**`categoriesSchema` không có model.** Export từ `schema/index.ts`, khai hai unique index, nhưng không hàm `create…Model` nào dùng. Nếu collection `categories` từng tồn tại ở deployment cũ thì các index của nó cũng không được build nữa.

**Nhiều unique logic chỉ được Mongoose thực thi, không phải database.** `promptGroup.productionId` và ba field `source*` dùng `required` dạng hàm theo `source`; `systemGrant` yêu cầu mọi ghi đi qua `grantCapability` vì không có hook chuẩn hóa `principalId`; `preset.defaultPreset` không có ràng buộc "một mặc định mỗi user". Mọi đường ghi bằng raw driver hoặc `bulkWrite` bỏ qua tất cả.

**Plugin `applySearchTokens` không chạy với `bulkWrite`.** Comment yêu cầu caller tự gọi `withSearchTokens`; quên thì user/group biến mất khỏi tìm kiếm mà không có lỗi.

**Build index thất bại im lặng nếu thiếu listener.** `models/index.ts` gắn listener `'index'` chính vì lý do này — và khi DocumentDB <5.0 từ chối `partialFilterExpression`, **unique constraint không được thực thi**. Nghĩa là trên target đó, nhiều bất biến ở §16 mục 1 trở thành không có hiệu lực. Tôi **chưa kiểm chứng** hành vi này trên DocumentDB thật; đây là điều code tự nói.

### 17.2. Việc chưa làm

- Chưa chạy ứng dụng, chưa kết nối MongoDB, chưa `getIndexes()` trên database thật. Toàn bộ index trong tài liệu là **khai báo trong source**, không phải index đang tồn tại.
- Tên collection: chỉ 21 tên được xác nhận trong source (§1.5). Phần còn lại suy từ quy tắc pluralize của Mongoose, **chưa đối chiếu được** vì `node_modules` chưa cài trong checkout này.
- Chưa đối chiếu mọi field với đường đọc/ghi runtime. Khác với [librechat.md](./librechat.md) vốn truy từ schema tới caller, tài liệu này là **bản liệt kê schema**; một field có mặt ở đây không có nghĩa là có code ghi vào nó.
- Chưa khảo sát phần Redis, RAG API và MeiliSearch ở mức schema — chỉ ghi nhận chúng tồn tại và nối vào đâu.
- Chưa đo kích thước document thực tế. Hai chỗ có rủi ro chạm trần 16 MB mà tôi **không kiểm chứng được nếu không có dữ liệu thật**: `agent.versions: [Mixed]` (lịch sử phiên bản nhúng) và `group.memberIds: [String]` (thành viên nhúng).
- Chưa kiểm tra các `methods/*.ts` xem có đường ghi nào bỏ qua validator schema. Số lượng comment cảnh báo về `bulkWrite`/`insertMany`/raw driver trong source cho thấy đây là vấn đề có thật mà họ đã gặp nhiều lần.
