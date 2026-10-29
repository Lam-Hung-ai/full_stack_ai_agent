# AGENTS.md — Backend

## Contents & Navigation

- [1. Mục đích và phạm vi](#1-mục-đích-và-phạm-vi) — Phạm vi áp dụng, đối tượng và kiến trúc tổng quan của backend. Keywords: `modular monolith`, `FastAPI`, `PostgreSQL`, `Celery`, `RustFS`.
- [2. Tuyên ngôn kiến trúc](#2-tuyên-ngôn-kiến-trúc) — 15 nguyên tắc kiến trúc cốt lõi định hình ranh giới domain, tenant isolation và database workflow. Keywords: `principles`, `domain-driven`, `tenant isolation`, `generated_tables`.
- [3. Tech stack đã chốt](#3-tech-stack-đã-chốt) — Danh mục công nghệ chính thức cho runtime, database, infrastructure, auth và testing. Keywords: `Python 3.13`, `FastAPI`, `SQLAlchemy 2`, `PostgreSQL`, `uv`, `Ruff`, `pytest`.
- [4. Cấu trúc repository chuẩn](#4-cấu-trúc-repository-chuẩn) — Cây thư mục dự án và phân định vị trí giữa app, modules, common, config, database, tools và tests. Keywords: `folder structure`, `src/app`, `modules`, `common`, `config`, `database`, `tools`, `tests`.
- [5. Luồng xử lý chuẩn](#5-luồng-xử-lý-chuẩn) — Chu trình xử lý request từ router qua dependencies, service, repository đến database. Keywords: `request flow`, `Router`, `Service`, `Repository`, `two-layer authorization`.
- [6. Ranh giới module và aggregate](#6-ranh-giới-module-và-aggregate) — Tiêu chí phân định domain module, aggregate root và quan hệ với các module nền tảng. Keywords: `aggregate root`, `module boundary`, `candidates`, `interviews`, `foundation modules`.
- [7. Cấu trúc chuẩn của mỗi module](#7-cấu-trúc-chuẩn-của-mỗi-module) — Tổ chức nội bộ tối thiểu và điều kiện mở rộng thành package cho từng feature. Keywords: `router.py`, `schemas.py`, `service.py`, `repository.py`.
- [8. Trách nhiệm từng layer](#8-trách-nhiệm-từng-layer) — Phân định quyền hạn và điều cấm đối với router.py, schemas.py, service.py và repository.py. Keywords: `Router`, `Schemas`, `Service`, `Repository`, `DTO`, `AsyncSession`.
- [9. Database schema là nguồn sự thật](#9-database-schema-là-nguồn-sự-thật) — Quy chuẩn quản lý PostgreSQL schema, migrations và file tự sinh generated_tables.py. Keywords: `source of truth`, `migration`, `generated_tables.py`, `dbmate`, `unique constraints`.
- [10. Database session và transaction](#10-database-session-và-transaction) — Quản lý vòng đời AsyncSession, ranh giới transaction do Service sở hữu và concurrency. Keywords: `AsyncSession`, `transaction boundary`, `session.begin`, `SELECT FOR UPDATE`, `concurrency`.
- [11. Tenant isolation theo organization_id](#11-tenant-isolation-theo-organization_id) — Yêu cầu bảo mật cô lập tenant bắt buộc trong query, insert, join và security tests. Keywords: `organization_id`, `tenant isolation`, `multi-tenant`, `test_isolation.py`, `RLS`.
- [12. Authentication](#12-authentication) — Cơ chế xác thực trung tâm tại FastAPI, quản lý token, cookie HttpOnly và hash mật khẩu. Keywords: `login`, `logout`, `refresh token`, `cookie`, `HttpOnly`, `password hash`.
- [13. Authorization](#13-authorization) — Mô hình phân quyền RBAC kết hợp organization scope, permission naming và HTTP 401/403. Keywords: `RBAC`, `permissions`, `roles`, `organization scope`, `HTTP 401`, `HTTP 403`.
- [14. Shared code và quy tắc reuse-first](#14-shared-code-và-quy-tắc-reuse-first) — Thứ tự tìm kiếm mã nguồn hiện có, tiêu chí phân bổ file và chuẩn mực thư mục common. Keywords: `reuse-first`, `app/common`, `ripgrep search`, `code location`.
- [15. config, database, common và tools](#15-config-database-common-và-tools) — Vai trò, giới hạn hoạt động và trách nhiệm của 4 thư mục nền tảng. Keywords: `config`, `database`, `common`, `tools`, `pydantic-settings`.
- [16. API contract](#16-api-contract) — Chuẩn thiết kế REST API, versioning /api/v1, định dạng lỗi chuẩn, phân trang và OpenAPI. Keywords: `REST API`, `/api/v1`, `HTTP status codes`, `error format`, `pagination`, `OpenAPI`.
- [17. RustFS và object storage](#17-rustfs-và-object-storage) — Contract chuẩn cho metadata `stored_files`, object key, public/private access, presigned upload và vòng đời file. Keywords: `RustFS`, `stored_files`, `file_id`, `presigned URL`, `object_key`, `public`, `private`.
- [18. Redis, Celery và background jobs](#18-redis-celery-và-background-jobs) — Kiến trúc xử lý tác vụ nền, giới hạn payload, bảo vệ transaction và hành vi worker. Keywords: `Celery`, `Redis`, `background jobs`, `job payload`, `idempotency`, `after-commit`.
- [19. Email và external integrations](#19-email-và-external-integrations) — Giao tiếp dịch vụ bên ngoài qua adapter, timeout, retry và bảo vệ transaction DB. Keywords: `external integration`, `email`, `timeout`, `retry`, `circuit breaker`.
- [20. Logging và observability](#20-logging-và-observability) — Chuẩn hóa structured JSON logging, gắn context request_id, tracing, metrics và chống lộ PII. Keywords: `structured logging`, `request_id`, `correlation_id`, `PII`, `observability`.
- [21. Cấu hình và secrets](#21-cấu-hình-và-secrets) — Quản lý cấu hình qua pydantic-settings, quy chuẩn .env/.env.example và bảo vệ secret. Keywords: `settings.py`, `pydantic-settings`, `.env`, `.env.example`, `secrets management`.
- [22. Security](#22-security) — Phòng thủ đa tầng: input validation, parameterized query, SSRF protection, scan upload và audit log. Keywords: `security`, `parameterized SQL`, `SSRF`, `file validation`, `audit logging`.
- [23. Naming và coding conventions](#23-naming-và-coding-conventions) — Quy ước đặt tên mã nguồn Python, kiến trúc class vs pure function và quy chuẩn typing. Keywords: `snake_case`, `PascalCase`, `AsyncSession`, `typing`, `Protocol`, `Ruff`.
- [24. Quy trình bắt buộc trước khi viết code](#24-quy-trình-bắt-buộc-trước-khi-viết-code) — Quy trình 8 bước bắt buộc từ khảo sát repository đến triển khai và nghiệm thu. Keywords: `workflow`, `8 steps`, `survey codebase`, `reuse check`, `schema check`.
- [25. Testing — cấu trúc hiện tại](#25-testing--cấu-trúc-hiện-tại) — Phân tầng kiểm thử hiện tại: api, integration, security và nguyên tắc dùng fixture. Keywords: `tests structure`, `fixtures`, `api tests`, `integration tests`, `security tests`.
- [26. Testing — ownership và mở rộng cấu trúc](#26-testing--ownership-và-mở-rộng-cấu-trúc) — Phân định quyền sở hữu của các file fixture và nguyên tắc mở rộng test suite an toàn. Keywords: `fixtures/database.py`, `fixtures/auth.py`, `factories.py`, `test expansion`.
- [27. Test data và factories](#27-test-data-và-factories) — Khởi tạo dữ liệu mẫu độc lập, thiết lập đa tenant A/B và dọn dẹp database sau test. Keywords: `test data`, `factories`, `multi-tenant testing`, `database cleanup`.
- [28. Background job tests](#28-background-job-tests) — Chiến lược kiểm thử Celery task: handler logic, commit enqueue, idempotency và error handling. Keywords: `Celery testing`, `worker tests`, `idempotency test`, `retry test`.
- [29. Database migration rules](#29-database-migration-rules) — Quy chuẩn viết migration SQL thuần bằng dbmate, diễn tập trên database dùng một lần, đánh giá DDL lock, backfill dữ liệu và regenerate code. Keywords: `dbmate`, `dry run`, `migrations`, `DDL locks`, `backfill`.
- [30. Performance](#30-performance) — Tối ưu truy vấn SQL, chống N+1, quản lý memory khi xử lý file và chiến lược cache tenant-aware. Keywords: `performance`, `SQL query optimization`, `N+1 queries`, `file streaming`, `caching`.
- [31. Code quality và dependency management](#31-code-quality-và-dependency-management) — Quản lý dependency bằng uv, kiểm soát file uv.lock và chính sách chất lượng mã nguồn. Keywords: `uv`, `pyproject.toml`, `uv.lock`, `dependency management`.
- [32. Lệnh kiểm tra](#32-lệnh-kiểm-tra) — Bộ lệnh chuẩn cho kiểm tra linting, format, typecheck, unit/integration test và pre-commit. Keywords: `uv sync`, `ruff check`, `ruff format`, `pyrefly`, `pytest`, `pre-commit`.
- [33. Definition of Done](#33-definition-of-done) — Bảng kiểm (checklist) 28 tiêu chí bắt buộc trước khi bàn giao bất kỳ task backend nào. Keywords: `Definition of Done`, `checklist`, `quality gates`, `verification`.
- [34. Anti-pattern bị cấm](#34-anti-pattern-bị-cấm) — Danh mục 32 hành vi, cấu trúc và thói quen kỹ thuật bị cấm tuyệt đối trong backend. Keywords: `anti-patterns`, `forbidden practices`, `architectural violations`, `security risks`.
- [35. Mẫu báo cáo cuối task](#35-mẫu-báo-cáo-cuối-task) — Khung cấu trúc chuẩn để báo cáo kết quả thực hiện, kiến trúc, kiểm tra và các lưu ý kỹ thuật. Keywords: `report format`, `task summary`, `verification report`, `final report`.

---

## 1. Mục đích và phạm vi

> **Scope:** Quy chuẩn kỹ thuật bắt buộc cho AI coding agent và developer trên toàn bộ backend modular monolith.
>
> **Keywords:** `modular monolith`, `FastAPI`, `PostgreSQL`, `Celery`, `RustFS`, `Next.js`

File này là quy chuẩn bắt buộc cho mọi AI coding agent và developer khi làm việc trong thư mục backend.

Backend được xây dựng theo mô hình modular monolith, tổ chức theo domain và lấy cảm hứng từ module của NestJS nhưng triển khai bằng FastAPI:

~~~text
Mỗi feature tự đóng gói:

API
DTO
Business logic
Authorization
Database queries
Tests
~~~

Kiến trúc tổng thể:

~~~text
Client
  -> Next.js frontend
  -> FastAPI REST API
  -> PostgreSQL
  -> Redis / Celery
  -> RustFS qua S3-compatible API
~~~

Phạm vi áp dụng:

- Tất cả code trong backend/.
- API contract mà frontend sử dụng.
- Database access và generated table definitions.
- Authentication, organization context và authorization.
- Background jobs, file storage và integration phía backend.
- Tests cho backend.

Nếu một thư mục con có AGENTS.md riêng, file gần code nhất được ưu tiên cho phần việc trong thư mục đó. Các quy tắc ở file cha vẫn có hiệu lực nếu file con không ghi đè rõ ràng.

## 2. Tuyên ngôn kiến trúc

> **Scope:** 15 nguyên tắc kiến trúc bất biến định hình ranh giới domain, tenant isolation và database workflow.
>
> **Keywords:** `principles`, `domain-driven`, `tenant isolation`, `generated_tables`, `modular monolith`

> Xây dựng backend modular monolith theo domain, mang phong cách NestJS nhưng triển khai bằng FastAPI; mỗi feature tự đóng gói API, DTO, nghiệp vụ và truy vấn, trong khi authentication, tenant isolation, authorization và database schema được dùng chung một cách nhất quán.

Các nguyên tắc không được phá vỡ:

1. Tổ chức code theo nghiệp vụ, không tổ chức toàn dự án theo technical layer.
2. Một module đại diện cho một domain hoặc aggregate có vòng đời nghiệp vụ chung.
3. Không mặc định mỗi bảng là một module.
4. Router chỉ xử lý HTTP và dependency injection.
5. Service điều phối nghiệp vụ, authorization và transaction.
6. Repository xây dựng và thực thi database query.
7. Schema là API DTO, tách biệt khỏi database table.
8. PostgreSQL schema là nguồn sự thật về cấu trúc dữ liệu.
9. Backend không định nghĩa lại ORM model trong từng module.
10. database/generated_tables.py được sinh tự động từ PostgreSQL schema và không được sửa bằng tay.
11. Tất cả dữ liệu nghiệp vụ phải được cô lập theo organization_id, trừ các bảng global được xác định rõ.
12. Thành phần dùng chung phải được tìm và tái sử dụng trước khi tạo mới.
13. Module tuyển dụng phải kế thừa auth, users, organizations, members và authorization hiện có; không tạo lại các khái niệm nền tảng.
14. Không tách microservice khi chưa có quyết định kiến trúc riêng.
15. Mọi thay đổi phải được kiểm tra bằng lint, typecheck và tests phù hợp.

## 3. Tech stack đã chốt

> **Scope:** Danh mục công nghệ, thư viện và công cụ được chuẩn hóa cho runtime, database, hạ tầng, kiểm thử và observability.
>
> **Keywords:** `Python 3.13`, `FastAPI`, `SQLAlchemy 2`, `PostgreSQL`, `uv`, `Ruff`, `Pyrefly`, `pytest`, `Celery`, `Redis`

### Runtime và API

- Python 3.13 trở lên.
- FastAPI.
- Uvicorn hoặc process runner được repository cấu hình.
- Pydantic v2.
- pydantic-settings cho cấu hình.
- REST API.
- OpenAPI do FastAPI sinh tự động.

### Database

- PostgreSQL là primary database.
- SQLAlchemy 2, ưu tiên API 2.x và async session.
- Migration là SQL thuần trong `db/migrations`, không dùng Alembic và không dùng
  ORM autogenerate. Quyết định này là chốt: schema dùng `GENERATED`, `ltree`,
  trigger và partial index, những thứ SQL diễn đạt trực tiếp và rõ hơn op-code.
- dbmate là migration runner: apply, rollback và theo dõi version đã chạy.
- Migration được diễn tập trên một PostgreSQL dùng một lần trước khi apply;
  không dùng linter schema ngoài (xem mục 29).
- PostgreSQL schema là source of truth.
- generated_tables.py được generate từ schema bằng `uv run db generate`.
- Không tạo ORM model thủ công cho từng module.

### Infrastructure

- Redis cho cache, distributed coordination, rate limit hoặc broker khi phù hợp.
- Celery cho background jobs.
- RustFS cho object storage thông qua S3-compatible API.
- Không lưu file binary lớn trực tiếp trong PostgreSQL.

### Authentication và authorization

- FastAPI là authentication authority.
- JWT hoặc session/token mechanism theo security contract của repository.
- Ưu tiên HttpOnly, Secure, SameSite cookies cho browser client.
- RBAC kết hợp organization scope.
- Có thể mở rộng ABAC khi nghiệp vụ thực sự yêu cầu.

### Quality

- uv là package và environment manager.
- Ruff cho lint và format.
- Pyrefly cho static type checking.
- Pytest.
- pytest-asyncio.
- HTTPX cho API tests.
- pre-commit.

### Observability

- Structured JSON logging.
- Sentry cho error tracking nếu được cấu hình.
- OpenTelemetry cho traces/metrics khi được cấu hình.
- Prometheus/Grafana ở tầng hạ tầng khi cần.

Không tự ý thêm package trùng chức năng. Trước khi thêm dependency, bắt buộc kiểm tra pyproject.toml, uv.lock và implementation hiện có.

## 4. Cấu trúc repository chuẩn

> **Scope:** Cây thư mục định hướng và nguyên tắc phân định trách nhiệm giữa các gói app, modules, common, config, database, tools và tests.
>
> **Keywords:** `folder structure`, `src/app`, `modules`, `common`, `config`, `database`, `tools`, `tests`

~~~text
backend/
├── AGENTS.md
├── README.md
├── IMPLEMENTATION_PLAN.md
├── pyproject.toml
├── uv.lock
├── .env
├── .env.example
│
├── src/
│   └── app/
│       ├── main.py
│       │
│       ├── config/
│       │   ├── settings.py
│       │   ├── security.py
│       │   └── constants.py
│       │
│       ├── database/
│       │   ├── session.py
│       │   └── generated_tables.py
│       │
│       ├── common/
│       │   ├── dependencies/
│       │   │   ├── auth.py
│       │   │   ├── organization.py
│       │   │   └── permission.py
│       │   ├── exceptions/
│       │   │   └── handlers.py
│       │   ├── schemas/
│       │   │   └── common.py
│       │   ├── storage/
│       │   │   ├── client.py
│       │   │   └── schemas.py
│       │   ├── repository.py
│       │   └── email.py
│       │
│       ├── modules/
│       │   ├── auth/
│       │   ├── users/
│       │   ├── organizations/
│       │   ├── organization_units/
│       │   ├── members/
│       │   ├── authorization/
│       │   ├── candidates/
│       │   ├── jobs/
│       │   ├── applications/
│       │   └── interviews/
│       │
│       └── tools/
│           ├── database.py
│           ├── clean_schema.py
│           ├── org_import.py
│           └── iam.py
│
└── tests/
    ├── conftest.py
    ├── fixtures/
    ├── integration/
    ├── api/
    └── security/
~~~

Đây là kiến trúc định hướng. Agent phải kiểm tra repository thực tế trước khi tạo file hoặc folder. Không tạo một cây thư mục song song chỉ vì tên hiện tại khác ví dụ trên.

Không commit file .env chứa secret. Chỉ .env.example với giá trị mẫu an toàn được phép đưa vào source control.

## 5. Luồng xử lý chuẩn

> **Scope:** Chu trình luân chuyển request qua các tầng Router, Dependencies, Service, Repository và mô hình phân quyền hai lớp.
>
> **Keywords:** `request flow`, `Router`, `Service`, `Repository`, `two-layer authorization`, `dependency injection`

Mọi request nghiệp vụ đi theo luồng:

~~~text
Request
  -> Router
  -> Authentication dependency
  -> Organization/Tenant dependency
  -> Service
  -> Repository
  -> PostgreSQL
~~~

Authorization có hai lớp:

1. Dependency có thể thực hiện coarse-grained guard như bắt buộc đăng nhập, resolve organization context hoặc kiểm tra permission chung.
2. Service bắt buộc kiểm tra business permission, ownership, trạng thái tài nguyên và các điều kiện nghiệp vụ.

Không gọi repository trực tiếp từ router cho endpoint nghiệp vụ chỉ vì operation đơn giản. Service vẫn là ranh giới use case và transaction.

Không để service gọi router. Không để repository phụ thuộc FastAPI.

## 6. Ranh giới module và aggregate

> **Scope:** Tiêu chí phân định domain module theo aggregate root, vòng đời nghiệp vụ và nguyên tắc phụ thuộc một chiều với các module nền tảng.
>
> **Keywords:** `aggregate root`, `module boundary`, `candidates`, `interviews`, `foundation modules`, `single direction`

### Module không đồng nghĩa với table

Một module đại diện cho một domain hoặc aggregate có vòng đời nghiệp vụ chung.

Ví dụ candidates sở hữu:

~~~text
candidates/
├── candidates
├── candidate_documents
├── cv_extractions
├── candidate_educations
├── candidate_experiences
└── candidate_duplicates
~~~

Ví dụ interviews sở hữu:

~~~text
interviews/
├── interviews
├── interview_participants
└── interview_feedbacks
~~~

Không tách candidate_documents hoặc interview_feedbacks thành module độc lập nếu chúng:

- Không có vòng đời độc lập.
- Luôn được truy cập thông qua aggregate cha.
- Chia sẻ permission và transaction với tài nguyên cha.
- Không có API/use case độc lập rõ ràng.

### Khi nào nên tạo module mới

Chỉ tạo module mới khi phần nghiệp vụ:

- Có vòng đời độc lập.
- Có API/use cases riêng.
- Có permission policy riêng.
- Có transaction boundary tương đối độc lập.
- Có khả năng phát triển mà không cần biết implementation nội bộ của module khác.

### Module nền tảng

Các module đã chốt:

~~~text
auth
users
organizations
organization_units
members
authorization
~~~

Các module mới phải sử dụng lại những module trên.

Không có module `invitations`: không dùng luồng thư mời. Admin tạo `users`, tạo
`organization_members`, rồi gán `member_role_assignments`; lần đăng nhập đầu đi
qua `verifications` với `purpose = 'password_reset'`.

Ví dụ:

- Candidate liên kết user nếu nghiệp vụ cần, không tạo bảng user mới.
- Job thuộc organization hiện có, không tạo organization kiểu tuyển dụng.
- Interview participant tham chiếu member/user/candidate thích hợp, không tạo identity system riêng.
- Permission mới được đăng ký trong authorization hiện có, không tạo role table riêng theo SQL cũ.

### Phụ thuộc giữa module

Ưu tiên dependency một chiều và public contract rõ ràng.

Không import repository nội bộ của module khác để né service. Khi một use case cần dữ liệu module khác:

1. Gọi public service/query interface của module sở hữu dữ liệu.
2. Tạo orchestration service ở module sở hữu use case.
3. Extract một shared policy/value object nếu nó thật sự dùng chung.
4. Với read query tổng hợp có yêu cầu hiệu năng, có thể join table qua repository của module sở hữu màn hình/query, nhưng phải tôn trọng ownership, tenant scope và không ghi dữ liệu module khác.

Không tạo circular dependency giữa modules.

## 7. Cấu trúc chuẩn của mỗi module

> **Scope:** Quy định cấu trúc tệp tối thiểu và ngưỡng phân tách thành package cho router, schemas, service và repository.
>
> **Keywords:** `router.py`, `schemas.py`, `service.py`, `repository.py`, `module structure`

Mỗi module tuân theo cấu trúc tối thiểu:

~~~text
modules/<feature>/
├── __init__.py
├── router.py
├── schemas.py
├── service.py
└── repository.py
~~~

Khi module lớn, được phép tách có chủ đích:

~~~text
modules/candidates/
├── __init__.py
├── router.py
├── schemas.py
├── service.py
├── repository.py
├── constants.py
├── exceptions.py
├── policies.py
├── mappers.py
└── tasks.py
~~~

Chỉ tạo file khi có nội dung thật sự. Không tạo hàng loạt file rỗng để giống template.

Không tạo models.py chứa ORM model. Database table definitions đến từ app.database.generated_tables.

Nếu schemas.py, service.py hoặc repository.py trở nên quá lớn, có thể chuyển sang package:

~~~text
modules/candidates/
├── router.py
├── schemas/
│   ├── common.py
│   ├── requests.py
│   └── responses.py
├── services/
│   ├── candidate_service.py
│   └── document_service.py
└── repositories/
    ├── candidate_repository.py
    └── document_repository.py
~~~

Không tách sớm. Chỉ tách khi file lớn, có nhiều aggregate con hoặc có ranh giới trách nhiệm rõ.

## 8. Trách nhiệm từng layer

> **Scope:** Phân công trách nhiệm chi tiết và các giới hạn nghiêm ngặt của từng layer: router.py, schemas.py, service.py và repository.py.
>
> **Keywords:** `Router`, `Schemas`, `Service`, `Repository`, `DTO`, `AsyncSession`, `transaction boundary`

### 8.1 router.py

Router tương đương Controller trong NestJS.

Router được phép:

- Khai báo path, method, status code và response model.
- Nhận path/query/header/body.
- Inject database session và shared dependencies.
- Resolve current user và organization context.
- Gọi đúng service use case.
- Chuyển kết quả service sang response khi mapping chỉ thuộc HTTP.

Router không được:

- Viết SQL trừ các trường hợp query cực kỳ phức tạp mà sqlalchemy tạo không được hoặc chứa các câu lệnh đặc thù trong postgres mà sqlalchemy và sqlalchemy-utils không có.
- Gọi generated table trực tiếp.
- Chứa business rule.
- Tự commit/rollback transaction.
- Tự kiểm tra permission phức tạp.
- Gửi email hoặc gọi RustFS trực tiếp.
- Chứa retry logic.
- Trả raw database Row cho client.

Ví dụ:

~~~python
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies.auth import CurrentUser
from app.common.dependencies.organization import OrganizationContext
from app.database.session import get_session

from .schemas import CandidateCreate, CandidateResponse
from .service import CandidateService

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.post(
    "",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_candidate(
    payload: CandidateCreate,
    current_user: CurrentUser,
    organization: OrganizationContext,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CandidateResponse:
    service = CandidateService(session)
    return await service.create(
        payload=payload,
        actor=current_user,
        organization_id=organization.id,
    )
~~~

Ví dụ trên chỉ là pattern. Agent phải theo dependency types và constructor convention thực tế của repository.

### 8.2 schemas.py

Schema tương đương DTO:

- Validate request shape.
- Định nghĩa response contract.
- Generate OpenAPI.
- Tách API data khỏi database representation.

Naming đề xuất:

~~~text
CandidateCreate
CandidateUpdate
CandidateResponse
CandidateListItem
CandidateListResponse
CandidateFilter
~~~

Quy tắc:

- Dùng Pydantic v2 syntax.
- Không dùng database Table hoặc Row làm response model.
- Không để internal-only field, secret, password hash hoặc storage credential lọt vào response.
- Field optional trong update phải phân biệt rõ omitted và explicit null.
- Validation đơn giản về format/shape nằm ở schema.
- Validation cần database, permission hoặc business state nằm ở service.
- Dùng datetime timezone-aware.
- UUID ở Python dùng uuid.UUID.
- Decimal/money dùng Decimal hoặc integer minor units theo contract; không dùng float tùy tiện.

Ví dụ:

~~~python
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CandidateCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    email: EmailStr
    full_name: str
    created_at: datetime
~~~

Không dùng ConfigDict(from_attributes=True) theo thói quen nếu dữ liệu trả về là mapping và project có mapper riêng. Theo convention thực tế.

### 8.3 service.py

Service là nơi thực thi use case.

Service chịu trách nhiệm:

- Business rule.
- Authorization theo actor, permission, organization và resource ownership.
- Orchestrate một hoặc nhiều repository.
- Transaction boundary.
- Idempotency/business conflict.
- Domain exception.
- Điều phối integration như email, storage và task queue thông qua abstraction chung.
- Bảo đảm thay đổi nhiều bảng là atomic khi nghiệp vụ yêu cầu.

Service không được:

- Phụ thuộc Request/Response của FastAPI.
- Trả HTTPException trực tiếp nếu project dùng domain exception chung.
- Xây SQL phức tạp thay repository.
- Tự tạo database engine/session.
- Tin organization_id hoặc role do request body gửi lên.
- Commit rải rác nhiều lần trong một use case.

Ví dụ:

~~~python
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies.auth import CurrentUser
from app.common.exceptions import ConflictError, PermissionDeniedError

from .repository import CandidateRepository
from .schemas import CandidateCreate, CandidateResponse


class CandidateService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = CandidateRepository(session)

    async def create(
        self,
        *,
        payload: CandidateCreate,
        actor: CurrentUser,
        organization_id: UUID,
    ) -> CandidateResponse:
        if not actor.can("candidate:create", organization_id=organization_id):
            raise PermissionDeniedError(code="CANDIDATE_CREATE_FORBIDDEN")

        async with self._session.begin():
            existing = await self._repository.get_by_email(
                organization_id=organization_id,
                email=payload.email,
            )
            if existing is not None:
                raise ConflictError(code="CANDIDATE_EMAIL_EXISTS")

            row = await self._repository.create(
                organization_id=organization_id,
                data=payload,
                created_by=actor.id,
            )

        return CandidateResponse.model_validate(row)
~~~

Permission API trong ví dụ chỉ minh họa. Phải tái sử dụng authorization service/policy thực tế.

### 8.4 repository.py

Repository chịu trách nhiệm:

- Xây select/insert/update/delete.
- Join và aggregate database.
- Pagination, ordering và filtering ở database.
- Lock row khi use case yêu cầu.
- Nhận organization_id rõ ràng.
- Trả dữ liệu có type/map rõ cho service.

Repository không được:

- Chứa HTTP concept.
- Raise HTTPException.
- Kiểm tra permission của actor.
- Điều phối email/task/storage.
- Commit hoặc rollback.
- Tạo session mới.
- Bỏ tenant filter.
- Trả query object ra router.

Repository chỉ dùng Table từ generated_tables.py:

~~~python
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.generated_tables import candidates

from .schemas import CandidateCreate


class CandidateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(
        self,
        *,
        organization_id: UUID,
        email: str,
    ):
        statement = (
            select(candidates)
            .where(candidates.c.organization_id == organization_id)
            .where(candidates.c.email == email)
        )
        result = await self._session.execute(statement)
        return result.mappings().one_or_none()

    async def create(
        self,
        *,
        organization_id: UUID,
        data: CandidateCreate,
        created_by: UUID,
    ):
        values = {
            **data.model_dump(),
            "organization_id": organization_id,
            "created_by": created_by,
        }
        statement = insert(candidates).values(values).returning(candidates)
        result = await self._session.execute(statement)
        return result.mappings().one()
~~~

Không nhận organization_id từ data.model_dump nếu tenant context đã được resolve. Luôn ghi đè bằng organization_id tin cậy từ context.

## 9. Database schema là nguồn sự thật

> **Scope:** Nguyên tắc lấy PostgreSQL schema làm nguồn sự thật duy nhất, quy trình cập nhật generated_tables.py và thiết kế constraints/indexes.
>
> **Keywords:** `source of truth`, `migrations`, `generated_tables.py`, `dbmate`, `unique constraints`, `indexes`

### Quy tắc bắt buộc

- PostgreSQL schema, migrations và constraints là nguồn sự thật về bảng/cột/index/foreign key/enum.
- app/database/generated_tables.py là output được sinh tự động.
- Không sửa generated_tables.py bằng tay.
- Không tạo models.py thủ công trong từng module để định nghĩa lại cùng bảng.
- Không dùng metadata.create_all để thay thế migration trong production.
- Migration là SQL thuần chạy bằng dbmate; không dùng Alembic.
- Không để schema API phụ thuộc trực tiếp vào generated table object.
- Repository import table từ generated_tables.py.

### Luồng thay đổi database

~~~text
Yêu cầu nghiệp vụ
  -> dbmate new <tên>            (sinh file migration SQL thuần)
  -> viết DDL trong -- migrate:up / -- migrate:down
  -> review tenant keys, constraints và indexes
  -> diễn tập trên database dùng một lần (mục 29)
  -> dbmate up --no-dump-schema  (apply, ghi version vào schema_migrations)
  -> uv run db export --clean    (sinh lại db/schema/schema.sql)
  -> uv run db generate          (sinh lại generated_tables.py)
  -> cập nhật repository
  -> cập nhật Pydantic schemas/API contract
  -> cập nhật tests
  -> regenerate frontend OpenAPI client/types nếu contract đổi
~~~

Hai file generated không bao giờ sửa tay, và luôn sinh lại từ một database đã
apply đủ bộ migration. Nếu chúng được export từ một database có lịch sử riêng
của máy dev thì nội dung sẽ lệch với bộ migration trong repo mà không ai thấy.

Trước khi thay đổi schema, agent phải tìm:

~~~bash
rg -n "generated_tables|sqlacodegen|reflect|schema" backend/pyproject.toml backend/src backend
rg -n "migrate:up|migrate:down|schema_migrations" db backend
rg -n "<table_name>|<column_name>" backend/src backend/tests
~~~

Phải dùng lệnh đã chốt ở mục 29 và 32. Không tự phát minh command, không tự cài
thêm một migration tool thứ hai.

### Constraints và indexes

Business invariant quan trọng phải được bảo vệ ở database khi có thể:

- Unique constraint.
- Foreign key.
- Check constraint.
- Not-null.
- Composite uniqueness có organization_id.
- Index theo organization_id và các filter/sort phổ biến.

Service vẫn cần kiểm tra để trả lỗi thân thiện, nhưng database constraint là lớp bảo vệ cuối trước race condition.

Ví dụ unique theo tenant:

~~~text
UNIQUE (organization_id, email)
~~~

Không tạo global unique email nếu nghiệp vụ cho phép cùng email ở nhiều organization.

### Generated file trong code review

Khi generated_tables.py thay đổi:

- Xác nhận thay đổi tương ứng migration/DDL.
- Kiểm tra không có table/cột unrelated biến mất do generate sai database.
- Không chỉnh diff generated bằng tay.
- Chạy generation lại từ clean schema nếu script hỗ trợ.

## 10. Database session và transaction

> **Scope:** Vòng đời AsyncSession theo request, ranh giới transaction do Service điều phối và cơ chế xử lý đồng thời (concurrency).
>
> **Keywords:** `AsyncSession`, `transaction boundary`, `session.begin`, `SELECT FOR UPDATE`, `concurrency`, `row lock`

### Session

- database/session.py là nơi duy nhất cấu hình engine và session factory.
- Session là request-scoped.
- Không tạo engine ở module.
- Không lưu AsyncSession trong global singleton.
- Worker/background task tự mở session theo lifecycle riêng.
- Repository dùng session được inject từ service/request scope.

### Transaction boundary

Service sở hữu transaction boundary.

~~~text
Router
  -> inject session
  -> Service
       -> begin transaction
       -> Repository A
       -> Repository B
       -> flush
       -> commit khi block thành công
       -> rollback khi exception
~~~

Repository:

- Không commit.
- Không rollback.
- Có thể flush nếu cần ID/constraint sớm và convention cho phép.
- Không mở transaction lồng nhau tùy tiện.

Không để một use case commit giữa chừng rồi tiếp tục xử lý các bước bắt buộc khác. Nếu side effect ngoài database như gửi email hoặc enqueue task phải xảy ra sau commit, thiết kế rõ:

- after-commit action;
- outbox pattern;
- hoặc trạng thái retry/idempotency phù hợp.

Không giữ database transaction mở trong lúc gọi AI service, gửi email hoặc upload file lâu. Tách phase và persist state rõ ràng.

### Concurrency

Khi nhiều request có thể sửa cùng tài nguyên:

- Dùng unique constraint cho uniqueness.
- Dùng row lock với SELECT ... FOR UPDATE khi workflow yêu cầu serialize.
- Dùng optimistic concurrency/version field nếu phù hợp.
- Map IntegrityError/serialization conflict thành domain error rõ ràng.
- Không chỉ check-then-insert mà thiếu database constraint.

## 11. Tenant isolation theo organization_id

> **Scope:** Yêu cầu bảo mật cô lập tenant bắt buộc đối với mọi truy vấn dữ liệu, thao tác ghi, join liên bảng và regression tests.
>
> **Keywords:** `organization_id`, `tenant isolation`, `multi-tenant`, `test_isolation.py`, `cross-tenant`, `RLS`

Đây là yêu cầu bảo mật bắt buộc, không phải convention tùy chọn.

### Nguồn organization context

organization_id tin cậy phải đến từ:

- Authenticated membership/session context.
- Path/header đã được dependency validate với membership.
- Internal job payload đã được ký/kiểm soát và resolve lại.

Không tin organization_id chỉ vì client gửi trong body.

### Repository rules

Mọi query đối với dữ liệu tenant phải có organization_id:

~~~python
select(jobs).where(
    jobs.c.organization_id == organization_id,
    jobs.c.id == job_id,
)
~~~

Update/delete cũng bắt buộc tenant scope:

~~~python
update(jobs).where(
    jobs.c.organization_id == organization_id,
    jobs.c.id == job_id,
)
~~~

Không được:

~~~python
select(jobs).where(jobs.c.id == job_id)
~~~

dù ID là UUID. UUID không thay thế tenant filter.

### Insert rules

- Service/repository gán organization_id từ trusted context.
- Không lấy organization_id trực tiếp từ request DTO cho create thông thường.
- Child table phải được xác thực parent thuộc cùng organization.
- Foreign key/composite constraint nên ngăn cross-tenant reference khi schema cho phép.

### Join rules

- Mọi root resource phải scope theo organization_id.
- Join phải tránh ghép dữ liệu khác tenant.
- Với bảng có organization_id ở cả hai phía, ưu tiên join thêm tenant key hoặc dựa trên constraint bảo đảm cùng tenant.
- Cross-organization operation chỉ được phép cho system/super-admin use case có policy rõ và tests riêng.

### Global tables

Chỉ bảng được xác định rõ mới được xem là global, ví dụ:

- System permission catalog.
- Country/timezone reference.
- Global configuration an toàn.

Không suy luận một bảng là global chỉ vì nó chưa có organization_id. Nếu không rõ, dừng và kiểm tra schema/requirements.

### Isolation tests

Mọi module tenant-aware mới phải có test chứng minh:

- Organization A không đọc được dữ liệu của B.
- A không update/delete dữ liệu của B.
- A không attach child vào parent của B.
- Filter/search/export không rò dữ liệu B.
- Background job không xử lý nhầm tenant.
- Permission ở A không tự áp dụng cho B.

tests/security/test_isolation.py là security regression suite quan trọng và không được bỏ qua.

Nếu PostgreSQL RLS được bật về sau, application-level organization filter vẫn phải rõ ràng trừ khi kiến trúc được sửa đổi chính thức. RLS là defense in depth, không phải lý do để viết query mơ hồ.

## 12. Authentication

> **Scope:** Thẩm quyền xác thực người dùng tập trung tại FastAPI, danh mục endpoint, quản lý cookie bảo mật và chính sách credential.
>
> **Keywords:** `login`, `logout`, `refresh token`, `cookies`, `HttpOnly`, `password hash`, `rate limit`

FastAPI là authentication authority.

Endpoint dự kiến:

~~~text
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
~~~

Quy tắc:

- Không log password, access token, refresh token, cookie hoặc credential.
- Password phải hash bằng algorithm đã chốt trong config/security.py.
- Không tự viết cryptography.
- So sánh secret/token bằng library an toàn.
- Refresh token rotation/revocation phải theo security contract.
- Cookie phải có HttpOnly, Secure và SameSite phù hợp.
- Nếu dùng cookie auth, CSRF policy phải được thiết kế và test.
- Rate-limit login/verification/reset endpoints nếu infrastructure hỗ trợ.
- Error không được tiết lộ tài khoản có tồn tại khi security contract yêu cầu chống enumeration.
- Session/token expiry dùng UTC.
- User disabled/revoked phải bị chặn theo policy.

Authentication dependency chỉ trả principal/context đã validate. Không truyền raw token sâu xuống service.

## 13. Authorization

> **Scope:** Mô hình phân quyền RBAC gắn với organization scope, danh mục quyền nghiệp vụ và quy chuẩn xử lý HTTP 401/403.
>
> **Keywords:** `RBAC`, `permissions`, `roles`, `organization scope`, `HTTP 401`, `HTTP 403`

Authorization sử dụng:

~~~text
RBAC
  + organization scope
  + resource ownership/business policy khi cần
~~~

Permission naming đề xuất:

~~~text
user:create
user:read
user:update
user:delete

job:create
job:read
job:update
job:publish

candidate:create
candidate:read
candidate:update
candidate:delete

interview:schedule
interview:read
interview:feedback
~~~

Quy tắc:

- Permission catalog và role mapping thuộc module authorization.
- Module mới đăng ký permission vào nền tảng hiện có.
- Không tạo role/permission table riêng trong module tuyển dụng.
- Không hard-code role name ở nhiều service nếu permission check diễn đạt đúng hơn.
- Super-admin bypass nếu có phải tập trung và có audit/test.
- Service kiểm tra permission trên organization/resource cụ thể.
- Frontend hide button không thay thế backend check.
- Trả 401 cho chưa xác thực và 403 cho đã xác thực nhưng không có quyền.
- Tránh để 404/403 làm lộ resource theo policy; dùng shared exception mapping nhất quán.

## 14. Shared code và quy tắc reuse-first

> **Scope:** Thứ tự tìm kiếm mã nguồn hiện có trước khi tạo mới, phân định vị trí đặt code và quy tắc giữ gìn thư mục common.
>
> **Keywords:** `reuse-first`, `app/common`, `ripgrep search`, `code location`, `utils anti-pattern`

Trước khi tạo function, class, dependency, schema, exception, repository helper hoặc integration mới, bắt buộc tìm implementation hiện có.

### Thứ tự tìm

1. Module hiện tại.
2. app/common.
3. app/config.
4. app/database.
5. Module nền tảng có ownership phù hợp.
6. Module tương tự.
7. Dependency đã cài trong pyproject.toml.

### Lệnh tìm bắt buộc

Tìm theo tên dự kiến, từ đồng nghĩa và hành vi:

~~~bash
rg -n "get_current_user|CurrentUser|authenticate" backend/src backend/tests
rg -n "organization_id|OrganizationContext|tenant" backend/src backend/tests
rg -n "require_permission|PermissionDenied|authorization" backend/src backend/tests
rg -n "BaseRepository|paginate|Pagination" backend/src backend/tests
rg -n "NotFoundError|ConflictError|exception_handler" backend/src
rg -n "get_session|async_sessionmaker|AsyncSession" backend/src
rg -n "S3|RustFS|presigned|object_key|storage" backend/src backend/tests
rg -n "send_email|EmailClient|mailer" backend/src
rg -n "<function_name>|<feature_keyword>" backend/src backend/tests
~~~

Nếu đã có implementation phù hợp:

- Dùng lại trực tiếp.
- Mở rộng backward-compatible nếu abstraction hiện có đúng ownership.
- Refactor ra common khi có ít nhất hai consumer thật sự và abstraction độc lập domain.
- Không copy rồi đổi tên.
- Không tạo helper global chỉ cho một use case.

### Quyết định vị trí

| Thành phần | Vị trí |
|---|---|
| Endpoint của candidates | modules/candidates/router.py |
| Candidate request/response DTO | modules/candidates/schemas.py |
| Candidate business logic | modules/candidates/service.py |
| Candidate SQL query | modules/candidates/repository.py |
| Auth dependency dùng toàn hệ thống | common/dependencies/auth.py |
| Organization context | common/dependencies/organization.py |
| Permission dependency/policy primitive | common/dependencies/permission.py hoặc authorization |
| Generic API error handler | common/exceptions/handlers.py |
| Pagination schema dùng chung | common/schemas/common.py |
| Generic repository helper nhỏ | common/repository.py |
| Settings | config/settings.py |
| Security primitive/config | config/security.py |
| Session/engine | database/session.py |
| Generated SQLAlchemy tables | database/generated_tables.py |
| RustFS S3 adapter | common/storage |
| Database/IAM CLI | tools |

Khi chưa chắc một function có dùng chung hay không, đặt nó trong module đang sở hữu use case. Chỉ đưa vào common khi ranh giới đã rõ. Không thiết kế abstraction theo dự đoán mơ hồ.

### common không phải thùng rác

Code trong common phải:

- Không thuộc riêng một domain.
- Có API nhỏ và rõ.
- Không import module feature.
- Không chứa business rule của candidates/jobs/interviews.
- Có tests phù hợp.

Không tạo utils.py tổng hợp hàng trăm function. Dùng package/file theo concern rõ ràng.

## 15. config, database, common và tools

> **Scope:** Trách nhiệm, phạm vi sử dụng và ranh giới cấm kỵ của 4 thư mục hạ tầng config, database, common và tools.
>
> **Keywords:** `config`, `database`, `common`, `tools`, `pydantic-settings`, `CLI scripts`

### config

config chứa cấu hình hệ thống tập trung:

- settings.py: đọc và validate environment.
- security.py: security configuration/primitives.
- constants.py: constant cấp hệ thống, không phải constant domain.

Không đọc os.environ rải rác trong modules.

Settings phải:

- Dùng pydantic-settings.
- Có type.
- Fail fast khi biến bắt buộc thiếu.
- Không có production secret hard-coded.
- Không log secret trong model dump.

### database

database chỉ chứa:

- Engine/session lifecycle.
- Generated table metadata.
- Database-level support code thật sự dùng chung.

Không đặt repository nghiệp vụ toàn cục trong database.

### common

common chứa cross-cutting concerns:

- Dependencies.
- Shared exceptions/handlers.
- Shared schemas.
- Storage/email clients.
- Repository primitives tối thiểu.

Không đưa business service vào common.

### tools

tools chứa CLI/maintenance scripts:

- Database generation/inspection.
- Clean schema cho test/dev.
- IAM seed/bootstrap.

Tool:

- Không được import vào runtime request path.
- Phải có guard và config an toàn.
- Không mặc định chạy destructive action.
- Phải xác nhận environment/target rõ trước clean/reset.
- Không dùng production database nếu chưa có bảo vệ rõ.

## 16. API contract

> **Scope:** Chuẩn thiết kế REST API, tiền tố /api/v1, quy ước danh từ số nhiều, mã lỗi đồng nhất, phân trang chuẩn và OpenAPI client.
>
> **Keywords:** `REST API`, `/api/v1`, `HTTP status codes`, `error format`, `pagination`, `OpenAPI`

### Versioning

Public API dùng prefix thống nhất:

~~~text
/api/v1
~~~

Không đưa version rải rác trong từng router nếu main.py đã cấu hình prefix chung.

### Resource naming

- URL dùng danh từ số nhiều.
- Dùng kebab-case khi path có nhiều từ.
- Không đưa động từ CRUD vào URL.
- Action nghiệp vụ được phép khi nó là command rõ, ví dụ POST /jobs/{id}/publish.

Ví dụ:

~~~text
GET    /api/v1/candidates
GET    /api/v1/candidates/{candidate_id}
POST   /api/v1/candidates
PATCH  /api/v1/candidates/{candidate_id}
DELETE /api/v1/candidates/{candidate_id}
POST   /api/v1/jobs/{job_id}/publish
~~~

### Status codes

- 200: read/update thành công.
- 201: create thành công.
- 202: background processing đã được chấp nhận.
- 204: delete/no-content thành công.
- 400: request semantic không hợp lệ nhưng không thuộc validation field chuẩn.
- 401: chưa xác thực.
- 403: không có quyền.
- 404: resource không tồn tại hoặc policy che giấu resource.
- 409: conflict/duplicate/state transition conflict.
- 422: validation.
- 429: rate limit.

Không trả 200 cho mọi trường hợp lỗi.

### Error format

Error response chuẩn:

~~~json
{
  "error": {
    "code": "CANDIDATE_EMAIL_EXISTS",
    "message": "Email ứng viên đã tồn tại",
    "details": {},
    "request_id": "..."
  }
}
~~~

Quy tắc:

- code ổn định để frontend xử lý.
- message thân thiện và an toàn.
- details không lộ SQL, stack trace, token hoặc internals.
- request_id dùng để tra log.
- Domain exception được central handler map sang HTTP.
- Không catch Exception rồi trả 200/None.
- Unknown exception được log với context an toàn và trả generic 500.

### Pagination/filter/sort

Dùng query parameters `page` và `page_size`. `page` bắt đầu từ 1; `page_size`
mặc định là 20 và tối đa là 100.

Response dùng shared schema/convention:

~~~json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 0,
    "total_pages": 0,
    "has_next_page": false,
    "has_previous_page": false
  }
}
~~~

Chỉ dùng cursor convention cho endpoint có dữ liệu rất lớn hoặc thay đổi liên tục
khi project đã chốt contract riêng.

Không tự tạo một pagination response khác cho mỗi module.

Repository thực hiện filter/sort/pagination tại database. Không load toàn bộ rồi slice trong Python.

Repository chuyển `page` và `page_size` thành offset nội bộ; không đưa `offset` vào
API contract. Query phải có thứ tự ổn định trước khi phân trang.

Sort field phải allowlist, không ghép raw input vào SQL.

### OpenAPI và frontend

Khi schema hoặc endpoint thay đổi:

1. Chạy backend tests.
2. Kiểm tra OpenAPI generation.
3. Generate lại frontend API types/client bằng script hiện có.
4. Sửa frontend consumer nếu breaking.

Không thay đổi field name/type âm thầm.

## 17. RustFS và object storage

> **Scope:** Contract chuẩn để các module lưu file trên S3-compatible storage, quản lý metadata trong PostgreSQL và upload trực tiếp từ browser mà không làm lộ quyền truy cập.
>
> **Keywords:** `RustFS`, `S3 adapter`, `stored_files`, `file_id`, `presigned URL`, `object_key`, `public`, `private`, `file upload`

RustFS hiện là S3-compatible implementation của dự án. Code phải phụ thuộc abstraction
S3-compatible chung, không phụ thuộc đặc tính riêng của RustFS để sau này có thể chuyển
sang AWS S3, MinIO hoặc dịch vụ tương thích khác.

### 17.1. Ba lớp trách nhiệm

~~~text
Module nghiệp vụ
  -> quyết định ai được upload/download, file thuộc resource nào và policy file
  -> app/common/storage
       -> tạo object key, presigned request và thao tác object qua adapter
       -> S3-compatible storage

PostgreSQL
  -> lưu metadata đã xác minh và quan hệ nghiệp vụ bằng file_id
S3-compatible storage
  -> lưu binary object
~~~

- Router chỉ nhận/trả HTTP contract và inject `ObjectStorage`.
- Service sở hữu authorization, validation, lifecycle, transaction và cleanup.
- Repository sở hữu query đối với `stored_files` và bảng nghiệp vụ.
- `app/common/storage` chỉ chứa primitive kỹ thuật dùng chung; không chứa rule riêng
  của avatar, CV, offer hoặc branding.
- Database không lưu binary. Object storage không phải nguồn sự thật cho ownership hay
  authorization.

### 17.2. Shared storage API

Module nghiệp vụ không gọi SDK S3/RustFS trực tiếp. Dùng adapter chung tại:

~~~text
app/common/storage/
├── client.py       # ObjectStorage protocol và S3-compatible adapter
├── database.py     # helper join/project public URL
├── exceptions.py   # lỗi kỹ thuật đã chuẩn hóa
├── keys.py         # ObjectKeyBuilder và public_object_url
└── schemas.py      # PresignedRequest, ObjectHead
~~~

Adapter cung cấp operation cần thiết:

- Tạo presigned PUT/GET request.
- Head, bounded read, copy và delete object.
- Chuẩn hóa lỗi storage để service map sang error contract của API.
- Chạy SDK đồng bộ qua threadpool để không block async event loop.

Tái sử dụng `ObjectStorage`, `ObjectKeyBuilder`, `public_file_join` và
`public_file_url_column` trước khi tạo helper mới. Không để `boto3`, tên SDK hoặc
RustFS detail lan vào schema nghiệp vụ.

### 17.3. Contract của `stored_files`

`stored_files` là registry metadata kỹ thuật dùng chung cho object **đã upload và xác
minh thành công**. Bảng này không phải một domain module và không tự biểu diễn file
thuộc candidate, organization hay user nào.

Schema đã chốt, không thêm field suy đoán nếu chưa có use case thật:

| Cột | Ý nghĩa |
|---|---|
| `id` | UUID ổn định của file; đồng thời dùng làm segment cuối của object key. |
| `bucket` | Bucket vật lý chứa object. Không suy ra từ visibility. |
| `object_key` | Key đầy đủ do backend tạo, bắt đầu bằng `public/` hoặc `private/`. |
| `original_name` | Tên file để hiển thị/download; chỉ là metadata, không dùng làm key/path. |
| `content_type` | MIME type đã được workflow hoàn tất kiểm tra. |
| `visibility` | Chỉ nhận `public` hoặc `private`, phải khớp prefix của `object_key`. |
| `size_bytes` | Kích thước object đã xác minh bằng storage metadata. |
| `checksum_sha256` | SHA-256 lowercase hex khi workflow tính được; có thể null. |
| `uploaded_by` | UUID actor dùng cho audit; không phải ownership hay authorization source. |
| `created_at` | Thời điểm metadata được tạo sau khi upload hoàn tất. |
| `deleted_at` | Soft delete metadata; null khi file còn hiệu lực. |

Không thêm `organization_id`, `resource_type`, `resource_id`, URL hoặc trạng thái upload
vào `stored_files` chỉ để dự phòng. Quan hệ nghiệp vụ nằm ở bảng sở hữu resource:

~~~text
users.file_id                     -> stored_files.id       # avatar hiện tại
organizations.file_id             -> stored_files.id       # branding hiện tại
<domain relation>.file_id          -> stored_files.id       # attachment khi có use case
~~~

Dùng tên `file_id` nhất quán. Nếu một resource có nhiều file hoặc cần metadata nghiệp
vụ riêng như loại tài liệu, thứ tự hay trạng thái duyệt, tạo relation table trong module
sở hữu aggregate và để relation table tham chiếu `file_id`; không nhồi các field đó vào
`stored_files`.

`uploaded_by` chỉ phục vụ audit. Không authorize, tenant-scope hoặc suy ra owner bằng
field này. Field này chủ ý không buộc foreign key tới `users` trong schema hiện tại để
tránh chu kỳ `users.file_id -> stored_files` và `stored_files.uploaded_by -> users` khi
seed/xóa dữ liệu; service vẫn ghi actor đã xác thực.

Chỉ join file còn hiệu lực (`deleted_at IS NULL`). Với public projection, đồng thời yêu
cầu `visibility = 'public'`; dùng helper trong `common/storage/database.py` thay vì lặp
điều kiện ở từng repository.

Không lưu access key, secret key hoặc presigned URL lâu dài trong database.

### 17.4. Bucket, visibility và object key

Dự án hiện dùng một bucket cấu hình bởi `STORAGE_BUCKET` và phân vùng bằng prefix.
Không tách public/private bằng suy đoán tên bucket; `bucket` vẫn được lưu trong metadata
để adapter và database không phụ thuộc một bucket cố định:

~~~text
public/users/{user_id}/avatar/{file_id}
public/organizations/{organization_id}/branding/{asset_type}/{file_id}

private/organizations/{organization_id}/{resource}/{resource_id}/{category}/{file_id}
private/temp/uploads/users/{user_id}/avatar/{file_id}
~~~

Đây là convention key, không phải danh sách domain folder đóng cứng. Chỉ thêm
`resource`/`category` khi backend đã có aggregate và use case tương ứng. Mọi segment động
không phải UUID phải đến từ allowlist hoặc qua validation của `ObjectKeyBuilder`.

Object key phải bao gồm organization scope hoặc mapping metadata không thể mơ hồ:

~~~text
private/organizations/{organization_id}/candidates/{candidate_id}/documents/{file_id}
~~~

- Backend là bên duy nhất tạo bucket/key; không nhận bucket hay object key từ client.
- Không dùng `original_name` làm key và không ghép path từ filename người dùng.
- Key tenant data phải chứa `organization_id` tin cậy từ context và resource ID đã được
  kiểm tra thuộc tenant đó.
- `visibility = 'public'` bắt buộc key bắt đầu `public/`; `private` bắt buộc bắt đầu
  `private/`. Database constraint cũng bảo vệ invariant này.
- Cặp `(bucket, object_key)` phải duy nhất.

### 17.5. Public và private access

`public/` dành cho asset thật sự được phép đọc ẩn danh như avatar hoặc branding. Bucket
policy chỉ mở anonymous GET cho prefix này, **không mở toàn bộ bucket**. Public URL có
dạng:

~~~text
{STORAGE_PUBLIC_BASE_URL}/{bucket}/public/...
http://localhost:9000/hr-ai/public/users/{user_id}/avatar/{file_id}
~~~

Dùng S3 API endpoint (local thường là cổng `9000`), không dùng RustFS console (cổng
`9001`). URL public được dựng khi query/serialize bằng shared helper; không lưu URL vào
database vì host/CDN có thể đổi.

`private/` tuyệt đối không có anonymous URL. Download private file phải đi qua endpoint
đã authenticate/authorize và trả presigned GET ngắn hạn, hoặc backend proxy khi policy
bắt buộc. Không biến file private thành public chỉ để frontend hiển thị được.

### 17.6. Presigned upload workflow chuẩn

Flow đã áp dụng cho avatar và là mẫu cho upload mới:

~~~text
1. Client -> FastAPI: xin upload với original_name, content_type, size_bytes
2. FastAPI: authenticate/authorize, validate policy, tạo file_id và private temp key
3. FastAPI -> Client: file_id + presigned PUT URL + method + headers + expiry
4. Client -> S3 endpoint: PUT binary trực tiếp với đúng headers được ký
5. Client -> FastAPI: complete(file_id, metadata)
6. FastAPI: tự dựng lại temp key từ actor/resource; HEAD và kiểm tra object
7. FastAPI: kiểm tra size, MIME/header, magic bytes/checksum/scan theo loại file
8. FastAPI: copy/move object từ private temp sang final public/private key
9. FastAPI transaction: insert stored_files, gắn file_id vào resource, soft-delete file cũ
10. FastAPI: dọn temp sau copy; commit rồi best-effort xóa object cũ; trả resource mới
~~~

Không tạo row `stored_files` ở bước xin URL cho upload tạm hiện tại. Chỉ persist metadata
sau khi complete đã xác minh object; upload dở dang vì vậy không trở thành file hợp lệ.
Temp object cần lifecycle/cleanup ở storage để tự hết hạn nếu client bỏ dở.

Presigned response phải trả cả `method` và `headers`; frontend phải gửi chính xác các
header đã ký, đặc biệt `Content-Type`. Upload binary đi thẳng tới S3 endpoint, không gửi
cookie hay bearer token của FastAPI tới URL presigned.

Endpoint nên theo cặp use case rõ ràng, như implementation avatar hiện tại:

~~~text
POST /.../uploads                     # validate và cấp file_id + presigned PUT
POST /.../uploads/{file_id}/complete  # xác minh object rồi gắn vào aggregate
DELETE /...                           # bỏ relation, soft-delete metadata, cleanup object
~~~

Request không chứa `bucket`, `object_key`, `visibility`, `uploaded_by` hoặc URL; service
suy ra các giá trị đó từ use case, actor và tenant context đáng tin cậy.

Backend phải tự xác minh, không tin metadata client khai báo:

- Giới hạn `size_bytes` trước khi cấp URL và kích thước thật từ HEAD/stream.
- Allowlist MIME type theo từng use case; extension chỉ là tín hiệu phụ.
- Magic bytes/file signature với định dạng hỗ trợ.
- Actor, organization, resource ownership và permission.
- Temp/final key được dựng lại từ trusted IDs, không lấy từ request.
- Checksum SHA-256 khi workflow cần integrity/dedup/audit.
- Malware scan trước khi file rủi ro được download hoặc xử lý tiếp.

Avatar hiện giới hạn 5 MiB nên backend được phép bounded-read để kiểm tra signature và
tính SHA-256. Với CV, import/export hoặc file lớn, không đọc toàn bộ binary vào memory;
dùng streaming, checksum do storage hỗ trợ hoặc background scanner phù hợp.

**Ngoại lệ: người upload ẩn danh.** Flow trên giả định bước 2 nhận ra được actor. Khi
người upload là người lạ chưa đăng nhập — hiện chỉ có form ứng tuyển công khai nộp CV —
thì **không cấp presigned PUT**, mà nhận multipart rồi backend ghi object bằng
`ObjectStorage.put_object`. Lý do: presigned PUT ký bằng `generate_presigned_url` chỉ
ràng buộc bucket, key và content type, **không ràng buộc được kích thước** (chỉ presigned
POST mới có `content-length-range`), nên một endpoint ẩn danh cấp URL là một endpoint cho
cả internet ghi tuỳ ý vào bucket: xin URL, PUT một file khổng lồ, không bao giờ gọi
complete, và không có row `stored_files` nào để lần ra. Rate limit theo IP không cứu
được vì chi phí của kẻ tấn công là một request còn chi phí của mình là dung lượng.

Đổi lại, đường ẩn danh phải: đọc theo luồng và chặn ngay khi vượt trần *trong lúc*
truyền; kiểm magic bytes và bắt phần mở rộng khớp nội dung thật; dựng key từ ID tin cậy
dưới `private/`; ghi `stored_files` cùng transaction với quan hệ nghiệp vụ và xoá object
khi transaction hỏng; để `uploaded_by` null vì không có actor. Chiều tải về vẫn theo mục
17.5: endpoint đã authorize trả presigned GET ngắn hạn, trả **trong body** chứ không
redirect, vì client gọi API kèm cookie phiên và redirect sẽ đẩy cookie đó sang object
storage.

External storage call không được nằm trong DB transaction lâu. Do PostgreSQL và S3 không
có distributed transaction, service phải có cleanup rõ ràng:

- DB fail sau khi copy final: rollback rồi best-effort xóa final object.
- Xóa object fail sau khi DB commit/soft-delete: log có cấu trúc và để retry/cleanup job
  xử lý; không phục hồi relation cũ một cách mơ hồ.
- Thay file: lock/read relation hiện tại khi concurrency có thể làm mất update.
- API complete nên có hành vi conflict/not-found rõ; chỉ thêm idempotency khi use case
  hoặc retry contract thực sự yêu cầu.

### 17.7. Browser CORS và cấu hình

CORS của FastAPI không áp dụng cho request từ browser tới S3 endpoint. Bucket phải
allowlist frontend origin cho các method/header thực dùng (`PUT`, `GET`, `HEAD`,
`Content-Type`) và expose `ETag` nếu frontend cần. Khi đổi bucket/origin phải cập nhật
bucket CORS tương ứng.

Các setting chuẩn hiện tại:

| Setting | Vai trò |
|---|---|
| `STORAGE_ENDPOINT_URL` | Endpoint backend dùng để gọi S3. |
| `STORAGE_BROWSER_ENDPOINT_URL` | Endpoint được nhúng vào presigned URL và browser truy cập được. |
| `STORAGE_PUBLIC_BASE_URL` | Base URL public/CDN; fallback về browser endpoint. |
| `STORAGE_REGION` | S3 signing region. |
| `STORAGE_ACCESS_KEY_ID` / `STORAGE_SECRET_ACCESS_KEY` | Credential chỉ có ở backend. |
| `STORAGE_BUCKET` | Bucket mặc định. |
| `STORAGE_PRESIGN_TTL_SECONDS` | Thời hạn URL ký, hiện giới hạn 60–3600 giây. |
| `STORAGE_ADDRESSING_STYLE` | `path` hoặc `virtual` theo provider. |

Local RustFS phải dùng API endpoint cổng `9000`; cổng `9001` chỉ là console. Xem
`backend/README.md` để cấu hình bucket CORS và anonymous access cho đúng prefix
`public/`.

### 17.8. Khi thêm một loại file mới

Trước khi code, dev/agent phải trả lời bằng code/schema cụ thể:

1. Aggregate nào sở hữu file và relation `file_id` nằm ở đâu?
2. File public hay private, ai được upload/download/delete?
3. Giới hạn size, MIME allowlist, signature và scan policy là gì?
4. Final key nào trong `ObjectKeyBuilder` biểu diễn đúng tenant/resource?
5. Thay thế một file hay đính kèm nhiều file; soft-delete/cleanup ra sao?
6. API dùng create + complete nào, response có cần public URL hay presigned GET?

Test tối thiểu phải bao phủ:

- happy path create -> PUT giả lập -> complete;
- unauthorized/cross-tenant resource;
- object thiếu, sai size, sai MIME/signature và vượt giới hạn;
- DB failure sau storage copy và storage cleanup failure;
- public projection bỏ qua private/deleted file;
- object key đúng tenant/resource và không chứa filename người dùng.

Unit/API tests phải fake `ObjectStorage`; không gọi RustFS thật. Integration test chỉ dùng
storage test environment khi suite đó khai báo rõ.

## 18. Redis, Celery và background jobs

> **Scope:** Ranh giới sử dụng tác vụ nền Celery/Redis, nguyên tắc payload tinh gọn, tính lũy đẳng idempotency và thời điểm enqueue sau commit.
>
> **Keywords:** `Celery`, `Redis`, `background jobs`, `job payload`, `idempotency`, `after-commit enqueue`

### Khi dùng background job

Dùng cho:

- CV extraction.
- Speech-to-text.
- Speaker diarization.
- AI summarization.
- Email.
- Report generation.
- Large file processing.
- Virus scanning.

Không giữ HTTP request mở cho tác vụ dài. Endpoint tạo job trả 202 và resource/job ID.

### Job payload

Job payload phải nhỏ:

- Resource ID.
- organization_id.
- actor/system context cần thiết.
- Idempotency key/correlation ID.

Không nhét file binary hoặc toàn bộ object lớn vào Redis/Celery message.

### Worker rules

- Worker tự mở/đóng database session.
- Query lại resource từ database.
- Enforce tenant scope.
- Có idempotency.
- Có retry policy hữu hạn.
- Phân biệt retryable và permanent error.
- Persist status/progress/error an toàn.
- Không log nội dung nhạy cảm của CV/recording nếu không cần.
- Không gọi router; gọi service/handler dùng chung phù hợp.

### Transaction và enqueue

Không enqueue job trước khi database transaction tạo resource đã commit, trừ khi dùng outbox pattern.

Nếu job có thể được gửi hai lần, handler phải chịu được duplicate delivery.

### Redis

Không dùng Redis làm source of truth cho dữ liệu nghiệp vụ.

Redis chỉ dùng cho:

- Cache.
- Rate limit.
- Temporary state.
- Distributed lock khi được thiết kế rõ.
- Celery broker/result backend.
- Pub/sub hoặc realtime coordination.

Mọi cache key tenant-aware phải chứa organization_id.

## 19. Email và external integrations

> **Scope:** Giao tiếp với dịch vụ bên ngoài thông qua abstraction chung, thiết lập timeout, retry hữu hạn và tách biệt khỏi transaction database.
>
> **Keywords:** `external integration`, `email`, `timeout`, `retry`, `circuit breaker`, `domain exception`

Module nghiệp vụ gọi abstraction chung, không phụ thuộc trực tiếp provider SDK.

Quy tắc:

- Timeout rõ ràng.
- Retry hữu hạn.
- Idempotency cho operation có side effect.
- Không giữ DB transaction trong lúc chờ network lâu.
- Log provider request ID, không log secret/body nhạy cảm.
- Circuit breaker chỉ thêm khi có nhu cầu và library/convention rõ.
- External failure phải map thành domain/integration error có kiểm soát.

Nếu integration lớn, có thể tách app/integrations theo quyết định kiến trúc. Không tự tạo song song common/integrations và integrations cho cùng concern.

## 20. Logging và observability

> **Scope:** Chuẩn mực structured JSON logging, lan truyền context request_id, kiểm soát cardinality của metric/tracing và chống rò rỉ dữ liệu nhạy cảm.
>
> **Keywords:** `structured logging`, `request_id`, `correlation_id`, `PII`, `observability`, `metrics cardinality`

Log phải structured và có context phù hợp:

- request_id/correlation_id.
- organization_id.
- user_id/actor_id.
- module/use_case.
- resource_id khi an toàn.
- job_id cho background task.

Không log:

- Password.
- Token/cookie.
- Authorization header.
- Database DSN có password.
- RustFS secret/access key.
- Full CV/meeting transcript/PII nếu không cần.

Mỗi request phải có request ID. Error response nên trả request_id để support tra cứu.

Không dùng print trong runtime code. Dùng logger được cấu hình chung.

Metric/tracing phải có cardinality hợp lý. Không dùng user_id, email hoặc resource ID làm metric label có cardinality cao.

## 21. Cấu hình và secrets

> **Scope:** Quản lý cấu hình tập trung qua pydantic-settings, nguyên tắc bảo mật file .env/.env.example và kiểm soát production secrets.
>
> **Keywords:** `settings.py`, `pydantic-settings`, `.env`, `.env.example`, `secrets management`, `CORS`

- Settings chỉ được đọc tập trung ở config/settings.py.
- Dependency/module nhận settings qua injection hoặc accessor được chốt.
- .env dùng local dev, không commit.
- .env.example liệt kê biến cần thiết với giá trị giả.
- Production secret đến từ secret manager/environment của deployment.
- Không đặt default không an toàn cho JWT secret, database password hoặc S3 secret.
- CORS origins phải allowlist.
- DEBUG mặc định false ngoài local.
- Docs/OpenAPI exposure ở production theo policy.

RustFS/S3 config hiện tại:

~~~text
STORAGE_ENDPOINT_URL
STORAGE_BROWSER_ENDPOINT_URL
STORAGE_PUBLIC_BASE_URL
STORAGE_REGION
STORAGE_ACCESS_KEY_ID
STORAGE_SECRET_ACCESS_KEY
STORAGE_BUCKET
STORAGE_PRESIGN_TTL_SECONDS
STORAGE_ADDRESSING_STYLE
~~~

Đây là tên đang được `config/settings.py` sử dụng; không tạo biến `S3_*` song song.
Credential chỉ tồn tại ở backend. Browser chỉ nhận presigned URL ngắn hạn và không được
nhận access key/secret key.

## 22. Security

> **Scope:** Tổng hợp các nguyên tắc phòng thủ bảo mật đa tầng: kiểm tra biên, parameterized SQL, chống SSRF, quét mã độc file và audit.
>
> **Keywords:** `security`, `parameterized SQL`, `SSRF`, `file validation`, `audit logging`, `admin guards`

- Validate mọi input ở boundary.
- Authorize mọi write và sensitive read.
- Tenant scope mọi query.
- Dùng parameterized SQLAlchemy statements; không nối raw SQL từ input.
- Allowlist sort/filter field.
- Không trả stack trace nội bộ.
- Không commit secrets.
- Không tự viết crypto.
- File upload phải validate và scan theo risk.
- Webhook phải verify signature và chống replay.
- URL do người dùng cung cấp phải có SSRF protection trước server-side fetch.
- Export/report phải tenant-scoped.
- Audit action nhạy cảm theo policy.
- Destructive admin tool phải có guard.

Nếu thay đổi auth, authorization, organization context, file access hoặc data export, bắt buộc cập nhật security contract/isolation tests.

### Nhật ký thao tác (audit log)

Thiết kế và hiện trạng ở `docs/audit_log/` (cách thêm log: `07-huong-dan-mo-rong.md`;
thiết kế đích: `11-thiet-ke-muc-tieu.md`). Luật bắt buộc:

- **Phải ghi log** (`ActivityLogService.record`): mọi thao tác ghi dữ liệu mức Cao
  (quyền, tài khoản, thành viên, dữ liệu cá nhân, tiền, quyết định duyệt, xoá
  cứng) và mức Trung bình (đổi quy trình nghiệp vụ). Mức theo
  `docs/audit_log/10-ma-tran-do-phu.md`.
- **Khai báo `AUDIT_POLICY`**: route `POST`/`PUT`/`PATCH`/`DELETE` mới phải có một
  dòng trong `tests/security/audit_policy.py` (`logged:`, `other_trace:`,
  `exempt:` hoặc `todo:`). Thiếu thì `tests/security/test_audit_coverage.py` đỏ.
- **Cùng transaction**: gọi `record()` trước `commit()` của thao tác; `record()`
  không commit. Log của thao tác bị rollback thì mất theo, đó là đúng.
- **Không ghi giá trị dữ liệu cá nhân** (QD-01): SĐT, email, ngày sinh, địa chỉ,
  ghi chú về ứng viên, số giấy tờ, lương và phụ cấp chỉ được ghi **tên field**
  (`{"phone": {"redacted": true}}` hoặc `{"fields": {"to": [...]}}`). Tên tệp gốc
  cũng không ghi. Fixture `tests/conftest.py` quét mọi log sinh trong test
  và đỏ khi gặp SĐT, email, CCCD.
- **Không đổi gì thì không ghi**: dùng `diff()`; `changes` rỗng thì bỏ qua.
- **Tên action mới**: động từ quá khứ `snake_case` (`created`, `updated`,
  `deleted`, `<noun>_<verb>ed`); không đổi tên action cũ (QD-08).
- **Đọc log**: `timeline()` không kiểm quyền. Module sở hữu thực thể kiểm quyền
  xem thực thể (và quyền xem lương với dòng `offer_*`) trước khi gọi.
- **Hạn giữ** (QD-13): `activity_logs` giữ 12 tháng, task `audit_logs.purge` dọn mỗi
  ngày lúc 2:00 (cửa sổ trượt). Tính năng nào cần dữ liệu lâu hơn thì lưu ở bảng
  nghiệp vụ, không dựa vào nhật ký.

## 23. Naming và coding conventions

> **Scope:** Quy ước đặt tên theo chuẩn PEP 8, phân định việc dùng class cho repository/service vs pure function và kỷ luật type annotations.
>
> **Keywords:** `snake_case`, `PascalCase`, `AsyncSession`, `typing`, `Protocol`, `Ruff imports`

### Python naming

- Module/file/function/variable: snake_case.
- Class/Pydantic model: PascalCase.
- Constant: UPPER_SNAKE_CASE.
- Boolean: is_, has_, can_, should_.
- Private attribute/helper: tiền tố underscore khi phù hợp.

### Async

- I/O function dùng async.
- Không đánh dấu async cho pure computation.
- Không gọi blocking network/file SDK trực tiếp trên event loop.
- Không tạo task fire-and-forget trong request nếu lifecycle không được quản lý.

### Quy ước class và function

Repository bắt buộc dùng class:

- Mỗi repository nhận `AsyncSession` qua constructor và giữ dưới dạng dependency
  private, ví dụ `self._session`.
- Method repository không nhận lại `session` ở từng lời gọi.
- Repository không dùng module-level async function để thực thi query.
- Shared repository primitive được đóng gói trong base class nhỏ tại
  `app/common/repository.py`; repository của feature có thể kế thừa khi phù hợp.
- Không tạo repository không state dưới dạng namespace chứa `@staticmethod`.

~~~python
class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, *, user_id: UUID):
        ...
~~~

Service/application service ưu tiên class khi có một trong các đặc điểm:

- Có dependency như repository, mailer, storage, task queue hoặc settings.
- Điều phối nhiều query/repository/integration.
- Sở hữu transaction boundary.
- Chứa nhiều use case liên quan trong cùng domain.

Dependency ổn định của service được truyền qua constructor. Router có thể tạo service
theo request từ dependency đã resolve; method service không nhận lại `session` nếu
service đã sở hữu session/repository. Dependency chỉ tồn tại cho một use case, chẳng
hạn mailer tùy chọn cho resend, có thể truyền vào method tương ứng.

~~~python
class UserService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserRepository | None = None,
    ) -> None:
        self._session = session
        self._users = user_repository or UserRepository(session)

    async def create(self, *, payload: UserCreate):
        ...
~~~

Pure domain logic, policy, mapper, validator hoặc utility không giữ state dùng function:

~~~python
def can_cancel_order(order: Order) -> bool:
    return order.status in {OrderStatus.PENDING, OrderStatus.CONFIRMED}
~~~

Không ép pure function thành class, không tạo class chỉ để gom static methods, và không
dùng class khi không có state/dependency/lifecycle cần quản lý.

### Imports

Thứ tự:

1. Standard library.
2. Third-party.
3. app imports.
4. Local module imports.

Ruff chịu trách nhiệm kiểm tra/sắp xếp import.

Không sửa lỗi E402 bằng cách bỏ qua rule nếu nguyên nhân là import đặt sai vị trí. Import phải ở đầu module, trừ trường hợp có lý do kỹ thuật rõ và noqa hẹp kèm giải thích.

### Typing

- Type public function/method.
- Không dùng Any để né thiết kế type.
- Dùng UUID, datetime, Decimal thay vì string/float chung chung khi domain yêu cầu.
- Dùng Protocol khi cần abstraction/injection mà không muốn coupling concrete.
- Không tạo generic abstraction quá sớm.
- Không dùng broad type: ignore. Nếu bất khả kháng, scope hẹp và ghi lý do.

### Function design

- Function có một mục đích rõ.
- Ưu tiên keyword-only arguments cho service/repository method có nhiều tham số.
- Không truyền dictionary không type xuyên nhiều layer nếu schema/dataclass rõ hơn.
- Không dùng boolean flag làm function thực hiện nhiều use case khác nhau.
- Comment giải thích vì sao, không lặp lại code.

## 24. Quy trình bắt buộc trước khi viết code

> **Scope:** Quy trình 8 bước bắt buộc cho mọi developer và AI agent trước khi viết mã nguồn mới hoặc chỉnh sửa chức năng.
>
> **Keywords:** `workflow`, `8 steps`, `survey codebase`, `reuse check`, `schema check`, `verification`

### Bước 1: Đọc repository

~~~bash
pwd
rg --files -g "AGENTS.md" -g "!**/.venv/**"
rg --files backend/src backend/tests | sed -n "1,260p"
~~~

Đọc:

- AGENTS.md áp dụng.
- backend/pyproject.toml.
- README.md và IMPLEMENTATION_PLAN.md liên quan.
- Module tương tự gần nhất.
- config/settings.py.
- database/session.py.
- common dependencies/exceptions.
- generated table liên quan.
- tests/conftest.py, tests/fixtures/ và test module tương tự gần nhất.

Không phỏng đoán package, import path, session pattern, error contract hoặc scripts.

### Bước 2: Xác định ownership

Trước khi tạo module/file, trả lời:

- Use case thuộc domain nào?
- Aggregate root là gì?
- Các bảng có cùng lifecycle không?
- Module nền tảng nào đã cung cấp identity/organization/permission?
- Có thật sự cần module mới không?
- Code này là domain-specific hay shared?

### Bước 3: Tìm code có sẵn

Thực hiện reuse-first search ở mục 14. Tìm cả tên, từ đồng nghĩa, behavior, table và endpoint.

### Bước 4: Kiểm tra schema/database

~~~bash
rg -n "<table_name>|<column_name>" backend/src/app/database/generated_tables.py
rg -n "<table_name>|<column_name>" backend
~~~

Xác nhận:

- Table/column tồn tại.
- organization_id và constraints.
- Foreign key.
- Index/unique behavior.
- Generated file không phải nơi cần sửa.

### Bước 5: Kiểm tra API contract

Tìm schema/router/frontend consumer trước khi thay đổi:

~~~bash
rg -n "<endpoint>|<SchemaName>|<field_name>" backend/src backend/tests frontend/src
~~~

Nếu repository không có frontend cùng workspace, ghi rõ chưa kiểm tra consumer.

### Bước 6: Lập kế hoạch

Với thay đổi không nhỏ, xác định:

- Module và files sẽ sửa.
- Reuse component/helper nào.
- Database/schema change hay không.
- organization isolation và permission policy.
- Transaction boundary.
- API/OpenAPI impact.
- Tests cần thêm/chạy.
- Background/storage side effects.

### Bước 7: Implement nhỏ nhất đúng kiến trúc

Không refactor ngoài phạm vi. Không tạo abstraction chưa có consumer rõ.

### Bước 8: Verify

Chạy Ruff, Pyrefly, Pytest và OpenAPI/build check phù hợp với phạm vi.

## 25. Testing — cấu trúc hiện tại

> **Scope:** Cấu trúc phân cấp kiểm thử thực tế (api, integration, security), quản lý fixture tập trung và quy tắc test tenant isolation.
>
> **Keywords:** `tests structure`, `fixtures`, `api tests`, `integration tests`, `security tests`, `pytest`

Tests được phân loại theo cấp độ và domain:

~~~text
tests/
├── conftest.py
├── fixtures/
│   ├── auth.py
│   ├── database.py
│   └── factories.py
├── api/
│   ├── activity_logs/
│   ├── applications/
│   ├── approval_requests/
│   ├── auth/
│   │   ├── test_auth.py
│   │   └── test_verifications.py
│   ├── candidate_imports/
│   ├── candidates/
│   ├── communications/
│   ├── email_templates/
│   ├── hiring_processes/
│   ├── interviews/
│   ├── job_descriptions/
│   ├── job_requisitions/
│   ├── members/
│   ├── offers/
│   ├── onboardings/
│   ├── organizations/
│   ├── organization_units/
│   ├── positions/
│   ├── recruitment_costs/
│   ├── recruitment_sources/
│   ├── users/
│   ├── work_items/
│   └── work_locations/
├── integration/
│   └── tools/
│       └── test_operations.py
└── security/
    ├── test_authorization.py
    ├── test_isolation.py
    └── test_security_contract.py
~~~

Chỉ tạo nhánh `unit/`, `integration/database/`, `integration/repositories/`,
`integration/storage/` hoặc `integration/workers/` khi có test thật sự thuộc loại đó.
Không tạo thư mục/file rỗng chỉ để đủ cây mẫu.

Quy tắc:

- Module mới phải có test tại nhánh phù hợp, ví dụ
  `tests/api/candidates/test_candidates.py`.
- Đặt test theo loại hành vi, không theo layer implementation một cách máy móc.
- `tests/conftest.py` chỉ đăng ký shared pytest plugins; không tích lũy fixture và
  factory trực tiếp tại đây.
- Tái sử dụng fixture trong `tests/fixtures/`.
- Không copy fixture database/auth cho từng file.
- Không gọi production database/RustFS/Redis thật trong tests.
- Test phải deterministic và độc lập thứ tự chạy.
- Test tenant isolation là bắt buộc cho module có organization_id.

### Phân loại test

Mỗi test phải được đặt theo một cấp độ rõ:

- Unit: pure function, policy, mapper, schema validation, service với dependency fake.
- Integration: repository với PostgreSQL test database, transaction, constraints, RustFS/Redis adapter khi có environment test.
- API: FastAPI route qua HTTPX, dependency wiring, auth, status code và response schema.
- Security/contract: tenant isolation, permissions, auth cookie/token và error/OpenAPI contract.

Nếu pytest markers đã được đăng ký trong pyproject.toml, dùng marker phù hợp. Không thêm marker chưa khai báo chỉ để tạo warning.

### Test service

Test:

- Happy path.
- Permission denied.
- Business conflict.
- Not found.
- Invalid state transition.
- Transaction rollback khi một bước thất bại.
- Side effect chỉ xảy ra đúng thời điểm.

### Test repository

Test với PostgreSQL thật/test container hoặc test database tương thích:

- Query/filter/sort.
- organization_id isolation.
- Unique/foreign/check constraint.
- Pagination.
- Lock/concurrency khi liên quan.
- Update/delete không chạm tenant khác.

Không dùng SQLite thay PostgreSQL cho test hành vi phụ thuộc Postgres nếu semantics có thể khác.

### Test API

Test:

- Request validation.
- Authentication.
- Organization resolution.
- Authorization.
- Status code.
- Response model.
- Error contract.
- OpenAPI endpoint nếu contract thay đổi.

### Mocking

- Mock tại external boundary: email, S3/RustFS, AI, external HTTP.
- Không mock repository trong repository integration test.
- Không mock chính function đang test.
- Ưu tiên fake có type/protocol rõ cho unit test.
- Assert behavior quan trọng, không assert implementation detail quá chặt.

### Regression

Mỗi bug fix nên có regression test tái hiện lỗi trước khi sửa ở cấp thấp nhất đáng tin cậy.

## 26. Testing — ownership và mở rộng cấu trúc

> **Scope:** Phân định quyền sở hữu của từng file fixture nền tảng và nguyên tắc mở rộng thư mục kiểm thử mà không phá vỡ test discovery.
>
> **Keywords:** `fixtures/database.py`, `fixtures/auth.py`, `factories.py`, `test ownership`, `test expansion`

- `tests/fixtures/database.py` sở hữu PostgreSQL test lifecycle và database reset.
- `tests/fixtures/auth.py` sở hữu HTTPX client, auth helpers và tenant fixture.
- `tests/fixtures/factories.py` sở hữu fake external boundary và API data factories.
- `tests/api/<domain>/` kiểm tra REST contract qua HTTPX.
- `tests/integration/<concern>/` kiểm tra database, repository, storage, worker hoặc
  operational tool với dependency thật dành cho test.
- `tests/security/` chứa regression suite xuyên module cho authentication,
  authorization, tenant isolation và security contract.
- `tests/unit/common/` hoặc `tests/unit/modules/<domain>/` chỉ được tạo khi có pure
  unit tests tương ứng.

Khi di chuyển hoặc tách test, phải giữ test discovery ổn định, cập nhật import về
`tests.fixtures`, và chạy toàn bộ suite để bảo đảm không thay đổi behavior.

## 27. Test data và factories

> **Scope:** Tiêu chuẩn khởi tạo dữ liệu mẫu, thiết lập tenant A và B cho kiểm thử cô lập, quy tắc dọn dẹp schema và cấm dùng dữ liệu thật.
>
> **Keywords:** `test data`, `factories`, `multi-tenant testing`, `database cleanup`, `deterministic test`

- Dữ liệu test phải có organization A và B khi kiểm tra tenant-aware code.
- Factory phải tạo ID/timestamp có kiểm soát.
- Không phụ thuộc dữ liệu seed từ môi trường developer.
- Test cleanup bằng transaction rollback/schema reset convention hiện có.
- Không truncate/drop database không được xác nhận là test database.
- Password/token fixture không dùng production secret.
- File fixture nhỏ và không chứa PII thật.

## 28. Background job tests

> **Scope:** Phương pháp kiểm thử toàn diện Celery tasks: kiểm thử logic handler, thời điểm enqueue sau commit, tính lũy đẳng và xử lý lỗi.
>
> **Keywords:** `Celery testing`, `worker tests`, `idempotency test`, `retry test`, `eager mode limitations`

Khi thêm Celery task:

- Unit test handler logic không cần worker thật.
- Test enqueue sau commit.
- Test duplicate delivery/idempotency.
- Test retryable/permanent error.
- Test organization isolation.
- Test status transition pending/running/succeeded/failed.
- Mock AI/email/S3 ở external boundary.
- Integration test broker/worker chỉ thêm khi infrastructure test đã được cấu hình.

Không dựa hoàn toàn vào eager mode nếu behavior cần xác minh khác worker thực.

## 29. Database migration rules

> **Scope:** Quy trình viết và áp dụng migration SQL thuần bằng dbmate, diễn tập trên database dùng một lần, đánh giá nguy cơ DDL lock, chiến lược backfill dữ liệu lớn và tái sinh file generated.
>
> **Keywords:** `dbmate`, `dry run`, `SQL thuần`, `schema_migrations`, `DDL locks`, `backfill`, `roll-forward`

### Công cụ và phân vai

Không dùng Alembic, không dùng ORM autogenerate. Mỗi công cụ có đúng một việc,
không chồng lấn:

| Công cụ | Việc | Không được dùng để |
|---|---|---|
| dbmate | Tạo file migration, apply, rollback, theo dõi version | Sinh `db/schema/schema.sql` |
| `uv run db export --clean` | Sinh `db/schema/schema.sql` | Apply migration |
| `uv run db generate` | Sinh `src/app/database/generated_tables.py` | Apply migration |

dbmate ghi version đã chạy vào bảng `schema_migrations`. Thư mục migration là
`db/migrations` — đúng mặc định của dbmate nên không cần `--migrations-dir`.

**Không dùng linter schema ngoài.** Atlas đã được thử trên repo này rồi bỏ. Schema
cố ý dùng cột `GENERATED`, `ltree`, trigger và partial index nhiều cột, và đó đúng
là vùng mù của nó:

- Migration xoá rồi tạo lại một cột sinh để đổi biểu thức — cách duy nhất
  PostgreSQL cho phép — làm Atlas hard-error ngay khi dựng diff
  (`changing the generation expression for a column "level" is not supported`),
  nên `-- atlas:nolint` cũng không tới lượt chạy.
- Nó đọc `UNIQUE (organization_id, LOWER(code)) WHERE code IS NOT NULL` thành
  unique một cột `organization_id` rồi cảnh báo trùng lặp không có thật.

Một cổng kiểm tra mà lần nào cũng phải bỏ qua thì dạy người ta quen bỏ qua. Vai
trò "soi DDL nguy hiểm trước khi chạy" chuyển sang bước diễn tập ở dưới, chạy trên
PostgreSQL thật nên không có mô hình nội bộ nào để hiểu sai.

### Sáu điều dễ sai, đã kiểm chứng trên repo này

1. **dbmate không đọc được `DATABASE_URL` của backend.** Biến đó là
   `postgresql+asyncpg://...` cho SQLAlchemy, còn dbmate báo
   `unsupported driver: postgresql+asyncpg`. dbmate cần URL libpq
   (`postgres://user:pass@host:port/db?sslmode=...`), nên phải có một biến riêng
   như `DBMATE_DATABASE_URL` bên cạnh `DATABASE_URL`. Thêm nữa, `--env-file` của
   dbmate mặc định là `.env` trong thư mục đang đứng, mà lệnh dbmate chạy từ gốc
   repository nên nó không tự đọc `backend/.env`. Phải chỉ rõ:
   `dbmate --env-file backend/.env -e DBMATE_DATABASE_URL ...`, hoặc truyền
   thẳng `--url`.

2. **Luôn truyền `--no-dump-schema`.** Mặc định `dbmate up` và `dbmate rollback`
   tự ghi schema file, và bản dump của dbmate chứa meta-command của psql
   (`\restrict`, `\unrestrict`) cùng phần `INSERT INTO schema_migrations`. Test
   fixture nạp `db/schema/schema.sql` bằng psycopg2, mà psycopg2 gặp `\restrict`
   là `SyntaxError`. `db/schema/schema.sql` chỉ được sinh bằng
   `uv run db export --clean`.

3. **File migration không tự mở transaction.** dbmate đã bọc mỗi migration
   trong một transaction, nên không viết `BEGIN;`/`COMMIT;` trong file. Câu lệnh
   không chạy được trong transaction (ví dụ `CREATE INDEX CONCURRENTLY`) thì khai
   báo `-- migrate:up transaction:false` và tự chịu trách nhiệm về tính nguyên tố.

4. **Ràng buộc cũ chặn chính bước backfill của mình.** Schema này nhiều CHECK
   và unique index nhiều cột, và chúng chặn cả những bước trung gian hợp lệ.
   Migration `20260918100000_organization_tree_slim.sql` là ví dụ đầy đủ, đụng cả
   hai loại:

   - `ck_member_role_assignments_scope` (đã bỏ trong chính migration đó) buộc
     `scope_type = 'ORGANIZATION'` phải đi kèm `scope_unit_id IS NULL`, nên nó
     chặn đúng câu `UPDATE` điền `scope_unit_id` cho các dòng ấy.
   - `uq_organization_units_sibling_name` coi `NULL` là bằng nhau
     (`NULLS NOT DISTINCT`), nên chèn gốc tập đoàn trùng tên với một công ty
     đang có sẽ đụng index ngay lúc `INSERT`.

   Phải **gỡ ràng buộc trước khi backfill** rồi dựng lại y nguyên ở cuối bước;
   đừng gộp `DROP CONSTRAINT` vào câu `ALTER TABLE` cuối cùng. Lỗi loại này chỉ
   lộ khi có dữ liệu, nên nó là lý do tồn tại của bước diễn tập.

5. **`dbmate new` đóng dấu thời gian theo UTC, và nó có thể nhỏ hơn migration
   đã có.** Máy phát triển ở UTC+7, nên lúc 16:36 giờ máy `dbmate new` sinh
   `20260918093605`. Những migration đặt tay trong repo này lại dùng giờ địa
   phương làm số tròn (`20260918100000`), nên file mới sắp xếp **trước** file cũ
   — vi phạm đúng quy tắc thứ tự ở phần dưới, và dbmate không cảnh báo. Sau
   `dbmate new`, luôn so tên file mới với `ls db/migrations | tail -2` và đổi tên
   nếu cần; chỉ đổi được khi file **chưa** chạy ở đâu.

6. **Không sinh `schema.sql` từ database dev đã dùng lâu.** PostgreSQL lưu biểu
   thức `CHECK` đã parse từ lúc tạo ràng buộc và **không** viết lại khi nâng cấp
   máy chủ, nên database dev dựng từ thời PG cũ dump ra khác database dựng mới
   trên PG hiện tại — khác ở cặp ngoặc trong, ví dụ
   `CHECK (((a >= 3) AND (a <= 63) AND …))` so với
   `CHECK ((((a >= 3) AND (a <= 63)) AND …))`. `tests/integration/test_migrations.py`
   dựng database sạch rồi so với `db/schema/schema.sql`, nên export từ dev làm CI
   đỏ ở một chỗ không liên quan gì tới thay đổi của mình (gặp thật 2026-10-26).
   Luôn sinh lại từ database sạch:

   ~~~bash
   psql "$ADMIN_URL" -c "DROP DATABASE IF EXISTS hr_ai_schema_check" \
                     -c "CREATE DATABASE hr_ai_schema_check OWNER <user>"
   dbmate --url "postgres://…/hr_ai_schema_check?sslmode=disable" \
          --migrations-dir db/migrations --no-dump-schema up
   DATABASE_URL="postgresql+asyncpg://…/hr_ai_schema_check" uv run db export --clean
   DATABASE_URL="postgresql+asyncpg://…/hr_ai_schema_check" uv run db generate
   ~~~

   Rồi chạy `uv run pytest tests/integration/test_migrations.py` trước khi push:
   nó bắt đúng lỗi này trong 2 giây, thay vì 20 phút chờ CI.

### Định dạng file migration

~~~sql
-- migrate:up
-- Vì sao cần thay đổi này, và những đánh đổi đã cân nhắc.
ALTER TABLE ... ;

-- migrate:down
-- Cách đảo, hoặc một dòng nói rõ vì sao không đảo được.
~~~

Tên file do `dbmate new` sinh, dạng `<timestamp>_<tên>.sql`. Không đổi tên file
đã chạy: dbmate nhận diện migration bằng phần timestamp của tên file.

### Quy tắc

- Chiến lược là **roll-forward**: muốn đảo một thay đổi đã chạy thì viết migration
  mới, không sửa và không chạy lùi migration cũ ở môi trường shared.
- `-- migrate:down` vẫn phải viết, để `dbmate rollback` dùng được trong lúc phát
  triển cục bộ. Thay đổi không đảo được **không được để block rỗng**: dbmate sẽ
  coi là rollback thành công và xoá version khỏi `schema_migrations` trong khi
  schema vẫn nguyên, tức là nói dối. Thay vào đó cho nó fail có lý do:

  ~~~sql
  -- migrate:down
  DO $$ BEGIN RAISE EXCEPTION 'khong dao duoc: <ly do>'; END $$;
  ~~~

  dbmate chạy down trong một transaction nên exception làm rollback thất bại và
  giữ nguyên cả schema lẫn version row.
- Không sửa migration đã chạy ở shared/production environment; tạo migration mới.
- Migration mới phải có timestamp lớn hơn mọi migration đã chạy. Chen một file có
  timestamp nhỏ hơn vào giữa sẽ làm thứ tự tên file khác thứ tự apply thực tế ở
  những môi trường đã đi trước.
- Data migration phải có batching khi dataset có thể lớn.
- Migration có bước backfill hoặc DDL phá huỷ phải được diễn tập trên database
  dùng một lần có dữ liệu trước khi apply vào bất kỳ môi trường nào.
- DDL lock risk phải được đánh giá.
- Add non-null column cần rollout an toàn cho bảng lớn.
- Index lớn cân nhắc `CONCURRENTLY` theo deployment policy, kèm
  `transaction:false`.
- Backfill phải idempotent hoặc có checkpoint khi cần.
- organization_id phải được backfill/validate trước khi enforce constraint.
- Sau khi apply: `uv run db export --clean` rồi `uv run db generate`. Hai file
  generated phải được commit cùng migration sinh ra chúng.
- Cập nhật test schema/bootstrap.

Không chạy migration destructive trên database không xác định rõ target.

### schema_migrations và hai file generated

Bảng `schema_migrations` là của dbmate. Phân biệt rõ hai thứ:

- **Các dòng trong bảng** (version nào đã apply) là **trạng thái của từng môi
  trường**, không phải source code: dev, staging và production mỗi nơi một khác.
  Không bao giờ commit. `uv run db export --clean` dùng `pg_dump --schema-only`
  nên đã loại sẵn, và `--no-dump-schema` chặn dbmate ghi bản dump của nó (bản đó
  có kèm `INSERT INTO schema_migrations`).
- **Định nghĩa bảng** thì có trong `db/schema/schema.sql` và
  `generated_tables.py`, và commit bình thường. Hai file đó là bản phản chiếu
  trung thực của database; lọc riêng một bảng ra sẽ phải đặc biệt hoá cả
  `clean_schema.py` lẫn bước sqlacodegen (sqlacodegen chỉ có `--tables` dạng
  allowlist, không có exclude), đổi lấy một chút thẩm mỹ mà thêm hai chỗ dễ sai.

`t_schema_migrations` trong `generated_tables.py` là metadata của công cụ.
Repository không được select, insert hay join vào nó. Nó cũng không phải "bảng
global" theo nghĩa ở mục 11.

`db/schema/schema.sql` dùng để bootstrap database test và để review schema. Nó
không phải cách dựng database phát triển: database phát triển dựng bằng
`dbmate up` để `schema_migrations` có đúng các version. Nạp schema.sql rồi chạy
`dbmate up` sẽ khiến dbmate tưởng chưa apply gì và chạy lại từ đầu.

### Kiểm chứng bộ migration

`tests/fixtures/database.py` bootstrap từ `db/schema/schema.sql` để suite chạy
nhanh, nên chuỗi migration không được thực thi trong suite thường. Bù lại bằng
một test dựng database rỗng, apply toàn bộ `db/migrations`, export rồi so với
`db/schema/schema.sql` đã commit. Test đó chứng minh cùng lúc ba điều: migration
apply được từ đầu, thứ tự hiện tại hợp lệ, và `schema.sql` đúng là sản phẩm của
bộ migration chứ không phải ảnh chụp một database lạ. Test này fail nghĩa là có
drift, phải sinh lại file generated chứ không sửa tay cho khớp.

Test đó là `tests/integration/test_migrations.py`, và nó cần `dbmate` trên PATH
như mọi binary khác mà suite đã cần (`initdb`, `pg_ctl`, `pg_dump`).

### Diễn tập migration có dữ liệu

Test ở trên chạy từ database **rỗng**, nên nó chỉ chứng minh DDL hợp lệ và không
drift. Nó không bao giờ chạm vào các nhánh backfill — mà đó chính là nơi migration
hay vỡ. Hai bước kiểm chứng này bù cho nhau:

| Bước | Xuất phát | Bắt được |
|---|---|---|
| `test_migrations.py` | database rỗng | DDL sai, thứ tự sai, `schema.sql` drift |
| Diễn tập | `schema.sql` + dữ liệu seed | backfill sai, constraint chặn backfill, dữ liệu biên |

Seed **không** phải dữ liệu tối thiểu cho chạy được, mà là dữ liệu **khó**: đúng
các trường hợp biên mà migration phải xử lý. Với migration đụng cây tổ chức thì
nghĩa là nhiều gốc, cây đủ độ sâu tối đa, tên trùng nhau giữa các nhánh sẽ bị gộp,
và đủ mọi giá trị của cột sắp bị bỏ.

Chạy trong một transaction: lỗi thì rollback sạch, sửa rồi chạy lại ngay trên
chính container đó, không phải dựng lại. Lệnh cụ thể ở mục 32.

## 30. Performance

> **Scope:** Hướng dẫn tối ưu hóa hiệu năng truy vấn SQL, loại bỏ N+1 query, streaming tệp lớn và chiến lược caching scoped theo organization.
>
> **Keywords:** `performance`, `SQL query optimization`, `N+1 queries`, `file streaming`, `caching strategy`

- Filter, sort, pagination trong SQL.
- Tránh N+1 query.
- Chọn column cần thiết cho list/query lớn.
- Không load file binary vào memory nếu có thể stream/presigned.
- Không giữ transaction khi gọi external network.
- Có timeout cho database/external calls.
- Batch insert/update khi phù hợp.
- Index theo tenant + access pattern.
- Không cache trước khi xác định invalidation.
- Cache key chứa organization_id.
- Không tối ưu phỏng đoán bằng abstraction phức tạp; đo hoặc có risk rõ.

### Chấm quyền nhiều lần trong một request là rẻ — vì có bộ nhớ, đừng gỡ nó

`AuthorizationRepository.grants()` chỉ chạy **một câu xuống database cho mỗi
`(organization_id, member_id)` trong cả request**, nhờ `app.common.session_memo`.
Nên cứ gọi `has_any` / `require_any` / `predicate` ở đúng chỗ nghiệp vụ cần, thay
vì chuyền kết quả chấm quyền qua tham số hay gộp các lần chấm lại cho "đỡ tốn".
Code rõ ràng hơn, và giá bằng nhau.

Hệ quả phải giữ:

- Bộ nhớ sống đúng một `AsyncSession`. Một session cho mỗi request
  (`get_session`), task nền và CLI tự mở session riêng — **đừng** dùng chung một
  session cho nhiều người dùng.
- Khoá có đủ `(organization_id, member_id)`. Thiếu một trong hai là trả quyền của
  người khác: lỗ hổng phân quyền, không phải lỗi hiệu năng.
- Bộ nhớ tự xoá sau **bất kỳ câu lệnh ghi nào** của session đó, nên thu hồi vai
  trò giữa request là thấy ngay. Viết thêm đường ghi thì không phải làm gì cả.
- `tests/security/test_grants_memo.py` giữ cả bốn điều trên. Đổi cách nhớ thì
  chạy **toàn bộ** `tests/security/`.

## 31. Code quality và dependency management

> **Scope:** Quản lý gói phụ thuộc bằng công cụ uv, kiểm soát nghiêm ngặt file uv.lock và nguyên tắc bảo đảm chất lượng mã nguồn.
>
> **Keywords:** `uv`, `pyproject.toml`, `uv.lock`, `dependency management`, `code quality`

Trước khi thêm dependency:

~~~bash
rg -n "^\[project\]|dependencies|dev-dependencies|dependency-groups" backend/pyproject.toml
uv tree
~~~

Quy tắc:

- Dùng uv add/remove theo convention repository.
- Không sửa uv.lock bằng tay.
- Không dùng pip/npm thay uv cho backend.
- Không thêm hai library cùng chức năng.
- Pin/range version theo policy hiện có.
- Đánh giá security/license/bundle chỉ ở mức phù hợp.

Không chạy auto-format/fix toàn repository nếu task chỉ sửa ít file và có thay đổi người dùng chưa commit. Chỉ format phạm vi đã sửa hoặc dùng script/pre-commit được chốt.

## 32. Lệnh kiểm tra

> **Scope:** Danh mục câu lệnh chuẩn cho quá trình kiểm tra cục bộ: đồng bộ uv, ruff check/format, pyrefly, pytest, pre-commit hooks và các lệnh database.
>
> **Keywords:** `uv sync`, `ruff check`, `ruff format`, `pyrefly`, `pytest`, `pre-commit`, `dbmate`, `dry run`

Agent phải đọc pyproject.toml và pre-commit config thực tế. Các lệnh dưới đây là convention dự kiến:

~~~bash
cd backend

uv sync
uv run ruff check src tests
uv run ruff format --check src tests
uv run pyrefly check
uv run pytest
~~~

Chạy test file/module liên quan trong vòng lặp nhanh:

~~~bash
uv run pytest tests/api/candidates/test_candidates.py -q
uv run pytest tests/security/test_isolation.py -q
~~~

Sau đó chạy suite rộng hơn trước khi hoàn thành khi thay đổi có impact rộng.
Chạy song song bằng pytest-xdist: mỗi worker tự dựng PostgreSQL tạm riêng
(`tests/support/postgres.py`) nên không đụng nhau; cả suite ~7 phút thay vì ~25:

~~~bash
uv run pytest -n auto
~~~

Ruff:

- ruff check --fix dùng để sửa lint fixable khi phù hợp.
- ruff format không nhận --fix.
- Không thêm --fix vào ruff format.
- Review diff sau auto-fix.

Pre-commit:

~~~bash
uv run pre-commit run --all-files
~~~

Chỉ chạy nếu project đã cấu hình và phạm vi phù hợp.

Nếu API contract đổi, chạy command kiểm tra/export OpenAPI và frontend codegen đã định nghĩa trong repository.

Database, chạy từ gốc repository vì `db/migrations` là đường dẫn tương đối:

~~~bash
DBM="dbmate --env-file backend/.env -e DBMATE_DATABASE_URL"

$DBM status
$DBM --no-dump-schema up
$DBM --no-dump-schema rollback
$DBM new <ten_migration>
~~~

`DBMATE_DATABASE_URL` là URL libpq (`postgres://...`) và là biến riêng, không
dùng chung với `DATABASE_URL` của backend.

Diễn tập migration trước khi apply, trên một PostgreSQL dùng một lần, không bao
giờ trỏ vào database của dự án:

~~~bash
MIG=db/migrations/<timestamp>_<ten>.sql

docker rm -f pg_dryrun 2>/dev/null
docker run -d --name pg_dryrun \
  -e POSTGRES_PASSWORD=x -e POSTGRES_DB=probe postgres:18
until docker exec pg_dryrun pg_isready -q; do sleep 1; done

# 1. Nạp schema đã commit = trạng thái ngay trước migration.
docker cp db/schema/schema.sql pg_dryrun:/schema.sql
docker exec pg_dryrun psql -U postgres -d probe -q -v ON_ERROR_STOP=1 -f /schema.sql

# 2. Seed dữ liệu biên mà migration phải xử lý (xem mục 29).
docker cp seed.sql pg_dryrun:/seed.sql
docker exec pg_dryrun psql -U postgres -d probe -q -v ON_ERROR_STOP=1 -f /seed.sql

# 3. Chạy phần -- migrate:up trong một transaction.
awk '/^-- migrate:up/{f=1;next} /^-- migrate:down/{f=0} f' "$MIG" > up.sql
docker cp up.sql pg_dryrun:/up.sql
docker exec pg_dryrun psql -U postgres -d probe -q -v ON_ERROR_STOP=1 \
  --single-transaction -f /up.sql

# 4. Kiểm chứng kết quả và các ràng buộc mới bằng SQL, rồi dọn.
docker rm -f pg_dryrun
~~~

Ảnh `postgres:18` phải khớp phiên bản nền của dự án: schema dùng `uuidv7()`, bản
thấp hơn sẽ không nạp được `schema.sql`.

Bước 4 không bỏ được: apply thành công mới chỉ là không có exception. Phải soi
bằng SQL rằng dữ liệu đã chuyển đúng, và thử ghi vào những đường mà constraint hay
trigger mới phải chặn — chặn được mới coi là xong.

Tính toàn vẹn của thư mục migration do `tests/integration/test_migrations.py` bảo
đảm, không do một file checksum nào cả.

Sinh lại file generated sau khi apply, chạy trong `backend`:

~~~bash
uv run db export --clean
uv run db generate
~~~

Cả hai lệnh chỉ đọc từ database mà `DATABASE_URL` trỏ tới và ghi ra file; chúng
không apply gì cả. Chạy chúng trên một database chưa apply đủ migration sẽ tạo ra
file generated lệch với repo.

## 33. Definition of Done

> **Scope:** Bảng kiểm tra toàn diện 28 tiêu chí bắt buộc phải đạt được trước khi đánh dấu hoàn thành bất kỳ task nào trong backend.
>
> **Keywords:** `Definition of Done`, `checklist`, `quality gates`, `verification`, `DoD`

Trước khi báo hoàn thành, agent phải xác nhận:

- [ ] Đã đọc AGENTS.md, pyproject.toml và module tương tự.
- [ ] Đã tìm code/helper/dependency hiện có trước khi tạo mới.
- [ ] Use case nằm đúng module/aggregate.
- [ ] Không tạo module theo từng bảng một cách máy móc.
- [ ] Router chỉ chứa HTTP concern.
- [ ] Service chứa business rule, permission và transaction.
- [ ] Repository chứa query và không commit.
- [ ] Schema API tách khỏi database table.
- [ ] Không tạo ORM model trùng generated table.
- [ ] Không sửa generated_tables.py bằng tay.
- [ ] Mọi query tenant-aware có organization_id.
- [ ] Insert dùng trusted organization context.
- [ ] Permission và ownership được kiểm tra ở backend.
- [ ] Không tạo lại user/organization/member/role foundation.
- [ ] API/error/status code nhất quán.
- [ ] Nếu contract đổi, OpenAPI/frontend generated client đã được xem xét.
- [ ] Nếu schema đổi: migration SQL đã diễn tập trên database dùng một lần rồi apply bằng dbmate, và `db/schema/schema.sql` cùng `generated_tables.py` đã sinh lại.
- [ ] Transaction boundary rõ và không giữ transaction qua external call lâu.
- [ ] RustFS được dùng qua S3-compatible shared adapter.
- [ ] Không lưu binary/secret/presigned URL lâu dài trong PostgreSQL.
- [ ] File relation dùng `file_id`; metadata kỹ thuật dùng đúng contract `stored_files`.
- [ ] Object key do backend tạo bằng trusted IDs, đúng `public/` hoặc `private/` prefix.
- [ ] Upload complete đã HEAD/validate object trước khi persist và có cleanup khi lỗi.
- [ ] Public URL chỉ dành cho public file; private download đã authorize và ký ngắn hạn.
- [ ] Background job tenant-aware và idempotent khi cần.
- [ ] Có test happy path và failure/security path phù hợp.
- [ ] Có tenant isolation test cho module mới.
- [ ] Ruff pass.
- [ ] Pyrefly pass cho phạm vi yêu cầu.
- [ ] Tests liên quan pass.
- [ ] Full suite đã chạy khi impact rộng.
- [ ] Không log/commit secret hoặc PII nhạy cảm.
- [ ] Không sửa file ngoài phạm vi không cần thiết.

Nếu một bước không thể chạy, agent phải nói rõ bước nào chưa chạy và lý do. Không báo pass nếu command chưa chạy hoặc đã thất bại.

## 34. Anti-pattern bị cấm

> **Scope:** Danh mục chi tiết các mẫu thiết kế sai lầm (anti-patterns), hành vi cấm kỵ về kiến trúc, bảo mật và chất lượng code.
>
> **Keywords:** `anti-patterns`, `forbidden practices`, `architectural violations`, `security risks`

- Tổ chức toàn bộ backend thành routers/, services/, repositories/, schemas/ chứa mọi domain.
- Mỗi table thành một module dù cùng aggregate.
- Router viết SQL hoặc business logic.
- Router gọi repository trực tiếp cho use case nghiệp vụ.
- Repository kiểm tra HTTP permission hoặc raise HTTPException.
- Repository commit transaction.
- Service tự tạo database session/engine.
- Module định nghĩa models.py để lặp lại generated tables.
- Sửa generated_tables.py bằng tay.
- Dùng metadata.create_all thay migration production.
- Query tenant data thiếu organization_id.
- Tin organization_id/role từ request body.
- Check resource bằng UUID nhưng không tenant scope.
- Hard-code role thay permission policy ở nhiều nơi.
- Module tuyển dụng tạo lại user/organization/membership/role.
- Import repository private của module khác để ghi dữ liệu.
- Circular dependency giữa modules.
- Copy shared helper rồi đổi tên.
- Biến common thành utils.py khổng lồ.
- Đọc environment trực tiếp rải rác.
- Dùng RustFS/S3 SDK trực tiếp trong từng module.
- Lưu file binary lớn hoặc credentials trong PostgreSQL.
- Lưu presigned URL/public URL vào database hoặc dùng URL làm định danh file.
- Nhận bucket/object key từ client hoặc dùng filename người dùng làm object key.
- Dùng `uploaded_by` thay cho ownership, tenant scope hoặc authorization.
- Mở anonymous access cho toàn bucket thay vì chỉ prefix `public/`.
- Tạo row `stored_files` hợp lệ trước khi object upload được xác minh.
- Trả anonymous URL cho object dưới `private/`.
- Enqueue Celery job trước commit mà không có outbox/idempotency.
- Giữ DB transaction khi chờ AI/email/storage lâu.
- Dùng Redis làm source of truth cho nghiệp vụ.
- Catch Exception rồi im lặng.
- Trả raw SQLAlchemy Row/internal field cho API.
- Dùng Any, type ignore hoặc noqa rộng chỉ để check pass.
- Thêm package trùng chức năng mà chưa kiểm tra.
- Tự ý di chuyển test sang unit/integration/api trong task không liên quan.
- Test bằng production database/storage.
- Bỏ qua tenant isolation/security regression.

## 35. Mẫu báo cáo cuối task

> **Scope:** Mẫu khung định dạng chuẩn dùng để báo cáo kết quả hoàn thành task, bao gồm kết quả, kiến trúc, API/DB, files, kiểm tra và lưu ý.
>
> **Keywords:** `report format`, `task summary`, `verification report`, `final report`

Khi hoàn thành task backend, báo cáo ngắn gọn:

~~~text
Kết quả
- Use case/behavior đã thêm hoặc sửa.

Kiến trúc
- Module và aggregate.
- Shared code đã tái sử dụng.
- Transaction và organization scope.

API/Database
- Endpoint/schema/migration/generated table thay đổi.
- OpenAPI/frontend impact.

Files
- Các file chính đã thay đổi.

Kiểm tra
- ruff: pass/fail/not run
- Pyrefly: pass/fail/not run
- tests liên quan: pass/fail/not run
- full tests: pass/fail/not run
- OpenAPI/codegen: pass/fail/not run

Lưu ý
- Rủi ro, migration, deployment hoặc bước tiếp theo.
~~~

Báo cáo phải dẫn đầu bằng kết quả và phản ánh verification thực tế. Không liệt kê dài dòng mọi thao tác nội bộ.
