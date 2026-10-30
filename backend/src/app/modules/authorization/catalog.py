"""Permission catalog kept in code (database decisions phase 1 §4, phase 3).

The baseline migration holds the schema only, so these rows reach a database
through `uv run iam sync-permissions` after `dbmate up`. Keys are stable:
renaming one is a data migration, not an edit here.
"""

from typing import NamedTuple


class Permission(NamedTuple):
    resource: str
    action: str
    description: str


PERMISSIONS: tuple[Permission, ...] = (
    Permission(
        "organization", "manage", "Quản trị tổ chức; không cấp quyền đọc chat riêng"
    ),
    Permission("member", "manage", "Mời, khóa và quản lý thành viên"),
    Permission("role", "manage", "Quản lý vai trò và gán quyền"),
    Permission("conversation", "create", "Tạo conversation riêng"),
    Permission(
        "conversation", "share", "Chia sẻ snapshot của conversation do mình sở hữu"
    ),
)

#: What a personal workspace may do without roles: its owner is its only user.
PERSONAL_ALLOWED: frozenset[tuple[str, str]] = frozenset(
    {("conversation", "create"), ("conversation", "share")}
)
