<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# AGENTS.md — Frontend

## Contents & Navigation

- [1. Mục đích và phạm vi](#1-mục-đích-và-phạm-vi) — Phạm vi áp dụng, đối tượng và kiến trúc tổng quan của frontend Next.js kết nối FastAPI. Keywords: `Next.js`, `FastAPI`, `App Router`, `monorepo`, `frontend scope`.
- [2. Nguyên tắc cốt lõi](#2-nguyên-tắc-cốt-lõi) — 12 nguyên tắc bất biến về ranh giới FastAPI, server-state cache, tenant isolation và tái sử dụng code. Keywords: `principles`, `feature-driven`, `tenant cache`, `server state`, `FastAPI authority`.
- [3. Tech stack đã chốt](#3-tech-stack-đã-chốt) — Danh mục công nghệ chính thức cho React, Next.js, UI library, state management và testing. Keywords: `Next.js App Router`, `TypeScript`, `Tailwind CSS`, `shadcn/ui`, `TanStack Query`, `Zustand`, `Zod`, `Vitest`.
- [4. Ranh giới trách nhiệm frontend và backend](#4-ranh-giới-trách-nhiệm-frontend-và-backend) — Phân định việc frontend được phép xử lý (UI/UX, routing) vs FastAPI bắt buộc xử lý (auth, business rule, storage). Keywords: `separation of concerns`, `business logic`, `authorization`, `FastAPI authority`, `presigned URL`.
- [5. Cấu trúc repository đề xuất](#5-cấu-trúc-repository-đề-xuất) — Mô hình tổng thể thư mục dự án monorepo chuẩn giữa frontend và backend. Keywords: `monorepo`, `project structure`, `frontend/src`, `backend/src`, `folder layout`.
- [6. Cấu trúc frontend chi tiết](#6-cấu-trúc-frontend-chi-tiết) — Tổ chức nội bộ frontend: app, features, components (ui/shared/layout), lib, hooks, stores, types và generated. Keywords: `src/app`, `src/features`, `components/ui`, `components/shared`, `lib`, `stores`, `generated/api`.
- [7. Quy tắc dependency](#7-quy-tắc-dependency) — Chiều phụ thuộc hợp lệ giữa app, features, shared, ui và lib; phòng chống import vòng lặp. Keywords: `dependency rule`, `one-way flow`, `circular dependency`, `barrel export`, `import boundary`.
- [8. Quy trình bắt buộc trước khi viết code mới](#8-quy-trình-bắt-buộc-trước-khi-viết-code-mới) — Quy trình 5 bước khảo sát context, tìm kiếm mã tái sử dụng, phân vị trí file và kiểm tra package. Keywords: `workflow`, `5 steps`, `reuse-first`, `code location matrix`, `package check`.
- [9. Quy tắc component React](#9-quy-tắc-component-react) — Nguyên tắc Server Component vs Client Component, ranh giới "use client", thiết kế component và naming. Keywords: `Server Component`, `Client Component`, `"use client"`, `accessibility`, `naming conventions`.
- [10. API integration với FastAPI](#10-api-integration-với-fastapi) — Tích hợp API client tập trung, OpenAPI codegen, mapping dữ liệu, error handling, presigned upload S3-compatible và job 202. Keywords: `apiClient`, `OpenAPI codegen`, `error contract`, `presigned upload`, `credentials omit`, `202 Accepted`, `polling`.
- [11. TanStack Query](#11-tanstack-query) — Quản lý server state, định nghĩa query-key factory scoped theo tenant, mutation invalidation và hủy request. Keywords: `TanStack Query`, `queryKey`, `query-key factory`, `organization_id`, `invalidation`, `mutation`.
- [12. Zustand](#12-zustand) — Phạm vi áp dụng Zustand cho global client-only UI state; cấm lưu bản sao authoritative của API data. Keywords: `Zustand`, `client state`, `UI shell`, `organization switcher`, `no server state`.
- [13. Form và Zod](#13-form-và-zod) — Xử lý form bằng React Hook Form, xác thực schema bằng Zod, liên kết lỗi 422 từ backend và chống submit đúp. Keywords: `React Hook Form`, `Zod`, `validation`, `422 field error`, `double submit prevention`.
- [14. Authentication và authorization](#14-authentication-và-authorization) — Luồng đăng nhập/đăng xuất, session cookie HttpOnly, bảo vệ URL redirect và hiển thị UI theo permission. Keywords: `auth endpoints`, `HttpOnly cookie`, `session expiry`, `PermissionGate`, `open redirect protection`.
- [15. Styling và design system](#15-styling-và-design-system) — Áp dụng Tailwind CSS theo token chuẩn, tiện ích merge cn(), thành phần shadcn/ui và dark mode/a11y. Keywords: `Tailwind CSS`, `cn()`, `design tokens`, `shadcn/ui`, `dark mode`, `accessibility`.
- [16. Testing](#16-testing) — Phân tầng kiểm thử: Vitest cho unit, React Testing Library cho component, Playwright cho E2E quan trọng. Keywords: `Vitest`, `React Testing Library`, `Playwright`, `E2E tests`, `regression tests`, `tenant switch test`.
- [17. Performance](#17-performance) — Tối ưu hóa hiệu năng render, dynamic import, debounce search, chống N+1 request và kiểm soát bundle size. Keywords: `performance`, `dynamic import`, `debounce`, `N+1 requests`, `bundle size`, `useMemo`.
- [18. Security](#18-security) — Phòng thủ bảo mật: chống lộ secret NEXT_PUBLIC_, sanitize HTML, bảo vệ presigned URL và chính sách CORS/CSRF. Keywords: `security`, `NEXT_PUBLIC_`, `dangerouslySetInnerHTML`, `presigned URL safety`, `CSRF`, `CORS`.
- [19. Chất lượng code](#19-chất-lượng-code) — Kỷ luật TypeScript strict, cấm @ts-ignore/any, giữ gìn code sạch, quản lý lockfile pnpm và tương thích ngược. Keywords: `TypeScript strict`, `no any`, `no ts-ignore`, `clean code`, `pnpm-lock.yaml`, `backward compatibility`.
- [20. Lệnh kiểm tra](#20-lệnh-kiểm-tra) — Bộ lệnh kiểm tra chuẩn: lint, typecheck, test, build, playwright và script generate:api. Keywords: `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`, `playwright`, `generate:api`.
- [21. Definition of Done](#21-definition-of-done) — Bảng kiểm hoàn tất bắt buộc trước khi kết thúc bất kỳ task frontend nào. Keywords: `Definition of Done`, `checklist`, `quality gates`, `verification`, `DoD`.
- [22. Những anti-pattern bị cấm](#22-những-anti-pattern-bị-cấm) — Danh mục hành vi, mẫu thiết kế và cấu trúc sai lầm bị cấm trên toàn frontend. Keywords: `anti-patterns`, `forbidden practices`, `architectural violations`, `security risks`.
- [23. Mẫu báo cáo cuối task của agent](#23-mẫu-báo-cáo-cuối-task-của-agent) — Khung cấu trúc chuẩn để báo cáo kết quả: Kết quả, Tái sử dụng, Files, Kiểm tra và Lưu ý. Keywords: `report format`, `task summary`, `verification report`, `final report`.

---

## 1. Mục đích và phạm vi

> **Scope:** Quy chuẩn kỹ thuật bắt buộc cho AI coding agent và developer trên toàn bộ mã nguồn frontend Next.js.
>
> **Keywords:** `Next.js`, `FastAPI`, `PostgreSQL`, `Celery`, `RustFS`, `frontend scope`

File này là quy chuẩn bắt buộc cho mọi AI coding agent và developer khi làm việc với frontend của dự án. Trong repository chuẩn, file này được đặt tại `frontend/AGENTS.md`.

Kiến trúc tổng thể:

```text
Browser
  -> Next.js frontend
  -> FastAPI backend
  -> PostgreSQL / Redis / Celery / RustFS
```

Phạm vi của tài liệu này là `frontend/`. Quy tắc dùng chung toàn repository nằm ở `../AGENTS.md` nếu file đó tồn tại; quy tắc backend nằm ở `../backend/AGENTS.md`.

Khi thay đổi API contract, authentication, organization context, authorization, upload file hoặc background-job flow, agent phải kiểm tra cả `backend/` để bảo đảm frontend khớp với FastAPI.

Nếu một thư mục con có `AGENTS.md` riêng, file gần code nhất được ưu tiên cho phần việc trong thư mục đó. Không được bỏ qua các quy tắc ở file cha nếu file con không ghi đè rõ ràng.

## 2. Nguyên tắc cốt lõi

> **Scope:** 12 nguyên tắc kiến trúc cốt lõi định hình ranh giới trách nhiệm, quản lý cache và tiêu chuẩn phát triển frontend.
>
> **Keywords:** `principles`, `feature-driven`, `tenant cache`, `server state`, `FastAPI authority`, `reuse-first`

1. FastAPI là backend chính và là nguồn sự thật cho business rule, authorization và dữ liệu.
2. Next.js chịu trách nhiệm presentation, navigation, form UX, client state và server-state cache.
3. Tổ chức frontend theo business feature, không gom toàn bộ code theo technical layer.
4. `app/` phải mỏng: route, layout, metadata, loading, error boundary và composition.
5. Tái sử dụng trước khi tạo mới. Luôn tìm component, hook, utility, type và API abstraction hiện có.
6. Chỉ đưa code vào khu vực shared khi nó thật sự độc lập với business domain và đã hoặc chắc chắn sẽ được dùng ở nhiều nơi.
7. Không sao chép business logic từ FastAPI sang frontend.
8. Không tin dữ liệu hoặc quyền do frontend tự quyết định. Backend phải validate và authorize lại mọi request.
9. Không sửa file generated bằng tay.
10. Mọi thay đổi phải được kiểm tra bằng lint, typecheck và test phù hợp trước khi hoàn thành.
11. Mọi server-state cache thuộc tenant phải được scope bằng `organization_id`.
12. Frontend không kết nối trực tiếp PostgreSQL, Redis hoặc Celery và không sở hữu credential RustFS.

## 3. Tech stack đã chốt

> **Scope:** Danh mục công nghệ, thư viện và công cụ được chuẩn hóa cho giao diện, quản lý state, form và kiểm thử frontend.
>
> **Keywords:** `Next.js App Router`, `TypeScript`, `Tailwind CSS`, `shadcn/ui`, `TanStack Query`, `Zustand`, `Zod`, `Vitest`, `Playwright`

### Frontend

- Next.js App Router
- React
- TypeScript strict mode
- pnpm
- Tailwind CSS
- shadcn/ui; Radix primitives khi component shadcn sử dụng hoặc cần primitive thấp hơn
- TanStack Query v5 cho server state ở Client Components
- Zustand cho global client/UI state thật sự cần thiết
- React Hook Form cho form state
- Zod cho validation phía frontend
- Native `fetch` thông qua API client chung
- OpenAPI code generation từ FastAPI; ưu tiên Orval hoặc `openapi-typescript` theo cấu hình repository
- Vitest
- React Testing Library
- Playwright
- ESLint
- Prettier

### Backend liên quan đến frontend

- Python 3.13+
- FastAPI
- Pydantic v2
- SQLAlchemy 2
- PostgreSQL, migration là SQL thuần chạy bằng dbmate (không dùng Alembic)
- Redis
- Celery cho background jobs
- RustFS thông qua S3-compatible API cho file/object storage
- Pytest, Ruff và Pyrefly

Không tự ý thêm framework hoặc package trùng chức năng. Ví dụ: không thêm Axios khi API client đang dùng `fetch`; không thêm Redux khi Zustand đã đáp ứng; không thêm một UI framework khác bên cạnh shadcn/ui nếu chưa có yêu cầu kiến trúc rõ ràng.

## 4. Ranh giới trách nhiệm frontend và backend

> **Scope:** Phân định rõ ràng trách nhiệm giữa lớp hiển thị (Next.js) và thẩm quyền nghiệp vụ/bảo mật tối cao (FastAPI).
>
> **Keywords:** `separation of concerns`, `business logic`, `authorization`, `FastAPI authority`, `presigned URL`, `client guards`

### Frontend được phép xử lý

- Hiển thị UI và trạng thái loading/error/empty/success.
- Routing, layout, metadata và navigation.
- Form state và validation để cải thiện UX.
- Gọi API, cache, refetch và invalidation.
- State giao diện như sidebar, theme, panel, bước wizard tạm thời.
- Ẩn hoặc hiện action dựa trên permission backend đã trả về để cải thiện UX.
- Mapping dữ liệu API sang view model khi UI thật sự cần format khác.

### FastAPI bắt buộc xử lý

- Authentication authority và session/token lifecycle.
- Authorization, RBAC, organization scope và resource ownership.
- Business rule và workflow transition.
- Database query và transaction.
- Validation mang tính nghiệp vụ hoặc bảo mật.
- Tính toán lương, scoring, quota, trạng thái tuyển dụng và các quyết định nghiệp vụ.
- Tạo presigned URL, kiểm tra file và quản lý object storage.
- Background processing, AI orchestration và tác vụ dài.

Frontend có thể ẩn nút `Edit`, nhưng FastAPI vẫn phải trả `403` nếu người dùng không có quyền. Không coi client-side guards là lớp bảo mật.

## 5. Cấu trúc repository đề xuất

> **Scope:** Sơ đồ tổ chức thư mục cấp repository chuẩn cho monorepo kết hợp frontend Next.js và backend FastAPI.
>
> **Keywords:** `monorepo`, `project structure`, `frontend/src`, `backend/src`, `folder layout`

```text
project/
├── AGENTS.md
├── frontend/
│   ├── AGENTS.md
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── eslint.config.mjs
│   ├── components.json
│   ├── public/
│   ├── tests/
│   │   ├── e2e/
│   │   └── fixtures/
│   └── src/
│       ├── app/
│       ├── features/
│       ├── components/
│       ├── lib/
│       ├── hooks/
│       ├── stores/
│       ├── config/
│       ├── types/
│       └── generated/
└── backend/
    ├── AGENTS.md
    ├── pyproject.toml
    ├── tests/
    └── src/
        └── app/
            ├── main.py
            ├── config/
            ├── database/
            │   ├── session.py
            │   └── generated_tables.py
            ├── common/
            ├── modules/
            └── tools/
```

Nếu repository thực tế khác cấu trúc này, agent phải kiểm tra và tuân theo cấu trúc hiện hữu trước khi tạo thư mục mới. Không tạo một cây song song chỉ vì tên folder khác với tài liệu này.

## 6. Cấu trúc frontend chi tiết

> **Scope:** Quy định chi tiết cấu trúc các gói bên trong frontend/src và tiêu chuẩn phân bổ mã nguồn theo từng tầng chức năng.
>
> **Keywords:** `src/app`, `src/features`, `components/ui`, `components/shared`, `components/layout`, `lib`, `stores`, `generated/api`

```text
frontend/src/
├── app/
│   ├── (public)/
│   ├── (auth)/
│   ├── (dashboard)/
│   ├── layout.tsx
│   ├── loading.tsx
│   ├── error.tsx
│   ├── not-found.tsx
│   └── providers.tsx
├── features/
│   ├── auth/
│   ├── users/
│   ├── organizations/
│   ├── roles/
│   ├── permissions/
│   ├── recruitment/
│   │   ├── jobs/
│   │   ├── candidates/
│   │   ├── applications/
│   │   └── interviews/
│   ├── meetings/
│   ├── tasks/
│   └── ai/
├── components/
│   ├── ui/
│   ├── shared/
│   └── layout/
├── lib/
│   ├── api/
│   ├── auth/
│   ├── permissions/
│   ├── errors/
│   └── utils/
├── hooks/
├── stores/
├── config/
├── types/
└── generated/
    └── api/
```

### `src/app/`

Chỉ dùng cho:

- Route segments và route groups.
- `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`.
- Metadata.
- Server-side composition và route-level data orchestration.
- Provider ở root khi thật sự cần.

Không đặt component nghiệp vụ lớn, API function, schema hoặc utility trực tiếp trong `app/`.

Một `page.tsx` nên chủ yếu compose feature:

```tsx
import { UsersScreen } from "@/features/users";

export default function Page() {
  return <UsersScreen />;
}
```

Route groups đề xuất:

```text
app/
├── (public)/
│   ├── page.tsx
│   └── about/page.tsx
├── (auth)/
│   ├── login/page.tsx
│   └── forgot-password/page.tsx
└── (dashboard)/
    ├── layout.tsx
    ├── dashboard/page.tsx
    ├── users/page.tsx
    └── organizations/page.tsx
```

### `src/features/`

Mỗi feature sở hữu code business-facing của chính nó:

```text
features/users/
├── api/
│   ├── get-users.ts
│   ├── get-user.ts
│   ├── create-user.ts
│   ├── update-user.ts
│   └── delete-user.ts
├── components/
│   ├── users-screen.tsx
│   ├── user-table.tsx
│   ├── user-form.tsx
│   ├── user-filters.tsx
│   └── user-permission-dialog.tsx
├── hooks/
│   ├── use-users.ts
│   ├── use-user.ts
│   └── use-create-user.ts
├── schemas/
│   └── user.schema.ts
├── types/
│   └── user.types.ts
├── utils/
│   └── map-user-to-view-model.ts
├── constants/
│   └── user.constants.ts
└── index.ts
```

Không bắt buộc tạo mọi folder cho mọi feature. Chỉ tạo folder khi có file thật sự thuộc loại đó. Feature nhỏ có thể bắt đầu với vài file và tách dần khi cần.

### `src/components/ui/`

Chứa UI primitive, không biết business domain:

- Button
- Input
- Select
- Dialog
- DropdownMenu
- Tabs
- Table primitive
- Badge
- Tooltip

Đây thường là component do shadcn/ui đưa vào và được project sở hữu. Không thêm logic gọi API hoặc permission nghiệp vụ vào đây.

### `src/components/shared/`

Chứa component dùng lại ở nhiều feature nhưng cao hơn UI primitive:

- DataTable engine tổng quát
- Pagination
- SearchInput
- ConfirmationDialog
- EmptyState
- ErrorState
- FileUpload dùng chung
- DateRangePicker
- PermissionGate tổng quát

Component shared phải nhận dữ liệu và callback qua props; không được import trực tiếp API của một feature cụ thể.

### `src/components/layout/`

Chứa component khung ứng dụng:

- AppSidebar
- Header
- Breadcrumbs
- UserMenu
- PageContainer
- Navigation

### `src/lib/`

Chứa infrastructure và logic framework-agnostic dùng chung:

```text
lib/
├── api/
│   ├── client.ts
│   ├── server.ts
│   ├── api-error.ts
│   └── request-options.ts
├── auth/
│   ├── session.ts
│   └── guards.ts
├── permissions/
│   └── can.ts
├── errors/
│   └── normalize-error.ts
├── storage/
│   └── upload.ts
├── realtime/
│   └── client.ts
└── utils/
    ├── cn.ts
    ├── format-date.ts
    └── format-file-size.ts
```

`lib` không được import từ `features`. Dependency phải đi từ feature xuống lib, không đi ngược lại.

`lib/storage/upload.ts` chỉ chứa transport chung cho presigned upload; API xin URL/confirm upload vẫn thuộc `features/<feature>/api`. `lib/realtime` chỉ chứa connection infrastructure; subscription và mapping event thuộc feature sở hữu dữ liệu.

### `src/hooks/`

Chỉ chứa hook dùng chung và không gắn với một domain cụ thể, ví dụ:

- `use-debounce.ts`
- `use-media-query.ts`
- `use-disclosure.ts`
- `use-mounted.ts`

Hook liên quan user, job, candidate hoặc domain khác phải nằm trong feature tương ứng.

### `src/stores/`

Chỉ chứa global client state thật sự cần chia sẻ qua nhiều route/feature:

- UI shell state.
- Organization đang được chọn nếu đó là context toàn app.
- Wizard draft cần tồn tại khi chuyển nhiều màn hình.

Không lưu dữ liệu API như danh sách users/jobs/candidates trong Zustand. Dùng TanStack Query cho server state.

### `src/config/`

Chứa config typed và giá trị tĩnh toàn app:

- Environment validation.
- Navigation definitions.
- Route names.
- Feature flags.
- Public runtime configuration.

Không đọc `process.env` rải rác trong component. Tập trung việc đọc và validate biến môi trường tại config hoặc API infrastructure phù hợp.

### `src/types/`

Chỉ chứa type toàn cục, ví dụ:

- `ApiResponse<T>`
- `PaginatedResponse<T>`
- `PaginationParams`
- `SelectOption`

Type của user/job/candidate phải nằm trong feature hoặc được lấy từ `generated/api`.

### `src/generated/`

Chứa code sinh tự động từ FastAPI OpenAPI.

- Không sửa bằng tay.
- Không đặt business helper thủ công vào đây.
- Codegen phải có script tái tạo được.
- Nếu API schema đổi, cập nhật backend/OpenAPI rồi generate lại.

## 7. Quy tắc dependency

> **Scope:** Quy tắc luồng phụ thuộc một chiều giữa các module frontend và biện pháp loại trừ import xoay vòng (circular import).
>
> **Keywords:** `dependency rule`, `one-way flow`, `circular dependency`, `barrel export`, `import boundary`

Dependency hợp lệ:

```text
app -> features -> components/shared -> components/ui
app -> features -> lib
features -> generated/api
components/shared -> components/ui
```

Các package cấp thấp như `lib`, `components/ui`, `types` và `generated` không được import feature.

Hạn chế import trực tiếp giữa các feature. Nếu `jobs` cần một component đặc thù của `candidates`, trước tiên đánh giá một trong ba cách:

1. Compose hai feature ở `app/` hoặc ở màn hình cha.
2. Chuyển phần thật sự generic sang `components/shared`, `hooks`, `lib` hoặc `types`.
3. Tạo public API rõ ràng qua `features/<name>/index.ts` nếu dependency domain là có chủ đích và một chiều.

Không tạo vòng lặp dependency. Không dùng barrel export sâu hoặc `export *` tràn lan vì dễ tạo circular import và bundle ngoài ý muốn.

## 8. Quy trình bắt buộc trước khi viết code mới

> **Scope:** Quy trình 5 bước khảo sát, tìm kiếm mã nguồn hiện có, xác định vị trí đặt file và kiểm tra thư viện trước khi code.
>
> **Keywords:** `workflow`, `5 steps`, `reuse-first`, `code location matrix`, `package check`, `survey`

Đây là quy tắc bắt buộc, không phải gợi ý.

### Bước 1: Đọc context của repository

Trước khi code, kiểm tra:

```bash
pwd
rg --files -g 'AGENTS.md' -g '!node_modules'
rg --files frontend/src | sed -n '1,240p'
```

Sau đó đọc:

- `AGENTS.md` áp dụng cho file định sửa.
- `frontend/package.json`.
- `frontend/tsconfig.json`.
- Cấu hình ESLint/Prettier.
- `components.json` nếu dùng shadcn/ui.
- Feature tương tự gần nhất.
- Tests liên quan.

Không phỏng đoán package, alias, convention hoặc script. Kiểm tra repository trước.

### Bước 2: Tìm implementation đã có

Trước khi tạo component, hook, function, schema, type hoặc API wrapper mới, bắt buộc tìm theo:

1. Tên dự kiến.
2. Từ đồng nghĩa.
3. Hành vi hoặc API được sử dụng.
4. Kiểu dữ liệu liên quan.

Ví dụ:

```bash
rg -n "DataTable|data-table|table columns" frontend/src
rg -n "formatDate|format-date|Intl.DateTimeFormat" frontend/src
rg -n "useDebounce|debounce" frontend/src
rg -n "ConfirmationDialog|confirm.*dialog|AlertDialog" frontend/src
rg -n "apiClient|fetchJson|ApiError" frontend/src
rg -n "PaginatedResponse|PaginationParams" frontend/src
rg -n "UserResponse|CreateUser|/api/v1/users" frontend/src backend/src
rg -n "organizationId|organization_id|tenant|queryKey" frontend/src
rg -n "presigned|uploadFile|RustFS|S3|object_key" frontend/src backend/src
rg -n "job_id|202 Accepted|polling|WebSocket|EventSource" frontend/src backend/src
```

Ưu tiên kiểm tra theo thứ tự:

```text
1. Feature hiện tại
2. components/shared, hooks, lib/utils, lib/api, types
3. Feature gần giống
4. generated/api
5. Dependency đã cài trong package.json
```

Nếu đã có implementation phù hợp:

- Dùng lại trực tiếp nếu API hiện tại đáp ứng.
- Mở rộng theo hướng backward-compatible nếu nhu cầu mới là hợp lý.
- Refactor thành shared nếu có ít nhất hai consumer thật sự và abstraction rõ ràng.
- Không tạo bản thứ hai chỉ vì khác tên hoặc khác một chi tiết nhỏ.

### Bước 3: Quyết định vị trí trước khi tạo file

| Code định tạo | Vị trí |
|---|---|
| Button/Input/Dialog generic | `components/ui` |
| DataTable/EmptyState/FileUpload generic | `components/shared` |
| Sidebar/Header/Breadcrumbs | `components/layout` |
| UserTable/UserForm | `features/users/components` |
| `useUsers`/`useCreateUser` | `features/users/hooks` |
| `getUsers`/`createUser` | `features/users/api` |
| User form Zod schema | `features/users/schemas` |
| User view model/helper | `features/users/types` hoặc `features/users/utils` |
| `useDebounce` generic | `hooks` |
| `formatDate` generic | `lib/utils` |
| Base API client/error | `lib/api` |
| Presigned upload helper không gắn app credential | `lib/storage` hoặc vị trí infrastructure hiện có |
| Realtime/SSE/WebSocket client dùng chung | `lib/realtime` hoặc vị trí infrastructure hiện có |
| API-generated schema/client | `generated/api` |
| Server response generic | `types` |

Khi chưa chắc code có dùng chung hay không, đặt nó gần feature đang dùng. Chỉ promote lên shared sau khi có abstraction rõ ràng. Không tạo abstraction theo suy đoán.

### Bước 4: Kiểm tra dependency có sẵn

Trước khi cài package mới:

```bash
rg -n '"dependencies"|"devDependencies"' frontend/package.json
pnpm --dir frontend why <package-name>
```

Không cài package mới nếu platform API, React, Next.js hoặc dependency hiện tại đã giải quyết tốt nhu cầu.

### Bước 5: Trình bày kế hoạch thay đổi

Với thay đổi không nhỏ, agent phải xác định ngắn gọn:

- File sẽ sửa/tạo.
- Code nào được dùng lại.
- API contract nào liên quan.
- Test nào sẽ thêm/chạy.
- Rủi ro về auth, permission, cache hoặc backward compatibility.

## 9. Quy tắc component React

> **Scope:** Tiêu chuẩn phân định Server Component và Client Component, kiểm soát ranh giới "use client" và quy ước thiết kế component.
>
> **Keywords:** `Server Component`, `Client Component`, `"use client"`, `accessibility`, `naming conventions`, `composition`

### Server Component và Client Component

- Mặc định dùng Server Component.
- Chỉ thêm `"use client"` khi cần event handler, browser API, React state/effect, client-only library hoặc TanStack Query hook.
- Đặt client boundary thấp nhất có thể; không biến cả page/layout thành Client Component chỉ vì một nút tương tác.
- Không truyền object không serializable từ Server Component sang Client Component.
- Không gọi browser API trong Server Component.

### Thiết kế component

- Một component có một trách nhiệm rõ ràng.
- Ưu tiên composition thay vì prop boolean ngày càng nhiều.
- Props phải có type rõ ràng; tránh `any`.
- Business component ở feature; generic component ở shared/UI.
- Không fetch cùng một resource ở nhiều component con nếu màn hình cha có thể điều phối hợp lý.
- Không dùng `useEffect` để derive state có thể tính trực tiếp trong render hoặc `useMemo`.
- Không mirror props vào state nếu không có lý do về editing/draft rõ ràng.
- Luôn xử lý loading, error, empty và success state cho UI gọi API.
- List item phải có key ổn định từ dữ liệu, không dùng index nếu thứ tự có thể thay đổi.
- Accessibility là bắt buộc: semantic HTML, label, focus, keyboard, aria khi cần.

### Naming

- File/folder: `kebab-case`.
- React component/type/interface: `PascalCase`.
- Function/variable/hook: `camelCase`; hook bắt đầu bằng `use`.
- Constant thật sự bất biến: `UPPER_SNAKE_CASE`.
- Boolean: bắt đầu bằng `is`, `has`, `can`, `should` hoặc `was`.
- Event props: `onSubmit`, `onClose`; internal handlers: `handleSubmit`, `handleClose`.
- API function dùng động từ: `getUsers`, `createUser`, `updateUser`, `deleteUser`.

## 10. API integration với FastAPI

> **Scope:** Kiến trúc tích hợp API với FastAPI, đồng bộ hợp đồng OpenAPI, xử lý mã lỗi, luồng tải tệp RustFS và theo dõi tác vụ nền 202.
>
> **Keywords:** `apiClient`, `OpenAPI codegen`, `error contract`, `RustFS presigned`, `202 Accepted`, `polling`, `data mapping`

### API client chung

Mọi request đến FastAPI phải đi qua abstraction chung trong `src/lib/api`. Không viết `fetch` gọi FastAPI rải rác trong component.

API client phải hỗ trợ nhất quán:

- Base URL từ config.
- `credentials: "include"` nếu auth dùng HttpOnly cookie.
- JSON serialization/deserialization.
- Request ID/correlation ID nếu backend hỗ trợ.
- Chuẩn hóa `ApiError`.
- `204 No Content`.
- Abort signal.
- Không tự động retry mutation nguy hiểm.
- Gắn organization context bằng path/header/cookie theo contract tập trung của backend; không để mỗi feature tự phát minh cơ chế tenant riêng.

Không đọc hoặc ghi token vào `localStorage` trừ khi kiến trúc bảo mật của dự án đã quyết định rõ bằng tài liệu khác. Ưu tiên HttpOnly, Secure, SameSite cookies do FastAPI phát hành.

Upload trực tiếp bằng presigned URL là ngoại lệ đối với FastAPI API client. Nó phải đi qua helper storage/upload riêng và không tự động gắn app cookie, Authorization header hoặc các header không nằm trong presigned contract.

### API function theo feature

```ts
// features/users/api/get-users.ts
import { apiClient } from "@/lib/api/client";
import type { GetUsersParams, UserListResponse } from "../types/user.types";

export function getUsers(params: GetUsersParams, signal?: AbortSignal) {
  return apiClient<UserListResponse>("/api/v1/users", {
    method: "GET",
    query: params,
    signal,
  });
}
```

Không gọi API trong UI primitive. Không trộn toast/navigation vào API function thuần. Side effect UI thuộc mutation hook hoặc component điều phối.

### OpenAPI contract

Đối với frontend, FastAPI `/openapi.json` là nguồn API contract. PostgreSQL schema là nguồn sự thật của cấu trúc database phía backend, nhưng frontend không đọc `generated_tables.py` và không phụ thuộc trực tiếp vào database schema.

Luồng contract toàn hệ thống:

```text
PostgreSQL schema/migration
  -> backend/src/app/database/generated_tables.py
  -> repository/service
  -> Pydantic request/response schema
  -> FastAPI OpenAPI
  -> codegen command
  -> frontend/src/generated/api
  -> feature adapter/hook/component
```

Trước khi tự viết type request/response, tìm trong `generated/api`. Có thể tạo type UI/view model riêng nếu UI có nhu cầu khác, nhưng phải map rõ ràng ở feature boundary.

Không sửa generated type để chữa mismatch. Sửa Pydantic/OpenAPI hoặc codegen configuration rồi generate lại.

Không tự suy luận API type từ `generated_tables.py`. Database table có thể chứa internal field, audit field hoặc storage metadata không được phép xuất hiện trong API.

### Quy ước dữ liệu

- Giữ nguyên field API tại boundary nếu chưa có convention mapping toàn dự án.
- Nếu backend dùng `snake_case` và UI dùng `camelCase`, chỉ map tại một lớp adapter xác định; không map thủ công ở từng component.
- Date/time từ API dùng ISO 8601 có timezone. Parse/format tại UI bằng utility chung.
- ID UUID được biểu diễn bằng `string` ở TypeScript.
- Tiền tệ/decimal không được tính toán bằng floating-point tùy tiện. Tuân theo contract backend, thường dùng string hoặc integer minor units.
- Pagination phải dùng type và query-key convention chung.

### Error contract

Frontend phải hỗ trợ error format thống nhất từ FastAPI, ví dụ:

```json
{
  "error": {
    "code": "USER_EMAIL_EXISTS",
    "message": "Email đã tồn tại",
    "details": {},
    "request_id": "..."
  }
}
```

- Hiển thị message an toàn, thân thiện cho người dùng.
- Dùng `code` cho mapping hành vi, không phụ thuộc hoàn toàn vào chuỗi `message`.
- Log/report `request_id` khi có.
- Không hiển thị stack trace, SQL, token hoặc thông tin nội bộ.
- Phân biệt `401` chưa đăng nhập, `403` không có quyền, `404` không tồn tại, `409` conflict và `422` validation.

### Upload file qua S3-compatible storage/RustFS

RustFS là S3-compatible object storage hiện tại. Frontend chỉ biết API contract do
FastAPI cấp; không được giữ access key/secret key, cài S3 SDK hoặc phụ thuộc vào chi tiết
bucket policy của RustFS.

#### Ranh giới code

```text
features/<feature>/api
  -> gọi FastAPI để create/complete/delete và điều phối use case
  -> lib/storage/upload.ts
       -> chỉ PUT binary tới absolute presigned URL

features/<feature>/components
  -> chọn/chỉnh sửa/preview file và hiển thị trạng thái
components/shared
  -> primitive upload thật sự dùng chung, nhận callback/config qua props
```

- API create/complete/delete thuộc feature sở hữu resource.
- `src/lib/storage/upload.ts` chỉ là transport dùng chung cho presigned upload; không
  import feature, không biết avatar/CV/candidate và không gọi endpoint FastAPI.
- UI chỉnh ảnh, crop hoặc metadata riêng thuộc feature; chỉ đưa ra shared khi có ít nhất
  hai consumer và abstraction đã rõ.
- Tái sử dụng `uploadPresignedFile` và `StorageUploadError`; không viết lại raw upload
  `fetch` trong mỗi feature.

#### Contract và luồng upload

Contract hiện tại dùng cặp endpoint create + complete:

```text
1. Chọn hoặc chuẩn bị File cuối cùng ở browser
2. Frontend -> FastAPI create:
   { original_name, content_type, size_bytes }
3. FastAPI -> frontend:
   { file_id, upload: { url, method, headers, expires_in } }
4. Frontend -> storage: PUT chính File đó tới upload.url
5. Frontend -> FastAPI complete(file_id): gửi lại cùng metadata
6. FastAPI xác minh object, lưu stored_files và gắn file_id vào resource
7. Frontend chỉ coi upload thành công sau khi complete trả resource mới
```

`file_id` là định danh backend cấp cho workflow; không tự tạo ở frontend. Frontend không
gửi và không tự suy ra các field nội bộ `bucket`, `object_key`, `visibility`,
`checksum_sha256`, `uploaded_by` hoặc `deleted_at`. Không đọc schema `stored_files` để
tự viết API type; dùng OpenAPI generated type.

Nếu UI crop/compress/convert ảnh trước upload, phải tạo `File` cuối cùng trước bước create
và dùng chính file đó cho cả metadata, PUT và complete. Không gửi size/type của file gốc
rồi PUT file đã biến đổi. Blob URL chỉ dùng preview cục bộ và phải `URL.revokeObjectURL`
khi thay file/unmount.

#### Ba request có credential policy khác nhau

```text
FastAPI create   -> apiClient, app auth/cookie theo contract
Presigned PUT    -> uploadPresignedFile, credentials: "omit", chỉ signed headers
FastAPI complete -> apiClient, app auth/cookie theo contract
```

Khi PUT tới storage:

- Dùng absolute `upload.url` nguyên vẹn; không nối API base URL và không sửa query string.
- Không hard-code storage endpoint bằng `NEXT_PUBLIC_*`; backend chịu trách nhiệm trả URL
  phù hợp với browser. Local URL phải là S3 API cổng `9000`, không phải console `9001`.
- Dùng đúng `upload.method` và toàn bộ `upload.headers` backend trả về.
- Không tự thêm `Authorization`, app cookie, organization header, CSRF header hoặc header
  mặc định của API client.
- Bắt buộc `credentials: "omit"`; request storage không được kích hoạt auth-refresh flow.
- Body là `File`/`Blob`, không JSON stringify, không multipart `FormData` trừ khi backend
  đổi contract sang presigned POST.
- Không tự đặt `Content-Length`; browser quản lý header bị giới hạn này.
- Không log/persist presigned URL hoặc đưa nó vào analytics/error payload.

Do đó upload presigned là ngoại lệ có chủ đích đối với quy tắc “mọi FastAPI request dùng
API client”: URL đích là storage, không phải FastAPI.

#### Public URL và private download

- Frontend nhận public URL qua resource response, ví dụ `user.image`; không dựng URL từ
  bucket, `file_id` hoặc quy ước `public/...`.
- Public URL là địa chỉ hiển thị có thể cache theo HTTP policy, nhưng không phải identity
  nghiệp vụ và không được dùng thay `file_id` trong mutation.
- Private file không có anonymous URL. Frontend phải gọi FastAPI endpoint đã authorize để
  lấy presigned GET ngắn hạn hoặc download qua backend; không đoán đường dẫn `private/`.
- Không đổi private URL thành public hoặc proxy qua Next.js chỉ để né CORS/authorization.
- Khi dùng `next/image` cho remote public URL, cập nhật `next.config.ts` bằng allowlist
  host/path hẹp theo environment. Không dùng wildcard rộng để chữa lỗi ảnh; với component
  `<img>`/Avatar hiện có vẫn phải có alt/fallback và error state phù hợp.

#### State, retry và lỗi

UI upload tối thiểu phải phân biệt:

```text
idle -> preparing -> creating -> uploading -> completing -> success/error
```

- Disable submit/close gây mất state khi đang prepare/upload/complete; hỗ trợ abort khi UX
  có cancel và truyền cùng `AbortSignal` qua ba bước.
- Chỉ hiển thị success, cập nhật cache và đóng dialog sau complete thành công.
- Invalidate/update query của resource từ response complete; không tự dựng public URL hay
  optimistic `file_id`.
- Presigned URL hết hạn hoặc PUT bị từ chối: xin session mới và upload lại nếu người dùng
  retry. Không tái sử dụng URL cũ.
- Không blind-retry create/complete mutation khi backend chưa công bố idempotency contract.
- FastAPI error đi qua `ApiError`; storage PUT error đi qua `StorageUploadError`.
- `storage_upload_unreachable` thường là endpoint storage không chạy, DNS/network hoặc
  bucket CORS. Việc FastAPI vẫn trả `200/201` không chứng minh PUT sang storage hoạt động.
- `storage_upload_rejected` là storage trả non-2xx, thường do URL hết hạn, chữ ký/header
  không khớp hoặc policy. Không gộp hai lỗi trên thành thông báo “backend mất kết nối”.
- Frontend không thể sửa bucket CORS bằng code UI; thông báo phải giúp kiểm tra S3 endpoint
  và CORS, không yêu cầu người dùng đăng nhập lại một cách sai lệch.

#### Validation và kiểm thử

Frontend validate MIME/size/filename để phản hồi sớm và có thể crop/compress cho UX,
nhưng FastAPI vẫn là security authority. Không coi extension hay `File.type` từ browser
là bằng chứng file an toàn.

Test tối thiểu khi thêm/sửa upload:

- feature orchestration gọi create -> PUT -> complete đúng thứ tự và chỉ complete sau PUT;
- helper PUT dùng exact method/headers, binary body và `credentials: "omit"`;
- lỗi network/CORS khác non-2xx storage và khác `ApiError` FastAPI;
- URL hết hạn/retry không tái sử dụng session cũ;
- cancel/abort và double-submit không gọi complete sai;
- file đã crop/convert dùng metadata khớp binary cuối cùng;
- UI chỉ báo success sau complete và render public URL từ response backend.

Không gọi RustFS thật trong unit/component test. Mock FastAPI boundary và storage `fetch`
riêng; luồng browser thật với CORS thuộc E2E/integration environment.

### Background job và API `202 Accepted`

Các tác vụ AI, CV extraction, transcription, report hoặc xử lý file dài được FastAPI/Celery thực hiện bất đồng bộ.

Frontend phải hỗ trợ contract tương đương:

```json
{
  "job_id": "...",
  "status": "pending",
  "resource_id": "..."
}
```

Quy tắc:

- `202 Accepted` nghĩa là request đã được nhận, không có nghĩa tác vụ đã hoàn thành.
- Lưu server state của job trong TanStack Query, không lưu bản sao authoritative trong Zustand.
- Polling phải có interval/backoff hợp lý và dừng ở trạng thái terminal.
- Nếu backend có SSE/WebSocket, dùng abstraction realtime chung; không tạo connection riêng cho từng component con.
- Hỗ trợ tối thiểu các trạng thái `pending`, `running`, `succeeded` và `failed` theo contract thực tế.
- Khi job hoàn thành, invalidate resource query liên quan thay vì tự ghép dữ liệu đoán trước.
- Không retry command tạo job một cách mù quáng; dùng idempotency contract nếu backend cung cấp.

## 11. TanStack Query

> **Scope:** Chuẩn mực quản lý server state bằng TanStack Query, xây dựng query-key factory bắt buộc scoped theo tenant và quy tắc invalidation.
>
> **Keywords:** `TanStack Query`, `queryKey`, `query-key factory`, `organization_id`, `invalidation`, `mutation`, `cache isolation`

TanStack Query chỉ quản lý server state.

Mỗi feature nên định nghĩa query-key factory ổn định:

```ts
export const userKeys = {
  all: (organizationId: string) =>
    ["organizations", organizationId, "users"] as const,
  lists: (organizationId: string) =>
    [...userKeys.all(organizationId), "list"] as const,
  list: (organizationId: string, params: GetUsersParams) =>
    [...userKeys.lists(organizationId), params] as const,
  details: (organizationId: string) =>
    [...userKeys.all(organizationId), "detail"] as const,
  detail: (organizationId: string, id: string) =>
    [...userKeys.details(organizationId), id] as const,
};
```

Quy tắc:

- Query key phải chứa mọi tham số ảnh hưởng kết quả.
- Query thuộc tenant bắt buộc chứa `organization_id` hoặc organization key tương đương.
- Query global chỉ được bỏ organization khỏi key khi backend contract xác định resource đó thật sự global.
- Không dùng query key kiểu `["candidates", params]` cho dữ liệu tenant-aware.
- Khi đổi organization, cancel request cũ và remove/invalidate cache tenant cũ theo security/UX policy trước khi render dữ liệu tenant mới.
- Mutation phải dùng organization context đang được backend xác thực; không lấy organization_id tùy ý từ form.
- Query function phải hỗ trợ abort signal khi hợp lý.
- Invalidate đúng phạm vi sau mutation.
- Không gọi `refetch` thủ công nếu invalidation giải quyết đúng hơn.
- Không cache cùng resource đồng thời trong TanStack Query và Zustand.
- Chỉ optimistic update khi rollback và conflict behavior đã được xác định.
- Không retry vô hạn; không retry lỗi `4xx` không thể tự hồi phục.

### `staleTime`: danh mục thì dài, nghiệp vụ thì ngắn

Mặc định của cả ứng dụng là **30 giây** (`app/providers.tsx`): rời màn rồi quay
lại sau đó là gọi lại. Đúng cho dữ liệu nghiệp vụ, sai cho danh mục tham chiếu.

| Loại dữ liệu | `staleTime` | Lý do |
| --- | --- | --- |
| Danh mục tham chiếu: vị trí, nguồn tuyển, loại hợp đồng, nơi làm việc, quy trình, cây đơn vị | `CATALOG_STALE_TIME` (`@/lib/query-cache`) | Hàng tháng mới đổi |
| Danh sách nghiệp vụ: yêu cầu, ứng viên, offer, lượt ứng tuyển | 30 giây — **giữ mặc định** | Nhiều người cùng sửa |
| Chi tiết một bản ghi đang xem | 30 giây — **giữ mặc định** | nt |
| Dữ liệu vừa sửa xong | `invalidate`, không dựa `staleTime` | Phải thấy ngay |

Quy tắc:

- **Không** tăng `staleTime` cho dữ liệu nghiệp vụ. Hai người cùng xử lý một hồ
  sơ mà thấy trạng thái cũ là lỗi nghiệp vụ, không phải đánh đổi hiệu năng.
- Dùng hằng `CATALOG_STALE_TIME`, đừng rải `10 * 60_000` khắp nơi: đổi chính sách
  thì phải đổi được ở **một** chỗ.
- Mỗi mutation sửa danh mục phải `invalidate` — nếu không, với `staleTime` dài,
  người vừa thêm một vị trí có thể không thấy nó trong ô chọn.
- Query **gộp** nhiều loại dữ liệu lấy theo loại ngắn nhất. Ví dụ
  `applications/filter-options` mang cả danh mục vị trí lẫn danh sách yêu cầu nên
  giữ 30 giây; `requisitions/form-options` chỉ mang danh mục nên dùng hằng trên.
- Đổi khoá của một query gộp thì **đi tìm mọi `invalidateQueries` trỏ vào khoá
  cũ**. Khoá cũ không còn ai đọc nên lệnh làm mới cũng không còn tác dụng, và
  không có gì đỏ để báo (L-09).

## 12. Zustand

> **Scope:** Giới hạn phạm vi sử dụng Zustand cho trạng thái client-only, lưu trữ ngữ cảnh UI và cấm trùng lặp server state.
>
> **Keywords:** `Zustand`, `client state`, `UI shell`, `organization switcher`, `no server state`, `selectors`

Chỉ dùng Zustand nếu state:

- Là client-only.
- Cần chia sẻ giữa component/route xa nhau.
- Không phải dữ liệu nguồn từ API.
- Không được giải quyết đơn giản hơn bằng URL, React state hoặc context cục bộ.

Ưu tiên lưu filter/search/sort có thể chia sẻ hoặc bookmark vào URL search params thay vì global store.

Store phải nhỏ, theo concern, có selector để hạn chế re-render. Không tạo một global store khổng lồ chứa toàn bộ app.

Nếu organization đang chọn được lưu trong Zustand:

- Store chỉ giữ ID/context lựa chọn cho UI, không giữ bản sao dữ liệu organization authoritative.
- Organization phải thuộc danh sách membership do FastAPI trả về.
- Khi chuyển organization, reset state tạm thời có tenant scope và phối hợp TanStack Query để không hiển thị cache tenant cũ.
- Không persist dữ liệu nhạy cảm hoặc toàn bộ permission payload lâu dài nếu không có lý do rõ.
- Backend vẫn resolve và kiểm tra membership/organization ở mọi request.

## 13. Form và Zod

> **Scope:** Quản lý biểu mẫu người dùng qua React Hook Form, kiểm thực dữ liệu bằng Zod và đồng bộ lỗi xác thực 422 từ backend Pydantic.
>
> **Keywords:** `React Hook Form`, `Zod`, `validation`, `422 field error`, `double submit prevention`, `form UX`

- React Hook Form quản lý form state.
- Zod cung cấp client-side validation và type inference cho dữ liệu form.
- Schema thuộc feature đặt trong `features/<feature>/schemas`.
- Schema dùng chung chỉ đưa ra shared khi thực sự domain-agnostic.
- Backend Pydantic vẫn là validation authority.
- Map FastAPI `422` field errors về đúng field khi contract hỗ trợ.
- Disable hoặc hiển thị pending state khi submit; tránh double submit.
- Không xóa dữ liệu người dùng nhập khi request thất bại.
- Xác nhận rõ với action destructive.

Không cố chia sẻ trực tiếp Zod schema với Pydantic bằng copy/paste. OpenAPI dùng để đồng bộ request/response contract; frontend có thể có validation UX chặt hoặc thân thiện hơn nhưng không được mâu thuẫn với backend.

## 14. Authentication và authorization

> **Scope:** Tương tác với hệ thống xác thực FastAPI, quản lý phiên qua cookie HttpOnly, bảo vệ redirect và kiểm soát quyền hiển thị UI.
>
> **Keywords:** `auth endpoints`, `HttpOnly cookie`, `session expiry`, `PermissionGate`, `open redirect protection`, `401 refresh`

FastAPI cung cấp tối thiểu các endpoint tương đương:

```text
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

Frontend:

- Không log token, cookie hoặc credential.
- Không lưu secret trong biến `NEXT_PUBLIC_*`.
- Không dùng client-side permission làm bảo mật.
- Xử lý refresh/session expiry theo một cơ chế tập trung, tránh mỗi feature tự làm.
- Không tạo refresh storm khi nhiều request cùng trả `401`.
- Redirect login phải tránh open redirect; chỉ chấp nhận URL nội bộ đã validate.
- UI permission dùng primitive/hook chung như `PermissionGate` hoặc `useCan` nếu đã tồn tại.

Backend:

- Xác thực request.
- Kiểm tra RBAC, organization scope và ownership.
- Trả mã lỗi nhất quán.
- Không tin `organization_id`, `role` hoặc permission chỉ vì frontend gửi lên.

## 15. Styling và design system

> **Scope:** Quy chuẩn xây dựng giao diện với Tailwind CSS, quản lý class qua cn(), mở rộng shadcn/ui và bảo đảm chuẩn tiếp cận (accessibility).
>
> **Keywords:** `Tailwind CSS`, `cn()`, `design tokens`, `shadcn/ui`, `dark mode`, `accessibility`, `variants`

- Dùng Tailwind theo tokens/theme của dự án.
- Dùng `cn()` chung để merge class names.
- Ưu tiên component variant bằng pattern hiện có; không tự tạo utility cạnh tranh.
- Không hard-code màu khi design token tương ứng đã có.
- Không trộn nhiều design systems.
- Responsive, dark mode và accessibility phải theo convention hiện hữu.
- Khi cần component shadcn mới, kiểm tra `components/ui` trước khi thêm.
- Không chỉnh base primitive theo cách phá vỡ consumer cũ; bổ sung variant hoặc wrapper nếu phù hợp hơn.

## 16. Testing

> **Scope:** Chiến lược kiểm thử đa tầng cho frontend bao gồm unit tests (Vitest), component tests (RTL) và E2E flows (Playwright).
>
> **Keywords:** `Vitest`, `React Testing Library`, `Playwright`, `E2E tests`, `regression tests`, `tenant switch test`

### Test đúng cấp độ

- Utility/schema/query-key: Vitest unit test.
- Component behavior: React Testing Library.
- Luồng người dùng quan trọng: Playwright.
- API business rule và permission: backend Pytest, không chỉ test ở frontend.

Ưu tiên test hành vi quan sát được, không test implementation detail.

Các luồng quan trọng cần E2E khi thay đổi liên quan:

- Login/logout/session expiry.
- Tạo/sửa/xóa user.
- Chuyển organization.
- Permission denied.
- Tạo job và candidate workflow.
- Upload file bằng presigned URL, confirm với FastAPI và xử lý URL hết hạn.
- Tác vụ AI/background job: `202 Accepted`, polling/realtime và trạng thái terminal.
- Chuyển từ organization A sang B không hiển thị dữ liệu/cache của A.
- Query, mutation và permission UI được scope theo organization hiện tại.

Mỗi bug fix nên có regression test ở cấp thấp nhất có thể tái hiện lỗi một cách đáng tin cậy.

Không snapshot cả page lớn nếu assertion hành vi cụ thể rõ ràng hơn.

## 17. Performance

> **Scope:** Các biện pháp tối ưu tốc độ tải và khả năng phản hồi của giao diện, tối ưu hoá bundle Next.js và loại bỏ gọi API dư thừa.
>
> **Keywords:** `performance`, `dynamic import`, `debounce`, `N+1 requests`, `bundle size`, `useMemo`, `image optimization`

- Không thêm `"use client"` quá cao trong cây component.
- Dynamic import component nặng chỉ khi có lợi đo được hoặc rõ ràng.
- Dùng Next.js Image cho ảnh phù hợp.
- Tránh gửi toàn bộ dataset nếu backend hỗ trợ pagination/filter.
- Debounce search input bằng hook chung; request cũ phải có khả năng bị abort.
- Tránh N+1 API calls từ list item.
- Không memo hóa mọi thứ theo thói quen; chỉ dùng khi có lý do.
- Theo dõi bundle impact trước khi thêm dependency lớn.
- `package.json` khai báo `"sideEffects": ["*.css"]`: bundler bỏ export không dùng của file gom `features/*/index.ts`, nên trang chỉ tải màn hình nó thật sự dùng (đo 19/10/2026: tổng JS ban đầu của 59 trang giảm 44%, trình soạn email chỉ còn ở 5 trang cần nó). Hệ quả: **không** viết `import "./x"` chỉ để lấy tác dụng phụ (đăng ký, polyfill); module cần chạy khi nạp phải được dùng qua một export. `src/lib/side-effects.test.ts` chặn cả hai.
- Đo JS tải ban đầu theo trang bằng bản build riêng, không đụng dev server: `NEXT_DIST_DIR=.next-measure pnpm build`, rồi đọc `entryJSFiles` trong `server/app/**/page_client-reference-manifest.js`. Xoá thư mục đo và hoàn tác `tsconfig.json` (Next tự thêm đường dẫn types) sau khi đo.

## 18. Security

> **Scope:** Nguyên tắc bảo mật bắt buộc phía frontend: bảo vệ biến môi trường, chống rò rỉ presigned URL, chống XSS và tuân thủ CORS/CSRF.
>
> **Keywords:** `security`, `NEXT_PUBLIC_`, `dangerouslySetInnerHTML`, `presigned URL safety`, `CSRF`, `CORS`, `sanitization`

- Không commit secret, token, password hoặc file `.env` thật.
- Chỉ biến môi trường công khai mới được đặt tiền tố `NEXT_PUBLIC_`.
- Không render HTML không tin cậy bằng `dangerouslySetInnerHTML` nếu chưa sanitize.
- Validate file type/size ở frontend cho UX và backend cho security.
- Không đưa RustFS/S3 access key hoặc secret key vào frontend hay biến `NEXT_PUBLIC_*`.
- Không log, đưa vào analytics hoặc persist presigned URL.
- Không gửi app cookie, bearer token hoặc organization credential tới presigned URL;
  storage upload phải dùng `credentials: "omit"` và chỉ dùng header được ký.
- Không đưa thông tin nhạy cảm vào URL/query string.
- Không lộ internal error detail cho người dùng.
- Tôn trọng CSRF/CORS/cookie policy đã thiết kế với FastAPI.
- Mọi destructive action phải có authorization backend và confirmation UX phù hợp.
- Màn lịch sử (nhật ký thao tác) chỉ hiện những gì API trả về; không tự tái dựng
  giá trị đã bị backend che (field `redacted`, `note = null` của dòng offer). Luật
  ở `backend/AGENTS.md` mục 22 "Nhật ký thao tác" và `docs/audit_log/05-frontend.md`.

## 19. Chất lượng code

> **Scope:** Tiêu chuẩn chất lượng mã nguồn TypeScript ở chế độ strict mode, quy tắc bảo toàn lockfile pnpm và duy trì tính ổn định lâu dài.
>
> **Keywords:** `TypeScript strict`, `no any`, `no ts-ignore`, `clean code`, `pnpm-lock.yaml`, `backward compatibility`

- TypeScript strict; không dùng `any` nếu có thể biểu diễn type chính xác.
- Không dùng `@ts-ignore` để che lỗi. Nếu bất khả kháng, dùng directive hẹp kèm lý do.
- Không để dead code, commented-out code hoặc debug log.
- Function nhỏ, tên thể hiện ý định.
- Comment giải thích “vì sao”, không lặp lại “code làm gì”.
- Không refactor ngoài phạm vi nếu không cần để hoàn thành task.
- Giữ backward compatibility trừ khi task yêu cầu breaking change.
- Không thay đổi API contract ngầm. Mọi thay đổi contract phải đồng bộ backend, OpenAPI, generated code và consumer.
- Không sửa lockfile bằng package manager khác. Dự án dùng pnpm.

## 20. Lệnh kiểm tra

> **Scope:** Danh mục câu lệnh chuẩn cho quá trình kiểm tra cục bộ frontend: linting, kiểm tra kiểu, unit test, build và sinh mã OpenAPI.
>
> **Keywords:** `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`, `playwright`, `generate:api`

Agent phải đọc scripts thực tế trong `frontend/package.json` và `backend/pyproject.toml`; các lệnh dưới đây là convention dự kiến, không được phỏng đoán nếu repository dùng tên khác.

Frontend:

```bash
pnpm --dir frontend lint
pnpm --dir frontend typecheck
pnpm --dir frontend test
pnpm --dir frontend build
pnpm --dir frontend exec playwright test
```

Backend khi có thay đổi contract hoặc integration:

```bash
cd backend && uv run ruff check src tests
cd backend && uv run pyrefly check
cd backend && uv run pytest
```

OpenAPI/codegen, dùng script repository đã khai báo, ví dụ:

```bash
pnpm --dir frontend generate:api
```

Không chạy formatter trên toàn repository nếu task chỉ thay đổi ít file và việc đó có thể ghi đè thay đổi không liên quan. Chỉ format file đã sửa hoặc dùng script đã được project quy định.

## 21. Definition of Done

> **Scope:** Bảng kiểm tra nghiệm thu bắt buộc phải đạt được trước khi đánh dấu hoàn thành bất kỳ task frontend nào.
>
> **Keywords:** `Definition of Done`, `checklist`, `quality gates`, `verification`, `DoD`

Trước khi báo hoàn thành, agent phải xác nhận:

- [ ] Đã đọc `AGENTS.md` áp dụng và config liên quan.
- [ ] Đã tìm code dùng chung/implementation tương tự trước khi tạo mới.
- [ ] Không tạo component, hook, utility, type hoặc API wrapper trùng lặp.
- [ ] File mới nằm đúng feature/shared/lib layer.
- [ ] Không đưa business logic hoặc authorization authority vào frontend.
- [ ] API contract khớp FastAPI/OpenAPI.
- [ ] Không sửa file generated bằng tay.
- [ ] Query key tenant-aware có `organization_id`.
- [ ] Chuyển organization không làm lộ cache/state của tenant trước.
- [ ] Upload dùng FastAPI presigned flow và không lộ RustFS credential.
- [ ] Presigned PUT dùng shared helper, exact signed headers và `credentials: "omit"`.
- [ ] Frontend không tự dựng bucket/object key/public URL hoặc gửi field nội bộ storage.
- [ ] Metadata create/complete khớp đúng binary cuối cùng sau crop/convert.
- [ ] UI chỉ báo upload thành công sau FastAPI complete; lỗi API/storage được phân biệt.
- [ ] Luồng `202 Accepted` không bị coi nhầm là hoàn tất.
- [ ] Có loading/error/empty/success state khi phù hợp.
- [ ] Có kiểm tra accessibility cơ bản.
- [ ] Có test mới hoặc cập nhật test khi behavior thay đổi.
- [ ] Lint và typecheck đã pass cho phạm vi thay đổi.
- [ ] Test liên quan đã pass.
- [ ] Build đã được chạy khi thay đổi có rủi ro build/runtime hoặc trước release.
- [ ] Không lộ secret hoặc dữ liệu nhạy cảm.
- [ ] Không sửa file không liên quan.

Nếu không thể chạy một bước kiểm tra, agent phải nói rõ bước nào chưa chạy và lý do. Không được nói “đã hoàn thành” khi verification quan trọng vẫn thất bại.

## 22. Những anti-pattern bị cấm

> **Scope:** Danh mục chi tiết các mẫu thiết kế sai lệch (anti-patterns), cấu trúc bị cấm kỵ về quản lý state, API và bảo mật frontend.
>
> **Keywords:** `anti-patterns`, `forbidden practices`, `architectural violations`, `security risks`

- Tạo `components/` khổng lồ chứa component của mọi domain.
- Tạo `services/`, `hooks/`, `schemas/`, `types/` toàn cục chứa toàn bộ domain.
- Viết raw `fetch` trực tiếp trong nhiều component.
- Copy một utility rồi đổi tên.
- Tự định nghĩa lại type đã có trong OpenAPI generated code.
- Lưu server state vào Zustand.
- Dùng query key tenant-aware nhưng thiếu `organization_id`.
- Giữ hoặc hiển thị cache của organization trước sau khi chuyển tenant.
- Đưa business rule hoặc permission authority vào Next.js.
- Dùng `useEffect` để đồng bộ state có thể derive trực tiếp.
- Đặt mọi component thành Client Component.
- Feature import vòng lặp hoặc import sâu implementation private của feature khác.
- Sửa code generated bằng tay.
- Suy luận API response trực tiếp từ `backend/src/app/database/generated_tables.py`.
- Đưa RustFS/S3 credential vào frontend.
- Persist hoặc log presigned URL.
- Gửi app cookie/Authorization header tới presigned URL hoặc upload storage qua API client.
- Tự nối API base URL, sửa query string hoặc thêm header ngoài presigned contract.
- Tự dựng public/private URL từ bucket, object key hoặc `file_id` ở frontend.
- Coi PUT storage thành công là hoàn tất trước khi FastAPI complete thành công.
- Dùng metadata file gốc khi binary đã được crop/compress/convert.
- Gộp lỗi CORS/storage thành lỗi “không kết nối được backend”.
- Coi response `202 Accepted` là tác vụ đã hoàn thành.
- Thêm package trùng chức năng mà chưa kiểm tra dependency hiện có.
- Bỏ qua error/loading/empty state.
- Catch error rồi im lặng.
- Dùng `any`, `@ts-ignore` hoặc type assertion chỉ để làm typecheck pass.
- Gộp refactor diện rộng vào một task nhỏ mà không có lý do.

## 23. Mẫu báo cáo cuối task của agent

> **Scope:** Mẫu khung định dạng chuẩn dùng để báo cáo ngắn gọn kết quả hoàn thành task, tài nguyên tái sử dụng và trạng thái kiểm tra thực tế.
>
> **Keywords:** `report format`, `task summary`, `verification report`, `final report`

Khi hoàn thành một task code, báo cáo ngắn gọn theo cấu trúc:

```text
Kết quả
- Behavior đã thêm hoặc sửa.

Tái sử dụng
- Component/hook/utility/API abstraction đã dùng lại.

Files
- Các file chính đã thay đổi.

Kiểm tra
- lint: pass/fail/not run
- typecheck: pass/fail/not run
- tests: pass/fail/not run
- build: pass/fail/not run

Lưu ý
- Migration, contract change, rủi ro hoặc bước tiếp theo nếu có.
```

Không liệt kê dài dòng mọi thao tác. Dẫn đầu bằng kết quả và nêu rõ verification thực tế.
